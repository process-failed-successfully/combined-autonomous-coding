#!/bin/bash

# Resolve project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# --- Image Selection ---
IMAGE_KEY="default"
ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --image)
            IMAGE_KEY="$2"
            shift # past argument
            shift # past value
            ;;
        *)
            ARGS+=("$1")
            shift # past argument
            ;;
    esac
done

# Restore args (without --image)
set -- "${ARGS[@]}"

# Resolve Dockerfile path from manifest
MANIFEST_PATH="$SCRIPT_DIR/images/manifest.json"
if [ ! -f "$MANIFEST_PATH" ]; then
    echo "❌ Error: Manifest file not found at $MANIFEST_PATH"
    exit 1
fi

# Use python to parse json (avoids jq dependency)
DOCKERFILE_REL_PATH=$(python3 -c "import sys, json; print(json.load(open('$MANIFEST_PATH')).get('$IMAGE_KEY', ''))")

if [ -z "$DOCKERFILE_REL_PATH" ]; then
    # Check if the key provided is actually a path to a custom Dockerfile
    if [ -f "$IMAGE_KEY" ]; then
        echo "🤔 Key '$IMAGE_KEY' not found in manifest, but file exists."
        # Resolve absolute path for consistent usage
        DOCKERFILE_PATH=$(readlink -f "$IMAGE_KEY")
    elif [ -f "$PROJECT_ROOT/$IMAGE_KEY" ]; then
        echo "🤔 Key '$IMAGE_KEY' not found in manifest, but found relative to project root."
        DOCKERFILE_PATH=$(readlink -f "$PROJECT_ROOT/$IMAGE_KEY")
    else
        echo "❌ Error: Invalid image key '$IMAGE_KEY'. Not found in manifest and not a valid file."
        exit 1
    fi
else
    DOCKERFILE_PATH="$SCRIPT_DIR/$DOCKERFILE_REL_PATH"
fi

export DOCKERFILE_PATH
echo "🐳 Using Dockerfile: $DOCKERFILE_PATH"




# Create config dirs if they don't exist to avoid docker creating root-owned dirs on host
mkdir -p ~/.gemini
mkdir -p ~/.cursor
mkdir -p agents/logs

# Fix permissions using a temporary root container
# This ensures that even if files were previously created by root, they are now owned by the user (UID 1000)
echo "Ensuring correct permissions for config directories..."
docker run --rm \
    -v ~/.gemini:/gemini \
    -v ~/.cursor:/cursor \
    -v "$(pwd)/agents/logs":/agents_logs \
    busybox sh -c "chown -R 1000:1000 /gemini /cursor /agents_logs"
# Set workspace directory for docker-compose
export WORKSPACE_DIR="${WORKSPACE_DIR:-$(pwd)}"
export PROJECT_NAME="$(basename "$WORKSPACE_DIR")"
# Define a consistent container name for this project's agent run
export CONTAINER_NAME="${PROJECT_NAME}_agent_run"

# --- Pre-flight Checks ---

# 1. Check for Project Completion
if [ -f "$WORKSPACE_DIR/PROJECT_SIGNED_OFF" ]; then
    echo "✅ Project is marked as SIGNED OFF (PROJECT_SIGNED_OFF exists)."
    echo "   Remove this file if you wish to run the agent again."
    exit 0
fi

# 2. Check for Existing Container
# Check if a container with this name already exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "🔍 Found existing container: ${CONTAINER_NAME}"
    
    # Check if it is currently running
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "❌ Error: Agent is already running for this project!"
        echo "   Container Name: ${CONTAINER_NAME}"
        echo "   To force restart, stop the container manually: docker stop ${CONTAINER_NAME}"
        exit 1
    else
        echo "🧹 Removing stale container..."
        docker rm -f "${CONTAINER_NAME}" > /dev/null
    fi
fi

# --- Cleanup Trap ---
# Ensure we remove the container when this script exits (e.g. Ctrl-C)
cleanup() {
    echo ""
    echo "🛑 Stopping and cleaning up agent container..."
    docker rm -f "${CONTAINER_NAME}" > /dev/null 2>&1
}
trap cleanup EXIT INT TERM

echo "🚀 Launching Agent in Container (${CONTAINER_NAME})..."

# Check for --build flag
if [[ "$1" == "--build" ]]; then
    echo "Rebuilding container image..."
    docker compose -f "$SCRIPT_DIR/docker-compose.yml" build
    shift # Remove --build from args
fi

# Determine command
if [ "$#" -eq 0 ]; then
    # No args, use default command from docker-compose (python3 main.py)
    CMD=""
elif [[ "$1" == -* ]]; then
    # Args are flags, prepend main script
    CMD="python3 /app/combined-autonomous-coding/main.py $@"
else
    # Args are a custom command (e.g. bash, python3 -m unittest)
    CMD="$@"
fi


# Run with docker compose
# We use -f to point to the compose file in this directory
# We assume we run from the project root usually, but here we enforce context
# Run with docker compose
# We use -f to point to the compose file in this directory
# We assume we run from the project root usually, but here we enforce context
# Check if we should expose dashboard ports
# Default to YES unless --no-dashboard is passed
USE_PORTS=true
if [[ "$CMD" == *"--no-dashboard"* ]]; then
    USE_PORTS=false
fi

# Detect if port 7654 is already busy (e.g. by start_dashboard)
# We check if any process is listening on 7654
if lsof -i :7654 > /dev/null 2>&1 || (command -v ss >/dev/null 2>&1 && ss -lptn 'sport = :7654' | grep -q 7654) || (command -v netstat >/dev/null 2>&1 && netstat -an | grep 7654 | grep -i LISTEN > /dev/null 2>&1); then
    PORT_BUSY=true
else
    PORT_BUSY=false
fi

if [ "$USE_PORTS" = true ]; then
    if [ "$PORT_BUSY" = true ]; then
        echo "⚠️  Port 7654 is busy. Agent will run without hosting dashboard and connect to existing instance."
        USE_PORTS=false
        # Inject the host URL to ensure it connects to the host machine's port 7654
        # We append it to CMD. logic in main.py takes the last arg if repeated, or uses this if default.
        CMD="$CMD --dashboard-url http://host.docker.internal:7654"
    fi
fi

if [ "$USE_PORTS" = true ]; then
    # Expose ports
    if [ -z "$CMD" ]; then
         docker compose -f "$SCRIPT_DIR/docker-compose.yml" run --name "$CONTAINER_NAME" --service-ports --rm agent
    else
         docker compose -f "$SCRIPT_DIR/docker-compose.yml" run --name "$CONTAINER_NAME" --service-ports --rm agent $CMD
    fi
else
    # Do not expose ports
    if [ -z "$CMD" ]; then
        docker compose -f "$SCRIPT_DIR/docker-compose.yml" run --name "$CONTAINER_NAME" --rm agent
    else
        docker compose -f "$SCRIPT_DIR/docker-compose.yml" run --name "$CONTAINER_NAME" --rm agent $CMD
    fi
fi
