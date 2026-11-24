"""Gera os 5 criativos do playbook pelo agente -> data/criativos_playbook.json"""
import json
from concurrent.futures import ThreadPoolExecutor

from agent import run

PEDIDOS = [
    ("Carrossel de fim de ano sobre separar o dinheiro do negócio do dinheiro de casa", None),
    ("Reels de Natal com dicas de vendas para quem vende comida em casa", "alimentação"),
    ("Reels de bastidores mostrando a rotina real de uma empreendedora e como ela organiza o caixa", None),
    ("Post que convida o empreendedor a contar o maior aprendizado do ano nos comentários", None),
    ("Carrossel tutorial sobre como precificar um serviço de beleza sem ter prejuízo", "beleza"),
]


def um(p):
    q, seg = p
    out = run("gerar_criativo", q, seg)
    return {"pedido": q, "segmento": seg, **out}


with ThreadPoolExecutor(5) as ex:
    res = list(ex.map(um, PEDIDOS))
json.dump(res, open("data/criativos_playbook.json", "w"), ensure_ascii=False, indent=1)
for r in res:
    print(r["pedido"][:60], "| criativos:", len(r["creatives"]), "| refs:", len(r["reference_posts"]),
          "| baixa confiança:", r["confidence_flag"])
