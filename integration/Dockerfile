FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git bash \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY . /workspace

RUN pip install -e .

ENTRYPOINT ["/bin/bash", "-lc", "./integration/run_matrix.sh"]
