#!/bin/bash

# Configuration
EC2_KEY="~/aws_keys/nls_deploy.pem"
EC2_USER="ec2-user"
EC2_IP="34.222.12.60"

# Parse command line arguments
SKIP_BUILD=false
SKIP_UPLOAD=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --skip-build) SKIP_BUILD=true ;;
        --skip-upload) SKIP_UPLOAD=true ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

if [ "$SKIP_BUILD" = false ]; then
    # Local preparation, dump images to tar files
    echo "Saving container images..."
    docker commit elasticsearch es-with-data:latest
    docker save -o es-with-data.tar es-with-data:latest
    docker save -o nls-app.tar nls-app
fi

if [ "$SKIP_UPLOAD" = false ]; then
    # Transfer files from local to EC2
    echo "Transferring files to EC2..."
    scp -i $EC2_KEY \
        es-with-data.tar \
        nls-app.tar \
        .env \
        deploy_commands.sh \
        $EC2_USER@$EC2_IP:~/
fi

# Execute commands on EC2
echo "Deploying on EC2..."
ssh -i $EC2_KEY $EC2_USER@$EC2_IP "bash -s" << 'EOF'
chmod +x deploy_commands.sh
./deploy_commands.sh
EOF

if [ "$SKIP_BUILD" = false ]; then
    # Cleanup local tar files
    echo "Cleaning up local files..."
    rm es-with-data.tar nls-app.tar
fi

echo "Deployment complete!" 