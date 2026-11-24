"""Foco B do case Stone: como o pequeno negócio engaja o CLIENTE FINAL dele no Instagram.

Etapas, nesta ordem (cada uma confere o gasto na Apify e para em US$ 4,50):
  python foco_b.py descobrir            # posts de hashtags de negócio local -> autores
  python foco_b.py triar [--rodada 2]   # detalhes dos autores + DeepSeek: é negócio real? -> data/b_perfis.csv
  python foco_b.py coletar              # posts dos aprovados -> data/foco_b.db (videos, canais) + rank + mídia
  python foco_b.py rank                 # ER, resíduo do modelo misto, top por porte, controle
  python foco_b.py midia                # baixa capas, imagens e vídeos dos candidatos (URLs expiram)
  python foco_b.py categorizar          # rubrica B: DeepSeek nas imagens + legenda (tudo); --metodo video = Gemini no vídeo
  python foco_b.py comentarios          # intenção de compra nos comentários (regex + DeepSeek)
  python foco_b.py analisar             # lift, perfis em destaque, segmento -> data/b_*.csv
"""
import argparse
import glob
import json
import os
import re
import shutil
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Literal

import httpx
import numpy as np
import pandas as pd
from pydantic import BaseModel

import pipeline as P

P._chave, P._google = min(2, len(P.GEMINI_KEYS) - 1), None  # terceira chave Gemini: não disputa cota com o Foco A
DATA = P.DATA
DBB = f"{DATA}/foco_b.db"
MIDIA = f"{DATA}/midia_b"
META = f"{DATA}/b_meta.json"
DEEPSEEK = P.N1_MODEL
TETO_USD, USD_RESULTADO = 4.50, 0.0027
HASHTAGS = ["padariaartesanal", "confeitariaartesanal", "salaodebeleza", "barbearia", "lojaderoupas",
            "modafemininabrasil", "petshop", "marmitaria", "hamburgueriaartesanal", "manicure", "atelie"]
SEGMENTOS = Literal["alimentação", "beleza", "moda/varejo", "serviços", "pet", "outro"]
MIN_SEG, MAX_SEG, MIN_POSTS, MAX_PERFIS = 500, 200_000, 30, 28


def db():
    return sqlite3.connect(DBB)


def meta(**novo):
    m = json.load(open(META)) if os.path.exists(META) else {}
    if novo:
        m.update(novo)
        json.dump(m, open(META, "w"), ensure_ascii=False, indent=1)
    return m


# ---------- orçamento Apify ----------

def gasto():
    """Maior entre o gasto que a Apify reporta (pode atrasar minutos) e o estimado pelos caches b_*.json."""
    r = httpx.get("https://api.apify.com/v2/users/me/limits", params={"token": os.environ["APIFY_TOKEN_2"]}, timeout=30)
    api = r.json()["data"]["current"]["monthlyUsageUsd"]
    local = sum(len(json.load(open(f))) for f in glob.glob(f"{DATA}/raw/b_*.json")
                if not f.endswith("b_triagem.json") and not f.endswith("b_pre.json")) * USD_RESULTADO
    return max(api, local)


def apify_b(cache, n_estimado, **inp):
    if not os.path.exists(f"{DATA}/raw/{cache}.json"):
        g = gasto()
        if g + n_estimado * USD_RESULTADO > TETO_USD:
            raise SystemExit(f"PARADO: gasto US$ {g:.2f} + ~US$ {n_estimado * USD_RESULTADO:.2f} passaria de US$ {TETO_USD}")
        print(f"Apify: gasto US$ {g:.2f}; rodando {cache} (~{n_estimado} resultados)")
    itens = P.apify(cache, **inp)
    print(f"Apify: {cache} = {len(itens)} itens; gasto agora US$ {gasto():.2f}")
    return itens


def em_paralelo(fn, itens, n=6):
    """Roda fn(item) em threads; devolve [(item, resultado)] dos que deram certo."""
    out = []
    with ThreadPoolExecutor(n) as ex:
        futs = {ex.submit(fn, i): i for i in itens}
        for f in as_completed(futs):
            try:
                out.append((futs[f], f.result()))
            except Exception as e:
                print(f"  ERRO {str(futs[f])[:40]}: {str(e)[:120]}")
    return out


# ---------- 1. descoberta ----------

class Pre(BaseModel):
    username: str
    negocio_local: bool  # parece um pequeno negócio que vende ao consumidor final


class Pres(BaseModel):
    itens: list[Pre]


