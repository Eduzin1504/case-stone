"""Vídeo pela Feita (gateway estilo OpenAI) com rotação de chaves.

As chaves vêm do .env: FEITA_API_KEY, FEITA_API_KEY_2, ... Quando uma chave não tem
saldo livre (insufficient_credits), a próxima assume. Clipes ficam em cache por
conteúdo em data/render/feita/, então rodar de novo não gasta de novo.
"""
import hashlib
import json
import os
import time
import urllib.request

from dotenv import load_dotenv

load_dotenv()
URL = "https://api.feita.ai/gateway/v1"
CACHE = os.path.join(os.getenv("DATA_DIR", "data"), "render", "feita")
MODELO = "bytedance/seedance-2.0-mini"  # 720p US$ 0,076/s; o gateway só aceita os tamanhos da OpenAI (720x1280)


def chaves():
    ks = [os.environ.get("FEITA_API_KEY", "")]
    n = 2
    while os.environ.get(f"FEITA_API_KEY_{n}"):
        ks.append(os.environ[f"FEITA_API_KEY_{n}"])
        n += 1
    return [k for k in ks if k]


def _req(metodo, rota, chave, corpo=None):
    req = urllib.request.Request(f"{URL}{rota}", method=metodo,
                                 headers={"Authorization": f"Bearer {chave}", "Content-Type": "application/json",
                                          "User-Agent": "curl/8.5.0"},  # o gateway bloqueia o UA padrão do urllib
                                 data=json.dumps(corpo).encode() if corpo is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            bruto = r.read()
    except urllib.error.HTTPError as e:
        bruto = e.read()
    try:
        return json.loads(bruto)
    except ValueError:
        return bruto  # download binário


def gerar_clipe(prompt, segundos=8, size="720x1280", log=print):
    """Gera um clipe e devolve o caminho do MP4 (cache por prompt+duração)."""
    os.makedirs(CACHE, exist_ok=True)
    h = hashlib.sha1(f"{MODELO}|{prompt}|{segundos}|{size}".encode()).hexdigest()[:16]
    caminho = os.path.join(CACHE, f"{h}.mp4")
    if os.path.exists(caminho):
        log(f"cache: {caminho}")
        return caminho
    corpo = {"model": MODELO, "prompt": prompt, "seconds": str(segundos), "size": size}
    for rodada in range(3):
        if rodada:
            log("todas as chaves ocupadas ou sem saldo; esperando 60s a pré-reserva assentar")
            time.sleep(60)
        caminho_ok = _tentar_chaves(corpo, caminho, log)
        if caminho_ok:
            return caminho_ok
    raise RuntimeError("Feita: nenhuma chave com saldo livre")


def _tentar_chaves(corpo, caminho, log):
    for i, chave in enumerate(chaves(), 1):
        job = _req("POST", "/videos", chave, corpo)
        erro = isinstance(job, dict) and job.get("error")
        if erro and erro.get("code") == "insufficient_credits":
            log(f"chave {i} sem saldo livre, tentando a próxima")
            continue
        if erro:
            raise RuntimeError(f"Feita: {erro}")
        vid = job["id"]
        log(f"chave {i}: job {vid} ({corpo['seconds']}s)")
        while job.get("status") in (None, "pending", "queued", "in_progress", "processing", "running"):
            time.sleep(5)
            job = _req("GET", f"/videos/{vid}", chave)
        if job.get("status") != "completed":
            raise RuntimeError(f"Feita: job {vid} terminou como {job.get('status')}: {job.get('error')}")
        dados = _req("GET", f"/videos/{vid}/content", chave)
        if isinstance(dados, dict):  # content veio como JSON com URL
            url = dados.get("url") or dados.get("data", [{}])[0].get("url")
            with urllib.request.urlopen(url, timeout=300) as r:
                dados = r.read()
        with open(caminho, "wb") as f:
            f.write(dados)
        log(f"salvo: {caminho} ({len(dados)//1024} KB)")
        return caminho
    return None  # todas as chaves recusaram nesta rodada; quem chamou decide esperar a pré-reserva


TTS = "google/gemini-2.5-flash-tts"  # PT-BR natural; o qwen3-tts sai com sotaque chinês


def gerar_fala(texto, voz="Kore", log=print):
    """Narração TTS em PT-BR (Gemini TTS, centavos por Reels), com cache. O Gemini só devolve PCM;
    o ffmpeg converte para MP3."""
    import subprocess
    os.makedirs(CACHE, exist_ok=True)
    h = hashlib.sha1(f"tts|{TTS}|{voz}|{texto}".encode()).hexdigest()[:16]
    caminho = os.path.join(CACHE, f"{h}.mp3")
    if os.path.exists(caminho):
        return caminho
    for i, chave in enumerate(chaves(), 1):
        r = _req("POST", "/audio/speech", chave, {"model": TTS, "voice": voz,
                                                  "response_format": "pcm", "input": texto})
        if isinstance(r, dict):
            if (r.get("error") or {}).get("code") == "insufficient_credits":
                continue
            raise RuntimeError(f"Feita TTS: {r.get('error')}")
        bruto = caminho + ".pcm"
        with open(bruto, "wb") as f:
            f.write(r)
        subprocess.run(["nice", "-n", "10", "ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", "24000", "-ac", "1",
                        "-i", bruto, caminho], check=True)
        os.remove(bruto)
        log(f"fala: {caminho} ({len(r)//1024} KB)")
        return caminho
    raise RuntimeError("Feita TTS: nenhuma chave com saldo livre")


def saldos():
    return [(f"chave {i}", _req("GET", "/credits", k).get("data", {}).get("ordinary_credits", 0) / 100)
            for i, k in enumerate(chaves(), 1)]


if __name__ == "__main__":
    for nome, usd in saldos():
        print(f"{nome}: US$ {usd:.2f} livres")
