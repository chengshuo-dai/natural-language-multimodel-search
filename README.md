# natural_language_search

This is a simple app that allows you to search for files using natural language. It has the following features:
- Semantic search on files by name and content
- Time-ranged search on files by creation date: e.g., "pdfs I created in 2023", "photos I added last week"
- Question answering about the contents of a file: e.g., "how much did i spent in SFO?"

Here is a demo video: https://capture.dropbox.com/vCuBkYtP40yWUXc9

## Virtual Environment

Install necessary packages: 

```bash
pip install -r requirements.txt
```

The `requirements.txt` file is generated with `pipreqs`. This requirement file is compatible with python 3.10. If you run into any issues with other python versions, you can manually install the latest version of the packages in the `requirements.txt` file by following the specific package installation instructions.

## Index Setup
Use the processor to process a folder of files and index them in Elasticsearch: `python processor/processor.py`. You only need to run this once.

![Processor Run Screenshot](/resources/processor_run_screenshot.png)

## Setup OpenAI API Key

Create a `.env` file in the `app` directory with your OpenAI API key:   

```
OPENAI_API_KEY=sk-...
```

## Launch Chainlit App  

Go to the `app` directory and launch the Chainlit app: 

```bash
cd app && chainlit run app.py -w
```

The `-w` flag runs the app in watch mode, which allows you to edit the app and see the changes without restarting the app.
