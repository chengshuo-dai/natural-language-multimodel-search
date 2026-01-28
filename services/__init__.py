import os

from dotenv import load_dotenv

from .es_service import ElasticsearchService

load_dotenv()

# Initialize the singleton instance once at module level
es_service = ElasticsearchService.get_instance(
    host=os.getenv("ELASTICSEARCH_HOST", "localhost"),
    port=os.getenv("ELASTICSEARCH_PORT", "9200"),
    index_name=os.getenv("ELASTICSEARCH_INDEX_NAME", "nls"),
)

__all__ = ["ElasticsearchService", "es_service"]
