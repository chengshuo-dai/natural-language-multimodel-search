FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make sure the app uses environment variables for ES connection
ENV ELASTICSEARCH_HOST=elasticsearch
ENV ELASTICSEARCH_PORT=9200

# Update the CMD to use chainlit
CMD ["chainlit", "run", "app.py", "--port", "8000"] 