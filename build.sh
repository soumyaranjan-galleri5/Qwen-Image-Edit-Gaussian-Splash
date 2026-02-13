#!/bin/bash
# Docker build script for ComfyUI RunPod Serverless

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
IMAGE_NAME="qwen-image-edit-splash"
TAG="latest"
REGISTRY="srmahapatra95"
PUSH=true
NO_CACHE=false

# Help message
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Build Docker image for ComfyUI RunPod Serverless"
    echo ""
    echo "Options:"
    echo "  -n, --name NAME       Image name (default: comfyui-serverless)"
    echo "  -t, --tag TAG         Image tag (default: latest)"
    echo "  -r, --registry REG    Docker registry (e.g., dockerhub-user, ghcr.io/user)"
    echo "  -p, --push            Push image to registry after build"
    echo "  --no-cache            Build without using cache"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Build locally"
    echo "  $0 -t v1.0.0                          # Build with tag"
    echo "  $0 -r myuser -p                       # Build and push to Docker Hub"
    echo "  $0 -r ghcr.io/myuser -t v1.0.0 -p    # Build and push to GitHub Registry"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -p|--push)
            PUSH=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Build full image name
if [ -n "$REGISTRY" ]; then
    FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${TAG}"
else
    FULL_IMAGE="${IMAGE_NAME}:${TAG}"
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  ComfyUI Serverless Docker Build${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Image:${NC} $FULL_IMAGE"
echo -e "${YELLOW}Push:${NC} $PUSH"
echo -e "${YELLOW}No Cache:${NC} $NO_CACHE"
echo ""

# Build command - use buildx for multi-platform support (required for RunPod linux/amd64)
BUILD_CMD="docker buildx build --platform linux/amd64"

if [ "$NO_CACHE" = true ]; then
    BUILD_CMD="$BUILD_CMD --no-cache"
fi

if [ "$PUSH" = true ]; then
    BUILD_CMD="$BUILD_CMD --push"
else
    BUILD_CMD="$BUILD_CMD --load"
fi

BUILD_CMD="$BUILD_CMD -t $FULL_IMAGE ."

# Also tag as latest if building a versioned tag
if [ "$TAG" != "latest" ] && [ -n "$REGISTRY" ]; then
    LATEST_IMAGE="${REGISTRY}/${IMAGE_NAME}:latest"
    BUILD_CMD="$BUILD_CMD -t $LATEST_IMAGE"
fi

# Run build
echo -e "${GREEN}Building image...${NC}"
echo -e "${YELLOW}$ $BUILD_CMD${NC}"
echo ""

eval $BUILD_CMD

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}Build successful!${NC}"
else
    echo ""
    echo -e "${RED}Build failed!${NC}"
    exit 1
fi

# Note: Push is handled by buildx --push flag above
if [ "$PUSH" = true ]; then
    echo ""
    echo -e "${GREEN}Image pushed to registry!${NC}"
fi

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Done!${NC}"
echo ""
echo "Image: $FULL_IMAGE"
if [ "$TAG" != "latest" ] && [ -n "$REGISTRY" ]; then
    echo "Also tagged as: $LATEST_IMAGE"
fi
echo ""
echo "To run locally:"
echo "  docker run --gpus all -p 8188:8188 $FULL_IMAGE"
echo ""
if [ "$PUSH" = false ] && [ -n "$REGISTRY" ]; then
    echo "To push to registry:"
    echo "  docker push $FULL_IMAGE"
fi