def descobrir(a):
    posts = apify_b("b_hashtags", len(HASHTAGS) * a.por_hashtag, resultsType="posts", resultsLimit=a.por_hashtag,
                    directUrls=[f"https://www.instagram.com/explore/tags/{h}/" for h in HASHTAGS])
    df = pd.DataFrame([dict(username=p.get("ownerUsername"), nome=p.get("ownerFullName") or "",
                            hashtag=(p.get("inputUrl") or "").rstrip("/").split("/")[-1],
                            legenda=(p.get("caption") or "")[:300].replace("\n", " "))
                       for p in posts if p.get("ownerUsername")]).drop_duplicates("username")
    # pré-triagem barata (DeepSeek, só texto) para não pagar detalhes de quem claramente não é negócio local
    f = f"{DATA}/raw/b_pre.json"
    pre = json.load(open(f)) if os.path.exists(f) else {}
    falta = df[~df.username.isin(pre)]
    lotes = [falta.iloc[i:i + 30] for i in range(0, len(falta), 30)]

    def um(lote):
        txt = "\n".join(f"@{r.username} | {r.nome} | #{r.hashtag} | {r.legenda}" for r in lote.itertuples())
        return P.llm("Para cada perfil do Instagram abaixo (usuário | nome | hashtag | legenda de um post), diga se "
                     "parece um PEQUENO NEGÓCIO LOCAL BRASILEIRO que vende produto ou serviço ao consumidor final "
                     "(padaria, salão, loja de bairro, pet shop, ateliê...). false para influenciador, curso, "
                     "fornecedor/atacado para lojistas, franquia ou marca grande, perfil pessoal, perfil estrangeiro.\n" + txt,
                     Pres, model=DEEPSEEK)
    for _, r in em_paralelo(um, lotes, 4):
        pre.update({i.username.lstrip("@"): i.negocio_local for i in r.itens})
    json.dump(pre, open(f, "w"))
    df["negocio_local"] = df.username.map(pre)
    df.to_csv(f"{DATA}/b_autores.csv", index=False)
    print(f"{len(posts)} posts de {len(HASHTAGS)} hashtags -> {len(df)} autores, {int((df.negocio_local == True).sum())} prováveis negócios")  # noqa: E712
    print(df.groupby("hashtag").negocio_local.agg(["size", "sum"]).to_string())


# ---------- 2. triagem ----------

class TriagemB(BaseModel):
    e_negocio_real: bool          # vende produto/serviço ao consumidor final
    segmento: SEGMENTOS
    brasileiro: bool
    franquia_ou_marca_grande: bool
    fala_com_empreendedores: bool  # curso, mentoria, fornecedor B2B, influenciador (isso é Foco A)
    motivo: str


def triar(a):
    aut = pd.read_csv(f"{DATA}/b_autores.csv")
    aut = aut[aut.negocio_local == True]  # noqa: E712
    aut = aut.assign(o=aut.groupby("hashtag").cumcount()).sort_values("o")  # rodízio entre hashtags: variedade de segmento
    ini = (a.rodada - 1) * a.limite
    alvo = list(aut.username[ini:ini + a.limite])
    if alvo:
        apify_b(f"b_detalhes_{a.rodada}", len(alvo), directUrls=[f"https://www.instagram.com/{u}/" for u in alvo],
                resultsType="details")
    det = {p["username"]: p for f in sorted(glob.glob(f"{DATA}/raw/b_detalhes_*.json")) for p in json.load(open(f))
           if p.get("username") and not p.get("error")}
    f = f"{DATA}/raw/b_triagem.json"
    tri = json.load(open(f)) if os.path.exists(f) else {}

    def um(u):
        p = det[u]
        legs = "\n".join("- " + (x.get("caption") or "")[:300].replace("\n", " ") for x in (p.get("latestPosts") or [])[:8])
        return P.llm(f"""Perfil do Instagram. Decida se é um micro/pequeno negócio REAL que vende produto ou serviço ao CONSUMIDOR FINAL.
- e_negocio_real: true só se o perfil é do próprio negócio (padaria, confeitaria, salão, barbearia, manicure, loja de bairro, pet shop, lanchonete, ateliê, assistência...) e fala com o cliente dele.
- franquia_ou_marca_grande: rede, franquia, indústria ou marca nacional.
- fala_com_empreendedores: curso, mentoria, fornecedor/atacado para lojistas, influenciador, agência, quem ensina a empreender.
- brasileiro: negócio no Brasil, em português do Brasil.
Usuário: @{u}
Nome: {p.get('fullName')}
Categoria: {p.get('businessCategoryName')}
Seguidores: {p.get('followersCount')} | posts: {p.get('postsCount')}
Bio: {p.get('biography')}
Legendas recentes:
{legs}""", TriagemB, model=DEEPSEEK).model_dump()
    for u, r in em_paralelo(um, [u for u in det if u not in tri]):
        tri[u] = r
    json.dump(tri, open(f, "w"), ensure_ascii=False)
    df = pd.DataFrame([dict(id=u, titulo=p.get("fullName") or u, descricao=(p.get("biography") or "").replace("\n", " "),
                            seguidores=p.get("followersCount") or 0, posts=p.get("postsCount") or 0,
                            privado=bool(p.get("private")), **tri.get(u, {})) for u, p in det.items()])
    df["porte"] = df.seguidores.map(P.porte)
    df["aprovado"] = ((df.e_negocio_real == True) & (df.brasileiro == True) & (df.franquia_ou_marca_grande == False)  # noqa: E712
                      & (df.fala_com_empreendedores == False) & ~df.privado  # noqa: E712
                      & df.seguidores.between(MIN_SEG, MAX_SEG) & (df.posts >= MIN_POSTS))
    # até MAX_PERFIS, em rodízio por segmento × porte (variedade)
    ap = df[df.aprovado]
    esc = ap.assign(o=ap.groupby(["segmento", "porte"]).cumcount()).sort_values(["o", "seguidores"]).head(MAX_PERFIS).id
    df["incluir"] = df.id.isin(esc).astype(int)
    df.sort_values(["incluir", "aprovado", "seguidores"], ascending=False).to_csv(f"{DATA}/b_perfis.csv", index=False)
    print(f"{len(df)} perfis triados, {int(df.aprovado.sum())} aprovados, {int(df.incluir.sum())} incluídos")
    print(df[df.incluir == 1].groupby(["segmento", "porte"]).size().to_string())
    meta(perfis_triados=len(df), perfis_aprovados=int(df.aprovado.sum()), perfis_incluidos=int(df.incluir.sum()))


