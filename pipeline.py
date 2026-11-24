"""Pipeline do case Stone: conteúdo de alto engajamento para MPEs (YouTube Shorts).

Etapas, nesta ordem:
  python pipeline.py check        # testa as chaves de API
  python pipeline.py discover     # acha canais candidatos -> data/canais.csv (revise a coluna "incluir")
  python pipeline.py collect      # coleta os Shorts dos canais incluídos
  python pipeline.py rank         # engajamento normalizado + outlier score + top 10%
  python pipeline.py categorize   # rubrica via Gemini (top 10% + amostra de controle do mesmo tamanho)
  python pipeline.py analyze      # frequência, lift e perfis em destaque -> data/*.csv
  python pipeline.py validate --gerar   # amostra de 50 para categorizar à mão
  python pipeline.py validate           # concordância e kappa por campo
"""
import argparse
import json
import os
import re
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from typing import Literal

import httpx
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()
DATA = os.getenv("DATA_DIR", "data")
DB = f"{DATA}/stone.db"
YT = "https://www.googleapis.com/youtube/v3"
FEITA_URL = "https://api.feita.ai/gateway/v1"
# Google direto (chave do AI Studio); modelos com "/" vão pela Feita (gateway OpenAI)
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.6-flash")  # 3.7/3.8 em "high demand" (503) em 23/11; 207 posts já com 3.7
FALLBACK_MODELS = ["gemini-3.7-flash", "gemini-3.5-flash"]

KEYWORDS = [
    "dicas para pequenos negócios", "MEI dicas", "como vender mais loja", "marketing para pequenos negócios",
    "empreendedorismo pequeno negócio", "educação financeira empreendedor", "maquininha de cartão",
    "dicas para lojista", "como precificar produto", "atendimento ao cliente pequeno negócio",
]
MIN_IDADE_DIAS = 14     # métricas estabilizadas (TAPI)
JANELA_DIAS = 365       # últimos 12 meses
MAX_DURACAO_S = 180     # ponytail: a API não marca Shorts; Short = vídeo de até 3 min
MAX_VIDEOS_CANAL = 200
YT_AMOSTRA = 60         # posts do YouTube categorizados por grupo x porte (top/controle x micro/medio/grande)  # 4 páginas de playlist por canal


# ---------- infraestrutura ----------

def db():
    os.makedirs(DATA, exist_ok=True)
    return sqlite3.connect(DB)


def yt(endpoint, **params):
    params["key"] = os.environ["YOUTUBE_API_KEY"]
    for t in range(5):
        r = httpx.get(f"{YT}/{endpoint}", params=params, timeout=30)
        if r.status_code in (429, 500, 503):
            time.sleep(2 ** t)
            continue
        r.raise_for_status()
        return r.json()
    r.raise_for_status()


_client = None


_google = None


def partes_google(content):
    """Converte partes no formato OpenAI (texto, image_url, video_url) para o SDK do Google."""
    import base64
    from google.genai import types
    if isinstance(content, str):
        return [content]
    out = []
    for p in content:
        if p["type"] == "text":
            out.append(p["text"])
            continue
        url = p[p["type"]]["url"]
        if "youtube.com" in url:
            out.append(types.Part(file_data=types.FileData(file_uri=url)))
            continue
        if url.startswith("data:"):
            mime, dado = url[5:].split(";base64,")
            dado = base64.b64decode(dado)
        else:
            r = httpx.get(url, timeout=60, follow_redirects=True)
            r.raise_for_status()
            mime, dado = r.headers.get("content-type", "image/jpeg").split(";")[0], r.content
        if len(dado) > 18_000_000:  # limite inline ~20 MB: sobe pela Files API
            import io
            f = _google.files.upload(file=io.BytesIO(dado), config={"mime_type": mime})
            while f.state.name == "PROCESSING":
                time.sleep(3)
                f = _google.files.get(name=f.name)
            out.append(types.Part(file_data=types.FileData(file_uri=f.uri, mime_type=mime)))
        else:
            out.append(types.Part.from_bytes(data=dado, mime_type=mime))
    return out


GEMINI_KEYS = [k for k in (os.getenv("GEMINI_API_KEY"), os.getenv("GEMINI_API_KEY_2"), os.getenv("GEMINI_API_KEY_3")) if k]
_chave = 0  # índice da chave em uso; avança quando a cota diária da atual acaba


def llm_google(content, schema, model, tentativas=3):
    global _google
    from google import genai
    from google.genai import errors, types
    _google = _google or genai.Client(api_key=GEMINI_KEYS[_chave])  # GEMINI_API_KEY (e _2) do .env
    cfg = types.GenerateContentConfig(response_mime_type="application/json", response_schema=schema, temperature=0,
                                      media_resolution=types.MediaResolution.MEDIA_RESOLUTION_LOW)
    partes = partes_google(content)
    for t in range(tentativas):
        try:
            r = _google.models.generate_content(model=model, contents=partes, config=cfg)
            if r.parsed is None:
                raise ValueError(f"resposta fora do schema: {(r.text or '')[:200]}")
            return r.parsed
        except errors.APIError as e:
            if e.code in (429, 500, 503) and t < tentativas - 1:
                time.sleep(min(60, 5 * 2 ** t))
                continue
            raise


def llm(content, schema, model=None, tentativas=5):
    """Modelo "gemini-*": Google direto. Modelo "x/y": Feita.ai (gateway OpenAI). Saída validada pelo schema."""
    if model is None or "/" not in model:
        global _google, _chave
        modelos = [model] if model else [LLM_MODEL] + FALLBACK_MODELS
        while True:
            try:
                for i, m in enumerate(modelos):
                    try:
                        return llm_google(content, schema, m)
                    except Exception as e:
                        if i == len(modelos) - 1:
                            raise
                        print(f"  {m} falhou ({str(e)[:60]}), tentando {modelos[i + 1]}")
            except Exception as e:
                # cota diária de todos os modelos esgotada nesta chave -> próxima chave (arquivos são reenviados)
                if "429" in str(e) and _chave + 1 < len(GEMINI_KEYS):
                    _chave, _google = _chave + 1, None
                    print(f"  cota esgotada; trocando para a chave {_chave + 1} de {len(GEMINI_KEYS)}")
                    continue
                raise
    global _client
    from openai import OpenAI
    _client = _client or OpenAI(base_url=FEITA_URL, api_key=os.environ["FEITA_API_KEY"], max_retries=tentativas)
    from openai import APIStatusError
    modelos = [model]
    from pydantic import ValidationError
    for i, m in enumerate(modelos):
        try:
            for t in range(3):
                r = _client.chat.completions.create(
                    model=m, temperature=0, max_tokens=16000,  # raciocínio + JSON dividem o limite
                    messages=[{"role": "user", "content": content}],
                    response_format={"type": "json_schema",
                                     "json_schema": {"name": schema.__name__, "schema": schema.model_json_schema()}},
                    extra_body={"reasoning": {"effort": "low"}},
                )
                try:
                    return valida_json(r.choices[0].message.content, schema)
                except (ValidationError, ValueError):
                    # o DeepSeek às vezes devolve o próprio schema em vez da resposta (~3% das chamadas): repete
                    if t == 2:
                        raise
        except APIStatusError as e:
            if e.status_code != 503 or i == len(modelos) - 1:  # 503 = modelo fora do ar na Feita
                raise


