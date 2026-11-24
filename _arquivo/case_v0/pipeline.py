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
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()
DATA = os.getenv("DATA_DIR", "data")
DB = f"{DATA}/stone.db"
YT = "https://www.googleapis.com/youtube/v3"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")

KEYWORDS = [
    "dicas para pequenos negócios", "MEI dicas", "como vender mais loja", "marketing para pequenos negócios",
    "empreendedorismo pequeno negócio", "educação financeira empreendedor", "maquininha de cartão",
    "dicas para lojista", "como precificar produto", "atendimento ao cliente pequeno negócio",
]
MIN_IDADE_DIAS = 14     # métricas estabilizadas (TAPI)
JANELA_DIAS = 365       # últimos 12 meses
MAX_DURACAO_S = 180     # ponytail: a API não marca Shorts; Short = vídeo de até 3 min
MAX_VIDEOS_CANAL = 200  # 4 páginas de playlist por canal


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


def gemini(contents, schema, tentativas=6):
    """Chamada ao Gemini com saída JSON validada por Pydantic e backoff em 429/5xx."""
    global _client
    from google import genai
    from google.genai import errors, types
    _client = _client or genai.Client()  # lê GEMINI_API_KEY do .env
    cfg = types.GenerateContentConfig(
        response_mime_type="application/json", response_schema=schema, temperature=0,
        media_resolution=types.MediaResolution.MEDIA_RESOLUTION_LOW,
    )
    for t in range(tentativas):
        try:
            r = _client.models.generate_content(model=GEMINI_MODEL, contents=contents, config=cfg)
            if r.parsed is None:
                raise ValueError(f"resposta fora do schema: {r.text[:200]}")
            return r.parsed
        except errors.APIError as e:
            if e.code in (429, 500, 503) and t < tentativas - 1:
                time.sleep(min(60, 5 * 2 ** t))
                continue
            raise


def duracao_s(iso):
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def porte(subs):
    return "pequeno" if subs < 50_000 else "medio" if subs < 500_000 else "grande"


# ---------- check ----------

def check(_):
    r = yt("search", part="id", q="sebrae", type="channel", maxResults=1)
    print("YouTube OK:", r["items"][0]["id"]["channelId"])
    from google import genai
    nomes = [m.name for m in genai.Client().models.list() if "flash" in m.name]
    print("Gemini OK. Modelos flash disponíveis:", ", ".join(n.split("/")[-1] for n in nomes))
    print("Modelo em uso:", GEMINI_MODEL, "(troque com GEMINI_MODEL no .env)")


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
    df.to_sql("videos", con, if_exists="replace", index=False)
    canais.to_sql("canais", con, if_exists="replace", index=False)
    print(f"{total} lidos -> {len(df)} Shorts entre {MIN_IDADE_DIAS} e {JANELA_DIAS} dias, "
          f"{df.channel_id.nunique()} canais. Coletado em {agora:%Y-%m-%d %H:%M} UTC")


# ---------- rank ----------

def ranquear(v, c):
    df = v.merge(c[["channel_id", "titulo", "inscritos", "porte"]].rename(columns={"titulo": "canal"}), on="channel_id")
    df = df[df.likes.notna() & (df.inscritos > 0)].copy()  # curtidas ocultas não entram (documentar no README)
    df["comentarios"] = df.comentarios.fillna(0)
    df["er"] = (df.likes + df.comentarios) / df.inscritos
    # outlier score: post vs. mediana do próprio canal -> separa conteúdo de popularidade do criador
    g = df.groupby("channel_id").er
    df["outlier"] = (df.er / g.transform("median")).where(g.transform("size") >= 5)
    df["top"] = df.er >= df.er.quantile(0.9)
    df["top_outlier"] = df.outlier >= df.outlier.quantile(0.9)
    df["url"] = "https://www.youtube.com/shorts/" + df.video_id
    return df.sort_values("er", ascending=False)


def rank(_):
    con = db()
    df = ranquear(pd.read_sql("select * from videos", con), pd.read_sql("select * from canais", con))
    df.to_sql("ranking", con, if_exists="replace", index=False)
    print(f"{len(df)} vídeos ranqueados, {df.top.sum()} no top 10% (er >= {df.er.quantile(0.9):.4f})")
    print("Top 10% por porte:\n" + df[df.top].porte.value_counts().to_string())
    print(df.head(10)[["canal", "titulo", "er", "outlier"]].to_string())


