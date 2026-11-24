"""Padrões: top × controle por tema, com selo e exemplos reais; no Foco A, o que os Ads do Impulso confirmam."""
import streamlit as st

import ui

fonte = ui.fonte_atual()
k = fonte["id"]
ui.titulo("Padrões", "O que aparece mais (ou menos) nos posts do top do que nos posts comuns. "
          "Clique em um padrão para ver 3 posts reais do top que o têm.", grifo="Padrões")
ps = ui.padroes(fonte)
if ps is None:
    ui.sem_dados(fonte, "padroes")
    st.stop()
R = ui.ranking(fonte)
selado = "selo" in ps

c = st.columns([1.2, 1.4, 2])
plats = ui.plataformas(ps)
plat = plats[0]
if len(plats) > 1:
    plat = c[0].selectbox("Plataforma", plats, format_func=lambda x: ui.PLAT_NOME.get(x, x), key=f"pd_plat_{k}")
todos = c[1].toggle("Mostrar também os que não diferenciam", key=f"pd_todos_{k}",
                    help="Por padrão ficam só os padrões que aparecem pelo menos 20% mais ou 20% menos no top.")
d = ps[ps.plataforma == plat]
d = d[d.lift.notna()]
if not todos:
    d = d[(d.lift >= 1.2) | (d.lift <= 0.8)]

st.html('<p class="muted" style="margin:0"><span style="color:var(--data)">■</span> top &nbsp; '
        '<span style="color:var(--data-soft)">■</span> controle: posts comuns, sorteados fora do top. '
        '“2,0×” quer dizer que a característica aparece duas vezes mais no top. '
        + ('O selo cruza com os anúncios do Impulso. ' if selado else '') +
        '<b>Frágil</b> = menos de 5 posts do top sustentam o padrão: é pista, não regra.</p>')


def exemplos(campo, valor):
    """Até 3 posts do top que têm o padrão (None = não dá para casar com os dados do post)."""
    if R is None:
        return None
    t = R[R.top & (R.plataforma == plat)] if plat != "todas" else R[R.top]
    v = {"True": "sim", "False": "não"}.get(valor, valor)
    if f"r_{campo}" in t:
        m = t[f"r_{campo}"].astype(str) == v
    elif campo == "segmento":
        m = t.seg.astype(str) == valor
    elif campo == "tipo_post":
        m = t.formato_post == {"carrossel": "Carrossel", "imagem": "Imagem", "reel": "Reels"}.get(valor, valor)
    elif campo in ("tipo_criador", "duracao_faixa") and campo in t:
        m = t[campo].astype(str) == valor
    else:
        return None
    return t[m].sort_values(["tem_midia", "resid"], ascending=False).drop_duplicates("canal").head(3).to_dict("records")


def linha(p, aberto):
    mx = max(p["freq_top"], p["freq_resto"], 0.01)
    chips = ""
    if isinstance(p.get("selo"), str) and p["selo"] != "inconclusivo":
        chips += ui.chip(p["selo"], "c-" + ui.SELO_CLS.get(p["selo"], "mut"))
    if p["n_top"] < 5:
        chips += ui.chip("frágil", "c-warn")
    chips += ui.chip(f"{int(p['n_top'])} posts do top", "c-mut")
    baixo = p["lift"] < 1
    return (f'<div class="pd {"on" if aberto else ""}"><div class="pd-n"><b>{ui.E(ui.nome_padrao(p["campo"], p["valor"]))}</b>{chips}</div>'
            f'<div class="pd-b"><div><span>top</span><i style="width:{p["freq_top"] / mx * 100:.0f}%"></i><em>{ui.pct(p["freq_top"], 0)}</em></div>'
            f'<div><span>controle</span><i style="width:{p["freq_resto"] / mx * 100:.0f}%"></i><em>{ui.pct(p["freq_resto"], 0)}</em></div></div>'
            f'<div class="pd-l {"dn" if baixo else ""}"><b>{ui.dec(p["lift"], 2 if baixo else 1)}<span class="x">×</span></b>'
            f'<span>{"menos no top" if baixo else "mais no top"}</span></div></div>')


