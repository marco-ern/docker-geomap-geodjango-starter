FROM ghcr.io/osgeo/gdal:ubuntu-small-latest

ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Args que pueden venir de .env vía docker-compose
ARG HTTP_PROXY=""
ARG HTTPS_PROXY=""
ENV http_proxy=${HTTP_PROXY}
ENV https_proxy=${HTTPS_PROXY}

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
      python3 \
      python3-pip \
      python3-venv \
      netcat-openbsd \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1

RUN python -m venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x /app/start.sh

WORKDIR /app/backend
EXPOSE 8000

CMD ["/app/start.sh"]