def valida_json(txt, schema):
    """Valida a saída do modelo; aceita a resposta embrulhada em {"properties": {...}} (eco do formato do schema)."""
    d = json.loads(txt)
    if isinstance(d, dict) and isinstance(d.get("properties"), dict) and not set(schema.model_fields) & set(d):
        d = d["properties"]
    return schema.model_validate(d)


def duracao_s(iso):
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def porte(subs):
    return "micro" if subs < 10_000 else "medio" if subs < 100_000 else "grande"  # faixas da aula 1


# ---------- check ----------

def check(_):
    r = yt("search", part="id", q="sebrae", type="channel", maxResults=1)
    print("YouTube OK:", r["items"][0]["id"]["channelId"])
    from apify_client import ApifyClient
    print("Apify OK:", ApifyClient(os.environ["APIFY_TOKEN"]).user().get().username)

    class Ok(BaseModel):
        ok: bool
    print("Feita OK:", llm('Responda {"ok": true}', Ok).ok, "| modelo:", LLM_MODEL)


# ---------- discover ----------

def ler_manuais():
    if not os.path.exists("canais_manuais.txt"):
        return []
    ids = []
    for linha in open("canais_manuais.txt", encoding="utf-8"):
        h = linha.split("#")[0].strip()
        if not h:
            continue
        if h.startswith("UC"):
            ids.append(h)
            continue
        items = yt("channels", part="id", forHandle=h).get("items", [])
        if items:
            ids.append(items[0]["id"])
        else:
            print("handle não encontrado:", h)
    return ids


def canais_info(ids):
    out = []
    for i in range(0, len(ids), 50):
        out += yt("channels", part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50])).get("items", [])
    return out


