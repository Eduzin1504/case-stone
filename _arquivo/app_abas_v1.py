"""Pauta Impulso: interface do agente (Streamlit). Chama a mesma run() do agent.py e do servidor MCP.
Dois focos de análise (FOCOS): A = Impulso → empreendedor (stone.db), B = Negócio → cliente (foco_b.db).

  .venv/bin/streamlit run app.py
"""
import html
import re
import json
import os
import sqlite3

import streamlit as st

import pipeline as P

st.set_page_config(page_title="Pauta Impulso", page_icon="🟩", layout="wide")

EXEMPLOS = {
    "gerar_criativo": "Reels de fim de ano para salão de beleza sobre organizar o caixa",
    "analisar": "O que diferencia os carrosséis de alto engajamento no Instagram?",
    "recomendar": "Quais 3 pautas o Impulso deveria postar em dezembro?",
}
MODOS = {"gerar_criativo": "Gerar criativo", "analisar": "Analisar", "recomendar": "Recomendar"}
SELO = {"confirmado": "ok", "contradito": "bad", "só mercado": "warn", "inconclusivo": "mut"}

# Tokens do kit visual (ux.html): neutros esverdeados ~88%, floresta como tinta, lima só como grifo e foco.
st.markdown("""
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Anton&family=Lexend:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
:root{--forest:#00442f;--lime:#c5ff1f;--hl:#d9ff66;--bg:#f7faf7;--surface:#fff;--sunk:#eef3ef;--fg:#14231b;--muted:#536359;
--line:#dfe7e1;--data:#1f9e55;--data-soft:#d5e7da;--ok:#0b6b3d;--ok-bg:#e6f3ea;--warn:#8a5a00;--warn-bg:#fbf2df;--bad:#b02d63;--bad-bg:#fbe9f0}
html,body,[class*="css"],.stMarkdown,.stTextInput,.stTextArea,button,p,li,label{font-family:"Lexend",system-ui,sans-serif}
h1,h2{font-family:"Anton","Arial Narrow",sans-serif!important;font-weight:400!important;text-transform:uppercase;color:var(--forest);letter-spacing:.005em}
h1{font-size:2.2rem!important} h2{font-size:1.35rem!important}
.block-container{padding-top:2rem;max-width:1200px}
.mk{background:linear-gradient(transparent 12%,var(--hl) 12%,var(--hl) 88%,transparent 88%);color:var(--forest);padding:0 .12em}
.meta,.stMarkdown p.meta{font:400 .78rem/1.5 "JetBrains Mono",monospace!important;color:var(--muted)}
.stMarkdown p.k{font-size:.78rem!important}
.k{font:500 .78rem "Lexend";color:var(--muted);margin-bottom:4px}
.hook{font:600 1.15rem/1.4 "Lexend";color:var(--forest);margin:2px 0 8px}
.pill{display:inline-block;font:500 .74rem "Lexend";padding:2px 10px;border-radius:99px;margin:0 6px 6px 0;white-space:nowrap}
.p-ok{background:var(--ok-bg);color:var(--ok)}.p-warn{background:var(--warn-bg);color:var(--warn)}
.p-bad{background:var(--bad-bg);color:var(--bad)}.p-mut{background:var(--sunk);color:var(--muted)}
.find{padding:8px 0;border-bottom:1px solid var(--line);font-size:.88rem}
.find .row{display:flex;justify-content:space-between;gap:10px;align-items:baseline;flex-wrap:wrap}
.find .num{font:400 .76rem "JetBrains Mono",monospace;color:var(--muted)}
.bar{height:6px;border-radius:3px;margin-top:3px}
.receipt{font:400 .8rem "JetBrains Mono",monospace;background:var(--bg);border:1px dashed var(--line);border-radius:4px;padding:12px 14px}
.receipt div{display:flex;justify-content:space-between;gap:12px;border-bottom:1px dotted var(--line);padding:3px 0}
.receipt div b{font-weight:500;text-align:right}
.receipt .warn b{color:var(--warn)}
.stamp{margin-top:6px;text-align:center;font:600 .78rem "JetBrains Mono";letter-spacing:.08em;text-transform:uppercase}
.ref{font-size:.8rem;line-height:1.35}
.ref b{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ref span{color:var(--muted)}
[data-testid="stImage"] img{max-height:240px;object-fit:cover;border-radius:10px}
.thumb-ph{aspect-ratio:4/5;border-radius:10px;background:#e6f0e8;color:var(--forest);display:flex;align-items:flex-end;padding:8px;font:600 .78rem "Lexend"}
.nota,.stMarkdown p.nota{font-size:.9rem;line-height:1.55;color:var(--fg);max-width:78ch;margin:0 0 10px}
.foco,.stMarkdown p.foco{font-size:.84rem;color:var(--muted);margin:0 0 2px}
[data-testid="stButtonGroup"] button[aria-checked="true"]{background:var(--forest)!important;border-color:var(--forest)!important}
[data-testid="stButtonGroup"] button[aria-checked="true"] p{color:#fff!important}
[data-testid="stButtonGroup"] button:focus-visible{outline:3px solid var(--lime)}.foco.on{color:var(--fg)}.foco.on b{color:var(--forest)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:14px 0 6px}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:10px 14px}
.stat span{display:block;font:500 .74rem "Lexend";color:var(--muted)}
.stat b{display:block;font:600 1.35rem/1.3 "Lexend";color:var(--forest)}
.stat small{display:block;font-size:.72rem;line-height:1.35;color:var(--muted)}
.vazio{background:var(--sunk);border:1px dashed var(--line);border-radius:12px;padding:16px 18px;font-size:.88rem;max-width:72ch}
.vazio b{color:var(--forest)}.vazio p{margin:6px 0}.vazio ul{margin:4px 0 0 18px}.vazio code{font-size:.78rem}
.stButton>button[kind="primary"]{background:var(--forest);border-color:var(--forest);border-radius:99px}
.stButton>button:focus-visible{outline:3px solid var(--lime)}
</style>""", unsafe_allow_html=True)


