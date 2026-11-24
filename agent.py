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

import pandas as pd

import pipeline as P


# ---------- contrato (TAPI, seção 7) ----------

class Filtros(BaseModel):
    porte: Literal["micro", "medio", "grande"] | None = None
    plataforma: Literal["youtube", "instagram"] | None = None
    pilar: str | None = None
    periodo_dias: int | None = None
    tema: str | None = None
    formato: str | None = None


class Entrada(BaseModel):
    mode: Literal["analisar", "recomendar", "gerar_criativo"]
    query: str
    segment: str | None = None
    filters: Filtros = Filtros()


class Achado(BaseModel):
    selo: str = "só mercado"  # confirmado | contradito | só mercado | inconclusivo (mercado x Ads do Impulso)
    campo: str
    valor: str
    freq_top: float
    freq_resto: float
    lift: float | None
    n_top: int


class PostRef(BaseModel):
    plataforma: str
    video_id: str
    url: str
    canal: str
    titulo: str
    er: float
    outlier: float | None
    categorias: dict


class Criativo(BaseModel):
    formato: str      # reel | carrossel | estático | story
    pilar: str        # um dos 5 pilares editoriais do Impulso
    gancho: str
    roteiro: str
    legenda: str
    cta: str
    inspirado_em: list[str]  # video_ids das publicações de referência


class Saida(BaseModel):
    filtros_relaxados: list[str] = []  # filtros soltos por falta de referências no recorte
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
    generico_0a10: int
    convite_participacao: bool
    tem_cta: bool
    tom_impulso: bool  # próximo, acolhedor, educativo, sem jargão


# ---------- recuperação (determinística, sem LLM) ----------

SEGMENTOS = {
    "alimentação": ["comida", "restaurante", "lanche", "doce", "confeitaria", "delivery", "marmita", "food", "bolo"],
    "beleza": ["salão", "salao", "beleza", "estética", "unha", "cabelo", "maquiagem", "barbearia", "nail"],
    "varejo": ["loja", "varejo", "roupa", "moda", "boutique", "estoque", "vitrine"],
    "serviços": ["serviço", "servico", "prestador", "autônomo", "autonomo", "cliente", "orçamento"],
}
COLS_REF = ["tipo_post", "formato_video", "tipo_hook", "hook_primeiros_3s", "tema_principal", "pilar_impulso",
            "gatilho_identificacao", "convite_participacao", "tem_cta", "tipo_cta", "prova_social", "elementos_top5"]
REDATOR = os.getenv("AGENT_MODEL", "deepseek/deepseek-v4.1-flash-1017")  # crédito da Feita restrito a ele
CHECADOR = REDATOR  # ponytail: ideal seria outro modelo checando; só o DeepSeek tem saldo


def selos():
    f = f"{P.DATA}/padroes_selados.csv"
    if not os.path.exists(f):
        return {}
    d = pd.read_csv(f, dtype={"valor": str})
    return {(r.campo, r.valor): r.selo for r in d.itertuples()}


def norm(s):
    return unicodedata.normalize("NFKD", str(s).lower()).encode("ascii", "ignore").decode()