# ---------- 3. coleta ----------

def coletar(a):
    perfis = pd.read_csv(f"{DATA}/b_perfis.csv")
    perfis = perfis[perfis.incluir == 1]
    itens = apify_b("b_posts", len(perfis) * a.por_perfil, directUrls=[f"https://www.instagram.com/{u}/" for u in perfis.id],
                    resultsType="posts", resultsLimit=a.por_perfil, onlyPostsNewerThan="365 days")
    agora = datetime.now(timezone.utc)
    rows = []
    for p in itens:
        if not p.get("shortCode") or p.get("error"):
            continue
        pub = datetime.fromisoformat(p["timestamp"].replace("Z", "+00:00"))
        rows.append(dict(
            video_id=p["shortCode"], channel_id=p["ownerUsername"], titulo="", descricao=p.get("caption") or "",
            tags=",".join(p.get("hashtags") or []), publicado=p["timestamp"], idade_dias=(agora - pub).days,
            duracao_s=p.get("videoDuration"), views=p.get("videoPlayCount"),
            likes=p["likesCount"] if (p.get("likesCount") or -1) >= 0 else None,  # -1 = curtidas ocultas
            comentarios=p.get("commentsCount"), thumbnail=p.get("displayUrl"), coletado_em=agora.isoformat(),
            plataforma="instagram", tipo=p.get("productType") or p.get("type"),
            fixado=bool(p.get("isPinned")), video_url=p.get("videoUrl"),
            imagens=",".join(c.get("displayUrl", "") for c in p.get("childPosts") or []),
            # a Apify já traz até ~12 comentários junto do post: intenção de compra sem gastar mais
            comentarios_txt=json.dumps([dict(u=c.get("ownerUsername"), t=c.get("text") or "")
                                        for c in p.get("latestComments") or []], ensure_ascii=False),
        ))
    df = pd.DataFrame(rows).drop_duplicates("video_id")
    total = len(df)
    df = df[df.channel_id.isin(perfis.id) & (df.idade_dias <= 365) & ~df.fixado]  # collabs trazem outro dono
    canais = pd.DataFrame(dict(channel_id=perfis.id, titulo=perfis.titulo, plataforma="instagram", inscritos=perfis.seguidores,
                               porte=perfis.porte, segmento=perfis.segmento, descricao=perfis.descricao))
    con = db()
    df.to_sql("videos", con, if_exists="replace", index=False)
    canais.to_sql("canais", con, if_exists="replace", index=False)
    print(f"{total} posts -> {len(df)} em 12 meses (sem fixados/collabs), {df.channel_id.nunique()} perfis | "
          f"tipos: {df.tipo.value_counts().to_dict()} | curtidas ocultas: {int(df.likes.isna().sum())}")
    meta(posts_coletados=len(df), coletado_em=agora.isoformat())
    rank(a)
    midia(a)


# ---------- 4. ranking ----------

def rankear(v, c, q=0.90):
    """Mesma régua do Foco A (pipeline.ranquear), com o quantil do top como parâmetro: top = resíduo do modelo misto
    >= quantil q dentro do porte, criador com >=5 posts, post com >=7 dias, máx. 3 por criador; controle = sorteio."""
    df = v.merge(c[["channel_id", "titulo", "inscritos", "porte", "segmento"]].rename(columns={"titulo": "canal"}), on="channel_id")
    df = df[df.likes.notna() & (df.inscritos > 0)].copy()
    df["comentarios"] = df.comentarios.fillna(0)
    df["er"] = (df.likes + df.comentarios) / df.inscritos
    df["conversa"] = df.comentarios / df.likes.where(df.likes > 0)
    g = df.groupby("channel_id").er
    df["outlier"] = (df.er / g.transform("median")).where(g.transform("size") >= P.MIN_POSTS_CRIADOR)
    df["elegivel"] = (g.transform("size") >= P.MIN_POSTS_CRIADOR) & (df.idade_dias >= P.MIN_IDADE_TOP)
    df["resid"], df["efeito_criador"] = np.nan, np.nan
    el = df[df.elegivel]
    df.loc[el.index, "resid"], df.loc[el.index, "efeito_criador"] = P.residuo_modelo(el)
    corte = df[df.elegivel].groupby("porte").resid.transform(lambda x: x.quantile(q))
    cand = df[df.elegivel & (df.resid >= corte.reindex(df.index))]
    df["top"] = df.index.isin(cand.sort_values("resid", ascending=False).groupby("channel_id").head(P.MAX_POR_CRIADOR).index)
    df["top_er_puro"] = df.er >= df.groupby("porte").er.transform(lambda x: x.quantile(0.9))
    n_top = df[df.top].groupby("porte").size()
    ctrl = df[~df.top & df.elegivel].groupby("porte", group_keys=False)[df.columns].apply(
        lambda d: d.sample(min(len(d), n_top.get(d.name, 0)), random_state=42))
    df["grupo"] = None
    df.loc[df.top, "grupo"] = "top"
    df.loc[ctrl.index, "grupo"] = "controle"
    df["amostra"] = df.grupo.notna()
    df["url"] = "https://www.instagram.com/p/" + df.video_id + "/"
    return df.sort_values("resid", ascending=False)


