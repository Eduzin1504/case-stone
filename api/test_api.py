"""Testes da API do Pauta Impulso, sem rede: .venv/bin/python api/test_api.py  (também roda com pytest).

Usa os bancos reais (só leitura) e um data/app.db temporário. /avaliar e /agente rodam com dublês."""
import io
import re
import os
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
TMP = tempfile.mkdtemp(prefix="pauta_teste_")
os.environ["PAUTA_APP_DB"] = f"{TMP}/app.db"
os.environ["PAUTA_AVALIACOES"] = f"{TMP}/avaliacoes"

from fastapi.testclient import TestClient  # noqa: E402

from api import dados  # noqa: E402
from api.app import app  # noqa: E402

c = TestClient(app, raise_server_exceptions=False)
N = type(None)
NUM = (int, float)
RESUMO = dict(id=str, foco=str, plataforma=str, formato=str, canal=str, canal_id=str, titulo=str, thumb=(str, N),
              tem_video=bool, er=(*NUM, N), vezes=(*NUM, N), top=bool, posicao_top=(int, N), likes=int, comentarios=int,
              views=(int, N), publicado=(str, N), gancho=(str, N), tema=(str, N), tipo_gancho=(str, N), porte=(str, N), url=str)
CRIADOR = dict(id=str, foco=str, nome=str, plataforma=str, seguidores=int, porte=str, vezes=(*NUM, N), n_top=int,
               n_posts=int, tema=(str, N), formato=(str, N), thumbs=list, url=str)
DETALHE = dict(RESUMO, midia=dict, legenda=str, leitura=list, notas=list, elementos=list, criador=(dict, N), parecidos=list,
               pct_intencao=(*NUM, N), metodo_leitura=(str, N))
TRABALHO = dict(estado=str, etapas=list, resultado=(dict, N), erro=(str, N))
AGENTE = dict(id=str, em=str, modo=str, pergunta=str, segmento=(str, N), achados=list, referencias=list, criativos=list,
              explicacao=str, baixa_confianca=bool, filtros_relaxados=list)
ACHADO = dict(selo=(str, N), campo=str, valor=str, rotulo=str, freq_top=NUM, freq_controle=NUM, lift=(*NUM, N), n_top=int)
COLECAO = dict(id=str, nome=str, nota=str, foco=str, posts=list, criada_em=str)


def forma(d, spec):
    """Toda chave prometida existe e tem o tipo básico certo."""
    assert isinstance(d, dict), d
    for chave, tipo in spec.items():
        assert chave in d, f"falta a chave {chave!r} em {list(d)}"
        assert isinstance(d[chave], tipo), f"{chave}={d[chave]!r} não é {tipo}"
        assert not (isinstance(d[chave], bool) and tipo in (int, NUM)), f"{chave} veio booleano"
    return d


def formas(lista, spec):
    assert isinstance(lista, list)
    return [forma(x, spec) for x in lista]


def ok(rota, **params):
    r = c.get("/api" + rota, params=params)
    assert r.status_code == 200, f"{rota} {params}: {r.status_code} {r.text[:300]}"
    return r.json()


def erro(r, status):
    assert r.status_code == status, f"{r.status_code} {r.text[:300]}"
    assert isinstance(r.json().get("erro"), str) and r.json()["erro"]


def um_post(foco, **filtros):
    return ok("/posts", foco=foco, limit=1, **filtros)["itens"][0]


def esperar(rota, tid):
    for _ in range(200):
        t = forma(ok(f"{rota}/{tid}"), TRABALHO)
        if t["estado"] != "rodando":
            return t
        time.sleep(0.05)
    raise AssertionError("o trabalho não terminou")