def recuperar(e: Entrada, n_refs=8):
    df = P.carregar(P.db())
    f = e.filters.model_copy()
    q = norm(e.query)
    # termos da pergunta que batem com o vocabulário da rubrica viram filtro
    f.tema = f.tema or next((t for t in P.TEMAS if norm(t) in q), None)
    f.formato = f.formato or next((t for t in P.FORMATOS if norm(t) in q), None)
    f.pilar = f.pilar or next((t for t in P.PILARES if norm(t) in q), None)
    f.plataforma = f.plataforma or ("instagram" if "instagram" in q or "reels" in q or "carrossel" in q
                                    else "youtube" if "youtube" in q or "shorts" in q else None)
    # filtros em ordem de importância; se sobram < 3 posts no top, solta do fim para o começo
    filtros = []
    if f.plataforma:
        filtros.append(("plataforma", lambda d: d.plataforma == f.plataforma))
    if f.porte:
        filtros.append(("porte", lambda d: d.porte == f.porte))
    if f.periodo_dias:
        filtros.append(("periodo", lambda d: d.idade_dias <= f.periodo_dias))
    if e.segment:
        termos = "|".join(norm(t) for t in SEGMENTOS.get(e.segment.lower(), [e.segment]))
        filtros.append(("segmento", lambda d: (d.titulo + " " + d.descricao + " " + d.tags).map(norm)
                        .str.contains(termos, regex=True)))
    if f.pilar:
        filtros.append(("pilar", lambda d: d.pilar_impulso == f.pilar))
    if f.tema:
        filtros.append(("tema", lambda d: d.tema_principal == f.tema))
    if f.formato:
        filtros.append(("formato", lambda d: d.formato_video == f.formato))
    relaxados = []
    while True:
        sub = df
        for _, cond in filtros:
            sub = sub[cond(sub)]
        if (sub.grupo == "top").sum() >= 3 or not filtros:
            break
        relaxados.append(filtros.pop()[0])
    df = sub
    lt = P.lift_table(df)
    lt = lt[(lt.plataforma == "todas") & (lt.n_top >= 2) & lt.lift.notna()].drop(columns="plataforma")
    lt = lt[lt.campo != "generico"].sort_values("lift", ascending=False).head(15)
    sl = selos()
    lt["selo"] = [sl.get((c, v), "só mercado") for c, v in zip(lt.campo, lt.valor)]
    top = df[df.grupo == "top"].copy()
    # relevância simples: palavras da pergunta no título/gancho; empate -> engajamento
    palavras = [w for w in q.split() if len(w) > 3]
    top["rel"] = (top.titulo + " " + top.descricao.str[:300] + " " + top.hook_primeiros_3s).map(norm).map(lambda t: sum(w in t for w in palavras))
    top = top.sort_values(["rel", "er"], ascending=False).head(n_refs)
    refs = [PostRef(plataforma=r.plataforma, video_id=r.video_id, url=r.url, canal=r.canal,
                    titulo=r.titulo or r.descricao[:120], er=round(r.er, 5),
                    outlier=None if r.outlier != r.outlier else round(r.outlier, 2),
                    categorias={c: getattr(r, c) for c in COLS_REF}) for r in top.itertuples()]
    achados = [Achado(**r) for r in lt.to_dict("records")]
    n_top = int((df.grupo == "top").sum())
    return achados, refs, n_top, df[df.grupo == "top"].forca_hook_0a10.median(), relaxados


# ---------- grafo ----------

class Estado(TypedDict, total=False):
    entrada: Entrada
    achados: list[Achado]
    refs: list[PostRef]
    n_top: int
    hook_ref: float
    relaxados: list[str]
    redacao: Redacao
    feedback: str
    tentativas: int


INSTRUCOES = {
    "analisar": "Responda a pergunta com base nos achados. creatives deve ser lista vazia.",
    "recomendar": "Dê de 3 a 5 recomendações práticas de conteúdo para o Instagram do Impulso Stone, cada uma citando "
                  "os achados e os video_ids que a sustentam. creatives pode ter 1 exemplo.",
    "gerar_criativo": "Gere 3 criativos para o Instagram do Impulso Stone (gancho, roteiro de Reels de 30-45s em "
                      "tópicos com marcação de tempo ou sequência de slides de carrossel, legenda e CTA).",
}


def no_recuperar(s):
    achados, refs, n_top, hook_ref, relaxados = recuperar(s["entrada"])
    return {"achados": achados, "refs": refs, "n_top": n_top, "hook_ref": hook_ref, "relaxados": relaxados,
            "tentativas": 0}


def no_redigir(s):
    return {"redacao": P.llm(prompt_redacao(s), Redacao, model=REDATOR), "tentativas": s["tentativas"] + 1, "feedback": ""}


