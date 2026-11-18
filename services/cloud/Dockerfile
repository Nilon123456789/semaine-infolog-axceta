FROM python:3.12-slim

WORKDIR /app

# ZoneInfo needs tzdata for named zones like America/Toronto (STRESS_PEAK_* windows).
RUN apt-get update \
  && apt-get install -y --no-install-recommends tzdata \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