# ---------- categorize ----------

FORMATOS = ["talking head", "tutorial", "bastidores", "antes/depois", "humor/esquete", "depoimento", "lista/dicas", "trend"]
TEMAS = ["vendas", "finanças", "marketing", "atendimento", "gestão", "motivação", "ferramentas/maquininha",
         "história de empreendedor"]


class Rubrica(BaseModel):
    formato_video: Literal["talking head", "tutorial", "bastidores", "antes/depois", "humor/esquete",
                           "depoimento", "lista/dicas", "trend"]
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
    elementos_top5: list[str]


PROMPT = """Você analisa vídeos curtos voltados a micro e pequenos empreendedores brasileiros.
Preencha a rubrica em JSON com base no que você vê e ouve no vídeo (ou na thumbnail, se for só imagem).
- hook_primeiros_3s: o que é dito ou mostrado nos primeiros 3 segundos, em até 15 palavras.
- tipo_hook: pergunta | promessa | dor | número | polêmica | curiosidade.
- notas 0a10: 0 = ausente/fraco, 10 = excelente. Seja conservador.
- criador_e_empreendedor_real: a pessoa do vídeo tem um negócio próprio de verdade (não só fala sobre negócios).
- prova_social: mostra resultados, números, depoimentos de clientes ou bastidores de vendas reais.
- tipo_cta: "nenhum" se tem_cta for false.
- elementos_top5: os 5 elementos que mais explicam a atenção que o vídeo gera, frases curtas.
Título: {titulo}
Descrição: {descricao}"""


def conteudo_video(r):
    from google.genai import types
    return types.Content(parts=[
        types.Part(file_data=types.FileData(file_uri=f"https://www.youtube.com/watch?v={r.video_id}")),
        types.Part(text=PROMPT.format(titulo=r.titulo, descricao=r.descricao[:1000])),
    ])


def conteudo_thumb(r):
    from google.genai import types
    img = httpx.get(r.thumbnail, timeout=30).content
    return [types.Part.from_bytes(data=img, mime_type="image/jpeg"),
            PROMPT.format(titulo=r.titulo, descricao=r.descricao[:1000])]


def categorize(a):
    con = db()
    con.execute("create table if not exists categorias "
                "(video_id text primary key, grupo text, fonte text, rubrica text, criado_em text)")
    df = ler_ranking(con)
    feitos = set(pd.read_sql("select video_id from categorias", con).video_id)
    top, resto = df[df.top], df[~df.top]
    controle = resto.sample(min(len(top), len(resto)), random_state=42)  # amostra de controle p/ calcular lift
    alvo = pd.concat([top.assign(grupo="top"), controle.assign(grupo="controle")])
    alvo = alvo[~alvo.video_id.isin(feitos)].head(a.limite)
    print(f"{len(feitos)} já categorizados, {len(alvo)} nesta rodada")
    for i, r in enumerate(alvo.itertuples(), 1):
        fonte = "video"
        try:
            rub = gemini(conteudo_video(r), Rubrica) if not a.so_thumb else None
        except Exception as e:  # vídeo indisponível ou cota de vídeo do plano gratuito estourada
            print(f"  vídeo falhou ({str(e)[:80]}), usando thumbnail")
            rub = None
        if rub is None:
            fonte = "thumbnail"
            rub = gemini(conteudo_thumb(r), Rubrica)
        con.execute("insert or replace into categorias values (?,?,?,?,?)",
                    (r.video_id, r.grupo, fonte, json.dumps(rub.model_dump(), ensure_ascii=False),
                     datetime.now().isoformat()))
        con.commit()
        print(f"[{i}/{len(alvo)}] {r.grupo:8} {fonte:9} {rub.formato_video:13} {rub.tema_principal:12} {r.titulo[:50]}")
        time.sleep(a.pausa)


# ---------- analyze ----------

CAMPOS = ["formato_video", "tipo_hook", "tema_principal", "tom", "tipo_cta", "duracao_faixa", "legenda_tamanho",
          "tem_rosto", "criador_e_empreendedor_real", "prova_social", "texto_na_tela", "usa_linguagem_regional",
          "tem_cta", "oferta_ou_beneficio_explicito"]
NOTAS = ["forca_hook_0a10", "ritmo_cortes_0a10", "clareza_mensagem_0a10"]