def modelo_stats(el):
    """Elasticidade b (log seguidores) e fatia da variância explicada pelo criador (ICC) — mesma fórmula do residuo_modelo."""
    import statsmodels.formula.api as smf
    d = el.assign(y=np.log1p(el.likes + el.comentarios), logF=np.log(el.inscritos.clip(lower=1)),
                  logIdade=np.log1p(el.idade_dias.fillna(30)), formato=el.tipo.fillna("x"))
    m = smf.mixedlm("y ~ logF + logIdade + C(formato)", d, groups=d["channel_id"]).fit(method="bfgs")
    var_c = float(m.cov_re.iloc[0, 0])
    return dict(b_seguidores=round(float(m.params["logF"]), 3), b_ic95=[round(float(x), 3) for x in m.conf_int().loc["logF"]],
                var_criador=round(var_c, 3), var_residual=round(float(m.scale), 3),
                icc_criador=round(var_c / (var_c + float(m.scale)), 3), n_posts=len(d), n_criadores=int(d.channel_id.nunique()))


def rank(a):
    con = db()
    v, c = pd.read_sql("select * from videos", con), pd.read_sql("select * from canais", con)
    q = 0.90
    df = rankear(v, c, q)
    por_porte = df[df.top].porte.value_counts()
    # base pequena: se algum porte com >=30 posts elegíveis ficar com menos de 5 no top, usa top 15% (declarado)
    grandes = df[df.elegivel].porte.value_counts()
    if a.q or any(por_porte.get(p, 0) < 5 for p in grandes[grandes >= 30].index):
        q = a.q or 0.85
        df = rankear(v, c, q)
    old = pd.read_sql("select video_id, pct_intencao, pct_intencao_regex from ranking", con) if con.execute(
        "select 1 from sqlite_master where name='ranking' and sql like '%pct_intencao_regex%'").fetchone() else None
    if old is not None:
        df = df.merge(old, on="video_id", how="left")
    df.to_sql("ranking", con, if_exists="replace", index=False)
    tam = df[df.grupo.notna()].groupby(["porte", "grupo"]).size().unstack(fill_value=0)
    print(f"{len(df)} posts ranqueados, {int(df.elegivel.sum())} elegíveis | top {round((1 - q) * 100)}% por porte:\n{tam.to_string()}")
    print(f"sobreposição top × top_er_puro: {int((df.top & df.top_er_puro).sum())} de {int(df.top.sum())}")
    st = modelo_stats(df[df.elegivel])
    print("modelo:", st)
    meta(quantil_top=q, modelo=st, top_por_porte={k: {g: int(n) for g, n in r.items()} for k, r in tam.iterrows()},
         er_mediano={k: round(float(x), 4) for k, x in df.groupby("porte").er.median().items()},
         sobreposicao_er_puro=int((df.top & df.top_er_puro).sum()))


# ---------- mídia ----------

def baixa(t):
    url, f, max_mb = t
    if os.path.exists(f):
        return True
    try:
        with httpx.stream("GET", url, timeout=120, follow_redirects=True) as r:
            r.raise_for_status()
            if int(r.headers.get("content-length") or 0) > max_mb * 1e6:
                return False
            dado = r.read()
        open(f, "wb").write(dado)
        return True
    except httpx.HTTPError:
        return False


def midia(_):
    """Capa de todos; até 5 imagens dos carrosséis e mp4 (até 50 MB) do top, do controle e de quem está no quartil
    de cima do resíduo (folga para trocar o corte de 10% para 15% sem perder a mídia, que expira)."""
    df = P.ler_ranking(db())
    cand = df.grupo.notna() | (df.resid >= df.groupby("porte").resid.transform(lambda x: x.quantile(0.75)))
    os.makedirs(MIDIA, exist_ok=True)
    tarefas = []
    for r, c in zip(df.itertuples(), cand):
        imgs = [u for u in str(r.imagens or "").split(",") if u.startswith("http")] or [r.thumbnail]
        tarefas += [(u, f"{MIDIA}/{r.video_id}_{i}.jpg", 20) for i, u in enumerate(imgs[:5 if c else 1]) if u]
        if c and isinstance(r.video_url, str) and r.video_url:
            tarefas.append((r.video_url, f"{MIDIA}/{r.video_id}.mp4", 50))
    with ThreadPoolExecutor(8) as ex:
        ok = list(ex.map(baixa, tarefas))
    print(f"mídia: {sum(ok)}/{len(ok)} arquivos em {MIDIA} ({int(cand.sum())} candidatos de {len(df)} posts)")
    os.makedirs("static/midia", exist_ok=True)
    n = 0
    for vid in df[df.grupo.notna()].video_id:  # capas do top e do controle para a interface
        if os.path.exists(f"{MIDIA}/{vid}_0.jpg"):
            shutil.copyfile(f"{MIDIA}/{vid}_0.jpg", f"static/midia/{vid}_0.jpg")
            n += 1
    print(f"{n} capas copiadas para static/midia")


