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
COPY smoke_test.py .

EXPOSE 8000
# If no artifacts are mounted, build the synthetic demo district first (about 1 minute), then serve.
CMD ["sh", "-c", "if [ ! -f artifacts/roll_v2.parquet ]; then \
  python -m generator --auto-plant 12 --seed 7 --out artifacts && \
  python -m generator --config generator/demo_config.yaml --key artifacts/demo_answer_key.json --seed 42 --out artifacts && \
  python -m engine.run --data artifacts --out artifacts --train-data artifacts/training --train-key artifacts/training/answer_key.json; \
  fi && exec uvicorn api.main:app --host 0.0.0.0 --port 8000"]