def discover(_):
    hits = {}
    desde = (datetime.now(timezone.utc) - timedelta(days=JANELA_DIAS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    for kw in KEYWORDS:  # 100 unidades de cota cada
        r = yt("search", part="snippet", q=kw, type="video", videoDuration="short", regionCode="BR",
               relevanceLanguage="pt", publishedAfter=desde, maxResults=50)
        for it in r.get("items", []):
            cid = it["snippet"]["channelId"]
            hits[cid] = hits.get(cid, 0) + 1
        print(f"busca '{kw}': {len(r.get('items', []))} vídeos")
    manuais = set(ler_manuais())
    rows = []
    for c in canais_info(list(set(hits) | manuais)):
        s, sn = c["statistics"], c["snippet"]
        subs = int(s.get("subscriberCount", 0))
        rows.append(dict(
            channel_id=c["id"], titulo=sn["title"], handle=sn.get("customUrl", ""), inscritos=subs,
            videos=int(s.get("videoCount", 0)), porte=porte(subs), hits=hits.get(c["id"], 0),
            origem="manual" if c["id"] in manuais else "busca",
            uploads=c["contentDetails"]["relatedPlaylists"]["uploads"],
            descricao=sn.get("description", "")[:200].replace("\n", " "),
        ))
    df = pd.DataFrame(rows)
    df["incluir"] = (((df.inscritos >= 1000) & (df.videos >= 30)) | (df.origem == "manual")).astype(int)
    df.sort_values(["incluir", "hits"], ascending=False).to_csv(f"{DATA}/canais.csv", index=False)
    print(df[df.incluir == 1].groupby("porte").size().to_string())
    print(f"-> revise {DATA}/canais.csv: deixe incluir=1 só em canais voltados a MPE")


class Triagem(BaseModel):
    id: str
    voltado_mpe: bool          # fala com dono de pequeno negócio / MEI / lojista
    tipo_criador: Literal["empreendedor_real", "especialista", "instituicao_ou_marca", "outro"]
    segmento: Literal["gestao_financas", "vendas_marketing", "pagamentos_maquininha", "alimentacao",
                      "beleza", "varejo_moda", "servicos", "geral"]


class Triagens(BaseModel):
    itens: list[Triagem]


TRIAGEM_PROMPT = """Para cada perfil abaixo (id | nome | bio), diga se o conteúdo é voltado a micro e pequenos
empreendedores brasileiros (MEI, lojista, dono de pequeno negócio), quem é o criador e o segmento principal.
Canais de cortes, de outros temas (games, investimentos pessoais, advocacia previdenciária) ou de outros países: voltado_mpe=false.
{linhas}"""


def triagem(a):
    """Classifica perfis (YouTube ou Instagram) por relevância MPE. Arquivo com colunas id, titulo, descricao."""
    df = pd.read_csv(a.arquivo)
    col = "channel_id" if "channel_id" in df else "id"
    alvo = df[df.incluir == 1] if "incluir" in df else df
    res = []
    for i in range(0, len(alvo), 40):
        bloco = alvo.iloc[i:i + 40]
        linhas = "\n".join(f"{r[col]} | {r.titulo} | {str(r.descricao)[:200]}" for _, r in bloco.iterrows())
        res += llm(TRIAGEM_PROMPT.format(linhas=linhas), Triagens, model="anthropic/claude-haiku-5.5").itens
        print(f"triados {min(i + 40, len(alvo))}/{len(alvo)}")
    t = pd.DataFrame([r.model_dump() for r in res]).rename(columns={"id": col}).drop_duplicates(col)
    df = df.drop(columns=[c for c in t.columns if c != col and c in df]).merge(t, on=col, how="left")
    if "incluir" in df:
        df["incluir"] = (((df.incluir == 1) & (df.voltado_mpe == True)) | (df.get("origem") == "manual")).astype(int)  # noqa: E712
    df.to_csv(a.arquivo, index=False)
    ok = df[df.voltado_mpe == True]  # noqa: E712
    print(ok.groupby(["porte", "tipo_criador"]).size().unstack(fill_value=0).to_string())


IG_HASHTAGS = ["dicasparaempreendedores", "pequenosnegocios", "dicasdevendas", "empreendedorismofeminino",
               "mei", "lojista", "educacaofinanceira"]
ACTOR = "apify/instagram-scraper"  # US$ 0,0027 por resultado no plano grátis (US$ 5)


def apify(cache, **inp):
    """Roda o actor da Apify com cache em data/raw/<cache>.json (não paga duas vezes)."""
    f = f"{DATA}/raw/{cache}.json"
    if os.path.exists(f):
        return json.load(open(f))
    from apify_client import ApifyClient
    c = ApifyClient(os.getenv("APIFY_TOKEN_2") or os.environ["APIFY_TOKEN"])  # _2: conta nova, com crédito
    run = c.actor(ACTOR).call(run_input=inp, logger=None)
    itens = list(c.dataset(run.default_dataset_id).iterate_items())
    os.makedirs(f"{DATA}/raw", exist_ok=True)
    json.dump(itens, open(f, "w"), ensure_ascii=False)
    return itens


def ig_linhas(itens, origem):
    return [dict(id=p.get("username"), titulo=p.get("fullName", ""),
                 descricao=(p.get("biography") or "").replace("\n", " "),
                 seguidores=p.get("followersCount") or 0, posts=p.get("postsCount") or 0,
                 porte=porte(p.get("followersCount") or 0), verificado=p.get("verified", False), origem=origem,
                 relacionados=",".join(r.get("username", "") for r in p.get("relatedProfiles") or []))
            for p in itens if p.get("username") and not p.get("private") and not p.get("error")]


def detalhes(cache, usernames):
    return apify(cache, directUrls=[f"https://www.instagram.com/{u}/" for u in usernames], resultsType="details")


def ig_discover(a):
    """Rodada 1: sementes manuais + mesmos @ dos canais MPE do YouTube. Rodada 2 (--expandir): relatedProfiles."""
    out = f"{DATA}/perfis_ig.csv"
    if a.expandir:  # ponytail: relatedProfiles vem vazio sem login; autores de posts em hashtags MPE
        df = pd.read_csv(out)
        posts = apify("hashtags", resultsType="posts", resultsLimit=a.por_hashtag,
                      directUrls=[f"https://www.instagram.com/explore/tags/{h}/" for h in IG_HASHTAGS])
        autores = pd.Series([p.get("ownerUsername") for p in posts]).value_counts()
        novos = [u for u in autores.index if u and u not in set(df.id)][:a.limite]
        df = pd.concat([df, pd.DataFrame(ig_linhas(detalhes("autores_hashtag", novos), "hashtag"))])
    else:
        manuais = [l.split("#")[0].strip() for l in open("perfis_ig_manuais.txt", encoding="utf-8")]
        yt = pd.read_csv(f"{DATA}/canais.csv")
        yt = yt[(yt.voltado_mpe == True) & (yt.tipo_criador != "instituicao_ou_marca")]  # noqa: E712
        handles = [h.lstrip("@").lower() for h in yt.sort_values("inscritos", ascending=False).handle.dropna()][:a.limite]
        df = pd.DataFrame(ig_linhas(detalhes("manuais", [m for m in manuais if m]), "manual")
                          + ig_linhas(detalhes("handles_youtube", handles), "handle_youtube"))
    df = df.drop_duplicates("id")
    df["incluir"] = (((df.seguidores >= 1000) & (df.posts >= 30)) | (df.origem == "manual")).astype(int)
    df.sort_values(["incluir", "seguidores"], ascending=False).to_csv(out, index=False)
    print(df.groupby(["origem", "incluir"]).size().to_string())
    print(f"-> rode: pipeline.py triagem {out}")


# ---------- collect ----------

def ids_da_playlist(playlist):
    ids, token = [], None
    while len(ids) < MAX_VIDEOS_CANAL:
        extra = {"pageToken": token} if token else {}
        r = yt("playlistItems", part="contentDetails", playlistId=playlist, maxResults=50, **extra)
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        token = r.get("nextPageToken")
        if not token:
            break
    return ids


def linha_video(v, cid, agora):
    s, sn = v.get("statistics", {}), v["snippet"]
    pub = datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00"))
    num = lambda k: int(s[k]) if k in s else None  # noqa: E731
    return dict(
        video_id=v["id"], channel_id=cid, titulo=sn["title"], descricao=sn.get("description", ""),
        tags="|".join(sn.get("tags", [])), publicado=pub.isoformat(), idade_dias=(agora - pub).days,
        duracao_s=duracao_s(v["contentDetails"]["duration"]), views=num("viewCount"), likes=num("likeCount"),
        comentarios=num("commentCount"),
        thumbnail=max(sn["thumbnails"].values(), key=lambda t: t.get("width", 0))["url"],
        coletado_em=agora.isoformat(),
    )


def collect(_):
    canais = pd.read_csv(f"{DATA}/canais.csv")
    canais = canais[canais.incluir == 1]
    agora = datetime.now(timezone.utc)
    rows = []
    for c in canais.itertuples():
        # ponytail: "UUSH..." é a playlist só de Shorts do canal (não documentada); cai para uploads se falhar
        try:
            ids = ids_da_playlist("UUSH" + c.uploads[2:])
        except httpx.HTTPStatusError:
            ids = []
        if not ids:
            try:
                ids = ids_da_playlist(c.uploads)
            except httpx.HTTPStatusError as e:
                print(f"{c.titulo}: erro {e.response.status_code}, pulando")
                continue
        for i in range(0, len(ids), 50):
            for v in yt("videos", part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50])).get("items", []):
                rows.append(linha_video(v, c.channel_id, agora))
        print(f"{c.titulo}: {len(ids)} vídeos lidos")
    df = pd.DataFrame(rows)
    total = len(df)
    df = df[(df.duracao_s.between(1, MAX_DURACAO_S)) & (df.idade_dias.between(MIN_IDADE_DIAS, JANELA_DIAS))]
    con = db()
    df["plataforma"] = "youtube"
    canais = canais.assign(plataforma="youtube")
    # ponytail: collect substitui o YouTube e preserva o Instagram já coletado
    for tab, novo in [("videos", df), ("canais", canais)]:
        try:
            velho = pd.read_sql(f"select * from {tab} where plataforma != 'youtube'", con)
        except Exception:
            velho = pd.DataFrame()
        pd.concat([novo, velho]).to_sql(tab, con, if_exists="replace", index=False)
    print(f"{total} lidos -> {len(df)} Shorts entre {MIN_IDADE_DIAS} e {JANELA_DIAS} dias, "
          f"{df.channel_id.nunique()} canais. Coletado em {agora:%Y-%m-%d %H:%M} UTC")


def ig_collect(a):
    """Posts dos perfis IG incluídos -> mesmas tabelas do YouTube (plataforma=instagram)."""
    perfis = pd.read_csv(f"{DATA}/perfis_ig.csv")
    perfis = perfis[perfis.incluir == 1]
    itens = apify("posts", directUrls=[f"https://www.instagram.com/{u}/" for u in perfis.id],
                  resultsType="posts", resultsLimit=a.por_perfil, onlyPostsNewerThan=f"{JANELA_DIAS} days")
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
            plataforma="instagram", tipo=p.get("productType") or p.get("type"),  # clips = Reel
            fixado=bool(p.get("isPinned")), video_url=p.get("videoUrl"),
            imagens=",".join(c.get("displayUrl", "") for c in p.get("childPosts") or []),
        ))
    df = pd.DataFrame(rows).drop_duplicates("video_id")
    total = len(df)
    df = df[df.channel_id.isin(perfis.id)]  # collabs trazem outro dono, sem seguidores conhecidos
    df = df[df.idade_dias.between(MIN_IDADE_DIAS, JANELA_DIAS) & ~df.fixado]
    canais = pd.DataFrame(dict(channel_id=perfis.id, titulo=perfis.titulo, handle=perfis.id, inscritos=perfis.seguidores,
                               porte=perfis.porte, origem=perfis.origem, descricao=perfis.descricao, incluir=1,
                               voltado_mpe=perfis.voltado_mpe, tipo_criador=perfis.tipo_criador,
                               segmento=perfis.segmento, plataforma="instagram"))
    con = db()
    for tab, novo in [("videos", df), ("canais", canais)]:
        velho = pd.read_sql(f"select * from {tab} where plataforma != 'instagram'", con)
        pd.concat([velho, novo]).to_sql(tab, con, if_exists="replace", index=False)
    print(f"{total} posts -> {len(df)} entre {MIN_IDADE_DIAS} e {JANELA_DIAS} dias (sem fixados), "
          f"{df.channel_id.nunique()} perfis | tipos: {df.tipo.value_counts().to_dict()}")