# ---------- 5. rubrica B ----------

FORMATOS_B = Literal["bastidor de produção", "produto em destaque", "antes/depois", "cliente real/depoimento", "oferta/promoção",
                     "tutorial/dica", "humor/trend", "institucional/aviso", "pessoal fora do tema"]


class RubricaB(BaseModel):
    relevante_b: bool  # é o negócio falando com o cliente final dele
    formato: FORMATOS_B
    mostra_produto: bool
    mostra_preco: bool
    mostra_processo: bool
    rosto_do_dono: bool
    cliente_aparece: bool
    gancho_3s: str
    tipo_gancho: Literal["produto na tela", "pergunta", "promessa/resultado", "curiosidade", "humor", "oferta", "emoção/história", "nenhum"]
    tem_oferta_ou_prazo: bool
    gatilho_sazonal: bool
    tipo_cta: Literal["comentar", "direct/WhatsApp", "link", "visitar loja", "encomendar", "nenhum"]
    convida_a_responder: bool
    prova_social: bool
    texto_na_tela: bool
    tom: Literal["próximo/informal", "divertido", "profissional", "emocional", "promocional"]
    qualidade_producao_0a10: int
    apetite_ou_desejo_0a10: int
    elementos_top5: list[str]


PROMPT_B = """Você analisa posts do Instagram de micro e pequenos negócios brasileiros (padaria, salão, loja de bairro, pet shop...) falando com o CLIENTE FINAL deles.
Preencha a rubrica em JSON com base no que você vê e ouve no vídeo (ou nas imagens) e na legenda.
- relevante_b: true se é o negócio falando com quem compra dele (produto, serviço, bastidor, oferta, aviso). false se é post pessoal sem relação com o negócio, repost alheio, ou conteúdo para outros empreendedores.
- formato: o que melhor descreve o post. bastidor de produção = mostra o fazer (massa, corte, costura, embalagem); produto em destaque = o produto/serviço pronto é o centro; antes/depois = transformação; cliente real/depoimento = cliente aparece ou fala; oferta/promoção = preço, desconto, sorteio, combo; tutorial/dica = ensina o cliente; humor/trend = meme, áudio em alta, esquete; institucional/aviso = horário, endereço, data comemorativa, recado; pessoal fora do tema.
- mostra_produto: o produto ou o resultado do serviço aparece com clareza. mostra_preco: preço visível na imagem, falado ou na legenda. mostra_processo: mostra como é feito.
- rosto_do_dono: o dono ou alguém da equipe aparece de rosto. cliente_aparece: um cliente real aparece.
- gancho_3s: o que é dito ou mostrado nos primeiros 3 segundos (ou o texto/elemento principal da primeira imagem), em até 15 palavras.
- tem_oferta_ou_prazo: promoção, desconto, sorteio, "últimas unidades", "só até sábado", encomendas até tal dia.
- gatilho_sazonal: usa data ou época (Natal, Black Friday, Dia das Mães, Páscoa, inverno, volta às aulas).
- tipo_cta: o pedido principal ao cliente; "nenhum" se não pede nada.
- convida_a_responder: faz pergunta ou pede opinião/marcação nos comentários (além de só pedir like).
- prova_social: mostra clientes satisfeitos, fila, avaliações, quantidade vendida, depoimento.
- texto_na_tela: há texto sobreposto relevante.
- notas 0a10 (seja conservador): qualidade_producao = imagem, luz, som, edição; apetite_ou_desejo = o quanto dá vontade de comer/usar/comprar.
- elementos_top5: os 5 elementos que mais explicam a atenção que o post gera, frases curtas.
Post de @{canal} ({segmento}, {seguidores} seguidores), tipo {tipo}.
Legenda: {legenda}"""


def conteudo_b(r, so_imagem=False):
    texto = {"type": "text", "text": PROMPT_B.format(canal=r.channel_id, segmento=r.segmento, seguidores=r.inscritos,
                                                     tipo=r.tipo, legenda=(r.descricao or "")[:1500])}
    mp4 = f"{MIDIA}/{r.video_id}.mp4"
    if os.path.exists(mp4) and not so_imagem:
        return [{"type": "video_url", "video_url": {"url": P.b64(mp4, "video/mp4")}}, texto], "video"
    imgs = sorted(glob.glob(f"{MIDIA}/{r.video_id}_*.jpg"))[:5]
    if not imgs:
        raise FileNotFoundError(f"sem mídia para {r.video_id}")
    return [{"type": "image_url", "image_url": {"url": P.b64(f, "image/jpeg")}} for f in imgs] + [texto], "imagens"


_esgotados = set()  # modelos Gemini com a cota DIÁRIA esgotada nesta chave


