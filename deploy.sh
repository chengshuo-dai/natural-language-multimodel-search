#!/bin/bash

# Configuration
EC2_KEY="~/aws_keys/nls_deploy.pem"
EC2_USER="ec2-user"
EC2_IP="34.222.12.60"
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

# Transfer configuration files
echo "Transferring files to EC2..."
scp -i $EC2_KEY \
    .env \
    deploy_commands.sh \
    $EC2_USER@$EC2_IP:~/

echo "Deployment files transferred!"

# Execute commands on EC2
echo "Deploying on EC2..."
ssh -i $EC2_KEY $EC2_USER@$EC2_IP "DOCKER_USERNAME=$DOCKER_USERNAME bash -s" << 'EOF'
chmod +x deploy_commands.sh
./deploy_commands.sh
EOF

echo "Deployment complete!" 