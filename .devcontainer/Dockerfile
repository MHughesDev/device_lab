FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    make \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# uv
RUN curl -Ls https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:/home/vscode/.local/bin:$PATH"

# Bun
RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="/root/.bun/bin:/home/vscode/.bun/bin:$PATH"
