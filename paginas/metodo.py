"""Método: como o top é escolhido, números da base, avaliação da régua e limitações."""
import streamlit as st

import pipeline as P
import ui

fonte = ui.fonte_atual()
k = fonte["id"]
ui.titulo("Método", "Como escolhemos o top, de onde vêm os dados e o que esta análise não consegue dizer.", grifo="Método")

ui.secao("Como escolhemos o top")
st.html('<div class="passos">' + "".join(f'<div class="passo"><b>{ui.E(t)}</b><p>{ui.E(x)}</p></div>' for t, x in ui.regua(fonte)) + "</div>")

ui.secao("A base em números")
R = ui.base(fonte)
if R is not None:
    cards = []
    for plat, d in R.groupby("plataforma"):
        linhas = [("Posts no ranking", ui.num(len(d))), ("Criadores", ui.num(d.canal.nunique()))]
        if "elegivel" in d:
            linhas.append(("Concorrem ao top", ui.num(int(d.elegivel.sum()))))
        linhas.append(("Posts no top", ui.num(int(d.top.sum()))))
        if "top_er_puro" in d and d.top.sum():
            linhas.append(("Também top pela régua antiga", f"{int((d.top & d.top_er_puro).sum())} de {int(d.top.sum())}"))
        linhas.append(("Lidos em detalhe pela IA", ui.num(int(d.analisado.sum()))))
        if ui.tem(d, "publicado"):
            linhas.append(("Período", f"{ui.data_br(d.publicado.dropna().min())} a {ui.data_br(d.publicado.dropna().max())}"))
        cards.append(f'<div class="kpi"><span>{ui.PLAT_NOME.get(plat, plat)}</span><div class="receipt" style="border:0;padding:6px 0 0;background:none">'
                     + "".join(f"<div><span>{a}</span><b>{b}</b></div>" for a, b in linhas) + "</div></div>")
    st.html(f'<div class="kpis" style="grid-template-columns:repeat({max(2, len(cards))},1fr)">' + "".join(cards) + "</div>")

if k == "A":
    v = ui.ler_csv(f"{P.DATA}/validacao_resultado.csv")
    if v is not None and "kappa" in v:
        ui.secao("Dá para confiar na leitura automática?", "10 posts rotulados à mão, às cegas")
        v = v.sort_values("kappa", ascending=False)
        linhas = "".join(
            f'<div class="{"alto" if x["kappa"] >= .4 else "baixo"}"><span>{ui.E(ui.rotulo(x["campo"]))}'
            f'<small>{"concordância boa" if x["kappa"] >= .6 else "concordância razoável" if x["kappa"] >= .4 else "pouco confiável: ler com cautela"}</small></span>'
            f'<i style="width:{max(2, x["kappa"] * 100):.0f}%"></i><em>{ui.dec(x["kappa"], 2)}</em></div>' for x in v.to_dict("records"))
        a, b = st.columns([1.5, 1], gap="large")
        with a, st.container(border=True):
            st.html(f'<div class="ads">{linhas}</div>')
        b.html('<div class="vazio"><b>Como ler</b><p>O número (kappa) vai de 0 a 1: quanto a leitura da IA concorda com a de uma '
               'pessoa, já descontando o acaso. Abaixo de 0,4 o campo é pouco confiável, e os padrões que dependem dele são '
               'pistas, não regras.</p></div>')

aval = ui.secao_md(f"{P.DATA}/avaliacao_regua.md", "")
if aval.strip():
    with st.expander("A régua nova é melhor que só olhar o maior ER? Avaliação completa"):
        if k != "A":
            st.caption("Avaliação feita na base do foco “Impulso → empreendedor”.")
        st.markdown(aval)

ui.secao("O que esta análise não diz")
if k == "A":
    lim = ui.secao_md("README.md", "## Limitações e evolução").replace("## Limitações e evolução", "", 1)
    base_txt = ui.secao_md("README.md", "### Limitações da base", "## Metodologia").replace("### Limitações da base", "", 1)
    st.markdown((lim + "\n" + base_txt).strip() or "Sem texto de limitações disponível.")
    for nome, ini, fim in [("De onde vêm os dados", "## Base de dados", "### Limitações da base"),
                           ("Metodologia completa", "## Metodologia", "## Resultados")]:
        txt = ui.secao_md("README.md", ini, fim).replace(ini, "", 1)
        if txt.strip():
            with st.expander(nome):
                st.markdown(txt)
else:
    lim = ui.secao_md(fonte["playbook"], "## Limitações").replace("## Limitações", "", 1)
    st.markdown(lim.strip() or "Amostra pequena e não aleatória; os padrões são observados, não são causa. Padrão com menos "
                "de 5 posts no top é pista, não regra.")
    met = ui.secao_md(fonte["playbook"], "## Metodologia em 5 linhas", "## ").replace("## Metodologia em 5 linhas", "", 1)
    if met.strip():
        with st.expander("Metodologia deste foco"):
            st.markdown(met)