def ig_midia(_):
    """Baixa mp4 dos Reels e imagens dos carrosséis do top+controle (URLs da Apify expiram em ~dias)."""
    from concurrent.futures import ThreadPoolExecutor
    df = ler_ranking(db())
    df = df[(df.plataforma == "instagram") & df.grupo.notna()]
    os.makedirs(f"{DATA}/midia", exist_ok=True)
    tarefas = []
    for r in df.itertuples():
        if isinstance(r.video_url, str) and r.video_url:
            tarefas.append((r.video_url, f"{DATA}/midia/{r.video_id}.mp4"))
        imgs = [u for u in str(r.imagens or "").split(",") if u.startswith("http")] or [r.thumbnail]
        tarefas += [(u, f"{DATA}/midia/{r.video_id}_{i}.jpg") for i, u in enumerate(imgs[:10]) if u]

    def baixa(t):
        url, f = t
        if os.path.exists(f):
            return True
        try:
            r = httpx.get(url, timeout=60, follow_redirects=True)
            r.raise_for_status()
            open(f, "wb").write(r.content)
            return True
        except httpx.HTTPError:
            return False
    with ThreadPoolExecutor(8) as ex:
        ok = list(ex.map(baixa, tarefas))
    print(f"{sum(ok)}/{len(ok)} arquivos em {DATA}/midia ({len(df)} posts)")


# ---------- rank ----------

MAX_POR_CRIADOR = 3   # no top: evita que um criador vire "o padrão do mercado"
MIN_POSTS_CRIADOR = 5
MIN_IDADE_TOP = 7


def residuo_modelo(df):
    """Resíduo do modelo misto log1p(curtidas+comentários) ~ log(seguidores) + formato + log(idade) + (1|criador),
    ajustado por plataforma. Resíduo = quanto o post superou o esperado para esse criador, formato e idade.
    Efeito do criador = quanto o criador engaja acima do esperado para o tamanho (encolhido se tem poucos posts)."""
    import statsmodels.formula.api as smf
    d = df.assign(y=np.log1p(df.likes + df.comentarios), logF=np.log(df.inscritos.clip(lower=1)),
                  logIdade=np.log1p(df.get("idade_dias", pd.Series(30, index=df.index)).fillna(30)),
                  formato=np.where(df.plataforma == "youtube",
                                   pd.cut(df.get("duracao_s", pd.Series(30, index=df.index)).fillna(30),
                                          [-1, 15, 30, 60, 1e9], labels=["0-15s", "15-30s", "30-60s", ">60s"]).astype(str),
                                   df.get("tipo", pd.Series("x", index=df.index)).fillna("x")))
    resid, efeito = pd.Series(np.nan, index=df.index), pd.Series(np.nan, index=df.index)
    for plat, g in d.groupby("plataforma"):
        forma = "y ~ logF + logIdade" + (" + C(formato)" if g.formato.nunique() > 1 else "")
        m = None
        # o lbfgs degenerava no YouTube (variância do criador ~0) e caía em silêncio no plano B; bfgs primeiro, e
        # ajuste que não converge ou zera a variância do criador conta como falha -> tenta o próximo otimizador
        for metodo in ("bfgs", "powell", "lbfgs"):
            try:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    t = smf.mixedlm(forma, g, groups=g["channel_id"]).fit(method=metodo)
                if t.converged and np.isfinite(t.llf) and t.cov_re.iloc[0, 0] >= 1e-6:
                    m = t
                    break
            except Exception:
                pass
        if m is not None:
            resid[g.index] = g.y - m.fittedvalues
            efeito[g.index] = g.channel_id.map({k: v.iloc[0] for k, v in m.random_effects.items()})
            print(f"  régua {plat}: modelo misto ({metodo}), b = {m.params['logF']:.3f}, "
                  f"variância do criador = {m.cov_re.iloc[0, 0]:.3f}, n = {len(g)}")
        else:  # ponytail: base pequena demais para o modelo -> log do outlier (mesma ideia, sem formato/idade)
            med = g.groupby("channel_id").y.transform("median")
            resid[g.index] = g.y - med
            print(f"  régua {plat}: PLANO B (log-engajamento − mediana do criador; modelo não ajustou), n = {len(g)}")
    return resid, efeito


def sorteio_estavel(d, n):
    """Sorteio que não muda quando a base muda: ordena por um hash do id. Um post que sai abre só uma vaga, em vez de
    trocar a amostra inteira (o sample(random_state) trocava, e a categorização nunca fechava)."""
    import zlib
    return d.loc[d.video_id.map(lambda x: zlib.crc32(str(x).encode())).sort_values().index[:n]]


def ranquear(v, c, excluidos=(), relevancia=None):
    """excluidos: channel_ids reprovados na validação manual. relevancia: {video_id: elegível para o Foco A} dos posts
    já categorizados (False = irrelevante para MPE ou fala com o consumidor final; ver elegivel_foco_a)."""
    c = c[["channel_id", "plataforma", "titulo", "inscritos", "porte", "segmento", "tipo_criador"]]
    df = v.merge(c.rename(columns={"titulo": "canal"}), on=["channel_id", "plataforma"])
    df = df[df.likes.notna() & (df.inscritos > 0)].copy()  # curtidas ocultas não entram (documentar no README)
    df["comentarios"] = df.comentarios.fillna(0)
    df["er"] = (df.likes + df.comentarios) / df.inscritos
    df["conversa"] = df.comentarios / df.likes.where(df.likes > 0)  # comentários por curtida
    # outlier score: post vs. mediana do próprio canal -> separa conteúdo de popularidade do criador
    g = df.groupby("channel_id").er
    df["outlier"] = (df.er / g.transform("median")).where(g.transform("size") >= 5)
    # Régua de alto desempenho (decidida em 23/11): o ER do TAPI segue sendo o reportado, mas o top sai do resíduo
    # do modelo misto, dentro da base elegível, top 10% por plataforma × porte e no máx. 3 posts por criador.
    n_posts = df.groupby("channel_id").video_id.transform("size")
    rel = df.video_id.map(relevancia or {})
    df["elegivel"] = (~df.channel_id.isin(set(excluidos)) & (n_posts >= MIN_POSTS_CRIADOR)
                      & (df.get("idade_dias", pd.Series(MIN_IDADE_TOP, index=df.index)).fillna(MIN_IDADE_TOP) >= MIN_IDADE_TOP)
                      & (rel != False))  # noqa: E712 (sem categoria ainda = candidato; categorize e rode rank de novo)
    df["resid"], df["efeito_criador"] = np.nan, np.nan
    el = df[df.elegivel]
    if len(el):
        df.loc[el.index, "resid"], df.loc[el.index, "efeito_criador"] = residuo_modelo(el)
    corte = df[df.elegivel].groupby(["plataforma", "porte"]).resid.transform(lambda x: x.quantile(0.9))
    cand = df[df.elegivel & (df.resid >= corte.reindex(df.index))]
    escolhidos = cand.sort_values("resid", ascending=False).groupby("channel_id").head(MAX_POR_CRIADOR).index
    df["top"] = df.index.isin(escolhidos)
    p = df.groupby(["plataforma", "porte"])
    df["top_er_puro"] = df.er >= p.er.transform(lambda x: x.quantile(0.9))  # régua antiga, para comparar no README
    # controle: sorteio fora do top, mesmo tamanho do top em cada estrato (para o lift)
    n_top = df[df.top].groupby(["plataforma", "porte"]).size()
    ctrl = df[~df.top & df.elegivel].groupby(["plataforma", "porte"], group_keys=False)[df.columns].apply(
        lambda d: sorteio_estavel(d, n_top.get(d.name, 0)))
    df["grupo"] = None
    df.loc[df.top, "grupo"] = "top"
    df.loc[ctrl.index, "grupo"] = "controle"
    # ponytail: saldo livre da Feita (US$ 2) não cobre os 2.200 do YouTube; amostra sorteada por estrato
    df["amostra"] = df.plataforma == "instagram"
    yt = df[(df.plataforma == "youtube") & df.grupo.notna()]
    sorteio = yt.groupby(["grupo", "porte"], group_keys=False)[yt.columns].apply(
        lambda d: sorteio_estavel(d, YT_AMOSTRA))
    df.loc[sorteio.index, "amostra"] = True
    df["amostra"] &= df.grupo.notna()
    df["url"] = df.video_id.radd("https://www.youtube.com/shorts/").where(
        df.plataforma == "youtube", "https://www.instagram.com/p/" + df.video_id + "/")
    return df.sort_values("resid", ascending=False)


