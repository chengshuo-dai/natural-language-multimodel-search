import datetime
import os
import time
from dataclasses import dataclass

import rich
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from langchain.agents import AgentExecutor, create_openai_functions_agent, tool
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.render import format_tool_to_openai_function
from langchain_elasticsearch import ElasticsearchRetriever
from langchain_experimental.tools.python.tool import PythonREPLTool
from langchain_openai import ChatOpenAI
from model.sbert import SBertModel

ES = Elasticsearch("http://localhost:9200/")
INDEX_NAME = "nls"


@dataclass
class File:
    filename: str
    created: float
    path: str
    size: int
    extension: str


@dataclass
class NLSResult:
    result_type: str  # "answer" or "search"
    # list of filenames for search results or sources for answers
    # NOTE: we don't use list[File] because we want to keep the result type simple enough as the output of tools
    # so that it's easier for LLM to parse
    # we keep a mapping from filename to File object separately.
    files: list[str]
    answer: str  # answer for question, empty string if result_type is "search"


# Serve as a cache for File objects
# Everytime we get a search result, we add the File objects to this cache.
# For simplicity, we don't invalidate the cache.
FILE_BY_NAME: dict[str, File] = {}


@tool
def get_time_ranged_search_results(
    start_ts: datetime.datetime, end_ts: datetime.datetime
) -> NLSResult:
    """
    Returns search results between two Unix timestamps.

    Parameters:
    - start_ts (datetime.datetime): Start of the time range.
    - end_ts (datetime.datetime): End of the time range.

    Returns:
    - NLSResult

    Here's the definition of NLSResult:
    @dataclass
    class NLSResult:
        result_type: str  # "answer" or "search"
        # list of filenames for search results or sources for answers
        files: list[str]
        answer: str  # answer for question, empty string if result_type is "search"

    Examples:
    >>> # Files created in 2021
    >>> get_time_ranged_search_results(
    ...     datetime.datetime(2021, 1, 1),
    ...     datetime.datetime(2021, 12, 31)
    ... )
    """
    resp = ES.search(
        index=INDEX_NAME, query={"range": {"created": {"gte": start_ts, "lte": end_ts}}}
    )

    files: list[str] = []
    for hit in resp["hits"]["hits"]:
        # Add to cache
        FILE_BY_NAME[hit["_source"]["filename"]] = File(
            filename=hit["_source"]["filename"],
            created=hit["_source"]["created"],
            path=hit["_source"]["metadata"]["path"],
            size=hit["_source"]["metadata"]["size"],
            extension=hit["_source"]["metadata"]["extension"],
        )

        # Add to result
        files.append(hit["_source"]["filename"])

    return NLSResult(result_type="search", files=files, answer="")


@tool
def get_semantic_search_results(query: str) -> NLSResult:
    """
    Returns search results based on semantic similarity to the query.
    """
    query_embedding = SBertModel.get_embedding(query)
    resp = ES.search(
        index=INDEX_NAME,
        query={
            "bool": {
                "should": [
                    {"match": {"filename": {"query": query, "fuzziness": "auto"}}},
                    {"match": {"text": {"query": query, "fuzziness": "auto"}}},
                ]
            }
        },
        knn={
            "field": "vector",
            "query_vector": query_embedding,
            "k": 1,
            "num_candidates": 3,
        },
    )

    files: list[str] = []
    for hit in resp["hits"]["hits"]:
        # Add to cache
        FILE_BY_NAME[hit["_source"]["filename"]] = File(
            filename=hit["_source"]["filename"],
            created=hit["_source"]["created"],
            path=hit["_source"]["metadata"]["path"],
            size=hit["_source"]["metadata"]["size"],
            extension=hit["_source"]["metadata"]["extension"],
        )

        # Add to result
        files.append(hit["_source"]["filename"])

    return NLSResult(result_type="search", files=files, answer="")


def es_query(query: str):
    # TODO: use KNN for QnA for now
    query_embedding = SBertModel.get_embedding(query)
    return {
        "knn": {
            "field": "embedding",
            "query_vector": query_embedding,
            "k": 1,
            "num_candidates": 3,
        },
    }


