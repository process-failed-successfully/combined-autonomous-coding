FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    nodejs \
    npm \
    curl \
    wget \
    procps \
    net-tools \
    iputils-ping \
    vim \
    nano \
    unzip \
    zip \
    jq \
    build-essential \
    python3-dev \
    dnsutils \
    ripgrep \
    fd-find \
    chromium \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Install Gemini CLI
RUN npm install -g @google/gemini-cli

# Install Cursor Agent
RUN curl https://cursor.com/install -fsS | bash

# Symlink cursor-agent to global bin
RUN ln -s /root/.local/bin/cursor-agent /usr/local/bin/cursor-agent

# Configure git to trust all directories (fixes dubious ownership in mounted volumes)
RUN git config --global --add safe.directory '*'

# Set working directory
WORKDIR /app

# Copy requirements if any (currently none, but good practice)
COPY requirements.txt .
RUN pip install -r requirements.txt

# We don't copy the code here because we bind mount it for development/execution
# COPY . /app

# Set entrypoint
# Set entrypoint
# ENTRYPOINT ["python3", "combined-autonomous-coding/main.py"]
