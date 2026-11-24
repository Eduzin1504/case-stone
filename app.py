"""Pauta Impulso: roteador da interface (Streamlit). As páginas ficam em paginas/ e as peças em ui.py.
Dois focos de análise: A = Impulso → empreendedor (stone.db), B = Negócio → cliente (foco_b.db).

  .venv/bin/streamlit run app.py
"""
import streamlit as st

import ui

st.set_page_config(page_title="Pauta Impulso", page_icon=":material/bolt:", layout="wide")
ui.estilo()

PAGINAS = [
    st.Page("paginas/visao.py", title="Visão geral", icon=":material/space_dashboard:", default=True),
    st.Page("paginas/catalogo.py", title="Catálogo", icon=":material/grid_view:"),
    st.Page("paginas/rankings.py", title="Rankings", icon=":material/leaderboard:"),
    st.Page("paginas/padroes.py", title="Padrões", icon=":material/compare_arrows:"),
    st.Page("paginas/avaliar_post.py", title="Avaliar meu post", icon=":material/fact_check:", url_path="avaliar"),
    st.Page("paginas/agente.py", title="Criar com o agente", icon=":material/edit_note:"),
    st.Page("paginas/playbook.py", title="Playbook", icon=":material/menu_book:"),
    st.Page("paginas/metodo.py", title="Método", icon=":material/science:"),
]
pg = st.navigation(PAGINAS, position="hidden")

if st.query_params.get("foco") in ui.FOCOS:  # link direto para um foco
    st.session_state["foco"] = st.query_params["foco"]
    del st.query_params["foco"]
if st.session_state.get("foco") not in ui.FOCOS:
    st.session_state["foco"] = "A"

with st.sidebar:
    st.html('<p class="marca">Pauta <span class="mk">Impulso</span></p>'
            '<p class="marca-s">O que faz um post de pequeno negócio engajar, com dados.</p>')
    st.radio("Foco da análise", list(ui.FOCOS), key="foco", format_func=lambda f: ui.FOCOS[f]["nome"],
             captions=[f["desc"] for f in ui.FOCOS.values()])
    for p in PAGINAS:
        st.page_link(p, width="stretch")
    fonte = ui.fonte_atual()
    info = ui.base_info(fonte)
    if info:
        plat, n_perfis, quando = info
        linhas = [f'<b>{ui.num(n)}</b> posts no {ui.PLAT_NOME.get(p, p)}' for p, n in sorted(plat.items())]
        st.html('<div class="sb-base">Base deste foco<br>' + "<br>".join(linhas) + f'<br><b>{ui.num(n_perfis)}</b> criadores'
                + (f'<br>coletado em {quando[8:10]}/{quando[5:7]}/{quando[:4]}' if len(quando) == 10 else "") + "</div>")
    else:
        st.html('<div class="sb-base">Base deste foco: ainda não disponível</div>')
    st.html('<p class="marca-s" style="margin-top:14px">Proposta de estudante · Inteli Academy × Impulso Stone</p>')

pg.run()
ui.abrir_detalhe_se_pedido()
