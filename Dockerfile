# RollWatch API + open engine (PRD M12: an election office can run POST /audit on its own server).
FROM python:3.12-slim

ENV PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

# ffmpeg turns the spoken reply into an OGG/Opus voice note (a proper voice-note bubble on WhatsApp/Telegram)
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
COPY requirements.lock .
RUN pip install -r requirements.lock

COPY contracts/ contracts/
COPY generator/ generator/
COPY engine/ engine/
COPY api/ api/
COPY bot/ bot/
COPY cache/ cache/
COPY smoke_test.py .

# Build the synthetic demo district at image build time, so a cold start only boots the API.
# Four training districts (seeds 7-10) for the confidence curves; engine.run finds every artifacts/training*.
RUN python -m generator --auto-plant 60 --seed 7 --out artifacts && \
    for s in 8 9 10; do python -m generator --auto-plant 60 --seed $s --out artifacts --name training_$s; done && \
    python -m generator --config generator/demo_config.yaml --key artifacts/answer_key.json --seed 42 --out artifacts && \
    python -m engine.run --data artifacts --out artifacts && \
    python -m engine.eval --key artifacts/answer_key.json && \
    cp cache/bench.json artifacts/bench.json  # measured on the dev laptop (machine recorded inside), not on the host

EXPOSE 8000
# Hosts like Render pass PORT; locally it defaults to 8000.
# WEB_CONCURRENCY = worker processes (one per core). Read paths are stateless; WhatsApp sign-in codes and the
# outbox live in process memory, so keep 1 worker per instance until they move to a shared store (e.g. Redis).
CMD ["sh", "-c", "exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-1}"]
