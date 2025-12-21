import datetime
import os
import warnings

import rich
import typer
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from rich.progress import Progress

from data.data import Document
from model.sbert_model import SBertModel
from processor.handlers import (
    AudioFileHandler,
    ImageFileHandler,
    PDFFileHandler,
    TextFileHandler,
    VideoFileHandler,
)

load_dotenv()

os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

elasticsearch_host = os.getenv("ELASTICSEARCH_HOST", "localhost")
elasticsearch_port = os.getenv("ELASTICSEARCH_PORT", "9200")
ES_URL = f"http://{elasticsearch_host}:{elasticsearch_port}/"
ES = Elasticsearch(ES_URL)

INDEX_NAME = os.getenv("ELASTICSEARCH_INDEX_NAME", "nls")

# Build extension-to-handler mapping from handlers (single source of truth)
EXTENSION_TO_HANDLER = {}
for handler in [
    TextFileHandler,
    ImageFileHandler,
    PDFFileHandler,
    AudioFileHandler,
    VideoFileHandler,
]:
    for ext in handler.get_supported_extensions():
        EXTENSION_TO_HANDLER[ext] = handler


def load_required_models(extensions: set[str]) -> None:
    """Load all required models for the given extensions."""
    required_models = set()
    for extension in extensions:
        handler_class = EXTENSION_TO_HANDLER.get(extension)
        if handler_class:
            required_models.update(handler_class.get_required_models())

    # Load each model (they use singleton pattern, so this is safe)
    for model_class in required_models:
        model_class.get_instance()


def get_supported_files(folder_path: str) -> tuple[list[str], list[str]]:
    """Get files that can be processed and files that will be skipped."""
    supported_files = []
    skipped_files = []

    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            extension = os.path.splitext(file)[1].lower()
            if extension in EXTENSION_TO_HANDLER:
                supported_files.append(file_path)
            else:
                skipped_files.append(file_path)

    return supported_files, skipped_files


def index_file(doc: Document) -> None:
    """Index a document in Elasticsearch."""
    ES.index(index=INDEX_NAME, body=doc.to_index_body())


def process_file(file_path: str) -> Document:
    """Process a single file using the appropriate handler."""
    extension = os.path.splitext(file_path)[1].lower()
    handler_class = EXTENSION_TO_HANDLER.get(extension)

    if not handler_class:
        raise ValueError(f"No handler found for extension: {extension}")

    return handler_class.process_file(file_path)


def process_files(folder_path: str) -> None:
    """Process all supported files in the specified folder."""
    # Get files we can process and files we'll skip
    supported_files, skipped_files = get_supported_files(folder_path)

    if not supported_files and not skipped_files:
        rich.print("[yellow]No files found in the specified folder.[/yellow]")
        return

    if not supported_files:
        rich.print("[yellow]No supported files found in the specified folder.[/yellow]")
        if skipped_files:
            rich.print(
                f"[yellow]Found {len(skipped_files)} unsupported files.[/yellow]"
            )
        return

    # Get extensions of files we'll process
    extensions_to_process = {os.path.splitext(f)[1].lower() for f in supported_files}

    # Load all required models upfront
    rich.print("[yellow]Loading required models...[/yellow]")
    load_required_models(extensions_to_process)
    rich.print("[green]All models loaded successfully![/green]\n")

    # Process files with progress tracking
    processed = []
    with Progress() as progress:
        task = progress.add_task("Processing files...", total=len(supported_files))

        for file_path in supported_files:
            filename = os.path.basename(file_path)
            # Print status on a separate line
            rich.print(f"[blue]Processing: {filename}[/blue]")

            try:
                doc = process_file(file_path)
                index_file(doc)
                processed.append(file_path)
            except Exception as e:
                rich.print(f"[red]Error processing {filename}: {e}[/red]")

            progress.update(task, advance=1)

    # Refresh index once at the end
    ES.indices.refresh(index=INDEX_NAME)

    rich.print(f"[green bold]Processed {len(processed)} files.[/green bold]")
    if skipped_files:
        rich.print(
            f"[yellow bold]Skipped {len(skipped_files)} unsupported files.[/yellow bold]"
        )


def get_index_mapping():
    """Get the index mapping with the correct embedding dimensions."""
    return {
        "properties": {
            "filename": {"type": "text", "analyzer": "english"},
            "extension": {"type": "text"},
            "text": {"type": "text", "analyzer": "english"},
            "created": {"type": "date"},
            "embedding": {
                "type": "dense_vector",
                "dims": SBertModel.get_dimension(),
                "index": True,
                "similarity": "cosine",
            },
            "metadata": {"type": "object", "enabled": False},
        }
    }


def main(
    folder_path: str = typer.Option(
        ..., "--folder_path", "-f", help="The path to the folder to process."
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", "-o", help="Overwrite the index if it already exists."
    ),
):
    """Process a folder of files and index them in Elasticsearch."""
    if overwrite:
        rich.print("[red]Overwriting the index...[/red]")
        if ES.indices.exists(index=INDEX_NAME):
            ES.indices.delete(index=INDEX_NAME)

    # Create the index if it doesn't exist
    if not ES.indices.exists(index=INDEX_NAME):
        ES.indices.create(index=INDEX_NAME, mappings=get_index_mapping())

    process_files(folder_path)


if __name__ == "__main__":
    typer.run(main)
