"""Visão geral: os números do foco, o que aprendemos, posts e criadores em destaque."""
import streamlit as st

import ui

fonte = ui.fonte_atual()
ui.titulo("Visão geral", fonte["desc"], grifo="geral")
R = ui.base(fonte)
ps = ui.padroes(fonte)

if R is not None:
    n_top = int(R.top.sum())
    plat = R.plataforma.value_counts()
    cores = {"instagram": "#c5ff1f", "youtube": "#7fb894"}
    split = "".join(f'<i style="width:{max(4, n / len(R) * 100):.0f}%;background:{cores.get(p, "#7fb894")}"></i>' for p, n in plat.items())
    partes = " · ".join(f"{ui.num(n)} {ui.PLAT_NOME.get(p, p)}" for p, n in plat.items())
    k = [("k1", "Posts na base", ui.num(len(R)), partes + (f'<div class="split">{split}</div>' if len(plat) > 1 else "")),
         ("", "Criadores", ui.num(R.canal.nunique()), "perfis acompanhados"),
         ("", "Posts no top", ui.num(n_top), f"de {ui.num(int(R.elegivel.sum()))} que concorrem" if "elegivel" in R else "os que mais superaram o esperado")]
    if "top_er_puro" in R and n_top:
        co = int((R.top & R.top_er_puro).sum())
        k.append(("", "Coincide com a régua antiga", ui.pct(co / n_top, 0),
                  f"{co} dos {n_top} posts do top também seriam top só pelo maior ER"))
    st.html('<div class="kpis">' + "".join(f'<div class="kpi {c}"><span>{t}</span><b>{v}</b><small>{s}</small></div>'
                                           for c, t, v, s in k) + "</div>")

# ---------- Foco B: curtida não é pedido
it = ui.intencao(fonte) if fonte["id"] == "B" else None
if it is not None:
    import altair as alt
    ui.secao("Curtida não é pedido")
    a, b = st.columns([1, 1.15], gap="large", vertical_alignment="center")
    g = dict(zip(it.grupo, it.pct))
    frase = []
    if "Humor ou trend" in g:
        frase.append(f"Posts de humor são os que mais se destacam em curtidas, mas só <b>{ui.pct(g['Humor ou trend'], 0)}</b> "
                     "dos comentários deles mostram vontade de comprar.")
    if "Mostra o preço" in g and "Não mostra o preço" in g:
        frase.append(f"Quando o post mostra o preço, <b>{ui.pct(g['Mostra o preço'], 0)}</b> dos comentários perguntam como "
                     f"comprar, contra {ui.pct(g['Não mostra o preço'], 0)} quando não mostra.")
    n_preco = it.set_index("grupo").posts.get("Mostra o preço", 0)
    a.html('<div class="aviso"><h3>Humor engaja. Preço gera pedido.</h3><p>' + " ".join(frase) +
           f'</p><p class="muted" style="margin-top:8px">São dois trabalhos diferentes, e o lojista precisa dos dois. '
           f'Indício: só {n_preco} posts mostram preço.</p></div>')
    it = it.assign(cor=["#b02d63" if "Humor" in x else "#1f9e55" for x in it.grupo],
                   rot=[ui.pct(x, 0) for x in it.pct])
    base_ = alt.Chart(it).encode(y=alt.Y("grupo:N", sort=list(it.grupo), title=None,
                                         axis=alt.Axis(labelLimit=200, labelFontSize=12, labelColor="#14231b", ticks=False, domain=False, labelPadding=8)),
                                 x=alt.X("pct:Q", axis=None, scale=alt.Scale(domain=[0, max(it.pct) * 1.18])))
    ch = (base_.mark_bar(cornerRadiusEnd=4, height=16).encode(color=alt.Color("cor:N", scale=None),
          tooltip=[alt.Tooltip("grupo:N", title="Post"), alt.Tooltip("pct:Q", title="Comentários com intenção de compra", format=".0%"),
                   alt.Tooltip("posts:Q", title="Posts"), alt.Tooltip("comentarios:Q", title="Comentários lidos")])
          + base_.mark_text(align="left", dx=6, font="JetBrains Mono", fontSize=12, color="#14231b").encode(text="rot:N"))
    b.html('<p class="muted" style="margin:0 0 2px">Comentários com intenção de compra, por tipo de post</p>')
    b.altair_chart(ch.properties(height=34 * len(it)).configure_view(strokeWidth=0).configure(font="Lexend", background="transparent"))

# ---------- 3 coisas que aprendemos
if ps is None:
    ui.secao("O que aprendemos")
    ui.sem_dados(fonte, "padroes")
