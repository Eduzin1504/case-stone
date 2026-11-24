"""Avaliar meu post: envia vídeo, imagens ou só a legenda e compara com o top. O motor é avaliar.avaliar()."""
import os

import streamlit as st

import ui

try:
    import avaliar as motor
except Exception:  # motor ausente ou com dependência faltando: a tela continua, com o exemplo
    motor = None

# médias da nota no top e nos posts comuns (controle), por foco e plataforma
MEDIAS = {("A", "instagram"): (66, 54), ("A", "youtube"): (59, 51), ("B", "instagram"): (60, 48)}
METODO = {"quadros_deepseek": "leitura por 6 quadros do vídeo", "imagens_deepseek": "leitura das imagens",
          "texto_deepseek": "leitura só do texto", "video_gemini": "leitura do vídeo inteiro, com áudio"}
EXEMPLO = dict(
    foco="A", plataforma="instagram", metodo="exemplo embutido (não é uma avaliação de verdade)",
    aviso="avaliado por 6 quadros, sem áudio", rubrica={}, nota=63,
    nota_explicacao="O post tem 3 características que aparecem mais no top e 1 que aparece menos.",
    padroes=[
        dict(campo="tema_principal", valor="finanças", rotulo="Tema: finanças", tem=True, lift=4.31, n_top=9, selo="só mercado", efeito="ajuda", fragil=False),
        dict(campo="tipo_hook", valor="promessa", rotulo="Gancho: promessa", tem=True, lift=2.39, n_top=10, selo="só mercado", efeito="ajuda", fragil=False),
        dict(campo="gatilho_identificacao", valor="pessoa_real", rotulo="Identificação: pessoa real", tem=False, lift=1.5, n_top=8, selo="confirmado", efeito="ajuda", fragil=False),
        dict(campo="convite_participacao", valor="True", rotulo="Convida o público a participar", tem=False, lift=1.48, n_top=12, selo="confirmado", efeito="ajuda", fragil=False),
        dict(campo="formato_video", valor="talking head", rotulo="Formato: talking head", tem=True, lift=0.64, n_top=14, selo="só mercado", efeito="atrapalha", fragil=False),
        dict(campo="tipo_cta", valor="salvar", rotulo="Chamada: salvar", tem=True, lift=1.9, n_top=3, selo="só mercado", efeito="ajuda", fragil=True),
    ],
    notas_vs_top=[dict(campo="forca_hook_0a10", rotulo="Força do gancho", valor=6, mediana_top=7),
                  dict(campo="clareza_mensagem_0a10", rotulo="Clareza da mensagem", valor=9, mediana_top=8),
                  dict(campo="ritmo_cortes_0a10", rotulo="Ritmo dos cortes", valor=4, mediana_top=5)],
    parecidos=[],
    recomendacoes=["Abra com a promessa já na primeira frase, antes de se apresentar.",
                   "Traga uma pessoa de verdade: nome, rosto e a rotina do negócio dela.",
                   "Feche convidando o empreendedor a contar a experiência dele nos comentários."],
)

fonte = ui.fonte_atual()
ui.titulo("Avaliar meu post", "Envie o seu vídeo, as imagens do carrossel ou só a legenda. A leitura usa os mesmos critérios "
          "da base e mostra o quanto o post se parece com o top. Não é promessa de resultado.", grifo="meu post", foco=False)
if motor is None:
    ui.vazio("Avaliação em preparação", "O motor de avaliação ainda não está disponível nesta instalação. "
             "Clique em “Ver exemplo” para conhecer a tela.")

