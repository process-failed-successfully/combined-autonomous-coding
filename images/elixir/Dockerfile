FROM elixir:1.16-slim

# Install system dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    build-essential \
    chromium \
    curl \
    dnsutils \
    fd-find \
    git \
    iputils-ping \
    jq \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    nano \
    net-tools \
    nodejs \
    npm \
    procps \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    ripgrep \
    sudo \
    unzip \
    vim \
    wget \
    zip \
    && rm -rf /var/lib/apt/lists/*

# Install Hex and Rebar
RUN mix local.hex --force && mix local.rebar --force

# Create a non-root user
ARG UID=1000
ARG GID=1000
RUN groupadd -g "${GID}" appuser && \
    useradd -l -u "${UID}" -g "${GID}" -m -s /bin/bash appuser && \
    echo "appuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Install Gemini CLI (Global)
# Requires Node.js and NPM to be installed
RUN npm install -g npm@latest && npm install -g @google/gemini-cli

# Configure git to trust all directories (Global)
RUN git config --global --add safe.directory '*'

# Create directory structure and set permissions
RUN mkdir -p /app/combined-autonomous-coding && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser
ENV HOME=/home/appuser

# Install Cursor Agent as appuser
RUN curl https://cursor.com/install -fsS | bash

# Add local bin to PATH
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Configure git for user
RUN git config --global --add safe.directory '*'

# Set working directory
WORKDIR /app

# Copy requirements and install (User install)
COPY requirements.txt .
# pip install as user (goes to ~/.local usually or checks permissions)
# Ensure we use the correct pip (pip3 or pip)
# Use venv
RUN python3 -m venv /home/appuser/venv
ENV PATH="/home/appuser/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt
# echo "export PATH=\$PATH:/home/appuser/.local/bin" >> ~/.bashrc

# Set entrypoint
# ENTRYPOINT ["python3", "combined-autonomous-coding/main.py"]
