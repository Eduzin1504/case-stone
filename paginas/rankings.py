"""Rankings: pódio e lista de posts; cards de criadores. A tabela completa fica num expander."""
import math

import streamlit as st

import ui

fonte = ui.fonte_atual()
k = fonte["id"]
ui.titulo("Rankings", "Quem mais superou o esperado. O ER aparece ao lado, mas a posição vem do “× o esperado”: "
          "quanto o post passou do que se previa para aquele perfil, formato e idade.", grifo="Rankings")
R = ui.base(fonte)
if R is None:
    st.stop()

c = st.columns([1.4, 1, 1, 1.6])
modo = c[0].segmented_control("Ver", ["Posts", "Criadores"], default="Posts", key=f"rk_modo_{k}") or "Posts"
plats = ui.plataformas(R)
plat = c[1].selectbox("Plataforma", plats, format_func=lambda x: ui.PLAT_NOME.get(x, x), key=f"rk_plat_{k}")
porte = c[2].selectbox("Tamanho do perfil", ["todos"] + ui.portes(R[R.plataforma == plat]),
                       format_func=lambda x: ui.PORTE_NOME.get(x, x), key=f"rk_porte_{k}")


def th(row):
    bg = ui._bg(row["video_id"], row["plataforma"], fonte) if row.get("tem_midia") else None
    return f'<div class="rk-th" style="{bg or ""}"></div>'


if modo == "Posts":
    d = R[(R.plataforma == plat) & R.resid.notna()]
    if porte != "todos":
        d = d[d.porte == porte]
    d = d.sort_values("resid", ascending=False).head(20)
    if d.empty:
        ui.vazio("Nenhum post neste recorte", "Troque a plataforma ou o tamanho do perfil.")
        st.stop()
    rows = d.to_dict("records")
    mx = max(rows[0]["resid"], 0.01)
    ui.secao("Pódio", f"os 3 posts que mais superaram o esperado no {ui.PLAT_NOME.get(plat, plat)}")
    with st.container(key="grade_podio"):
        for i, (col, row) in enumerate(zip(st.columns([1, 1, 1, 0.6]), rows[:3]), 1):
            with col:
                st.html(f'<div class="podio-n">{i}<small>{ui.vezes(row["resid"])} o esperado</small></div>')
                ui.post_card(row, fonte, "pod")
    if len(rows) > 3:
        ui.secao("Do 4º ao 20º")
        for i, row in enumerate(rows[3:], 4):
            with st.container(key=f"rk_{row['video_id']}"):
                sub = " · ".join(x for x in [row["formato_post"], ui.PORTE_CURTO.get(row.get("porte"), ""),
                                             (row.get("post") or "")[:90]] if x)
                st.html(f'<div class="rk"><div class="rk-pos">{i}</div>{th(row)}'
                        f'<div class="rk-t"><b>{ui.E(str(row.get("canal") or "—"))}</b><span>{ui.E(sub)}</span></div>'
                        f'<div><div class="bar-l">× o esperado</div>{ui.barra(max(row["resid"], 0) / mx, ui.vezes(row["resid"]))}</div>'
                        f'<div class="rk-er"><b>{ui.pct(row.get("er"))}</b>ER</div></div>')
                st.button(f"Abrir post de {row.get('canal')}", key=f"b_rk_{row['video_id']}", on_click=ui.abrir_post,
                          args=(fonte["id"], row["video_id"]))
    st.html('<p class="muted" style="font-size:.78rem;margin-top:6px">A barra usa escala comprimida (logarítmica): a diferença '
            'real entre os primeiros é maior do que parece.</p>')
    with st.expander("Ver tabela"):
        N = st.column_config.NumberColumn
        t = R[(R.plataforma == plat) & R.resid.notna()]
        t = (t if porte == "todos" else t[t.porte == porte]).sort_values("resid", ascending=False).head(300)
        t = t.assign(er_pct=t.er * 100, vezes=t.resid.clip(upper=50).map(math.exp))
        cfg = {"canal": "Criador", "post": st.column_config.TextColumn("Post", width="large"), "formato_post": "Formato",
               "vezes": N("× o esperado", format="%.1f×"), "er_pct": N("ER", format="%.2f%%"),
               "likes": N("Curtidas", format="localized"), "comentarios": N("Comentários", format="localized"),
               "views": N("Views", format="localized"), "top": st.column_config.CheckboxColumn("Top"),
               "url": st.column_config.LinkColumn("Link", display_text="abrir")}
        mostrar = [x for x in cfg if ui.tem(t, x)]
        st.dataframe(t[mostrar], hide_index=True, width="stretch", column_config={x: cfg[x] for x in mostrar})
