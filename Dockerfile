# ============================================
# Neuro-Trap Honeypot - Docker Image
# Phase 4: Containerized Deployment
# ============================================
FROM python:3.11-slim

LABEL maintainer="Neuro-Trap Team"
LABEL description="AI-Powered SSH Honeypot with Llama 3.2"

# Set working directory
WORKDIR /app

# Install system dependencies 
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Generate SSH host key if not present
RUN python keys/generate_key.py || true

# Create logs directory
RUN mkdir -p logs

# Expose ports
# 2222 = SSH Honeypot
# 8501 = Streamlit Dashboard
EXPOSE 2222 8501

# Default: Start the honeypot server
CMD ["python", "server/server.py"]