def alternar(chave):
    st.session_state[f"pd_aberto_{k}"] = None if st.session_state.get(f"pd_aberto_{k}") == chave else chave


if d.empty:
    ui.vazio("Nenhum padrão neste recorte", "Ligue “Mostrar também os que não diferenciam”.")
usados = set()
grupos = ui.GRUPOS + [("Outros", "", sorted(set(d.campo) - {c_ for g in ui.GRUPOS for c_ in g[2]}))]
for nome, desc, campos in grupos:
    g = d[d.campo.isin(campos)].sort_values("lift", ascending=False)
    if g.empty:
        continue
    ui.secao(nome, desc)
    for p in g.to_dict("records"):
        chave = f"{plat}|{p['campo']}|{p['valor']}"
        aberto = st.session_state.get(f"pd_aberto_{k}") == chave
        with st.container(key=f"pr_{abs(hash(chave))}"):
            st.html(linha(p, aberto))
            st.button(f"Ver exemplos de {ui.nome_padrao(p['campo'], p['valor'])}", key=f"b_pr_{chave}", on_click=alternar, args=(chave,))
        if aberto:
            ex = exemplos(p["campo"], p["valor"])
            if ex:
                with st.container(key=f"grade_ex"):
                    for col, row in zip(st.columns([1, 1, 1, 2.4]), ex):
                        with col:
                            ui.post_card(row, fonte, "ex", "mini")
            else:
                st.caption("Este padrão vem de uma conta feita sobre vários campos; não há como apontar posts de exemplo direto."
                           if ex is None else "Nenhum post do top com este padrão tem os dados para mostrar aqui.")

# ---------- Ads do Impulso (só Foco A)
if k == "A":
    ii = ui.ler_csv("impulso_interno.csv")
    if ii is not None and "ctr" in ii:
        ui.secao("O que os Ads do Impulso confirmam", "taxa de clique (CTR) de cada anúncio")
        ii = ii[ii.ctr.notna()].sort_values("ctr", ascending=False)
        mx = ii.ctr.max()
        linhas = []
        for a in ii.to_dict("records"):
            marcas = []
            if a.get("convite_participacao") is True or str(a.get("convite_participacao")) == "True":
                marcas.append("convida a participar")
            if isinstance(a.get("gatilho_identificacao"), str) and a["gatilho_identificacao"] != "nenhum":
                marcas.append(ui.valor_nome(a["gatilho_identificacao"]))
            linhas.append(f'<div class="{ui.E(str(a.get("desempenho", "")))}"><span>{ui.E(str(a["criativo"]))}'
                          f'<small>{ui.E(" · ".join(marcas) or "sem gatilho de identificação")}</small></span>'
                          f'<i style="width:{a["ctr"] / mx * 100:.0f}%"></i><em>{ui.dec(a["ctr"], 2)}%</em></div>')
        a_, b_ = st.columns([1.5, 1], gap="large")
        with a_, st.container(border=True):
            st.html('<div class="ads">' + "".join(linhas) + "</div>")
        b_.html('<div class="aviso" style="border-left-color:var(--data)"><h3>Pessoa real e convite a participar</h3>'
                '<p>Os anúncios com CTR acima de 8% chamam o empreendedor pelo nome do que ele vive ou pedem que ele participe. '
                'Os genéricos e motivacionais ficam abaixo de 1%.</p><p class="muted" style="margin-top:8px">'
                '<span style="color:var(--data)">■</span> desempenho alto &nbsp;<span style="color:var(--data-soft)">■</span> médio '
                '&nbsp;<span style="color:var(--bad)">■</span> baixo</p><p class="muted" style="margin-top:8px">'
                'Um padrão ganha o selo <b>confirmado</b> quando aparece mais no top do mercado e também nos anúncios de CTR alto; '
                '<b>contradito</b> quando os dois apontam para lados opostos; <b>só mercado</b> quando não há anúncio para comparar.</p></div>')
