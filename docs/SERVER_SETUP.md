# Server Setup Guide — Linux + RTX 3060

## Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| GPU | RTX 3060 (12GB VRAM) | RTX 3060 12GB+ |
| RAM | 16GB | 32GB |
| CPU | 4 cores | 8+ cores |
| Storage | 50GB SSD | 100GB+ SSD |
| Network | 100 Mbps | 1 Gbps |

> RTX 3060 12GB VRAM — ideal for this project. Runs qwen2.5:7b (5.5GB) + InsightFace + Whisper simultaneously.

---

## Step 1: Install Ubuntu Server

```bash
# Ubuntu 22.04 LTS or 24.04 LTS recommended
# During install: enable OpenSSH server
```

After install, update:
```bash
sudo apt update && sudo apt upgrade -y
sudo reboot
```

---

## Step 2: Install NVIDIA Drivers

```bash
# Check GPU is detected
lspci | grep -i nvidia

# Install drivers
sudo apt install -y ubuntu-drivers-common
sudo ubuntu-drivers autoinstall
sudo reboot

# Verify
nvidia-smi
```

Expected output:
```
+-------------------------------------------------------+
| NVIDIA-SMI 550.x    Driver Version: 550.x    CUDA: 12.x |
| RTX 3060 12GB                                          |
+-------------------------------------------------------+
```

---

## Step 3: Install Docker

```bash
# Remove old versions
sudo apt remove docker docker-engine docker.io containerd runc 2>/dev/null

# Add Docker repo
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group (no sudo needed)
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker compose version
```

---

## Step 4: Install NVIDIA Container Toolkit

```bash
# Add NVIDIA repo
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt update
sudo apt install -y nvidia-container-toolkit

# Configure Docker runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Verify GPU in Docker
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```

---

## Step 5: Install Git

```bash
sudo apt install -y git
```

---

## Step 6: Clone & Run

```bash
# Clone
git clone https://github.com/beknurakhmed/ai-chatbot.git
cd ai-chatbot

# (Optional) Edit config before first run
# nano .env.example          # ports, passwords, model
# nano frontend/.env.example # backend URL
# nano admin/.env.example    # backend URL

# Start
chmod +x start.sh
./start.sh
```

### First run timeline (RTX 3060, 100 Mbps):
| Step | What happens | Time |
|------|-------------|------|
| Docker images | Pull base images (PostgreSQL, Ollama, Node, PyTorch) | 5-10 min |
| Backend build | Install Python deps + Playwright | 5-8 min |
| Frontend build | npm install + next build | 3-5 min |
| Admin build | npm install + next build | 2-3 min |
| Ollama model | Download qwen2.5:7b (4.7GB) | 3-10 min |
| InsightFace | Download face model (300MB) | 1-2 min |
| **Total first run** | | **~20-40 min** |

Subsequent starts: **~30 seconds**.

---

## Step 7: Verify Services

```bash
# Check all containers running
docker compose ps

# Expected:
# aut-postgres    running   0.0.0.0:5432->5432
# aut-ollama      running   0.0.0.0:11434->11434
# aut-backend     running   0.0.0.0:8000->8000
# aut-frontend    running   0.0.0.0:3000->3000
# aut-admin       running   0.0.0.0:3001->3001

# Check health
curl http://localhost:8000/health
# {"status":"healthy"}

# Check GPU usage
nvidia-smi
# Should show ollama + python processes using VRAM
```

---

## Step 8: Initial Data Setup

Open admin panel: `http://<server-ip>:3001`

Login token: `chito-admin-secret` (or what you set in `.env`)

1. **Timetable** → "Refresh from edupage"
2. **Staff** → "Refresh from ajou.uz"
3. **News** → "Refresh"
4. **Rooms** → "Sync from timetable"

---

## VRAM Usage (RTX 3060 12GB)

| Service | VRAM | Notes |
|---------|------|-------|
| Ollama qwen2.5:7b | ~5.5 GB | Main LLM |
| InsightFace | ~0.5 GB | Face recognition |
| Faster Whisper (base) | ~0.3 GB | Speech-to-text |
| Silero TTS | ~0.2 GB | Text-to-speech |
| **Total** | **~6.5 GB** | Fits in 12GB |

> If VRAM is tight, switch to `qwen2.5:3b` (~2.5GB) in `.env`:
> ```
> OLLAMA_MODEL=qwen2.5:3b
> ```

---

## Production Configuration

### Firewall
```bash
# Allow only needed ports
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 3000/tcp    # Frontend (kiosk)
sudo ufw allow 3001/tcp    # Admin (restrict to admin IP)
sudo ufw allow 8000/tcp    # Backend API
# Don't expose PostgreSQL (5432) and Ollama (11434) externally
```

### Auto-start on boot
```bash
# Docker already auto-starts containers with restart: unless-stopped
# Just enable Docker service:
sudo systemctl enable docker
```

### Nginx reverse proxy (optional, for domain)
```bash
sudo apt install -y nginx

# /etc/nginx/sites-available/chatbot
server {
    listen 80;
    server_name kiosk.yourdomain.uz;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 80;
    server_name api.yourdomain.uz;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

sudo ln -s /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### SSL (Let's Encrypt)
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d kiosk.yourdomain.uz -d api.yourdomain.uz
```

### Change passwords
```bash
# Edit .env before first run:
nano .env
# POSTGRES_PASSWORD=strong-random-password
# ADMIN_TOKEN=strong-random-token
```

---

## Monitoring

```bash
# Live logs
docker compose logs -f

# Specific service
docker compose logs -f backend

# GPU monitoring
watch -n 1 nvidia-smi

# Disk usage
docker system df

# Cleanup unused images
docker system prune -f
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `nvidia-smi` not found | Reinstall drivers: `sudo ubuntu-drivers autoinstall && reboot` |
| Docker GPU error | Reinstall nvidia-container-toolkit, restart docker |
| Backend OOM killed | Reduce model: `OLLAMA_MODEL=qwen2.5:3b` |
| Port already in use | Change in `.env`: `BACKEND_PORT=9000` |
| Slow first start | Normal — downloading ~12GB of models |
| Permission denied on start.sh | `chmod +x start.sh` |

---

## Summary: What to Install

```
1. Ubuntu 22.04/24.04 LTS
2. NVIDIA Driver (ubuntu-drivers autoinstall)
3. Docker + Docker Compose (docker-ce)
4. NVIDIA Container Toolkit (nvidia-container-toolkit)
5. Git
```

Then: `git clone ... && ./start.sh` — everything else is automatic.
