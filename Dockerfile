# RollWatch API + open engine (PRD M12: an election office can run POST /audit on its own server).
FROM python:3.12-slim

ENV PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY requirements.lock .
RUN pip install -r requirements.lock

COPY contracts/ contracts/
COPY generator/ generator/
COPY engine/ engine/
COPY api/ api/
COPY cache/ cache/
COPY smoke_test.py .

# Build the synthetic demo district at image build time, so a cold start only boots the API.
RUN python -m generator --auto-plant 60 --seed 7 --out artifacts && \
    python -m generator --config generator/demo_config.yaml --key artifacts/answer_key.json --seed 42 --out artifacts && \
    python -m engine.run --data artifacts --out artifacts --train-data artifacts/training --train-key artifacts/training/answer_key.json && \
    python -m engine.eval --key artifacts/answer_key.json && \
    cp cache/bench.json artifacts/bench.json  # measured on the dev laptop (machine recorded inside), not on the host

EXPOSE 8000
# Hosts like Render pass PORT; locally it defaults to 8000.
CMD ["sh", "-c", "exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
