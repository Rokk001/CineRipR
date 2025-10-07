# ---- Builder ----
FROM python:3.11-slim AS builder
ENV PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip install --upgrade pip build \
    && python -m build --wheel --outdir /dist

# ---- Runtime ----
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update \
    && apt-get install -y --no-install-recommends p7zip-full \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /dist /tmp/dist
RUN python -m pip install --no-cache-dir /tmp/dist/*.whl && rm -rf /tmp/dist
WORKDIR /work
ENTRYPOINT ["python","-m","cineripr.cli"]
