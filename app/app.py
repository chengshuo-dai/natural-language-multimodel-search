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
        # Simulate a time-consuming function (replace this with your actual function later)
        response = await time_consuming_function(message.content)

    # Send the response back to the user
    await cl.Message(content=response).send()


async def time_consuming_function(user_input: str) -> str:
    # Load the environment variables
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(
        None, natural_language_search, user_input, openai_api_key
    )

    if len(results) == 0:
        return "No results found."

    elements = [
        cl.Text(content=result, name=f"Result {i+1}", display="inline")
        for i, result in enumerate(results)
    ]
    # Send the Select element
    await cl.Message(
        content="Here are the search results: Result 1, Result 2, Result 3, etc.",
        elements=elements,
    ).send()

    return "Search completed. See the results above."


if __name__ == "__main__":
    cl.run()