def categoriza_b(r):
    """Gemini vê o vídeo. 503 (pico) ou 429 por minuto: espera e tenta de novo. 429 da cota diária: próximo modelo.
    Sem nenhum modelo Gemini: DeepSeek nas imagens + legenda (fonte capa_deepseek)."""
    conteudo, fonte = conteudo_b(r)
    for m in [P.LLM_MODEL] + P.FALLBACK_MODELS[:1]:
        for t in range(6):
            if m in _esgotados:
                break
            try:
                return P.llm_google(conteudo, RubricaB, m, tentativas=1), fonte
            except Exception as e:
                s = str(e)
                if "429" in s and "per day" in s.lower():
                    _esgotados.add(m)
                    print(f"  cota diária de {m} esgotada", flush=True)
                elif ("429" in s or "503" in s or "500" in s) and t < 5:
                    time.sleep(40)
                elif "503" in s or "429" in s:
                    break  # modelo fora do ar há 4 min: tenta o próximo
                else:
                    raise
    raise RuntimeError("sem Gemini disponível (cota diária ou 503)")


def categoriza_capa(r):
    conteudo, _ = conteudo_b(r, so_imagem=True)
    return P.llm(conteudo, RubricaB, model=DEEPSEEK), "capa_deepseek"


def categoriza_quadros(r):
    """Reel com mp4 local: DeepSeek vê os 12 quadros (6 no gancho) + a transcrição do áudio (data/transcricoes.json)."""
    import avaliar as A  # avaliar importa este módulo
    import transcrever as T
    mp4 = f"{MIDIA}/{r.video_id}.mp4"
    if not os.path.exists(mp4):
        return categoriza_capa(r)
    qs, dur = A.quadros(open(mp4, "rb").read())
    segs = T.cache().get(r.video_id)
    if segs is None:
        segs = T.segmentos(mp4)
    texto = conteudo_b(r, so_imagem=True)[0][-1]["text"] + (
        f"\nO vídeo tem {dur:.0f} s; seguem {len(qs)} quadros em ordem, os marcados (gancho) são dos 3 primeiros segundos.\n"
        + T.para_prompt(segs))
    imgs = [x for t, q in qs for x in ({"type": "text", "text": f"Quadro em {t:.1f} s" + (" (gancho)" if t <= 3 else "")},
                                       {"type": "image_url", "image_url": {"url": A.data_url(q)}})]
    return P.llm(imgs + [{"type": "text", "text": texto}], RubricaB, model=DEEPSEEK), "quadros_audio_deepseek"


def categorizar(a):
    """metodo capa (padrão): DeepSeek vê até 5 imagens + legenda de TODO o top e controle -> tabela categorias (método
    único nos dois grupos, é o que entra no lift). metodo video: Gemini vê o vídeo -> categorias_video (só o que a cota
    diária de 20 chamadas por modelo cobre; serve para medir a concordância entre os métodos e para os ganchos)."""
    con = db()
    tab, fn = {"video": ("categorias_video", categoriza_b), "quadros": ("categorias", categoriza_quadros)}.get(
        a.metodo, ("categorias", categoriza_capa))
    con.execute(f"create table if not exists {tab} (video_id text primary key, grupo text, fonte text, rubrica text, criado_em text)")
    df = P.ler_ranking(con)
    feitos = set(pd.read_sql(f"select video_id from {tab}", con).video_id)
    if a.metodo == "quadros":  # refaz os Reels com mp4 local que ainda não têm a leitura com quadros + áudio
        feitos = set(pd.read_sql(f"select video_id from {tab} where fonte = 'quadros_audio_deepseek'", con).video_id)
        df = df[[os.path.exists(f"{MIDIA}/{v}.mp4") for v in df.video_id]]
    alvo = df[df.grupo.notna() & ~df.video_id.isin(feitos)]
    alvo = alvo.assign(o=alvo.groupby("grupo").cumcount()).sort_values(["grupo", "o"] if a.metodo == "video" else ["o", "grupo"]).head(a.limite)
    print(f"{len(feitos)} já categorizados em {tab}, {len(alvo)} nesta rodada")
    with ThreadPoolExecutor(a.paralelo) as ex:
        futs = {ex.submit(fn, r): r for r in alvo.itertuples()}
        for i, f in enumerate(as_completed(futs), 1):
            r = futs[f]
            try:
                rub, fonte = f.result()
            except Exception as e:
                print(f"[{i}/{len(alvo)}] ERRO {r.video_id}: {str(e)[:120]}", flush=True)
                continue
            con.execute(f"insert or replace into {tab} values (?,?,?,?,?)",
                        (r.video_id, r.grupo, fonte, json.dumps(rub.model_dump(), ensure_ascii=False), datetime.now().isoformat()))
            con.commit()
            print(f"[{i}/{len(alvo)}] {r.grupo} {fonte} {rub.formato} relevante={rub.relevante_b}", flush=True)
    print(pd.read_sql(f"select grupo, fonte, count(*) n from {tab} group by 1, 2", con).to_string())


# ---------- 6. intenção de compra ----------

INTENCAO = re.compile(
    r"\b(quanto|valor(es)?|pre[çc]os?|entrega[ms]?|onde|quero|encomend\w+|pix|card[aá]pio|endere[çc]o|frete|or[çc]amento|"
    r"agend\w+|hor[aá]rios?|vende[ms]?|envia[ms]?|whats\w*|zap|como (fa[çc]o|compr\w+|pe[çd]\w+)|"
    r"tem (no|na|em|para|pra|tamanho|dispon\w+|como|loja|entrega))\b", re.I)


