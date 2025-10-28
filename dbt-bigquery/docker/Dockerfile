# this image gets published to GHCR for production use
ARG py_version=3.11.2

FROM python:$py_version-slim-bullseye AS base

RUN apt-get update \
  && apt-get dist-upgrade -y \
  && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    git \
    libpq-dev \
    make \
    openssh-client \
    software-properties-common \
  && apt-get clean \
  && rm -rf \
    /var/lib/apt/lists/* \
    /tmp/* \
    /var/tmp/*

ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8

RUN python -m pip install --upgrade "pip==24.0" "setuptools==69.2.0" "wheel==0.43.0" --no-cache-dir


FROM base AS dbt-bigquery

HEALTHCHECK CMD dbt --version || exit 1

WORKDIR /usr/app/dbt/

# Note: Build this with context from /Users/jarmo/git/tokenterminal:
# docker build -f dbt-adapters/dbt-bigquery/docker/Dockerfile -t dbt-bigquery:patched-model-labels .

# Install our forked dbt-common first (adds current_node context)
COPY dbt-common /tmp/dbt-common
RUN python -m pip install --no-cache-dir /tmp/dbt-common && \
    rm -rf /tmp/dbt-common

# Install our forked dbt-core (sets node in context before execution)
COPY dbt-core/core /tmp/dbt-core
RUN python -m pip install --no-cache-dir /tmp/dbt-core && \
    rm -rf /tmp/dbt-core

# Copy and install patched dbt-bigquery with model config labels support
COPY dbt-adapters/dbt-bigquery /tmp/dbt-bigquery-src
RUN python -m pip install --no-cache-dir /tmp/dbt-bigquery-src && \
    rm -rf /tmp/dbt-bigquery-src

ENTRYPOINT ["dbt"]
