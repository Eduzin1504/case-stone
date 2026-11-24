"""Checagens do "Avaliar meu post". Sem rede: .venv/bin/python test_avaliar.py
Ponta a ponta real (gasta chamadas do DeepSeek): AVALIAR_REAL=1 .venv/bin/python test_avaliar.py"""
import glob
import json
import os
import subprocess
import tempfile
import time

import avaliar as A

PADROES = [dict(campo="tipo_hook", valor="promessa", lift=2.0, n_top=10, selo="só mercado"),
           dict(campo="tipo_hook", valor="pergunta", lift=0.5, n_top=10, selo="só mercado"),
           dict(campo="tem_rosto", valor="False", lift=9.0, n_top=4, selo="só mercado"),
           dict(campo="gatilho_identificacao", valor="nenhum", lift=2.0, n_top=9, selo="contradito")]
CHAVES = {"foco", "plataforma", "metodo", "aviso", "rubrica", "nota", "nota_explicacao", "padroes", "notas_vs_top", "parecidos",
          "recomendacoes"}


def test_casar_e_nota():
    ps = A.casar(dict(tipo_hook="promessa", tem_rosto=False, gatilho_identificacao="nenhum"), PADROES)
    assert [p["tem"] for p in ps] == [True, False, True, True]
    assert [p["efeito"] for p in ps] == ["ajuda", "atrapalha", "ajuda", "ajuda"]
    assert [p["fragil"] for p in ps] == [False, False, True, False]
    assert ps[0]["rotulo"] == "Gancho com promessa" and ps[2]["rotulo"] == "Sem rosto na tela"
    # 50 + 10*ln(2) + metade de 10*ln(3) (lift 9 limitado a 3, frágil); o contradito não conta
    nota, txt = A.calcular_nota(ps)
    assert nota == round(50 + 6.93 + 5.49) == 62 and "não é promessa" in txt
    assert A.calcular_nota(A.casar(dict(tipo_hook="pergunta", tem_rosto=True), PADROES))[0] == 43  # 50 - 10*ln(2)
    assert A.calcular_nota(A.casar({}, PADROES))[0] == 50
    muitos = [dict(campo=f"c{i}", valor="x", lift=3.0, n_top=9, selo="só mercado") for i in range(9)]
    assert A.calcular_nota(A.casar({f"c{i}": "x" for i in range(9)}, muitos))[0] == 100  # limitada a 100


def test_derivar():
    rub = dict(generico_0a10=7)
    d = A.derivar(rub, "A", "reel", 42.0, "x" * 120)
    assert (d["generico"], d["duracao_faixa"], d["legenda_tamanho"], d["tipo_post"]) == (True, "30-60s", "media", "reel")
    assert A.derivar(rub, "A", "carrossel", None, "")["duracao_faixa"] == "sem vídeo"
    assert "tipo_post" not in A.derivar(rub, "A", None, None, "só o roteiro")  # só texto: tipo e duração desconhecidos
    b = A.derivar(dict(qualidade_producao_0a10=7, apetite_ou_desejo_0a10=6), "B", "imagem", None, "")
    assert b["producao_alta"] and not b["desejo_alto"]


def test_padroes_dos_csvs():
    for foco, plat in [("A", "instagram"), ("A", "youtube"), ("B", "instagram")]:
        ps, aviso = A.ler_padroes(foco, plat)
        assert ps and not aviso
        assert all((p["lift"] >= 1.3 or p["lift"] <= 0.75) and p["n_top"] >= 3 and p["campo"] not in A.FORA for p in ps)
    assert "instagram" in A.ler_padroes("B", "youtube")[1]  # Foco B só tem Instagram: avisa e usa o que há


def test_arquivo_ausente():
    cfg = A.FOCOS["A"]
    antigo = dict(cfg)
    try:
        cfg.update(db="data/nao_existe.db", csv="data/nao_existe.csv")
        A.base.cache_clear()
        assert A.ler_padroes("A", "instagram")[0] == [] and A.base("A") is None
        assert A.parecidos({}, "A", "instagram") == [] and A.notas_vs_top({}, "A", "instagram") == []
    finally:
        cfg.update(antigo)
        A.base.cache_clear()


