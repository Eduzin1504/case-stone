"""Criar com o agente: gerar criativo, analisar ou recomendar (mesma run() do agent.py e do servidor MCP)."""
import json
import re

import streamlit as st

import pipeline as P
import ui

EXEMPLOS = {
    "gerar_criativo": "Reels de fim de ano para salão de beleza sobre organizar o caixa",
    "analisar": "O que diferencia os carrosséis de alto engajamento no Instagram?",
    "recomendar": "Quais 3 pautas o Impulso deveria postar em dezembro?",
}
MODOS = {"gerar_criativo": "Gerar criativo", "analisar": "Analisar", "recomendar": "Recomendar"}
FA = ui.FOCOS["A"]  # o agente trabalha sempre com a base do Foco A

ui.titulo("Criar com o agente", "Peça um criativo, uma análise ou uma recomendação. O agente consulta a base, escolhe posts "
          "reais como referência e só entrega o que tem lastro neles.", grifo="agente", foco=False)
if ui.fonte_atual()["id"] != "A":
    st.info("O agente cria para o Impulso, com a base do foco “Impulso → empreendedor”. As outras páginas seguem no foco "
            "que você escolheu.", icon=":material/info:")


def passos(t):
    """Quebra 'Card 1: … Card 2: …' ou marcas de tempo (0-3s) em passos (rótulo, texto)."""
    t = re.sub(r"\s*((?:Slide|Card|Cena|Take) \d+[^:\n]{0,30}:|\(?\d{1,2}\s?[–-]\s?\d{1,3}\s?s\)?:?)", r"\n\1", t.strip())
    out = []
    for l in (x.strip() for x in t.split("\n")):
        if not l:
            continue
        m = re.match(r"((?:Slide|Card|Cena|Take) \d+[^:]{0,30}|\(?\d{1,2}\s?[–-]\s?\d{1,3}\s?s\)?):?\s*(.*)", l)
        if m:
            out.append((m.group(1).strip("() "), m.group(2)))
        elif out and not l.startswith("("):
            out[-1] = (out[-1][0], (out[-1][1] + " " + l).strip())
        else:
            out.append(("", l))
    return out


def comprovante(c, refs_ids, tentativas, pendencias):
    validas = sum(i in refs_ids for i in c["inspirado_em"])
    falta = validas < len(c["inspirado_em"])
    carimbo = ('<p class="stamp" style="color:var(--warn)">Revisar antes de postar</p>' if falta or pendencias else
               '<p class="stamp" style="color:var(--ok)">Aprovado</p>')
    extra = f'<p class="muted" style="font-size:.76rem;margin:6px 0 0">Pendência da revisão: {ui.E(pendencias[:220])}</p>' if pendencias else ""
    return (f'<div class="receipt"><div class="{"warn" if falta else ""}"><span>Referências reais na base</span>'
            f'<b>{validas} de {len(c["inspirado_em"])}</b></div><div><span>Tentativas do agente</span><b>{tentativas or 1}</b></div>'
            f'{carimbo}{extra}</div>')


def refs(lista, ids, chave):
    """Posts de referência como miniaturas clicáveis (abrem o detalhe)."""
    R = ui.ranking(FA)
    alvo = [r for r in lista if ids is None or r["video_id"] in ids] or lista
    with st.container(key=f"grade_ref{chave}"):
        for col, r in zip(st.columns(4), alvo[:4]):
            d = R[R.video_id == r["video_id"]] if R is not None else None
            row = d.iloc[0].to_dict() if d is not None and len(d) else dict(
                video_id=r["video_id"], plataforma=r["plataforma"], canal=r["canal"], post=(r.get("titulo") or "")[:140],
                er=r.get("er"), resid=None, url=r.get("url"), top=True, tem_midia=r["plataforma"] == "youtube",
                tem_video=r["plataforma"] == "youtube", formato_post="Short" if r["plataforma"] == "youtube" else "Post")
            with col:
                ui.post_card(row, FA, f"ref{chave}", "mini")


def achados(findings, n=8):
    linhas = []
    for a in findings[:n]:
        mx = max(a["freq_top"], a["freq_resto"], 0.01)
        selo = a.get("selo") if isinstance(a.get("selo"), str) else ""
        chips = (ui.chip(selo, "c-" + ui.SELO_CLS.get(selo, "mut")) if selo else "") + \
                (ui.chip("frágil", "c-warn") if a.get("n_top", 5) < 5 else "")
        lift = a.get("lift") if ui._ok(a.get("lift")) else None
        linhas.append(
            f'<div class="pd" style="grid-template-columns:1fr 64px;margin-bottom:8px;padding:10px 14px">'
            f'<div><div class="pd-n"><b>{ui.E(ui.nome_padrao(a["campo"], a["valor"]))}</b>{chips}</div>'
            f'<div class="pd-b" style="margin-top:6px"><div><span>top</span><i style="width:{a["freq_top"] / mx * 100:.0f}%"></i><em>{ui.pct(a["freq_top"], 0)}</em></div>'
            f'<div><span>controle</span><i style="width:{a["freq_resto"] / mx * 100:.0f}%"></i><em>{ui.pct(a["freq_resto"], 0)}</em></div></div></div>'
            f'<div class="pd-l"><b>{ui.dec(lift) + '<span class="x">×</span>' if lift else "—"}</b><span>no top</span></div></div>')
    return "".join(linhas)


modo = st.segmented_control("Modo", list(MODOS), format_func=MODOS.get, default="gerar_criativo",
                            label_visibility="collapsed", key="ag_modo") or "gerar_criativo"
