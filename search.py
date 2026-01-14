import datetime
import os

import rich
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_experimental.tools.python.tool import PythonREPLTool
from langchain_openai import ChatOpenAI

from data.data import File, NLSResult
from services.es_service import ElasticsearchService
from tools.search_tools import (
    get_answers_for_question,
    get_semantic_search_results,
    get_time_ranged_search_results,
)

# Configuration - load from environment variables
load_dotenv()  # Load environment variables early

# Initialize services
es_service = ElasticsearchService.get_instance(
    host=os.getenv("ELASTICSEARCH_HOST", "localhost"),
    port=os.getenv("ELASTICSEARCH_PORT", "9200"),
    index_name=os.getenv("ELASTICSEARCH_INDEX_NAME", "nls"),
)

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


def natural_language_search(query: str) -> tuple[NLSResult, dict[str, File], list[str]]:
    """
    Perform natural language search using appropriate tools.

    Returns a tuple of (NLSResult, dict[str, File], list[str]).
    The File dict contains the mapping from filename to File object that are relevant to the result.
    The list of strings is the list of tools that were used.
    """
    tools = [
        get_answers_for_question,  # to answer questions about the file contents
        get_time_ranged_search_results,  # to perform time-ranged search
        get_semantic_search_results,  # to perform semantic search
        PythonREPLTool(),  # to execute python code, for doing math
    ]

    llm = ChatOpenAI(temperature=0, api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT.format(current_time=datetime.datetime.now())),
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

    # Validate result type
    if search_result.result_type not in ["search", "answer"]:
        raise ValueError(f"Invalid result type: {search_result.result_type}")

    # Filter search results if needed
    if search_result.result_type == "search":
        # Filter out the search result that the LLM chose to return in the final response
        # This helps perform file type filtering in the final response
        # TODO: this is a hack, we should encode the filter type into the search tool.
        search_result.files = [f for f in search_result.files if f in result["output"]]

    # Build file metadata mapping
    file_metas = es_service.get_file_metadata(search_result.files)

    tools_used = [step[0].tool for step in result["intermediate_steps"]]

    return search_result, file_metas, tools_used
