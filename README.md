# natural_language_search

## Virtual Environment

Install necessary packages: 

```bash
pip install -r requirements.txt
```

The `requirements.txt` file is generated with `pipreqs`. If you run into any issues, you can manually install the packages in the `requirements.txt` file by following the specific package installation instructions.

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