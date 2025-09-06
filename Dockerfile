# Use Python 3.12 slim image for smaller size
FROM python:3.12-slim

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files first (for better Docker layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen

# Copy application files
COPY main.py helper_functions.py ./

# Expose the port the app runs on
EXPOSE 8000

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application with SSE transport
CMD ["uv", "run", "python", "main.py", "--http"]