@st.cache_data
def salvas():
    """Execuções já feitas (data/execucoes.jsonl), para a demo funcionar sem rede."""
    f = f"{P.DATA}/execucoes.jsonl"
    if not os.path.exists(f):
        return []
    out = [json.loads(l) for l in open(f, encoding="utf-8") if l.strip()]
    vistos, uniq = set(), []
    for d in reversed(out):  # a mais recente de cada pergunta
        chave = (d["entrada"]["mode"], d["entrada"]["query"])
        if chave not in vistos and (d["saida"]["creatives"] or d["entrada"]["mode"] != "gerar_criativo"):
            vistos.add(chave)
            uniq.append(d)
    return uniq


def thumb(ref):
    local = f"{P.DATA}/midia/{ref['video_id']}_0.jpg"
    if os.path.exists(local):
        return local
    if ref["plataforma"] == "youtube":
        return f"https://i.ytimg.com/vi/{ref['video_id']}/hqdefault.jpg"
    return None


def roteiro_md(t):
    """Quebra 'Slide 1: … Slide 2: …' e marcas de tempo (0-3s) em linhas, para ler como roteiro."""
    t = re.sub(r"\s*(Slide \d+|Cena \d+|\(?\d{1,2}\s?[–-]\s?\d{1,2}\s?s\)?)", r"\n\n**\1**", t.strip())
    return t.strip()


def curto(formato):
    return re.split(r"[(,:]", formato)[0].strip()


def pct(x):
    return f"{x * 100:.0f}%"


AVALIACAO = f"{P.DATA}/avaliacao_regua.md"
LEGENDA_BARRAS = ('<p class="meta"><span style="color:var(--data)">■</span> top 10% · '
                  '<span style="color:#9fbfa9">■</span> controle (fora do top)</p>')


def achados_html(findings, n=8):
    linhas = []
    for a in findings[:n]:
        selo = a.get("selo") if isinstance(a.get("selo"), str) else ""  # Foco B não tem selo de Ads
        pill = f'<span class="pill p-{SELO.get(selo, "mut")}">{html.escape(selo)}</span>' if selo else ""
        if a.get("n_top", 5) < 5:
            pill += '<span class="pill p-warn" title="menos de 5 posts do top">frágil</span>'
        lift = f" · {a['lift']:.1f}× mais" if a.get("lift") and a["lift"] == a["lift"] else ""
        w_t, w_c = min(100, a["freq_top"] * 100), min(100, a["freq_resto"] * 100)
        linhas.append(
            f'<div class="find"><div class="row"><b>{html.escape(a["campo"].replace("_", " "))}: '
            f'{html.escape({"True": "sim", "False": "não"}.get(str(a["valor"]), str(a["valor"])).replace("_", " "))}</b><span>{pill}</span></div>'
            f'<div class="num">{pct(a["freq_top"])} no top vs {pct(a["freq_resto"])} no controle{lift} · {a.get("n_top", "?")} posts do top</div>'
            f'<div class="bar" style="width:{w_t:.0f}%;background:var(--data)"></div>'
            f'<div class="bar" style="width:{w_c:.0f}%;background:var(--data-soft)"></div></div>')
    return "".join(linhas)


def comprovante(c, refs_ids, tentativas, pendencias):
    validas = sum(i in refs_ids for i in c["inspirado_em"])
    linhas = [
        ("Referências reais na base", f"{validas} de {len(c['inspirado_em'])}", validas < len(c["inspirado_em"])),
        ("Tentativas do agente", str(tentativas or 1), False),
    ]
    ok = not any(w for *_, w in linhas) and not pendencias
    corpo = "".join(f'<div class="{"warn" if w else ""}"><span>{k}</span><b>{html.escape(v)}</b></div>' for k, v, w in linhas)
    carimbo = ('<p class="stamp" style="color:var(--ok)">Aprovado</p>' if ok else
               '<p class="stamp" style="color:var(--warn)">Revisar antes de postar</p>')
    extra = f'<p class="meta" style="margin-top:6px">Pendência do juiz: {html.escape(pendencias[:220])}</p>' if pendencias else ""
    return f'<div class="receipt">{corpo}{carimbo}{extra}</div>'


def refs_grid(refs, ids=None):
    alvo = [r for r in refs if ids is None or r["video_id"] in ids] or refs
    cols = st.columns(4)  # fixo: miniaturas do mesmo tamanho com 2 ou 8 referências
    for col, r in zip(cols * 3, alvo[:8]):
        with col:
            t = thumb(r)
            if t:
                st.image(t, width="stretch")
            else:
                st.markdown(f'<div class="thumb-ph">{html.escape(r["categorias"].get("tipo_post", r["plataforma"]))}</div>',
                            unsafe_allow_html=True)
            outl = f" · {r['outlier']:.1f}× a média do perfil" if r.get("outlier") else ""
            st.markdown(f'<div class="ref"><b>{html.escape(r["canal"])}</b><span>ER {r["er"] * 100:.1f}%{outl}</span><br>'
                        f'<a href="{html.escape(r["url"])}" target="_blank">abrir post ↗</a></div>', unsafe_allow_html=True)


# ---------- dados do mapeamento (só leitura, sem custo de API) ----------
SEG_NOME = {"gestao_financas": "gestão e finanças", "vendas_marketing": "vendas e marketing", "pagamentos_maquininha":
            "pagamentos", "alimentacao": "alimentação", "beleza": "beleza", "varejo_moda": "varejo e moda",
            "servicos": "serviços", "geral": "geral"}