# ---------------------------------------------------------------- leitura, nos dois focos
def test_saude_e_focos():
    assert ok("/saude") == {"ok": True}
    fs = formas(ok("/focos"), dict(id=str, nome=str, descricao=str, pergunta=str, base=dict))
    assert [f["id"] for f in fs] == ["A", "B"]
    for f in fs:
        forma(f["base"], dict(posts=int, criadores=int, top=int, por_plataforma=dict, coletado_em=(str, N)))
        forma(f["base"]["por_plataforma"], dict(instagram=int, youtube=int))
        assert f["base"]["posts"] > 0 and f["base"]["top"] > 0


def test_posts():
    for foco in "AB":
        p = forma(ok("/posts", foco=foco), dict(total=int, itens=list, filtros=dict))
        forma(p["filtros"], dict(plataformas=list, formatos=list, temas=list, portes=list))
        formas(p["itens"], RESUMO)
        assert len(p["itens"]) == 24 and p["total"] > 24
        assert all(x["foco"] == foco for x in p["itens"])
        for ordem in ("destaques", "vezes", "er", "comentarios", "recentes"):
            formas(ok("/posts", foco=foco, ordem=ordem, limit=5)["itens"], RESUMO)
        v = [x["vezes"] for x in ok("/posts", foco=foco, ordem="vezes", limit=30)["itens"]]
        assert v == sorted(v, reverse=True)
        topo = ok("/posts", foco=foco, so_top="true", com_video="true", limit=200)
        assert topo["itens"] and all(x["top"] and x["tem_video"] and x["posicao_top"] for x in topo["itens"])
        f = p["filtros"]
        assert f["portes"] == ["micro", "medio", "grande"]
        assert ok("/posts", foco=foco, porte="médio")["total"] == ok("/posts", foco=foco, porte="medio")["total"] > 0
        d = ok("/posts", foco=foco, plataforma=f["plataformas"][0], formato=f["formatos"][0], tema=f["temas"][0], porte=f["portes"][0])
        assert all(x["plataforma"] == f["plataformas"][0] and x["formato"] == f["formatos"][0] and x["tema"] == f["temas"][0]
                   and x["porte"] == f["portes"][0] for x in d["itens"])
        pag = ok("/posts", foco=foco, offset=24, limit=3)["itens"]
        assert pag and pag[0]["id"] not in {x["id"] for x in p["itens"]}
        assert ok("/posts", foco=foco, q="zzzzqqqxx")["total"] == 0
    assert ok("/posts", foco="A", q="finanças")["total"] > 0
    erro(c.get("/api/posts", params=dict(foco="C")), 400)
    erro(c.get("/api/posts", params=dict(ordem="sorte")), 400)
    erro(c.get("/api/posts", params=dict(limit="muitos")), 400)


def test_vezes_e_thumb():
    """vezes = exp(resid); null quando não concorre; miniatura do YouTube no formato do contrato."""
    import math
    R = dados.ranking("A")
    com, sem = R[R.resid.notna()].iloc[0], R[R.resid.isna()].iloc[0]
    assert abs(ok(f"/posts/{com.video_id}")["vezes"] - math.exp(com.resid)) < 0.01
    d = ok(f"/posts/{sem.video_id}")
    assert d["vezes"] is None and d["posicao_top"] is None and not d["top"]
    yt = um_post("A", plataforma="youtube")
    assert yt["thumb"] == f"https://i.ytimg.com/vi/{yt['id']}/hqdefault.jpg"
    ig = um_post("A", plataforma="instagram")
    assert ig["thumb"].startswith("/midia/thumbs/") and c.get(ig["thumb"]).status_code == 200


