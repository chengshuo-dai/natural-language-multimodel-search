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

![Processor Run Screenshot](/app/resources/processor_run_screenshot.png)

## Setup OpenAI API Key

Create a `.env` file in the `app` directory with your OpenAI API key:   

```
OPENAI_API_KEY=sk-...
```

## Launch Chainlit App (for development)

Go to the `app` directory and launch the Chainlit app: 

```bash
cd app && chainlit run app.py -w
```

The `-w` flag runs the app in watch mode, which allows you to edit the app and see the changes without restarting the app.


## Launch Chainlit App (for production)

Go to the `app` directory and launch the Chainlit app with `pm2`:

```bash
cd app && pm2 start "chainlit run app.py --port 8000" --name chainlit
```

This will start the Chainlit app on port 8000 and name the process `chainlit`.

To stop the Chainlit app, run:

```bash
pm2 stop chainlit
```

To check the status of the Chainlit app, run:

```bash
pm2 status chainlit
```

To check the logs of the Chainlit app, run:

```bash
pm2 logs chainlit
```

This is helpful in case you run into any issues launching the app and stuck in a restart loop.

## Expose Chainlit App to the internet

If you do own a domain, you can expose the Chainlit app to the internet by adding a Caddyfile to the `app` directory with the following content:

```
your-domain.com {
    reverse_proxy localhost:8000
}
```

If you do not own a domain, you can use [ngrok](https://ngrok.com/) to expose the Chainlit app to the internet.

```bash
ngrok http 8000
```

This will start a ngrok tunnel on port 8000 and expose the Chainlit app to the internet. You can then access the Chainlit app at `https://<ngrok-url>`.

To run ngrok in the background, you can use `nohup`:

```bash
nohup ngrok http 8000 > /dev/null 2>&1 &
```

Then you need to fetch the url from the ngrok endpoint dashboard: https://dashboard.ngrok.com/endpoints

To stop the ngrok tunnel, you can use `pkill`:

```bash
pkill ngrok
```

Alternatively, you could use tmux to run the ngrok tunnel in the background.