esq, dir_ = st.columns([1, 1.7], gap="large")
with esq:
    arqs = st.file_uploader("Vídeo ou imagens do post", type=["mp4", "mov", "webm", "jpg", "jpeg", "png", "webp"],
                            accept_multiple_files=True, help="1 vídeo, ou de 1 a 10 imagens. Até 200 MB.") or []
    legenda = st.text_area("Legenda ou roteiro (opcional se enviou mídia)", height=110, key="av_legenda",
                           placeholder="Cole aqui a legenda, ou o roteiro se ainda não gravou.")
    c1, c2 = st.columns(2)
    foco = c1.selectbox("Comparar com", list(ui.FOCOS), index=list(ui.FOCOS).index(fonte["id"]),
                        format_func=lambda f: ui.FOCOS[f]["nome"], key=f"av_foco_{fonte['id']}")
    plataforma = c2.selectbox("Plataforma", ["instagram", "youtube"] if foco == "A" else ["instagram"],
                              format_func=lambda x: ui.PLAT_NOME[x], key=f"av_plat_{foco}")
    with st.expander("Opções avançadas"):
        usar_video = st.toggle("Ler o vídeo inteiro, com áudio", key="av_video",
                               help="Em vez de 6 quadros do vídeo, a IA assiste ao vídeo todo.")
        st.caption("Mais completo, mas pode passar de 2 minutos e a cota desse modelo é limitada. Se falhar, a leitura "
                   "volta sozinha para os quadros.")
    b1, b2 = st.columns(2)
    enviar = b1.button("Avaliar", type="primary", width="stretch", disabled=motor is None, icon=":material/fact_check:")
    if b2.button("Ver exemplo", width="stretch"):
        st.session_state["avaliacao"] = EXEMPLO
    st.caption("Leva cerca de 35 segundos.")
    if arqs:
        videos = [a for a in arqs if os.path.splitext(a.name)[1].lower() in (".mp4", ".mov", ".webm")]
        with st.container(key="fone"):
            if videos:
                st.video(videos[0])
            else:
                st.image(arqs[0], width="stretch")
        if not videos and len(arqs) > 1:
            st.caption(f"{len(arqs)} imagens enviadas (mostrando a primeira).")

erro = None
if enviar and motor:
    with dir_, st.status("Avaliando o post…", expanded=True) as stt:
        def progresso(msg):
            stt.update(label=f"{msg}…")
            st.write(msg)
        try:
            res = motor.avaliar([(a.name, a.getvalue()) for a in arqs], legenda, foco, plataforma, usar_video, progresso)
            st.session_state["avaliacao"] = res
            stt.update(label="Pronto", state="complete", expanded=False)
        except ValueError as e:  # entrada inválida: a mensagem já vem pronta para o usuário
            stt.update(label="Não deu para avaliar", state="error", expanded=False)
            erro = ("entrada", str(e))
        except Exception as e:  # rede, crédito ou modelo fora do ar
            stt.update(label="A leitura do post falhou", state="error", expanded=False)
            erro = ("modelo", f"{type(e).__name__}: {str(e)[:240]}")


def medidor(nota, m_top, m_com):
    return (f'<div class="gauge" role="img" aria-label="Nota {nota:.0f} de 100. Média do top: {m_top}. Média dos comuns: {m_com}.">'
            f'<b>{nota:.0f}</b><span>de 100</span><div class="t"><i style="width:{max(2, min(100, nota)):.0f}%"></i>'
            f'<u class="c" style="left:{m_com}%"><em>média dos comuns · {m_com}</em></u>'
            f'<u class="p" style="left:{m_top}%"><em>média do top · {m_top}</em></u></div></div>')


