"""Rodada noturna do Foco A: 103 creators novos do Instagram (influencers.club, aprovados à mão em
data/influencers_club/aprovar_foco_a.csv) -> coleta (Apify, 20 posts/perfil) -> rank -> mídia -> Gemini lendo o vídeo
até a cota acabar (de novo depois das 5h de Brasília, quando a cota zera) -> o que sobrar: DeepSeek com 12 quadros +
transcrição (Whisper) -> rank + analyze + cruzar.

Roda numa CÓPIA (data_noite/) para não mexer na base que o site usa. Para adotar: conferir data_noite/ e trocar.
Uso (com teto de memória):  systemd-run --user --scope -p MemoryMax=5G .venv/bin/python -u noite_foco_a.py
Pode ser interrompido e rodado de novo: cada passo vê o que já foi feito (chamadas pagas ficam em cache).
"""
import datetime as dt
import glob
import os
import shutil
import subprocess
import sys
import time

os.chdir(os.path.dirname(os.path.abspath(__file__)))
N = "data_noite"
if not os.path.exists(f"{N}/stone.db"):
    os.makedirs(N, exist_ok=True)
    for f in glob.glob("data/*.db") + glob.glob("data/*.csv") + glob.glob("data/*.json") + glob.glob("data/*.jsonl"):
        if "_antes_" not in f:
            shutil.copy2(f, N)
    shutil.copytree("data/raw", f"{N}/raw")
    os.symlink(os.path.abspath("data/midia"), f"{N}/midia")  # mídia é só arquivo novo por id: pode ser compartilhada
os.environ["DATA_DIR"] = N
from dotenv import dotenv_values  # noqa: E402

ENV = {k: v for k, v in dotenv_values(".env").items() if v}
os.environ.update(ENV)
import pandas as pd  # noqa: E402

import pipeline as P  # noqa: E402

PY = [sys.executable, "-u", "pipeline.py"]
FIM = dt.datetime.now().replace(hour=8, minute=30, second=0) + dt.timedelta(days=dt.datetime.now().hour >= 9)
RESET = dt.datetime.now().replace(hour=5, minute=10, second=0) + dt.timedelta(days=dt.datetime.now().hour >= 5)


def log(*a):
    print(time.strftime("%H:%M"), *a, flush=True)


def etapa(*args, **kw):
    log("$ pipeline.py", *args)
    subprocess.run(PY + list(args), check=kw.get("check", True), env=os.environ)


def falta(metodo_ok=None):
    """Posts do Instagram na amostra (top + controle) sem leitura em categorias."""
    con = P.db()
    df = P.ler_ranking(con)
    feitos = set(pd.read_sql("select video_id from categorias", con).video_id)
    return int((df.amostra & (df.plataforma == "instagram") & ~df.video_id.isin(feitos)).sum())


def lidos(fonte_like="%"):
    return P.db().execute("select count(*) from categorias k join videos v using(video_id) "
                          "where v.plataforma='instagram' and k.fonte like ?", (fonte_like,)).fetchone()[0]


# ---------------------------------------------------------------- 1. coleta dos creators aprovados
apr = pd.read_csv("data/influencers_club/aprovar_foco_a.csv")
apr = apr[apr.aprovar == 1]
con = P.db()
ja = set(pd.read_sql("select distinct channel_id from canais where plataforma='instagram'", con).channel_id)
if not apr.id.isin(ja).any():
    itens = []
    # ponytail: 20 posts/perfil ≈ US$ 0,0027 cada; a conta _3 (US$ 5) não cobre os 103, o resto vai na _2
    for cache, token, ids in [("posts_ic_1", ENV["APIFY_TOKEN_3"], apr.id[:80]), ("posts_ic_2", ENV["APIFY_TOKEN_2"], apr.id[80:])]:
        os.environ["APIFY_TOKEN_2"] = token
        log(f"Apify: {len(ids)} perfis ({cache})")
        itens += P.apify(cache, directUrls=[f"https://www.instagram.com/{u}/" for u in ids], resultsType="posts",
                         resultsLimit=20, onlyPostsNewerThan=f"{P.JANELA_DIAS} days")
    os.environ["APIFY_TOKEN_2"] = ENV["APIFY_TOKEN_2"]
    df = P.posts_ig(itens)
    df = df[df.channel_id.isin(apr.id) & df.idade_dias.between(P.MIN_IDADE_DIAS, P.JANELA_DIAS) & ~df.fixado]
    canais = pd.DataFrame(dict(channel_id=apr.id, titulo=apr.titulo, handle=apr.id, inscritos=apr.seguidores,
                               porte=[P.porte(x) for x in apr.seguidores], origem="influencers_club",
                               descricao=apr.descricao, incluir=1, voltado_mpe=apr.voltado_mpe,
                               tipo_criador=apr.tipo_criador, segmento=None, plataforma="instagram"))
    for tab, novo in [("videos", df), ("canais", canais)]:
        velho = pd.read_sql(f"select * from {tab}", con)
        pd.concat([velho, novo[~novo.iloc[:, 0].isin(velho.iloc[:, 0])]]).to_sql(tab, con, if_exists="replace", index=False)
    pf = pd.read_csv(f"{N}/perfis_ig.csv")
    novos = canais.rename(columns={"channel_id": "id", "inscritos": "seguidores"})[["id", "titulo", "descricao", "seguidores",
                                                                                   "porte", "origem", "incluir",
                                                                                   "voltado_mpe", "tipo_criador"]]
    pd.concat([pf, novos[~novos.id.isin(pf.id)]]).to_csv(f"{N}/perfis_ig.csv", index=False)
    log(f"coleta: {len(itens)} itens -> {len(df)} posts de {df.channel_id.nunique()} perfis | {df.tipo.value_counts().to_dict()}")

# ---------------------------------------------------------------- 2. rank (define top e controle) + mídia
etapa("rank")
etapa("ig_midia")
log(f"faltam {falta()} leituras no Instagram")

# ---------------------------------------------------------------- 3. Gemini (vídeo) em blocos; bloco sem avanço = cota acabou
for janela in ("agora", "depois do reset"):
    if janela == "depois do reset":
        if dt.datetime.now() < RESET:
            log(f"cota do Gemini esgotada; esperando o reset ({RESET:%H:%M})")
            time.sleep(max(0, (RESET - dt.datetime.now()).total_seconds()))
        else:
            break  # o reset já passou durante a primeira janela
    while falta() and dt.datetime.now() < FIM:
        antes = lidos()
        etapa("categorize", "--metodo", "video", "--plataforma", "instagram", "--limite", "20", "--paralelo", "2", check=False)
        if lidos() == antes:
            break
        etapa("rank")  # post do top que sai irrelevante abre vaga para o próximo
        etapa("ig_midia")
    log(f"Gemini ({janela}): {lidos('video') + lidos('imagens')} leituras no Instagram, faltam {falta()}")

# ---------------------------------------------------------------- 4. o resto: DeepSeek com quadros + transcrição
for _ in range(3):
    if not falta():
        break
    etapa("categorize", "--metodo", "quadros", "--plataforma", "instagram", "--paralelo", "3", check=False)
    etapa("rank")
    etapa("ig_midia")
log(f"DeepSeek: {lidos('quadros%') + lidos('imagens_deepseek')} leituras, faltam {falta()}")

# ---------------------------------------------------------------- 5. análise na cópia (o site continua com data/)
etapa("analyze")
etapa("cruzar")
con = P.db()
log("FIM. Instagram:", pd.read_sql("select k.fonte, count(*) n from categorias k join videos v using(video_id) "
                                   "where v.plataforma='instagram' group by 1", con).to_dict("records"))
