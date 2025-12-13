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
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
ARG UID=1000
ARG GID=1000
RUN groupadd -g "${GID}" appuser && \
    useradd -l -u "${UID}" -g "${GID}" -m -s /bin/bash appuser && \
    echo "appuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Install Gemini CLI (Global)
RUN npm install -g @google/gemini-cli

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
RUN pip install --user -r requirements.txt && \
    echo "export PATH=\$PATH:/home/appuser/.local/bin" >> ~/.bashrc

# Set entrypoint
# ENTRYPOINT ["python3", "combined-autonomous-coding/main.py"]