def mostrar(res):
    f = ui.FOCOS.get(res.get("foco"), fonte)
    nota = float(res.get("nota") or 0)
    m_top, m_com = MEDIAS.get((res.get("foco"), res.get("plataforma")), (60, 50))
    if nota >= m_top:
        veredito = "Parecido com os posts do top"
    elif nota > m_com:
        veredito = "Entre os posts comuns e o top"
    else:
        veredito = "Mais parecido com os posts comuns"
    a, b = st.columns([1, 1.1], gap="large", vertical_alignment="center")
    a.html(medidor(nota, m_top, m_com))
    metodo = str(res.get("metodo") or "")
    metodo = METODO.get(metodo, metodo.replace("_", " "))
    with b:
        st.html(f'<h3 style="font-size:1.25rem!important;color:var(--forest);margin:0!important;padding:0">{veredito}</h3>'
                f'<p style="font-size:.9rem;line-height:1.5;margin:6px 0">A nota começa em 50 e sobe ou desce pelo que o post tem. '
                f'Um post do top de verdade costuma ficar perto de {m_top}, não de 100.</p>'
                f'<p class="muted" style="font-size:.8rem;margin:0">Ela mede o quanto o post se parece com o top; '
                f'não prevê quanto ele vai engajar.</p>'
                f'<p class="muted" style="font-size:.74rem;margin:8px 0 0">Comparado com: {ui.E(f["nome"])} · '
                f'{ui.PLAT_NOME.get(res.get("plataforma"), "")} · {ui.E(metodo)}'
                f'{" · " + ui.E(res["aviso"]) if res.get("aviso") else ""}</p>')
        if res.get("nota_explicacao"):
            with st.expander("Como a nota foi calculada"):
                st.html(f'<p style="font-size:.84rem;line-height:1.55;margin:0">{ui.E(res["nota_explicacao"])}</p>')

    recs = [r for r in res.get("recomendacoes") or [] if isinstance(r, str)]
    if recs:
        ui.secao("O que fazer agora")
        st.html("".join(f'<div class="rec" data-n="{i}">{ui.E(r)}</div>' for i, r in enumerate(recs, 1)))

    pads = res.get("padroes") or []
    if pads:
        ui.secao("Padrões do top no seu post", "o que o post tem e o que não tem")

        def item(p):
            sobe = p.get("efeito") == "ajuda"
            cls = ("sim" if sobe else "ruim") if p.get("tem") else "nao"
            ic = ("✓" if sobe else "!") if p.get("tem") else "–"
            ef = "aparece mais no top" if sobe else "aparece menos no top"
            chips = ""
            if res.get("foco") != "B" and p.get("selo") in ("confirmado", "contradito"):
                chips += ui.chip(p["selo"], "c-" + ui.SELO_CLS[p["selo"]])
            if p.get("fragil"):
                chips += ui.chip("frágil", "c-warn")
            lift = f'{ui.dec(p["lift"], 1 if p["lift"] >= 1 else 2)}×' if ui._ok(p.get("lift")) else ""
            return (f'<div class="chk {cls}"><span class="ic">{ic}</span><div>{ui.E(str(p.get("rotulo") or ""))}'
                    f'<small>{ef} · {int(p.get("n_top") or 0)} posts do top</small>'
                    f'{f"<div style=margin-top:4px>{chips}</div>" if chips else ""}</div><em>{lift}</em></div>')
        tem_, falta = [p for p in pads if p.get("tem")], [p for p in pads if not p.get("tem")]
        x, y = st.columns(2, gap="medium")
        for col, nome, lst in [(x, "Seu post tem", tem_), (y, "Seu post não tem", falta)]:
            with col, st.container(border=True):
                st.html(f'<b style="font-size:.9rem">{nome}</b>' + ("".join(item(p) for p in lst[:8])
                        or '<p class="muted" style="margin:6px 0 0">Nada nesta lista.</p>'))
        st.html('<p class="muted" style="font-size:.76rem;margin:0">O número é quantas vezes a característica aparece no top em '
                'relação aos posts comuns. É uma descrição, não um conselho: os conselhos estão em “O que fazer agora”.</p>')

    nts = [n for n in res.get("notas_vs_top") or [] if ui._ok(n.get("valor"))]
    if nts:
        ui.secao("Você × mediana do top", "notas de 0 a 10")
        linhas = []
        for n in nts:
            med = n.get("mediana_top")
            marca = f'<u style="left:calc({min(10, med) * 10:.0f}% - 1px)"></u>' if ui._ok(med) else ""
            linhas.append(f'<div class="vs"><span>{ui.E(str(n.get("rotulo") or n.get("campo")))}</span>'
                          f'<div class="t"><i style="width:{min(10, n["valor"]) * 10:.0f}%"></i>{marca}</div>'
                          f'<em>{n["valor"]:g}{f" × {med:g}" if ui._ok(med) else ""}</em></div>')
        st.html("".join(linhas) + '<p class="muted" style="font-size:.76rem;margin:4px 0 0">Barra verde = seu post · '
                'traço escuro = mediana do top.</p>')

    par = res.get("parecidos") or []
    R = ui.ranking(f) if par else None
    if par and R is not None:
        ui.secao("Posts do top parecidos com o seu", "clique para ver por dentro")
        with st.container(key="grade_par"):
            for col, p in zip(st.columns(4), par[:4]):
                d = R[R.video_id == p.get("video_id")]
                if d.empty:
                    continue
                with col:
                    ui.post_card(d.iloc[0].to_dict(), f, "par", "mini")
                    if p.get("motivo"):
                        st.caption(str(p["motivo"]))


with dir_:
    if erro and erro[0] == "entrada":
        st.error(erro[1][:1].upper() + erro[1][1:] + ".", icon=":material/error:")
    elif erro:
        st.error("Não conseguimos falar com o modelo que lê o post. Confira a conexão e clique em “Avaliar” de novo; "
                 "o que você enviou continua aqui.", icon=":material/cloud_off:")
        st.caption(erro[1])
    res = st.session_state.get("avaliacao")
    if res and not erro:
        mostrar(res)
    elif not erro:
        ui.vazio("O resultado aparece aqui", "Você recebe uma nota de 0 a 100, a lista do que o post tem e não tem dos padrões "
                 "do top, recomendações práticas e posts reais parecidos com o seu.")
