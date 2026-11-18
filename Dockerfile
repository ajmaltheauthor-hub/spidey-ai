FROM python:3.11-slim

WORKDIR /app

# Install ffmpeg for 30s video rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

ENV PORT=8080
EXPOSE 8080

CMD ["python", "-B", "server.py"]