offline = st.toggle("Usar respostas salvas (sem rede)", value=st.query_params.get("offline", "1") == "1", key="ag_off",
                    help="Mostra respostas reais que o agente já deu, guardadas no projeto. Desligue para fazer uma pergunta nova.")
saida, meta = None, {}
if offline:
    opcoes = [d for d in ui.salvas(ui.versao(f"{P.DATA}/execucoes.jsonl")) if d["entrada"]["mode"] == modo]
    if not opcoes:
        st.info("Ainda não há resposta salva neste modo. Desligue “Usar respostas salvas” para perguntar ao agente.")
    else:
        d = st.selectbox("Resposta salva", opcoes, format_func=lambda d: d["entrada"]["query"], key=f"ag_salva_{modo}")
        saida, meta = d["saida"], {"tentativas": d.get("tentativas"), "pendencias": d.get("pendencias", "")}
        st.caption("Resposta gerada pelo agente em " + d["em"][:16].replace("T", " às "))
else:
    with st.form("pergunta"):
        q = st.text_area("O que você quer?", value=EXEMPLOS[modo], height=80)
        c1, c2, c3, c4 = st.columns(4)
        seg = c1.selectbox("Segmento", ["todos", "alimentação", "beleza", "varejo", "serviços"])
        plataforma = c2.selectbox("Plataforma", ["todas", "instagram", "youtube"], format_func=lambda x: ui.PLAT_NOME.get(x, "Todas"))
        porte = c3.selectbox("Tamanho do perfil", ["todos", "micro", "medio", "grande"], format_func=lambda x: ui.PORTE_NOME.get(x, x))
        pilar = c4.selectbox("Pilar", ["todos"] + P.PILARES)
        enviar = st.form_submit_button("Perguntar ao agente", type="primary", icon=":material/send:")
    if enviar and q.strip():
        filtros = {k_: v for k_, v in {"plataforma": plataforma, "porte": porte, "pilar": pilar}.items() if v not in ("todas", "todos")}
        with st.status("O agente está trabalhando…", expanded=True) as stt:
            st.write("Consultando a base e escolhendo referências reais")
            st.write("Escrevendo e checando (pode levar até 1 minuto)")
            try:
                import agent  # import tardio: carrega o grafo só quando alguém pergunta
                saida = agent.run(modo, q.strip(), None if seg == "todos" else seg, filtros or None)
                ult = ui.tentar(lambda: json.loads(open(f"{P.DATA}/execucoes.jsonl", encoding="utf-8").readlines()[-1])) or {}
                meta = {"tentativas": ult.get("tentativas"), "pendencias": ult.get("pendencias", "")}
                stt.update(label="Pronto", state="complete", expanded=False)
                st.session_state["ultima"] = (saida, meta)
            except Exception as e:  # rede, crédito ou API fora
                stt.update(label="Não deu para falar com o modelo agora", state="error")
                st.error(f"{type(e).__name__}: {str(e)[:300]}. Ligue “Usar respostas salvas” para seguir.")
    elif "ultima" in st.session_state:
        saida, meta = st.session_state["ultima"]

if not saida:
    st.stop()
if saida.get("confidence_flag"):
    relax = (" Filtros soltos por falta de exemplos: " + ", ".join(saida["filtros_relaxados"]) + ".") if saida.get("filtros_relaxados") else ""
    st.warning("Pouca evidência neste recorte: trate como pista, não como regra." + relax, icon=":material/warning:")
ids = {r["video_id"] for r in saida["reference_posts"]}

if saida["creatives"]:
    abas = st.tabs([f"Criativo {i}" for i, _ in enumerate(saida["creatives"], 1)])
    for n_, (aba, c) in enumerate(zip(abas, saida["creatives"])):
        with aba:
            st.html(ui.chip(c["formato"][:70], "c-line", "formato") + ui.chip(c["pilar"], "c-line", "pilar"))
            esq, dir_ = st.columns([1.3, 1], gap="large")
            with esq:
                st.html(f'<div class="hookq"><span>Gancho, nos 3 primeiros segundos</span><p>“{ui.E(c["gancho"])}”</p></div>')
                with st.container(border=True):
                    st.html('<b style="font-size:.9rem">Roteiro</b><ol class="tl">' + "".join(
                        f'<li>{f"<b>{ui.E(r)}</b>" if r else ""}{ui.E(t)}</li>' for r, t in passos(c["roteiro"])) + "</ol>")
                with st.container(border=True):
                    st.html('<b style="font-size:.9rem">Chamada para ação</b>'
                            f'<p style="margin:4px 0 0;font-size:.9rem;line-height:1.5">{ui.E(c["cta"])}</p>')
            with dir_:
                st.html('<b style="font-size:.9rem">Legenda</b> <span class="muted" style="font-size:.78rem">· o ícone no canto copia</span>')
                st.code(c["legenda"], language=None, wrap_lines=True)
                st.html('<b style="font-size:.9rem">Checagem</b>')
                st.html(comprovante(c, ids, meta.get("tentativas"), meta.get("pendencias", "")))
            ui.secao("Inspirado em", "posts reais da base · clique para ver")
            refs(saida["reference_posts"], set(c["inspirado_em"]), n_)

esq, dir_ = st.columns([1.3, 1], gap="large")
with esq:
    ui.secao("Por quê")
    with st.container(border=True):
        st.markdown(saida["explanation"])
with dir_:
    if saida["findings"]:
        ui.secao("O que aparece mais no top")
        st.html(achados(saida["findings"]))
if not saida["creatives"] and saida["reference_posts"]:
    ui.secao("Posts de referência", "clique para ver")
    refs(saida["reference_posts"], None, "x")