def ler_ranking(con, sql="select * from ranking"):
    df = pd.read_sql(sql, con)
    df[["top", "top_outlier"]] = df[["top", "top_outlier"]].astype(bool)  # SQLite guarda bool como 0/1
    return df


def carregar(con):
    df = ler_ranking(con, "select r.*, c.grupo, c.fonte, c.rubrica from ranking r join categorias c using(video_id)")
    rub = pd.json_normalize(df.rubrica.map(json.loads))
    df = pd.concat([df.drop(columns="rubrica").reset_index(drop=True), rub], axis=1)
    df["tipo_post"] = "short"
    df["duracao_faixa"] = pd.cut(df.duracao_s, [0, 15, 30, 60, 180], labels=["<15s", "15-30s", "30-60s", "60-180s"]).astype(str)
    df["legenda_tamanho"] = pd.cut(df.descricao.str.len(), [-1, 100, 500, 10**6], labels=["curta", "media", "longa"]).astype(str)
    return df


def lift_table(df, campos=CAMPOS):
    """Frequência de cada valor no top vs. no controle. lift > 1 = mais comum entre os de alto desempenho."""
    top, ctl = df[df.grupo == "top"], df[df.grupo == "controle"]
    out = []
    for campo in campos:
        for valor in df[campo].dropna().unique():
            ft, fc = (top[campo] == valor).mean(), (ctl[campo] == valor).mean()
            out.append(dict(campo=campo, valor=str(valor), freq_top=round(ft, 3), freq_resto=round(fc, 3),
                            lift=round(ft / fc, 2) if fc else None, n_top=int((top[campo] == valor).sum())))
    return pd.DataFrame(out, columns=["campo", "valor", "freq_top", "freq_resto", "lift", "n_top"])


def perfis_destaque(df_rank, df_cat):
    top = df_rank[df_rank.top]
    p = top.groupby(["canal", "porte", "inscritos"]).size().rename("n_top").reset_index()
    pred = df_cat[df_cat.grupo == "top"].groupby("canal").agg(
        tema=("tema_principal", lambda s: s.mode().iat[0]), formato=("formato_video", lambda s: s.mode().iat[0]))
    return p.merge(pred, on="canal", how="left").sort_values("n_top", ascending=False)


def analyze(_):
    con = db()
    df = carregar(con)
    lt = lift_table(df).sort_values(["campo", "freq_top"], ascending=[True, False])
    lt.to_csv(f"{DATA}/achados.csv", index=False)
    notas = df.groupby("grupo")[NOTAS].median().T
    notas.to_csv(f"{DATA}/notas.csv")
    pf = perfis_destaque(ler_ranking(con), df)
    pf.to_csv(f"{DATA}/perfis_destaque.csv", index=False)
    print(f"Base categorizada: {(df.grupo == 'top').sum()} top, {(df.grupo == 'controle').sum()} controle "
          f"({(df.fonte == 'thumbnail').mean():.0%} só por thumbnail)\n")
    print("Características mais associadas ao alto desempenho (lift, n_top >= 5):")
    print(lt[(lt.n_top >= 5) & lt.lift.notna()].sort_values("lift", ascending=False).head(20).to_string(index=False))
    print("\nNotas medianas:\n" + notas.to_string())
    print("\nPerfis em destaque:\n" + pf.head(15).to_string(index=False))
    print(f"\n-> {DATA}/achados.csv, notas.csv, perfis_destaque.csv")


# ---------- validate ----------

VALIDAR = ["formato_video", "tipo_hook", "tema_principal", "tom", "tem_rosto", "texto_na_tela", "prova_social",
           "tem_cta", "tipo_cta"]


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
        df = df.sample(min(50, len(df)), random_state=7)
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
    for nome in ["check", "discover", "collect", "rank", "analyze"]:
        sub.add_parser(nome)
    c = sub.add_parser("categorize")
    c.add_argument("--limite", type=int, default=1000)
    c.add_argument("--pausa", type=float, default=4.0, help="segundos entre chamadas (plano gratuito ~15/min)")
    c.add_argument("--so-thumb", action="store_true", help="não manda o vídeo, só thumbnail + texto")
    v = sub.add_parser("validate")
    v.add_argument("--gerar", action="store_true")
    a = ap.parse_args()
    globals()[a.etapa](a)