TIPO_NOME = {"clips": "Reels", "carousel_container": "Carrossel", "feed": "Imagem"}
PORTE_NOME = {"micro": "micro (até 10 mil)", "medio": "médio (10–100 mil)", "grande": "grande (100 mil+)"}

# Os dois focos de análise. Cada aba recebe a fonte (dict) em vez de ler caminhos fixos.
# FOCO_B_DIR / FOCO_B_PLAYBOOK existem para testar a interface sem os arquivos do Foco B.
_B = os.getenv("FOCO_B_DIR", P.DATA)
FOCOS = {
    "A": dict(id="A", nome="Impulso → empreendedor",
              desc="conteúdo que engaja donos de pequeno negócio (o público do Impulso).",
              db=P.DB, padroes=f"{P.DATA}/padroes_selados.csv", perfis=f"{P.DATA}/perfis_destaque.csv",
              playbook="PLAYBOOK.md", rubrica=["tema_principal", "tipo_hook", "pilar_impulso", "publico_alvo"],
              elegivel="perfis validados à mão, com 5 posts ou mais, e posts com pelo menos 7 dias que falam com dono de "
                       "pequeno negócio"),
    "B": dict(id="B", nome="Negócio → cliente",
              desc="como o pequeno negócio engaja o cliente final dele.",
              db=f"{_B}/foco_b.db", padroes=f"{_B}/b_achados.csv", perfis=f"{_B}/b_perfis_destaque.csv",
              playbook=os.getenv("FOCO_B_PLAYBOOK", "PLAYBOOK_B.md"), rubrica=None,  # None = todos os campos curtos
              elegivel="posts e perfis que passaram nos filtros deste foco"),
}
ARQUIVO = {"db": "banco com o ranking", "padroes": "tabela de padrões", "perfis": "lista de perfis em destaque",
           "playbook": "playbook"}
ROTULO = {"tema_principal": "Tema (VLM)", "tipo_hook": "Gancho (VLM)", "pilar_impulso": "Pilar (VLM)",
          "publico_alvo": "Público-alvo (VLM)", "formato": "Formato do conteúdo (VLM)", "formato_video": "Formato do vídeo (VLM)",
          "tipo_cta": "Chamada para ação (VLM)", "mostra_produto": "Mostra produto", "mostra_preco": "Mostra preço",
          "tem_cta": "Tem chamada para ação", "tem_rosto": "Tem rosto", "tom": "Tom"}
ORDENS = {"resid": "acima do esperado (modelo)", "er": "engajamento (ER)", "outlier": "acima da média do perfil",
          "conversa": "conversa (coment. ÷ curtidas)", "pct_intencao": "intenção de compra nos comentários",
          "comentarios": "comentários", "views": "views"}


def rotulo(campo):
    return ROTULO.get(campo) or campo.removesuffix("_0a10").replace("_", " ").capitalize()


def regua(fonte):
    """A régua nova em 4 frases, linguagem simples."""
    return [
        "A nota que aparece em cada post continua sendo o engajamento (ER): curtidas + comentários, divididos pelos "
        "seguidores do perfil.",
        "Escolher o top só pelo maior ER premia perfil pequeno e criador que já engaja muito. Por isso um modelo estatístico "
        "calcula quanto cada post deveria engajar, olhando o tamanho do perfil, o formato, a idade do post e o histórico "
        "do próprio criador.",
        "O top 10% são os posts que mais passaram desse esperado (a coluna “Acima do esperado”), dentro de cada plataforma "
        "e faixa de tamanho de perfil.",
        f"Só concorre a base elegível ({fonte['elegivel']}) e cada criador entra com no máximo 3 posts, para ninguém virar "
        "sozinho “o padrão do mercado”.",
    ]


def versao(f):
    """Entra na chave do cache: quando outro processo regrava o arquivo, a interface relê."""
    return os.path.getmtime(f) if os.path.exists(f) else 0


def conectar(db):
    if not os.path.exists(db):
        raise FileNotFoundError(db)
    return sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=3)  # só leitura: nunca cria banco vazio


def tentar(fn, *a):
    """Leitura resiliente: o erro não é guardado no cache e não aparece na tela; quem chama mostra o estado vazio."""
    try:
        return fn(*a)
    except Exception:
        return None


def tem(d, col):
    return col in d and d[col].notna().any()


def sem_dados(fonte, *chaves, extra=""):
    faltam = "".join(f"<li>{ARQUIVO[k]}: <code>{html.escape(fonte[k])}</code> "
                     f"({'não foi possível ler agora' if os.path.exists(fonte[k]) else 'ainda não existe'})</li>"
                     for k in chaves)
    st.markdown(f'<div class="vazio"><b>Ainda sem dados deste foco</b><p>O foco “{fonte["nome"]}” está sendo montado. '
                f'Esta parte aparece sozinha quando o arquivo abaixo ficar pronto. {extra}</p><ul>{faltam}</ul></div>',
                unsafe_allow_html=True)


def capa_local(video_id):
    for pasta in ("static/midia", f"{P.DATA}/midia"):
        if os.path.exists(f"{pasta}/{video_id}_0.jpg"):
            return f"{pasta}/{video_id}_0.jpg"


def capa_url(video_id, plataforma):
    """URL para a tabela: static/midia = hard links das capas de data/midia (server.enableStaticServing)."""
    alvo, origem = f"static/midia/{video_id}_0.jpg", f"{P.DATA}/midia/{video_id}_0.jpg"
    if not os.path.exists(alvo) and os.path.exists(origem):
        try:  # capa nova (ex.: Foco B) ainda sem link em static/
            os.makedirs("static/midia", exist_ok=True)
            os.link(origem, alvo)
        except OSError:
            pass
    if os.path.exists(alvo):
        return f"/app/static/midia/{video_id}_0.jpg"
    return f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg" if plataforma == "youtube" else None


