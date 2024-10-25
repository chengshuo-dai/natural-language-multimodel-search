import asyncio
import os

import chainlit as cl
from chainlit.input_widget import Select
from dotenv import load_dotenv
from search import natural_language_search


@cl.on_chat_start
async def start():
    await cl.Message(content="Hello! How can I assist you today?").send()


@cl.on_message
async def main(message: cl.Message):
    # Start a loading status indicator
    async with cl.Step("Processing your query..."):
        await time_consuming_function(message.content)


async def time_consuming_function(user_input: str) -> None:
    # Load the environment variables
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(
        None, natural_language_search, user_input, openai_api_key
    )

    if results.result_type == "search":
        if len(results.files) == 0:
            await cl.Message(content="No results found.").send()
        else:
            elements = [
                cl.Text(content=result, name=f"Result {i+1}", display="inline")
                for i, result in enumerate(results.files)
            ]
            await cl.Message(
                content="Here are the search results:", elements=elements
            ).send()
    else:
        await cl.Message(content=results.answer).send()


if __name__ == "__main__":
    cl.run()
