FROM python:3.11-slim

LABEL maintainer="Discord Bot Team"
LABEL description="Discord Bot Backend Relay and Async Task Worker"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Shanghai

WORKDIR /app

# Install system dependencies required for background worker tasks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    openssl \
    ca-certificates \
    procps \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy modular service source files and entrypoint
COPY main.py core.py utils.py config.py entrypoint.sh ./

# Ensure entrypoint permissions and LF format
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

# Web service and sync ports
EXPOSE 3000 8001 10203

ENTRYPOINT ["/app/entrypoint.sh"]