else:
    fortes = ps[(ps.n_top >= 5) & ps.lift.notna()].sort_values("lift", ascending=False)
    if "selo" in fortes:  # o confirmado pelos Ads vem primeiro
        fortes = fortes.assign(_c=(fortes.selo == "confirmado")).sort_values(["_c", "lift"], ascending=False)
    tres = fortes.drop_duplicates("campo").drop_duplicates("valor").head(3)
    ui.secao("3 coisas que aprendemos", "os padrões mais fortes deste foco")
    cards = []
    for p in tres.to_dict("records"):
        onde = "" if p["plataforma"] == "todas" or ps.plataforma.nunique() == 1 else f" no {ui.PLAT_NOME.get(p['plataforma'], p['plataforma'])}"
        selo = ui.chip("confirmado pelos Ads do Impulso", "c-ok") if p.get("selo") == "confirmado" else ""
        cards.append(f'<div class="apr"><div class="n">{ui.dec(p["lift"])}<span class="x">×</span><small>mais no top{onde}</small></div>'
                     f'<p><b>{ui.E(ui.nome_padrao(p["campo"], p["valor"]))}</b><br>Está em {ui.pct(p["freq_top"], 0)} dos posts do top '
                     f'e em {ui.pct(p["freq_resto"], 0)} dos posts comuns ({int(p["n_top"])} posts do top).</p>'
                     f'<div class="f">{selo}</div></div>')
    st.html('<div class="aprs">' + "".join(cards) + "</div>")

    ui.secao("O que aparece mais no top", "top × posts comuns (controle)")
    plats = ui.plataformas(ps)
    d = ps[ps.plataforma == plats[0]] if len(plats) > 1 else ps
    if len(plats) > 1:
        escolha = st.segmented_control("Plataforma", plats, default=plats[0], format_func=lambda x: ui.PLAT_NOME.get(x, x),
                                       key=f"vg_plat_{fonte['id']}", label_visibility="collapsed") or plats[0]
        d = ps[ps.plataforma == escolha]
    d = d[(d.n_top >= 5) & d.lift.notna()].sort_values("lift", ascending=False).head(8)
    if d.empty:
        st.info("Nenhum padrão com pelo menos 5 posts do top nesta plataforma.")
    else:
        st.altair_chart(ui.grafico_padroes(d))
        st.page_link("paginas/padroes.py", label="Ver todos os padrões, com exemplos", icon=":material/arrow_forward:")

# ---------- em destaque
if R is not None:
    dest = R[R.top & R.tem_midia].sort_values("resid", ascending=False).drop_duplicates("canal")
    ig = dest[(dest.plataforma == "instagram")].head(3 if (dest.plataforma == "youtube").any() else 5)
    dest = (ig.to_dict("records") + dest[dest.plataforma == "youtube"].head(5 - len(ig)).to_dict("records"))[:5]
    if dest:
        ui.secao("Em destaque agora", "posts do top · clique para ver por dentro")
        ui.grade(dest, fonte, "dest", colunas=5)
        st.page_link("paginas/catalogo.py", label="Abrir o catálogo completo", icon=":material/arrow_forward:")

# ---------- criadores
pf = ui.ler_csv(fonte["perfis"])
if pf is not None and "efeito_criador" in pf:
    import math
    ui.secao("Quem mais supera o esperado", "criadores com post no top")
    pf = pf.sort_values("efeito_criador", ascending=False).head(5)
    mx = max(pf.efeito_criador.max(), 0.01)
    linhas = []
    for i, p in enumerate(pf.to_dict("records"), 1):
        meta = " · ".join(str(x) for x in [ui.PLAT_NOME.get(p.get("plataforma"), ""), f"{ui.compacto(p.get('inscritos'))} seguidores",
                                           f"{int(p['n_top'])} no top" if ui._ok(p.get("n_top")) else ""] if x)
        linhas.append(f'<div class="rk rk3" style="margin-bottom:8px">'
                      f'<div class="rk-pos">{i}</div><div class="rk-t"><b>{ui.E(str(p["canal"]))}</b><span>{ui.E(meta)}</span></div>'
                      f'{ui.barra(max(p["efeito_criador"], 0) / mx, ui.dec(math.exp(p["efeito_criador"])) + "×")}</div>')
    st.html("".join(linhas) + '<p class="muted" style="font-size:.78rem">A barra mostra quantas vezes o perfil engaja acima do '
            'esperado para o tamanho dele.</p>')
    st.page_link("paginas/rankings.py", label="Ver o ranking de criadores", icon=":material/arrow_forward:")
