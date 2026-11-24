"""Pauta Impulso (API): leitura (somente leitura) dos bancos e CSVs e montagem das respostas do contrato.

As funções de dados e de rótulo vêm de ui.py e paginas/*.py, sem streamlit. O cache é por mtime dos arquivos do foco."""
import collections
import datetime
import json
import math
import os
import random
import re
import sqlite3
import unicodedata

import numpy as np
import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = f"{RAIZ}/data"
THUMBS = f"{RAIZ}/static/thumbs"

# ---------------------------------------------------------------- focos e rótulos (de ui.py)
SEG_NOME = {"gestao_financas": "gestão e finanças", "vendas_marketing": "vendas e marketing", "pagamentos_maquininha":
            "pagamentos", "alimentacao": "alimentação", "beleza": "beleza", "varejo_moda": "varejo e moda",
            "servicos": "serviços", "geral": "geral"}
TIPO_NOME = {"clips": "Reels", "carousel_container": "Carrossel", "feed": "Imagem"}
PORTE_CURTO = {"micro": "micro", "medio": "médio", "grande": "grande"}
PLAT_NOME = {"instagram": "Instagram", "youtube": "YouTube", "todas": "Todas juntas"}
FOCOS = {
    "A": dict(id="A", nome="Impulso → empreendedor",
              desc="Conteúdo que engaja donos de pequeno negócio (o público do Impulso).",
              pergunta="O que faz um post engajar donos de pequeno negócio?",
              db=f"{DATA}/stone.db", padroes=f"{DATA}/padroes_selados.csv", perfis=f"{DATA}/perfis_destaque.csv",
              playbook=f"{RAIZ}/PLAYBOOK.md", midia=f"{DATA}/midia", url_midia="/midia/a",
              campos=dict(tema="r_tema_principal", formato="r_formato_video", gancho="r_tipo_hook",
                          gancho_txt="hook_primeiros_3s"),
              elegivel="perfis validados à mão, com 5 posts ou mais, e posts com pelo menos 7 dias que falam com dono de "
                       "pequeno negócio"),
    "B": dict(id="B", nome="Negócio → cliente",
              desc="Como o pequeno negócio engaja o cliente final dele.",
              pergunta="O que faz o post de um pequeno negócio engajar o cliente dele?",
              db=f"{DATA}/foco_b.db", padroes=f"{DATA}/b_achados.csv", perfis=f"{DATA}/b_perfis_destaque.csv",
              playbook=f"{RAIZ}/PLAYBOOK_B.md", midia=f"{DATA}/midia_b", url_midia="/midia/b",
              campos=dict(tema="segmento", formato="r_formato", gancho="r_tipo_gancho", gancho_txt="gancho_3s"),
              elegivel="posts e perfis que passaram nos filtros deste foco"),
}
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
    "desejo_alto": "Desperta desejo", "producao_alta": "Produção caprichada", "porte": "Tamanho do perfil",
}
VALOR = {"donos_de_negocio": "donos de negócio", "consumidor_final": "consumidor final", "pessoa_real": "pessoa real",
         "data_sazonal": "data comemorativa", "empreendedor_real": "empreendedor de verdade",
         "instituicao_ou_marca": "instituição ou marca", "True": "sim", "False": "não", "reel": "Reels",
         "medio": "médio", "media": "média", **SEG_NOME}
GRUPOS = [  # agrupamento dos padrões
    ("Gancho", ["tipo_hook", "tipo_gancho"]),
    ("Formato", ["formato_video", "formato", "tipo_post", "duracao_faixa", "legenda_tamanho", "texto_na_tela", "producao_alta"]),
    ("Tema e segmento", ["tema_principal", "segmento", "pilar_impulso"]),
    ("Chamada para ação", ["tem_cta", "tipo_cta", "convite_participacao", "convida_a_responder",
                           "oferta_ou_beneficio_explicito", "tem_oferta_ou_prazo", "mostra_preco"]),
    ("Quem aparece", ["tem_rosto", "rosto_do_dono", "cliente_aparece", "criador_e_empreendedor_real", "tipo_criador",
                      "gatilho_identificacao", "prova_social", "usa_linguagem_regional"]),
    ("Produto e tom", ["mostra_produto", "mostra_processo", "desejo_alto", "tom", "generico", "gatilho_sazonal"]),
]
GRUPO_DE = {c: g for g, campos in GRUPOS for c in campos}
LEITURA = {"video": "vídeo completo, com áudio", "imagens": "imagens do post", "thumbnail": "só a capa",
           "thumbnail_deepseek": "só a capa", "capa_deepseek": "só a capa",
           "quadros_audio_deepseek": "12 quadros do vídeo e o áudio transcrito"}
PRINCIPAIS = ["formato_video", "formato", "tema_principal", "tipo_hook", "tipo_gancho", "tipo_cta", "publico_alvo", "tom",
              "pilar_impulso", "gatilho_identificacao"]
ABRE_COM = {"promessa": "uma promessa", "pergunta": "uma pergunta", "curiosidade": "uma curiosidade", "polêmica":
            "uma polêmica", "dor": "uma dor do público", "número": "um número", "humor": "humor", "produto na tela":
            "o produto na tela", "emoção/história": "uma história", "promessa/resultado": "uma promessa de resultado",
            "oferta": "uma oferta"}


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


# ---------------------------------------------------------------- números e valores seguros para JSON
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


def vezes(resid):
    """Resíduo do modelo (escala log) -> vezes o esperado (número), ou None se o post não concorre."""
    return round(math.exp(min(float(resid), 50)), 3) if _ok(resid) else None


def vezes_txt(v):
    if not _ok(v):
        return "—"
    return f"{dec(v)}×" if v < 10 else (f"{v:.0f}×" if v < 1000 else f"{compacto(v)}×")


def numero(x):
    return float(x) if _ok(x) and isinstance(x, (int, float, np.number)) else None


def inteiro(x):
    return int(x) if numero(x) is not None else None


def texto(x):
    return x if isinstance(x, str) and x else None


def limpar(o):
    """Tipos do numpy/pandas e NaN -> JSON válido (NaN e infinito viram null)."""
    if isinstance(o, dict):
        return {str(k): limpar(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, set)):
        return [limpar(v) for v in o]
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, (int, np.integer)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return float(o) if _ok(float(o)) else None
    return None if o is pd.NaT or o is pd.NA else o


def norm(s):
    return unicodedata.normalize("NFKD", str(s).lower()).encode("ascii", "ignore").decode()


# ---------------------------------------------------------------- leitura com cache por mtime
def versao(f):
    return os.path.getmtime(f) if os.path.exists(f) else 0


_memo = {}


def memo(fn):
    """Cache simples por foco: refaz quando muda o mtime do banco, da pasta de mídia ou dos CSVs do foco."""
    def embrulho(k, *a):
        v = tuple(versao(FOCOS[k][x]) for x in ("db", "midia", "padroes", "perfis", "playbook"))
        achado = _memo.get((fn.__name__, k, a))
        if not achado or achado[0] != v:
            achado = _memo[(fn.__name__, k, a)] = (v, fn(k, *a))
        return achado[1]
    return embrulho


def conectar(db):
    if not os.path.exists(db):
        raise FileNotFoundError(db)
    return sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=3)  # só leitura: nunca cria banco vazio


