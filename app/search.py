import time

import rich
from elasticsearch import Elasticsearch
from langchain.agents import AgentExecutor, tool
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.render import format_tool_to_openai_function
from langchain_experimental.tools.python.tool import PythonREPLTool
from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer

ES = Elasticsearch("http://localhost:9200/")
SBERT_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
INDEX = "nls_search_final"


def time_ranged_search(start_ts: float, end_ts: float) -> list[str]:
    resp = ES.search(
        index=INDEX, query={"range": {"created": {"gte": start_ts, "lte": end_ts}}}
    )
    return [hit["_source"]["filename"] for hit in resp["hits"]["hits"]]


@tool
def get_time_ranged_search_results(start_ts: float, end_ts: float) -> list[str]:
    """
    Returns search results between two Unix timestamps.

    Parameters:
    - start_ts (float): Start of the time range (in seconds since epoch). Default is 0
    - end_ts (float): End of the time range (in seconds since epoch).

    Notes:
    - Both `start_ts` and `end_ts` are required. Do not use the current timestamp as `end_ts` unless specified.
    - For queries like "files created in 2021", compute `start_ts` as the beginning of 2021 and `end_ts` as the end of 2021.

    Example:
    - get_time_ranged_search_results(1609459200.0, 1640995199.0) for "files created in 2021".
    """
    return time_ranged_search(start_ts, end_ts)


def semantic_search(query: str) -> list[str]:
    query_embedding = SBERT_MODEL.encode([query])[0]
    resp = ES.search(
        index=INDEX,
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

    return [hit["_source"]["filename"] for hit in resp["hits"]["hits"]]


@tool
def get_semantic_search_results(query: str) -> list[str]:
    """
    Returns search results for a semantic query that does not involve time ranges.
    Example:
    - get_semantic_search_results("christmas hat")
    """
    return semantic_search(query)


def get_answers_for_question(question: str) -> str:
    return f"QA tool not implemented yet! Question received: {question}"


@tool
def get_answers_for_question(question: str) -> str:
    """
    Returns answers for a question about the file contents.
    """
    return get_answers_for_question(question)


SYSTEM_PROMPT = """You are a highly capable assistant designed to help with searching for files and answering questions about them. You have access to specialized tools for different types of queries.

1. For time-ranged queries (involving dates or times):
   Use the time-ranged search tool. Remember that the current Unix timestamp is {current_time}.
   Avoid performing time calculations yourself; use the provided tools for accuracy.

2. For semantic queries (general search without time constraints):
   Use the semantic search tool to find relevant files based on content or keywords.

3. For questions about file contents:
   Use the question answering tool to provide information from the files.

When responding:
- Analyze the query to determine which tool is most appropriate.
- Use the tools to obtain accurate results rather than estimating or computing manually.
- For time-ranged searches, ensure you pass properly computed timestamps (as floats representing Unix time) to the tools.
- If unsure about any calculation or process, use the appropriate tool to achieve the desired outcome.
- Return tool outputs to the user without modifications if they appear correct.

Your goal is to route each query to the most suitable tool and provide accurate, helpful responses based on the tool's output.
"""


def natural_language_search(query: str, openai_api_key: str) -> list[str]:
    tools = [
        # TODO: Consider combining these two tools into a single tool that can perform both time-ranged and semantic search.
        get_time_ranged_search_results,  # to perform time-ranged search
        get_semantic_search_results,  # to perform semantic search
        get_answers_for_question,  # to answer questions about the file contents
        PythonREPLTool(),  # to execute python code, for doing math
    ]

    llm = ChatOpenAI(temperature=0, openai_api_key=openai_api_key)
    llm_with_tools = llm.bind(
        functions=[format_tool_to_openai_function(tool) for tool in tools]
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT.format(current_time=int(time.time()))),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = (
        {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_to_openai_functions(
                x["intermediate_steps"]
            ),
        }
        | prompt
        | llm_with_tools
        | OpenAIFunctionsAgentOutputParser()
    )

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )

    result = agent_executor.invoke({"input": query})

    # Filter out the search result that the LLM chose to return in the final response
    # This helps perform file type filtering in the final response
    search_result = result["intermediate_steps"][-1][-1]
    ret = [r for r in search_result if r in result["output"]]

    # Uncomment this for debugging
    # rich.print(ret)

    return ret
