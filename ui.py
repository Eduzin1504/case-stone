"""Pauta Impulso: dados (só leitura, com cache) e peças visuais compartilhadas pelas páginas de paginas/."""
import html
import json
import math
import os
import re
import sqlite3

import streamlit as st

import pipeline as P

RAIZ = os.path.dirname(os.path.abspath(__file__))
E = html.escape

# ---------------------------------------------------------------- focos e rótulos
SEG_NOME = {"gestao_financas": "gestão e finanças", "vendas_marketing": "vendas e marketing", "pagamentos_maquininha":
            "pagamentos", "alimentacao": "alimentação", "beleza": "beleza", "varejo_moda": "varejo e moda",
            "servicos": "serviços", "geral": "geral"}
TIPO_NOME = {"clips": "Reels", "carousel_container": "Carrossel", "feed": "Imagem"}
PORTE_NOME = {"micro": "micro (até 10 mil)", "medio": "médio (10–100 mil)", "grande": "grande (100 mil+)"}
PORTE_CURTO = {"micro": "micro", "medio": "médio", "grande": "grande"}
PLAT_NOME = {"instagram": "Instagram", "youtube": "YouTube", "todas": "Todas juntas"}

# FOCO_B_DIR / FOCO_B_PLAYBOOK existem para testar a interface sem os arquivos do Foco B.
_B = os.getenv("FOCO_B_DIR", P.DATA)
FOCOS = {
    "A": dict(id="A", nome="Impulso → empreendedor",
              desc="Conteúdo que engaja donos de pequeno negócio (o público do Impulso).",
              db=P.DB, padroes=f"{P.DATA}/padroes_selados.csv", perfis=f"{P.DATA}/perfis_destaque.csv",
              playbook="PLAYBOOK.md", midia=f"{P.DATA}/midia",
              campos=dict(tema="r_tema_principal", formato="r_formato_video", gancho="r_tipo_hook",
                          gancho_txt="hook_primeiros_3s"),
              elegivel="perfis validados à mão, com 5 posts ou mais, e posts com pelo menos 7 dias que falam com dono de "
                       "pequeno negócio"),
    "B": dict(id="B", nome="Negócio → cliente",
              desc="Como o pequeno negócio engaja o cliente final dele.",
              db=f"{_B}/foco_b.db", padroes=f"{_B}/b_achados.csv", perfis=f"{_B}/b_perfis_destaque.csv",
              playbook=os.getenv("FOCO_B_PLAYBOOK", "PLAYBOOK_B.md"), midia=f"{_B}/midia_b",
              campos=dict(tema="segmento", formato="r_formato", gancho="r_tipo_gancho", gancho_txt="gancho_3s"),
              elegivel="posts e perfis que passaram nos filtros deste foco"),
}
ARQUIVO = {"db": "banco com o ranking", "padroes": "tabela de padrões", "perfis": "lista de perfis em destaque",
           "playbook": "playbook"}
ROTULO = {
    "tema_principal": "Tema", "tipo_hook": "Gancho", "tipo_gancho": "Gancho", "pilar_impulso": "Pilar do Impulso",
    "publico_alvo": "Público", "formato": "Formato", "formato_video": "Formato", "tipo_cta": "Chamada para ação",
    "mostra_produto": "Mostra o produto", "mostra_preco": "Mostra o preço", "tem_cta": "Tem chamada para ação",
    "tem_rosto": "Tem rosto", "tom": "Tom", "gatilho_identificacao": "Identificação",
    "convite_participacao": "Convida a participar", "prova_social": "Prova social", "texto_na_tela": "Texto na tela",
    "mostra_processo": "Mostra como é feito", "rosto_do_dono": "Rosto do dono", "cliente_aparece": "Cliente aparece",
    "tem_oferta_ou_prazo": "Oferta ou prazo", "gatilho_sazonal": "Data comemorativa",
    "convida_a_responder": "Convida a responder", "criador_e_empreendedor_real": "Quem posta é empreendedor de verdade",
    "usa_linguagem_regional": "Linguagem regional", "oferta_ou_beneficio_explicito": "Benefício explícito",
    "forca_hook_0a10": "Força do gancho", "ritmo_cortes_0a10": "Ritmo dos cortes", "clareza_mensagem_0a10": "Clareza",
    "generico_0a10": "Genérico", "qualidade_producao_0a10": "Qualidade da produção",
    "apetite_ou_desejo_0a10": "Desejo que desperta", "segmento": "Segmento", "tipo_post": "Tipo de post",
    "duracao_faixa": "Duração", "legenda_tamanho": "Legenda", "tipo_criador": "Quem posta", "generico": "Genérico",
    "desejo_alto": "Desperta desejo", "producao_alta": "Produção caprichada",
}
VALOR = {"donos_de_negocio": "donos de negócio", "consumidor_final": "consumidor final", "pessoa_real": "pessoa real",
         "data_sazonal": "data comemorativa", "empreendedor_real": "empreendedor de verdade",
         "instituicao_ou_marca": "instituição ou marca", "True": "sim", "False": "não", "reel": "Reels", **SEG_NOME}
GRUPOS = [  # agrupamento da página Padrões
    ("Gancho", "Como o post abre, nos primeiros segundos.", ["tipo_hook", "tipo_gancho"]),
    ("Formato", "O jeito de apresentar o conteúdo.",
     ["formato_video", "formato", "tipo_post", "duracao_faixa", "legenda_tamanho", "texto_na_tela", "producao_alta"]),
    ("Tema e segmento", "Do que o post fala e para quem.", ["tema_principal", "segmento", "pilar_impulso"]),
    ("Chamada para ação", "O que o post pede para a pessoa fazer.",
     ["tem_cta", "tipo_cta", "convite_participacao", "convida_a_responder", "oferta_ou_beneficio_explicito",
      "tem_oferta_ou_prazo", "mostra_preco"]),
    ("Quem aparece", "Rosto, cliente, pessoa de verdade.",
     ["tem_rosto", "rosto_do_dono", "cliente_aparece", "criador_e_empreendedor_real", "tipo_criador",
      "gatilho_identificacao", "prova_social", "usa_linguagem_regional"]),
    ("Produto e tom", "O que se mostra e em que clima.",
     ["mostra_produto", "mostra_processo", "desejo_alto", "tom", "generico", "gatilho_sazonal"]),
]
SELO_CLS = {"confirmado": "ok", "contradito": "bad", "só mercado": "mut", "inconclusivo": "mut"}


def rotulo(campo):
    return ROTULO.get(campo) or campo.removesuffix("_0a10").replace("_", " ").capitalize()


def valor_nome(v):
    v = str(v)
    return VALOR.get(v, v.replace("_", " "))


def nome_padrao(campo, valor):
    """'tema_principal', 'finanças' -> 'Tema: finanças'; 'mostra_preco', 'True' -> 'Mostra o preço'."""
    v = str(valor)
    if v in ("True", "sim"):
        return rotulo(campo)
    if v in ("False", "não"):
        return f"{rotulo(campo)}: não"
    return f"{rotulo(campo)}: {valor_nome(v)}"


# ---------------------------------------------------------------- números em pt-BR
def _ok(x):
    return x is not None and x == x and not (isinstance(x, float) and math.isinf(x))


def num(x):
    return f"{int(x):,}".replace(",", ".") if _ok(x) else "—"


def dec(x, casas=1):
    return f"{x:.{casas}f}".replace(".", ",")


def compacto(x):
    if not _ok(x):
        return "—"
    x = float(x)
    if x >= 1e6:
        return f"{dec(x / 1e6)} mi"
    if x >= 1e4:
        return f"{x / 1e3:.0f} mil"
    if x >= 1e3:
        return f"{dec(x / 1e3)} mil"
    return f"{x:.0f}"


def pct(x, casas=1):
    """Fração -> '2,3%'."""
    if not _ok(x):
        return "—"
    x = x * 100
    return f"{x:.0f}%" if x >= 100 or casas == 0 else f"{dec(x, casas)}%"


def data_br(d):
    """'2026-07-03' -> '03/07/2026'."""
    d = str(d)
    return f"{d[8:10]}/{d[5:7]}/{d[:4]}" if len(d) >= 10 and d[4] == "-" else E(d)