class Intencoes(BaseModel):
    intencao: list[bool]  # um por comentário, na ordem


def comentarios(_):
    """Comentários que vieram junto dos posts (até ~12 por post, custo zero). Regex em todos; DeepSeek no top e controle."""
    con = db()
    v = pd.read_sql("select video_id, channel_id, comentarios_txt from videos", con)
    rows = [dict(video_id=r.video_id, autor=c["u"], texto=c["t"]) for r in v.itertuples()
            for c in json.loads(r.comentarios_txt or "[]") if c["t"].strip() and c["u"] != r.channel_id]  # sem respostas do dono
    c = pd.DataFrame(rows)
    c["regex"] = c.texto.map(lambda t: bool(INTENCAO.search(t)))
    rk = P.ler_ranking(con)
    alvo = c[c.video_id.isin(rk[rk.grupo.notna()].video_id)]
    lotes = [alvo.iloc[i:i + 40] for i in range(0, len(alvo), 40)]

    def um(lote):
        txt = "\n".join(f"{i + 1}. {t[:200]}" for i, t in enumerate(lote.texto.str.replace("\n", " ")))
        r = P.llm("Comentários em posts do Instagram de pequenos negócios brasileiros. Para cada um, diga se mostra "
                  "INTENÇÃO DE COMPRA: pergunta preço, valor, entrega, endereço, horário, disponibilidade, como encomendar "
                  "ou agendar, ou diz que quer/vai comprar. Elogio, emoji, marcação de amigo sem pedido = false. "
                  f"Devolva exatamente {len(lote)} valores, na ordem.\n" + txt, Intencoes, model=DEEPSEEK).intencao
        if len(r) != len(lote):
            raise ValueError("tamanho diferente")
        return r
    c["intencao"] = None
    for lote, r in em_paralelo(um, lotes, 4):
        c.loc[lote.index, "intencao"] = r
    c.to_sql("comentarios", con, if_exists="replace", index=False)
    cl = c[c.intencao.notna()]
    pct = cl.assign(i=cl.intencao.astype(bool)).groupby("video_id").i.mean().rename("pct_intencao")
    rk = rk.drop(columns=[x for x in ("pct_intencao", "pct_intencao_regex") if x in rk]).merge(pct, on="video_id", how="left").merge(
        c.groupby("video_id").regex.mean().rename("pct_intencao_regex"), on="video_id", how="left")
    rk.to_sql("ranking", con, if_exists="replace", index=False)
    conc = (cl.regex == cl.intencao.astype(bool)).mean() if len(cl) else float("nan")
    print(f"{len(c)} comentários de clientes em {c.video_id.nunique()} posts; {len(cl)} classificados pelo DeepSeek "
          f"({cl.video_id.nunique()} posts do top/controle); concordância regex × LLM {conc:.2f}, "
          f"kappa {P.kappa(cl.regex.astype(str), cl.intencao.astype(bool).astype(str)) if len(cl) else float('nan'):.2f}")
    print(rk[rk.grupo.notna()].groupby("grupo").agg(posts_com_comentario=("pct_intencao", "count"),
                                                    pct_intencao=("pct_intencao", "mean")).round(3).to_string())


# ---------- 7. análise ----------

CAMPOS_B = ["formato", "tipo_gancho", "tipo_cta", "tom", "mostra_produto", "mostra_preco", "mostra_processo", "rosto_do_dono",
            "cliente_aparece", "tem_oferta_ou_prazo", "gatilho_sazonal", "convida_a_responder", "prova_social", "texto_na_tela",
            "tipo_post", "duracao_faixa", "legenda_tamanho", "producao_alta", "desejo_alto", "segmento"]
NOTAS_B = ["qualidade_producao_0a10", "apetite_ou_desejo_0a10"]


def carregar_b(con):
    df = P.ler_ranking(con, "select r.*, c.fonte, c.rubrica from ranking r join categorias c using(video_id)")
    rub = pd.json_normalize(df.rubrica.map(json.loads))
    df = pd.concat([df.drop(columns="rubrica").reset_index(drop=True), rub], axis=1)
    df["tipo_post"] = df.tipo.map(P.TIPO_POST).fillna(df.tipo)
    df["duracao_faixa"] = pd.cut(df.duracao_s, [0, 15, 30, 60, 10**5],
                                 labels=["<15s", "15-30s", "30-60s", ">60s"]).astype(str).replace("nan", "sem vídeo")
    df["legenda_tamanho"] = pd.cut(df.descricao.str.len(), [-1, 100, 500, 10**6], labels=["curta", "media", "longa"]).astype(str)
    df["producao_alta"] = df.qualidade_producao_0a10 >= 7
    df["desejo_alto"] = df.apetite_ou_desejo_0a10 >= 7
    return df


