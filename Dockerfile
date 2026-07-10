FROM python:3.10-slim

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY fixlot/ fixlot/
COPY tests/ tests/

RUN pip install --no-cache-dir -e .

EXPOSE 5000

ENV FIXLOT_MODE=cli

ENTRYPOINT ["sh", "-c", "if [ \"$FIXLOT_MODE\" = \"web\" ]; then python -m fixlot.webui.app; else python -m fixlot \"$@\"; fi", "--"]