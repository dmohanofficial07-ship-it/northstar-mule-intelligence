FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY alembic.ini index.html styles.css script.js /app/
COPY assets /app/assets

RUN useradd --create-home --uid 10001 northstar && chown -R northstar:northstar /app
USER northstar

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
