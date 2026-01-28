import os
import warnings

import rich
import typer
from dotenv import load_dotenv
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

from data.data import Document
from handlers import (
    AudioFileHandler,
    ImageFileHandler,
    PDFFileHandler,
    TextFileHandler,
    VideoFileHandler,
)
from services.es_service import ElasticsearchService

load_dotenv()

os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

es_service = ElasticsearchService.get_instance(
    host=os.getenv("ELASTICSEARCH_HOST", "localhost"),
    port=os.getenv("ELASTICSEARCH_PORT", "9200"),
    index_name=os.getenv("ELASTICSEARCH_INDEX_NAME", "nls"),
)

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


def process_file(file_path: str) -> Document:
    """Process a single file using the appropriate handler."""
    extension = os.path.splitext(file_path)[1].lower()
    handler_class = EXTENSION_TO_HANDLER.get(extension)

    if not handler_class:
        raise ValueError(f"No handler found for extension: {extension}")

    return handler_class.process_file(file_path)


def main(
    folder_path: str = typer.Option(
        ..., "--folder-path", "-f", help="The path to the folder to process"
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", "-o", help="Overwrite the existing index"
    ),
):
    if overwrite:
        rich.print(f"[red]󰴀 Overwriting existing index...[/red]")
        es_service.overwrite_index()
    else:
        es_service.ensure_index_exists()

    supported_files, skipped_files = get_supported_files(folder_path)
    if skipped_files:
        rich.print(
            f"[red]󰒬 Skipped {len(skipped_files)} files that are not supported.[/red]"
        )

    processed = []
    with Progress(
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
    ) as progress:
        task = progress.add_task("Processing files", total=len(supported_files))
        for file_path in supported_files:
            filename = os.path.basename(file_path)
            progress.update(
                task, description=f"Processing [italic]'{filename}'[/italic]..."
            )
            document = process_file(file_path)
            es_service.index_document(document)
            processed.append(document)
            progress.update(task, advance=1, description="")

    rich.print(f"[green] Processed {len(processed)} files successfully.[/green]")


if __name__ == "__main__":
    typer.run(main)