@st.cache_data(ttl=600, show_spinner=False)
def _base_info(db, v):
    c = conectar(db)
    plat = dict(c.execute("select plataforma, count(*) from videos group by plataforma").fetchall())
    perfis = c.execute("select count(*) from canais").fetchone()[0]
    quando = tentar(lambda: (c.execute("select max(coletado_em) from videos").fetchone()[0] or "")[:10]) or ""
    return plat, perfis, quando


@st.cache_data(ttl=600, show_spinner=False)
def _ranking(db, v):
    """Ranking + campos curtos da rubrica (prefixo r_). Colunas que a fonte não tem simplesmente não aparecem."""
    import pandas as pd
    c = conectar(db)
    r = pd.read_sql("select * from ranking", c)
    cat = tentar(pd.read_sql, "select video_id, rubrica from categorias", c)
    if cat is not None and len(cat):
        rub = pd.DataFrame([tentar(json.loads, x) or {} for x in cat.rubrica], index=cat.index)
        curtos = [k for k in rub if not rub[k].map(lambda x: isinstance(x, (list, dict)) or (isinstance(x, str) and len(x) > 60)).any()]
        rub = rub[curtos].add_prefix("r_").assign(video_id=cat.video_id).drop_duplicates("video_id")
        rub = rub.apply(lambda col: col.map(lambda x: {True: "sim", False: "não"}.get(x, x) if isinstance(x, bool) else x))
        r = r.merge(rub, on="video_id", how="left")
    r["capa"] = [capa_url(v_, p) for v_, p in zip(r.video_id, r.plataforma)]
    tipo = r.tipo if "tipo" in r else pd.Series(None, index=r.index, dtype=object)
    r["formato_post"] = tipo.map(TIPO_NOME).fillna("Short" if (r.plataforma == "youtube").all() else "Post")
    r.loc[r.plataforma == "youtube", "formato_post"] = "Short"
    for col in ["titulo", "descricao", "canal", "url", "segmento", "porte"]:
        if col not in r:
            r[col] = None
    r["post"] = r.titulo.fillna("").where(r.titulo.fillna("") != "", r.descricao.fillna("")).str.slice(0, 140)
    r["segmento"] = r.segmento.map(SEG_NOME).fillna(r.segmento)
    r["porte_nome"] = r.porte.map(PORTE_NOME).fillna(r.porte)
    r["top"] = r.top.fillna(0).astype(bool)
    for col in ["top_er_puro", "elegivel"]:
        if col in r:
            r[col] = r[col].fillna(0).astype(bool)
    if "publicado" in r:
        r["publicado"] = r.publicado.astype(str).str[:10].where(r.publicado.notna())
    if tem(r, "pct_intencao") and r.pct_intencao.max() <= 1:
        r["pct_intencao"] = r.pct_intencao * 100  # ponytail: aceita fração (0–1) ou percentual (0–100)
    return r


@st.cache_data(ttl=600, show_spinner=False)
def _csv(f, v, **kw):
    import pandas as pd
    return pd.read_csv(f, **kw)


@st.cache_data(ttl=600, show_spinner=False)
def _canais(db, v):
    import pandas as pd
    return pd.read_sql("select * from canais", conectar(db))


def ranking(fonte):
    return tentar(_ranking, fonte["db"], versao(fonte["db"]))


def ler_csv(f, **kw):
    """DataFrame ou None (arquivo ausente, vazio ou ilegível)."""
    d = tentar(lambda: _csv(f, versao(f), **kw)) if os.path.exists(f) else None
    return d if d is not None and len(d) else None


def secao_md(arquivo, inicio, fim=None):
    t = tentar(lambda: open(arquivo, encoding="utf-8").read()) or ""
    a = t.find(inicio)
    if a < 0:
        return ""
    b = t.find(fim, a + len(inicio)) if fim else -1
    return t[a:b if b > 0 else None]


def plataformas(d):
    return sorted(d.plataforma.dropna().unique(), key=lambda x: (x != "instagram", x == "todas", x))  # Instagram primeiro


def filtro_porte(col, d, key):
    opc = [p for p in PORTE_NOME if p in set(d.porte)] + sorted(set(d.porte.dropna()) - set(PORTE_NOME))
    return col.selectbox("Tamanho do perfil", ["todos"] + opc, format_func=lambda x: PORTE_NOME.get(x, x), key=key)