@tool
def get_answers_for_question(question: str) -> NLSResult:
    """
    Returns answers for questions about file contents by analyzing the content semantically.
    """
    es_retriever = ElasticsearchRetriever.from_es_params(
        url="http://localhost:9200",
        index_name=INDEX_NAME,
        content_field="text",
        body_func=es_query,
    )

    # Setup llm to use
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(temperature=0.1, api_key=openai_api_key, model="gpt-4o")

    # Setup QA chain
    qa = RetrievalQA.from_chain_type(
        chain_type="stuff",  # -> fill up
        llm=llm,
        retriever=es_retriever,
        return_source_documents=True,
    )

    # Invoke QA chain
    resp = qa.invoke(question)

    answer = resp["result"]
    files: list[str] = []
    for doc in resp["source_documents"]:
        # Add to cache
        FILE_BY_NAME[doc.metadata["_source"]["filename"]] = File(
            filename=doc.metadata["_source"]["filename"],
            created=doc.metadata["_source"]["created"],
            path=doc.metadata["_source"]["metadata"]["path"],
            size=doc.metadata["_source"]["metadata"]["size"],
            extension=doc.metadata["_source"]["metadata"]["extension"],
        )

        # Add to result
        files.append(doc.metadata["_source"]["filename"])

    return NLSResult(result_type="answer", files=files, answer=answer)


SYSTEM_PROMPT = """You are a highly capable assistant designed to help with searching for files and answering questions about them. You have access to specialized tools for different types of queries. You always have to use at least one tool.

1. For questions about file contents:
   Use the question answering tool to provide information from the files. A query is considered a question if it:
   - Ends with a question mark (?)
   - Starts with question words (what, what's, how, why, when, where, who, which)
   - Asks for instructions or explanations (e.g., "explain...", "tell me about...", "steps to...")

2. For time-ranged queries (involving dates or times):
   Use the time-ranged search tool. Remember that the current Unix timestamp is {current_time}.
   Avoid performing time calculations yourself; use the provided tools for accuracy.

3. For semantic queries (general search without time constraints):
   Use the semantic search tool to find relevant files based on content or keywords.
   Only use this tool if the query does not fit into any of the above categories.

When responding:
- Analyze the query to determine which tool is most appropriate, starting with the question answering tool, then the time-ranged search tool, and finally the semantic search tool.
- You have to use at least one tool.
- Use the tools to obtain accurate results rather than estimating or computing manually.
- For time-ranged searches, ensure you pass properly computed timestamps (as floats representing Unix time) to the tools.
- If unsure about any calculation or process, use the appropriate tool to achieve the desired outcome.
- Return tool outputs to the user without modifications if they appear correct.

Examples of questions (use question answering tool):
- "how to setup a new python virtual env"
- "steps to install docker"
- "explain the deployment process"
- "what are the requirements for this project"
- "tell me about the database schema"

Your goal is to route each query to the most suitable tool and provide accurate, helpful responses based on the tool's output.
"""


def natural_language_search(query: str) -> tuple[NLSResult, dict[str, File]]:
    """
    Returns a tuple of (NLSResult, dict[str, File]).
    The File dict contians the mapping from filename to File object that are relevant to the result.
    """
    # TODO: Figure out a better way to split the tools
    tools = [
        get_answers_for_question,  # to answer questions about the file contents
        get_time_ranged_search_results,  # to perform time-ranged search
        get_semantic_search_results,  # to perform semantic search
        PythonREPLTool(),  # to execute python code, for doing math
    ]

    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(temperature=0, api_key=openai_api_key, model="gpt-4o")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT.format(current_time=int(time.time()))),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        handle_parsing_errors=True,  # Try to auto-correct the agent response is malformed
        return_intermediate_steps=True,
        verbose=True,  # Display the agent's thought process
    )

    result = agent_executor.invoke({"input": query})

    # Uncomment this for debugging
    # rich.print(result)

    search_result = result["intermediate_steps"][-1][-1]

    try:
        if search_result.result_type == "search":
            # Filter out the search result that the LLM chose to return in the final response
            # This helps perform file type filtering in the final response
            search_result.files = [
                r for r in search_result.files if r in result["output"]
            ]
        elif search_result.result_type not in ["search", "answer"]:
            # This should never happen
            raise ValueError(f"Invalid result type: {search_result.result_type}")

        file_metas = {
            fname: f
            for fname, f in FILE_BY_NAME.items()
            if fname in search_result.files
        }

        return search_result, file_metas
    except Exception as e:
        rich.print(e)
        raise e
