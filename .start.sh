#!/bin/bash

# Real Estate Assistant Docker Start Script
# This script builds and runs the Docker container for the Real Estate Valuation Agent

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_IMAGE_NAME="realestate-assistant"
DOCKER_CONTAINER_NAME="realestate-assistant-app"
DOCKERFILE_PATH="./Dockerfile"

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Real Estate Valuation Assistant - Docker Start Script${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not installed${NC}"
    echo "Please install Docker from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo -e "${GREEN}✓ Docker is installed${NC}\n"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found${NC}"
    echo -e "${YELLOW}You need to create .env with GROQ_API_KEY:${NC}\n"
    cat << 'EOF'
    Create a .env file with:
    ├── GROQ_API_KEY=your_groq_api_key_here
    └── (other optional variables)

EOF
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Aborted${NC}"
        exit 1
    fi
fi

# Check if Dockerfile exists
if [ ! -f "$DOCKERFILE_PATH" ]; then
    echo -e "${RED}❌ Error: Dockerfile not found at $DOCKERFILE_PATH${NC}"
    exit 1
fi

echo -e "${YELLOW}Building Docker image: $DOCKER_IMAGE_NAME${NC}\n"

# Build Docker image
docker build -t "$DOCKER_IMAGE_NAME" -f "$DOCKERFILE_PATH" . || {
    echo -e "${RED}❌ Failed to build Docker image${NC}"
    exit 1
}

echo -e "\n${GREEN}✓ Docker image built successfully${NC}\n"

# Stop and remove existing container if it exists
if [ "$(docker ps -aq -f name=$DOCKER_CONTAINER_NAME)" ]; then
    echo -e "${YELLOW}Stopping and removing existing container...${NC}"
    docker stop "$DOCKER_CONTAINER_NAME" 2>/dev/null || true
    docker rm "$DOCKER_CONTAINER_NAME" 2>/dev/null || true
    echo -e "${GREEN}✓ Old container cleaned up${NC}\n"
fi

echo -e "${YELLOW}Starting container: $DOCKER_CONTAINER_NAME${NC}\n"

# Run Docker container
docker run \
    --name "$DOCKER_CONTAINER_NAME" \
    --env-file .env \
    -v "$(pwd)":/app \
    -it \
    "$DOCKER_IMAGE_NAME"

echo -e "\n${GREEN}✓ Container execution completed${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"
