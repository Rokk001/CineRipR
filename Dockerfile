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

# Install official 7-Zip and create non-root user with specific UID/GID
RUN apt-get update \
    && apt-get install -y --no-install-recommends wget xz-utils \
    && wget -q https://www.7-zip.org/a/7z2409-linux-x64.tar.xz \
    && tar -xf 7z2409-linux-x64.tar.xz -C /usr/local/bin \
    && rm 7z2409-linux-x64.tar.xz \
    && chmod +x /usr/local/bin/7zz \
    && ln -s /usr/local/bin/7zz /usr/local/bin/7z \
    && apt-get remove -y wget xz-utils \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r -g 1000 cineripr \
    && useradd -r -u 1000 -g cineripr cineripr

COPY --from=builder /dist /tmp/dist
RUN python -m pip install --no-cache-dir /tmp/dist/*.whl && rm -rf /tmp/dist

# Set proper umask for file permissions (readable/writable by owner and group)
ENV UMASK=002

# Expose WebGUI port
EXPOSE 8080

WORKDIR /work
USER cineripr
ENTRYPOINT ["python","-m","cineripr.cli"]
