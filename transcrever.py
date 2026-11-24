"""Transcrição do áudio dos vídeos com Whisper local (faster-whisper "small", int8, CPU), para o deepseek "ouvir" o post.

Uso no código: transcrever.segmentos(video_bytes_ou_caminho) -> [(inicio, fim, texto)]; transcrever.para_prompt(segs).
Em lote (todos os vídeos locais, em paralelo, com cache em data/transcricoes.json):
    .venv/bin/python transcrever.py            # só os que faltam
    .venv/bin/python transcrever.py --teste    # auto-checagem
"""
import functools
import glob
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

MODELO = os.getenv("WHISPER_MODELO", "small")  # "base" é ~40% mais rápido e erra mais em pt
CACHE = "data/transcricoes.json"
PASTAS = ("data/midia", "data/midia_b")
GANCHO_S = 3.0
_trava = threading.Lock()  # um modelo por processo; a API pode ter dois pedidos ao mesmo tempo


@functools.lru_cache(maxsize=1)
def _modelo(threads=0):
    from faster_whisper import WhisperModel
    return WhisperModel(MODELO, device="cpu", compute_type="int8", cpu_threads=threads)


def _pcm(fonte):
    """Áudio mono 16 kHz em float32 via ffmpeg (o PyAV do faster-whisper não abre com esta versão do av). None se não há áudio."""
    entrada, dado = (fonte, None) if isinstance(fonte, str) else ("pipe:0", fonte)
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", entrada, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                       input=dado, capture_output=True)
    if r.returncode or not r.stdout:
        return None
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768


def segmentos(fonte, threads=0):
    """[(início s, fim s, texto)]; [] se o vídeo não tem áudio ou ninguém fala."""
    if not isinstance(fonte, str):  # bytes: o ffmpeg precisa de arquivo para alguns contêineres (mov com moov no fim)
        with tempfile.NamedTemporaryFile(suffix=".mp4") as f:
            f.write(fonte), f.flush()
            return segmentos(f.name, threads)
    audio = _pcm(fonte)
    if audio is None or not len(audio):
        return []
    with _trava:
        segs, _ = _modelo(threads).transcribe(audio, language="pt", beam_size=1, vad_filter=True)
        return [(round(s.start, 1), round(s.end, 1), s.text.strip()) for s in segs if s.text.strip()]


def cache():
    return json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def para_prompt(segs, limite=3000):
    """Texto com tempos para o prompt; marca o que é falado no gancho."""
    if not segs:
        return "TRANSCRIÇÃO DO ÁUDIO: ninguém fala no vídeo (ou não há áudio).\n"
    linhas = [f"[{a:.1f}–{b:.1f} s]{' (gancho)' if a < GANCHO_S else ''} {t}" for a, b, t in segs]
    return "TRANSCRIÇÃO DO ÁUDIO (Whisper, com tempos; a fala dos primeiros 3 s faz parte do gancho):\n" + "\n".join(linhas)[:limite] + "\n"


# ---------------------------------------------------------------- lote
THREADS = int(os.getenv("WHISPER_THREADS", "4"))  # cada processo carrega o modelo (~0,6 GB de RAM)


def _um(caminho):
    t = time.time()
    return os.path.basename(caminho).rsplit(".", 1)[0], segmentos(caminho, threads=THREADS), time.time() - t


def lote(processos=None):
    feito = cache()
    videos = [f for p in PASTAS for f in sorted(glob.glob(f"{p}/*.mp4"))]
    falta = [f for f in videos if os.path.basename(f).rsplit(".", 1)[0] not in feito]
    # ponytail: 1 processo por padrão; 2 processos + o teste carregando outro modelo esgotaram a RAM e travaram o notebook
    processos = processos or int(os.getenv("WHISPER_PROCESSOS", "1"))
    print(f"{len(videos)} vídeos, {len(falta)} sem transcrição; {processos} processos × {THREADS} threads", flush=True)
    t0, feitos = time.time(), 0
    with ProcessPoolExecutor(processos) as ex:
        for fut in as_completed([ex.submit(_um, f) for f in falta]):
            try:
                vid, segs, dt = fut.result()
            except Exception as e:  # um vídeo corrompido não derruba o lote
                print("  erro:", type(e).__name__, e, flush=True)
                continue
            feito[vid] = [list(s) for s in segs]
            feitos += 1
            json.dump(feito, open(CACHE + ".tmp", "w"), ensure_ascii=False)  # grava a cada vídeo: se cair, não perde nada
            os.replace(CACHE + ".tmp", CACHE)
            print(f"  {feitos}/{len(falta)} ({time.time() - t0:.0f} s)", flush=True)
    return feito


def _teste():
    assert para_prompt([]).startswith("TRANSCRIÇÃO DO ÁUDIO: ninguém")
    p = para_prompt([(0.0, 2.2, "Quer cabelos com mais luz?"), (3.4, 5.0, "Agende já.")])
    assert "[0.0–2.2 s] (gancho) Quer cabelos" in p and "[3.4–5.0 s] Agende" in p
    with tempfile.TemporaryDirectory() as d:  # vídeo sem áudio -> []
        f = f"{d}/v.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=duration=2:size=64x64:rate=10", f], check=True)
        assert segmentos(f) == [] and segmentos(open(f, "rb").read()) == []
    print("ok")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    _teste() if "--teste" in sys.argv else lote()
