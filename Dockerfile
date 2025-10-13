FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY unified_monitor.py .

VOLUME ["/app/logs", "/app/data", "/app/config"]

HEALTHCHECK --interval=5m --timeout=10s --start-period=30s \
  CMD python -c "import os; exit(0 if os.path.exists('/app/logs') else 1)"

CMD ["python", "-u", "unified_monitor.py"]