def tentar(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except Exception:
        return None


def ler_csv(f, **kw):
    d = tentar(pd.read_csv, f, **kw) if os.path.exists(f) else None
    return d if d is not None and len(d) else None


def ler(f):
    return tentar(lambda: open(f, encoding="utf-8").read()) or ""


def secao_md(arquivo, inicio, fim=None):
    t = ler(arquivo)
    a = t.find(inicio)
    if a < 0:
        return ""
    b = t.find(fim, a + len(inicio)) if fim else -1
    return t[a:b if b > 0 else None]


def midia_idx(pasta):
    """{video_id: (nº de imagens, tem mp4)} com um único listdir."""
    idx = {}
    for f in tentar(os.listdir, pasta) or []:
        if f.endswith(".mp4"):
            idx[f[:-4]] = (idx.get(f[:-4], (0, False))[0], True)
        elif f.endswith(".jpg") and "_" in f:
            vid = f.rsplit("_", 1)[0]
            n, m = idx.get(vid, (0, False))
            idx[vid] = (n + 1, m)
    return idx


def gerar_thumb(vid, pasta):
    """Capa local reduzida uma vez em static/thumbs (mesma regra de ui.thumb_url). `vid` vem sempre do banco."""
    try:
        from PIL import Image
        os.makedirs(THUMBS, exist_ok=True)
        im = Image.open(f"{pasta}/{vid}_0.jpg").convert("RGB")
        im.thumbnail((400, 800))
        im.save(f"{THUMBS}/{vid}.jpg.tmp", "JPEG", quality=80)
        os.replace(f"{THUMBS}/{vid}.jpg.tmp", f"{THUMBS}/{vid}.jpg")
        return True
    except Exception:
        return False


@memo
def categorias(k):
    """({video_id: rubrica}, {video_id: fonte da leitura})."""
    c = conectar(FOCOS[k]["db"])
    linhas = c.execute("select video_id, rubrica, fonte from categorias").fetchall()
    c.close()
    return {v: (tentar(json.loads, r) or {}) for v, r, _ in linhas}, {v: f for v, _, f in linhas}


def rubricas(k):
    return categorias(k)[0]


@memo
def ranking(k):
    """Ranking + campos curtos da rubrica (prefixo r_) + mídia local + miniatura + texto de busca. Índice = video_id."""
    f = FOCOS[k]
    c = conectar(f["db"])
    r = pd.read_sql("select * from ranking", c)
    c.close()
    r = r.drop(columns=[x for x in ["tags", "thumbnail", "video_url", "imagens", "comentarios_txt", "coletado_em"] if x in r])
    r = r.drop_duplicates("video_id")
    rub = rubricas(k)
    if rub:
        rb = pd.DataFrame.from_dict(rub, orient="index")
        curtos = [x for x in rb if not rb[x].map(lambda v: isinstance(v, (list, dict)) or (isinstance(v, str) and len(v) > 60)).any()]
        rb = rb[curtos].apply(lambda col: col.map(lambda v: {True: "sim", False: "não"}.get(v, v) if isinstance(v, bool) else v))
        r = r.merge(rb.add_prefix("r_"), left_on="video_id", right_index=True, how="left")
    for col in ["titulo", "descricao", "canal", "url", "segmento", "porte", "tipo", "resid", "er", "channel_id", "grupo",
                "duracao_s", "views", "efeito_criador", "inscritos", "publicado"]:
        if col not in r:
            r[col] = None
    r["formato_post"] = r.tipo.map(TIPO_NOME).fillna("Post")
    r.loc[r.plataforma == "youtube", "formato_post"] = "Short"
    r["titulo"] = r.titulo.fillna("")
    r["descricao"] = r.descricao.fillna("").str.slice(0, 1200)
    r["post"] = r.titulo.where(r.titulo != "", r.descricao).str.slice(0, 140)
    r["seg"] = r.segmento  # valor cru, para casar com a tabela de padrões
    r["segmento"] = r.segmento.map(SEG_NOME).fillna(r.segmento)
    r["top"] = r.top.fillna(0).astype(bool)
    for col in ["top_er_puro", "elegivel"]:
        if col in r:
            r[col] = r[col].fillna(0).astype(bool)
    r["publicado"] = r.publicado.astype(str).str[:10].where(r.publicado.notna())
    if "pct_intencao" in r and r.pct_intencao.max() > 1:
        r["pct_intencao"] = r.pct_intencao / 100  # ponytail: aceita percentual (0–100) ou fração (0–1); guarda fração
    idx = midia_idx(f["midia"])
    r["n_img"] = [idx.get(i, (0, False))[0] for i in r.video_id]
    r["tem_mp4"] = [idx.get(i, (0, False))[1] for i in r.video_id]
    r["tem_video"] = r.tem_mp4 | (r.plataforma == "youtube")
    r["tem_midia"] = (r.n_img > 0) | r.tem_video
    r["analisado"] = r.video_id.isin(rub)
    r["resid"] = pd.to_numeric(r.resid, errors="coerce")
    r["pos_top"] = r[r.top].groupby("plataforma").resid.rank(ascending=False, method="first")
    r["duracao_faixa"] = pd.cut(pd.to_numeric(r.duracao_s, errors="coerce"), [0, 15, 30, 60, np.inf],
                                labels=["<15s", "15-30s", "30-60s", ">60s"]).astype(object)
    feitas = {x[:-4] for x in tentar(os.listdir, THUMBS) or []}
    r["thumb"] = [f"https://i.ytimg.com/vi/{v}/hqdefault.jpg" if p == "youtube" else
                  f"/midia/thumbs/{v}.jpg" if v in feitas or (n and gerar_thumb(v, f["midia"])) else None
                  for v, p, n in zip(r.video_id, r.plataforma, r.n_img)]
    gt = f["campos"]["gancho_txt"]
    r["gancho"] = [texto(str(rub.get(v, {}).get(gt) or "").strip(" \"“”'")) for v in r.video_id]
    extra = [" ".join([str(rub.get(v, {}).get(gt) or "")] + [x for x in rub.get(v, {}).get("elementos_top5") or [] if isinstance(x, str)])
             for v in r.video_id]
    tema = r[f["campos"]["tema"]].fillna("").astype(str) if f["campos"]["tema"] in r else ""
    r["_busca"] = (r.titulo + " " + r.descricao + " " + pd.Series(extra, index=r.index) + " " + tema + " " + r.canal.fillna("")).map(norm)
    # ordem "destaques": quem tem mídia e leitura primeiro, depois o top e o quanto superou; alterna as plataformas
    d = r.assign(_m=r.tem_midia & r.analisado).sort_values(["_m", "top", "resid"], ascending=False, na_position="last")
    d = d.assign(_i=d.groupby("plataforma").cumcount()).sort_values("_i", kind="stable")
    r["_dest"] = pd.Series(range(len(d)), index=d.index)
    return r.set_index("video_id", drop=False)


def linha(k, vid):
    """Linha do ranking como dict, ou None. É a conferência do id contra o banco antes de qualquer outra coisa."""
    R = ranking(k)
    return R.loc[vid].to_dict() if isinstance(vid, str) and vid in R.index else None


# ---------------------------------------------------------------- posts
def resumo(r, k):
    c = FOCOS[k]["campos"]
    return dict(
        id=r["video_id"], foco=k, plataforma=r["plataforma"], formato=r["formato_post"], canal=texto(r.get("canal")) or "",
        canal_id=texto(r.get("channel_id")) or "", titulo=r.get("post") or "", thumb=r.get("thumb"),
        tem_video=bool(r["tem_video"]), er=numero(r.get("er")), vezes=vezes(r.get("resid")), top=bool(r["top"]),
        posicao_top=inteiro(r.get("pos_top")), likes=inteiro(r.get("likes")) or 0, comentarios=inteiro(r.get("comentarios")) or 0,
        views=inteiro(r.get("views")), publicado=texto(r.get("publicado")), gancho=texto(r.get("gancho")),
        tema=texto(r.get(c["tema"])), tipo_gancho=valor_nome(r[c["gancho"]]) if texto(r.get(c["gancho"])) else None,
        porte=texto(r.get("porte")), url=texto(r.get("url")) or "")


def resumos(d, k):
    return [resumo(r, k) for r in d.to_dict("records")]


def post_resumo(k, vid):
    r = linha(k, vid)
    return resumo(r, k) if r else None


def _unicos(s):
    return sorted(x for x in s.dropna().astype(str).unique() if x)


def _porte_cru(p):
    return next((cru for cru, nome in PORTE_CURTO.items() if norm(nome) == norm(p)), p)


def filtrar(R, k, plataforma=None, formato=None, tema=None, porte=None):
    col = FOCOS[k]["campos"]["tema"]
    if plataforma and plataforma != "todas":
        R = R[R.plataforma == plataforma]
    if formato:
        R = R[R.formato_post == formato]
    if tema:
        R = R[R[col].astype(str) == tema] if col in R else R.head(0)
    if porte:
        R = R[R.porte == _porte_cru(porte)]
    return R


ORDENS = {"vezes": "resid", "er": "er", "comentarios": "comentarios", "recentes": "publicado"}


def posts(k, plataforma=None, formato=None, tema=None, porte=None, so_top=False, com_video=False, q=None,
          ordem="destaques", offset=0, limit=24):
    R = ranking(k)
    col = FOCOS[k]["campos"]["tema"]
    d = filtrar(R, k, plataforma, formato, tema, porte)
    if so_top:
        d = d[d.top]
    if com_video:
        d = d[d.tem_video]
    if q and q.strip():
        d = d[d._busca.str.contains(norm(q.strip()), regex=False)]
    d = (d.sort_values(ORDENS[ordem], ascending=False, na_position="last") if ordem in ORDENS else d.sort_values("_dest"))
    filtros = dict(plataformas=sorted(R.plataforma.dropna().unique(), key=lambda x: (x != "instagram", x)),
                   formatos=_unicos(R.formato_post), temas=_unicos(R[col]) if col in R else [],
                   portes=[p for p in PORTE_CURTO if p in set(R.porte)])
    return dict(total=len(d), itens=resumos(d.iloc[offset:offset + limit], k), filtros=filtros)


def midia(r, k):
    vid, u = r["video_id"], FOCOS[k]["url_midia"]
    imagens = [f"{u}/{vid}_{i}.jpg" for i in range(int(r.get("n_img") or 0))]
    if r["plataforma"] == "youtube":
        return dict(tipo="youtube", youtube_id=vid)
    if r.get("tem_mp4"):
        return dict(tipo="video", video_url=f"{u}/{vid}.mp4", imagens=imagens)
    if imagens:
        return dict(tipo="imagens" if len(imagens) > 1 else "capa", imagens=imagens)
    return dict(tipo="nenhuma")


def leitura(rub):
    """A leitura automática em pares rótulo/valor, sem nomes crus de campo."""
    out = [dict(rotulo=rotulo(c), valor=valor_nome(rub[c])) for c in PRINCIPAIS
           if isinstance(rub.get(c), str) and rub[c] and rub[c] != "nenhum"]
    return out + [dict(rotulo=rotulo(c), valor="sim") for c, v in rub.items() if v is True and not c.startswith("relevante")]


@memo
def medianas_top(k):
    """{plataforma: {campo de nota: mediana no top}}; 'todas' serve de reserva quando a plataforma tem menos de 5."""
    R, rub = ranking(k), rubricas(k)
    out = {}
    for plat, ids in [("todas", R[R.top].video_id)] + [(p, g.video_id) for p, g in R[R.top].groupby("plataforma")]:
        notas = pd.DataFrame([{c: v for c, v in rub[i].items() if c.endswith("_0a10") and isinstance(v, (int, float))}
                              for i in ids if i in rub])
        if len(notas) >= 5 or plat == "todas":
            out[plat] = notas.median().to_dict() if len(notas) else {}
    return out


def notas(rub, k, plataforma):
    med = medianas_top(k)
    med = med.get(plataforma) or med.get("todas") or {}
    return [dict(rotulo=rotulo(c), valor=v, mediana_top=numero(med.get(c))) for c, v in rub.items()
            if c.endswith("_0a10") and isinstance(v, (int, float)) and not isinstance(v, bool)]


def parecidos(R, row, k, n=6):
    """Posts com o mesmo tema, formato e gancho (ou, sem leitura, do mesmo segmento e criador). De ui.parecidos."""
    c = FOCOS[k]["campos"]
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
    return resumos(d.head(n), k)


def detalhe(k, vid):
    r = linha(k, vid)
    if not r:
        return None
    rub, fontes = categorias(k)
    rb = rub.get(vid) or {}
    leg, desc = r["titulo"].strip(), r["descricao"].strip()
    return dict(
        resumo(r, k), midia=midia(r, k), legenda=(leg + "\n\n" + desc).strip() if leg and desc and leg not in desc else (desc or leg),
        leitura=leitura(rb), notas=notas(rb, k, r["plataforma"]),
        elementos=[x for x in rb.get("elementos_top5") or [] if isinstance(x, str)][:5],
        criador=criadores_idx(k).get(r.get("channel_id")), parecidos=parecidos(ranking(k), r, k),
        pct_intencao=numero(r.get("pct_intencao")),
        metodo_leitura=LEITURA.get(fontes[vid], str(fontes[vid] or "").replace("_", " ") or None) if vid in fontes else None,
        seguidores=inteiro(r.get("inscritos")), duracao_s=numero(r.get("duracao_s")), concorre=bool(r.get("elegivel", True)))


def porque(r, k):
    """Frase curta montada da rubrica e dos números, sem modelo."""
    c = FOCOS[k]["campos"]
    g = ABRE_COM.get(r.get(c["gancho"]))
    tema, fmt = texto(r.get(c["tema"])), texto(r.get(c["formato"]))
    if k == "A":
        partes = [f"Abre com {g}" if g else "", f"fala de {tema}" if tema else ""]
        ini = " e ".join(p for p in partes if p) or f"{r['formato_post']} de perfil {PORTE_CURTO.get(r.get('porte'), '')}".strip()
    else:
        ini = (fmt or r["formato_post"]).capitalize() + (f" que abre com {g}" if g else "")
    v = vezes(r.get("resid"))
    fim = f"{dec(v) if v < 10 else num(round(v))} vezes o esperado para este perfil" if v else f"ER de {pct(r.get('er'))}"
    return f"{ini[0].upper()}{ini[1:]}; {fim}"


def destaques(k, limit=12):
    """Posts do top com mídia, um por criador, alternando as plataformas."""
    R = ranking(k)
    d = R[R.top & R.tem_midia & R.thumb.notna()].sort_values(["analisado", "resid"], ascending=False).drop_duplicates("canal")
    d = d.assign(_i=d.groupby("plataforma").cumcount()).sort_values(["_i", "plataforma"], kind="stable")
    return [dict(post=resumo(r, k), porque=porque(r, k)) for r in d.head(limit).to_dict("records")]


# ---------------------------------------------------------------- busca por ideia (TF-IDF à mão, sem rede)
PARADAS = set("que para com uma por dos das como mais seu sua voce nao sao tem tambem isso esse essa este esta aqui "
              "pra pro nos nas num numa aos ele ela eles elas meu minha quando muito sobre entre sem ser foi the and".split())


BONUS_TOP = 1.15


def termos(s):
    # ponytail: "radical" = tirar o s do plural; trocar por stemmer de verdade se a busca errar muito
    return [t[:-1] if len(t) > 4 and t.endswith("s") else t for t in re.findall(r"[a-z0-9]{3,}", norm(s)) if t not in PARADAS]


@memo
def indice(k):
    """Índice invertido: termo -> [(posição do post, tf)], idf por termo e norma de cada post."""
    R = ranking(k)
    postings = collections.defaultdict(list)
    for i, txt in enumerate(R._busca):
        for t, n in collections.Counter(termos(txt)).items():
            postings[t].append((i, 1 + math.log(n)))
    idf = {t: math.log(1 + len(R) / len(p)) for t, p in postings.items()}
    norma = [0.0] * len(R)
    for t, p in postings.items():
        for i, tf in p:
            norma[i] += (tf * idf[t]) ** 2
    return postings, idf, [math.sqrt(x) or 1 for x in norma]


def busca(k, q, limit=20, so_top=False):
    postings, idf, norma = indice(k)
    eh_top = ranking(k).top.to_numpy()
    de = {}  # radical -> palavra como a pessoa digitou
    for palavra in re.findall(r"\w{3,}", q.lower()):
        for t in termos(palavra):
            de.setdefault(t, palavra)
    pontos, casou = collections.defaultdict(float), collections.defaultdict(list)
    for t in de:
        for i, tf in postings.get(t, []):
            pontos[i] += tf * idf[t] ** 2
            casou[i].append(de[t])
    norma_q = math.sqrt(sum(idf[t] ** 2 for t in de if t in idf)) or 1
    # cosseno entre a pergunta e o post, vezes a fração das palavras da pergunta que o post tem
    achados = [(len(casou[i]) / len(de) * p / (norma[i] * norma_q), i) for i, p in pontos.items() if eh_top[i] or not so_top]
    # ponytail: desempate = post do top vale 15% a mais na ORDEM (o score devolvido é o cosseno puro); trocar por
    # faixas de semelhança se alguém reclamar da ordem
    achados = sorted(achados, key=lambda x: -x[0] * (BONUS_TOP if eh_top[x[1]] else 1))[:limit]
    R = ranking(k)
    return [dict(post=resumo(R.iloc[i].to_dict(), k), score=round(s, 4), casou=casou[i]) for s, i in achados]


# ---------------------------------------------------------------- criadores
def link_canal(cid, plat):
    if not texto(cid):
        return ""
    return f"https://www.youtube.com/channel/{cid}" if plat == "youtube" else f"https://www.instagram.com/{cid}/"


def _moda(s):
    s = s.dropna()
    return texto(s.mode().iloc[0]) if len(s) else None


@memo
def criadores_idx(k):
    """{channel_id: CriadorResumo}, a partir do ranking (todos os criadores da base, não só os da lista de destaque)."""
    R, c = ranking(k), FOCOS[k]["campos"]
    out = {}
    for cid, g in R.groupby("channel_id", sort=False):
        p = g.iloc[0]
        melhores = g[g.thumb.notna()].sort_values(["top", "resid"], ascending=False)
        ef = g.efeito_criador.dropna()
        out[cid] = dict(
            id=cid, foco=k, nome=texto(p.canal) or cid, plataforma=p.plataforma, seguidores=inteiro(p.inscritos) or 0,
            porte=texto(p.porte) or "", vezes=vezes(ef.iloc[0]) if len(ef) else None,
            n_top=int(g.top.sum()), n_posts=len(g), tema=_moda(g[c["tema"]]) if c["tema"] in g else None,
            formato=_moda(g[c["formato"]]) if c["formato"] in g else None, thumbs=list(melhores.thumb.head(4)),
            url=link_canal(cid, p.plataforma), er_mediano=numero(g.er.median()), comentarios=inteiro(g.comentarios.sum()) or 0)
    return out


def criadores(k, plataforma=None, porte=None):
    cs = [c for c in criadores_idx(k).values() if (not plataforma or plataforma == "todas" or c["plataforma"] == plataforma)
          and (not porte or c["porte"] == _porte_cru(porte))]
    return sorted(cs, key=lambda c: (c["vezes"] is None, -(c["vezes"] or 0), -c["n_top"]))


def criador(k, cid):
    c = criadores_idx(k).get(cid)
    if not c:
        return None
    R = ranking(k)
    g = R[R.channel_id == cid]
    bio = tentar(lambda: conectar(FOCOS[k]["db"]).execute("select descricao from canais where channel_id = ?", (cid,)).fetchone())
    serie = [dict(id=r["video_id"], data=texto(r.get("publicado")), er=numero(r.get("er")), vezes=vezes(r.get("resid")),
                  top=bool(r["top"])) for r in g.sort_values("publicado").to_dict("records")]
    return dict(resumo=c, bio=(texto(bio[0]) if bio else None) or "",
                posts=resumos(g.sort_values(["top", "resid"], ascending=False, na_position="last"), k), serie=serie)


# ---------------------------------------------------------------- rankings e comparação
FMT = {"vezes": vezes_txt, "er": pct, "comentarios": compacto}


def rankings(k, tipo="posts", plataforma=None, porte=None, metrica="vezes", limit=20):
    if tipo == "criadores":
        campo = {"vezes": "vezes", "er": "er_mediano", "comentarios": "comentarios"}[metrica]
        cs = sorted((c for c in criadores(k, plataforma, porte) if c[campo] is not None), key=lambda c: -c[campo])[:limit]
        return [dict(posicao=i, id=c["id"], nome=c["nome"], thumb=(c["thumbs"] or [None])[0], thumbs=c["thumbs"][:3], valor=c[campo],
                     valor_fmt=FMT[metrica](c[campo]),
                     sub=" · ".join([PLAT_NOME.get(c["plataforma"], c["plataforma"]), f"{compacto(c['seguidores'])} seguidores",
                                     f"{c['n_top']} no top"])) for i, c in enumerate(cs, 1)]
    col = ORDENS[metrica]
    d = filtrar(ranking(k), k, plataforma, porte=porte)
    d = d[d[col].notna()].sort_values(col, ascending=False).head(limit)
    out = []
    for i, r in enumerate(d.to_dict("records"), 1):
        v = vezes(r["resid"]) if metrica == "vezes" else numero(r[col])
        out.append(dict(posicao=i, id=r["video_id"], nome=texto(r.get("canal")) or "", thumb=r.get("thumb"), valor=v,
                        valor_fmt=FMT[metrica](v), sub=" · ".join(x for x in [r["formato_post"], (r.get("post") or "")[:90]] if x)))
    return out


def _valor_rub(c, v):
    if isinstance(v, bool):
        return "sim" if v else "não"
    if isinstance(v, (int, float)):
        return f"{v}/10" if c.endswith("_0a10") else str(v)
    return valor_nome(v) if isinstance(v, str) and v else None


def comparar(k, a, b):
    da, db_ = detalhe(k, a), detalhe(k, b)
    if not da or not db_:
        return None
    linhas = [("Plataforma", lambda d: PLAT_NOME.get(d["plataforma"], d["plataforma"])), ("Formato", lambda d: d["formato"]),
              ("Tamanho do perfil", lambda d: PORTE_CURTO.get(d["porte"], d["porte"])), ("Seguidores", lambda d: compacto(d["seguidores"])),
              ("Vezes o esperado", lambda d: vezes_txt(d["vezes"]) if d["vezes"] else "não concorre"),
              ("ER", lambda d: pct(d["er"])), ("Curtidas", lambda d: compacto(d["likes"])),
              ("Comentários", lambda d: compacto(d["comentarios"])), ("Views", lambda d: compacto(d["views"])),
              ("No top", lambda d: "sim" if d["top"] else "não")]
    dif = [dict(rotulo=r, a=fn(da) or "—", b=fn(db_) or "—", igual=fn(da) == fn(db_)) for r, fn in linhas]
    ra, rb = rubricas(k).get(a) or {}, rubricas(k).get(b) or {}
    for c in dict.fromkeys(list(ra) + list(rb)):
        va, vb = _valor_rub(c, ra.get(c)), _valor_rub(c, rb.get(c))
        if c.startswith("relevante") or isinstance(ra.get(c, rb.get(c)), list) or (va is None and vb is None):
            continue
        nome = "Gancho, nos 3 primeiros segundos" if c == FOCOS[k]["campos"]["gancho_txt"] else rotulo(c)
        nome = nome if nome not in {d["rotulo"] for d in dif} else f"{nome} (leitura)"
        dif.append(dict(rotulo=nome, a=va or "—", b=vb or "—", igual=va == vb))
    return dict(a=da, b=db_, diferencas=dif)


# ---------------------------------------------------------------- padrões e Ads
def _exemplos(R, plat, campo, valor, k, n=3):
    """Até n posts do top que têm o padrão (mesma regra da página Padrões)."""
    t = R[R.top & (R.plataforma == plat)] if plat != "todas" else R[R.top]
    v = {"True": "sim", "False": "não"}.get(valor, valor)
    if f"r_{campo}" in t:
        m = t[f"r_{campo}"].astype(str) == v
    elif campo == "segmento":
        m = t.seg.astype(str) == valor
    elif campo == "tipo_post":
        m = t.formato_post == {"carrossel": "Carrossel", "imagem": "Imagem", "reel": "Reels"}.get(valor, valor)
    elif campo in ("tipo_criador", "duracao_faixa", "porte") and campo in t:
        m = t[campo].astype(str) == valor
    else:
        return []
    return resumos(t[m].sort_values(["tem_midia", "resid"], ascending=False).drop_duplicates("canal").head(n), k)


@memo
def padroes(k, plataforma=None):
    ps = ler_csv(FOCOS[k]["padroes"], dtype={"valor": str})
    if ps is None or not {"campo", "valor", "freq_top", "freq_resto"} <= set(ps.columns):
        return dict(plataformas=[], itens=[])
    if "lift" not in ps:
        ps = ps.assign(lift=ps.freq_top / ps.freq_resto.where(ps.freq_resto > 0))
    if "plataforma" not in ps:
        ps = ps.assign(plataforma="todas")
    plats = sorted(ps.plataforma.dropna().unique(), key=lambda x: (x != "instagram", x == "todas", x))
    plat = plataforma if plataforma in plats else plats[0]
    R = ranking(k)
    itens = []
    for p in ps[ps.plataforma == plat].sort_values("lift", ascending=False, na_position="last").to_dict("records"):
        n_top = inteiro(p.get("n_top")) if "n_top" in p else None
        itens.append(dict(
            campo=p["campo"], valor=p["valor"], rotulo=nome_padrao(p["campo"], p["valor"]), grupo=GRUPO_DE.get(p["campo"], "Outros"),
            freq_top=numero(p["freq_top"]) or 0.0, freq_controle=numero(p["freq_resto"]) or 0.0, lift=numero(p["lift"]),
            n_top=n_top or 0, selo=texto(p.get("selo")), fragil=(n_top or 0) < 5, confianca=texto(p.get("confianca")),
            exemplos=_exemplos(R, plat, p["campo"], str(p["valor"]), k)))
    return dict(plataformas=plats, itens=itens, plataforma=plat)


def ads():
    ii = ler_csv(f"{RAIZ}/impulso_interno.csv")
    if ii is None or "ctr" not in ii:
        return []
    ps = ler_csv(FOCOS["A"]["padroes"], dtype={"valor": str})
    confirmados = sorted({(p["campo"], p["valor"]) for p in ps[ps.selo == "confirmado"].to_dict("records")} if ps is not None
                         and "selo" in ps else [])
    out = []
    for a in ii[ii.ctr.notna()].sort_values("ctr", ascending=False).to_dict("records"):
        marcas = ["convida a participar"] if str(a.get("convite_participacao")) == "True" else []
        if isinstance(a.get("gatilho_identificacao"), str) and a["gatilho_identificacao"] != "nenhum":
            marcas.append(valor_nome(a["gatilho_identificacao"]))
        if str(a.get("generico")) == "True":
            marcas.append("genérico")
        out.append(dict(criativo=a["criativo"], formato=texto(a.get("formato")), ctr=numero(a["ctr"]),
                        desempenho=texto(a.get("desempenho")), periodo=texto(a.get("periodo")), marcas=marcas,
                        impressoes=inteiro(a.get("impressoes")), engajamento=inteiro(a.get("engajamento")),
                        nota=texto(a.get("nota_do_relatorio")),
                        # padrões com selo "confirmado" que este criativo tem (mesmo rótulo de /padroes), pelas colunas do CSV
                        confirma=[nome_padrao(c, v) for c, v in confirmados if c in a and str(a[c]) == v]))
    return out


# ---------------------------------------------------------------- visualizações
@memo
def esperado_real(k, plataforma=None):
    R = filtrar(ranking(k), k, plataforma)
    d = R[R.resid.notna()]
    d = d.assign(real=d.likes.fillna(0) + d.comentarios.fillna(0))
    d = d[d.real > 0]  # escala log: zero não tem lugar no gráfico
    topo, resto = d[d.top], d[~d.top]
    resto = resto.sample(n=min(len(resto), max(0, 1500 - len(topo))), random_state=42)
    pontos = [dict(id=r["video_id"], canal=texto(r.get("canal")) or "", real=float(r["real"]),
                   esperado=round(r["real"] / math.exp(min(r["resid"], 50)), 2), top=bool(r["top"]), plataforma=r["plataforma"])
              for r in pd.concat([topo, resto]).to_dict("records")]
    return dict(pontos=pontos, nota=(
        f"Cada ponto é um post. Real = curtidas + comentários; esperado = real ÷ vezes o esperado (a estimativa do modelo para o "
        f"tamanho do perfil, formato, idade do post e histórico do criador). Use escala logarítmica nos dois eixos: acima da "
        f"diagonal, o post superou o esperado. Mostrando {len(pontos)} de {len(d)} posts que concorrem ao top: todos os "
        f"{len(topo)} do top e uma amostra aleatória fixa do resto."))


def _lidos(k, R):
    """Posts lidos pela IA que entram na comparação top × controle (mesmos cortes de P.carregar e ui.intencao)."""
    d = R[R.analisado]
    if "r_relevante_mpe" in d:
        d = d[(d.r_relevante_mpe != "não") & ~d.get("r_publico_alvo", pd.Series("", index=d.index)).isin(["consumidor_final", "nenhum"])]
    if "r_relevante_b" in d:
        d = d[d.r_relevante_b != "não"]
    return d


@memo
def temas(k, plataforma=None):
    col = FOCOS[k]["campos"]["tema"]
    d = _lidos(k, filtrar(ranking(k), k, plataforma))
    if col not in d:
        return []
    topo, ctl = d[d.grupo == "top"], d[d.grupo == "controle"]
    out = []
    for t in _unicos(d[d.grupo.notna()][col]):
        nt, nc = int((topo[col] == t).sum()), int((ctl[col] == t).sum())
        pt, pc = nt / max(len(topo), 1), nc / max(len(ctl), 1)
        out.append(dict(tema=t, n_top=nt, n_controle=nc, pct_top=round(pt, 4), pct_controle=round(pc, 4),
                        lift=round(pt / pc, 2) if pc else None))
    return sorted(out, key=lambda x: -x["n_top"])


def anatomia(k, vid):
    r = linha(k, vid)
    if not r:
        return None
    rub, fontes = categorias(k)
    rb, c = rub.get(vid) or {}, FOCOS[k]["campos"]
    dur = numero(r.get("duracao_s"))
    # Só o gancho tem janela definida pela rubrica (3 s). O resto não tem tempo medido: com duração, vai um lugar
    # aproximado (depois do gancho; a chamada para ação nos 3 s finais); sem duração (imagem, carrossel), fica null.
    g = min(3.0, dur) if dur else 3.0
    fim_meio = round(max(g, dur - 3), 1) if dur else None
    trechos = []
    if texto(r.get("gancho")):
        tipo = rb.get(c["gancho"].removeprefix("r_"))
        trechos.append(dict(rotulo="Gancho, nos 3 primeiros segundos" + (f" ({valor_nome(tipo)})" if texto(tipo) else ""),
                            texto=r["gancho"], inicio_s=0, fim_s=g,
                            aproximado=fontes.get(vid) not in ("video", "quadros_audio_deepseek") or not dur))  # só essas leituras viram os 3 s
    el = [x for x in rb.get("elementos_top5") or [] if isinstance(x, str)][:5]
    if el:
        trechos.append(dict(rotulo="O que explica a atenção", texto="; ".join(el), itens=el, inicio_s=g if dur else None,
                            fim_s=fim_meio, aproximado=True))
    if rb:
        cta = rb.get("tipo_cta")
        trechos.append(dict(rotulo="Chamada para ação", texto=valor_nome(cta) if texto(cta) and cta != "nenhum" else "nenhuma",
                            inicio_s=fim_meio, fim_s=dur, aproximado=True))
    return dict(post=resumo(r, k), duracao_s=dur, trechos=trechos,
                nota="Só o gancho tem janela definida (os 3 primeiros segundos). Os outros trechos não têm tempo medido: a "
                     "posição é aproximada.")


def falas(k, n=4):
    """Comentários reais de clientes com intenção de compra (regex e modelo concordam). Sem nome de usuário, sem @,
    sem telefone. Um por negócio, variando o segmento. De paginas/playbook.py."""
    rows = tentar(lambda: conectar(FOCOS[k]["db"]).execute(
        "select c.texto, r.canal, r.segmento from comentarios c join ranking r using (video_id) "
        "where c.intencao = 1 and c.regex = 1").fetchall()) or []
    chaves = ["quanto", "valor", "preço", "preco", "endereço", "endereco", "encomend", "entrega", "quero", "agenda", "comprar"]
    melhor = {}
    for t, canal, seg in rows:
        t = " ".join((t or "").split())
        tl = t.lower()
        if not 20 <= len(t) <= 110 or "@" in t or re.search(r"\d{5,}", t) or any(x in tl for x in ("link", "http", "cobrar")):
            continue
        s = sum(c in tl for c in chaves)
        if s and (canal not in melhor or (s, -len(t)) > (melhor[canal][0], -len(melhor[canal][1]))):
            melhor[canal] = (s, t, seg)
    out, segs = [], set()
    for canal, (_, t, seg) in sorted(melhor.items(), key=lambda kv: (-kv[1][0], len(kv[1][1]))):
        if seg not in segs:
            segs.add(seg)
            out.append(dict(texto=t, negocio=canal.split("|")[0].strip(), segmento=valor_nome(seg)))
    return out[:n]


@memo
def funil(k):
    """Curtida -> pedido (Foco B). Nos outros focos a forma é a mesma, vazia."""
    R = ranking(k)
    vazio = dict(etapas=[], por_formato=[], preco=dict(com=None, sem=None, n_com=0, n_sem=0), comentarios=[], nota=None)
    if "pct_intencao" not in R or "r_formato" not in R:
        return vazio
    lidos, quer, regex = tentar(lambda: conectar(FOCOS[k]["db"]).execute(
        "select sum(intencao is not null), sum(intencao = 1), sum(regex = 1) from comentarios").fetchone()) or (0, 0, 0)
    d = _lidos(k, R)
    d = d[d.pct_intencao.notna()]
    media = lambda g: round(float(g.pct_intencao.mean()), 4) if len(g) else None
    com, sem = (d[d.r_mostra_preco == v] for v in ("sim", "não")) if "r_mostra_preco" in d else (d.head(0), d.head(0))
    por_formato = sorted((dict(formato=f, pct_intencao=media(g), n=len(g)) for f, g in d.groupby("r_formato")),
                         key=lambda x: -x["pct_intencao"])
    return dict(
        etapas=[dict(rotulo="Curtidas", valor=inteiro(R.likes.sum()) or 0),
                dict(rotulo="Comentários", valor=inteiro(R.comentarios.sum()) or 0),
                dict(rotulo="Comentários lidos um a um", valor=int(lidos or 0)),
                dict(rotulo="Comentários com intenção de compra", valor=int(quer or 0))],
        por_formato=por_formato, preco=dict(com=media(com), sem=media(sem), n_com=len(com), n_sem=len(sem)),
        comentarios=falas(k, 6),
        nota=f"Intenção de compra = comentário de cliente que pergunta preço, endereço ou entrega, ou diz que quer. Lidos pelo "
             f"modelo: {int(lidos or 0)} comentários dos posts do top e do controle; a busca por palavras-chave na base toda "
             f"acha {int(regex or 0)}. As médias por formato e por preço usam {len(d)} posts lidos pela IA que têm comentário.")


# ---------------------------------------------------------------- agente e criativos
MARCA = r"(?:Slide|Card|Cena|Take) \d+|\(?\d{1,3}\s?[–-]\s?\d{1,3}\s?s\)?"


def cenas(roteiro):
    """Roteiro -> [{n, tempo, texto}]: uma cena por slide ('Slide 2: …') ou marca de tempo ('3-10s | …: …').
    `rotulo` (extra) traz a anotação curta da cena, como 'capa' ou 'GANCHO'."""
    t = (roteiro or "").strip()
    if "\n" not in t:  # tudo numa linha só: quebra antes de cada marca
        t = re.sub(rf"\s*/?\s*((?:{MARCA})[^:\n]{{0,40}}:)", r"\n\1", t)
    out = []
    for l in (x.strip() for x in t.split("\n")):
        m = re.match(rf"({MARCA})(.{{0,140}}?):\s+(.*)", l, flags=re.S)
        if m:
            cab = m.group(2).strip(" |")
            cab = cab[1:-1] if cab.startswith("(") and cab.endswith(")") else cab
            curto = len(cab) <= 40
            out.append(dict(n=len(out) + 1, tempo=m.group(1).strip("() "), rotulo=cab.replace(" | ", " · ") or None if curto else None,
                            texto=m.group(3) if curto else f"{cab}: {m.group(3)}"))
        elif l and out:
            out[-1]["texto"] += " " + l
        elif l:
            out.append(dict(n=1, tempo="", rotulo=None, texto=l))
    return out


_CAMPO_VALOR = re.compile(r"`?\b([a-z]+(?:_[a-z0-9]+)+|tom|formato|segmento|porte)\s*=\s*([\wÀ-ÿ/-]+(?: e [\wÀ-ÿ]+)?)`?")


def explicar(txt):
    """Troca os nomes crus de campo da explicação do agente pelos rótulos ('gatilho_identificacao = pessoa_real' ->
    'identificação: pessoa real'). Só na resposta: data/execucoes.jsonl fica como está."""
    def troca(m):
        campo, valor = m.group(1), m.group(2)
        if campo not in ROTULO:
            return m.group(0)
        return nome_padrao(campo, valor)[0].lower() + nome_padrao(campo, valor)[1:]
    t = _CAMPO_VALOR.sub(troca, txt or "")
    t = re.sub(r"`([a-z]+(?:_[a-z0-9]+)+)`", lambda m: rotulo(m.group(1)).lower() if m.group(1) in ROTULO else m.group(0), t)
    t = re.sub(r"\b[a-z]+(?:_[a-z0-9]+)+\b", lambda m: rotulo(m.group(0)).lower() if m.group(0) in ROTULO else
               VALOR.get(m.group(0), m.group(0)), t)  # campo ou valor cru solto no texto
    t = re.sub(r"\bgestão_financas\b", SEG_NOME["gestao_financas"], t)
    t = re.sub(r"\s+—\s+", ", ", t)
    t = re.sub(r"\bfreq_(top|resto)\b", lambda m: "frequência no top" if m.group(1) == "top" else "nos comuns", t)
    t = re.sub(r"\bn_top\s*(?:=|de)?\s*(\d+)", r"\1 posts do top", t)
    t = re.sub(r"\bn_top\b", "posts do top", t)
    t = re.sub(r"\blift\b(?:\s+de)?\s*(?:=\s*)?(\**)(\d+)[.,](\d+)(\**)", r"\1\2,\3×\4 mais no top", t)
    return re.sub(r"\blift\b", "vezes mais no top", t)


def resposta_agente(saida, **meta):
    """Saída do agent.py -> RespostaAgente do front: achados com rótulo, referências como PostResumo (o agente usa a base
    do Foco A) e criativos com as cenas já separadas. `meta` = id, em, modo, pergunta, segmento, tentativas, pendencias."""
    achados = [dict(selo=texto(a.get("selo")), campo=a["campo"], valor=str(a["valor"]), rotulo=nome_padrao(a["campo"], a["valor"]),
                    freq_top=numero(a.get("freq_top")) or 0.0, freq_controle=numero(a.get("freq_resto")) or 0.0,
                    lift=numero(a.get("lift")), n_top=inteiro(a.get("n_top")) or 0, fragil=(inteiro(a.get("n_top")) or 0) < 5)
               for a in saida.get("findings") or []]
    refs = [p for p in (post_resumo("A", r.get("video_id")) for r in saida.get("reference_posts") or []) if p]
    return dict(meta, achados=achados, referencias=refs,
                criativos=[dict(c, cenas=cenas(c.get("roteiro"))) for c in saida.get("creatives") or []],
                explicacao=explicar(saida.get("explanation")), baixa_confianca=bool(saida.get("confidence_flag")),
                filtros_relaxados=saida.get("filtros_relaxados") or [])


def salvas():
    """Respostas que o agente já deu (data/execucoes.jsonl): a mais recente de cada pergunta."""
    linhas = [d for d in (tentar(json.loads, l) for l in ler(f"{DATA}/execucoes.jsonl").splitlines() if l.strip()) if d]
    vistos, out = set(), []
    for i, d in reversed(list(enumerate(linhas))):
        e = d["entrada"]
        if (e["mode"], e["query"]) in vistos or (e["mode"] == "gerar_criativo" and not d["saida"]["creatives"]):
            continue
        vistos.add((e["mode"], e["query"]))
        out.append(resposta_agente(d["saida"], id=f"salva-{i}", em=d.get("em"), modo=e["mode"], pergunta=e["query"],
                                   segmento=e.get("segment"), tentativas=d.get("tentativas"), pendencias=d.get("pendencias", "")))
    return out


def criativos():
    """Os 5 criativos do playbook, no mesmo formato das respostas do agente."""
    f = f"{DATA}/criativos_playbook.json"
    em = datetime.datetime.fromtimestamp(versao(f)).isoformat(timespec="seconds")
    return [resposta_agente(c, id=f"pauta-{i}", em=em, modo="gerar_criativo", pergunta=c.get("pedido") or "",
                            segmento=texto(c.get("segmento")), tentativas=None, pendencias="")
            for i, c in enumerate(tentar(lambda: json.load(open(f, encoding="utf-8"))) or [], 1)]


# ---------------------------------------------------------------- playbook, método, focos
CAPS = {  # trecho do título no markdown -> (rótulo no sumário, título que afirma); de paginas/playbook.py
    "A": [("Como ler", "Como ler", "Três passos e quatro selos para ler os números"),
          ("diferencia o top", "O que o top faz diferente", "Quem ensina a fazer a conta aparece mais no top"),
          ("Mercado × Ads", "Mercado × Ads", "O que dá curtida no mercado não é o que dá clique nos Ads"),
          ("Perfis em destaque", "Perfis em destaque", "Quem engaja acima do próprio tamanho"),
          ("YouTube Shorts", "YouTube", "No YouTube, mostrar o negócio por dentro se destaca"),
          ("criativos", "As 5 pautas", "Cinco pautas prontas para o @impulsostone"),
          ("Próximo passo", "Próximo passo", "O próximo passo é um piloto em Ads"),
          ("Limitações", "Limitações", "O que este playbook não prova")],
    "B": [("Metodologia", "Como ler", "Como chegamos a estes números"),
          ("descoberta principal", "Curtida não é pedido", "O que dá curtida não é o que dá pedido"),
          ("Padrões", "O que o top faz diferente", "Humor e bastidor se destacam. Foto de produto é o básico."),
          ("Perfis em destaque", "Perfis em destaque", "Quem engaja acima do próprio tamanho"),
          ("Estudos de caso", "Estudos de caso", "Quatro negócios para olhar de perto"),
          ("recomendações", "5 recomendações", "Cinco recomendações para o lojista"),
          ("Limitações", "Limitações", "O que este playbook não prova")],
}
CAPA = {
    "A": ("Ensinar a conta engaja. Convidar a participar gera clique.",
          "Finanças explicadas na prática são o que mais separa o top dos posts comuns no Instagram. Mas reação não é clique: nos "
          "Ads do Impulso, ganha o post com gente de verdade e convite para participar. No fim, cinco pautas prontas para testar."),
    "B": ("O que dá curtida não é o que dá pedido",
          "Humor da rotina e bastidor fazem o post de um pequeno negócio aparecer. Preço à mostra é o que faz o cliente perguntar "
          "como comprar. São dois trabalhos diferentes, e o lojista precisa dos dois."),
}


def playbook(k):
    f = FOCOS[k]
    md = ler(f["playbook"])
    partes = re.split(r"^## +(.+)$", md, flags=re.M)  # [intro, título, corpo, título, corpo…]
    caps = []
    for i, (t, txt) in enumerate(zip(partes[1::2], partes[2::2]), 1):
        c = next((c for c in CAPS[k] if c[0].lower() in t.lower()), None)
        limpo = re.sub(r"^\d+\.\s*", "", t.strip())
        caps.append(dict(id=f"cap-{i}", titulo=c[2] if c else limpo, rotulo=c[1] if c else limpo, titulo_original=t.strip(),
                         markdown=txt.strip()))
    m1 = re.search(r"^# +(.+)$", partes[0], flags=re.M)
    intro = re.sub(r"^# +.+$", "", partes[0], count=1, flags=re.M).strip()
    conhecido = len(caps) >= 3 and md.strip()
    out = dict(titulo=CAPA[k][0] if conhecido else (m1.group(1) if m1 else "Playbook"),
               linha_fina=CAPA[k][1] if conhecido else intro,
               atualizado=datetime.date.fromtimestamp(versao(f["playbook"])).isoformat() if md else None,
               leitura_min=max(1, round(len(md.split()) / 200)), capitulos=caps, titulo_original=m1.group(1) if m1 else None,
               intro=intro)
    if k == "B":
        out["comentarios"] = falas(k)
    return out


def regua(k):
    """A régua em 4 passos, linguagem simples. De ui.regua."""
    return [dict(titulo=t, texto=x) for t, x in [
        ("Medimos o engajamento", "A nota de cada post é o ER: curtidas + comentários, divididos pelos seguidores do perfil."),
        ("Calculamos o esperado", "Só olhar o maior ER premia perfil pequeno e quem já engaja muito. Um modelo estima quanto "
         "cada post deveria engajar pelo tamanho do perfil, formato, idade do post e histórico do criador."),
        ("Ficamos com quem superou", "O top 10% são os posts que mais passaram desse esperado, dentro de cada plataforma e "
         "faixa de tamanho de perfil."),
        ("Sem deixar um criador dominar", f"Só concorre a base elegível ({FOCOS[k]['elegivel']}) e cada criador entra com no "
         "máximo 3 posts.")]]


def numeros(k):
    """A base em números: [{rotulo, valor, nota}] (valor já formatado; nota = a plataforma)."""
    out = []
    for plat, d in ranking(k).groupby("plataforma"):
        it = [("Posts no ranking", num(len(d))), ("Criadores", num(d.canal.nunique()))]
        if "elegivel" in d:
            it.append(("Concorrem ao top", num(int(d.elegivel.sum()))))
        it.append(("Posts no top", num(int(d.top.sum()))))
        if "top_er_puro" in d and d.top.sum():
            it.append(("Também top pela régua antiga", f"{int((d.top & d.top_er_puro).sum())} de {int(d.top.sum())}"))
        it.append(("Lidos em detalhe pela IA", num(int(d.analisado.sum()))))
        datas = d.publicado.dropna()
        if len(datas):
            br = lambda s: f"{s[8:10]}/{s[5:7]}/{s[:4]}"
            it.append(("Período", f"{br(datas.min())} a {br(datas.max())}"))
        out += [dict(rotulo=a, valor=b, nota=PLAT_NOME.get(plat, plat), plataforma=plat) for a, b in it]
    return out


def itens_md(md):
    """Itens de lista do markdown (com as linhas de continuação), em texto simples; sem lista, os parágrafos."""
    its = [" ".join(x.split()) for x in re.findall(r"(?m)^(?:-|\d+\.) +(.+(?:\n(?!\s*(?:-|\d+\.) |\s*$|#).+)*)", md)]
    its = its or [" ".join(p.split()) for p in re.split(r"\n\s*\n", md) if p.strip() and not p.lstrip().startswith(("#", "|"))]
    return [re.sub(r"\*\*|`", "", x) for x in its]


def metodo(k):
    f, readme = FOCOS[k], f"{RAIZ}/README.md"
    if k == "A":
        lim = secao_md(readme, "## Limitações e evolução").replace("## Limitações e evolução", "", 1)
        lim += "\n" + secao_md(readme, "### Limitações da base", "## Metodologia").replace("### Limitações da base", "", 1)
        metodologia = secao_md(readme, "## Metodologia", "## Resultados").replace("## Metodologia", "", 1)
        v = ler_csv(f"{DATA}/validacao_resultado.csv")
    else:
        lim = secao_md(f["playbook"], "## Limitações").replace("## Limitações", "", 1)
        metodologia = secao_md(f["playbook"], "## Metodologia em 5 linhas", "## ").replace("## Metodologia em 5 linhas", "", 1)
        v = None  # a validação manual foi feita só na base do Foco A
    kappa = [dict(campo=x["campo"], rotulo=rotulo(x["campo"]), concordancia=numero(x.get("concordancia")), kappa=numero(x["kappa"]),
                  n=inteiro(x.get("n"))) for x in v.sort_values("kappa", ascending=False).to_dict("records")] if v is not None and "kappa" in v else []
    return dict(passos=regua(k), numeros=numeros(k), avaliacao_md=ler(f"{DATA}/avaliacao_regua.md"),
                limitacoes=itens_md(lim) or ["Amostra pequena e não aleatória; os padrões são observados, não são causa."],
                limitacoes_md=lim.strip(),
                kappa=kappa, metodologia_md=metodologia.strip(),
                avaliacao_nota=None if k == "A" else "Avaliação feita na base do foco “Impulso → empreendedor”.")


def focos():
    out = []
    for k, f in FOCOS.items():
        R = tentar(ranking, k)
        quando = tentar(lambda: conectar(f["db"]).execute("select max(coletado_em) from videos").fetchone()[0]) or ""
        plat = R.plataforma.value_counts().to_dict() if R is not None else {}
        out.append(dict(id=k, nome=f["nome"], descricao=f["desc"], pergunta=f["pergunta"], base=dict(
            posts=len(R) if R is not None else 0, criadores=int(R.channel_id.nunique()) if R is not None else 0,
            top=int(R.top.sum()) if R is not None else 0,
            por_plataforma=dict(instagram=int(plat.get("instagram", 0)), youtube=int(plat.get("youtube", 0))),
            coletado_em=quando[:10] or None)))
    return out


# ---------------------------------------------------------------- avaliar: média da nota no top e nos comuns
@memo
def medias_nota(k, plataforma):
    """Nota do avaliar.py aplicada aos posts lidos do top e do controle -> {top, comuns} (médias, 0 a 100)."""
    import avaliar as A
    base = A.base(k)
    padroes_, _ = A.ler_padroes(k, plataforma)
    if base is None or not padroes_:
        return dict(top=None, comuns=None)
    da_plat = base[base.plataforma == plataforma]
    base = da_plat if (da_plat.grupo == "top").sum() >= 5 else base
    notas_ = base.assign(_nota=[A.calcular_nota(A.casar(p, padroes_))[0] for p in base.to_dict("records")]).groupby("grupo")._nota.mean()
    return dict(top=numero(round(notas_.get("top", float("nan")), 1)), comuns=numero(round(notas_.get("controle", float("nan")), 1)))


def opcoes_agente():
    """Segmentos e pilares que o agente aceita como filtro (as mesmas listas do agent.py e do pipeline.py)."""
    import agent
    return dict(segmentos=list(agent.SEGMENTOS), pilares=list(agent.P.PILARES))


def aquecer():
    """Carrega o que é caro (ranking do YouTube, índice da busca, médias) antes do primeiro pedido."""
    for k in FOCOS:
        tentar(ranking, k)
        tentar(criadores_idx, k)
        tentar(indice, k)
        tentar(medias_nota, k, "instagram")
        tentar(padroes, k, None)
    tentar(medias_nota, "A", "youtube")
