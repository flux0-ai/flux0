# see https://github.com/astral-sh/uv-docker-example/blob/main/Dockerfile
# Pin the version of the builder image to ensure reproducibility
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder
# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
# TODO: temporary until flux0-client is published
RUN apt-get update && apt-get install -y git && apt-get clean && rm -rf /var/lib/apt/lists/*
WORKDIR /app
# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    # NOTE: with a workspace, sync fails if packages, src are not mounted
    --mount=type=bind,source=packages,target=packages \
    --mount=type=bind,source=src,target=src \
    uv sync --all-packages --all-extras --frozen --no-install-project --no-dev
COPY ./src /app
COPY ./packages /app/packages
COPY ./uv.lock /app
COPY ./pyproject.toml /app
COPY ./README.md /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --all-packages --all-extras --frozen --no-dev

  ## UI Builder START
FROM node:23-alpine AS ui-builder
# Enable Corepack and install PNPM
RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /ui

# Cache dependencies and install UI dependencies
COPY ./chat/package.json ./chat/pnpm-lock.yaml ./
RUN pnpm install

# Copy the UI source and build
COPY ./chat .
RUN pnpm run build
## UI Buider END


# Then, use a final image without uv
FROM python:3.13-slim-bookworm
# It is important to use the image that matches the builder, as the path to the
# Python executable must be the same, e.g., using `python:3.11-slim-bookworm`
# will fail.

# Copy the application from the builder
COPY --from=builder --chown=app:app /app /app

# Copy built UI from ui-builder
COPY --from=ui-builder /ui/dist /app/chat

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/modules"

# Ensure we're in the app directory (helpful to find the configuration file)
WORKDIR /app

# start the flux0 server
CMD ["flux0-server"]
