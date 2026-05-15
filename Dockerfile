# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Non-root user for security
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy installed deps from builder
COPY --from=builder /install /usr/local

# Copy app
COPY --chown=appuser:appuser . .

# Audio output dir
RUN mkdir -p public/audio && chown appuser:appuser public/audio

USER appuser

EXPOSE 5000

# Uvicorn: 2 workers, production settings
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "5000", \
     "--workers", "2", \
     "--log-level", "info", \
     "--access-log"]