def test_detalhe_e_midia():
    for foco in "AB":
        p = um_post(foco, so_top="true", plataforma="instagram", com_video="true")
        d = forma(ok(f"/posts/{p['id']}", foco=foco), DETALHE)
        forma(d["midia"], dict(tipo=str))
        assert d["midia"]["tipo"] == "video" and c.get(d["midia"]["video_url"], headers={"Range": "bytes=0-99"}).status_code == 206
        formas(d["leitura"], dict(rotulo=str, valor=str))
        formas(d["notas"], dict(rotulo=str, valor=NUM, mediana_top=(*NUM, N)))
        assert d["leitura"] and d["notas"] and d["elementos"] and all(isinstance(x, str) for x in d["elementos"])
        forma(d["criador"], CRIADOR)
        formas(d["parecidos"], RESUMO)
        assert not any("_" in x["rotulo"] for x in d["leitura"] + d["notas"]), "rótulo cru na leitura"
        erro(c.get("/api/posts/nao-existe", params=dict(foco=foco)), 404)
        erro(c.get("/api/posts/..%2F..%2Fapp.py", params=dict(foco=foco)), 404)
    yt = ok(f"/posts/{um_post('A', plataforma='youtube')['id']}")
    assert yt["midia"] == dict(tipo="youtube", youtube_id=yt["id"])
    assert isinstance(ok(f"/posts/{um_post('B', so_top='true')['id']}", foco="B")["pct_intencao"], (*NUM, N))


def test_destaques_e_busca():
    for foco in "AB":
        ds = formas(ok("/destaques", foco=foco, limit=8), dict(post=dict, porque=str))
        assert len(ds) == 8 and all(forma(d["post"], RESUMO)["top"] and d["post"]["thumb"] and "esperado" in d["porque"] for d in ds)
        assert len({d["post"]["canal"] for d in ds}) == 8, "um post por criador"
        bs = formas(ok("/busca", foco=foco, q="promoção de Natal", limit=5), dict(post=dict, score=NUM, casou=list))
        assert bs and all(forma(b["post"], RESUMO) and b["casou"] and 0 < b["score"] <= 1 for b in bs)
        peso = [b["score"] * (dados.BONUS_TOP if b["post"]["top"] else 1) for b in bs]
        assert peso == sorted(peso, reverse=True), "ordem = semelhança, com desempate a favor do top"
        so = ok("/busca", foco=foco, q="promoção de Natal venda cliente", so_top="true", limit=50)
        assert all(b["post"]["top"] for b in so)
        assert ok("/busca", foco=foco, q="") == [] and ok("/busca", foco=foco, q="xqzwv") == []
    assert "promoção" in ok("/busca", foco="B", q="PROMOCAO")[0]["casou"] or ok("/busca", foco="B", q="PROMOCAO")[0]["casou"] == ["promocao"]
    assert len({d["post"]["plataforma"] for d in ok("/destaques", foco="A", limit=4)}) == 2, "alterna plataformas"


def test_criadores_e_rankings():
    for foco in "AB":
        cs = formas(ok("/criadores", foco=foco), CRIADOR)
        v = [x["vezes"] for x in cs if x["vezes"] is not None]
        assert cs and v == sorted(v, reverse=True)
        assert all(x["plataforma"] == "instagram" for x in ok("/criadores", foco=foco, plataforma="instagram", porte="micro"))
        cr = forma(ok(f"/criadores/{cs[0]['id']}", foco=foco), dict(resumo=dict, bio=str, posts=list, serie=list))
        forma(cr["resumo"], CRIADOR)
        formas(cr["posts"], RESUMO)
        formas(cr["serie"], dict(id=str, data=(str, N), er=(*NUM, N), vezes=(*NUM, N), top=bool))
        assert len(cr["posts"]) == cr["resumo"]["n_posts"] == len(cr["serie"])
        erro(c.get("/api/criadores/ninguem", params=dict(foco=foco)), 404)
        for tipo in ("posts", "criadores"):
            for metrica in ("vezes", "er", "comentarios"):
                rk = formas(ok("/rankings", foco=foco, tipo=tipo, metrica=metrica, limit=10),
                            dict(posicao=int, id=str, nome=str, sub=str, thumb=(str, N), valor=NUM, valor_fmt=str))
                assert [x["posicao"] for x in rk] == list(range(1, len(rk) + 1)) and rk
                assert [x["valor"] for x in rk] == sorted((x["valor"] for x in rk), reverse=True)
        assert ok("/rankings", foco=foco, plataforma="instagram", porte="micro", limit=3)
        assert all(isinstance(x["thumbs"], list) and len(x["thumbs"]) <= 3 for x in ok("/rankings", foco=foco, tipo="criadores"))
        erro(c.get("/api/rankings", params=dict(foco=foco, tipo="lojas")), 400)


