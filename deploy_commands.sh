#!/bin/bash

# Remove existing containers if they exist (suppress errors if they don't)
if docker ps -a | grep -q elasticsearch; then
    docker rm -f elasticsearch
fi

if docker ps -a | grep -q nls-app; then
    docker rm -f nls-app
fi

# Load images
echo "Loading images..."
docker load < es-with-data.tar
docker load < nls-app.tar

# Create network if it doesn't exist
echo "Creating network..."
docker network create elastic || true

# Run Elasticsearch
echo "Starting Elasticsearch..."
docker run -d \
    --name elasticsearch \
    --network elastic \
    --restart unless-stopped \
    -p 9200:9200 \
    es-with-data:latest

# Wait for Elasticsearch to start
echo "Waiting for Elasticsearch to start..."
sleep 30

# Run nls-app
echo "Starting nls-app..."
docker run -d \
    --name nls-app \
    --network elastic \
    --restart unless-stopped \
    -p 8000:8000 \
    --env-file .env \
    -e ELASTICSEARCH_HOST=elasticsearch \
    -e ELASTICSEARCH_PORT=9200 \
    nls-app:latest

# Show container status
docker ps 