def aba_ranking(fonte):
    r, k = ranking(fonte), fonte["id"]
    st.markdown("<h2>Ranking de engajamento</h2>", unsafe_allow_html=True)
    if r is None or r.empty:
        return sem_dados(fonte, "db")
    st.markdown('<p class="nota"><b>Como ler:</b> a nota de cada post é o <b>ER</b> = (curtidas + comentários) ÷ seguidores. '
                'Mas o <span class="mk">top 10%</span> não é “quem tem o maior ER”: é quem mais <b>passou do esperado</b>. '
                'Um modelo estatístico estima quanto o post deveria engajar pelo tamanho do perfil, formato, idade do post e '
                'histórico do criador; entram no top os que mais superam essa conta, só na base elegível e com no máximo '
                '3 posts por criador.</p>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    plat = c1.selectbox("Plataforma", plataformas(r), format_func=str.capitalize, key=f"rk_plat_{k}")
    d = r[r.plataforma == plat]

    # régua nova x régua antiga, na plataforma escolhida
    n_top = int(d.top.sum())
    stats = [("Posts no ranking", len(d), "")]
    if "elegivel" in d:
        stats.append(("Base elegível", int(d.elegivel.sum()), "concorrem ao top"))
    stats.append(("Top atual", n_top, "acima do esperado (modelo)"))
    if "top_er_puro" in d:
        stats.append(("Top pelo ER puro", int(d.top_er_puro.sum()), "régua antiga: maior ER"))
        stats.append(("Coincidem", f"{int((d.top & d.top_er_puro).sum())} de {n_top}", "posts do top atual que também "
                      "estariam no top pelo ER puro"))
    st.markdown('<div class="stats">' + "".join(
        f'<div class="stat"><span>{t}</span><b>{f"{v:,}".replace(",", ".") if isinstance(v, int) else v}</b><small>{s}</small></div>'
        for t, v, s in stats) + "</div>", unsafe_allow_html=True)

    porte = filtro_porte(c2, d, f"rk_porte_{k}")
    seg = c3.selectbox("Segmento", ["todos"] + sorted(d.segmento.dropna().unique()), key=f"rk_seg_{k}")
    fmt = c4.selectbox("Formato", ["todos"] + sorted(d.formato_post.unique()), key=f"rk_fmt_{k}")
    ordem = c5.selectbox("Ordenar por", [o for o in ORDENS if tem(d, o)], key=f"rk_ord_{k}", format_func=ORDENS.get)
    so_top = st.toggle("Só posts do top 10%", value=True, key=f"rk_top_{k}")
    if porte != "todos":
        d = d[d.porte == porte]
    if seg != "todos":
        d = d[d.segmento == seg]
    if fmt != "todos":
        d = d[d.formato_post == fmt]
    if so_top:
        d = d[d.top]
    d = d.sort_values(ordem, ascending=False)
    st.markdown(f'<p class="meta">{len(d):,} posts no recorte</p>'.replace(",", "."), unsafe_allow_html=True)
    if d.empty:
        st.info("Nenhum post neste recorte. Solte um dos filtros.")
        return
    rub = [c for c in (d.columns if fonte["rubrica"] is None else ["r_" + x for x in fonte["rubrica"]])
           if c.startswith("r_") and tem(d, c)]

    def num(x):
        return f"{int(x):,}".replace(",", ".") if x == x and x is not None else "0"

    st.markdown("<h2>Em destaque</h2>", unsafe_allow_html=True)
    cols = st.columns(4)
    for col, row in zip(cols * 2, d.head(8).to_dict("records")):
        with col:
            local = capa_local(row["video_id"])
            if local or row["capa"]:
                st.image(local or row["capa"], width="stretch")
            else:
                st.markdown(f'<div class="thumb-ph">{html.escape(row["formato_post"])}</div>', unsafe_allow_html=True)
            extras = []
            if row.get("outlier") == row.get("outlier") and row.get("outlier") is not None:
                extras.append(f"{row['outlier']:.1f}× a média")
            if row.get("pct_intencao") == row.get("pct_intencao") and row.get("pct_intencao") is not None:
                extras.append(f"{row['pct_intencao']:.0f}% com intenção de compra")
            extras += [f"{num(row.get('likes'))} curtidas", f"{num(row.get('comentarios'))} coment."]
            tags = " · ".join(html.escape(str(row[c]).replace("_", " ")) for c in [c for c in rub if row[c] not in ("sim", "não")][:2] if isinstance(row[c], str))
            link = f'<a href="{html.escape(row["url"])}" target="_blank">abrir post ↗</a>' if row.get("url") else ""
            st.markdown(f'<div class="ref"><b>{html.escape(row["canal"] or "")}</b><span>ER {row["er"] * 100:.1f}% · '
                        f'{" · ".join(extras)}</span><br>{f"<span>{tags}</span><br>" if tags else ""}{link}</div>',
                        unsafe_allow_html=True)

    st.markdown("<h2>Tabela completa</h2>", unsafe_allow_html=True)
    N = st.column_config.NumberColumn
    t = d.assign(er_pct=d.er * 100)
    if "conversa" in t:
        t["conversa_pct"] = t.conversa * 100
    cfg = {
        "capa": st.column_config.ImageColumn("Capa", width="small"),
        "post": st.column_config.TextColumn("Post", width="large"),
        "canal": "Perfil", "porte_nome": "Tamanho", "segmento": "Segmento", "formato_post": "Formato",
        "resid": N("Acima do esperado", format="%+.2f",
                   help="Quanto o post passou do que o modelo previa. 0 = o esperado; +1 ≈ 2,7 vezes o esperado."),
        "er_pct": N("ER", format="%.2f%%", help="(curtidas + comentários) ÷ seguidores"),
        "outlier": N("× média do perfil", format="%.1f×"),
        "conversa_pct": N("Conversa", format="%.0f%%", help="Comentários ÷ curtidas"),
        "pct_intencao": N("Intenção de compra nos comentários", format="%.0f%%"),
        "likes": N("Curtidas", format="localized"), "comentarios": N("Comentários", format="localized"),
        "views": N("Views", format="localized"),
        **{c: rotulo(c[2:]) for c in rub},
        "publicado": st.column_config.TextColumn("Publicado"),
        "url": st.column_config.LinkColumn("Link", display_text="abrir"),
    }
    mostrar = [c for c in cfg if tem(t, c)]
    st.dataframe(t[mostrar], hide_index=True, height=min(520, 38 + 35 * len(t)), width="stretch",
                 column_config={c: cfg[c] for c in mostrar})
    if rub:
        st.caption("As colunas marcadas com (VLM) e as de sim/não vêm da leitura automática do post (rubrica); "
                   "aparecem só nos posts categorizados (top e controle).")


def aba_perfis(fonte):
    k = fonte["id"]
    st.markdown("<h2>Perfis em destaque</h2>", unsafe_allow_html=True)
    d = ler_csv(fonte["perfis"])
    if d is None:
        sem_dados(fonte, "perfis")
    else:
        st.markdown('<p class="meta">Ordenados pelo quanto o perfil engaja acima do esperado para o seu tamanho, já descontando '
                    'a sorte de quem tem poucos posts. Só entram perfis com ao menos 1 post no top.</p>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        if "plataforma" in d:
            plat = c1.selectbox("Plataforma", ["todas"] + [p for p in plataformas(d) if p != "todas"], key=f"pf_plat_{k}")
            if plat != "todas":
                d = d[d.plataforma == plat]
        if "porte" in d:
            porte = filtro_porte(c2, d, f"pf_porte_{k}")
            if porte != "todos":
                d = d[d.porte == porte]
            d = d.assign(porte=d.porte.map(PORTE_NOME).fillna(d.porte))
        ordem = next((c for c in ["efeito_criador", "n_top"] if tem(d, c)), None)
        if ordem:
            d = d.sort_values(ordem, ascending=False)
        N = st.column_config.NumberColumn
        cfg = {"canal": st.column_config.TextColumn("Perfil", width="medium"), "plataforma": "Plataforma", "porte": "Tamanho",
               "segmento": "Segmento", "inscritos": N("Seguidores", format="localized"),
               "efeito_criador": N("Acima do esperado", format="%+.2f",
                                   help="Quanto o perfil engaja acima do esperado para o tamanho (0 = o esperado)"),
               "n_top": N("Posts no top", format="%d"), "n_posts": N("Posts na base", format="%d"),
               "tema": "Tema mais frequente", "formato": "Formato mais frequente", "pilar": "Pilar do Impulso",
               "outlier_mediano": N("× média", format="%.1f×")}
        mostrar = [c for c in cfg if tem(d, c)]
        if "segmento" in mostrar:
            d = d.assign(segmento=d.segmento.map(SEG_NOME).fillna(d.segmento))
        st.dataframe(d[mostrar], hide_index=True, width="stretch", height=480, column_config={c: cfg[c] for c in mostrar})
    todos = tentar(_canais, fonte["db"], versao(fonte["db"]))
    if todos is None or todos.empty:
        return
    with st.expander("Todos os perfis da base e como entraram"):
        if "incluir" in todos:
            todos = todos[todos.incluir == 1]
        if "segmento" in todos:
            todos = todos.assign(segmento=todos.segmento.map(SEG_NOME).fillna(todos.segmento))
        if "inscritos" in todos:
            todos = todos.sort_values("inscritos", ascending=False)
        cfg = {"titulo": "Perfil", "handle": "@", "plataforma": "Plataforma", "porte": "Tamanho",
               "inscritos": st.column_config.NumberColumn("Seguidores", format="localized"), "segmento": "Segmento",
               "tipo_criador": "Tipo de criador", "origem": "Como entrou"}
        mostrar = [c for c in cfg if tem(todos, c)]
        st.dataframe(todos[mostrar], hide_index=True, width="stretch", column_config={c: cfg[c] for c in mostrar})


def aba_padroes(fonte):
    k = fonte["id"]
    st.markdown("<h2>O que diferencia o top</h2>", unsafe_allow_html=True)
    ps = ler_csv(fonte["padroes"], dtype={"valor": str})
    if ps is None or not {"campo", "valor", "freq_top", "freq_resto"} <= set(ps.columns):
        return sem_dados(fonte, "padroes")
    selado = "selo" in ps
    st.markdown('<p class="meta">Quantas vezes cada característica aparece no top 10% e no controle (grupo do mesmo tamanho, '
                'sorteado fora do top). ' +
                ('O selo cruza com os Ads do Impulso: confirmado = também separa anúncio de CTR alto de CTR baixo. '
                 if selado else '') +
                '“Frágil” = menos de 5 posts do top sustentam o padrão.</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    d = ps
    if "plataforma" in ps:
        plat = c1.selectbox("Plataforma", plataformas(ps), key=f"pd_plat_{k}",
                            format_func=lambda x: "Todas juntas" if x == "todas" else x.capitalize())
        d = ps[ps.plataforma == plat]
    if selado:
        selos_ = c2.multiselect("Selo", sorted(ps.selo.dropna().unique()), default=sorted(ps.selo.dropna().unique()),
                                key=f"pd_selo_{k}")
        d = d[d.selo.isin(selos_)]
    if "lift" in d:
        d = d.sort_values("lift", ascending=False)
    esq, dir_ = st.columns([1.2, 1], gap="medium")
    with esq:
        st.markdown(LEGENDA_BARRAS, unsafe_allow_html=True)
        st.markdown(achados_html(d.to_dict("records"), n=40) or '<p class="meta">Nenhum padrão com esses filtros.</p>',
                    unsafe_allow_html=True)
    with dir_:
        if fonte["id"] != "A":  # Ads e kappa são evidências do Foco A
            st.markdown('<div class="vazio"><b>Como ler</b><p>Cada linha compara o top com o controle. “2,0× mais” quer dizer '
                        'que a característica aparece duas vezes mais no top. Padrão com poucos posts (frágil) é pista, '
                        'não regra.</p><p>Neste foco não há cruzamento com anúncios: os Ads do Impulso falam com '
                        'empreendedores, não com o cliente final.</p></div>', unsafe_allow_html=True)
            return
        st.markdown("<h2>Evidência da casa (Ads)</h2>", unsafe_allow_html=True)
        ii = ler_csv("impulso_interno.csv")
        if ii is not None:
            cfg = {"criativo": st.column_config.TextColumn("Criativo", width="medium"), "formato": "Formato",
                   "ctr": st.column_config.NumberColumn("CTR", format="%.2f%%"), "desempenho": "Desempenho",
                   "convite_participacao": "Convida a participar", "gatilho_identificacao": "Gatilho"}
            mostrar = [c for c in cfg if c in ii]
            st.dataframe(ii.sort_values("ctr", ascending=False)[mostrar] if "ctr" in ii else ii[mostrar],
                         hide_index=True, width="stretch", height=380, column_config={c: cfg[c] for c in mostrar})
        st.markdown("<h2>Confiabilidade da rubrica</h2>", unsafe_allow_html=True)
        v = ler_csv(f"{P.DATA}/validacao_resultado.csv")
        if v is not None and "kappa" in v:
            st.dataframe(v.sort_values("kappa", ascending=False), hide_index=True, width="stretch", column_config={
                "campo": "Campo", "n": "Posts rotulados à mão",
                "concordancia": st.column_config.NumberColumn("Concordância", format="percent"),
                "kappa": st.column_config.NumberColumn("Kappa", format="%.2f")})
            fracos = ", ".join(v[v.kappa < 0.4].campo)
            if fracos:
                st.caption(f"Kappa abaixo de 0,4 (pouco confiável, ler com cautela): {fracos}.")


def aba_base(fonte):
    st.markdown("<h2>Base de dados</h2>", unsafe_allow_html=True)
    r = ranking(fonte)
    if r is None or r.empty:
        sem_dados(fonte, "db")
    else:
        ag = dict(posts=("video_id", "size"), perfis=("canal", "nunique"), top=("top", "sum"))
        if "elegivel" in r:
            ag["elegiveis"] = ("elegivel", "sum")
        if "publicado" in r:
            ag |= dict(de=("publicado", "min"), ate=("publicado", "max"))
        st.dataframe(r.groupby("plataforma").agg(**ag).reset_index(), hide_index=True, width="stretch", column_config={
            "plataforma": "Plataforma", "posts": "Posts no ranking", "perfis": "Perfis", "top": "Posts no top 10%",
            "elegiveis": "Posts elegíveis", "de": "Mais antigo", "ate": "Mais recente"})
    if fonte["id"] == "A":
        st.markdown(secao_md("README.md", "## Base de dados", "## Metodologia").replace("## Base de dados", "", 1))
    else:
        st.markdown(f"Este foco olha para {fonte['desc']} A base é separada da do Foco A: são perfis de pequenos negócios "
                    "no Instagram falando com o próprio cliente.")
    st.markdown("<h2>Como escolhemos o top</h2>", unsafe_allow_html=True)
    st.markdown("\n".join(f"{i}. {f}" for i, f in enumerate(regua(fonte), 1)))
    aval = secao_md(AVALIACAO, "")
    if aval.strip():
        with st.expander("A régua nova é melhor? Avaliação"):
            if fonte["id"] != "A":
                st.caption("Avaliação feita na base do Foco A (Impulso → empreendedor).")
            st.markdown(aval)
    if fonte["id"] == "A":
        st.markdown("<h2>Metodologia</h2>", unsafe_allow_html=True)
        st.markdown(secao_md("README.md", "## Metodologia", "## Resultados").replace("## Metodologia", "", 1))


def aba_playbook(fonte):
    md = secao_md(fonte["playbook"], "")
    if md.strip():
        st.markdown(md)
    else:
        sem_dados(fonte, "playbook")


def aba_agente():
    modo = st.segmented_control("Modo", list(MODOS), format_func=MODOS.get, default="gerar_criativo",
                                label_visibility="collapsed") or "gerar_criativo"
    offline = st.toggle("Usar respostas salvas (sem rede)", value=st.query_params.get("offline") == "1",
                        help="Mostra execuções reais já feitas pelo agente, guardadas em data/execucoes.jsonl.")
    saida, meta = None, {}
    if offline:
        opcoes = [d for d in salvas() if d["entrada"]["mode"] == modo]
        if not opcoes:
            st.info("Ainda não há resposta salva neste modo. Desligue o modo sem rede para perguntar ao agente.")
        else:
            d = st.selectbox("Resposta salva", opcoes, format_func=lambda d: d["entrada"]["query"])
            saida, meta = d["saida"], {"tentativas": d.get("tentativas"), "pendencias": d.get("pendencias", "")}
            st.caption("Resposta salva · gerada pelo agente em " + d["em"][:16].replace("T", " "))
    else:
        with st.form("pergunta"):
            q = st.text_area("Pergunta", value=EXEMPLOS[modo], height=80)
            c1, c2, c3, c4 = st.columns(4)
            seg = c1.selectbox("Segmento", ["todos", "alimentação", "beleza", "varejo", "serviços"])
            plataforma = c2.selectbox("Plataforma", ["todas", "instagram", "youtube"])
            porte = c3.selectbox("Tamanho do perfil", ["todos", "micro", "medio", "grande"],
                                 format_func=lambda x: PORTE_NOME.get(x, x))
            pilar = c4.selectbox("Pilar", ["todos"] + P.PILARES)
            enviar = st.form_submit_button("Perguntar", type="primary")
        if enviar and q.strip():
            import agent  # import tardio: carrega o grafo só quando alguém pergunta
            filtros = {k: v for k, v in {"plataforma": plataforma, "porte": porte, "pilar": pilar}.items()
                       if v not in ("todas", "todos")}
            with st.status("O agente está trabalhando…", expanded=True) as stt:
                st.write("Consultando a base e escolhendo referências reais")
                st.write("Escrevendo e checando (pode levar até 1 minuto)")
                try:
                    saida = agent.run(modo, q.strip(), None if seg == "todos" else seg, filtros or None)
                except Exception as e:  # rede, crédito ou API fora
                    stt.update(label="Não deu para falar com o modelo agora", state="error")
                    st.error(f"{type(e).__name__}: {str(e)[:300]}. Ligue “Usar respostas salvas” para seguir a demo.")
                    return
                ult = json.loads(open(f"{P.DATA}/execucoes.jsonl", encoding="utf-8").readlines()[-1])
                meta = {"tentativas": ult.get("tentativas"), "pendencias": ult.get("pendencias", "")}
                stt.update(label=f"Pronto · {meta['tentativas']} tentativa(s)", state="complete", expanded=False)
            salvas.clear()
            st.session_state["ultima"] = (saida, meta)
        elif "ultima" in st.session_state:
            saida, meta = st.session_state["ultima"]

    if not saida:
        st.markdown('<p class="meta">Escolha um modo, ajuste a pergunta e clique em Perguntar. '
                    'Sem rede? Ligue “Usar respostas salvas”.</p>', unsafe_allow_html=True)
        return
    if saida["confidence_flag"]:
        relax = (" Filtros soltos por falta de exemplos: " + ", ".join(saida["filtros_relaxados"]) + ".") \
            if saida["filtros_relaxados"] else ""
        st.warning("Pouca evidência neste recorte: trate como pista, não como regra." + relax)
    ids = {r["video_id"] for r in saida["reference_posts"]}
    esq, dir_ = st.columns([1.35, 1], gap="medium")
    with esq:
        if saida["creatives"]:
            abas = st.tabs([f"{i}. {curto(c['formato'])} · {c['pilar']}" for i, c in enumerate(saida["creatives"], 1)])
            for aba, c in zip(abas, saida["creatives"]):
                with aba:
                    st.markdown(f'<p class="k">Gancho · primeiros 3 segundos</p><p class="hook">{html.escape(c["gancho"])}</p>',
                                unsafe_allow_html=True)
                    st.markdown('<p class="k">Roteiro</p>', unsafe_allow_html=True)
                    st.markdown(roteiro_md(c["roteiro"]))
                    st.markdown('<p class="k">Legenda (ícone no canto copia)</p>', unsafe_allow_html=True)
                    st.code(c["legenda"], language=None, wrap_lines=True)
                    st.markdown(f'<p class="k">Chamada para ação</p><p>{html.escape(c["cta"])}</p>', unsafe_allow_html=True)
                    st.markdown('<p class="k">Comprovante da checagem</p>', unsafe_allow_html=True)
                    st.markdown(comprovante(c, ids, meta.get("tentativas"), meta.get("pendencias", "")),
                                unsafe_allow_html=True)
                    st.markdown('<p class="k" style="margin-top:12px">Inspirado em</p>', unsafe_allow_html=True)
                    refs_grid(saida["reference_posts"], set(c["inspirado_em"]))
        st.markdown('<p class="k" style="margin-top:8px">Por quê</p>', unsafe_allow_html=True)
        st.markdown(saida["explanation"])
    with dir_:
        st.markdown("<h2>O que aparece mais no topo</h2>", unsafe_allow_html=True)
        st.markdown(LEGENDA_BARRAS.replace("</p>", " · selo = cruzamento com os Ads do Impulso</p>"), unsafe_allow_html=True)
        st.markdown(achados_html(saida["findings"]), unsafe_allow_html=True)
        if not saida["creatives"]:
            st.markdown("<h2>Posts de referência</h2>", unsafe_allow_html=True)
            refs_grid(saida["reference_posts"])


# ---------- página ----------
st.markdown('<h1>Pauta <span class="mk">Impulso</span></h1>', unsafe_allow_html=True)
if st.session_state.get("foco") not in FOCOS:  # clicar no foco já marcado desmarca; volta para o A
    st.session_state["foco"] = "A"
foco = st.segmented_control("Foco da análise", list(FOCOS), format_func=lambda f: FOCOS[f]["nome"], key="foco") or "A"
fonte = FOCOS[foco]
st.markdown("".join(f'<p class="foco{" on" if f["id"] == foco else ""}"><b>{f["nome"]}</b>: {f["desc"]}</p>'
                    for f in FOCOS.values()), unsafe_allow_html=True)
info = tentar(_base_info, fonte["db"], versao(fonte["db"]))
if info:
    plat, n_perfis, quando = info
    partes = ([f'{plat["instagram"]:,} posts do Instagram'] if plat.get("instagram") else []) + \
             ([f'{plat["youtube"]:,} vídeos do YouTube'] if plat.get("youtube") else [])
    st.markdown(f'<p class="meta">base deste foco: {" + ".join(partes) or "sem posts"} · {n_perfis} perfis'
                f'{" · coletado em " + quando if quando else ""}</p>'.replace(",", "."), unsafe_allow_html=True)
else:
    st.markdown('<p class="meta">base deste foco: ainda não disponível</p>', unsafe_allow_html=True)

t_ag, t_rk, t_pf, t_pd, t_bs, t_pb = st.tabs(["Agente", "Ranking", "Perfis em destaque", "Padrões", "Base e método", "Playbook"])
with t_ag:
    if foco != "A":
        st.info("O agente gera criativos para o Impulso (foco “Impulso → empreendedor”). As outras abas mostram o foco "
                "escolhido acima.")
    aba_agente()
with t_rk:
    aba_ranking(fonte)
with t_pf:
    aba_perfis(fonte)
with t_pd:
    aba_padroes(fonte)
with t_bs:
    aba_base(fonte)
with t_pb:
    aba_playbook(fonte)

st.markdown('<p class="meta" style="margin-top:32px">Proposta de estudante · Inteli Academy × Impulso Stone. '
            'Mesma função do servidor MCP e do agent.py. Cores inspiradas nos posts públicos do @impulsostone.</p>',
            unsafe_allow_html=True)