def test_comparar():
    for foco in "AB":
        a, b = (x["id"] for x in ok("/posts", foco=foco, so_top="true", limit=2)["itens"])
        r = forma(ok("/comparar", foco=foco, a=a, b=b), dict(a=dict, b=dict, diferencas=list))
        forma(r["a"], DETALHE), forma(r["b"], DETALHE)
        formas(r["diferencas"], dict(rotulo=str, a=str, b=str, igual=bool))
        assert r["a"]["id"] == a and len(r["diferencas"]) > 8
        erro(c.get("/api/comparar", params=dict(foco=foco, a=a, b="nao-existe")), 404)
    erro(c.get("/api/comparar", params=dict(a="x")), 400)


def test_padroes_e_ads():
    padrao = dict(campo=str, valor=str, rotulo=str, grupo=str, freq_top=NUM, freq_controle=NUM, lift=(*NUM, N), n_top=int,
                  selo=(str, N), fragil=bool, exemplos=list)
    for foco in "AB":
        p = forma(ok("/padroes", foco=foco), dict(plataformas=list, itens=list))
        assert p["plataformas"][0] == "instagram" and formas(p["itens"], padrao)
        assert any(formas(x["exemplos"], RESUMO) for x in p["itens"])
        assert all(x["fragil"] == (x["n_top"] < 5) for x in p["itens"])
    assert any(x["selo"] == "confirmado" for x in ok("/padroes", foco="A", plataforma="todas")["itens"])
    assert ok("/padroes", foco="A", plataforma="youtube")["itens"]
    ads = formas(ok("/ads"), dict(criativo=str, formato=(str, N), ctr=NUM, desempenho=(str, N), confirma=list))
    rotulos = {x["rotulo"] for x in ok("/padroes", foco="A", plataforma="todas")["itens"] if x["selo"] == "confirmado"}
    assert any(a["confirma"] for a in ads) and all(set(a["confirma"]) <= rotulos for a in ads)


