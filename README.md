# natural_language_search

## Index Setup
Use the processor to process a folder of files and index them in Elasticsearch: `python processor/processor.py`. You only need to run this once.


![Processor Run Screenshot](/resources/processor_run_screenshot.png)

## Launch Chainlit App  

Go to the `app` directory and launch the Chainlit app: 

```bash
cd app && chainlit run app.py -w
```

The `-w` flag runs the app in watch mode, which allows you to edit the app and see the changes without restarting the app.