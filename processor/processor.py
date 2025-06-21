import datetime
import os
import warnings

import pytesseract
import rich
import typer
from elasticsearch import Elasticsearch
from pdf2image import convert_from_path
from PIL import Image
from rich.progress import Progress

from data.data import Document
from model.blip_model import BlipModel
from model.sbert import SBertModel
from model.whisper_model import WhisperModel

os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# This is just for illustration purposes.
# Expand the list to include more extensions and update the process_file function as needed.
VALID_FILE_EXTENSIONS = [".pdf", ".mp3", ".txt", ".png", ".jpg", ".jpeg"]

elasticsearch_host = os.getenv("ELASTICSEARCH_HOST", "localhost")
elasticsearch_port = os.getenv("ELASTICSEARCH_PORT", "9200")
ES_URL = f"http://{elasticsearch_host}:{elasticsearch_port}/"
ES = Elasticsearch(ES_URL)

INDEX_NAME = "nls"


def get_files_in_folder(folder_path: str) -> list[str]:
    """
    Get a list of all files within the specified folder.
    """
    file_list = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_list.append(os.path.join(root, file))
    return file_list


def index_file(doc: Document):
    ES.index(index=INDEX_NAME, body=doc.to_index_body())


def process_file(file_path: str) -> bool:
    """
    Process a single file. Returns True if the file was processed successfully, False otherwise.
    """
    if not file_path.lower().endswith(tuple(VALID_FILE_EXTENSIONS)):
        return False

    # Get basic file metadata
    filename = os.path.basename(file_path)
    extension = os.path.splitext(file_path)[1].lower()

    text = ""
    if extension in [".txt"]:
        # Pure text files
        with open(file_path, "r") as f:
            text = f.read()
    elif extension in [".mp3"]:
        # Audio files
        text = WhisperModel.transcribe(file_path)["text"]
    elif extension in [".png", ".jpg", ".jpeg"]:
        # We get both the image description and the image caption, and concatenate them
        image = Image.open(file_path).convert("RGB")

        # Get the image description using BLIP
        description = BlipModel.generate_caption(image)

        # Get the image caption using OCR
        ocr_result = pytesseract.image_to_string(image)
        text = f"{description}\n{ocr_result}"
    elif extension in [".pdf"]:
        # PDF files
        pages = convert_from_path(file_path)
        pdf_page_texts = [
            pytesseract.image_to_string(page.convert("RGB")) for page in pages
        ]
        text = "\n".join(pdf_page_texts)
    else:
        raise ValueError(f"Unsupported file extension: {extension}")

    embedding = SBertModel.get_embedding(text)

    doc = Document(
        filename=filename,
        text=text,
        extension=extension,
        created=datetime.datetime.fromtimestamp(os.path.getmtime(file_path)),
        size=os.path.getsize(file_path),
        path=file_path,
        embedding=embedding,
    )
    index_file(doc)

    ES.indices.refresh(index=INDEX_NAME)

    return True


def process_files(folder_path: str):
    """
    Process all files in the specified folder using the given process function.
    """
    files = get_files_in_folder(folder_path)
    skipped = []
    processed = []

    with Progress() as progress:
        task = progress.add_task("Processing files...", total=len(files))

        for file_path in files:
            success = process_file(file_path)
            if not success:
                skipped.append(file_path)
            else:
                processed.append(file_path)
            progress.update(task, advance=1)

    rich.print(f"[green bold]Processed {len(processed)} files.[/green bold]")
    rich.print(f"[yellow bold]Skipped {len(skipped)} files.[/yellow bold]")


def get_index_mapping():
    """
    Get the index mapping with the correct embedding dimensions.
    """
    return {
        "properties": {
            "filename": {"type": "text", "analyzer": "english"},
            "extension": {"type": "text"},
            "text": {"type": "text", "analyzer": "english"},
            "created": {"type": "date"},
            "embedding": {
                "type": "dense_vector",
                "dims": SBertModel.get_dimension(),
                "index": True,  # required for similarity search
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
    """
    Process a folder of files and index them in Elasticsearch.
    """
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