def vezes(resid):
    """Resíduo do modelo (escala log) -> '2,7×' o esperado."""
    if not _ok(resid):
        return "—"
    v = math.exp(min(resid, 50))
    return f"{dec(v)}×" if v < 10 else (f"{v:.0f}×" if v < 1000 else f"{compacto(v)}×")


# ---------------------------------------------------------------- leitura tolerante
def versao(f):
    """Entra na chave do cache: quando outro processo regrava o arquivo, a interface relê."""
    return os.path.getmtime(f) if os.path.exists(f) else 0


def conectar(db):
    if not os.path.exists(db):
        raise FileNotFoundError(db)
    return sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=3)  # só leitura: nunca cria banco vazio


def tentar(fn, *a, **kw):
    """Leitura resiliente: o erro não vai para o cache nem para a tela; quem chama mostra o estado vazio."""
    try:
        return fn(*a, **kw)
    except Exception:
        return None


def tem(d, col):
    return col in d and d[col].notna().any()


@st.cache_data(ttl=600, show_spinner=False)
def _midia_idx(pasta, v):
    """{video_id: (nº de imagens, tem mp4)} com um único listdir."""
    idx = {}
    for f in os.listdir(pasta):
        if f.endswith(".mp4"):
            n, _ = idx.get(f[:-4], (0, False))
            idx[f[:-4]] = (n, True)
        elif f.endswith(".jpg") and "_" in f:
            vid = f.rsplit("_", 1)[0]
            n, m = idx.get(vid, (0, False))
            idx[vid] = (n + 1, m)
    return idx


def midia_idx(fonte):
    return tentar(_midia_idx, fonte["midia"], versao(fonte["midia"])) or {}


@st.cache_data(ttl=600, show_spinner=False)
def _base_info(db, v):
    c = conectar(db)
    plat = dict(c.execute("select plataforma, count(*) from ranking group by plataforma").fetchall())
    perfis = c.execute("select count(distinct canal) from ranking").fetchone()[0]
    quando = tentar(lambda: (c.execute("select max(coletado_em) from videos").fetchone()[0] or "")[:10]) or ""
    return plat, perfis, quando


def base_info(fonte):
    return tentar(_base_info, fonte["db"], versao(fonte["db"]))


@st.cache_data(ttl=600, show_spinner=False)
def _rubricas(db, v):
    c = conectar(db)
    return {vid: (tentar(json.loads, r) or {}) for vid, r in c.execute("select video_id, rubrica from categorias")}


def rubricas(fonte):
    return tentar(_rubricas, fonte["db"], versao(fonte["db"])) or {}


@st.cache_data(ttl=600, show_spinner=False)
def _ranking(db, v, pasta_midia, v_midia):
    """Ranking + campos curtos da rubrica (prefixo r_) + o que existe de mídia local. Colunas ausentes não quebram."""
    import numpy as np
    import pandas as pd
    c = conectar(db)
    r = pd.read_sql("select * from ranking", c)
    r = r.drop(columns=[x for x in ["tags", "thumbnail", "video_url", "imagens", "comentarios_txt", "coletado_em"] if x in r])
    rub = tentar(_rubricas, db, v) or {}
    if rub:
        rb = pd.DataFrame.from_dict(rub, orient="index")
        curtos = [k for k in rb if not rb[k].map(lambda x: isinstance(x, (list, dict)) or (isinstance(x, str) and len(x) > 60)).any()]
        rb = rb[curtos].apply(lambda col: col.map(lambda x: {True: "sim", False: "não"}.get(x, x) if isinstance(x, bool) else x))
        r = r.merge(rb.add_prefix("r_"), left_on="video_id", right_index=True, how="left")
    for col in ["titulo", "descricao", "canal", "url", "segmento", "porte", "tipo", "resid", "er", "channel_id"]:
        if col not in r:
            r[col] = None
    r["formato_post"] = r.tipo.map(TIPO_NOME).fillna("Post")
    r.loc[r.plataforma == "youtube", "formato_post"] = "Short"
    r["descricao"] = r.descricao.fillna("").str.slice(0, 1200)
    r["post"] = r.titulo.fillna("").where(r.titulo.fillna("") != "", r.descricao).str.slice(0, 140)
    r["seg"] = r.segmento  # valor cru, para casar com a tabela de padrões
    r["segmento"] = r.segmento.map(SEG_NOME).fillna(r.segmento)
    r["top"] = r.top.fillna(0).astype(bool)
    for col in ["top_er_puro", "elegivel"]:
        if col in r:
            r[col] = r[col].fillna(0).astype(bool)
    if "publicado" in r:
        r["publicado"] = r.publicado.astype(str).str[:10].where(r.publicado.notna())
    if tem(r, "pct_intencao") and r.pct_intencao.max() > 1:
        r["pct_intencao"] = r.pct_intencao / 100  # ponytail: aceita percentual (0–100) ou fração (0–1); guarda fração
    idx = tentar(_midia_idx, pasta_midia, v_midia) or {}
    r["n_img"] = [idx.get(i, (0, False))[0] for i in r.video_id]
    r["tem_video"] = r.video_id.map(lambda i: idx.get(i, (0, False))[1]).astype(bool) | (r.plataforma == "youtube")
    r["tem_midia"] = (r.n_img > 0) | r.tem_video
    r["analisado"] = r.video_id.isin(rub)
    r["resid"] = pd.to_numeric(r.resid, errors="coerce")
    r["pos_top"] = r[r.top].groupby("plataforma").resid.rank(ascending=False, method="first")
    r["duracao_faixa"] = pd.cut(pd.to_numeric(r.get("duracao_s"), errors="coerce"), [0, 15, 30, 60, np.inf],
                                labels=["<15s", "15-30s", "30-60s", ">60s"]).astype(object) if "duracao_s" in r else None
    return r


def ranking(fonte):
    return tentar(_ranking, fonte["db"], versao(fonte["db"]), fonte["midia"], versao(fonte["midia"]))


@st.cache_data(ttl=600, show_spinner=False)
def _csv(f, v, **kw):
    import pandas as pd
    return pd.read_csv(f, **kw)


def ler_csv(f, **kw):
    """DataFrame ou None (arquivo ausente, vazio ou ilegível)."""
    d = tentar(lambda: _csv(f, versao(f), **kw)) if os.path.exists(f) else None
    return d if d is not None and len(d) else None


def padroes(fonte):
    ps = ler_csv(fonte["padroes"], dtype={"valor": str})
    if ps is None or not {"campo", "valor", "freq_top", "freq_resto"} <= set(ps.columns):
        return None
    if "lift" not in ps:
        ps = ps.assign(lift=ps.freq_top / ps.freq_resto.where(ps.freq_resto > 0))
    if "n_top" not in ps:
        ps = ps.assign(n_top=5)
    if "plataforma" not in ps:
        ps = ps.assign(plataforma="todas")
    return ps


def intencao(fonte):
    """Foco B: % médio de comentários com intenção de compra, por característica do post (mesma conta do playbook)."""
    import pandas as pd
    r = ranking(fonte)
    if r is None or not tem(r, "pct_intencao") or "r_formato" not in r:
        return None
    d = r[r.pct_intencao.notna() & r.analisado]
    if "r_relevante_b" in d:
        d = d[d.r_relevante_b != "não"]
    out = []
    for nome, col, v in [("Mostra o preço", "r_mostra_preco", "sim"), ("Não mostra o preço", "r_mostra_preco", "não"),
                         ("Humor ou trend", "r_formato", "humor/trend"), ("Produto em destaque", "r_formato", "produto em destaque"),
                         ("Bastidor de produção", "r_formato", "bastidor de produção")]:
        g = d[d[col] == v] if col in d else d.head(0)
        if len(g):
            out.append(dict(grupo=nome, pct=float(g.pct_intencao.mean()), posts=len(g)))
    return pd.DataFrame(out) if out else None


def secao_md(arquivo, inicio, fim=None):
    t = tentar(lambda: open(arquivo, encoding="utf-8").read()) or ""
    a = t.find(inicio)
    if a < 0:
        return ""
    b = t.find(fim, a + len(inicio)) if fim else -1
    return t[a:b if b > 0 else None]


def plataformas(d):
    return sorted(d.plataforma.dropna().unique(), key=lambda x: (x != "instagram", x == "todas", x))  # Instagram primeiro


def portes(d):
    return [p for p in PORTE_NOME if p in set(d.porte)] + sorted(set(d.porte.dropna()) - set(PORTE_NOME))


