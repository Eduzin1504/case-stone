"""Gera src/api/exemplos/base.json com uma amostra REAL dos bancos (somente leitura) e copia
algumas miniaturas para public/exemplos. Rodar da raiz do projeto:
    .venv/bin/python web/scripts/gerar_exemplos.py
Não é parte do app: só refaz os dados de exemplo usados com VITE_EXEMPLOS=1."""
import csv, json, math, os, re, shutil, sqlite3

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WEB = os.path.join(RAIZ, "web")
PUB = os.path.join(WEB, "public", "exemplos")
os.makedirs(os.path.join(PUB, "thumbs"), exist_ok=True)
os.makedirs(os.path.join(PUB, "midia"), exist_ok=True)


def db(nome):
    c = sqlite3.connect(f"file:{RAIZ}/data/{nome}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    return c


FORMATO = {"clips": "Reels", "carousel_container": "Carrossel", "feed": "Imagem", None: "Short"}
ROT = {  # campo da rubrica -> rótulo de interface
    "formato_video": "Formato", "formato": "Formato", "tema_principal": "Tema", "tipo_hook": "Gancho", "tipo_gancho": "Gancho",
    "publico_alvo": "Público", "tom": "Tom", "pilar_impulso": "Pilar do Impulso", "tipo_cta": "Chamada para ação",
    "gatilho_identificacao": "Identificação", "segmento": "Segmento", "tipo_post": "Tipo de post",
    "tem_rosto": "Tem rosto", "texto_na_tela": "Texto na tela", "prova_social": "Prova social", "tem_cta": "Chamada para ação",
    "convite_participacao": "Convite à participação", "usa_linguagem_regional": "Jeito de falar regional",
    "criador_e_empreendedor_real": "Empreendedor real", "oferta_ou_beneficio_explicito": "Oferta explícita", "generico": "Genérico",
    "mostra_produto": "Mostra o produto", "mostra_preco": "Mostra o preço", "mostra_processo": "Mostra o processo",
    "rosto_do_dono": "Rosto do dono", "cliente_aparece": "Cliente aparece", "tem_oferta_ou_prazo": "Oferta ou prazo",
    "gatilho_sazonal": "Gancho sazonal", "convida_a_responder": "Convida a responder", "duracao_faixa": "Duração",
    "legenda_tamanho": "Legenda", "producao_alta": "Produção caprichada", "desejo_alto": "Dá vontade",
}
NOTAS = {"forca_hook_0a10": "Força do gancho", "ritmo_cortes_0a10": "Ritmo dos cortes", "clareza_mensagem_0a10": "Clareza da mensagem",
         "generico_0a10": "Quão genérico (menor é melhor)", "qualidade_producao_0a10": "Qualidade da produção",
         "apetite_ou_desejo_0a10": "Vontade que desperta"}
GRUPO = {"formato_video": "Formato", "formato": "Formato", "tipo_post": "Formato", "duracao_faixa": "Formato", "legenda_tamanho": "Formato",
         "tema_principal": "Tema", "segmento": "Tema", "pilar_impulso": "Tema",
         "tipo_hook": "Gancho", "tipo_gancho": "Gancho", "gatilho_identificacao": "Gancho", "gatilho_sazonal": "Gancho"}


def limpo(v):
    return str(v).replace("_", " ")


def rub_de(txt):
    try:
        return json.loads(txt) if txt else {}
    except Exception:
        return {}


def thumb(r, vid):
    if r["plataforma"] == "youtube":
        return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
    src = f"{RAIZ}/static/thumbs/{vid}.jpg"
    if os.path.exists(src):
        shutil.copy(src, f"{PUB}/thumbs/{vid}.jpg")
        return f"/exemplos/thumbs/{vid}.jpg"
    return None


def post(r, foco, pos, com_midia=False):
    vid, rub = r["video_id"], rub_de(r["rub"])
    yt = r["plataforma"] == "youtube"
    titulo = (r["titulo"] or r["descricao"] or "").strip().split("\n")[0][:110]
    gancho = rub.get("hook_primeiros_3s") or rub.get("gancho_3s")
    resumo = dict(
        id=vid, foco=foco, plataforma=r["plataforma"], formato=FORMATO.get(r["tipo"], "Short" if yt else "Imagem"),
        canal=r["canal"] or r["channel_id"], canal_id=r["channel_id"], titulo=titulo or (gancho or ""), thumb=thumb(r, vid),
        tem_video=bool(yt or r["video_url"]), er=round(r["er"], 4) if r["er"] is not None else None,
        vezes=round(math.exp(r["resid"]), 2) if r["resid"] is not None and r["elegivel"] else None,
        top=bool(r["top"]), posicao_top=pos, likes=int(r["likes"] or 0), comentarios=int(r["comentarios"] or 0),
        views=int(r["views"]) if r["views"] else None, publicado=(r["publicado"] or "")[:10] or None, gancho=gancho,
        tema=rub.get("tema_principal") or rub.get("formato"), tipo_gancho=rub.get("tipo_hook") or rub.get("tipo_gancho"),
        porte=r["porte"], url=r["url"])
    if yt:
        midia = dict(tipo="youtube", youtube_id=vid)
    elif com_midia == "imagens":
        imgs = []
        for i in range(4):
            src = f"{RAIZ}/data/{'midia' if foco == 'A' else 'midia_b'}/{vid}_{i}.jpg"
            if os.path.exists(src):
                shutil.copy(src, f"{PUB}/midia/{vid}_{i}.jpg")
                imgs.append(f"/exemplos/midia/{vid}_{i}.jpg")
        midia = dict(tipo="imagens", imagens=imgs) if imgs else dict(tipo="capa")
    else:
        midia = dict(tipo="capa") if resumo["thumb"] else dict(tipo="nenhuma")
    leitura = [dict(rotulo=ROT[k], valor=limpo(v)) for k, v in rub.items()
               if k in ROT and isinstance(v, str) and v and v != "nenhum"]
    marcas = [ROT[k] for k, v in rub.items() if k in ROT and v is True]
    return dict(resumo=resumo, extra=dict(
        midia=midia, legenda=(r["descricao"] or "")[:900], leitura=leitura, marcas=marcas,
        notas={k: rub[k] for k in NOTAS if isinstance(rub.get(k), (int, float))},
        elementos=rub.get("elementos_top5") or [], duracao_s=r["duracao_s"],
        pct_intencao=(r["pct_intencao"] if "pct_intencao" in r.keys() else None), rub=rub))


SQL = """select r.*, k.rubrica rub from ranking r left join categorias k using(video_id)
         where r.plataforma=? and r.top=? and r.elegivel=1 {extra} order by {ordem} limit ?"""


def amostra(c, foco, planos):
    out = []
    for plat, top, n, ordem, extra in planos:
        rows = c.execute(SQL.format(ordem=ordem, extra=extra), (plat, top, n)).fetchall()
        for i, r in enumerate(rows):
            out.append(post(r, foco, i + 1 if top else None,
                            com_midia="imagens" if r["tipo"] in ("carousel_container", "feed") and i < 3 else False))
    return out


def medianas(c, campos):
    import statistics
    vals = {k: [] for k in campos}
    for (t,) in c.execute("select k.rubrica from ranking r join categorias k using(video_id) where r.top=1"):
        rb = rub_de(t)
        for k in campos:
            if isinstance(rb.get(k), (int, float)):
                vals[k].append(rb[k])
    return {k: statistics.median(v) if v else None for k, v in vals.items()}


def criadores(c, foco, posts):
    ids = list(dict.fromkeys(p["resumo"]["canal_id"] for p in posts))
    out = {}
    for cid in ids:
        rows = c.execute("select video_id,publicado,er,resid,top,elegivel,canal,inscritos,porte,segmento,plataforma from ranking "
                         "where channel_id=? order by publicado", (cid,)).fetchall()
        if not rows:
            continue
        r0 = rows[0]
        res = sorted(r["resid"] for r in rows if r["resid"] is not None and r["elegivel"])
        meus = [p["resumo"] for p in posts if p["resumo"]["canal_id"] == cid]
        desc = c.execute("select descricao from canais where channel_id=?", (cid,)).fetchone()
        out[cid] = dict(
            resumo=dict(id=cid, foco=foco, nome=r0["canal"] or cid, plataforma=r0["plataforma"], seguidores=int(r0["inscritos"] or 0),
                        porte=r0["porte"], vezes=round(math.exp(res[len(res) // 2]), 2) if res else None,
                        n_top=sum(1 for r in rows if r["top"]), n_posts=len(rows), tema=meus[0]["tema"], formato=meus[0]["formato"],
                        thumbs=[p["thumb"] for p in meus if p["thumb"]][:3],
                        url=(f"https://www.youtube.com/channel/{cid}" if r0["plataforma"] == "youtube" else f"https://www.instagram.com/{cid}/")),
            bio=(desc[0] if desc and desc[0] else "")[:400],
            serie=[dict(id=r["video_id"], data=(r["publicado"] or "")[:10], er=round(r["er"] or 0, 4),
                        vezes=round(math.exp(r["resid"]), 2) if r["resid"] is not None and r["elegivel"] else None, top=bool(r["top"]))
                   for r in rows[-60:]])
    return out


def padroes(caminho, col_resto="freq_resto"):
    out = []
    for l in csv.DictReader(open(caminho, encoding="utf-8")):
        if not l.get("campo"):
            continue
        campo, valor = l["campo"], l["valor"]
        nome = ROT.get(campo, limpo(campo))
        rot = (nome if valor == "True" else f"Sem {nome[0].lower() + nome[1:]}" if valor == "False" else f"{nome}: {limpo(valor)}")
        lift = float(l["lift"]) if l["lift"] not in ("", "nan") else None
        out.append(dict(plataforma=l["plataforma"], campo=campo, valor=valor, rotulo=rot, grupo=GRUPO.get(campo, "Elementos"),
                        freq_top=float(l["freq_top"]), freq_controle=float(l[col_resto]), lift=lift, n_top=int(float(l["n_top"])),
                        selo=l.get("selo") or None, fragil=int(float(l["n_top"])) < 5))
    return out


def temas(c):
    cont = {}
    for grupo, t in c.execute("select r.grupo, k.rubrica from ranking r join categorias k using(video_id) where r.grupo in ('top','controle')"):
        rb = rub_de(t)
        tema = rb.get("tema_principal") or rb.get("formato")
        if tema:
            cont.setdefault(tema, {"top": 0, "controle": 0})[grupo] += 1
    nt = sum(v["top"] for v in cont.values()) or 1
    nc = sum(v["controle"] for v in cont.values()) or 1
    return sorted([dict(tema=k, n_top=v["top"], n_controle=v["controle"], pct_top=round(v["top"] / nt, 3),
                        lift=round((v["top"] / nt) / (v["controle"] / nc), 2) if v["controle"] else None) for k, v in cont.items()],
                  key=lambda d: -d["n_top"])


def esperado_real(c, n=260):
    pts = []
    q = "select video_id,canal,likes,comentarios,resid,top from ranking where elegivel=1 and resid is not null and {} limit ?"
    for r in list(c.execute(q.format("top=1 order by resid desc"), (120,))) + list(c.execute(q.format("top=0 order by video_id"), (n,))):
        real = (r["likes"] or 0) + (r["comentarios"] or 0)
        if real > 0:
            pts.append(dict(id=r["video_id"], canal=r["canal"], esperado=round(real / math.exp(r["resid"]), 2), real=real, top=bool(r["top"])))
    return pts


def cenas(roteiro):
    out = []
    for linha in [l.strip() for l in roteiro.split("\n") if l.strip()]:
        m = re.match(r"^(Slide\s*\d+[^:]*|\d+\s*[-–]\s*\d+\s*s)\s*[:|]\s*(.+)$", linha)
        out.append(dict(n=len(out) + 1, tempo=m.group(1) if m else None, texto=m.group(2) if m else linha))
    return out


def resposta(i, modo, pergunta, segmento, saida, em, prefixo):
    return dict(id=f"{prefixo}-{i + 1}", em=em, modo=modo, pergunta=pergunta, segmento=segmento,
                achados=[dict(selo=f.get("selo"), campo=f["campo"], valor=str(f["valor"]), rotulo=f"{ROT.get(f['campo'], limpo(f['campo']))}: {limpo(f['valor'])}",
                              freq_top=f["freq_top"], freq_controle=f["freq_resto"], lift=f["lift"], n_top=f["n_top"]) for f in saida["findings"][:6]],
                referencias_ids=[r["video_id"] for r in saida["reference_posts"][:6]],
                criativos=[dict(c, cenas=cenas(c["roteiro"])) for c in saida["creatives"]],
                explicacao=saida["explanation"], baixa_confianca=bool(saida.get("confidence_flag")),
                filtros_relaxados=saida.get("filtros_relaxados") or [])


a, b = db("stone.db"), db("foco_b.db")
posts_a = amostra(a, "A", [("youtube", 1, 16, "r.resid desc", ""), ("instagram", 1, 12, "r.resid desc", ""),
                           ("youtube", 0, 6, "r.video_id", "and k.rubrica is not null"), ("instagram", 0, 4, "r.video_id", "and k.rubrica is not null")])
posts_b = amostra(b, "B", [("instagram", 1, 10, "r.resid desc", "and k.rubrica is not null"), ("instagram", 0, 4, "r.video_id", "and k.rubrica is not null")])

# um vídeo local pequeno para demonstrar <video> sem a API
vid_demo = None
for p in posts_a:
    src = f"{RAIZ}/data/midia/{p['resumo']['id']}.mp4"
    if p["resumo"]["plataforma"] == "instagram" and os.path.exists(src) and os.path.getsize(src) < 4_000_000:
        shutil.copy(src, f"{PUB}/midia/{p['resumo']['id']}.mp4")
        p["extra"]["midia"] = dict(tipo="video", video_url=f"/exemplos/midia/{p['resumo']['id']}.mp4")
        vid_demo = p["resumo"]["id"]
        break

def base_de(c):
    por = dict(c.execute("select plataforma,count(*) from ranking group by 1").fetchall())
    return dict(posts=sum(por.values()), criadores=c.execute("select count(distinct channel_id) from ranking").fetchone()[0],
                top=c.execute("select count(*) from ranking where top=1").fetchone()[0],
                por_plataforma=dict(instagram=por.get("instagram", 0), youtube=por.get("youtube", 0)),
                coletado_em=(c.execute("select max(coletado_em) from ranking").fetchone()[0] or "")[:10])

com = b.execute("select texto from comentarios where intencao=1 and length(texto) between 12 and 90 limit 8").fetchall()
fun = b.execute("select sum(likes), sum(comentarios) from ranking where elegivel=1").fetchone()
intenc = b.execute("select count(*) from comentarios where intencao=1").fetchone()[0]
lidos = b.execute("select count(*) from comentarios").fetchone()[0]
por_fmt = {}
for t, pct in b.execute("select k.rubrica, r.pct_intencao from ranking r join categorias k using(video_id) where r.pct_intencao is not null"):
    por_fmt.setdefault(rub_de(t).get("formato", "outro"), []).append(pct)

pb = open(f"{RAIZ}/PLAYBOOK.md", encoding="utf-8").read()
partes = re.split(r"\n(?=## )", pb)
caps = [dict(id=f"cap-{i}", titulo=p.split("\n")[0].lstrip("# ").strip(), markdown="\n".join(p.split("\n")[1:]).strip()[:2500])
        for i, p in enumerate(partes[1:], 1)]

crs = json.load(open(f"{RAIZ}/data/criativos_playbook.json", encoding="utf-8"))
salvas = [json.loads(l) for l in open(f"{RAIZ}/data/execucoes.jsonl", encoding="utf-8")][-3:]

json.dump(dict(
    gerado_de="data/stone.db, data/foco_b.db, data/padroes_selados.csv, data/b_achados.csv, PLAYBOOK.md (amostra)",
    video_demo=vid_demo,
    focos=dict(A=base_de(a), B=base_de(b)),
    posts=dict(A=posts_a, B=posts_b),
    criadores=dict(A=criadores(a, "A", posts_a), B=criadores(b, "B", posts_b)),
    medianas=dict(A=medianas(a, ["forca_hook_0a10", "ritmo_cortes_0a10", "clareza_mensagem_0a10", "generico_0a10"]),
                  B=medianas(b, ["qualidade_producao_0a10", "apetite_ou_desejo_0a10"])),
    rotulos_notas=NOTAS,
    padroes=dict(A=padroes(f"{RAIZ}/data/padroes_selados.csv"), B=padroes(f"{RAIZ}/data/b_achados.csv")),
    temas=dict(A=temas(a), B=temas(b)),
    esperado_real=dict(A=esperado_real(a), B=esperado_real(b, 200)),
    funil=dict(etapas=[dict(rotulo="Curtidas", valor=int(fun[0] or 0)), dict(rotulo="Comentários", valor=int(fun[1] or 0)),
                       dict(rotulo="Comentários lidos", valor=lidos), dict(rotulo="Comentários com intenção de compra", valor=intenc)],
               por_formato=sorted([dict(formato=k, pct_intencao=round(sum(v) / len(v), 3), n=len(v)) for k, v in por_fmt.items()],
                                  key=lambda d: -d["pct_intencao"]),
               comentarios=[dict(texto=r[0], negocio="") for r in com]),
    kappa=[dict(campo=ROT.get(l["campo"], limpo(l["campo"])), concordancia=float(l["concordancia"]), kappa=float(l["kappa"]))
           for l in csv.DictReader(open(f"{RAIZ}/data/validacao_resultado.csv", encoding="utf-8"))],
    playbook=dict(titulo=partes[0].split("\n")[0].lstrip("# ").strip(), capitulos=caps),
    criativos=[resposta(i, "gerar_criativo", c["pedido"], c.get("segmento"), c, "2026-11-23T20:45:00", "criativo") for i, c in enumerate(crs)],
    salvas=[resposta(i, e["entrada"]["mode"], e["entrada"]["query"], e["entrada"].get("segment"), e["saida"], e["em"], "salva") for i, e in enumerate(salvas)],
), open(f"{WEB}/src/api/exemplos/base.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok", len(posts_a), len(posts_b), "video demo:", vid_demo)
