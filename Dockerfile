# Stage 1: Builder
FROM python:3.11-slim-bookworm AS builder

# Configure apt for robustness
RUN echo 'Acquire::Retries "20";' > /etc/apt/apt.conf.d/80-retries && \
    echo 'Acquire::http::Timeout "60";' >> /etc/apt/apt.conf.d/80-retries

WORKDIR /build
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install python dependencies to a specific location
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Final
FROM python:3.11-slim-bookworm

# Configure apt for robustness
RUN echo 'Acquire::Retries "20";' > /etc/apt/apt.conf.d/80-retries && \
    echo 'Acquire::http::Timeout "60";' >> /etc/apt/apt.conf.d/80-retries

ENV DEBIAN_FRONTEND=noninteractive
ARG UID=1000
ARG GID=1000

# Install runtime system dependencies in chunks
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    git \
    jq \
    ripgrep \
    fd-find \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y ca-certificates curl gnupg && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    NODE_MAJOR=22 && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install nodejs -y --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    chromium \
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
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openssh-client \
    procps \
    unzip \
    zip \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g "${GID}" appuser && \
    useradd -l -u "${UID}" -g "${GID}" -m -s /bin/bash appuser

# Copy installed python packages from builder
COPY --from=builder /install /usr/local

# Install Gemini CLI (Global)
RUN npm install -g @google/gemini-cli

# Configure git to trust all directories (Global)
RUN git config --global --add safe.directory '*'

# Install Git Wrapper Safeguard
COPY shared/git_wrapper.py /usr/local/bin/git
RUN chmod +x /usr/local/bin/git && \
    mv /usr/bin/git /usr/bin/git.real

# Install Global Pre-push Hook (Secondary Safeguard)
COPY shared/pre-push /usr/local/share/git-hooks/pre-push
RUN chmod 0555 /usr/local/share/git-hooks/pre-push && \
    chown root:root /usr/local/share/git-hooks/pre-push && \
    git config --global core.hooksPath /usr/local/share/git-hooks

# Install Global Git Ignore (Protected)
COPY shared/.gitignore_global /usr/local/share/git/gitignore_global
RUN chmod 0444 /usr/local/share/git/gitignore_global && \
    git config --system core.excludesfile /usr/local/share/git/gitignore_global

# Prepare application directory
WORKDIR /app
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

# Set entrypoint (can be overridden by docker-compose)
# ENTRYPOINT ["python3", "combined-autonomous-coding/main.py"]