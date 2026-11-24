"""Agente do case Stone: contrato Pydantic + grafo LangGraph (recuperar -> redigir -> checar).

Uso:
  python agent.py analisar "quais formatos mais aparecem no topo?"
  python agent.py gerar_criativo "Reels sobre aceitar Pix na maquininha" --segment alimentação
"""
import argparse
import json
import os
import unicodedata
from datetime import datetime
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel

import pipeline as P


# ---------- contrato (TAPI, seção 7) ----------

class Filtros(BaseModel):
    porte: Literal["pequeno", "medio", "grande"] | None = None
    periodo_dias: int | None = None
    tema: str | None = None
    formato: str | None = None


class Entrada(BaseModel):
    mode: Literal["analisar", "recomendar", "gerar_criativo"]
    query: str
    segment: str | None = None
    filters: Filtros = Filtros()


class Achado(BaseModel):
    campo: str
    valor: str
    freq_top: float
    freq_resto: float
    lift: float | None
    n_top: int


class PostRef(BaseModel):
    video_id: str
    url: str
    canal: str
    titulo: str
    er: float
    outlier: float | None
    categorias: dict


class Criativo(BaseModel):
    gancho: str
    roteiro: str
    legenda: str
    cta: str
    inspirado_em: list[str]  # video_ids das publicações de referência


class Saida(BaseModel):
    findings: list[Achado]
    reference_posts: list[PostRef]
    creatives: list[Criativo]
    confidence_flag: bool
    explanation: str


class Redacao(BaseModel):  # o que o LLM devolve; dados vêm sempre da base
    explanation: str
    creatives: list[Criativo]


class Checagem(BaseModel):
    forca_hook_0a10: int
    clareza_mensagem_0a10: int
    tem_cta: bool


# ---------- recuperação (determinística, sem LLM) ----------

SEGMENTOS = {
    "alimentação": ["comida", "restaurante", "lanche", "doce", "confeitaria", "delivery", "marmita", "food", "bolo"],
    "beleza": ["salão", "salao", "beleza", "estética", "unha", "cabelo", "maquiagem", "barbearia", "nail"],
    "varejo": ["loja", "varejo", "roupa", "moda", "boutique", "estoque", "vitrine"],
    "serviços": ["serviço", "servico", "prestador", "autônomo", "autonomo", "cliente", "orçamento"],
}
COLS_REF = ["formato_video", "tipo_hook", "hook_primeiros_3s", "tema_principal", "tom", "tem_cta", "tipo_cta",
            "prova_social", "elementos_top5"]


def norm(s):
    return unicodedata.normalize("NFKD", str(s).lower()).encode("ascii", "ignore").decode()


def recuperar(e: Entrada, n_refs=8):
    df = P.carregar(P.db())
    f = e.filters.model_copy()
    q = norm(e.query)
    # termos da pergunta que batem com o vocabulário da rubrica viram filtro
    f.tema = f.tema or next((t for t in P.TEMAS if norm(t) in q), None)
    f.formato = f.formato or next((t for t in P.FORMATOS if norm(t) in q), None)
    if f.porte:
        df = df[df.porte == f.porte]
    if f.periodo_dias:
        df = df[df.idade_dias <= f.periodo_dias]
    if f.tema:
        df = df[df.tema_principal == f.tema]
    if f.formato:
        df = df[df.formato_video == f.formato]
    if e.segment:
        termos = SEGMENTOS.get(e.segment.lower(), [e.segment])
        texto = (df.titulo + " " + df.descricao + " " + df.tags).map(norm)
        df = df[texto.str.contains("|".join(norm(t) for t in termos), regex=True)]
    lt = P.lift_table(df)
    lt = lt[(lt.n_top >= 2) & lt.lift.notna()].sort_values("lift", ascending=False).head(15)
    top = df[df.grupo == "top"].copy()
    # relevância simples: palavras da pergunta no título/gancho; empate -> engajamento
    palavras = [w for w in q.split() if len(w) > 3]
    top["rel"] = (top.titulo + " " + top.hook_primeiros_3s).map(norm).map(lambda t: sum(w in t for w in palavras))
    top = top.sort_values(["rel", "er"], ascending=False).head(n_refs)
    refs = [PostRef(video_id=r.video_id, url=r.url, canal=r.canal, titulo=r.titulo, er=round(r.er, 5),
                    outlier=None if r.outlier != r.outlier else round(r.outlier, 2),
                    categorias={c: getattr(r, c) for c in COLS_REF}) for r in top.itertuples()]
    achados = [Achado(**r) for r in lt.to_dict("records")]
    n_top = int((df.grupo == "top").sum())
    return achados, refs, n_top, df[df.grupo == "top"].forca_hook_0a10.median()


# ---------- grafo ----------

class Estado(TypedDict, total=False):
    entrada: Entrada
    achados: list[Achado]
    refs: list[PostRef]
    n_top: int
    hook_ref: float
    redacao: Redacao
    feedback: str
    tentativas: int


