"""Baixa um post a partir do link (Instagram ou YouTube) para o "avaliar meu post".

YouTube: yt-dlp com Node como runtime JS (só o vídeo, até 720p, + título/descrição). Instagram: actor da Apify com directUrls (cache em data/raw,
~US$ 0,003 por post). Devolve (arquivos, legenda, plataforma) no formato que avaliar.avaliar espera.
"""
import json
import os
import re
import subprocess
import tempfile

import httpx

IG = re.compile(r"instagram\.com/(?:[\w.]+/)?(?:p|reels?|tv)/([\w-]+)")
YT = re.compile(r"(?:youtube\.com/(?:shorts/|watch\?(?:.*&)?v=|embed/)|youtu\.be/)([\w-]{11})")
LIMITE = 200 * 1024 * 1024


def ler(link: str):
    """(plataforma, id) ou None."""
    if m := IG.search(link):
        return "instagram", m.group(1)
    if m := YT.search(link):
        return "youtube", m.group(1)
    return None


def _youtube(vid):
    with tempfile.TemporaryDirectory() as d:
        r = subprocess.run(
            ["yt-dlp", "-q", "--no-update", "--js-runtimes", "node", "--no-playlist", "--max-filesize", "200M",
             # ponytail: só o vídeo (a avaliação lê quadros, não o áudio); vertical 720p tem 1280 de altura
             "-f", "bv*[height<=1280][ext=mp4]/bv*[height<=1280]/b",
             "--write-info-json", "-o", f"{d}/v.%(ext)s", f"https://www.youtube.com/watch?v={vid}"],
            capture_output=True, text=True, timeout=300)
        arqs = [f for f in os.listdir(d) if f.startswith("v.") and not f.endswith(".json")]
        if r.returncode or not arqs:
            raise ValueError("não conseguimos baixar este vídeo do YouTube (privado, removido ou bloqueado)")
        info = json.load(open(f"{d}/v.info.json")) if os.path.exists(f"{d}/v.info.json") else {}
        legenda = "\n".join(x for x in (info.get("title"), info.get("description")) if x)
        return [(arqs[0], open(f"{d}/{arqs[0]}", "rb").read())], legenda


def _instagram(codigo):
    import pipeline as P  # mesmo helper (com cache) da coleta
    itens = P.apify(f"link_{codigo}", directUrls=[f"https://www.instagram.com/p/{codigo}/"], resultsType="posts", resultsLimit=1)
    p = next((i for i in itens if not i.get("error")), None)
    if not p:
        raise ValueError("não encontramos este post do Instagram (privado ou removido)")
    if p.get("videoUrl"):
        urls = [(f"{codigo}.mp4", p["videoUrl"])]
    else:
        filhos = [c.get("displayUrl") for c in p.get("childPosts") or [] if c.get("displayUrl")]
        urls = [(f"{codigo}_{i}.jpg", u) for i, u in enumerate((filhos or [p.get("displayUrl")])[:10]) if u]
    if not urls:
        raise ValueError("o post não tem mídia que dê para baixar")
    with httpx.Client(timeout=120, follow_redirects=True) as c:
        arquivos = [(nome, c.get(u).raise_for_status().content) for nome, u in urls]
    if sum(len(b) for _, b in arquivos) > LIMITE:
        raise ValueError("mídia acima de 200 MB")
    return arquivos, p.get("caption") or ""


def baixar(link: str):
    alvo = ler(link)
    if not alvo:
        raise ValueError("o link precisa ser de um post do Instagram ou de um vídeo do YouTube")
    plataforma, id_ = alvo
    arquivos, legenda = (_youtube if plataforma == "youtube" else _instagram)(id_)
    return arquivos, legenda, plataforma


if __name__ == "__main__":
    assert ler("https://www.instagram.com/reel/De69nJci1Y_/?igsh=x") == ("instagram", "De69nJci1Y_")
    assert ler("https://instagram.com/fulano/p/ABC-12_/") == ("instagram", "ABC-12_")
    assert ler("https://youtube.com/shorts/DkpnGeH5IRg?si=1") == ("youtube", "DkpnGeH5IRg")
    assert ler("https://www.youtube.com/watch?t=3&v=DkpnGeH5IRg") == ("youtube", "DkpnGeH5IRg")
    assert ler("https://youtu.be/DkpnGeH5IRg") == ("youtube", "DkpnGeH5IRg")
    assert ler("https://example.com/p/abc") is None
    print("ok")
