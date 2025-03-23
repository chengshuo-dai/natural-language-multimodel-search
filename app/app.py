import asyncio
import datetime

import chainlit as cl
from chainlit.element import Element
from search import File, natural_language_search


def _get_file_element(file_meta: File) -> Element:
    element_cls_by_ext = {
        ".pdf": cl.Pdf,
        ".txt": cl.Text,
        ".mp3": cl.Audio,
        ".jpg": cl.Image,
        ".jpeg": cl.Image,
        ".png": cl.Image,
    }

    element_cls = element_cls_by_ext.get(file_meta.extension)
    if element_cls is None:
        raise ValueError(f"Unsupported file extension: {file_meta.extension}")

    return element_cls(path=file_meta.path, name=file_meta.filename, display="side")


async def time_consuming_function(user_input: str) -> None:
    result, file_metas = natural_language_search(user_input)

    if len(result.files) == 0 and result.result_type == "search":
        await cl.Message(content="No results found.").send()
        return

    elements = [_get_file_element(file_metas[result]) for result in result.files]

    # Build message content
    if result.result_type == "search":
        message_content = "Here are the search results:\n\n"
    else:
        message_content = f"{result.answer}\n\nSources:\n\n"

    # Add metadata table
    message_content += "| File | Size | Created |\n|------|------|---------|\n"

    for file in result.files:
        file_meta = file_metas[file]
        size_mb = f"{file_meta.size / (1024 * 1024):.2f} MB"
        created_dt = datetime.datetime.fromisoformat(file_meta.created).strftime(
            "%Y-%m-%d %H:%M"
        )
        message_content += f"| {file_meta.filename} | {size_mb} | {created_dt} |\n"

    await cl.Message(content=message_content, elements=elements).send()


@cl.on_chat_start
async def start():
    await cl.Message(content="Hello! How can I assist you today?").send()


@cl.on_message
async def main(message: cl.Message):
    # Start a loading status indicator
    async with cl.Step("Processing your query...") as step:
        await time_consuming_function(message.content)
        step.update("Processing completed")


if __name__ == "__main__":
    cl.run()
