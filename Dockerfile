# Multi-stage build for smaller final image
FROM python:3.10-slim as builder

WORKDIR /app

# Install uv for fast dependency installation
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv (much faster than pip)
# --frozen: Don't update uv.lock
# --no-dev: Skip development dependencies
RUN uv sync --frozen --no-dev

# Runtime stage - smaller final image
FROM python:3.10-slim

WORKDIR /app

# Copy installed dependencies from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8001
# Add .venv to PATH so Python uses installed packages
ENV PATH="/app/.venv/bin:$PATH"

# Run the application
CMD ["python", "src/ansari_whatsapp/app/main.py"]