def prompt_redacao(s):
    """Prompt completo do redator a partir do estado recuperado (usado aqui e no MCP, onde quem redige é o cliente)."""
    e = s["entrada"]
    return f"""Você é estrategista de conteúdo do Impulso Stone (@impulsostone), o braço social do Instituto Stone
que capacita micro e pequenos empreendedores (público: 70% mulheres, 35-54 anos; 94% das views vêm de não seguidores).
Tom de voz: próximo, acolhedor, educativo, sem jargão. Objetivo dos posts: o empreendedor participar e se inscrever no Impulso.
Pilares editoriais: educação financeira, gestão e vendas, histórias reais, especialistas, comunidade.
Aprendizados dos Ads do Impulso: convite à participação e identificação (nicho, data do calendário, dor real,
pessoa real) passam de 6-8% de CTR; frase motivacional genérica e post sem chamada para ação ficam abaixo de 1%.
Use APENAS os dados abaixo. Não invente números. Cite video_ids entre colchetes na explicação.
Achados com selo "confirmado" valem no mercado E nos Ads do Impulso: priorize-os e diga isso.
Cada criativo deve listar em inspirado_em os video_ids das referências que o inspiraram (só ids da lista).

Tarefa ({e.mode}): {INSTRUCOES[e.mode]}
Pergunta: {e.query}
Segmento: {e.segment or "todos"}
Publicações de alto desempenho analisadas no recorte: {s["n_top"]}
{("Filtros soltos por falta de exemplos (diga isso na explicação): " + ", ".join(s["relaxados"])) if s["relaxados"] else ""}

Achados (freq no top vs. no resto; lift > 1 = mais comum entre os de alto desempenho):
{json.dumps([a.model_dump() for a in s["achados"]], ensure_ascii=False)}

Publicações de referência:
{json.dumps([r.model_dump() for r in s["refs"]], ensure_ascii=False, default=str)}
{("Correção pedida na versão anterior: " + s["feedback"]) if s.get("feedback") else ""}"""


def no_checar(s):
    """Rastreabilidade + autoavaliação pela própria rubrica."""
    ids = {r.video_id for r in s["refs"]}
    problemas = []
    for i, c in enumerate(s["redacao"].creatives, 1):
        if not c.inspirado_em or not set(c.inspirado_em) <= ids:
            problemas.append(f"criativo {i} sem referência válida")
            continue
        if s["entrada"].mode == "gerar_criativo":
            ch = P.llm("Avalie este roteiro de post para pequenos empreendedores. generico_0a10: 10 = frase que serve "
                       "para qualquer público. tom_impulso: próximo, acolhedor, educativo e sem jargão.\n"
                       f"Gancho: {c.gancho}\nRoteiro: {c.roteiro}\nLegenda: {c.legenda}\nCTA: {c.cta}", Checagem,
                       model=CHECADOR)
            if s["hook_ref"] == s["hook_ref"] and ch.forca_hook_0a10 < s["hook_ref"]:
                problemas.append(f"criativo {i}: força do gancho {ch.forca_hook_0a10} abaixo da mediana do top "
                                 f"({s['hook_ref']:.0f}); deixe o gancho mais forte")
            if not ch.tem_cta:
                problemas.append(f"criativo {i}: sem chamada para ação clara")
            if ch.generico_0a10 >= 6:
                problemas.append(f"criativo {i}: genérico demais ({ch.generico_0a10}/10); fale com um nicho, data ou dor")
            if not ch.convite_participacao:
                problemas.append(f"criativo {i}: convide o empreendedor a participar (contar, perguntar, responder)")
            if not ch.tom_impulso:
                problemas.append(f"criativo {i}: ajuste o tom (próximo, acolhedor, sem jargão)")
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
    saida = Saida(filtros_relaxados=s["relaxados"], findings=s["achados"], reference_posts=s["refs"], creatives=criativos,
                  confidence_flag=s["n_top"] < 10 or bool(s["relaxados"]), explanation=s["redacao"].explanation)
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
    ap.add_argument("--porte", choices=["micro", "medio", "grande"])
    a = ap.parse_args()
    out = run(a.mode, a.query, a.segment, {"porte": a.porte} if a.porte else None)
    print(out["explanation"], "\n")
    urls = {r["video_id"]: r["url"] for r in out["reference_posts"]}
    for c in out["creatives"]:
        print(f"[{c['formato']} · {c['pilar']}]\nGANCHO: {c['gancho']}\nROTEIRO:\n{c['roteiro']}\n"
              f"LEGENDA: {c['legenda']}\nCTA: {c['cta']}\nINSPIRADO EM: {', '.join(urls[i] for i in c['inspirado_em'])}\n")
    print(f"Referências: {len(out['reference_posts'])} | baixa confiança: {out['confidence_flag']}")
