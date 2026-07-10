FROM python:3.10-slim

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY fixlot/ fixlot/
COPY tests/ tests/

RUN pip install --no-cache-dir -e .

ENTRYPOINT ["python", "-m", "fixlot"]