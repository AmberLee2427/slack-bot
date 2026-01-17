# Nancy Slack Bot Docker Image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY nancy_bot.py ./
COPY bot ./bot
COPY manifest.json ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create config directory
RUN mkdir -p /app/bot/config

# Environment variables (override at runtime)
ENV PYTHONUNBUFFERED=1
ENV KMP_DUPLICATE_LIB_OK=TRUE
ENV NANCY_BASE_DIR=/app
ENV PORT=3000

# Expose port for Slack events
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:3000/health').raise_for_status()" || exit 1

# Run bot
CMD ["python", "nancy_bot.py"]
