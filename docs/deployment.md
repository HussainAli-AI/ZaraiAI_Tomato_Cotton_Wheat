# ZaraiAI: Production Deployment Guide (Alibaba Cloud & Docker)

This guide documents the deployment procedures for ZaraiAI on **Alibaba Cloud** using Elastic Compute Service (ECS) and containerized workflows.

---

## 1. Local Container Deployment

### Build Docker Image
```bash
docker build -t zarai-ai:latest .
```

### Run Container
```bash
docker run -d \
  --name zarai-ai-app \
  -p 8501:8501 \
  --env-file .env \
  --restart unless-stopped \
  zarai-ai:latest
```

### Verify Container Health
```bash
curl -I http://localhost:8501/_stcore/health
```

---

## 2. Alibaba Cloud ECS Deployment

### Step 1: Provision ECS Instance
- **Region:** `me-central-1` (Dubai / Middle East) or `ap-southeast-1` (Singapore) for lowest latency to Pakistan.
- **Instance Type:** `ecs.c7.large` (2 vCPU, 4GB RAM) or `ecs.gn7i-vws` (for GPU inference).
- **OS:** Ubuntu 22.04 LTS.

### Step 2: Configure Alibaba Cloud Model Studio API
Set up DashScope credentials for Qwen3.7-Plus:
```bash
export ALIBABA_API_KEY="your_actual_dashscope_api_key"
export ALIBABA_BASE_URL="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
export LLM_MODEL="qwen3.7-plus"
```

### Step 3: Run with Docker Compose
Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  zarai-ai:
    image: zarai-ai:latest
    ports:
      - "80:8501"
    environment:
      - ALIBABA_API_KEY=${ALIBABA_API_KEY}
      - ALIBABA_BASE_URL=${ALIBABA_BASE_URL}
      - LLM_MODEL=qwen3.7-plus
      - WEATHER_PROVIDER=open-meteo
    restart: always
```

Run:
```bash
docker compose up -d
```

---

## 3. High Availability & Serverless Fallback
- **Alibaba Cloud OSS:** Used for persisting dataset archives and pretrained model weights.
- **Graceful Fallbacks:** If the cloud LLM connection experiences latency or timeout, ZaraiAI automatically engages the local grounded rule engine, ensuring uninterrupted uptime for farmers in low-connectivity areas.
