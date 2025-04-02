#!/bin/bash

# Use DOCKER_USERNAME from environment variable
: "${DOCKER_USERNAME:=jdedward}"

# Remove existing containers if they exist
if docker ps -a | grep -q elasticsearch; then
    docker rm -f elasticsearch
fi

if docker ps -a | grep -q nls-app; then
    docker rm -f nls-app
fi

# Create network if it doesn't exist
echo "Creating network..."
docker network create elastic || true

# Pull and run Elasticsearch
echo "Starting Elasticsearch..."
docker run -d \
    --name elasticsearch \
    --network elastic \
    --restart unless-stopped \
    -p 9200:9200 \
    -e "discovery.type=single-node" \
    -e "xpack.security.enabled=false" \
    -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
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

# Wait a bit for nls-app to start
sleep 30

# Run indexing process inside the nls-app container
echo "Starting data indexing..."
docker exec -e PYTHONPATH=/app nls-app python /app/processor/processor.py --folder_path /app/sample_folder

# Show container status
docker ps 