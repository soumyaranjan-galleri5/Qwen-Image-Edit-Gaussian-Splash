#!/bin/bash
set -e

echo "=========================================="
echo "Starting ComfyUI RunPod Serverless Worker"
echo "=========================================="

# Symlink /workspace to network volume
echo ""
echo "Checking volume mounts..."
echo "  /runpod-volume exists: $([ -d /runpod-volume ] && echo 'YES' || echo 'NO')"
echo "  /workspace exists: $([ -d /workspace ] && echo 'YES' || echo 'NO')"

if [ -d "/runpod-volume" ]; then
    echo "Symlinking files from Network Volume"
    rm -rf /workspace && \
      ln -s /runpod-volume /workspace
    echo "  Contents of /runpod-volume:"
    ls /runpod-volume/ 2>/dev/null || echo "  (empty or not accessible)"
else
    echo "[WARN] /runpod-volume not found, checking /workspace directly..."
    echo "  Contents of /workspace:"
    ls /workspace/ 2>/dev/null || echo "  (empty or not accessible)"
fi

# Verify ComfyUI is accessible
if [ -d "/workspace/ComfyUI" ]; then
    echo "[OK] ComfyUI accessible at /workspace/ComfyUI"
else
    echo ""
    echo "=========================================="
    echo "[ERROR] ComfyUI not found at /workspace/ComfyUI"
    echo "=========================================="
    echo ""
    echo "Debug info:"
    echo "  /runpod-volume contents:"
    ls -la /runpod-volume/ 2>/dev/null || echo "    (not accessible)"
    echo "  /workspace contents:"
    ls -la /workspace/ 2>/dev/null || echo "    (not accessible)"
    echo "  Mount points:"
    df -h 2>/dev/null | head -20
    echo ""
    echo "Make sure your RunPod network volume has ComfyUI installed."
    exit 1
fi

# Activate virtual environment
if [ -d "/workspace/pytenvenv/" ]; then
    echo "[OK] Activating virtual environment"
    source /workspace/pytenvenv/bin/activate
else
    echo "[WARN] Virtual environment not found at /workspace/pytenvenv"
fi

# Create log file
LOG_FILE="/workspace/comfy.log"
echo "Logging ComfyUI output to $LOG_FILE"

# Start ComfyUI server in background with logging
echo ""
echo "Starting ComfyUI server..."
cd /workspace/ComfyUI
python main.py --cuda-device 0 --listen 0.0.0.0 --port 8188 --disable-auto-launch >> "$LOG_FILE" 2>&1 &

# Wait for ComfyUI server to be fully ready (10 minutes = 600 seconds)
echo "Waiting for ComfyUI server to be ready (up to 10 minutes)..."
MAX_WAIT=600
ELAPSED=0
INTERVAL=10

echo "MAX_WAIT is $MAX_WAIT seconds"

# Stage 1: Wait for server to respond
echo ""
echo "Stage 1: Waiting for ComfyUI server to start..."
while [ $ELAPSED -lt $MAX_WAIT ]; do
    if curl -s http://127.0.0.1:8188/system_stats > /dev/null 2>&1; then
        echo "  [OK] Server is responding after ${ELAPSED}s"
        break
    fi
    ELAPSED=$((ELAPSED + INTERVAL))
    REMAINING=$((MAX_WAIT - ELAPSED))
    echo "  Waiting for server... (${ELAPSED}s elapsed, ${REMAINING}s remaining)"
    sleep $INTERVAL
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo ""
    echo "=========================================="
    echo "[ERROR] ComfyUI server FAILED to start!"
    echo "  Timeout after $MAX_WAIT seconds"
    echo "=========================================="
    echo ""
    echo "Last 50 lines of log:"
    tail -50 "$LOG_FILE"
    exit 1
fi

# Stage 2: Wait for ComfyUI-Manager to complete all startup tasks
echo ""
echo "Stage 2: Waiting for ComfyUI-Manager to complete startup tasks..."
REGISTRY_WAIT=300
REGISTRY_ELAPSED=0

while [ $REGISTRY_ELAPSED -lt $REGISTRY_WAIT ]; do
    # Check if ComfyUI-Manager has finished all startup tasks
    if grep -q "All startup tasks have been completed" "$LOG_FILE" 2>/dev/null; then
        echo "  [OK] All startup tasks completed after ${REGISTRY_ELAPSED}s"
        break
    fi

    # Show current registry loading status from log
    REGISTRY_STATUS=$(grep -o "FETCH ComfyRegistry Data: [0-9]*/[0-9]*" "$LOG_FILE" 2>/dev/null | tail -1)
    if [ -n "$REGISTRY_STATUS" ]; then
        echo "  Loading: $REGISTRY_STATUS (${REGISTRY_ELAPSED}s elapsed)"
    elif grep -q "FETCH ComfyRegistry Data \[DONE\]" "$LOG_FILE" 2>/dev/null; then
        echo "  Registry data loaded, waiting for Manager... (${REGISTRY_ELAPSED}s elapsed)"
    else
        echo "  Waiting for startup tasks... (${REGISTRY_ELAPSED}s elapsed)"
    fi

    REGISTRY_ELAPSED=$((REGISTRY_ELAPSED + INTERVAL))
    sleep $INTERVAL
done

if [ $REGISTRY_ELAPSED -ge $REGISTRY_WAIT ]; then
    echo ""
    echo "[WARN] Startup tasks timed out, proceeding anyway..."
fi

echo ""
echo "=========================================="
echo "[OK] ComfyUI server is READY!"
echo "  Total startup time: $((ELAPSED + REGISTRY_ELAPSED)) seconds"
echo "=========================================="

# Start the RunPod handler (use system Python where runpod is installed)
echo "Starting RunPod handler..."
pwd
cd ../../
pwd
[ -f "handler.py" ] && echo "File exists." || echo "File does not exist."
/usr/bin/python3 /handler.py