INSTRUCOES = {
    "analisar": "Responda a pergunta com base nos achados. creatives deve ser lista vazia.",
    "recomendar": "Dê de 3 a 5 recomendações práticas de conteúdo para o Instagram da Stone, cada uma citando "
                  "os achados e os video_ids que a sustentam. creatives pode ter 1 exemplo.",
    "gerar_criativo": "Gere 3 criativos (gancho, roteiro de 30-45s em tópicos com marcação de tempo, legenda e CTA) "
                      "para o Instagram da Stone, voltados a micro e pequenos empreendedores.",
}


def no_recuperar(s):
    achados, refs, n_top, hook_ref = recuperar(s["entrada"])
    return {"achados": achados, "refs": refs, "n_top": n_top, "hook_ref": hook_ref, "tentativas": 0}


def no_redigir(s):
    e = s["entrada"]
    prompt = f"""Você é estrategista de conteúdo da Stone (maquininha e conta para micro e pequenos empreendedores).
Use APENAS os dados abaixo. Não invente números. Cite video_ids entre colchetes na explicação.
Cada criativo deve listar em inspirado_em os video_ids das referências que o inspiraram (só ids da lista).
Escreva em português do Brasil, linguagem simples de lojista.

Tarefa ({e.mode}): {INSTRUCOES[e.mode]}
Pergunta: {e.query}
Segmento: {e.segment or "todos"}
Publicações de alto desempenho analisadas no recorte: {s["n_top"]}

Achados (freq no top vs. no resto; lift > 1 = mais comum entre os de alto desempenho):
{json.dumps([a.model_dump() for a in s["achados"]], ensure_ascii=False)}

Publicações de referência:
{json.dumps([r.model_dump() for r in s["refs"]], ensure_ascii=False, default=str)}
{("Correção pedida na versão anterior: " + s["feedback"]) if s.get("feedback") else ""}"""
    return {"redacao": P.gemini(prompt, Redacao), "tentativas": s["tentativas"] + 1, "feedback": ""}


def no_checar(s):
    """Rastreabilidade + autoavaliação pela própria rubrica."""
    ids = {r.video_id for r in s["refs"]}
    problemas = []
    for i, c in enumerate(s["redacao"].creatives, 1):
        if not c.inspirado_em or not set(c.inspirado_em) <= ids:
            problemas.append(f"criativo {i} sem referência válida")
            continue
        if s["entrada"].mode == "gerar_criativo":
            ch = P.gemini(f"Avalie este roteiro de vídeo curto segundo a rubrica.\nGancho: {c.gancho}\n"
                          f"Roteiro: {c.roteiro}\nCTA: {c.cta}", Checagem)
            if s["hook_ref"] == s["hook_ref"] and ch.forca_hook_0a10 < s["hook_ref"]:
                problemas.append(f"criativo {i}: força do gancho {ch.forca_hook_0a10} abaixo da mediana do top "
                                 f"({s['hook_ref']:.0f}); deixe o gancho mais forte")
            if not ch.tem_cta:
                problemas.append(f"criativo {i}: sem chamada para ação clara")
    return {"feedback": "; ".join(problemas)}


def proximo(s):
    return "redigir" if s.get("feedback") and s["tentativas"] < 3 else END


g = StateGraph(Estado)
g.add_node("recuperar", no_recuperar)
g.add_node("redigir", no_redigir)
g.add_node("checar", no_checar)
g.add_edge(START, "recuperar")
g.add_edge("recuperar", "redigir")
g.add_edge("redigir", "checar")
g.add_conditional_edges("checar", proximo)
grafo = g.compile()


def run(mode, query, segment=None, filters=None) -> dict:
    """Ponto de entrada único (função Python e servidor MCP)."""
    e = Entrada(mode=mode, query=query, segment=segment, filters=Filtros(**(filters or {})))
    s = grafo.invoke({"entrada": e})
    ids = {r.video_id for r in s["refs"]}
    # nunca sai criativo sem lastro em publicação real
    criativos = [c for c in s["redacao"].creatives if c.inspirado_em and set(c.inspirado_em) <= ids]
    saida = Saida(findings=s["achados"], reference_posts=s["refs"], creatives=criativos,
                  confidence_flag=s["n_top"] < 10, explanation=s["redacao"].explanation)
    os.makedirs(P.DATA, exist_ok=True)
    with open(f"{P.DATA}/execucoes.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"em": datetime.now().isoformat(), "entrada": e.model_dump(),
                             "tentativas": s["tentativas"], "pendencias": s.get("feedback", ""),
                             "saida": saida.model_dump()}, ensure_ascii=False) + "\n")
    return saida.model_dump()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["analisar", "recomendar", "gerar_criativo"])
    ap.add_argument("query")
    ap.add_argument("--segment")
    ap.add_argument("--porte", choices=["pequeno", "medio", "grande"])
    a = ap.parse_args()
    out = run(a.mode, a.query, a.segment, {"porte": a.porte} if a.porte else None)
    print(out["explanation"], "\n")
    for c in out["creatives"]:
        print(f"GANCHO: {c['gancho']}\nROTEIRO:\n{c['roteiro']}\nLEGENDA: {c['legenda']}\nCTA: {c['cta']}\n"
              f"INSPIRADO EM: {', '.join('https://www.youtube.com/shorts/' + i for i in c['inspirado_em'])}\n")
    print(f"Referências: {len(out['reference_posts'])} | baixa confiança: {out['confidence_flag']}")
