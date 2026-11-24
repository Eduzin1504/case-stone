"""Catálogo: galeria de posts com filtros; o clique abre o detalhe."""
import streamlit as st

import ui

fonte = ui.fonte_atual()
k = fonte["id"]
ui.titulo("Catálogo", "Todos os posts da base. Clique em um para ver a prévia, os números e o que explica a atenção.", grifo="Catálogo")
R = ui.base(fonte)
if R is None:
    st.stop()

tema_col = fonte["campos"]["tema"]
tema_rot = "Segmento" if tema_col == "segmento" else "Tema"
ORDENS = {"destaque": "Destaques", "resid": "Mais acima do esperado", "er": "Maior ER", "likes": "Mais curtidas",
          "comentarios": "Mais comentários", "views": "Mais views", "pct_intencao": "Mais intenção de compra",
          "publicado": "Mais recentes"}

c = st.columns([1.5, 1, 1, 1, 1, 1.1])
busca = c[0].text_input("Buscar", placeholder="criador ou palavra da legenda", key=f"ct_q_{k}")
plats = ui.plataformas(R)
plat = c[1].selectbox("Plataforma", ["todas"] + plats, format_func=lambda x: ui.PLAT_NOME.get(x, x).replace("Todas juntas", "Todas"),
                      key=f"ct_plat_{k}") if len(plats) > 1 else plats[0]
if len(plats) == 1:
    c[1].selectbox("Plataforma", plats, format_func=lambda x: ui.PLAT_NOME.get(x, x), key=f"ct_plat_{k}", disabled=True)
d = R if plat == "todas" else R[R.plataforma == plat]
fmt = c[2].selectbox("Formato", ["todos"] + sorted(d.formato_post.dropna().unique()), key=f"ct_fmt_{k}")
tema = c[3].selectbox(tema_rot, ["todos"] + sorted(d[tema_col].dropna().astype(str).unique()) if tema_col in d else ["todos"],
                      key=f"ct_tema_{k}")
porte = c[4].selectbox("Tamanho do perfil", ["todos"] + ui.portes(d), format_func=lambda x: ui.PORTE_NOME.get(x, x), key=f"ct_porte_{k}")
ordem = c[5].selectbox("Ordenar por", [o for o in ORDENS if o == "destaque" or ui.tem(d, o)], format_func=ORDENS.get, key=f"ct_ord_{k}")
t1, t2, _ = st.columns([1, 1.3, 3])
so_top = t1.toggle("Só o top", key=f"ct_top_{k}")
so_video = t2.toggle("Com prévia de vídeo", key=f"ct_vid_{k}")

if fmt != "todos":
    d = d[d.formato_post == fmt]
if tema != "todos":
    d = d[d[tema_col].astype(str) == tema]
if porte != "todos":
    d = d[d.porte == porte]
if so_top:
    d = d[d.top]
if so_video:
    d = d[d.tem_video]
if busca.strip():
    q = busca.strip()
    d = d[d.canal.fillna("").str.contains(q, case=False, regex=False) | d.post.str.contains(q, case=False, regex=False)
          | d.descricao.str.contains(q, case=False, regex=False)]
if ordem == "destaque":  # quem tem mídia e leitura primeiro; depois o top e o quanto superou o esperado
    d = d.assign(_m=d.tem_midia & d.analisado).sort_values(["_m", "top", "resid"], ascending=False, na_position="last")
    d = d.assign(_i=d.groupby("plataforma").cumcount()).sort_values("_i", kind="stable")  # alterna as plataformas
else:
    d = d.sort_values(ordem, ascending=False, na_position="last")

chave = (plat, fmt, tema, porte, ordem, so_top, so_video, busca)
if st.session_state.get(f"ct_chave_{k}") != chave:  # mudou o filtro: volta para a primeira leva
    st.session_state[f"ct_chave_{k}"], st.session_state[f"ct_n_{k}"] = chave, 24
n = st.session_state.get(f"ct_n_{k}", 24)

st.html(f'<p class="muted" style="margin:4px 0 2px"><b class="mono" style="color:var(--forest)">{ui.num(len(d))}</b> posts '
        f'· mostrando {min(n, len(d))} · {ui.num(int(d.top.sum()))} no top · {ui.num(int(d.tem_video.sum()))} com prévia de vídeo</p>')
if d.empty:
    ui.vazio("Nenhum post com esses filtros", "Solte um dos filtros ou apague a busca.")
    st.stop()
ui.grade(d.head(n).to_dict("records"), fonte, "cat", colunas=4)
if len(d) > n:
    _, m, _ = st.columns([1, 1, 1])
    if m.button("Carregar mais 24", width="stretch", key=f"ct_mais_{k}"):
        st.session_state[f"ct_n_{k}"] = n + 24
        st.rerun()
