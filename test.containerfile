# vim: set filetype=dockerfile
FROM registry.access.redhat.com/ubi9/ubi-minimal

ARG APP_ROOT=/app-root

ENV PATH="$PATH:/root/.local/bin"

WORKDIR ${APP_ROOT}
COPY run.yaml ./
COPY pyproject.toml uv.lock ./

RUN microdnf install -y --nodocs --setopt=keepcache=0 --setopt=tsflags=nodocs \
    python3.12 python3.12-devel python3.12-pip git tar

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

RUN uv -h

RUN uv sync --no-install-project  --no-dev && \
    uv pip install \
    opentelemetry-sdk \
    opentelemetry-exporter-otlp \
    opentelemetry-instrumentation \
    aiosqlite \
    litellm \
    blobfile \
    datasets \
    sqlalchemy \
    faiss-cpu \
    mcp \
    autoevals \
    psutil \
    torch \
    peft \
    trl

CMD ["uv", "run", "llama", "stack", "run", "run.yaml"]
