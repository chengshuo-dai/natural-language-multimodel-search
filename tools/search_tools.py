import datetime
import os

from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain.tools import tool
from langchain_elasticsearch import ElasticsearchRetriever
from langchain_openai import ChatOpenAI

from data.data import File, NLSResult
from model.sbert_model import SBertModel
from services.elasticsearch_service import ElasticsearchService

# Initialize the Elasticsearch service
load_dotenv()
es_service = ElasticsearchService.get_instance(
    host=os.getenv("ELASTICSEARCH_HOST", "localhost"),
    port=os.getenv("ELASTICSEARCH_PORT", "9200"),
    index_name=os.getenv("ELASTICSEARCH_INDEX_NAME", "nls"),
)


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
    resp = es_service.client.search(
        index=es_service.index_name,
        query={"range": {"created": {"gte": start_ts, "lte": end_ts}}},
    )

    files = es_service._process_search_results(resp)

    return NLSResult(result_type="search", files=files, answer="")


@tool
def get_semantic_search_results(query: str) -> NLSResult:
    """
    Returns search results based on semantic similarity to the query.
    """
    query_embedding = SBertModel.get_embedding(query)
    resp = es_service.client.search(
        index=es_service.index_name,
        query={
            "bool": {
                "should": [
                    {"match": {"filename": {"query": query, "fuzziness": "auto"}}},
                    {"match": {"text": {"query": query, "fuzziness": "auto"}}},
                ]
            }
        },
        knn={
            "field": "embedding",
            "query_vector": query_embedding,
            "k": 1,
            "num_candidates": 3,
        },
    )

    files = es_service._process_search_results(resp)

    return NLSResult(result_type="search", files=files, answer="")


@tool
def get_answers_for_question(question: str) -> NLSResult:
    """
    Returns answers for questions about file contents by analyzing the content semantically.
    """
    # TODO: we're using KNN for QnA for now, expand this to better retrieval methods
    es_retriever = ElasticsearchRetriever.from_es_params(
        url=es_service.url,
        index_name=es_service.index_name,
        content_field="text",
        body_func=lambda query: {
            "knn": {
                "field": "embedding",
                "query_vector": SBertModel.get_embedding(query),
                "k": 1,
                "num_candidates": 3,
            },
        },
    )

    # Setup llm to use
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
        source = doc.metadata["_source"]
        filename = source["filename"]

        # Add to cache
        es_service.add_file_to_cache(filename, File.from_elasticsearch_source(source))

        # Add to result
        files.append(filename)

    return NLSResult(result_type="answer", files=files, answer=answer)