def rank(_):
    con = db()
    exc = pd.read_csv(f"{DATA}/veredictos.csv") if os.path.exists(f"{DATA}/veredictos.csv") else pd.DataFrame(columns=["id", "decisao"])
    excluidos = set(exc[exc.decisao == "excluir"].id)
    cat = pd.read_sql("select video_id, rubrica from categorias", con) if con.execute(
        "select name from sqlite_master where name='categorias'").fetchone() else pd.DataFrame(columns=["video_id", "rubrica"])
    relevancia = {v: elegivel_foco_a(json.loads(r)) for v, r in zip(cat.video_id, cat.rubrica)}
    print(f"excluídos pela validação: {len(excluidos)} canais · posts categorizados: {len(relevancia)} "
          f"({sum(not x for x in relevancia.values())} fora do Foco A: irrelevantes ou para o consumidor final)")
    df = ranquear(pd.read_sql("select * from videos", con), pd.read_sql("select * from canais", con), excluidos, relevancia)
    df.to_sql("ranking", con, if_exists="replace", index=False)
    for plat, d in df.groupby("plataforma"):
        print(f"\n{plat}: {len(d)} posts, {d.elegivel.sum()} elegíveis, {d.top.sum()} no top "
              f"({d[d.top].channel_id.nunique()} criadores; ER mediano do top {d[d.top].er.median():.4f}, da base {d.er.median():.4f})")
        print("top por porte:", d[d.top].porte.value_counts().to_dict(),
              "· amostra sem categoria:", int((d.amostra & ~d.video_id.isin(relevancia)).sum()))
        print(d.head(5)[["canal", "resid", "er", "outlier", "conversa"]].to_string())


# ---------- categorize ----------

FORMATOS = ["talking head", "tutorial", "bastidores", "antes/depois", "humor/esquete", "depoimento", "lista/dicas", "trend",
            "carrossel/estático"]
PILARES = ["educação financeira", "gestão e vendas", "histórias reais", "especialistas", "comunidade"]
TEMAS = ["vendas", "finanças", "marketing", "atendimento", "gestão", "motivação", "ferramentas/maquininha",
         "história de empreendedor"]


PUBLICO_FORA_A = {"consumidor_final", "nenhum"}


def elegivel_foco_a(rub):
    """Rubrica (dict) -> o post pode entrar no top do Foco A? Rubrica antiga, sem publico_alvo, vale pela relevância."""
    return rub.get("relevante_mpe") is not False and rub.get("publico_alvo") not in PUBLICO_FORA_A


class Rubrica(BaseModel):
    relevante_mpe: bool  # o post em si fala com dono de pequeno negócio (canal MPE também posta fora do tema)
    # Foco A = donos_de_negocio (ou ambos); consumidor_final é o Foco B (negócio falando com o cliente dele)
    publico_alvo: Literal["donos_de_negocio", "consumidor_final", "ambos", "nenhum"]
    formato_video: Literal["talking head", "tutorial", "bastidores", "antes/depois", "humor/esquete",
                           "depoimento", "lista/dicas", "trend", "carrossel/estático"]
    hook_primeiros_3s: str
    tipo_hook: Literal["pergunta", "promessa", "dor", "número", "polêmica", "curiosidade"]
    forca_hook_0a10: int
    tema_principal: Literal["vendas", "finanças", "marketing", "atendimento", "gestão", "motivação",
                            "ferramentas/maquininha", "história de empreendedor"]
    tem_rosto: bool
    criador_e_empreendedor_real: bool
    prova_social: bool
    texto_na_tela: bool
    ritmo_cortes_0a10: int
    tom: Literal["informal", "técnico", "inspiracional", "humorístico"]
    usa_linguagem_regional: bool
    clareza_mensagem_0a10: int
    tem_cta: bool
    tipo_cta: Literal["comentar", "salvar", "link na bio", "DM", "seguir", "nenhum"]
    oferta_ou_beneficio_explicito: bool
    # calibrados pelos Ads do Impulso: convite à participação > 8% CTR; genérico/motivacional < 1%
    convite_participacao: bool
    gatilho_identificacao: Literal["nicho", "data_sazonal", "dor", "pessoa_real", "nenhum"]
    generico_0a10: int
    pilar_impulso: Literal["educação financeira", "gestão e vendas", "histórias reais", "especialistas", "comunidade"]
    elementos_top5: list[str]


