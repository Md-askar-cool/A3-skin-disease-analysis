# ============================================================
# SafeSkin AI – Backend API Dockerfile
# Base: Python 3.11-slim for a lean production image
# ============================================================

FROM python:3.11-slim

# Metadata
LABEL maintainer="SafeSkin AI Team"
LABEL description="SafeSkin AI FastAPI Backend"

# ── System dependencies ───────────────────────────────────────────────
# libGL is required by OpenCV; libglib for PIL
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────────────────
WORKDIR /app

# ── Install Python dependencies ───────────────────────────────────────
# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Copy application source ───────────────────────────────────────────
COPY . .

# ── Create models directory ───────────────────────────────────────────
RUN mkdir -p /app/models/gradcam

# ── Non-root user for security ────────────────────────────────────────
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# ── Expose API port ───────────────────────────────────────────────────
EXPOSE 8000

# ── Health check ──────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# ── Startup command ───────────────────────────────────────────────────
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--log-level", "info"]