def test_viz():
    for foco in "AB":
        er = forma(ok("/viz/esperado-real", foco=foco), dict(pontos=list, nota=str))
        pts = formas(er["pontos"], dict(id=str, canal=str, esperado=NUM, real=NUM, top=bool))
        assert 0 < len(pts) <= 1500 and all(p["real"] > 0 and p["esperado"] > 0 for p in pts)
        R = dados.ranking(foco)
        n_top = int((R.top & R.resid.notna() & ((R.likes.fillna(0) + R.comentarios.fillna(0)) > 0)).sum())
        assert sum(p["top"] for p in pts) == n_top, "todos os do top entram"
        assert er == ok("/viz/esperado-real", foco=foco), "amostra com seed fixa"
        ts = formas(ok("/viz/temas", foco=foco), dict(tema=str, n_top=int, n_controle=int, pct_top=NUM, lift=(*NUM, N)))
        assert ts and abs(sum(t["pct_top"] for t in ts) - 1) < 0.02
        p = um_post(foco, so_top="true", com_video="true", plataforma="instagram")
        an = forma(ok(f"/viz/anatomia/{p['id']}", foco=foco), dict(post=dict, duracao_s=(*NUM, N), trechos=list))
        tr = formas(an["trechos"], dict(rotulo=str, texto=str, inicio_s=NUM, fim_s=NUM, aproximado=bool))  # vídeo: tem duração
        assert forma(an["post"], RESUMO) and tr[0]["inicio_s"] == 0 and tr[0]["fim_s"] <= 3 and tr[0]["texto"] == p["gancho"]
        assert all(t["aproximado"] for t in tr[1:]), "sem tempo medido = aproximado"
        assert all(0 <= t["inicio_s"] <= t["fim_s"] <= an["duracao_s"] for t in tr) and tr[-1]["fim_s"] == an["duracao_s"]
        img = ok(f"/viz/anatomia/{um_post(foco, so_top='true', formato='Carrossel')['id']}", foco=foco)
        assert img["duracao_s"] is None and all(t["fim_s"] is None and t["aproximado"] for t in img["trechos"][1:])
        erro(c.get("/api/viz/anatomia/nao-existe", params=dict(foco=foco)), 404)
        fu = forma(ok("/viz/funil", foco=foco), dict(etapas=list, por_formato=list, preco=dict, comentarios=list))
        forma(fu["preco"], dict(com=(*NUM, N), sem=(*NUM, N), n_com=int, n_sem=int))
    assert ok("/viz/esperado-real", foco="A", plataforma="youtube")["pontos"][0]["id"] in dados.ranking("A").index
    fu = ok("/viz/funil")  # o padrão é o Foco B
    et = [e["valor"] for e in formas(fu["etapas"], dict(rotulo=str, valor=int))]
    assert len(et) == 4 and et == sorted(et, reverse=True) and et[-1] > 0
    assert formas(fu["por_formato"], dict(formato=str, pct_intencao=NUM, n=int))
    assert fu["preco"]["com"] > fu["preco"]["sem"] > 0
    for f in formas(fu["comentarios"], dict(texto=str, negocio=str)):
        assert "@" not in f["texto"] and not any(ch.isdigit() for ch in f["texto"]) and "autor" not in f
    assert ok("/viz/funil", foco="A")["etapas"] == []


def test_playbook_metodo_criativos():
    for foco in "AB":
        pb = forma(ok("/playbook", foco=foco), dict(titulo=str, linha_fina=str, atualizado=str, leitura_min=int, capitulos=list))
        assert len(formas(pb["capitulos"], dict(id=str, titulo=str, markdown=str))) >= 6
        assert ("comentarios" in pb) == (foco == "B")
        m = forma(ok("/metodo", foco=foco), dict(passos=list, numeros=list, avaliacao_md=str, limitacoes=list, kappa=list))
        assert len(formas(m["passos"], dict(titulo=str, texto=str))) == 4 and m["avaliacao_md"]
        assert formas(m["numeros"], dict(rotulo=str, valor=str)) and len(m["limitacoes"]) >= 3
        assert all(isinstance(x, str) and len(x) > 20 and "**" not in x for x in m["limitacoes"])
        formas(m["kappa"], dict(campo=str, concordancia=NUM, kappa=NUM))
    assert formas(ok("/playbook", foco="B")["comentarios"], dict(texto=str, negocio=str))
    assert len(ok("/metodo", foco="A")["kappa"]) == 8
    cri = formas(ok("/criativos"), AGENTE)
    assert len(cri) == 5
    for x in cri:
        assert formas(x["referencias"], RESUMO) and x["pergunta"]
        cr = forma(x["criativos"][0], dict(formato=str, pilar=str, gancho=str, roteiro=str, legenda=str, cta=str, cenas=list))
        cenas = formas(cr["cenas"], dict(n=int, tempo=str, texto=str))
        assert len(cenas) >= 4 and [s["n"] for s in cenas] == list(range(1, len(cenas) + 1)) and all(s["tempo"] and s["texto"] for s in cenas)


def test_cenas():
    assert [(s["tempo"], s["texto"]) for s in dados.cenas("0-3s | GANCHO: oi\n3-10s: mostra o caixa\ne segue falando")] == \
        [("0-3s", "oi"), ("3-10s", "mostra o caixa e segue falando")]
    uma_linha = dados.cenas('Slide 1 (capa): "Seu preço cobre tudo?" / Slide 2 (dor real): "O dinheiro some."')
    assert [(s["tempo"], s["rotulo"]) for s in uma_linha] == [("Slide 1", "capa"), ("Slide 2", "dor real")]
    assert dados.cenas("texto solto, sem marcação")[0]["n"] == 1 and dados.cenas("") == []


