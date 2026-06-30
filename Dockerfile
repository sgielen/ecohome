FROM python:3.14-slim

RUN apt-get update && apt-get install -y --no-install-recommends jq && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY . .

RUN uv pip install --system --no-cache .

COPY scripts/hot-water.sh /usr/local/bin/hot-water.sh
RUN chmod +x /usr/local/bin/hot-water.sh

CMD ["bash", "-c", "while :; do /usr/local/bin/hot-water.sh; sleep 300; done"]