def regua(fonte):
    """A régua em 4 passos, linguagem simples: (título, texto)."""
    return [
        ("Medimos o engajamento", "A nota de cada post é o ER: curtidas + comentários, divididos pelos seguidores do perfil."),
        ("Calculamos o esperado", "Só olhar o maior ER premia perfil pequeno e quem já engaja muito. Um modelo estima quanto "
         "cada post deveria engajar pelo tamanho do perfil, formato, idade do post e histórico do criador."),
        ("Ficamos com quem superou", "O top 10% são os posts que mais passaram desse esperado, dentro de cada plataforma e "
         "faixa de tamanho de perfil."),
        ("Sem deixar um criador dominar", f"Só concorre a base elegível ({fonte['elegivel']}) e cada criador entra com no "
         "máximo 3 posts."),
    ]


@st.cache_data
def salvas(v=0):
    """Execuções já feitas pelo agente (data/execucoes.jsonl), para a demo funcionar sem rede."""
    f = f"{P.DATA}/execucoes.jsonl"
    if not os.path.exists(f):
        return []
    out = [d for d in (tentar(json.loads, l) for l in open(f, encoding="utf-8") if l.strip()) if d]
    vistos, uniq = set(), []
    for d in reversed(out):  # a mais recente de cada pergunta
        chave = (d["entrada"]["mode"], d["entrada"]["query"])
        if chave not in vistos and (d["saida"]["creatives"] or d["entrada"]["mode"] != "gerar_criativo"):
            vistos.add(chave)
            uniq.append(d)
    return uniq


# ---------------------------------------------------------------- mídia
def capa_path(vid, fonte):
    f = f"{fonte['midia']}/{vid}_0.jpg"
    return f if os.path.exists(f) else None


def thumb_url(vid, plataforma, fonte):
    """URL da miniatura: YouTube direto (capa vertical do Short); Instagram = capa local reduzida uma vez em static/thumbs."""
    if plataforma == "youtube":
        return f"https://i.ytimg.com/vi/{vid}/oar2.jpg"
    dst = f"{RAIZ}/static/thumbs/{vid}.jpg"
    if not os.path.exists(dst):
        src = capa_path(vid, fonte)
        if not src:
            return None
        try:
            from PIL import Image
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            im = Image.open(src).convert("RGB")
            im.thumbnail((400, 800))
            im.save(dst + ".tmp", "JPEG", quality=80)
            os.replace(dst + ".tmp", dst)
        except Exception:
            return None
    return f"/app/static/thumbs/{vid}.jpg"


def _bg(vid, plataforma, fonte):
    u = thumb_url(vid, plataforma, fonte)
    if not u:
        return None
    if plataforma == "youtube":  # se a capa vertical não existir, cai na capa padrão
        return f"background-image:url('{E(u)}'),url('https://i.ytimg.com/vi/{E(vid)}/hqdefault.jpg')"
    return f"background-image:url('{E(u)}')"


# ---------------------------------------------------------------- estilo
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Lexend:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
:root{--forest:#00442f;--lime:#c5ff1f;--hl:#d9ff66;--bg:#f7faf7;--surface:#fff;--sunk:#eef3ef;--fg:#14231b;--muted:#536359;
--line:#dfe7e1;--data:#1f9e55;--data-soft:#b9d3c1;--ok:#0b6b3d;--ok-bg:#e6f3ea;--warn:#8a5a00;--warn-bg:#fbf2df;--bad:#b02d63;--bad-bg:#fbe9f0;
--mono:"JetBrains Mono",ui-monospace,monospace}
html,body,.stApp,.stMarkdown,button,input,textarea,p,li,label,h2,h3,h4{font-family:"Lexend",system-ui,sans-serif}
.block-container{padding-top:2.2rem;padding-bottom:4rem;max-width:1240px}
h1,.pg-h1{font-family:"Anton","Arial Narrow",sans-serif!important;font-weight:400!important;text-transform:uppercase;color:var(--forest);
letter-spacing:.01em;font-size:2.5rem!important;line-height:1.05!important;margin:0!important;padding:0!important}
[data-testid="stMainBlockContainer"] h2,.sec h2{font-size:1.2rem!important;font-weight:600!important;color:var(--fg);letter-spacing:-.005em;padding:.2rem 0 .1rem!important}
h3{font-size:1rem!important;font-weight:600!important;color:var(--fg)}
.mk{background:linear-gradient(transparent 14%,var(--hl) 14%,var(--hl) 86%,transparent 86%);color:var(--forest);padding:0 .12em}
.pg-head{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap;margin-bottom:6px}
.pg-sub{color:var(--muted);font-size:.95rem;line-height:1.5;max-width:68ch;margin:8px 0 0}
.pg-foco{font-size:.8rem;color:var(--forest);border:1px solid var(--line);background:var(--surface);border-radius:99px;padding:5px 12px;white-space:nowrap}
.pg-foco b{font-weight:600}
.sec{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin:26px 0 10px}
.sec h2{margin:0!important;padding:0!important}
.sec span{font-size:.84rem;color:var(--muted)}
.muted{color:var(--muted);font-size:.86rem;line-height:1.5}
.mono{font-family:var(--mono);font-variant-numeric:tabular-nums}
.chip{display:inline-flex;align-items:center;gap:5px;font-size:.76rem;font-weight:500;padding:3px 10px;border-radius:99px;margin:0 6px 6px 0;
background:var(--sunk);color:var(--fg);white-space:nowrap;max-width:100%;overflow:hidden;text-overflow:ellipsis}
.chip i{font-style:normal;color:var(--muted);font-weight:400}
.c-ok{background:var(--ok-bg);color:var(--ok)}.c-warn{background:var(--warn-bg);color:var(--warn)}
.c-bad{background:var(--bad-bg);color:var(--bad)}.c-mut{background:var(--sunk);color:var(--muted)}
.c-top{background:var(--lime);color:var(--forest);font-weight:600}.c-line{background:transparent;border:1px solid var(--line)}

