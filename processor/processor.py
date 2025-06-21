import datetime
import os
import warnings

import pytesseract
import rich
import typer
import whisper
from elasticsearch import Elasticsearch
from pdf2image import convert_from_path
from PIL import Image
from rich.progress import Progress
from transformers import BlipForConditionalGeneration, BlipProcessor

from data.data import Document
from model.sbert import SBertModel

os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# This is just for illustration purposes.
# Expand the list to include more extensions and update the process_file function as needed.
VALID_FILE_EXTENSIONS = [".pdf", ".mp3", ".txt", ".png", ".jpg", ".jpeg"]


WHISPER_MODEL = whisper.load_model("base")

BLIP_PROCESSOR = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
BLIP_MODEL = BlipForConditionalGeneration.from_pretrained(
    "Salesforce/blip-image-captioning-base"
)

elasticsearch_host = os.getenv("ELASTICSEARCH_HOST", "localhost")
elasticsearch_port = os.getenv("ELASTICSEARCH_PORT", "9200")
ES_URL = f"http://{elasticsearch_host}:{elasticsearch_port}/"
ES = Elasticsearch(ES_URL)

INDEX_NAME = "nls"
INDEX_MAPPING = {
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
        rich.print(f"[yellow]Skipping file: {file_path}[/yellow]")
        return False

    rich.print(f"[blue]Processing file: {file_path}[/blue]")

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
        text = WHISPER_MODEL.transcribe(file_path)["text"]
    elif extension in [".png", ".jpg", ".jpeg"]:
        # We get both the image description and the image caption, and concatenate them
        image = Image.open(file_path).convert("RGB")

        # Get the image description
        inputs = BLIP_PROCESSOR(image, return_tensors="pt")
        out = BLIP_MODEL.generate(**inputs, max_new_tokens=400)
        description = BLIP_PROCESSOR.decode(out[0], skip_special_tokens=True)

        # Get the image caption
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

    with Progress() as progress:
        task = progress.add_task("Processing files...", total=len(files))

        for file_path in files:
            success = process_file(file_path)
            if not success:
                skipped.append(file_path)
            progress.update(task, advance=1)

    rich.print(f"[yellow]Skipped {len(skipped)} files.[/yellow]")
    rich.print("[green bold]Done[/green bold]")


def main(
    folder_path: str = typer.Argument(..., help="The path to the folder to process."),
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
        ES.indices.create(index=INDEX_NAME, mappings=INDEX_MAPPING)

    process_files(folder_path)


if __name__ == "__main__":
    typer.run(main)
