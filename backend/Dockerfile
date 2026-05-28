FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY sample_data/ /app/sample_data/
RUN chmod +x /app/entrypoint.sh

RUN python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