else:
    pf = ui.ler_csv(fonte["perfis"])
    if pf is None or "canal" not in pf:
        ui.sem_dados(fonte, "perfis")
        st.stop()
    if "plataforma" in pf:
        pf = pf[pf.plataforma == plat]
    if porte != "todos" and "porte" in pf:
        pf = pf[pf.porte == porte]
    ordem = next((x for x in ["efeito_criador", "n_top"] if ui.tem(pf, x)), None)
    if ordem:
        pf = pf.sort_values(ordem, ascending=False)
    if pf.empty:
        ui.vazio("Nenhum criador neste recorte", "Troque a plataforma ou o tamanho do perfil.")
        st.stop()
    ui.secao("Criadores em destaque", f"{len(pf)} perfis com pelo menos 1 post no top")
    n = st.session_state.get(f"rk_ncr_{k}", 8)
    mx = max(pf.efeito_criador.max(), 0.01) if "efeito_criador" in pf else 1
    lista = pf.head(n).to_dict("records")
    for i in range(0, len(lista), 2):
        for j, (col, p) in enumerate(zip(st.columns(2), lista[i:i + 2])):
            with col, st.container(border=True):
                pos = i + j + 1
                meta = " · ".join(str(x) for x in [ui.PLAT_NOME.get(p.get("plataforma"), ""), f"{ui.compacto(p.get('inscritos'))} seguidores",
                                                   "perfil " + ui.PORTE_CURTO.get(p.get("porte"), str(p.get("porte")))] if x)
                chips = "".join(ui.chip(ui.valor_nome(p[x]), "c-line", r) for x, r in
                                [("segmento", "segmento"), ("tema", "tema"), ("formato", "formato")] if isinstance(p.get(x), str))
                if ui._ok(p.get("n_top")):
                    chips = ui.chip(f"{int(p['n_top'])} no top", "c-top") + chips
                bar = ""
                if ui._ok(p.get("efeito_criador")):
                    bar = ('<div class="bar-l">engaja acima do esperado para o tamanho</div>'
                           + ui.barra(max(p["efeito_criador"], 0) / mx, ui.dec(math.exp(p["efeito_criador"])) + "×"))
                st.html(f'<div class="cr"><div class="cr-top"><span class="cr-pos">{pos}</span><h3>{ui.E(str(p["canal"]))}</h3></div>'
                        f'<p class="cr-meta">{ui.E(meta)}</p>{bar}<div style="margin-top:10px">{chips}</div></div>')
                melhores = R[(R.canal == p["canal"]) & (R.plataforma == plat)].sort_values(["top", "resid"], ascending=False).head(3)
                for cc, row in zip(st.columns(3), melhores.to_dict("records")):
                    with cc:
                        ui.post_card(row, fonte, f"cr{pos}", "mini")
    if len(pf) > n:
        _, m, _ = st.columns(3)
        if m.button(f"Carregar mais criadores ({n} de {len(pf)})", width="stretch", key=f"rk_mais_{k}"):
            st.session_state[f"rk_ncr_{k}"] = n + 8
            st.rerun()
    with st.expander("Ver tabela"):
        N = st.column_config.NumberColumn
        cfg = {"canal": st.column_config.TextColumn("Criador", width="medium"), "porte": "Tamanho", "segmento": "Segmento",
               "inscritos": N("Seguidores", format="localized"), "efeito_criador": N("Acima do esperado (log)", format="%+.2f"),
               "n_top": N("Posts no top", format="%d"), "n_posts": N("Posts na base", format="%d"), "tema": "Tema mais frequente",
               "formato": "Formato mais frequente", "pilar": "Pilar do Impulso"}
        mostrar = [x for x in cfg if ui.tem(pf, x)]
        st.dataframe(pf[mostrar], hide_index=True, width="stretch", column_config={x: cfg[x] for x in mostrar})
