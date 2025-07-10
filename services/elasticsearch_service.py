from elasticsearch import Elasticsearch

from data.data import File


class ElasticsearchService:
    """Service class for Elasticsearch operations."""

    _instance = None

    @classmethod
    def _get_instance(
        cls, host: str = "localhost", port: str = "9200", index_name: str = "nls"
    ):
        """Get the singleton instance, initializing it if needed."""
        if cls._instance is None:
            cls._instance = cls(host, port, index_name)
        return cls._instance

    @classmethod
    def get_instance(
        cls, host: str = "localhost", port: str = "9200", index_name: str = "nls"
    ):
        """Public method to get the service instance."""
        return cls._get_instance(host, port, index_name)

    def __init__(
        self, host: str = "localhost", port: str = "9200", index_name: str = "nls"
    ):
        self.url = f"http://{host}:{port}/"
        self.client = Elasticsearch(self.url)
        self.index_name = index_name
        # Cache for File objects - replaces the global FILE_BY_NAME
        self.file_cache: dict[str, File] = {}

    def _process_search_results(self, response: dict) -> list[str]:
        """Extract filenames and build File objects from search response."""
        files = []

        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            filename = source["filename"]

            file_obj = File.from_elasticsearch_source(source)

            self.file_cache[filename] = file_obj
            files.append(filename)

        return files

    def get_file_metadata(self, filenames: list[str]) -> dict[str, File]:
        """Get File objects for the given filenames from the cache."""
        return {
            fname: self.file_cache[fname]
            for fname in filenames
            if fname in self.file_cache
        }

    def add_file_to_cache(self, filename: str, file_obj: File) -> None:
        """Add a file to the cache."""
        self.file_cache[filename] = file_obj
