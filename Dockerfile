# Multi-stage build for Hrisa Code
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/
COPY README.md ./

# Install the package
RUN pip install --no-cache-dir -e .

# Final stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 hrisa && \
    mkdir -p /home/hrisa/.hrisa /workspace && \
    chown -R hrisa:hrisa /home/hrisa /workspace

# Set working directory
WORKDIR /workspace

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/hrisa /usr/local/bin/hrisa
COPY --from=builder /app/src /app/src

# Switch to non-root user
USER hrisa

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Default command
CMD ["hrisa", "--help"]
