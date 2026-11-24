"""Teste da interface nos dois focos, com e sem os arquivos do Foco B (fixture falsa em pasta temporária).
   cd /home/eduardo/fellow/Stone && .venv/bin/python /tmp/focos/teste_app.py"""
import json, os, sqlite3, sys, tempfile
import pandas as pd
from streamlit.testing.v1 import AppTest


def fixture(d):
    n = 40
    r = pd.DataFrame(dict(
        video_id=[f"B{i}" for i in range(n)], plataforma="instagram", tipo=["clips", "feed"] * 20, canal=[f"Loja {i % 6}" for i in range(n)],
        porte=["micro", "medio"] * 20, segmento=["alimentacao", "beleza", "pet", "varejo_moda"] * 10, titulo=None,
        descricao=[f"Promoção <b>{i}</b> do dia" for i in range(n)], publicado="2026-10-01T10:00:00", views=[None] * n,
        likes=range(n), comentarios=range(n), er=[i / 100 for i in range(n)], outlier=[None] * 5 + [1.5] * 35,
        conversa=0.1, resid=[i / 10 - 2 for i in range(n)], efeito_criador=0.2, elegivel=[1] * 30 + [0] * 10,
        top=[0] * 26 + [1] * 4 + [0] * 10, top_er_puro=[0] * 36 + [1] * 4, grupo=None, pct_intencao=[i / 80 for i in range(n)],
        url=[f"https://www.instagram.com/p/B{i}/" for i in range(n)]))
    c = sqlite3.connect(f"{d}/foco_b.db")
    r.to_sql("ranking", c, index=False)
    r[["video_id", "plataforma", "likes"]].to_sql("videos", c, index=False)
    pd.DataFrame(dict(titulo=[f"Loja {i}" for i in range(6)], plataforma="instagram", porte="micro", inscritos=range(6),
                      segmento="pet")).to_sql("canais", c, index=False)
    rub = dict(formato="oferta", mostra_produto=True, mostra_preco=False, tipo_cta="chamar_no_whatsapp",
               elementos=["a", "b"], texto="x" * 200)
    pd.DataFrame(dict(video_id=[f"B{i}" for i in range(20, 34)], grupo="top", fonte="vlm", rubrica=json.dumps(rub))).to_sql("categorias", c, index=False)
    c.close()
    pd.DataFrame(dict(plataforma="instagram", campo=["mostra_preco", "tipo_cta", "formato"], valor=["True", "chamar_no_whatsapp", "oferta"],
                      freq_top=[.5, .3, .1], freq_resto=[.2, .2, .05], lift=[2.5, 1.5, 2.0], n_top=[10, 6, 3])).to_csv(f"{d}/b_achados.csv", index=False)
    pd.DataFrame(dict(plataforma="instagram", canal=["Loja 1", "Loja 2"], porte="micro", inscritos=[900, 5000], efeito_criador=[.8, .3],
                      n_top=[2, 1], n_posts=[12, 9], segmento=["pet", "beleza"])).to_csv(f"{d}/b_perfis_destaque.csv", index=False)
    open(f"{d}/PLAYBOOK_B.md", "w").write("# Playbook B de teste\n\nConteúdo.")


def roda(nome, foco, espera, nao_espera=()):
    at = AppTest.from_file(os.path.abspath("app.py"), default_timeout=90).run()
    assert not at.exception, (nome, at.exception)
    if foco == "B":
        at.button_group(key="foco").set_value("B").run()
        assert not at.exception, (nome, at.exception)
    txt = " ".join(str(getattr(e, "value", "")) for e in at.markdown) + " ".join(str(e.value) for e in list(at.info) + list(at.caption))
    for e in espera:
        assert e in txt, (nome, "faltou", e)
    for e in nao_espera:
        assert e not in txt, (nome, "sobrou", e)
    print(f"ok  {nome}: {len(at.dataframe)} tabelas, {len(at.tabs)} abas, {txt.count('Ainda sem dados deste foco')} estados vazios")
    return at


tmp = tempfile.mkdtemp()
fixture(tmp)
A = ["Como escolhemos o top", "no controle", "Coincidem", "Evidência da casa"]
os.environ.update(FOCO_B_DIR="/nao/existe", FOCO_B_PLAYBOOK="/nao/existe/PLAYBOOK_B.md")
roda("A, sem arquivos do B", "A", A, ["Ainda sem dados deste foco", "no resto"])
at = roda("B, sem arquivos do B", "B", ["Ainda sem dados deste foco", "Como escolhemos o top", "O agente gera criativos"], ["Evidência da casa"])
assert len(at.dataframe) == 0
assert not os.path.exists("/nao/existe")
os.environ.update(FOCO_B_DIR=tmp, FOCO_B_PLAYBOOK=f"{tmp}/PLAYBOOK_B.md")
roda("A, com arquivos do B", "A", A, ["Ainda sem dados deste foco"])
at = roda("B, com arquivos do B", "B", ["Coincidem", "0 de 4", "frágil", "no controle", "Playbook B de teste", "intenção de compra",
                                       "&lt;b&gt;"[:0] or "Como ler"], ["Ainda sem dados deste foco", "Evidência da casa", "confirmado"])
cols = [list(d.value.columns) for d in at.dataframe]
assert "pct_intencao" in cols[0] and "r_tipo_cta" in cols[0] and "views" not in cols[0] and "r_texto" not in cols[0], cols[0]
print("colunas do ranking B:", cols[0])
# Foco A com o banco fora do ar (ranking sendo recalculado): estado vazio, sem exceção
if "--sem-a" in sys.argv:
    os.environ["DATA_DIR"] = "/nao/existe"
    roda("A, sem banco", "A", ["Ainda sem dados deste foco"])