# ---------------------------------------------------------------- agente e avaliar (dublês, sem rede)
def test_agente():
    import agent
    salvas = formas(ok("/agente/salvas"), AGENTE)
    assert salvas and any(s["criativos"] and s["criativos"][0]["cenas"] for s in salvas)
    assert any(formas(s["referencias"], RESUMO) and formas(s["achados"], ACHADO) for s in salvas)
    assert not any(re.search(r"[a-z]_[a-z]|\blift\b| — ", re.sub(r"\[[^\]]*\]", "", s["explicacao"])) for s in salvas + ok("/criativos"))
    assert dados.explicar("`gatilho_identificacao = pessoa_real` (lift 1.87, n_top 31) e tem_rosto=False") == \
        "identificação: pessoa real (1,87× mais no top, 31 posts do top) e tem rosto: não"
    op = forma(ok("/agente/opcoes"), dict(segmentos=list, pilares=list))
    assert "beleza" in op["segmentos"] and "comunidade" in op["pilares"]
    ref = dados.ranking("A").index[0]
    pedidos = []

    def falso(mode, query, segment=None, filters=None):
        pedidos.append((mode, query, segment, filters))
        return dict(filtros_relaxados=[], findings=[], confidence_flag=False, explanation="porque sim",
                    reference_posts=[dict(plataforma="youtube", video_id=ref, url="", canal="x", titulo="t", er=0.1, outlier=None, categorias={})],
                    creatives=[dict(formato="reel", pilar="comunidade", gancho="g", legenda="l", cta="c", inspirado_em=[ref],
                                    roteiro="0-3s | Gancho: abre\n3-10s: desenvolve")])
    original, agent.run = agent.run, falso
    try:
        r = c.post("/api/agente", json=dict(modo="gerar_criativo", pergunta="Reels de Natal", segmento="todos", filtros=dict(porte="micro", pilar="todos")))
        assert r.status_code == 200
        t = esperar("/agente", r.json()["id"])
    finally:
        agent.run = original
    assert t["estado"] == "pronto" and len(t["etapas"]) == 2, t
    assert pedidos == [("gerar_criativo", "Reels de Natal", None, {"porte": "micro"})]
    res = forma(t["resultado"], AGENTE)
    assert res["id"] == r.json()["id"] and res["pergunta"] == "Reels de Natal" and res["explicacao"] == "porque sim"
    assert [s["tempo"] for s in res["criativos"][0]["cenas"]] == ["0-3s", "3-10s"]
    assert forma(res["referencias"][0], RESUMO)["id"] == ref
    erro(c.post("/api/agente", json=dict(modo="gerar_criativo", pergunta="  ")), 400)
    erro(c.post("/api/agente", json=dict(modo="dançar", pergunta="oi")), 400)
    erro(c.get("/api/agente/nao-existe"), 404)


def _png():
    from PIL import Image
    b = io.BytesIO()
    Image.new("RGB", (900, 1200), "#c5ff1f").save(b, "PNG")
    return b.getvalue()


