FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY _sdk /app/_sdk
COPY kettle/main.py /app/main.py

ENV PYTHONUNBUFFERED=1
CMD ["python", "main.py"]