PROMPT = """Você analisa posts (vídeos curtos, carrosséis e imagens) voltados a micro e pequenos empreendedores brasileiros.
Preencha a rubrica em JSON com base no que você vê e ouve no vídeo (ou na thumbnail, se for só imagem).
- hook_primeiros_3s: o que é dito ou mostrado nos primeiros 3 segundos, em até 15 palavras.
- tipo_hook: pergunta | promessa | dor | número | polêmica | curiosidade.
- notas 0a10: 0 = ausente/fraco, 10 = excelente. Seja conservador.
- criador_e_empreendedor_real: a pessoa do vídeo tem um negócio próprio de verdade (não só fala sobre negócios).
- prova_social: mostra resultados, números, depoimentos de clientes ou bastidores de vendas reais.
- tipo_cta: "nenhum" se tem_cta for false.
- relevante_mpe: false se o post não tem relação com empreender ou ter um pequeno negócio (política, fofoca, reparo de eletrônico sem lição de negócio), mesmo vindo de um canal de negócios.
- publico_alvo: para quem o post fala. donos_de_negocio = ensina, aconselha ou inspira quem tem ou quer ter um negócio; consumidor_final = é o próprio negócio falando com o cliente dele para atrair ou vender (produto, serviço, bastidor, oferta); ambos = serve aos dois; nenhum = fora do tema (use junto com relevante_mpe = false).
- convite_participacao: o post chama o público a participar (contar a própria história, mandar dúvida, responder enquete), além de só pedir like ou seguir.
- gatilho_identificacao: o que faz o empreendedor pensar "isso é comigo". nicho = fala com um segmento específico (salão, lanchonete); data_sazonal = data ou época (Natal, Dia das Mães); dor = problema concreto (caixa no vermelho, cliente que some); pessoa_real = um empreendedor real e identificável; nenhum.
- generico_0a10: 10 = frase motivacional que serviria para qualquer público; 0 = específico e acionável para quem tem pequeno negócio.
- pilar_impulso: o pilar editorial que melhor descreve o post (histórias reais = trajetória de um empreendedor; especialistas = alguém com autoridade ensinando; comunidade = troca e participação do público).
- carrossel ou imagem: formato_video = "carrossel/estático", ritmo_cortes_0a10 = 0 e hook_primeiros_3s = o texto da primeira imagem.
- elementos_top5: os 5 elementos que mais explicam a atenção que o post gera, frases curtas.
Título: {titulo}
Descrição: {descricao}"""


def conteudo_video(r):
    return [{"type": "video_url", "video_url": {"url": f"https://www.youtube.com/watch?v={r.video_id}"}},
            {"type": "text", "text": PROMPT.format(titulo=r.titulo, descricao=r.descricao[:1000])}]


def conteudo_thumb(r):
    return [{"type": "image_url", "image_url": {"url": r.thumbnail}},
            {"type": "text", "text": PROMPT.format(titulo=r.titulo, descricao=r.descricao[:1000])}]


def b64(f, mime):
    import base64
    return f"data:{mime};base64," + base64.b64encode(open(f, "rb").read()).decode()


def conteudo_ig(r, so_imagens=False):
    """Reel: mp4 baixado (vídeo com áudio). Carrossel/imagem: até 10 imagens. Sempre com a legenda.
    so_imagens: para modelo que não lê vídeo (DeepSeek); do Reel vai só a capa."""
    import glob
    texto = {"type": "text", "text": PROMPT.format(titulo=f"post de @{r.channel_id} ({r.tipo})", descricao=r.descricao[:1500])}
    mp4 = f"{DATA}/midia/{r.video_id}.mp4"
    if os.path.exists(mp4) and not so_imagens:
        return [{"type": "video_url", "video_url": {"url": b64(mp4, "video/mp4")}}, texto], "video"
    imgs = sorted(glob.glob(f"{DATA}/midia/{r.video_id}_*.jpg"))[:10]
    if not imgs:
        raise FileNotFoundError(f"sem mídia para {r.video_id}")
    return [{"type": "image_url", "image_url": {"url": b64(f, "image/jpeg")}} for f in imgs] + [texto], "imagens"


def categoriza_um(r, so_thumb=False):
    if r.plataforma == "instagram":
        conteudo, fonte = conteudo_ig(r)
        return llm(conteudo, Rubrica), fonte
    if not so_thumb:
        try:
            return llm(conteudo_video(r), Rubrica), "video"
        except Exception as e:  # vídeo indisponível: cai para thumbnail + texto
            from openai import InternalServerError, RateLimitError
            # limite da Feita (20 simultâneas) ou cota/pico do Gemini (429/503): não é falha do vídeo, fica para a próxima rodada
            if isinstance(e, (RateLimitError, InternalServerError)) or getattr(e, "code", None) in (429, 500, 503):
                raise
            print(f"  vídeo {r.video_id} falhou ({str(e)[:60]}), usando thumbnail")
    return llm(conteudo_thumb(r), Rubrica), "thumbnail"


N1_MODEL = "deepseek/deepseek-v4.1-flash-1017"  # crédito da Feita restrito a ele; só lê imagem + texto


def categorize(a):
    """metodo video: Gemini vê o vídeo (tabela categorias). metodo n1: DeepSeek vê thumbnail + título + descrição
    (tabela categorias_n1, separada, para medir o impacto do método). metodo deepseek: igual ao n1, mas grava na
    tabela categorias com fonte thumbnail_deepseek (completa o YouTube quando a cota do Gemini acaba)."""
    con = db()
    tab = "categorias_n1" if a.metodo == "n1" else "categorias"
    con.execute(f"create table if not exists {tab} "
                "(video_id text primary key, grupo text, fonte text, rubrica text, criado_em text)")
    df = ler_ranking(con)
    if a.metodo == "n1" or (a.metodo == "deepseek" and not a.plataforma):
        df = df[df.plataforma == "youtube"]  # deepseek no Instagram só se pedido com --plataforma instagram
    feitos = set(pd.read_sql(f"select video_id from {tab}", con).video_id)
    alvo = df[df.amostra & ((df.plataforma == a.plataforma) if a.plataforma else True)]
    # instagram e top primeiro: é o foco, e cada post do top que sai irrelevante abre vaga no próximo rank
    alvo = alvo.assign(o=(alvo.plataforma == "youtube") * 2 + (alvo.grupo != "top")).sort_values("o")
    alvo = alvo[~alvo.video_id.isin(feitos)].head(a.limite)
    print(f"{len(feitos)} já categorizados, {len(alvo)} nesta rodada")
    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(a.paralelo) as ex:
        def um(r):
            if a.metodo != "video" and r.plataforma == "instagram":  # provisório: sem o vídeo do Reel, só capa + legenda
                return llm(conteudo_ig(r, so_imagens=True)[0][-5:], Rubrica, model=N1_MODEL), "imagens_deepseek"
            if a.metodo != "video":
                return llm(conteudo_thumb(r), Rubrica, model=N1_MODEL), "thumbnail_deepseek"
            return categoriza_um(r, a.so_thumb)
        futs = {ex.submit(um, r): r for r in alvo.itertuples()}
        for i, f in enumerate(as_completed(futs), 1):
            r = futs[f]
            try:
                rub, fonte = f.result()
            except Exception as e:
                print(f"[{i}/{len(alvo)}] ERRO {r.video_id}: {str(e)[:100]}")
                continue
            con.execute(f"insert or replace into {tab} values (?,?,?,?,?)",
                        (r.video_id, r.grupo, fonte, json.dumps(rub.model_dump(), ensure_ascii=False),
                         datetime.now().isoformat()))
            con.commit()
            if i % 25 == 0 or i == len(alvo):
                print(f"[{i}/{len(alvo)}] {r.plataforma} {r.grupo} {fonte} {rub.formato_video} {rub.tema_principal}")


# ---------- analyze ----------

