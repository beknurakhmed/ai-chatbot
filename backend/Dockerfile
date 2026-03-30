FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime

ENV PIP_BREAK_SYSTEM_PACKAGES=1
ENV DEBIAN_FRONTEND=noninteractive
ENV LD_LIBRARY_PATH=/opt/conda/lib/python3.11/site-packages/nvidia/cudnn/lib:/opt/conda/lib/python3.11/site-packages/nvidia/cuda_runtime/lib:/usr/local/cuda/lib64:${LD_LIBRARY_PATH}

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 build-essential g++ \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
    libasound2 libpango-1.0-0 libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium --with-deps

COPY . .
RUN mkdir -p app/data/faces app/data/celebrities/photos

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