def test_avaliar():
    import avaliar as A
    erro(c.post("/api/avaliar", data=dict(foco="A")), 400)  # sem arquivo e sem legenda
    erro(c.post("/api/avaliar", data=dict(legenda="oi", foco="Z")), 400)
    erro(c.post("/api/avaliar", data=dict(legenda="oi"), files=[("arquivos", ("notas.txt", b"oi", "text/plain"))]), 400)
    erro(c.post("/api/avaliar", data=dict(legenda="oi"), files=[("arquivos", (f, b"x", "video/mp4")) for f in ("a.mp4", "b.mp4")]), 400)
    erro(c.get("/api/avaliar/nao-existe"), 404)
    chamadas = []

    def falso(arquivos, legenda="", foco="A", plataforma="instagram", usar_video=False, progresso=None):
        chamadas.append(([n for n, _ in arquivos], legenda, foco, plataforma, usar_video))
        if legenda == "quebra":
            raise ValueError("não consegui ler o vídeo")
        progresso("Lendo o post com a IA")
        progresso("Comparando com o top")
        return dict(foco=foco, plataforma=plataforma, metodo="imagens_deepseek", aviso="", rubrica={}, nota=61,
                    nota_explicacao="…", padroes=[], notas_vs_top=[], recomendacoes=["Teste um gancho"],
                    parecidos=[dict(video_id=dados.ranking(foco).index[0], motivo="Em comum")])
    original, A.avaliar = A.avaliar, falso
    try:
        for foco, campo in (("A", "arquivos"), ("B", "arquivos[]")):
            r = c.post("/api/avaliar", data=dict(legenda="Promoção de Natal", foco=foco, plataforma="instagram", usar_video="true"),
                       files=[(campo, ("../../foto do post.png", _png(), "image/png"))])
            assert r.status_code == 200, r.text
            t = esperar("/avaliar", r.json()["id"])
            assert t["estado"] == "pronto" and t["etapas"][:2] == ["Lendo o post com a IA", "Comparando com o top"], t
            res = t["resultado"]
            assert res["id"] == r.json()["id"], "o id do pedido é o id no histórico"
            assert res["nota"] == 61 and forma(res["medias"], dict(top=NUM, comuns=NUM))
            assert 0 < res["medias"]["comuns"] < res["medias"]["top"] <= 100
            assert forma(res["parecidos"][0]["post"], RESUMO)
            salvo = ok(f"/avaliacoes/{res['id']}")
            assert salvo["resultado"]["nota"] == 61 and salvo["legenda"] == "Promoção de Natal" and salvo["foco"] == foco
            assert salvo["thumb"] == f"/midia/avaliacoes/{res['id']}.jpg" and c.get(salvo["thumb"]).status_code == 200
        assert chamadas[0] == (["../../foto do post.png"], "Promoção de Natal", "A", "instagram", True)
        assert sorted(os.listdir(os.environ["PAUTA_AVALIACOES"])) == sorted(f"{a['id']}.jpg" for a in ok("/avaliacoes"))
        r = c.post("/api/avaliar", json=dict(legenda="quebra", foco="A"))  # só texto, em JSON; o erro vem do avaliar
        t = esperar("/avaliar", r.json()["id"])
        assert t["estado"] == "erro" and t["erro"] == "não consegui ler o vídeo" and t["resultado"] is None
    finally:
        A.avaliar = original
    hist = formas(ok("/avaliacoes"), dict(id=str, criada_em=str, foco=str, plataforma=str, legenda=str, nota=int, thumb=(str, N), estado=str))
    assert len(hist) == 2 and "resultado" not in hist[0]
    erro(c.get("/api/avaliacoes/nao-existe"), 404)