CAMPOS = ["formato_video", "tipo_hook", "tema_principal", "tom", "tipo_cta", "duracao_faixa", "legenda_tamanho",
          "tem_rosto", "criador_e_empreendedor_real", "prova_social", "texto_na_tela", "usa_linguagem_regional",
          "tem_cta", "oferta_ou_beneficio_explicito", "convite_participacao", "gatilho_identificacao",
          "pilar_impulso", "tipo_post", "porte", "segmento", "tipo_criador", "generico"]
NOTAS = ["forca_hook_0a10", "ritmo_cortes_0a10", "clareza_mensagem_0a10", "generico_0a10"]
TIPO_POST = {"clips": "reel", "carousel_container": "carrossel", "feed": "imagem"}


def ler_ranking(con, sql="select * from ranking"):
    df = pd.read_sql(sql, con)
    for c in ["top", "top_er_puro", "elegivel", "amostra"]:
        if c in df:
            df[c] = df[c].astype(bool)  # SQLite guarda bool como 0/1
    return df


def carregar(con, tab="categorias"):
    df = ler_ranking(con, f"select r.*, c.fonte, c.rubrica from ranking r join {tab} c using(video_id)")
    rub = pd.json_normalize(df.rubrica.map(json.loads))
    df = pd.concat([df.drop(columns="rubrica").reset_index(drop=True), rub], axis=1)
    # post fora do tema ou que fala com o consumidor final (Foco B) não entra na análise do Foco A
    df = df[[elegivel_foco_a(r) for r in rub.to_dict("records")]]
    df["generico"] = df.generico_0a10 >= 6  # mesmo corte binário da base interna
    df["tipo_post"] = df.tipo.map(TIPO_POST).where(df.plataforma == "instagram", "short")
    df["duracao_faixa"] = pd.cut(df.duracao_s, [0, 15, 30, 60, 10**5],
                                 labels=["<15s", "15-30s", "30-60s", ">60s"]).astype(str).replace("nan", "sem vídeo")
    df["legenda_tamanho"] = pd.cut(df.descricao.str.len(), [-1, 100, 500, 10**6], labels=["curta", "media", "longa"]).astype(str)
    return df


def lift_table(df, campos=CAMPOS):
    """Frequência de cada valor no top vs. no controle, por plataforma. lift > 1 = mais comum no top.
    "todas" = média simples das plataformas (peso igual: o YouTube tem 4× mais posts no top e dominaria a soma)."""
    out = []
    for plat, d in df.groupby("plataforma"):
        top, ctl = d[d.grupo == "top"], d[d.grupo == "controle"]
        for campo in campos:
            for valor in d[campo].dropna().unique():
                out.append(dict(plataforma=plat, campo=campo, valor=str(valor), freq_top=(top[campo] == valor).mean(),
                                freq_resto=(ctl[campo] == valor).mean(), n_top=int((top[campo] == valor).sum())))
    lt = pd.DataFrame(out, columns=["plataforma", "campo", "valor", "freq_top", "freq_resto", "n_top"])
    # valor ausente numa plataforma conta como frequência 0 nela (unstack + fillna), não some da média
    f = lt.set_index(["campo", "valor", "plataforma"])[["freq_top", "freq_resto"]].unstack().fillna(0).stack(future_stack=True)
    todas = f.groupby(level=["campo", "valor"]).mean().join(lt.groupby(["campo", "valor"]).n_top.sum()).reset_index()
    lt = pd.concat([todas.assign(plataforma="todas"), lt], ignore_index=True)
    lt["lift"] = (lt.freq_top / lt.freq_resto.where(lt.freq_resto > 0)).round(2)
    lt[["freq_top", "freq_resto"]] = lt[["freq_top", "freq_resto"]].round(3)
    return lt[["plataforma", "campo", "valor", "freq_top", "freq_resto", "lift", "n_top"]]


def perfis_destaque(df_rank, df_cat):
    # ordem pelo efeito do criador no modelo misto (engaja acima do esperado para o tamanho; encolhido se tem poucos posts)
    el = df_rank[df_rank.elegivel] if "elegivel" in df_rank else df_rank
    p = el.groupby(["plataforma", "canal", "porte", "inscritos"]).agg(
        efeito_criador=("efeito_criador", "first"), n_top=("top", "sum"), n_posts=("video_id", "size")).reset_index()
    p = p[p.n_top > 0]
    t = df_cat[df_cat.grupo == "top"]
    pred = t.groupby("canal").agg(tema=("tema_principal", lambda s: s.mode().iat[0]),
                                  formato=("formato_video", lambda s: s.mode().iat[0]),
                                  pilar=("pilar_impulso", lambda s: s.mode().iat[0]),
                                  outlier_mediano=("outlier", "median"))
    return p.merge(pred, on="canal", how="left").sort_values(["plataforma", "efeito_criador"], ascending=[True, False])


def comparar_metodos(video, n1, campos=CAMPOS):
    """Mesmos posts nos dois métodos: % de concordância e kappa por campo da rubrica."""
    m = video.merge(n1, on="video_id", suffixes=("_v", "_n1"))
    out = []
    for c in [c for c in campos if f"{c}_v" in m and c not in ("porte", "segmento", "tipo_criador", "tipo_post",
                                                                 "duracao_faixa", "legenda_tamanho")]:
        a, b = m[f"{c}_v"].astype(str), m[f"{c}_n1"].astype(str)
        out.append(dict(campo=c, n=len(m), concordancia=round((a == b).mean(), 2), kappa=round(kappa(a, b), 2)))
    return pd.DataFrame(out).sort_values("kappa")


def analyze(_):
    con = db()
    df = carregar(con)
    lt = lift_table(df[df.amostra]).sort_values(["campo", "freq_top"], ascending=[True, False])
    lt.to_csv(f"{DATA}/achados.csv", index=False)
    notas = df[df.amostra].groupby(["plataforma", "grupo"])[NOTAS].median().T
    notas.to_csv(f"{DATA}/notas.csv")
    # parcela YouTube nível 1 (DeepSeek, sem vídeo): lift próprio + concordância com o Gemini nos mesmos posts
    if con.execute("select count(*) from sqlite_master where name='categorias_n1'").fetchone()[0]:
        n1 = carregar(con, "categorias_n1")
        n1 = n1[n1.amostra]
        lt1 = lift_table(n1).query("plataforma == 'youtube'").assign(metodo="n1_deepseek")
        lt1.to_csv(f"{DATA}/achados_youtube_n1.csv", index=False)
        cmp = comparar_metodos(df, n1)
        cmp.to_csv(f"{DATA}/comparacao_metodos.csv", index=False)
        print(f"\n[youtube · nível 1 DeepSeek] {len(n1)} posts\n"
              + lt1[(lt1.n_top >= 5) & lt1.lift.notna()].sort_values("lift", ascending=False).head(12).to_string(index=False))
        print("\nConcordância Gemini (vídeo) x DeepSeek (thumbnail) nos mesmos posts:\n" + cmp.to_string(index=False))
    pf = perfis_destaque(ler_ranking(con), df)
    pf.to_csv(f"{DATA}/perfis_destaque.csv", index=False)
    print(f"Base categorizada: {(df.grupo == 'top').sum()} top, {(df.grupo == 'controle').sum()} controle, "
          f"{df.amostra.sum()} na amostra do lift "
          f"({df.fonte.str.startswith('thumbnail').mean():.0%} só por thumbnail)\n")
    print("Características mais associadas ao alto desempenho (lift, n_top >= 5):")
    for plat, d in lt[(lt.n_top >= 5) & lt.lift.notna()].groupby("plataforma"):
        print(f"\n[{plat}]\n" + d.sort_values("lift", ascending=False).head(15).to_string(index=False))
    print("\nNotas medianas:\n" + notas.to_string())
    print("\nPerfis em destaque:\n" + pf.groupby("plataforma").head(8).to_string(index=False))
    print(f"\n-> {DATA}/achados.csv, notas.csv, perfis_destaque.csv")


