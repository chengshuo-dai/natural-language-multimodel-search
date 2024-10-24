import time
from typing import Optional

from elasticsearch import Elasticsearch
from langchain.agents import AgentExecutor, tool
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.render import format_tool_to_openai_function
from langchain_experimental.tools.python.tool import PythonREPLTool
from langchain_openai import ChatOpenAI

es = Elasticsearch("http://localhost:9200/")
INDEX = "nls_search"


def search(start_ts: float, end_ts: float) -> list[str]:
    resp = es.search(
        index=INDEX, query={"range": {"created": {"gte": start_ts, "lte": end_ts}}}
    )
    return [hit["_source"]["filename"] for hit in resp["hits"]["hits"]]


@tool
def get_time_ranged_search_results(
    query: str, start_ts: float, end_ts: float
) -> list[str]:
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
    return search(start_ts, end_ts)


SYSTEM_PROMPT = """You are a highly capable assistant designed to help with searching for files using a time range.
Although you cannot perform time-ranged searches directly, you have access to specialized tools for this purpose.

If you need to calculate relative time or determine specific timestamps, remember that the current Unix timestamp is {current_time}.
Avoid performing any calculations yourself. Instead, use the tools provided to handle any time calculations or searches.

When responding, focus on using the tools to obtain accurate results rather than trying to manually compute or estimate values.
Ensure that you only pass properly computed timestamps (as floats representing Unix time) to the tools.

If you are unsure or require assistance with any calculation, request the use of a tool to achieve the desired outcome.

If you think the tool output is correct, return the result to the user as it is without any modifications.
"""


def natural_language_search(query: str, openai_api_key: str) -> list[str]:
    tools = [
        get_time_ranged_search_results,  # to perform the search
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
    return result["intermediate_steps"][-1][-1]