# ---------------------------------------------------------------- coleções (data/app.db temporário)
def test_colecoes():
    assert ok("/colecoes") == []
    erro(c.post("/api/colecoes", json=dict(nome=" ", foco="A")), 400)
    col = forma(c.post("/api/colecoes", params=dict(foco="B"), json=dict(nome="Natal", nota="para dezembro")).json(), COLECAO)
    assert col["posts"] == [] and col["foco"] == "B" and col["nome"] == "Natal"
    cid, (p1, p2) = col["id"], (x["id"] for x in ok("/posts", foco="B", limit=2)["itens"])
    for p in (p1, p2, p1):  # repetir não duplica
        r = c.post(f"/api/colecoes/{cid}/posts", json=dict(post_id=p))
        assert r.status_code == 200, r.text
    assert [x["id"] for x in formas(r.json()["posts"], RESUMO)] == [p1, p2]
    erro(c.post(f"/api/colecoes/{cid}/posts", json=dict(post_id="nao-existe")), 404)
    erro(c.post(f"/api/colecoes/{cid}/posts", json=dict(post_id=dados.ranking("A").index[0])), 404)  # post de outro foco
    erro(c.post(f"/api/colecoes/{cid}/posts", json={}), 400)
    editada = forma(c.patch(f"/api/colecoes/{cid}", json=dict(nome="Natal 2026")).json(), COLECAO)
    assert editada["nome"] == "Natal 2026" and editada["nota"] == "para dezembro" and len(editada["posts"]) == 2
    assert [x["id"] for x in c.delete(f"/api/colecoes/{cid}/posts", params=dict(post_id=p1)).json()["posts"]] == [p2]  # como o front manda
    assert c.request("DELETE", f"/api/colecoes/{cid}/posts", json=dict(post_id=p2)).json()["posts"] == []
    erro(c.delete(f"/api/colecoes/{cid}/posts"), 400)
    assert forma(ok(f"/colecoes/{cid}"), COLECAO)["nome"] == "Natal 2026"
    assert [x["id"] for x in ok("/colecoes", foco="B")] == [cid] and ok("/colecoes", foco="A") == []
    assert c.delete(f"/api/colecoes/{cid}").status_code == 200
    for r in (c.get(f"/api/colecoes/{cid}"), c.delete(f"/api/colecoes/{cid}"), c.patch(f"/api/colecoes/{cid}", json=dict(nome="x")),
              c.post(f"/api/colecoes/{cid}/posts", json=dict(post_id=p1))):
        erro(r, 404)
    assert ok("/colecoes") == []
    for r in (c.get("/api/colecoes/999"), c.get("/api/colecoes/abc")):
        erro(r, 404)
        assert r.json()["erro"] == "Coleção não encontrada."
    pa = dados.ranking("A").index[0]  # post que só existe no Foco A abre pedindo o B, com o foco real
    assert ok(f"/posts/{pa}", foco="B")["foco"] == "A"


# ---------------------------------------------------------------- erros, só leitura e tempo
def test_erros_e_escrita():
    erro(c.get("/api/rota-que-nao-existe"), 404)
    fuga = c.get("/midia/a/../../.env")  # o cliente normaliza para /.env: com o site compilado, cai no index.html
    assert fuga.status_code == 404 or "text/html" in fuga.headers["content-type"]
    assert c.get("/midia/thumbs/nao-existe.jpg").status_code == 404
    r = c.options("/api/focos", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "access-control-allow-origin" not in c.get("/api/saude", headers={"Origin": "http://exemplo.com"}).headers
    try:
        dados.conectar(dados.FOCOS["A"]["db"]).execute("create table teste (x)")
        raise AssertionError("o banco principal aceitou escrita")
    except Exception as e:
        assert "readonly" in str(e), e


def test_tempo_dos_posts():
    ok("/posts", foco="A")  # aquece
    t = time.perf_counter()
    for params in (dict(), dict(q="dinheiro", ordem="vezes"), dict(plataforma="youtube", porte="micro", ordem="recentes", offset=240)):
        ok("/posts", foco="A", **params)
    ms = (time.perf_counter() - t) / 3 * 1000
    assert ms < 300, f"/posts levou {ms:.0f} ms"


if __name__ == "__main__":
    falhas = 0
    for nome, fn in list(globals().items()):
        if nome.startswith("test_"):
            t = time.perf_counter()
            try:
                fn()
                print(f"ok    {nome} ({time.perf_counter() - t:.2f}s)")
            except Exception:
                import traceback
                falhas += 1
                print(f"FALHA {nome}")
                traceback.print_exc()
    print(f"\n{falhas} falha(s)" if falhas else "\ntudo passou")
    sys.exit(1 if falhas else 0)