CAMPOS_INTERNOS = ["convite_participacao", "gatilho_identificacao", "tem_cta", "generico"]


def selo(lift, dif_interna):
    """Mercado (lift top/controle) x casa (freq. nos Ads de alto - baixo desempenho)."""
    if dif_interna is None or pd.isna(dif_interna):
        return "só mercado"
    mercado = 1 if lift >= 1.2 else -1 if lift <= 0.8 else 0
    casa = 1 if dif_interna > 0.1 else -1 if dif_interna < -0.1 else 0
    if mercado == 0 or casa == 0:
        return "inconclusivo"
    return "confirmado" if mercado == casa else "contradito"


def cruzar(_):
    lt = pd.read_csv(f"{DATA}/achados.csv", dtype={"valor": str})
    # selo por plataforma (o Instagram é o que pauta o @impulsostone); "todas" = peso igual por plataforma
    lt = lt[(lt.n_top >= 5) & lt.lift.notna()].copy()
    ads = pd.read_csv("impulso_interno.csv", dtype=str)
    ads = ads[ads.fonte == "ads"]
    alto, baixo = ads[ads.desempenho == "alto"], ads[ads.desempenho == "baixo"]

    def dif(r):
        if r.campo not in CAMPOS_INTERNOS:
            return None
        return (alto[r.campo] == r.valor).mean() - (baixo[r.campo] == r.valor).mean()

    lt["dif_interna"] = lt.apply(dif, axis=1).astype(float).round(2)
    lt["selo"] = [selo(l, d) for l, d in zip(lt.lift, lt.dif_interna)]
    lt = lt[(lt.lift >= 1.2) | (lt.lift <= 0.8) | lt.dif_interna.notna()]
    # confiança do campo vem da validação manual (kappa você x IA)
    vf = f"{DATA}/validacao_resultado.csv"
    k = pd.read_csv(vf).set_index("campo").kappa.to_dict() if os.path.exists(vf) else {}
    lt["kappa"] = lt.campo.map(k)
    lt["confianca"] = lt.kappa.map(lambda x: "não validado" if pd.isna(x) else "alta" if x >= 0.6
                                   else "média" if x >= 0.4 else "baixa")
    lt.loc[lt.campo.isin(["porte", "segmento", "tipo_criador", "tipo_post", "duracao_faixa"]), "confianca"] = "dado objetivo"
    # instagram por último: quem lê o csv como {(campo, valor): selo} (agent.selos) fica com o selo do Instagram
    lt["o"] = lt.plataforma.map({"todas": 0, "youtube": 1, "instagram": 2})
    lt = lt.sort_values(["o", "selo", "lift"], ascending=[True, True, False]).drop(columns="o")
    lt.to_csv(f"{DATA}/padroes_selados.csv", index=False)
    print(lt.groupby("plataforma").selo.value_counts().to_string())
    print(lt[lt.dif_interna.notna()].to_string(index=False))
    print(f"-> {DATA}/padroes_selados.csv")


# ---------- validate ----------

VALIDAR = ["formato_video", "tema_principal", "tipo_hook", "pilar_impulso", "gatilho_identificacao",
           "convite_participacao", "tem_cta", "texto_na_tela"]


def kappa(a, b):
    a = pd.Series(a).astype(str).str.strip().str.lower().reset_index(drop=True)
    b = pd.Series(b).astype(str).str.strip().str.lower().reset_index(drop=True)
    po = (a == b).mean()
    pa, pb = a.value_counts(normalize=True), b.value_counts(normalize=True)
    pe = sum(pa.get(k, 0) * pb.get(k, 0) for k in set(pa.index) | set(pb.index))
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def validate(a):
    path = f"{DATA}/validacao.csv"
    if a.gerar:
        df = carregar(db())
        df = df[df.amostra & (df.plataforma == a.plataforma)] if a.plataforma else df[df.amostra]
        # metade top, metade controle
        df = df.groupby("grupo", group_keys=False)[df.columns].apply(lambda d: d.sample(min(a.n // 2, len(d)), random_state=7))
        out = df[["video_id", "url", "titulo"]].copy()
        for c in VALIDAR:
            out[f"manual_{c}"] = ""
        out.to_csv(path, index=False)
        print(f"-> preencha as colunas manual_* em {path} assistindo cada vídeo (bool: True/False). "
              f"Valores possíveis estão na classe Rubrica do pipeline.py")
        return
    man = pd.read_csv(path)
    auto = carregar(db()).set_index("video_id").loc[man.video_id].reset_index()
    rows = []
    for c in VALIDAR:
        ok = man[f"manual_{c}"].notna()
        rows.append(dict(campo=c, n=int(ok.sum()),
                         concordancia=round((auto[c][ok].astype(str).str.lower().values ==
                                             man[f"manual_{c}"][ok].astype(str).str.strip().str.lower().values).mean(), 2),
                         kappa=round(kappa(auto[c][ok], man[f"manual_{c}"][ok]), 2)))
    res = pd.DataFrame(rows)
    res.to_csv(f"{DATA}/validacao_resultado.csv", index=False)
    print(res.to_string(index=False))
    print("kappa < 0.4 = campo pouco confiável: cite isso no README e no playbook")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="etapa", required=True)
    for nome in ["check", "discover", "collect", "rank", "analyze", "cruzar"]:
        sub.add_parser(nome)
    sub.add_parser("ig_midia")
    sub.add_parser("ig_collect").add_argument("--por-perfil", type=int, default=40)
    ig = sub.add_parser("ig_discover")
    ig.add_argument("--expandir", action="store_true")
    ig.add_argument("--limite", type=int, default=60)
    ig.add_argument("--por-hashtag", type=int, default=30)
    sub.add_parser("triagem").add_argument("arquivo", nargs="?", default=f"{DATA}/canais.csv")
    c = sub.add_parser("categorize")
    c.add_argument("--limite", type=int, default=100_000)
    c.add_argument("--metodo", choices=["video", "n1", "deepseek"], default="video")
    c.add_argument("--paralelo", type=int, default=18)  # Feita: no máx. 20 simultâneas por chave
    c.add_argument("--plataforma", choices=["youtube", "instagram"])
    c.add_argument("--so-thumb", action="store_true", help="não manda o vídeo, só thumbnail + texto")
    v = sub.add_parser("validate")
    v.add_argument("--gerar", action="store_true")
    v.add_argument("--n", type=int, default=50)
    v.add_argument("--plataforma", choices=["youtube", "instagram"])
    a = ap.parse_args()
    globals()[a.etapa](a)