def test_base_real():
    """Com os bancos do projeto: um post do top acha a si mesmo entre os parecidos e o top pontua acima do controle."""
    for foco in "AB":
        df = A.base(foco)
        if df is None:
            continue
        d = df[df.plataforma == "instagram"]
        ps, _ = A.ler_padroes(foco, "instagram")
        notas = d.apply(lambda r: A.calcular_nota(A.casar(r.to_dict(), ps))[0], axis=1)
        assert notas[d.grupo == "top"].mean() > notas[d.grupo == "controle"].mean() + 5
        r = d[d.grupo == "top"].iloc[0].to_dict()
        achados = A.parecidos(r, foco, "instagram")
        assert 1 <= len(achados) <= 4 and all(a["plataforma"] == "instagram" for a in achados)
        assert len({a["canal"] for a in achados}) == len(achados)
        assert all(0 <= n["valor"] <= 10 for n in A.notas_vs_top(r, foco, "instagram"))
        json.dumps(achados)


def test_recomendacoes_fixas():
    ps = A.casar(dict(tipo_hook="pergunta", tem_rosto=True, gatilho_identificacao="dor"), PADROES)
    recs = A.recomendacoes_fixas(ps)
    assert len(recs) == 2 and "Gancho com pergunta" in recs[0] and "Sem rosto na tela" in recs[1] and "vale testar" in recs[1]
    assert A.recomendacoes_fixas(A.casar(dict(tipo_hook="promessa"), PADROES))[0].startswith('Teste "Sem rosto')  # não troca o gancho que já acerta


def test_separar():
    assert A.separar([("a.MP4", b"x")])[0] == "video" and A.separar([("a.png", b"x"), ("b.jpg", b"x")])[0] == "imagens"
    assert A.separar([]) == ("texto", [])
    for ruim in [[("a.mp4", b"x"), ("b.jpg", b"x")], [("a.pdf", b"x")], [(f"{i}.jpg", b"x") for i in range(11)]]:
        try:
            A.separar(ruim)
            assert False, ruim
        except ValueError:
            pass


def video_sintetico(d, s=8):
    f = f"{d}/teste.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc=duration={s}:size=1280x720:rate=15",
                    "-pix_fmt", "yuv420p", f], check=True)
    return f


def test_quadros():
    assert A.instantes(60)[:6] == [0.0, 0.5, 1.0, 1.5, 2.0, 3.0] and len(A.instantes(60)) == 12 and A.instantes(60)[-1] < 60
    assert A.instantes(0.4) == [0.0] and A.instantes(2.2) == [0.0, 0.5, 1.0, 1.5, 2.0]
    with tempfile.TemporaryDirectory() as d:
        dado = open(video_sintetico(d), "rb").read()
        qs, dur = A.quadros(dado)
        assert len(qs) == 12 and abs(dur - 8) < 0.3 and qs[0][0] == 0.0
        assert len({q for t, q in qs if t in (0.0, 1.0, 2.0, 3.0)}) == 4  # o testsrc muda a cada segundo
        open(f"{d}/q.jpg", "wb").write(qs[0][1])
        dim = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0", f"{d}/q.jpg"],
                             capture_output=True, text=True).stdout.strip()
        assert dim == "768,432", dim
        assert A.reduzir(qs[0][1])[:2] == b"\xff\xd8"
    try:
        A.quadros(b"isto nao e um video")
        assert False
    except ValueError:
        pass


