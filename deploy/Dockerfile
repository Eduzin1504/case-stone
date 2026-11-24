# Só as dependências; código e dados entram por volume em /app (ver deploy/subir.sh)
FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
# node: runtime JS do yt-dlp (avaliar link do YouTube)
COPY --from=node:22-bookworm-slim /usr/local/bin/node /usr/local/bin/node
COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt
RUN useradd -m -u 1000 user
USER user
WORKDIR /app
ENV WHISPER_MODELO=base WHISPER_THREADS=1
EXPOSE 7860
CMD ["uvicorn", "servir:app", "--host", "0.0.0.0", "--port", "7860"]
