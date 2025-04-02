#!/bin/bash

# Configuration
DOCKER_USERNAME="jdedward"  # Default username, can be overridden
SKIP_BUILD=false  # Default to not skipping build

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --docker-user) DOCKER_USERNAME="$2"; shift ;;
        --skip-build) SKIP_BUILD=true ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Build and push Docker image (unless skipped)
if [ "$SKIP_BUILD" = false ]; then
    echo "Building and pushing Docker image..."
    docker build -t $DOCKER_USERNAME/nls-app:latest .
    docker push $DOCKER_USERNAME/nls-app:latest
else
    echo "Skipping Docker build and push..."
fi

# Run deployment commands
echo "Starting deployment..."
DOCKER_USERNAME=$DOCKER_USERNAME ./deploy_commands.sh

echo "Deployment complete!" 