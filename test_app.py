"""Teste da interface: todas as páginas, nos dois focos, com e sem os arquivos do Foco B (fixture falsa em pasta
temporária). Nenhuma página pode levantar exceção.
   cd /home/eduardo/fellow/Stone && .venv/bin/python test_app.py"""
import json, os, sqlite3, sys, tempfile
import pandas as pd
from streamlit.testing.v1 import AppTest

PAGINAS = ["visao", "catalogo", "rankings", "padroes", "avaliar_post", "agente", "playbook", "metodo"]


def fixture(d):
    n = 40
    r = pd.DataFrame(dict(
        video_id=[f"B{i}" for i in range(n)], plataforma="instagram", tipo=["clips", "feed"] * 20, canal=[f"Loja {i % 6}" for i in range(n)],
        channel_id=[f"loja{i % 6}" for i in range(n)], inscritos=1000,
        porte=["micro", "medio"] * 20, segmento=["alimentacao", "beleza", "pet", "varejo_moda"] * 10, titulo=None,
        descricao=[f"Promoção <b>{i}</b> do dia" for i in range(n)], publicado="2026-10-01T10:00:00", views=[None] * n,
        likes=range(n), comentarios=range(n), er=[i / 100 for i in range(n)], outlier=[None] * 5 + [1.5] * 35,
        conversa=0.1, resid=[i / 10 - 2 for i in range(n)], efeito_criador=0.2, elegivel=[1] * 30 + [0] * 10,
        top=[0] * 26 + [1] * 4 + [0] * 10, top_er_puro=[0] * 36 + [1] * 4, grupo=None, pct_intencao=[i / 80 for i in range(n)],
        url=[f"https://www.instagram.com/p/B{i}/" for i in range(n)]))
    c = sqlite3.connect(f"{d}/foco_b.db")
    r.to_sql("ranking", c, index=False)
    r[["video_id", "plataforma", "likes"]].to_sql("videos", c, index=False)
    rub = dict(formato="oferta", mostra_produto=True, mostra_preco=False, tipo_cta="chamar_no_whatsapp", gancho_3s="Olha <i>isso</i>",
               elementos_top5=["a", "<script>b</script>"], texto="x" * 200)
    pd.DataFrame(dict(video_id=[f"B{i}" for i in range(20, 34)], grupo="top", fonte="vlm", rubrica=json.dumps(rub))).to_sql("categorias", c, index=False)
    c.close()
    pd.DataFrame(dict(plataforma="instagram", campo=["mostra_preco", "tipo_cta", "formato"], valor=["True", "chamar_no_whatsapp", "oferta"],
                      freq_top=[.5, .3, .1], freq_resto=[.2, .2, .05], lift=[2.5, 1.5, 2.0], n_top=[10, 6, 3])).to_csv(f"{d}/b_achados.csv", index=False)
    pd.DataFrame(dict(plataforma="instagram", canal=["Loja 1", "Loja 2"], porte="micro", inscritos=[900, 5000], efeito_criador=[.8, .3],
                      n_top=[2, 1], n_posts=[12, 9], segmento=["pet", "beleza"])).to_csv(f"{d}/b_perfis_destaque.csv", index=False)
    open(f"{d}/PLAYBOOK_B.md", "w").write("# Playbook B de teste\n\nIntro.\n\n## Parte um\n\nConteúdo.\n\n## Limitações\n\nPoucas.")


def texto(at):
    return " ".join(str(getattr(e, "value", "") or getattr(e, "body", "")) for e in list(at.markdown) + list(at.get("html"))
                    + list(at.info) + list(at.caption) + list(at.header))


def roda(nome, foco, pagina, espera=(), nao_espera=(), estado=None):
    at = AppTest.from_file(os.path.abspath("app.py"), default_timeout=120)
    at.session_state["foco"] = foco
    for k_, v in (estado or {}).items():
        at.session_state[k_] = v
    at.run()
    assert not at.exception, (nome, pagina, at.exception)
    if pagina != "visao":
        at.switch_page(f"paginas/{pagina}.py").run()
        assert not at.exception, (nome, pagina, [e.value for e in at.exception])
    txt = texto(at)
    for e in espera:
        assert e in txt, (nome, pagina, "faltou", e)
    for e in nao_espera:
        assert e not in txt, (nome, pagina, "sobrou", e)
    return at, txt