def analisar(_):
    con = db()
    tudo = carregar_b(con)
    df = tudo[(tudo.relevante_b == True) & tudo.grupo.notna()]  # noqa: E712
    print(f"categorizados: {len(tudo)} | relevante_b: {len(df)} (top {int((df.grupo == 'top').sum())}, "
          f"controle {int((df.grupo == 'controle').sum())}) | fora do tema: {len(tudo) - len(df)}")
    lt = P.lift_table(df, CAMPOS_B).query("plataforma == 'instagram'").sort_values(["campo", "freq_top"], ascending=[True, False])
    lt.to_csv(f"{DATA}/b_achados.csv", index=False)
    pd.set_option("display.width", 200)
    print(lt.to_string(index=False))
    if con.execute("select 1 from sqlite_master where name='categorias_video'").fetchone():
        vid = pd.read_sql("select video_id, rubrica from categorias_video", con)
        m = pd.concat([vid[["video_id"]], pd.json_normalize(vid.rubrica.map(json.loads))], axis=1).merge(tudo, on="video_id", suffixes=("_v", "_c"))
        cmp = pd.DataFrame([dict(campo=c, n=len(m), concordancia=round((m[c + "_v"].astype(str) == m[c + "_c"].astype(str)).mean(), 2),
                                 kappa=round(P.kappa(m[c + "_v"], m[c + "_c"]), 2))
                            for c in RubricaB.model_fields if c + "_v" in m and c not in ("gancho_3s", "elementos_top5")
                            and not c.endswith("0a10")]).sort_values("kappa")
        cmp.to_csv(f"{DATA}/b_comparacao_metodos.csv", index=False)
        print(f"\nGemini (vídeo) × DeepSeek (imagens) nos mesmos {len(m)} posts:\n", cmp.to_string(index=False))
    notas = df.groupby("grupo")[NOTAS_B].agg(["median", "mean"]).round(2)
    print("\nnotas:\n", notas.to_string())
    # perfis em destaque: efeito do criador no modelo misto
    rk = P.ler_ranking(con)
    el = rk[rk.elegivel]
    p = el.groupby(["plataforma", "canal", "channel_id", "porte", "inscritos", "segmento"]).agg(
        efeito_criador=("efeito_criador", "first"), n_top=("top", "sum"), n_posts=("video_id", "size"),
        er_mediano=("er", "median")).reset_index()
    fmt = tudo[tudo.relevante_b == True].groupby("channel_id").formato.agg(lambda s: s.mode().iat[0]).rename("formato")  # noqa: E712
    p = p.merge(fmt, on="channel_id", how="left").sort_values("efeito_criador", ascending=False)
    p[["plataforma", "canal", "porte", "inscritos", "efeito_criador", "n_top", "n_posts", "segmento", "formato",
       "channel_id", "er_mediano"]].to_csv(f"{DATA}/b_perfis_destaque.csv", index=False)
    print("\nperfis:\n", p.drop(columns="plataforma").round(3).to_string(index=False))
    seg = rk.groupby("segmento").agg(perfis=("channel_id", "nunique"), posts=("video_id", "size"), er_mediano=("er", "median"),
                                     conversa_mediana=("conversa", "median"), top=("top", "sum")).round(4)
    print("\nsegmento:\n", seg.to_string())
    tp = rk.assign(tipo_post=rk.tipo.map(P.TIPO_POST).fillna(rk.tipo)).groupby("tipo_post").agg(
        posts=("video_id", "size"), er_mediano=("er", "median"), resid_medio=("resid", "mean"), top=("top", "sum")).round(4)
    print("\ntipo de post (base toda):\n", tp.to_string())
    extra = {}
    if "pct_intencao" in df:
        d = df[df.pct_intencao.notna()]
        g = d.groupby("grupo").pct_intencao.agg(["size", "mean"]).round(3)
        print("\nintenção de compra (posts com comentário de cliente):\n", g.to_string())
        campos = ["mostra_preco", "tem_oferta_ou_prazo", "mostra_produto", "convida_a_responder", "desejo_alto", "formato"]
        cruz = {c: d.groupby(c).pct_intencao.agg(["size", "mean"]).round(3) for c in campos}
        for c, t in cruz.items():
            print(f"\npct_intencao por {c}:\n", t.to_string())
        extra = dict(intencao={k: dict(n=int(r["size"]), pct=float(r["mean"])) for k, r in g.iterrows()},
                     intencao_regex_base_toda=round(float(rk.pct_intencao_regex.mean()), 3),
                     posts_com_comentario=int(rk.pct_intencao_regex.notna().sum()))
    meta(categorizados=tudo.groupby(["grupo", "fonte"]).size().rename("n").reset_index().to_dict("records"),
         relevantes=dict(top=int((df.grupo == "top").sum()), controle=int((df.grupo == "controle").sum())), **extra)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("etapa", choices=["descobrir", "triar", "coletar", "rank", "midia", "categorizar", "comentarios", "analisar"])
    ap.add_argument("--por-hashtag", type=int, default=25)
    ap.add_argument("--rodada", type=int, default=1)
    ap.add_argument("--limite", type=int, default=60, help="perfis por rodada (triar) ou posts (categorizar)")
    ap.add_argument("--por-perfil", type=int, default=35)
    ap.add_argument("--q", type=float, default=None, help="quantil do top (ex.: 0.85 = top 15%%)")
    ap.add_argument("--paralelo", type=int, default=2)
    ap.add_argument("--metodo", choices=["capa", "video", "quadros"], default="capa")
    a = ap.parse_args()
    globals()[a.etapa](a)
