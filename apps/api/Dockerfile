FROM python:3.12

ENV PYTHONUNBUFFERED=1

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

# Compile bytecode
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1

# uv Cache
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_LINK_MODE=copy

# Set workdir to where pyproject.toml lives so hatchling can find the app/ package
WORKDIR /app/apps/api/

# Place executables in the environment at the front of the path
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#using-the-environment
ENV PATH="/app/apps/api/.venv/bin:$PATH"

# Install dependencies (no-install-workspace skips building the app package itself)
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=apps/api/uv.lock,target=uv.lock \
    --mount=type=bind,source=apps/api/pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-workspace

COPY ./apps/api/scripts /app/apps/api/scripts

COPY ./apps/api/pyproject.toml ./apps/api/alembic.ini /app/apps/api/

COPY ./apps/api/app /app/apps/api/app

# Sync the project — hatchling now finds app/ as a sibling of pyproject.toml
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=apps/api/uv.lock,target=uv.lock \
    --mount=type=bind,source=apps/api/pyproject.toml,target=pyproject.toml \
    uv sync --frozen

CMD ["fastapi", "run", "--workers", "4", "app/main.py"]
