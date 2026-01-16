from elasticsearch import Elasticsearch

from data.data import Document
from model.sbert_model import SBertModel


class ElasticsearchService:
    """Service class for Elasticsearch operations."""

    _instance = None

    @classmethod
    def get_instance(cls, host: str, port: str, index_name: str):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls(host, port, index_name)
        return cls._instance

    def __init__(self, host: str, port: str, index_name: str):
        self.url = f"http://{host}:{port}/"
        self.client = Elasticsearch(self.url)
        self.index_name = index_name
        self.file_cache: dict[str, Document] = {}

    @staticmethod
    def get_index_mapping() -> dict:
        """Get the index mapping with the correct embedding dimensions."""
        return {
            "properties": {
                "filename": {"type": "text", "analyzer": "english"},
                "extension": {"type": "text"},
                "text": {"type": "text", "analyzer": "english"},
                "created_at": {"type": "date"},
                "path": {"type": "text"},
                "size": {"type": "long"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": SBertModel.get_dimension(),
                    "index": True,
                    "similarity": "cosine",
                },
            }
        }

    def overwrite_index(self) -> None:
        """Delete the index if it exists and create a new one."""
        if self.client.indices.exists(index=self.index_name):
            self.client.indices.delete(index=self.index_name)
        self.client.indices.create(
            index=self.index_name, mappings=self.get_index_mapping()
        )

    def ensure_index_exists(self) -> None:
        """Create the index if it doesn't already exist."""
        if not self.client.indices.exists(index=self.index_name):
            self.client.indices.create(
                index=self.index_name, mappings=self.get_index_mapping()
            )

    def index_document(self, doc: Document) -> None:
        """Index a document."""
        self.client.index(index=self.index_name, body=doc.to_es_dict())

    def _process_search_results(self, response: dict) -> list[str]:
        """Extract filenames and build Document objects from search response."""
        files = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            filename = source["filename"]
            self.file_cache[filename] = Document.from_es_dict(source)
            files.append(filename)
        return files

    def get_file_metadata(self, filenames: list[str]) -> dict[str, Document]:
        """Get Document objects for the given filenames from the cache."""
        return {
            fname: self.file_cache[fname]
            for fname in filenames
            if fname in self.file_cache
        }

    def add_file_to_cache(self, filename: str, file_obj: Document) -> None:
        """Add a file to the cache."""
        self.file_cache[filename] = file_obj

    def search(self, query: dict, knn: dict | None = None) -> dict:
        """Search the index with the given query and optional KNN parameters."""
        search_params = {
            "index": self.index_name,
            "query": query,
        }
        if knn is not None:
            search_params["knn"] = knn
        return self.client.search(**search_params)