/* cartões de número */
.kpis{display:grid;grid-template-columns:1.25fr 1fr 1fr 1.25fr;gap:12px;margin:18px 0 4px}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px 18px;min-width:0}
.kpi span{display:block;font-size:.84rem;color:var(--muted)}
.kpi b{display:block;font:600 2.1rem/1.15 "Lexend";color:var(--forest);font-variant-numeric:tabular-nums;letter-spacing:-.02em;margin:4px 0 2px}
.kpi small{display:block;font-size:.78rem;line-height:1.4;color:var(--muted)}
.kpi .receipt span{display:inline;font:400 .78rem var(--mono)}.kpi .receipt b{display:inline;font:500 .84rem var(--mono);margin:0;letter-spacing:0;text-align:right}
.rk.rk3{grid-template-columns:44px minmax(0,1.3fr) minmax(0,1fr)}
.kpi.k1{background:var(--forest);border-color:var(--forest)}
.kpi.k1 span,.kpi.k1 small{color:#bcd6c8}.kpi.k1 b{color:#fff}
.kpi .split{display:flex;gap:6px;margin-top:8px;height:6px;border-radius:3px;overflow:hidden}
.kpi .split i{display:block;height:100%;border-radius:3px}

/* aprendizados */
.aprs{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.apr{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px 18px;display:flex;flex-direction:column;gap:8px}
.apr .n{font:400 2.4rem/1 "Anton";color:var(--forest)}
.x{font:600 .55em "Lexend";margin-left:1px}
.apr .n small{font:500 .8rem "Lexend";color:var(--muted);margin-left:6px}
.apr p{margin:0;font-size:.92rem;line-height:1.5}
.apr .f{font-size:.78rem;color:var(--muted);margin-top:auto}
.aviso{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--bad);border-radius:14px;padding:16px 20px}
.aviso h3{margin:0 0 4px!important;padding:0!important;font-size:1.1rem!important;color:var(--forest)}
.aviso p{margin:0;font-size:.92rem;line-height:1.55;max-width:70ch}

/* card de post (o botão do Streamlit cobre o card inteiro e fica invisível) */
[class*="st-key-pc_"],[class*="st-key-rk_"],[class*="st-key-pr_"]{position:relative;gap:0!important}
[class*="st-key-pc_"] [data-testid="stElementContainer"]:has(.stButton),
[class*="st-key-rk_"] [data-testid="stElementContainer"]:has(.stButton),
[class*="st-key-pr_"] [data-testid="stElementContainer"]:has(.stButton){position:absolute!important;inset:0;z-index:2;width:100%!important;height:100%}
[class*="st-key-pc_"] .stButton,[class*="st-key-rk_"] .stButton,[class*="st-key-pr_"] .stButton{height:100%;width:100%}
[class*="st-key-pc_"] .stButton button,[class*="st-key-rk_"] .stButton button,[class*="st-key-pr_"] .stButton button{
width:100%;height:100%;min-height:0;opacity:0;cursor:pointer;padding:0}
.pc{background:var(--surface);border:1px solid var(--line);border-radius:14px;overflow:hidden;transition:border-color .12s,transform .12s}
[class*="st-key-pc_"]:hover .pc{border-color:var(--forest);transform:translateY(-2px)}
[class*="st-key-pc_"]:has(button:focus-visible) .pc,[class*="st-key-rk_"]:has(button:focus-visible) .rk,
[class*="st-key-pr_"]:has(button:focus-visible) .pd{outline:3px solid var(--lime);outline-offset:2px;border-color:var(--forest)}
.pc-img{position:relative;aspect-ratio:4/5;background:var(--sunk) center/cover no-repeat}
.pc.v .pc-img{aspect-ratio:9/16}
.pc-ph{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;text-align:center;padding:14px;color:var(--muted)}
.pc-ph .fr{width:44px;height:56px;border:2px solid #b9cbbf;border-radius:8px;position:relative}
.pc-ph .fr::after{content:"";position:absolute;left:8px;right:8px;bottom:8px;height:2px;background:#b9cbbf;box-shadow:0 -7px 0 #b9cbbf}
.pc-ph b{font:500 .82rem "Lexend";color:var(--forest)}
.pc-ph small{font-size:.72rem;line-height:1.35}
.pc-ph a{position:relative;z-index:3;font-size:.76rem;color:var(--forest);font-weight:500}
.pc-badge{position:absolute;left:8px;bottom:8px;background:rgba(10,24,17,.78);color:#fff;font-size:.7rem;font-weight:500;padding:3px 8px;border-radius:99px}
.pc-top{position:absolute;left:8px;top:8px;background:var(--lime);color:var(--forest);font-size:.7rem;font-weight:700;padding:3px 9px;border-radius:99px}
.pc-play{position:absolute;right:8px;top:8px;width:26px;height:26px;border-radius:50%;background:rgba(10,24,17,.78)}
.pc-play::after{content:"";position:absolute;left:10px;top:7px;border-left:9px solid #fff;border-top:6px solid transparent;border-bottom:6px solid transparent}
.pc-body{padding:10px 12px 12px}
.pc-canal{display:block;font-size:.82rem;font-weight:600;color:var(--fg);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pc-tit{margin:2px 0 8px;font-size:.76rem;line-height:1.4;color:var(--muted);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.8em}
.pc-nums{display:flex;gap:12px;font-size:.72rem;color:var(--muted);border-top:1px solid var(--line);padding-top:8px}
.pc-nums span{white-space:nowrap;min-width:0}
.pc-nums b{display:block;font:500 .9rem var(--mono);color:var(--forest);font-variant-numeric:tabular-nums}
.pc.mini .pc-body{padding:7px 9px 8px}.pc.mini .pc-tit{display:none}.pc.mini .pc-nums{border:0;padding:2px 0 0}
.pc.mini .pc-canal{font-size:.76rem}.pc.mini .pc-nums{gap:8px;font-size:.66rem;overflow:hidden}.pc.mini .pc-nums b{font-size:.8rem}
.pc.mini .pc-badge i{display:none}.pc-badge i{font-style:normal}
.pc.nu .pc-body{display:none}

/* ranking */
.podio-n{font:400 3.2rem/1 "Anton";color:var(--forest);display:flex;align-items:baseline;gap:8px;margin-bottom:6px}
.podio-n small{font:500 .8rem "Lexend";color:var(--muted)}
.rk{display:grid;grid-template-columns:44px 52px minmax(0,1.5fr) minmax(0,1fr) 76px;gap:14px;align-items:center;background:var(--surface);
border:1px solid var(--line);border-radius:14px;padding:8px 16px 8px 10px;transition:border-color .12s}
[class*="st-key-rk_"]:hover .rk{border-color:var(--forest)}
.rk-pos{font:400 1.6rem/1 "Anton";color:var(--forest);text-align:center}
.rk-th{width:52px;height:65px;border-radius:8px;background:var(--sunk) center/cover no-repeat}
.rk-t{min-width:0}.rk-t b{display:block;font-size:.9rem;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rk-t span{display:block;font-size:.78rem;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rk-er{text-align:right;font-size:.7rem;color:var(--muted)}.rk-er b{display:block;font:500 .92rem var(--mono);color:var(--fg)}
.bar{display:flex;align-items:center;gap:10px}
.bar .tr{flex:1;height:8px;border-radius:4px;background:var(--sunk);overflow:hidden}
.bar .tr i{display:block;height:100%;border-radius:4px;background:var(--data)}
.bar b{font:500 .88rem var(--mono);color:var(--forest);min-width:58px;text-align:right;font-variant-numeric:tabular-nums}
.bar-l{font-size:.7rem;color:var(--muted);margin-bottom:3px}
.cr h3{margin:0!important;padding:0!important;font-size:1.02rem!important;line-height:1.3!important;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cr-pos{font:400 1.5rem/1 "Anton";color:var(--forest);margin-right:10px}
.cr-top{display:flex;align-items:baseline;min-width:0}
.cr-meta{font-size:.8rem;color:var(--muted);margin:4px 0 10px}

/* padrões */
.pd{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:12px 16px;display:grid;
grid-template-columns:minmax(0,1.1fr) minmax(0,1.4fr) 84px;gap:18px;align-items:center;transition:border-color .12s}
[class*="st-key-pr_"]:hover .pd{border-color:var(--forest)}
.pd.on{border-color:var(--forest)}
.pd-n b{display:block;font-size:.92rem;font-weight:600}
.pd-n .chip{margin:6px 6px 0 0}
.pd-b div{display:grid;grid-template-columns:62px 1fr 44px;gap:8px;align-items:center;font-size:.72rem;color:var(--muted)}
.pd-b div+div{margin-top:5px}
.pd-b i{display:block;height:10px;border-radius:5px;background:var(--data);min-width:2px}
.pd-b div+div i{background:var(--data-soft)}
.pd-b em{font:500 .8rem var(--mono);font-style:normal;color:var(--fg);text-align:right}
.pd-l{text-align:right}.pd-l b{display:block;font:400 1.5rem/1 "Anton";color:var(--forest)}
.pd-l.dn b{color:var(--bad)}.pd-l span{font-size:.7rem;color:var(--muted)}
.ads div{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr) 58px;gap:12px;align-items:center;padding:7px 0;border-bottom:1px solid var(--line);font-size:.84rem}
.ads div:last-child{border:0}
.ads span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.ads small{display:block;font-size:.72rem;color:var(--muted)}
.ads i{display:block;height:10px;border-radius:5px;background:var(--data)}
.ads .medio i{background:var(--data-soft)}.ads .baixo i{background:var(--bad)}
.ads em{font:500 .84rem var(--mono);font-style:normal;text-align:right}

/* detalhe do post */
.st-key-fone{border:9px solid #14231b;border-radius:34px;background:#0c1510;overflow:hidden;max-width:340px;margin:0 auto;gap:0!important;min-height:300px;justify-content:center}
.st-key-fone img,.st-key-fone video,.st-key-fone iframe{display:block;border-radius:0!important;width:100%}
.st-key-fone video{max-height:600px;background:#000}
.st-key-fone [data-testid="stImage"] img{max-height:600px;object-fit:contain;background:#0c1510}
.fone-ph{color:#bcd6c8;text-align:center;padding:60px 22px;font-size:.88rem;line-height:1.5}
.fone-ph b{display:block;color:#fff;font-size:1rem;margin-bottom:6px}
.mets{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px 0}
.met{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:9px 12px}
.met span{display:block;font-size:.72rem;color:var(--muted)}
.met b{display:block;font:500 1.05rem var(--mono);color:var(--forest);font-variant-numeric:tabular-nums}
.met.hl{background:var(--forest);border-color:var(--forest)}.met.hl span{color:#bcd6c8}.met.hl b{color:var(--lime)}
.hookq{border-left:4px solid var(--lime);background:var(--bg);border-radius:0 10px 10px 0;padding:10px 14px;margin:8px 0 12px}
.hookq span{display:block;font-size:.74rem;color:var(--muted);margin-bottom:2px}
.hookq p{margin:0;font-size:1.02rem;font-weight:600;line-height:1.4;color:var(--forest)}
.lst{margin:4px 0 0;padding-left:18px;font-size:.86rem;line-height:1.55}
.dt-canal{font-size:1.15rem;font-weight:600;line-height:1.3;margin:6px 0 2px}
.dt-canal a{color:var(--forest);text-decoration:underline;text-decoration-color:var(--lime);text-decoration-thickness:3px;text-underline-offset:3px}
.dt-leg{font-size:.88rem;line-height:1.55;color:var(--fg);margin:8px 0 0;white-space:pre-line;overflow-wrap:anywhere}

/* passos, linha do tempo, medidor */
.passos{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;counter-reset:p}
.passo{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px 18px;counter-increment:p}
.passo::before{content:counter(p);font:400 2rem/1 "Anton";color:var(--forest);display:block;margin-bottom:8px}
.passo b{display:block;font-size:.95rem;margin-bottom:4px}.passo p{margin:0;font-size:.84rem;line-height:1.5;color:var(--muted)}
.tl{list-style:none;margin:6px 0 0;padding:0;border-left:2px solid var(--line);margin-left:7px}
.tl li{position:relative;padding:0 0 14px 20px;font-size:.88rem;line-height:1.55}
.tl li::before{content:"";position:absolute;left:-7px;top:5px;width:12px;height:12px;border-radius:50%;background:var(--surface);border:3px solid var(--forest);box-sizing:border-box}
.tl li b{display:block;font:500 .74rem var(--mono);color:var(--forest);margin-bottom:1px}
.tl li:last-child{padding-bottom:0}
.gauge b{font:400 4.6rem/1 "Anton";color:var(--forest)}.gauge>span{font-size:.9rem;color:var(--muted);margin-left:6px}
.gauge .t{position:relative;height:18px;border-radius:9px;background:var(--sunk);margin:12px 0 40px}
.gauge .t i{position:absolute;left:0;top:0;bottom:0;border-radius:9px;background:var(--data)}
.gauge .t u{position:absolute;top:-5px;bottom:-5px;width:3px;border-radius:2px;background:var(--forest);text-decoration:none}
.gauge .t u em{position:absolute;top:32px;font:500 .7rem/1.2 "Lexend";font-style:normal;color:var(--muted);white-space:nowrap;transform:translateX(-50%)}
.gauge .t u.c{background:var(--muted)}.gauge .t u.c em{transform:translateX(-92%)}.gauge .t u.p em{transform:translateX(-8%)}
.chk{display:grid;grid-template-columns:22px minmax(0,1fr) auto;gap:10px;align-items:center;padding:8px 0;border-bottom:1px solid var(--line);font-size:.88rem}
.chk:last-child{border:0}
.chk .ic{width:20px;height:20px;border-radius:50%;display:grid;place-items:center;font-size:.72rem;font-weight:700}
.chk.sim .ic{background:var(--ok-bg);color:var(--ok)}.chk.nao .ic{background:var(--sunk);color:var(--muted)}.chk.ruim .ic{background:var(--bad-bg);color:var(--bad)}
.chk small{display:block;font-size:.74rem;color:var(--muted)}
.chk em{font:500 .8rem var(--mono);font-style:normal;color:var(--forest)}
.vs{display:grid;grid-template-columns:minmax(0,150px) 1fr 70px;gap:10px;align-items:center;font-size:.82rem;padding:5px 0}
.vs .t{position:relative;height:10px;border-radius:5px;background:var(--sunk)}
.vs .t i{position:absolute;left:0;top:0;bottom:0;border-radius:5px;background:var(--data)}
.vs .t u{position:absolute;top:-4px;bottom:-4px;width:3px;border-radius:2px;background:var(--fg)}
.vs em{font:500 .78rem var(--mono);font-style:normal;text-align:right}
.rec{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:12px 16px 12px 46px;position:relative;font-size:.9rem;line-height:1.5;margin-bottom:8px}
.rec::before{content:attr(data-n);position:absolute;left:14px;top:9px;font:400 1.4rem/1.2 "Anton";color:var(--forest)}
.vazio{background:var(--sunk);border:1px dashed #c3d2c8;border-radius:14px;padding:18px 20px;font-size:.9rem;max-width:72ch;line-height:1.5}
.vazio b{color:var(--forest)}.vazio p{margin:6px 0}.vazio ul{margin:4px 0 0 18px}.vazio code{font-size:.78rem}
.toc{position:sticky;top:4rem;border-left:2px solid var(--line);padding:2px 0 2px 14px}
.toc b{display:block;font-size:.8rem;color:var(--muted);font-weight:500;margin-bottom:6px}
.toc a{display:block;font-size:.84rem;line-height:1.35;color:var(--fg);text-decoration:none;padding:5px 0}
.toc a:hover{color:var(--forest);text-decoration:underline;text-decoration-color:var(--lime);text-decoration-thickness:3px}
.receipt{font:400 .8rem var(--mono);background:var(--bg);border:1px dashed #c3d2c8;border-radius:8px;padding:12px 14px}
.receipt div{display:flex;justify-content:space-between;gap:12px;border-bottom:1px dotted var(--line);padding:3px 0}
.receipt .warn b{color:var(--warn)}
.stamp{margin:8px 0 0;text-align:center;font:600 .78rem var(--mono);letter-spacing:.08em;text-transform:uppercase}

/* componentes do Streamlit */
[data-testid="stSidebar"]{border-right:1px solid var(--line)}
[data-testid="stSidebar"] .block-container,[data-testid="stSidebarUserContent"]{padding-top:1rem}
.marca{font:400 1.7rem/1 "Anton";text-transform:uppercase;color:var(--forest);letter-spacing:.01em;margin:0 0 2px}
.marca-s{font-size:.76rem;color:var(--muted);margin:4px 0 0;line-height:1.4}
.sb-base{font-size:.78rem;color:var(--muted);line-height:1.6;border-top:1px solid var(--line);padding-top:12px;margin-top:6px}
.sb-base b{font:500 .82rem var(--mono);color:var(--forest)}
[data-testid="stSidebar"] [data-testid="stPageLink"] a{border-radius:10px;padding:7px 10px}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover{background:#e3ece5}
[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"]{background:var(--forest)}
[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"] *{color:#fff!important}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:focus-visible{outline:3px solid var(--lime)}
.stButton>button,.stLinkButton>a,.stDownloadButton>button,[data-testid="stFormSubmitButton"]>button{border-radius:99px}
button[data-testid="stBaseButton-primary"],button[data-testid="stBaseButton-primaryFormSubmit"]{background:var(--forest);border-color:var(--forest);color:#fff}
button[data-testid="stBaseButton-primary"]:hover,button[data-testid="stBaseButton-primaryFormSubmit"]:hover{background:#00573c;border-color:#00573c}
.stButton>button:focus-visible,.stLinkButton>a:focus-visible,[data-testid="stFormSubmitButton"]>button:focus-visible{outline:3px solid var(--lime);outline-offset:1px}
[data-testid="stButtonGroup"] button[aria-checked="true"],[data-testid="stButtonGroup"] button[aria-pressed="true"]{background:var(--forest)!important;border-color:var(--forest)!important}
[data-testid="stButtonGroup"] button[aria-checked="true"] p,[data-testid="stButtonGroup"] button[aria-pressed="true"] p{color:#fff!important}
[data-testid="stButtonGroup"] button:focus-visible{outline:3px solid var(--lime)}
[data-testid="stVerticalBlockBorderWrapper"]{background:transparent}
[data-testid="stExpander"] details{background:var(--surface)}
[role="dialog"]{border-radius:18px}

@media (max-width:900px){
 .kpis,.aprs,.passos{grid-template-columns:1fr 1fr}
 .pd{grid-template-columns:1fr 70px}.pd-n{grid-column:1/-1}
}
@media (max-width:640px){
 .block-container{padding-left:1rem;padding-right:1rem;padding-top:4.2rem}
 .sec{flex-direction:column;gap:2px;align-items:flex-start}
 .rk.rk3{grid-template-columns:30px minmax(0,1fr) 62px}.rk.rk3 .bar{display:flex}.rk.rk3 .bar .tr{display:none}.rk.rk3 .bar b{min-width:0}
 .pg-foco{white-space:normal}
 h1,.pg-h1{font-size:2rem!important}
 .aprs,.passos{grid-template-columns:1fr}
 .kpi b{font-size:1.6rem}
 .rk{grid-template-columns:30px 44px minmax(0,1fr) 64px;gap:10px}.rk .bar{display:none}.rk-th{width:44px;height:55px}
 .mets{grid-template-columns:1fr 1fr}
 .ads div{grid-template-columns:minmax(0,1.3fr) minmax(0,.7fr) 52px}
 /* grades de cards: 2 por linha no celular em vez de 1 */
 [class*="st-key-grade_"] [data-testid="stHorizontalBlock"]{flex-wrap:wrap;gap:10px}
 [class*="st-key-grade_"] [data-testid="stHorizontalBlock"]>[data-testid="stColumn"]{min-width:calc(50% - 5px)!important;flex:0 0 calc(50% - 5px)!important;width:calc(50% - 5px)!important}
}
</style>
"""


def estilo():
    st.html(CSS)


# ---------------------------------------------------------------- peças
def fonte_atual():
    return FOCOS[st.session_state.get("foco") if st.session_state.get("foco") in FOCOS else "A"]


def titulo(nome, sub="", grifo=None, foco=True):
    """Título da página. `grifo` = palavra do título que ganha o marca-texto lima."""
    f = fonte_atual()
    t = E(nome).replace(E(grifo), f'<span class="mk">{E(grifo)}</span>') if grifo else E(nome)
    chip = f'<span class="pg-foco">Foco {f["id"]} · <b>{E(f["nome"])}</b></span>' if foco else ""
    st.html(f'<div class="pg-head"><div><h1 class="pg-h1">{t}</h1>'
            f'{f"<p class=pg-sub>{sub}</p>" if sub else ""}</div>{chip}</div>')


def secao(nome, lado=""):
    st.html(f'<div class="sec"><h2>{E(nome)}</h2><span>{lado}</span></div>')


def chip(txt, cls="", rot=None):
    return f'<span class="chip {cls}">{f"<i>{E(rot)}</i> " if rot else ""}{E(str(txt))}</span>'


def sem_dados(fonte, *chaves, extra=""):
    faltam = "".join(f"<li>{ARQUIVO[k]}: <code>{E(fonte[k])}</code> "
                     f"({'não foi possível ler agora' if os.path.exists(fonte[k]) else 'ainda não existe'})</li>"
                     for k in chaves)
    st.html(f'<div class="vazio"><b>Ainda sem dados deste foco</b><p>O foco “{E(fonte["nome"])}” está sendo montado. '
            f'Esta parte aparece sozinha quando o arquivo abaixo ficar pronto. {extra}</p><ul>{faltam}</ul></div>')


def vazio(titulo_, texto):
    st.html(f'<div class="vazio"><b>{E(titulo_)}</b><p>{texto}</p></div>')


def base(fonte):
    """Ranking do foco, ou None depois de mostrar o estado vazio."""
    r = ranking(fonte)
    if r is None or r.empty:
        sem_dados(fonte, "db")
        return None
    return r


def card_html(row, fonte, cls=""):
    vid, plat = row["video_id"], row["plataforma"]
    bg = _bg(vid, plat, fonte) if row.get("tem_midia") or plat == "youtube" else None
    selo = f'<span class="pc-badge">{E(row["formato_post"])}<i> · {PLAT_NOME.get(plat, plat)}</i></span>'
    top = '<span class="pc-top">Top</span>' if row.get("top") else ""
    if bg:
        play = '<span class="pc-play"></span>' if row.get("tem_video") else ""
        img = f'<div class="pc-img" style="{bg}" role="img" aria-label="Capa do post">{top}{play}{selo}</div>'
    else:
        link = f'<a href="{E(row["url"])}" target="_blank" rel="noopener">abrir no {PLAT_NOME.get(plat, plat)} ↗</a>' if row.get("url") else ""
        img = (f'<div class="pc-img pc-ph">{top}<span class="fr"></span><b>{E(row["formato_post"])}</b>'
               f'<small>sem prévia salva</small>{link}</div>')
    er = pct(row.get("er"))
    return (f'<div class="pc {cls}">{img}<div class="pc-body"><span class="pc-canal">{E(str(row.get("canal") or "—"))}</span>'
            f'<p class="pc-tit">{E(str(row.get("post") or ""))}</p>'
            f'<div class="pc-nums"><span><b>{er}</b>ER</span><span><b>{vezes(row.get("resid"))}</b>o esperado</span></div></div></div>')


def abrir_post(foco_id, vid):
    st.session_state["post_aberto"] = (foco_id, vid)


def post_card(row, fonte, chave, cls=""):
    """Card clicável: abre o detalhe do post."""
    with st.container(key=f"pc_{chave}_{row['video_id']}"):
        st.html(card_html(row, fonte, cls))
        st.button(f"Abrir post de {row.get('canal') or 'perfil'}", key=f"b_{chave}_{row['video_id']}",
                  on_click=abrir_post, args=(fonte["id"], row["video_id"]))


def grade(rows, fonte, chave, colunas=4, cls=""):
    """Grade de cards em linhas de `colunas` (2 por linha no celular)."""
    with st.container(key=f"grade_{chave}"):
        for i in range(0, len(rows), colunas):
            cols = st.columns(colunas)
            for col, row in zip(cols, rows[i:i + colunas]):
                with col:
                    post_card(row, fonte, chave, cls)


def barra(frac, txt):
    return (f'<div class="bar"><div class="tr"><i style="width:{max(2, min(100, frac * 100)):.0f}%"></i></div>'
            f'<b>{E(txt)}</b></div>')


def link_canal(row):
    cid, plat = row.get("channel_id"), row.get("plataforma")
    if not cid or cid != cid:
        return None
    return f"https://www.youtube.com/channel/{cid}" if plat == "youtube" else f"https://www.instagram.com/{cid}/"


def parecidos(R, row, fonte, n=6):
    """Posts com o mesmo tema, formato e gancho (ou, sem leitura, do mesmo segmento e criador)."""
    c = fonte["campos"]
    d = R[(R.video_id != row["video_id"]) & R.tem_midia]
    if d.empty:
        return []
    s = (d.plataforma == row["plataforma"]) * 1.0 + d.top * 0.5
    for campo, peso in [(c["tema"], 3), (c["formato"], 2), (c["gancho"], 2), ("segmento", 1), ("canal", .5)]:
        v = row.get(campo)
        if campo in d and isinstance(v, str) and v:
            s = s + (d[campo] == v) * peso
    d = d.assign(_s=s).sort_values(["_s", "resid"], ascending=False)
    d = d[d._s >= 2].drop_duplicates("canal") if (d._s >= 2).any() else d.head(0)
    return d.head(n).to_dict("records")


def leitura_html(rub, fonte):
    """A leitura automática do post em chips, sem JSON."""
    if not rub:
        return ('<p class="muted">Este post não passou pela leitura automática: só os posts do top e do grupo de '
                'comparação são lidos em detalhe.</p>')
    c = fonte["campos"]
    out = []
    gancho = rub.get(c["gancho_txt"])
    tipo_g = rub.get(c["gancho"].removeprefix("r_"))
    if gancho:
        out.append(f'<div class="hookq"><span>Gancho, nos 3 primeiros segundos'
                   f'{f" · {E(valor_nome(tipo_g))}" if tipo_g else ""}</span><p>“{E(str(gancho).strip(' \"“”' + chr(39)))}”</p></div>')
    principais = ["formato_video", "formato", "tema_principal", "tipo_hook", "tipo_gancho", "tipo_cta", "publico_alvo", "tom",
                  "pilar_impulso", "gatilho_identificacao"]
    chips = [chip(valor_nome(rub[k]), "c-line", rotulo(k)) for k in principais
             if isinstance(rub.get(k), str) and rub[k] and rub[k] != "nenhum"]
    sinais = [chip("✓ " + rotulo(k), "c-ok") for k, v in rub.items() if v is True and not k.startswith("relevante")]
    notas = [chip(f"{v}/10", "c-mut", rotulo(k)) for k, v in rub.items() if k.endswith("_0a10") and isinstance(v, (int, float))]
    out.append("<div>" + "".join(chips) + "</div>")
    if sinais:
        out.append('<div style="margin-top:4px">' + "".join(sinais) + "</div>")
    if notas:
        out.append('<div style="margin-top:4px">' + "".join(notas) + "</div>")
    el = [x for x in (rub.get("elementos_top5") or []) if isinstance(x, str)]
    if el:
        out.append('<p class="muted" style="margin:10px 0 0"><b style="color:var(--fg)">O que explica a atenção</b></p>'
                   '<ul class="lst">' + "".join(f"<li>{E(x)}</li>" for x in el[:5]) + "</ul>")
    return "".join(out)


def _previa(row, fonte):
    vid, plat = row["video_id"], row["plataforma"]
    mp4 = f"{fonte['midia']}/{vid}.mp4"
    with st.container(key="fone"):
        if plat == "youtube":
            st.iframe(f"https://www.youtube.com/embed/{vid}", height=560)
        elif os.path.exists(mp4):
            st.video(mp4)
        elif row.get("n_img", 0) > 0:
            n = int(row["n_img"])
            i = st.session_state.get(f"car_{vid}", 0) % n
            f = f"{fonte['midia']}/{vid}_{i}.jpg"
            if os.path.exists(f):
                st.image(f, width="stretch")
        else:
            st.html(f'<div class="fone-ph"><b>{E(row["formato_post"])}</b>Não guardamos a imagem deste post. '
                    f'Abra no {PLAT_NOME.get(plat, plat)} para ver.</div>')
    if plat != "youtube" and not os.path.exists(mp4) and row.get("n_img", 0) > 1:
        n = int(row["n_img"])
        i = st.session_state.get(f"car_{vid}", 0) % n
        a, b, c = st.columns([1, 1.4, 1], vertical_alignment="center")
        if a.button("", icon=":material/chevron_left:", key=f"ant_{vid}", width="stretch", help="Imagem anterior"):
            st.session_state[f"car_{vid}"] = (i - 1) % n
            st.rerun(scope="fragment")
        b.html(f'<p class="mono" style="text-align:center;margin:0;font-size:.82rem;color:var(--muted)">{i + 1} de {n}</p>')
        if c.button("", icon=":material/chevron_right:", key=f"prox_{vid}", width="stretch", help="Próxima imagem"):
            st.session_state[f"car_{vid}"] = (i + 1) % n
            st.rerun(scope="fragment")
    if row.get("url"):
        st.link_button(f"Abrir no {PLAT_NOME.get(plat, plat)}", row["url"], icon=":material/open_in_new:", width="stretch")


def _fechar():
    st.session_state.pop("post_aberto", None)


@st.dialog("Detalhe do post", width="large", on_dismiss=_fechar)
def detalhe():
    foco_id, vid = st.session_state.get("post_aberto") or (None, None)
    fonte = FOCOS.get(foco_id)
    R = ranking(fonte) if fonte else None
    d = R[R.video_id == vid] if R is not None else None
    if d is None or d.empty:
        st.info("Não encontramos este post na base deste foco.")
        return
    row = d.iloc[0].to_dict()
    plat = row["plataforma"]
    esq, dir_ = st.columns([0.8, 1.2], gap="large")
    with esq:
        _previa(row, fonte)
    with dir_:
        chips = chip(PLAT_NOME.get(plat, plat), "c-line") + chip(row["formato_post"], "c-line")
        if row.get("top") and _ok(row.get("pos_top")):
            chips += chip(f"Top · nº {int(row['pos_top'])} no {PLAT_NOME.get(plat, plat)}", "c-top")
        elif "elegivel" in row and not row.get("elegivel"):
            chips += chip("fora da base que concorre ao top", "c-mut")
        url_c = link_canal(row)
        nome = E(str(row.get("canal") or "—"))
        seg = f' · {E(str(row["segmento"]))}' if isinstance(row.get("segmento"), str) else ""
        st.html(f'<div>{chips}</div><p class="dt-canal">'
                f'{f"<a href={chr(34)}{E(url_c)}{chr(34)} target=_blank rel=noopener>{nome}</a>" if url_c else nome}</p>'
                f'<p class="muted" style="margin:0">{compacto(row.get("inscritos"))} seguidores · perfil '
                f'{PORTE_CURTO.get(row.get("porte"), row.get("porte") or "—")}{seg}'
                f'{" · publicado em " + data_br(row["publicado"]) if isinstance(row.get("publicado"), str) else ""}</p>')
        mets = [("× o esperado", vezes(row.get("resid")) if _ok(row.get("resid")) else "não concorre", "hl"), ("ER", pct(row.get("er")), ""),
                ("Curtidas", compacto(row.get("likes")), ""), ("Comentários", compacto(row.get("comentarios")), "")]
        if _ok(row.get("views")):
            mets.append(("Views", compacto(row["views"]), ""))
        if _ok(row.get("pct_intencao")):
            mets.append(("Comentários querendo comprar", pct(row["pct_intencao"], 0), ""))
        elif _ok(row.get("outlier")):
            mets.append(("× a média do perfil", f"{dec(row['outlier'])}×" if row["outlier"] < 100 else f"{compacto(row['outlier'])}×", ""))
        st.html('<div class="mets">' + "".join(f'<div class="met {c}"><span>{E(k)}</span><b>{E(v)}</b></div>' for k, v, c in mets)
                + '</div><p class="muted" style="font-size:.76rem;margin:0">ER = (curtidas + comentários) ÷ seguidores. '
                  '“× o esperado” compara com o que se previa para este perfil, formato e idade do post.</p>')
        st.html('<h3 style="margin:14px 0 2px!important;padding:0">O que a leitura automática viu</h3>'
                + leitura_html(rubricas(fonte).get(vid), fonte))
        leg = (row.get("titulo") or "").strip()
        desc = (row.get("descricao") or "").strip()
        texto = (leg + "\n\n" + desc).strip() if leg and desc and leg not in desc else (desc or leg)
        if texto:
            with st.expander("Legenda do post"):
                st.html(f'<p class="dt-leg">{E(texto)}</p>')
    sim = parecidos(R, row, fonte)
    if sim:
        secao("Posts parecidos", "mesmo tema, formato ou gancho")
        with st.container(key="grade_sim"):
            for col, r_ in zip(st.columns(6), sim):
                with col:
                    post_card(r_, fonte, "sim", "mini")


def abrir_detalhe_se_pedido():
    """Chamado pelo roteador depois da página: abre o diálogo se algum card foi clicado (ou veio ?post=ID na URL)."""
    q = st.query_params
    if q.get("post"):
        st.session_state["post_aberto"] = (fonte_atual()["id"], q["post"])
        del q["post"]
    if st.session_state.get("post_aberto"):
        detalhe()


def grafico_padroes(d, altura=None):
    """Barras top × controle (altair). `d` = linhas da tabela de padrões."""
    import altair as alt
    import pandas as pd
    d = d.assign(nome=[nome_padrao(c, v) for c, v in zip(d.campo, d.valor)])
    longo = pd.concat([d.assign(grupo="Top", pct=d.freq_top), d.assign(grupo="Controle", pct=d.freq_resto)])
    ordem = list(d.nome)
    return (alt.Chart(longo).mark_bar(cornerRadiusEnd=4, height=11).encode(
        y=alt.Y("nome:N", sort=ordem, title=None, axis=alt.Axis(labelLimit=230, labelFontSize=12, labelColor="#14231b", ticks=False, domain=False, labelPadding=8)),
        yOffset=alt.YOffset("grupo:N", sort=["Top", "Controle"]),
        x=alt.X("pct:Q", title="% dos posts que têm a característica", axis=alt.Axis(format=".0%", grid=True, gridColor="#e8eee9", domain=False, ticks=False, labelColor="#536359", titleColor="#536359", titleFontWeight="normal")),
        color=alt.Color("grupo:N", sort=["Top", "Controle"], scale=alt.Scale(domain=["Top", "Controle"], range=["#1f9e55", "#b9d3c1"]),
                        legend=alt.Legend(title=None, orient="top", labelFontSize=12, symbolType="square")),
        tooltip=[alt.Tooltip("nome:N", title="Padrão"), alt.Tooltip("grupo:N", title="Grupo"),
                 alt.Tooltip("pct:Q", title="Frequência", format=".0%"), alt.Tooltip("lift:Q", title="Vezes mais no top", format=".1f"),
                 alt.Tooltip("n_top:Q", title="Posts do top")],
    ).properties(height=altura or max(180, 40 * len(d))).configure_view(strokeWidth=0)
        .configure(font="Lexend", background="transparent"))


# ---------------------------------------------------------------- peças editoriais (página Playbook)
CSS_EMBED = """
<style>
.emb{position:relative;width:100%;background:var(--sunk);overflow:hidden}
.emb iframe{position:absolute;inset:0;width:100%;height:100%;border:0;display:block}
.emb>a{position:absolute;inset:0;display:grid;place-items:center;font-size:.84rem;color:var(--forest);font-weight:500}
.emb-ig{width:100%;max-width:400px;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#fff}
.emb-ig .emb{background:#fff}
.fone-yt{width:100%;max-width:292px;border:8px solid #14231b;border-radius:30px;background:#0c1510;overflow:hidden}
.fone-yt .emb{aspect-ratio:9/16;background:#0c1510}.fone-yt .emb>a{color:#bcd6c8}
[class*="st-key-igl_"]{border:1px solid var(--line);border-radius:14px;background:#fff;overflow:hidden;gap:0!important;max-width:400px}
[class*="st-key-igl_"] video{display:block;width:100%;max-height:520px;background:#000;border-radius:0!important}
.igl-h{display:flex;align-items:center;gap:10px;padding:10px 12px}
.igl-av{flex:none;width:32px;height:32px;border-radius:50%;background:var(--sunk);border:2px solid var(--lime);position:relative;overflow:hidden}
.igl-av::before{content:"";position:absolute;left:9px;top:5px;width:10px;height:10px;border-radius:50%;background:#b9cbbf}
.igl-av::after{content:"";position:absolute;left:4px;top:18px;width:20px;height:16px;border-radius:50%;background:#b9cbbf}
.igl-h b{display:block;font-size:.84rem;font-weight:600;line-height:1.2;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.igl-h span{display:block;font-size:.72rem;color:var(--muted)}
.igl-h div{min-width:0;flex:1}
.igl-h a,.igl-f a{font-size:.76rem;font-weight:600;color:var(--forest);white-space:nowrap}
.igl-m{position:relative;background:var(--sunk)}
.igl-m img{display:block;width:100%;max-height:520px;object-fit:cover}
.igl-m span{position:absolute;right:10px;top:10px;background:rgba(10,24,17,.78);color:#fff;font:500 .7rem var(--mono);padding:3px 8px;border-radius:99px}
.igl-f{padding:10px 12px 12px;font-size:.8rem;line-height:1.45}
.igl-f .n{font:500 .8rem var(--mono);color:var(--forest);margin-bottom:4px}
.igl-f p{margin:0 0 6px;color:var(--fg);display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;overflow-wrap:anywhere}
</style>
"""
# O st.html remove <iframe>. Vai um marcador (.emb[data-src]) e este script cria o iframe com loading="lazy".
# O embed do Instagram avisa a própria altura por postMessage (MEASURE): usamos para o quadro não cortar nem sobrar.
EMBED_JS = """<script>(function(){
document.querySelectorAll('.emb[data-src]').forEach(function(d){var f=document.createElement('iframe');
f.loading='lazy';f.referrerPolicy='strict-origin-when-cross-origin';f.title=d.dataset.title||'';
f.allow='autoplay; encrypted-media; picture-in-picture; fullscreen';f.setAttribute('allowfullscreen','');
f.src=d.dataset.src;d.removeAttribute('data-src');d.replaceChildren(f)});
if(!window.__embMede){window.__embMede=1;window.addEventListener('message',function(e){
if(!/^https:\\/\\/www\\.instagram\\.com$/.test(e.origin))return;var m;try{m=typeof e.data==='string'?JSON.parse(e.data):e.data}catch(x){return}
var h=m&&m.type==='MEASURE'&&m.details&&m.details.height;if(!h)return;
document.querySelectorAll('.emb-ig iframe').forEach(function(f){if(f.contentWindow===e.source){
var d=f.parentNode;d.style.paddingBottom='0';d.style.height=Math.round(h)+'px'}})})}
})();</script>"""
_ID_OK = re.compile(r"^[A-Za-z0-9_-]{5,40}$")


def estilo_embeds():
    st.html(CSS_EMBED)


def md_inline(s):
    """Markdown de uma linha -> HTML seguro: escapa tudo e só então reabre **negrito**, `código` e [texto](link)."""
    s = E(str(s))
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)


def embed_html(src, titulo="", link=None, estilo=""):
    """Marcador de um iframe preguiçoso. Sem JavaScript, sobra o link para abrir o post."""
    fb = f'<a href="{E(link)}" target="_blank" rel="noopener">abrir o post ↗</a>' if link else ""
    return f'<div class="emb" style="{estilo}" data-src="{E(src)}" data-title="{E(titulo)}">{fb}</div>'


def embed_instagram(video_id, altura=None, proporcao=1.25):
    """Embed oficial e público do Instagram (o video_id do banco é o shortcode). `altura` em px; sem ela, o quadro
    acompanha a largura (mídia na `proporcao` altura/largura + cabeçalho e rodapé do embed)."""
    if not _ID_OK.match(str(video_id)):
        return
    est = f"height:{int(altura)}px" if altura else f"padding-bottom:calc({proporcao * 100:.0f}% + 230px)"
    st.html('<div class="emb-ig">' + embed_html(f"https://www.instagram.com/p/{video_id}/embed", "Post no Instagram",
                                                f"https://www.instagram.com/p/{video_id}/", est) + "</div>" + EMBED_JS,
            unsafe_allow_javascript=True)


def embed_youtube(video_id):
    """Player do YouTube na vertical (Short), em moldura de celular."""
    if not _ID_OK.match(str(video_id)):
        return
    st.html('<div class="fone-yt">' + embed_html(f"https://www.youtube.com/embed/{video_id}", "Vídeo no YouTube",
                                                 f"https://www.youtube.com/shorts/{video_id}") + "</div>" + EMBED_JS,
            unsafe_allow_javascript=True)


def post_instagram_local(row, fonte, chave):
    """Mesma área do embed, sem depender do Instagram: moldura de post com a mídia salva na coleta e os números do banco."""
    vid = row["video_id"]
    arroba = row.get("channel_id") if isinstance(row.get("channel_id"), str) else None
    url = row.get("url") if isinstance(row.get("url"), str) else f"https://www.instagram.com/p/{vid}/"
    ver = f'<a href="{E(url)}" target="_blank" rel="noopener">ver no Instagram ↗</a>'
    cab = (f'<div class="igl-h"><span class="igl-av"></span><div><b>{E("@" + arroba if arroba else str(row.get("canal") or "perfil"))}</b>'
           f'<span>{E(str(row.get("formato_post") or "Post"))} · prévia salva na coleta</span></div></div>')
    leg = (row.get("descricao") or row.get("titulo") or "").strip()
    nums = " · ".join(f"{compacto(row[c])} {r}" for c, r in [("likes", "curtidas"), ("comentarios", "comentários"), ("views", "views")]
                      if _ok(row.get(c)))
    pe = f'<div class="igl-f"><div class="n">{E(nums)}</div>{f"<p>{E(leg[:220])}</p>" if leg else ""}{ver}</div>'
    mp4 = f"{fonte['midia']}/{vid}.mp4"
    with st.container(key=f"igl_{chave}"):
        if os.path.exists(mp4):
            st.html(cab)
            st.video(mp4)
            st.html(pe)
        else:
            u = thumb_url(vid, "instagram", fonte)
            n = int(row.get("n_img") or 0)
            img = (f'<div class="igl-m"><img src="{E(u)}" alt="Imagem do post" loading="lazy">{f"<span>1 de {n}</span>" if n > 1 else ""}</div>'
                   if u else '<div class="igl-m muted" style="padding:60px 16px;text-align:center">Sem imagem salva deste post.</div>')
            st.html(cab + img + pe)
