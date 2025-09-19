# Dockerfile (fixed w/ compilers)
FROM python:3.12-slim

WORKDIR /app

# OS deps + build tools first
RUN apt-get update && apt-get install -y \
    build-essential \
    libgdal-dev \
    gdal-bin \
    python3-gdal \
    chromium-driver \
    wget \
    && wget https://github.com/mozilla/geckodriver/releases/download/v0.35.0/geckodriver-v0.35.0-linux-aarch64.tar.gz \
    && tar -xvzf geckodriver-v0.35.0-linux-aarch64.tar.gz \
    && mv geckodriver /usr/local/bin/ \
    && rm geckodriver-v0.35.0-linux-aarch64.tar.gz \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]