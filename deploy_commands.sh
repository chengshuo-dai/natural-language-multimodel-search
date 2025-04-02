#!/bin/bash

# Use DOCKER_USERNAME from environment variable
: "${DOCKER_USERNAME:=jdedward}"

# Remove existing containers if they exist
if docker ps -a | grep -q elasticsearch; then
    docker rm -f elasticsearch
fi

echo "Starting Elasticsearch..."
docker run -d \
    --name elasticsearch \
    --network elastic \
    --restart unless-stopped \
    -p 9200:9200 \
    docker.elastic.co/elasticsearch/elasticsearch:8.17.2

# Wait for Elasticsearch to start
echo "Waiting for Elasticsearch to start..."
sleep 30

# Pull and run nls-app
echo "Starting nls-app..."
docker run -d \
    --name nls-app \
    --network elastic \
    --restart unless-stopped \
    -p 8000:8000 \
    --env-file .env \
    -e ELASTICSEARCH_HOST=elasticsearch \
    -e ELASTICSEARCH_PORT=9200 \
    $DOCKER_USERNAME/nls-app:latest

# Run indexing process inside the nls-app container
echo "Starting data indexing..."
docker exec nls-app python processor/process_files.py sample_folder

# Show container status
docker ps 