def todas(nome, foco, vazio):
    """Todas as páginas do foco sem exceção; `vazio` diz se o foco deve estar no estado 'sem dados'."""
    for p in PAGINAS:
        at, txt = roda(nome, foco, p)
        if p in ("visao", "catalogo", "rankings", "padroes"):
            assert ("Ainda sem dados deste foco" in txt) == vazio, (nome, p, "estado vazio inesperado")
        assert len(at.dataframe) == 0 or p == "rankings", (nome, p, "tabela fora do expander de Rankings")
    print(f"ok  {nome}: {len(PAGINAS)} páginas")


tmp = tempfile.mkdtemp()
fixture(tmp)
# os caminhos do Foco B são lidos no import do ui: cada cenário roda com o ambiente já definido
cenario = sys.argv[1] if len(sys.argv) > 1 else None
if cenario is None:  # roda os 3 cenários em processos separados
    import subprocess
    for c_ in ["real", "sem_b", "fixture_b"]:
        subprocess.run([sys.executable, __file__, c_], check=True)
    sys.exit(0)
if cenario == "sem_b":
    os.environ.update(FOCO_B_DIR="/nao/existe", FOCO_B_PLAYBOOK="/nao/existe/PLAYBOOK_B.md")
    todas("A, sem arquivos do B", "A", False)
    todas("B, sem arquivos do B", "B", True)
    assert not os.path.exists("/nao/existe")
elif cenario == "fixture_b":
    os.environ.update(FOCO_B_DIR=tmp, FOCO_B_PLAYBOOK=f"{tmp}/PLAYBOOK_B.md")
    todas("B, com base falsa", "B", False)
    _, txt = roda("B falso", "B", "padroes", ["frágil", "controle", "Mostra o preço"], ["confirmado", "Ads do Impulso"])
    _, txt = roda("B falso", "B", "playbook", ["Parte um"])
    _, txt = roda("B falso", "B", "catalogo", ["Promoção &lt;b&gt;"], ["Promoção <b>"])  # texto dos dados sempre escapado
    at, txt = roda("B falso, detalhe", "B", "catalogo", ["O que a leitura automática viu", "Olha &lt;i&gt;isso", "&lt;script&gt;"],
                   ["<script>b"], estado={"post_aberto": ("B", "B25")})
    print("ok  escape de HTML e detalhe do post (base falsa)")
else:
    todas("A, base real", "A", False)
    todas("B, base real", "B", False)
    roda("A", "A", "visao", ["3 coisas que aprendemos", "Coincide com a régua antiga", "Em destaque agora"])
    roda("B", "B", "visao", ["Humor engaja. Preço gera pedido."])
    roda("A", "A", "padroes", ["O que os Ads do Impulso confirmam", "confirmado", "controle"])
    roda("B", "B", "padroes", ["controle"], ["O que os Ads do Impulso confirmam"])
    roda("A", "A", "metodo", ["Como escolhemos o top", "Medimos o engajamento"])
    roda("B", "B", "agente", ["O agente cria para o Impulso"])
    # playbook em formato de matéria: capítulos, ranking de perfis, pautas e posts embutidos; sem tabela solta
    at, txt = roda("A", "A", "playbook", ["Reação não é clique", "No Instagram", "No YouTube", "Pauta 5", "instagram.com/p/",
                                           "youtube.com/embed/", "Neste playbook"], ["| Perfil |"])
    assert txt.count("instagram.com/p/") and txt.count('class="emb-ig"') <= 6 and txt.count('class="fone-yt"') <= 6, "embutidos demais"
    roda("A, prévia local", "A", "playbook", ["prévia salva na coleta"], ['class="emb-ig"'], estado={"pb_modo": "local"})
    roda("B", "B", "playbook", ["Cinco recomendações para o lojista", "cliente de", "Quatro negócios para olhar de perto"], ["| Perfil |"])
    at, _ = roda("A, exemplo de avaliação", "A", "avaliar_post")
    next(b for b in at.button if b.label == "Ver exemplo").click().run()
    assert not at.exception and "O que fazer agora" in texto(at)
    import ui
    for foco in "AB":
        r = ui.ranking(ui.FOCOS[foco])
        vid = r[r.top & r.analisado].video_id.iloc[0]
        roda(f"{foco}, detalhe", foco, "catalogo", ["O que a leitura automática viu", "× o esperado"], estado={"post_aberto": (foco, vid)})
    print("ok  conteúdo das páginas, exemplo de avaliação e detalhe do post (base real)")
