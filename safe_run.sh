#!/bin/bash

# Resolve project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"


# Create config dirs if they don't exist to avoid docker creating root-owned dirs on host
mkdir -p ~/.gemini
mkdir -p ~/.cursor

# Set workspace directory for docker-compose
export WORKSPACE_DIR="${WORKSPACE_DIR:-$(pwd)}"

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
if [[ "$CMD" == *"--dashboard"* ]]; then
    # If running dashboard, we need to expose ports
    if [ -z "$CMD" ]; then
         docker compose -f "$SCRIPT_DIR/docker-compose.yml" run --service-ports --rm agent
    else
         docker compose -f "$SCRIPT_DIR/docker-compose.yml" run --service-ports --rm agent $CMD
    fi
else
    if [ -z "$CMD" ]; then
        docker compose -f "$SCRIPT_DIR/docker-compose.yml" run --rm agent
    else
        docker compose -f "$SCRIPT_DIR/docker-compose.yml" run --rm agent $CMD
    fi
fi
