"""Cliente mínimo do influencers.club (descoberta de creators). Trial: 30 chamadas com sucesso e 10 créditos.
Cada chamada fica salva em data/influencers_club/ (nunca repetir uma busca paga: ler o arquivo)."""
import json, os, sys, time
import httpx
from dotenv import dotenv_values

BASE = "https://api-dashboard.influencers.club/public/v1"
PASTA = "data/influencers_club"
_h = {"Authorization": f"Bearer {dotenv_values('.env')['INFLUENCERS_CLUB_KEY']}"}


def chamar(nome, metodo, caminho, corpo=None):
    arq = f"{PASTA}/{nome}.json"
    if os.path.exists(arq):  # já pago: reaproveita
        return json.load(open(arq))["resposta"]
    r = httpx.request(metodo, BASE + caminho, headers=_h, json=corpo, timeout=90)
    d = r.json() if "json" in r.headers.get("content-type", "") else {"texto": r.text[:500]}
    if r.status_code != 200:
        raise SystemExit(f"{nome}: HTTP {r.status_code} {str(d)[:300]}")
    json.dump(dict(em=time.strftime("%F %T"), caminho=caminho, corpo=corpo, resposta=d), open(arq, "w"), ensure_ascii=False, indent=1)
    return d
