#!/bin/bash

# Resolve project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"



# Create config dirs if they don't exist to avoid docker creating root-owned dirs on host
mkdir -p ~/.gemini
mkdir -p ~/.cursor

# Fix permissions using a temporary root container
# This ensures that even if files were previously created by root, they are now owned by the user (UID 1000)
echo "Ensuring correct permissions for config directories..."
docker run --rm \
    -v ~/.gemini:/gemini \
    -v ~/.cursor:/cursor \
    busybox sh -c "chown -R 1000:1000 /gemini /cursor"
# Set workspace directory for docker-compose
export WORKSPACE_DIR="${WORKSPACE_DIR:-$(pwd)}"
export PROJECT_NAME="$(basename "$WORKSPACE_DIR")"

echo "Launching Agent in Container..."

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
         docker compose -f "$SCRIPT_DIR/docker-compose.yml" run --service-ports --rm agent
    else
         docker compose -f "$SCRIPT_DIR/docker-compose.yml" run --service-ports --rm agent $CMD
    fi
else
    # Do not expose ports
    if [ -z "$CMD" ]; then
        docker compose -f "$SCRIPT_DIR/docker-compose.yml" run --rm agent
    else
        docker compose -f "$SCRIPT_DIR/docker-compose.yml" run --rm agent $CMD
    fi
fi