def test_avaliar_sem_rede():
    """Fluxo inteiro com o modelo trocado por uma rubrica fixa: contrato de saída e fallback do vídeo e das recomendações."""
    rub = A.P.Rubrica(relevante_mpe=True, publico_alvo="donos_de_negocio", formato_video="tutorial", hook_primeiros_3s="x",
                      tipo_hook="promessa", forca_hook_0a10=7, tema_principal="finanças", tem_rosto=False,
                      criador_e_empreendedor_real=True, prova_social=False, texto_na_tela=True, ritmo_cortes_0a10=5, tom="informal",
                      usa_linguagem_regional=False, clareza_mensagem_0a10=8, tem_cta=True, tipo_cta="seguir",
                      oferta_ou_beneficio_explicito=False, convite_participacao=True, gatilho_identificacao="dor", generico_0a10=2,
                      pilar_impulso="educação financeira", elementos_top5=["a"])
    chamadas = []

    def falso(content, schema, model=None, tentativas=5):
        chamadas.append((schema.__name__, model, content))
        if model is None or schema is A.Recomendacoes:
            raise RuntimeError("sem cota")
        return rub
    original, A.P.llm = A.P.llm, falso
    etapas = []
    try:
        with tempfile.TemporaryDirectory() as d:
            dado = open(video_sintetico(d, 4), "rb").read()
        r = A.avaliar([("post.mp4", dado)], "Como separar o dinheiro da empresa", "a", usar_video=True, progresso=etapas.append)
        so_texto = A.avaliar([], "roteiro do post", "A")
    finally:
        A.P.llm = original
    assert set(r) == CHAVES and r["metodo"] == "quadros_deepseek" and "12 quadros e pela transcrição do áudio" in r["aviso"] and "RuntimeError" in r["aviso"]
    assert [c[1] for c in chamadas[:3]] == [None, A.P.N1_MODEL, A.P.N1_MODEL]  # Gemini falhou -> DeepSeek; depois recomendações
    assert sum(p["type"] == "image_url" for p in chamadas[1][2]) == 12 and "Quadro em 0.0 s (gancho)" in chamadas[1][2][0]["text"] and "ninguém fala" in chamadas[1][2][-1]["text"]
    assert r["nota"] > 60 and 3 <= len(r["recomendacoes"]) <= 5 and "Extraindo quadros e transcrevendo o áudio" in etapas and "Comparando com o top" in etapas
    assert {p["rotulo"] for p in r["padroes"] if p["tem"]} >= {"Gancho com promessa", "Tema: finanças", "Convida o público a participar"}
    assert so_texto["metodo"] == "texto_deepseek" and not any(p["tem"] for p in so_texto["padroes"] if p["campo"] == "tipo_post")
    json.dumps(r)
    try:
        A.avaliar([], "")
        assert False
    except ValueError:
        pass


def resumo(r, s):
    print(json.dumps(dict(foco=r["foco"], metodo=r["metodo"], aviso=r["aviso"], nota=r["nota"], segundos=round(s, 1),
                          tem=[f"{p['rotulo']} ({p['efeito']}, lift {p['lift']})" for p in r["padroes"] if p["tem"]],
                          notas_vs_top=[f"{n['rotulo']}: {n['valor']} x {n['mediana_top']}" for n in r["notas_vs_top"]],
                          parecidos=[f"@{p['canal']} | {p['motivo']}" for p in r["parecidos"]], recomendacoes=r["recomendacoes"],
                          gancho=r["rubrica"].get("hook_primeiros_3s") or r["rubrica"].get("gancho_3s")), ensure_ascii=False, indent=1))


def test_real():
    """Um Reel do top do Foco A (por quadros) e um carrossel do top do Foco B (imagens): devem sair acima de 50."""
    for foco, pasta, tipo in [("A", "data/midia", "video"), ("B", "data/midia_b", "imagens")]:
        top = A.top_da_base(foco)
        top = top[top.plataforma == "instagram"].sort_values("resid", ascending=False)
        for r in top.itertuples():
            fs = [f"{pasta}/{r.video_id}.mp4"] if tipo == "video" else sorted(glob.glob(f"{pasta}/{r.video_id}_*.jpg"))[:10]
            if all(os.path.exists(f) for f in fs) and (tipo == "video" or len(fs) > 1):
                break
        t = time.time()
        out = A.avaliar([(f, open(f, "rb").read()) for f in fs], r.descricao or "", foco, progresso=lambda s: print("  ..", s))
        print(f"\n== Foco {foco}: {r.video_id} (@{r.channel_id}), {len(fs)} arquivo(s)")
        resumo(out, time.time() - t)
        assert set(out) == CHAVES and out["metodo"] == ("quadros_deepseek" if tipo == "video" else "imagens_deepseek")
        assert out["nota"] > 50 and 3 <= len(out["recomendacoes"]) <= 5 and out["parecidos"]


if __name__ == "__main__":
    for nome, fn in list(globals().items()):
        if nome.startswith("test_") and (nome != "test_real" or os.getenv("AVALIAR_REAL")):
            fn()
            print("ok", nome)
