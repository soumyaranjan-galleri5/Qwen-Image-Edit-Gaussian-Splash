# RunPod Serverless Dockerfile for ComfyUI with 4K Mask Preserve Workflow
FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    COMFYUI_PATH=/workspace/ComfyUI

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    git-lfs \
    wget \
    curl \
    aria2 \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (these persist in the image)
RUN pip install --upgrade pip && \
    pip install \
    runpod \
    requests \
    pillow \
    numpy \
    opencv-python-headless \
    onnxruntime-gpu \
    segment-anything \
    groundingdino-py \
    huggingface_hub \
    safetensors \
    accelerate \
    transformers \
    sentencepiece \
    gguf \
    aiohttp \
    einops \
    kornia \
    spandrel \
    torchsde

# Copy handler and scripts
COPY handler.py /handler.py
COPY start.sh /start.sh

RUN chmod +x /start.sh

# Set the handler as entrypoint
CMD ["/start.sh"]