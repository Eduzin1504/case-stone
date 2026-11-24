"""Playbook do foco em formato de matéria: capa, sumário lateral, capítulos com achados, ranking de perfis, posts
embutidos e pautas. O texto e a ordem dos capítulos vêm do markdown do playbook (PLAYBOOK.md / PLAYBOOK_B.md); os blocos
visuais vêm dos arquivos de dados. Seção do markdown que a página não reconhece sai como texto corrido, na mesma ordem."""
import datetime
import json
import math
import os
import re

import streamlit as st

import ui

E = ui.E
MAX_IG, MAX_YT = 6, 6  # posts embutidos por página; o resto vira miniatura clicável
PORTE = {"micro": "perfil pequeno", "medio": "perfil médio", "grande": "perfil grande"}
FRASE = {  # nome do padrão em linguagem de gente; o que não está aqui usa ui.nome_padrao
    ("segmento", "gestao_financas"): "Perfis de finanças e contabilidade",
    ("segmento", "alimentacao"): "Perfis de alimentação",
    ("tema_principal", "finanças"): "Posts que falam de finanças",
    ("tema_principal", "história de empreendedor"): "Histórias de empreendedor",
    ("tema_principal", "vendas"): "Posts com tema vendas",
    ("tem_rosto", "False"): "Posts sem rosto na tela",
    ("tipo_cta", "seguir"): "Posts que pedem para seguir o perfil",
    ("tipo_post", "imagem"): "Posts de imagem única",
    ("tipo_hook", "promessa"): "Posts que abrem com uma promessa",
    ("tipo_hook", "polêmica"): "Posts que abrem com uma polêmica",
    ("formato_video", "carrossel/estático"): "Carrossel ou post estático",
    ("formato_video", "talking head"): "Pessoa falando para a câmera",
    ("formato_video", "bastidores"): "Bastidores do negócio",
    ("usa_linguagem_regional", "True"): "Posts com o jeito de falar da região",
    ("tom", "técnico"): "Posts com tom técnico",
    ("duracao_faixa", "30-60s"): "Vídeos de 30 a 60 segundos",
    ("oferta_ou_beneficio_explicito", "True"): "Posts com benefício explícito",
    ("gatilho_identificacao", "pessoa_real"): "Gente de verdade no post",
    ("gatilho_identificacao", "nenhum"): "Post sem nada que crie identificação",
    ("convite_participacao", "True"): "Post que convida a participar",
    ("generico", "True"): "Post genérico",
    ("pilar_impulso", "comunidade"): "Posts de comunidade",
    ("pilar_impulso", "gestão e vendas"): "Posts de gestão e vendas",
}

CSS = """
<style>
.block-container:has(.pb-capa){padding-left:2.5rem;padding-right:2.5rem}
[data-testid="stMain"]:has(.pb-capa){scroll-behavior:smooth}
.pb-capa{max-width:900px;margin:0 0 14px}
.pb-capa .k,.cap>span,.rot{font:500 .72rem var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.pb-capa h1{font-size:3.3rem!important;line-height:1.03!important;margin:.6rem 0 0!important;max-width:24ch}
.pb-capa .fina{font-size:1.2rem;line-height:1.55;color:var(--fg);max-width:62ch;margin:18px 0 0}
.pb-capa .meta{display:flex;flex-wrap:wrap;gap:6px 22px;margin-top:20px;padding-top:14px;border-top:1px solid var(--line);font-size:.8rem;color:var(--muted)}
.pb-capa .meta b{font-weight:500;color:var(--fg)}

/* sumário lateral */
[data-testid="stLayoutWrapper"]:has(>.st-key-pb_rail){position:sticky;top:3.75rem}
.st-key-pb_rail [data-testid="stRadio"] label p{font-size:.84rem}
.pb-toc b{display:block;font:500 .72rem var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:8px}
.pb-toc a{display:block;font-size:.84rem;line-height:1.35;color:var(--muted);text-decoration:none;padding:6px 0 6px 12px;border-left:2px solid var(--line)}
.pb-toc a i{font:400 .7rem var(--mono);font-style:normal;margin-right:6px}
.pb-toc a:hover{color:var(--forest)}
.pb-toc a.on{color:var(--forest);font-weight:600;border-left-color:var(--forest);background:linear-gradient(90deg,var(--hl),transparent 70%)}
.st-key-pb_rail .nota-modo{font-size:.72rem;line-height:1.45;color:var(--muted);margin:0}

/* capítulo e texto */
.cap{margin:44px 0 0;padding-top:26px;border-top:1px solid var(--line);scroll-margin-top:4.5rem}
.cap.c1{margin-top:6px}
[data-testid="stMainBlockContainer"] .cap h2{font:400 2.2rem/1.08 "Anton","Arial Narrow",sans-serif!important;text-transform:uppercase;
color:var(--forest);letter-spacing:.01em;margin:8px 0 0!important;padding:0!important;max-width:27ch}
.ed{max-width:740px}
.ed p{font-size:1.04rem;line-height:1.7;margin:0 0 14px;color:var(--fg)}
.ed p:last-child{margin-bottom:0}
.ed a,.ach a,.rkp a,.lim a,.nota a{color:var(--forest);text-decoration:underline;text-decoration-color:var(--lime);text-decoration-thickness:3px;text-underline-offset:3px}
.ed code,.lim code,.nota code{font:400 .86em var(--mono);background:var(--sunk);padding:1px 5px;border-radius:5px}
.rot{margin:0 0 8px}
.bloco{margin:18px 0 0;display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
.bloco h3{font:600 1.3rem/1.2 "Lexend"!important;margin:0!important;padding:0!important;color:var(--fg)}
.bloco span{font-size:.84rem;color:var(--muted)}
.plat{font:500 .66rem var(--mono);text-transform:uppercase;letter-spacing:.06em;border:1px solid var(--line);border-radius:6px;padding:2px 7px;
color:var(--forest);background:var(--surface);white-space:nowrap}
.cred{font:400 .72rem/1.4 var(--mono);color:var(--muted);margin:0;overflow-wrap:anywhere}
.nota{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px 20px;max-width:740px}
.nota b.t{display:block;font-size:.95rem;margin-bottom:6px;color:var(--forest)}
.nota p,.nota li{font-size:.92rem;line-height:1.6;margin:0}
.nota ul{margin:0;padding-left:18px}.nota li+li{margin-top:6px}

/* como ler: régua e selos */
.regua{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.rg{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px 18px}
.rg .il{height:70px;display:flex;flex-direction:column;justify-content:center;gap:7px;margin-bottom:12px;padding-bottom:12px;border-bottom:1px dashed var(--line)}
.rg .il.f{align-items:flex-start;font:500 .78rem var(--mono);color:var(--forest);gap:4px}
.rg .il.f hr{width:170px;max-width:100%;height:2px;border:0;background:var(--forest);margin:0}
.rg .il.b div{display:grid;grid-template-columns:1fr 104px;gap:8px;align-items:center;font-size:.7rem;color:var(--muted)}
.rg .il.b i{display:block;height:12px;border-radius:6px;background:var(--data-soft)}
.rg .il.b i.on{background:linear-gradient(90deg,var(--data) 50%,var(--lime) 50%)}
.rg .il.d{flex-direction:row;align-items:center;justify-content:flex-start;gap:6px}
.rg .il.d i{width:14px;height:14px;border-radius:50%;background:var(--data-soft)}
.rg .il.d i.on{background:var(--forest);box-shadow:0 0 0 4px var(--lime)}
.rg .n{font:500 .7rem var(--mono);color:var(--muted)}
.rg b{display:block;font-size:.98rem;margin:2px 0 4px}
.rg p{font-size:.84rem;line-height:1.5;color:var(--muted);margin:0}
.selos{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.selo{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.selo .par{display:flex;gap:14px;margin-bottom:12px;min-height:36px}
.selo .par span{display:flex;flex-direction:column;align-items:center;gap:4px;font-size:.66rem;color:var(--muted)}
.selo .par i{width:18px;height:18px;border-radius:50%;border:2px solid #9db0a4;box-sizing:border-box}
.selo .par i.s{background:var(--data);border-color:var(--data)}.selo .par i.n{background:var(--bad);border-color:var(--bad)}
.selo .par i.q{width:10px;height:10px;border-radius:3px}
.selo .par.pts{gap:5px;align-items:center}
.selo p{font-size:.84rem;line-height:1.5;margin:8px 0 0;color:var(--muted)}
.selo .chip{margin:0}

/* achado */
[class*="st-key-achado_"],[class*="st-key-rkp_"],[class*="st-key-caso_"]{border-top:1px solid var(--line);padding-top:22px;margin-top:6px}
.ach{display:grid;grid-template-columns:118px minmax(0,1fr);gap:0 18px;align-items:start}
.ach .n{font:400 3.3rem/.95 "Anton";color:var(--forest);white-space:nowrap}
.ach.dn .n{color:var(--bad)}
.ach .n small{display:block;font:500 .7rem/1.3 "Lexend";color:var(--muted);margin-top:8px;white-space:normal}
.ach h3{font:600 1.14rem/1.3 "Lexend"!important;margin:0!important;padding:0!important;color:var(--fg)}
.ach p{margin:6px 0 12px;font-size:.94rem;line-height:1.6;color:var(--fg)}
.ach .pd-b{max-width:420px;margin-bottom:12px}
.ach .chip{margin-bottom:0}
.menos{display:grid;gap:0;max-width:740px}
.menos div{display:grid;grid-template-columns:74px minmax(0,1fr) auto;gap:14px;align-items:baseline;padding:10px 0;border-bottom:1px solid var(--line);font-size:.92rem}
.menos div:last-child{border:0}
.menos b{font:400 1.5rem/1 "Anton";color:var(--bad)}
.menos em{font:400 .76rem var(--mono);font-style:normal;color:var(--muted);text-align:right}
.tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.tile{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.tile b{display:block;font:400 2.2rem/1 "Anton";color:var(--forest)}
.tile>span{display:block;font-size:.9rem;font-weight:600;margin:8px 0 2px}
.tile small{font-size:.74rem;color:var(--muted)}

/* mercado × ads */
.lado{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px 20px}
.lado h3{font:600 1.05rem/1.3 "Lexend"!important;margin:0 0 2px!important;padding:0!important}
.lado>p{font-size:.8rem;line-height:1.45;color:var(--muted);margin:0 0 14px}
.lado .it{padding:10px 0;border-top:1px solid var(--line)}
.lado .it b{display:block;font-size:.88rem;font-weight:600;margin-bottom:6px}
.lado .it b em{font:500 .8rem var(--mono);font-style:normal;color:var(--forest);float:right}
.lado .it small{display:block;font-size:.74rem;line-height:1.4;color:var(--muted);margin-top:6px}
.lado .ads div{padding:7px 0;font-size:.8rem;grid-template-columns:minmax(0,1.7fr) minmax(0,1fr) 54px}
.lado .ads span{white-space:normal;line-height:1.3}.lado .ads small{margin-top:2px}
.cit{margin:10px 0;padding:4px 0 4px 24px;border-left:6px solid var(--lime);max-width:800px}
.cit .q{font:400 2.5rem/1.05 "Anton";text-transform:uppercase;color:var(--forest);margin:0 0 12px}
.cit p{font-size:1.04rem;line-height:1.7;margin:0}

/* ranking de perfis */
.rkp{display:grid;grid-template-columns:70px minmax(0,1fr);gap:0 12px}
.rkp .pos{font:400 3.6rem/.9 "Anton";color:var(--forest)}
.rkp h3{font:600 1.36rem/1.2 "Lexend"!important;margin:0!important;padding:0!important;color:var(--fg);overflow-wrap:anywhere}
.rkp .desc{font-size:.86rem;color:var(--muted);margin:3px 0 0}
.rkp .quem{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;font-size:.82rem;color:var(--muted);margin:10px 0 0}
.rkp .quem a{font-weight:600}
.rkp .porque{font-size:1rem;line-height:1.65;margin:12px 0}
.rkp .porque b{color:var(--forest)}
.rkp .chip{margin-bottom:0}

/* foco B: intenção, falas, recomendações */
.duo{display:grid;gap:14px}
.duo div b{display:block;font:400 3.6rem/.95 "Anton";color:var(--forest)}
.duo div.s b{color:var(--muted)}
.duo div span{display:block;font-size:.92rem;line-height:1.45;margin-top:6px}
.duo div i{display:block;height:10px;border-radius:5px;background:var(--data);margin-top:8px;min-width:4px}
.duo div.s i{background:var(--data-soft)}
.duo small{font-size:.74rem;color:var(--muted)}
.falas{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.fala{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px 18px 14px}
.fala::before{content:"“";display:block;font:400 2.4rem/.6 "Anton";color:var(--lime);-webkit-text-stroke:1px var(--forest);margin:6px 0 4px}
.fala p{font-size:1.04rem;line-height:1.45;margin:0 0 10px;font-weight:500;color:var(--forest);overflow-wrap:anywhere}
.fala span{font-size:.76rem;color:var(--muted)}
.recs{display:grid;gap:10px;max-width:800px}
.rc{display:grid;grid-template-columns:62px minmax(0,1fr);gap:0 8px;background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px 22px 18px 18px}
.rc>b{font:400 3rem/.9 "Anton";color:var(--forest)}
.rc h3{font:600 1.1rem/1.35 "Lexend"!important;margin:0 0 6px!important;padding:0!important}
.rc p{font-size:.94rem;line-height:1.6;margin:0;color:var(--fg)}

/* pautas (criativos) */
[class*="st-key-pauta_"]{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:22px 24px 24px;margin-top:10px}
.pauta-h>span{font:400 1rem/1 "Anton";text-transform:uppercase;letter-spacing:.04em;color:var(--forest);background:var(--hl);padding:3px 8px}
.pauta-h h3{font:600 1.32rem/1.25 "Lexend"!important;margin:12px 0 10px!important;padding:0!important;max-width:30ch}
.pauta-h .chip{white-space:normal;margin-bottom:0}
.mock{width:100%;max-width:252px;border:8px solid #14231b;border-radius:30px;background:var(--forest);overflow:hidden;margin:0 auto}
.mock .top{display:flex;align-items:center;gap:8px;padding:9px 12px;background:#fff;font-size:.74rem;font-weight:600}
.mock .top i{width:22px;height:22px;border-radius:50%;background:var(--lime);display:grid;place-items:center;font:400 .72rem "Anton";font-style:normal;color:var(--forest)}
.mock .capa{aspect-ratio:4/5;display:flex;flex-direction:column;justify-content:center;padding:34px 16px 30px;position:relative;box-sizing:border-box}
.mock.v .capa{aspect-ratio:9/16}
.mock .capa p{font:400 1.3rem/1.14 "Anton";text-transform:uppercase;color:#fff;margin:0;overflow-wrap:anywhere}
.mock .capa p.m{font-size:1.06rem}.mock .capa p.g{font-size:.9rem;line-height:1.2}
.mock .capa p::after{content:"";display:block;width:44px;height:6px;background:var(--lime);margin-top:12px}
.mock .capa .tp{position:absolute;left:16px;top:13px;font:500 .6rem var(--mono);color:var(--lime);letter-spacing:.08em;text-transform:uppercase}
.mock .capa .as{position:absolute;left:16px;bottom:12px;font:500 .64rem "Lexend";color:#bcd6c8}
.mock .pts{display:flex;gap:4px;justify-content:center;padding:8px;background:#fff}
.mock .pts i{width:5px;height:5px;border-radius:50%;background:#c9d6cd}.mock .pts i:first-child{background:var(--forest)}
[class*="st-key-pauta_"] [data-testid="stElementContainer"]:has(.mock){position:sticky;top:4.5rem}
.mock-l{text-align:center;font-size:.72rem;color:var(--muted);margin:8px 0 0}
.tl li small{display:block;font-size:.74rem;color:var(--muted);margin-bottom:2px}
.cta{background:var(--forest);border-radius:14px;padding:16px 20px}
.cta span{display:block;font:500 .7rem var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--lime);margin-bottom:6px}
.cta p{margin:0;font-size:1rem;line-height:1.5;font-weight:500;color:#fff}
[class*="st-key-pauta_"] [data-testid="stCode"] pre{background:var(--bg);border:1px solid var(--line);border-radius:10px}
[class*="st-key-pauta_"] [data-testid="stCode"] code{font-family:"Lexend",system-ui,sans-serif;font-size:.9rem;line-height:1.6}

/* próximo passo e limitações */
.passos.dois{grid-template-columns:1fr 1fr;max-width:800px}
.passos.dois .passo p{color:var(--fg);font-size:.92rem;line-height:1.55}.passos.dois .passo b{display:inline;font-size:inherit}
.lim{background:var(--sunk);border-radius:14px;padding:18px 22px;max-width:800px}
.lim ul{margin:0;padding-left:18px}
.lim li,.lim p{font-size:.88rem;line-height:1.6;color:var(--muted);margin:0}
.lim li+li{margin-top:8px}.lim li b{color:var(--fg)}
[class*="st-key-d_"] button{padding:0;min-height:0;font-size:.8rem}
/* miniaturas estreitas: número e rótulo na mesma linha, quebrando quando não cabe */
.block-container:has(.pb-capa) .pc.mini .pc-nums{flex-wrap:wrap;gap:1px 10px}
.block-container:has(.pb-capa) .pc.mini .pc-nums span{display:flex;gap:4px;align-items:baseline}
.block-container:has(.pb-capa) .pc.mini .pc-nums b{display:inline}

@media (max-width:900px){
 .selos{grid-template-columns:1fr 1fr}
 .pb-capa h1{font-size:2.6rem!important}
}
@media (max-width:640px){
 .block-container:has(.pb-capa){padding-left:1rem;padding-right:1rem}
 .pb-capa h1{font-size:2.15rem!important}
 .pb-capa .fina{font-size:1.04rem}
 [data-testid="stMainBlockContainer"] .cap h2{font-size:1.7rem!important}
 [data-testid="stLayoutWrapper"]:has(>.st-key-pb_rail){position:static}
 .pb-toc{display:flex;flex-wrap:wrap;gap:6px}
 .pb-toc b{width:100%;margin:0}
 .pb-toc a,.pb-toc a.on{border:1px solid var(--line);border-radius:99px;padding:4px 10px;font-size:.78rem;background:var(--surface)}
 .regua,.falas,.tiles,.passos.dois{grid-template-columns:1fr}
 .ach{grid-template-columns:1fr;gap:10px}
 .ach .n small{display:inline;margin-left:8px}
 .rkp{grid-template-columns:46px minmax(0,1fr)}.rkp .pos{font-size:2.4rem}
 .rkp h3{font-size:1.16rem!important}
 .menos div{grid-template-columns:62px minmax(0,1fr)}.menos em{grid-column:2;text-align:left}
 .cit .q{font-size:1.9rem}
 .rc{grid-template-columns:44px minmax(0,1fr);padding:16px}.rc>b{font-size:2.2rem}
 [class*="st-key-pauta_"]{padding:16px}
 .emb-ig,.fone-yt,[class*="st-key-igl_"]{max-width:100%!important}
 [class*="st-key-pauta_"] [data-testid="stElementContainer"]:has(.mock){position:static}
 /* miniaturas dos achados: 3 por linha no celular */
 [class*="st-key-grade_ac"] [data-testid="stHorizontalBlock"]>[data-testid="stColumn"],
 [class*="st-key-grade_pb"] [data-testid="stHorizontalBlock"]>[data-testid="stColumn"]{min-width:calc(33.33% - 7px)!important;flex:0 0 calc(33.33% - 7px)!important;width:calc(33.33% - 7px)!important}
}
</style>
"""
# Atenção: nada de "<" seguido de letra ou número dentro do script (o st.html descarta o script inteiro).
SPY = """<script>(function(){if(window.__pbSpy)return;window.__pbSpy=1;var t=0;
function f(){t=0;var c=document.querySelectorAll('.cap[id]');if(!c.length)return;var at=c[0].id;
c.forEach(function(x){if(170>x.getBoundingClientRect().top)at=x.id});
document.querySelectorAll('.pb-toc a').forEach(function(a){a.classList.toggle('on',a.getAttribute('href')==='#'+at)})}
document.addEventListener('scroll',function(){if(!t)t=requestAnimationFrame(f)},true);setTimeout(f,500)})();</script>"""


# ---------------------------------------------------------------- markdown -> pedaços
def paragrafos(txt):
    return [p.strip() for p in re.split(r"\n\s*\n", txt) if p.strip()]


def itens(txt):
    """Itens de lista (- ou 1.) de um trecho do markdown."""
    return [re.sub(r"^(?:-|\d+\.) +", "", l.strip()) for l in txt.splitlines() if re.match(r"^(?:-|\d+\.) +", l.strip())]


def texto_puro(txt):
    """Parágrafos que não são lista, tabela nem citação."""
    return [p for p in paragrafos(txt) if not re.match(r"^(?:-|\d+\.|\||>|#) ?", p)]


def ids_dos_links(txt):
    return list(dict.fromkeys(re.findall(r"\(https?://[^)\s]*?/(?:p|reel|shorts)/([\w-]+)", txt)))


def prosa(*ps):
    ps = [p for p in ps if p]
    if ps:
        st.html('<div class="ed">' + "".join(f"<p>{p}</p>" for p in ps) + "</div>")


def nota(titulo, corpo):
    st.html(f'<div class="nota"><b class="t">{E(titulo)}</b>{corpo}</div>')


def ver_numeros(txt):
    """Sem tabela na página: quem quiser a tabela do markdown abre aqui."""
    t = "\n".join(l for l in txt.splitlines() if l.startswith("|"))
    if t:
        with st.expander("Ver os números"):
            st.markdown(t)


def nome_simples(campo, valor):
    return FRASE.get((campo, str(valor))) or ui.nome_padrao(campo, valor)


def br(s):
    return float(str(s).replace(",", "."))


# ---------------------------------------------------------------- posts: destaque (embutido) e miniaturas
def credito(row):
    arroba = row.get("channel_id") if row.get("plataforma") == "instagram" and isinstance(row.get("channel_id"), str) else None
    p = ["@" + arroba if arroba else str(row.get("canal") or "")]
    if ui._ok(row.get("er")):
        p.append(f"ER {ui.pct(row['er'])}")
    if ui._ok(row.get("resid")):
        p.append(f"{ui.vezes(row['resid'])} o esperado")
    return " · ".join(x for x in p if x)


def destaque(row, f, chave):
    """Post principal de um bloco: player do YouTube, embed do Instagram ou a prévia local. Passou do limite de
    embutidos da página, vira miniatura clicável."""
    vid, plat = row["video_id"], row["plataforma"]
    if plat == "youtube" and uso["yt"] < MAX_YT:
        uso["yt"] += 1
        ui.embed_youtube(vid)
    elif plat == "instagram" and uso["ig"] < MAX_IG and (modo == "embed" or row.get("tem_midia")):
        uso["ig"] += 1
        if modo == "embed":
            ui.embed_instagram(vid)
        else:
            ui.post_instagram_local(row, f, f"{chave}_{vid}")
    else:
        ui.post_card(row, f, chave)
        return
    vistos.add(vid)
    st.html(f'<p class="cred">{E(credito(row))}</p>')
    st.button("Ver a leitura deste post", key=f"d_{chave}_{vid}", type="tertiary", icon=":material/arrow_forward:",
              on_click=ui.abrir_post, args=(f["id"], vid))


def miniaturas(rows, f, chave, colunas=3):
    if rows:
        with st.container(key=f"grade_{chave}"):
            for col, row in zip(st.columns(colunas), rows[:colunas]):
                with col:
                    if ui._ok(row.get("resid")):
                        ui.post_card(row, f, chave, "mini")
                    else:  # post que não concorre ao top: só a imagem e a legenda com o que existe
                        ui.post_card(row, f, chave, "mini nu")
                        st.html(f'<p class="cred">{E(credito(row))}</p>')


def posts_por_id(ids, *bases):
    """Linhas do ranking, na ordem pedida; cada base é (ranking, fonte). Devolve [(linha, fonte)]."""
    out = []
    for i in ids:
        for Rb, fb in bases:
            d = Rb[Rb.video_id == i] if Rb is not None else None
            if d is not None and len(d):
                out.append((d.iloc[0].to_dict(), fb))
                break
    return out


def exemplos(campo, valor, plat, n=3):
    """Até n posts do top da plataforma que têm o padrão (mesma regra da página Padrões)."""
    if R is None:
        return []
    t = R[R.top & (R.plataforma == plat)]
    v = {"True": "sim", "False": "não"}.get(str(valor), str(valor))
    if f"r_{campo}" in t:
        m = t[f"r_{campo}"].astype(str) == v
    elif campo == "segmento":
        m = t.seg.astype(str) == str(valor)
    elif campo == "tipo_post":
        m = t.formato_post == {"carrossel": "Carrossel", "imagem": "Imagem", "reel": "Reels"}.get(valor, valor)
    elif campo in ("tipo_criador", "duracao_faixa") and campo in t:
        m = t[campo].astype(str) == str(valor)
    else:
        return []
    return t[m].sort_values(["tem_midia", "resid"], ascending=False).drop_duplicates("canal").head(n).to_dict("records")


def barras(a, b, rot_a="top", rot_b="comuns"):
    """Mini-barra top × controle (frações)."""
    mx = max(a, b, .01)
    return (f'<div class="pd-b"><div><span>{rot_a}</span><i style="width:{a / mx * 100:.0f}%"></i><em>{ui.pct(a, 0)}</em></div>'
            f'<div><span>{rot_b}</span><i style="width:{b / mx * 100:.0f}%"></i><em>{ui.pct(b, 0)}</em></div></div>')


def achado_html(p):
    baixo = p["lift"] < 1
    chips = ""
    if isinstance(p.get("selo"), str) and p["selo"] != "inconclusivo":
        chips += ui.chip(p["selo"], "c-" + ui.SELO_CLS.get(p["selo"], "mut"))
    if p["n_top"] < 5:
        chips += ui.chip("frágil", "c-warn")
    c = p.get("confianca")
    if isinstance(c, str):
        chips += ui.chip({"não validado": "sem revisão humana", "dado objetivo": "dado objetivo"}.get(c, f"confiança {c}"), "c-line")
    chips += ui.chip(f"{int(p['n_top'])} posts do top", "c-mut")
    return (f'<div class="ach {"dn" if baixo else ""}"><div class="n">{ui.dec(p["lift"], 2 if baixo else 1)}<span class="x">×</span>'
            f'<small>{"menos" if baixo else "mais"} no top</small></div><div><h3>{E(nome_simples(p["campo"], p["valor"]))}</h3>'
            f'<p>Aparece em {ui.pct(p["freq_top"], 0)} dos posts do top e em {ui.pct(p["freq_resto"], 0)} dos posts comuns.</p>'
            f'{barras(p["freq_top"], p["freq_resto"])}<div>{chips}</div></div></div>')


# ---------------------------------------------------------------- capítulos
def regua_html():
    return ('<div class="regua">'
            '<div class="rg"><div class="il f"><span>curtidas + comentários</span><hr><span>seguidores</span></div>'
            '<span class="n">passo 1</span><b>Medimos o engajamento</b><p>A nota de cada post é o ER: curtidas mais comentários, '
            'divididos pelos seguidores do perfil.</p></div>'
            '<div class="rg"><div class="il b"><div><i style="width:46%"></i>esperado</div><div><i class="on"></i>o que o post fez</div></div>'
            '<span class="n">passo 2</span><b>Comparamos com o esperado</b><p>Um modelo estima quanto cada post deveria engajar pelo '
            'tamanho do perfil, formato, idade do post e histórico do criador. Assim perfil pequeno não leva vantagem.</p></div>'
            '<div class="rg"><div class="il d"><i class="on"></i>' + "<i></i>" * 9 + '</div>'
            '<span class="n">passo 3</span><b>Ficamos com o top 10%</b><p>São os posts que mais passaram do esperado, em cada '
            'plataforma e faixa de tamanho. Cada criador entra com no máximo 3 posts.</p></div></div>')


def selo_html(nome, cls, par, texto):
    return f'<div class="selo"><div class="par {"pts" if "q" in par else ""}">{par}</div>{ui.chip(nome, cls)}<p>{texto}</p></div>'


def cap_como_ler(txt):
    it = {m.group(1): m.group(2) for m in (re.match(r"^\*\*(.+?):\*\*\s*(.+)$", x) for x in itens(txt)) if m}
    prosa("Todo número deste playbook sai da mesma régua. Ela tem três passos.")
    st.html(regua_html())
    prosa(ui.md_inline("**Lift** é o número grande que aparece ao lado de cada padrão: " + it["Lift"])
          if "Lift" in it else "", "Cada padrão também leva um selo, que diz o quanto dá para confiar nele.")
    par = lambda a, b: f'<span><i class="{a}"></i>mercado</span><span><i class="{b}"></i>Ads</span>'
    st.html('<div class="selos">'
            + selo_html("confirmado", "c-ok", par("s", "s"), "Funciona no mercado e também nos Ads do Impulso.")
            + selo_html("contradito", "c-bad", par("s", "n"), "Mercado e Ads apontam em direções opostas.")
            + selo_html("só mercado", "c-mut", par("s", ""), "Aparece no mercado, mas ainda não foi testado nos Ads.")
            + selo_html("frágil", "c-warn", '<i class="q s"></i>' * 3 + '<i class="q"></i>' * 2,
                        "Menos de 5 posts do top sustentam o padrão. É pista, não regra.") + "</div>")
    if "Confiança" in it:
        prosa(ui.md_inline("**Confiança** é a " + it["Confiança"]))


def cap_metodo_b(txt):
    prosa("Olhamos para o que o próprio negócio posta para quem compra dele: padaria, salão, loja de bairro, pet shop, ateliê. "
          "A régua é a mesma do outro foco e tem três passos.")
    st.html(regua_html())
    prosa("Quatro palavras aparecem o tempo todo daqui para a frente.")
    st.html('<div class="selos">'
            + selo_html("top", "c-top", '<i class="q s"></i>', "Os posts que mais passaram do esperado para o tamanho do perfil.")
            + selo_html("controle", "c-mut", '<i class="q"></i>', "Posts comuns, sorteados fora do top. É com eles que o top é comparado.")
            + selo_html("intenção de compra", "c-ok", '<i class="q s"></i><i class="q s"></i>',
                        "Comentário de cliente que pergunta preço, endereço ou entrega, ou diz que quer.")
            + selo_html("frágil", "c-warn", '<i class="q s"></i>' * 3 + '<i class="q"></i>' * 2,
                        "Menos de 5 posts do top sustentam o achado. É pista, não regra.") + "</div>")
    with st.expander("Ver a metodologia completa"):
        st.markdown(txt)


def cap_padroes_a(txt):
    if ps is None or R is None:
        return False
    ig = ps[(ps.plataforma == "instagram") & (ps.n_top >= 5) & ps.lift.notna()]
    mais = ig[ig.lift >= 1.5].sort_values("lift", ascending=False).head(10).to_dict("records")
    menos = ig[ig.lift <= 0.65].sort_values("lift").head(6).to_dict("records")
    if not mais:
        return False
    prosa("Comparamos os posts do top com posts comuns dos mesmos perfis, no Instagram. O número grande diz quantas vezes cada "
          "característica aparece mais no top.", "Ao lado de cada achado estão posts reais do top que têm aquela característica. "
          "Clique em qualquer um para ver por dentro.")
    for i, p in enumerate(mais):
        ex = exemplos(p["campo"], p["valor"], "instagram")
        with st.container(key=f"achado_{i}"):
            a, b = st.columns([1.3, 1] if i < 2 else [1.05, 1], gap="large")
            with a:
                st.html(achado_html(p))
                if i < 2 and len(ex) > 1:
                    miniaturas(ex[1:], fonte, f"ac{i}")
            with b:
                if i < 2 and ex:
                    destaque(ex[0], fonte, f"ac{i}")
                else:
                    miniaturas(ex, fonte, f"ac{i}")
    if menos:
        st.html('<div class="bloco"><h3>O que aparece menos no top</h3><span>comparado com os posts comuns</span></div>')
        st.html('<div class="menos">' + "".join(
            f'<div><b>{ui.dec(p["lift"], 2)}<span class="x">×</span></b><span>{E(nome_simples(p["campo"], p["valor"]))}</span>'
            f'<em>{ui.pct(p["freq_top"], 0)} no top · {ui.pct(p["freq_resto"], 0)} nos comuns</em></div>' for p in menos) + "</div>")
    leitura = itens(txt.split("**Leitura para o Impulso:**")[1]) if "**Leitura para o Impulso:**" in txt else []
    if leitura:
        nota("Leitura para o Impulso", "<ul>" + "".join(f"<li>{ui.md_inline(x)}</li>" for x in leitura) + "</ul>")
    ver_numeros(txt)


def cap_ads(txt):
    ii = ui.ler_csv("impulso_interno.csv")
    if ps is None or "selo" not in ps or ii is None or "ctr" not in ii:
        return False
    geral = ps[ps.plataforma == "todas"]
    pega = lambda c, v: next(iter(geral[(geral.campo == c) & (geral.valor == v)].to_dict("records")), None)
    prosa("O mercado mede reação: curtida e comentário. Os Ads do Impulso medem clique. Colocamos os dois lado a lado para ver "
          "onde eles concordam.")
    a, b = st.columns(2, gap="medium")
    its = []
    for c, v in [("gatilho_identificacao", "pessoa_real"), ("convite_participacao", "True"), ("generico", "True"),
                 ("gatilho_identificacao", "nenhum")]:
        p = pega(c, v)
        if not p:
            continue
        selo = ui.chip(p["selo"], "c-" + ui.SELO_CLS.get(p["selo"], "mut")) if p["selo"] != "inconclusivo" else ""
        por = " · ".join(f"{ui.PLAT_NOME[x.plataforma]} {ui.dec(x.lift, 2)}×" for x in
                         ps[(ps.campo == c) & (ps.valor == v) & (ps.plataforma != "todas")].itertuples())
        casa = "" if p["selo"] == "inconclusivo" else ("Nos Ads: mais comum nos de CTR alto. " if p["dif_interna"] > 0
                                                      else "Nos Ads: mais comum nos de CTR baixo. ")
        its.append(f'<div class="it"><b>{E(nome_simples(c, v))}<em>{ui.dec(p["lift"], 2)}×</em></b>{barras(p["freq_top"], p["freq_resto"])}'
                   f'<small>{selo}{casa}{E(por)}</small></div>')
    a.html('<div class="lado"><h3>No mercado: o que engaja</h3><p>Quanto do top e dos posts comuns tem cada característica. '
           'O número à direita é o lift.</p>' + "".join(its) + "</div>")
    ii = ii[ii.ctr.notna()].sort_values("ctr", ascending=False)
    mx = ii.ctr.max()
    linhas = []
    for x in ii.to_dict("records"):
        marcas = []
        if str(x.get("convite_participacao")) == "True":
            marcas.append("convida a participar")
        if isinstance(x.get("gatilho_identificacao"), str) and x["gatilho_identificacao"] != "nenhum":
            marcas.append(ui.valor_nome(x["gatilho_identificacao"]))
        if str(x.get("generico")) == "True":
            marcas.append("genérico")
        linhas.append(f'<div class="{E(str(x.get("desempenho", "")))}"><span>{E(str(x["criativo"]))}'
                      f'<small>{E(" · ".join(marcas) or "sem gatilho de identificação")}</small></span>'
                      f'<i style="width:{x["ctr"] / mx * 100:.0f}%"></i><em>{ui.dec(x["ctr"], 2)}%</em></div>')
    b.html(f'<div class="lado"><h3>Nos Ads do Impulso: o que gera clique</h3><p>Taxa de clique (CTR) dos {len(ii)} anúncios da conta. '
           '<span style="color:var(--data)">■</span> alto <span style="color:var(--data-soft)">■</span> médio '
           '<span style="color:var(--bad)">■</span> baixo</p><div class="ads">' + "".join(linhas) + "</div></div>")
    ps_ = texto_puro(txt)
    tese = next((p for p in ps_ if "reação não é clique" in p), None)
    if tese:
        st.html('<blockquote class="cit"><p class="q">Reação não é clique</p><p>'
                + ui.md_inline(re.sub(r"^\*\*.+?\*\*\s*", "", tese)) + "</p></blockquote>")
    prosa(*[ui.md_inline(p) for p in ps_ if p is not tese])
    ver_numeros(txt)


def perfil(i, p, plat, f, Rb, com_destaque):
    canal = str(p["canal"])
    nome, _, desc = [x.strip() for x in canal.partition("|")]
    posts = Rb[(Rb.canal == canal) & (Rb.plataforma == plat)].sort_values(["top", "tem_midia", "resid"], ascending=False).head(3).to_dict("records")
    posts.sort(key=lambda r: r["video_id"] in vistos)  # o post que já foi embutido acima não abre o bloco de novo
    cid = p.get("channel_id") if isinstance(p.get("channel_id"), str) else (posts[0].get("channel_id") if posts else None)
    url = ui.link_canal(dict(channel_id=cid, plataforma=plat))
    ig = plat == "instagram"
    quem = f'<span class="plat">{ui.PLAT_NOME.get(plat, plat)}</span>'
    if url:
        quem += f'<a href="{E(url)}" target="_blank" rel="noopener">{E("@" + cid) if ig else "abrir o canal"} ↗</a>'
    quem += f'<span>{PORTE.get(p.get("porte"), "perfil")}, {ui.compacto(p.get("inscritos"))} {"seguidores" if ig else "inscritos"}</span>'
    fr = []
    if ui._ok(p.get("n_top")) and p["n_top"] > 0:
        n = int(p["n_top"])
        fr.append(f"Tem {n} {'posts' if n > 1 else 'post'} no top{', o limite por criador' if n == 3 else ''}"
                  + (f", com ER mediano de {ui.pct(p['er_mediano'])}." if ui._ok(p.get("er_mediano")) else "."))
    tema, fmt = (p.get(x) if isinstance(p.get(x), str) else None for x in ("tema", "formato"))
    if tema and fmt:
        fr.append(f"O que mais rende por lá: <b>{E(tema)}</b>, em formato <b>{E(fmt)}</b>.")
    elif fmt:
        fr.append(f"O formato que mais usa: <b>{E(fmt)}</b>.")
    if ui._ok(p.get("efeito_criador")) and p["efeito_criador"] > 0:
        fr.append(f"Engaja <b>{ui.dec(math.exp(p['efeito_criador']))} vezes</b> o esperado para o tamanho do perfil.")
    chips = "".join(ui.chip(ui.valor_nome(p[x]), "c-line", r) for x, r in
                    [("segmento", "segmento"), ("tema", "tema"), ("formato", "formato"), ("pilar", "pilar")] if isinstance(p.get(x), str))
    if ui._ok(p.get("n_posts")):
        chips += ui.chip(f"{int(p['n_posts'])} posts na base", "c-mut")
    cab = (f'<div class="rkp"><div class="pos">{i}</div><div><h3>{E(nome)}</h3>{f"<p class=desc>{E(desc)}</p>" if desc else ""}'
           f'<div class="quem">{quem}</div><p class="porque">{" ".join(fr)}</p><div>{chips}</div></div></div>')
    with st.container(key=f"rkp_{plat}_{i}"):
        a, b = st.columns([1.3, 1], gap="large")
        with a:
            st.html(cab)
            if com_destaque and len(posts) > 1:
                miniaturas(posts[1:], f, f"pf{plat[:2]}{i}")
        with b:
            if com_destaque and posts:
                destaque(posts[0], f, f"pf{plat[:2]}{i}")
            else:
                miniaturas(posts, f, f"pf{plat[:2]}{i}")


def cap_perfis(txt):
    if pf is None or R is None or "canal" not in pf:
        return False
    n_md = sum(l.startswith("|") for l in txt.splitlines()) - 2
    d = pf.sort_values("efeito_criador", ascending=False) if "efeito_criador" in pf else pf
    blocos = [(plat, d[d.plataforma == plat] if "plataforma" in d else d) for plat in (ui.plataformas(d) if "plataforma" in d else ["instagram"])]
    prosa("A ordem aqui não é de quem tem mais seguidores nem de quem tem mais curtidas. É de quem mais engaja acima do "
          "esperado para o próprio tamanho. Por isso perfil pequeno aparece na frente de perfil grande.")
    for plat, g in blocos:
        n = (n_md if n_md > 0 else 6) if plat == "instagram" else 5
        st.html(f'<div class="bloco"><h3>No {ui.PLAT_NOME.get(plat, plat)}</h3>'
                f'<span>os {min(n, len(g))} primeiros de {len(g)} perfis da lista</span></div>')
        for i, p in enumerate(g.head(n).to_dict("records"), 1):
            perfil(i, p, plat, fonte, R, com_destaque=i <= 3)
    extra = texto_puro(txt)
    if extra:
        nota("Vale notar", "".join(f"<p>{ui.md_inline(p)}</p>" for p in extra))


def cap_youtube(txt):
    if ps is None or R is None:
        return False
    yt = ps[(ps.plataforma == "youtube") & (ps.n_top >= 5) & (ps.lift >= 1.5) & (ps.campo != "porte")]
    yt = yt.sort_values("lift", ascending=False).head(6).to_dict("records")
    if not yt:
        return False
    tp = texto_puro(txt)
    prosa(ui.md_inline(tp[-1]) if len(tp) > 1 else "", "O YouTube entra como evidência complementar: a base é maior, mas só uma "
          "parte dos vídeos foi vista por inteiro.")
    st.html('<div class="tiles">' + "".join(
        f'<div class="tile"><b>{ui.dec(p["lift"])}<span class="x">×</span></b><span>{E(nome_simples(p["campo"], p["valor"]))}</span>'
        f'<small>{int(p["n_top"])} posts no top</small></div>' for p in yt) + "</div>")
    alvo = next((p for p in yt if p["campo"] == "formato_video"), yt[0])
    ex = exemplos(alvo["campo"], alvo["valor"], "youtube", 6)
    if ex:
        st.html(f'<div class="bloco"><h3>{E(nome_simples(alvo["campo"], alvo["valor"]))}, na prática</h3>'
                '<span>Shorts do top com essa característica</span></div>')
        for col, row, j in zip(st.columns([1, 1, 0.5]), ex[:2], "ab"):
            with col:
                destaque(row, fonte, f"yt{j}")
        miniaturas(ex[2:], fonte, "ytm", 4)
    if tp:
        st.html(f'<p class="muted" style="max-width:740px;font-size:.8rem">{ui.md_inline(tp[0])}</p>')


def roteiro_html(roteiro):
    lis = []
    for l in (x.strip() for x in roteiro.split("\n")):
        if not l:
            continue
        cab, sep, resto = l.partition(": ")
        if not sep or len(cab) > 90:
            lis.append(f"<li>{E(l)}</li>")
            continue
        rot_, _, obs = cab.partition(" (")
        lis.append(f'<li><b>{E(rot_.replace(" | ", " · "))}</b>{f"<small>{E(obs.rstrip(")"))}</small>" if obs else ""}{E(resto)}</li>')
    return '<ul class="tl">' + "".join(lis) + "</ul>"


def mock_html(c):
    """Capa do post na identidade do Impulso, em moldura de celular. Carrossel usa o texto do slide 1; vídeo, o gancho."""
    video = not re.match(r"(?i)carrossel", c["formato"])
    m = re.match(r'^Slide 1[^:]*:\s*["“](.+?)["”]', c["roteiro"])
    capa = (m.group(1) if m and not video else c["gancho"]).strip()
    tam = "" if len(capa) <= 70 else "m" if len(capa) <= 120 else "g"
    n = len(re.findall(r"(?m)^Slide \d+", c["roteiro"]))
    pts = '<div class="pts">' + "<i></i>" * min(n, 9) + "</div>" if n and not video else ""
    return (f'<div class="mock {"v" if video else ""}"><div class="top"><i>I</i>impulsostone</div><div class="capa">'
            f'<span class="tp">{"Reels" if video else "Carrossel"}</span><p class="{tam}">{E(capa)}</p>'
            f'<span class="as">@impulsostone</span></div>{pts}</div>'
            f'<p class="mock-l">{"Abertura do vídeo, com o gancho na tela" if video else f"Capa do carrossel, slide 1 de {n}"}</p>')


def cap_criativos(txt):
    cri = ui.tentar(lambda: json.load(open(f"{ui.P.DATA}/criativos_playbook.json", encoding="utf-8")))
    if not cri or R is None:
        return False
    prosa("Cada pauta abaixo foi escrita pelo agente a partir de posts reais do top e checada em quatro pontos: chamada para "
          "ação, convite à participação, linguagem genérica e tom do Impulso.",
          "Está tudo pronto para usar: a capa, o roteiro na ordem, a legenda para copiar e os posts que serviram de referência.")
    for i, r in enumerate(cri, 1):
        c = r["creatives"][0]
        refs = posts_por_id(c.get("inspirado_em", []), (R, fonte))
        with st.container(key=f"pauta_{i}"):
            st.html(f'<div class="pauta-h"><span>Pauta {i}</span><h3>{E(r["pedido"])}</h3>'
                    f'<div>{ui.chip(c["formato"], "c-line", "formato")}{ui.chip(c["pilar"], "c-line", "pilar")}</div></div>')
            a, b = st.columns([1, 1.7], gap="large")
            a.html(mock_html(c))
            b.html(f'<div class="hookq"><span>Gancho</span><p>{E(c["gancho"])}</p></div>'
                   f'<p class="rot" style="margin-top:16px">Roteiro</p>{roteiro_html(c["roteiro"])}')
            st.html('<p class="rot" style="margin:6px 0 -6px">Legenda pronta para copiar</p>')
            st.code(c["legenda"], language=None, wrap_lines=True)
            st.html(f'<div class="cta"><span>Chamada para ação</span><p>{E(c["cta"])}</p></div>')
            if refs:
                st.html('<p class="rot" style="margin:10px 0 -4px">Inspirado em posts reais do top</p>')
                if i == 1 or (i == 4 and any(x["plataforma"] == "youtube" for x, _ in refs)):
                    j = next((j for j, (x, _) in enumerate(refs) if x["plataforma"] == "youtube"), 0) if i == 4 else 0
                    x, y = st.columns([1, 1.3], gap="large")
                    with x:
                        destaque(refs[j][0], fonte, f"cr{i}")
                    with y:
                        miniaturas([x_ for n_, (x_, _) in enumerate(refs) if n_ != j], fonte, f"cr{i}", 2)
                else:
                    miniaturas([x for x, _ in refs], fonte, f"cr{i}", 4)


def cap_passos(txt):
    its = itens(txt)
    if not its:
        return False
    prosa("Padrão observado não é efeito medido. O que fecha a conta é um teste pequeno, com dinheiro e público iguais aos dos "
          "Ads que já rodaram.")
    st.html('<div class="passos dois">' + "".join(f'<div class="passo"><p>{ui.md_inline(x)}</p></div>' for x in its) + "</div>")


def cap_limites(txt):
    its = itens(txt)
    if its:
        st.html('<div class="lim"><ul>' + "".join(f"<li>{ui.md_inline(x)}</li>" for x in its) + "</ul></div>")
    else:
        st.html('<div class="lim">' + "".join(f"<p>{ui.md_inline(p)}</p>" for p in paragrafos(txt)) + "</div>")


@st.cache_data(ttl=600, show_spinner=False)
def _falas(db, v, n=4):
    """Comentários reais de clientes com intenção de compra (regex e modelo concordam). Sem nome de usuário: só o texto e
    o negócio. Um por negócio, variando o segmento."""
    c = ui.conectar(db)
    rows = c.execute("select c.texto, r.canal, r.segmento from comentarios c join ranking r using (video_id) "
                     "where c.intencao = 1 and c.regex = 1").fetchall()
    chaves = ["quanto", "valor", "preço", "preco", "endereço", "endereco", "encomend", "entrega", "quero", "agenda", "comprar"]
    melhor = {}
    for t, canal, seg in rows:
        t = " ".join((t or "").split())
        tl = t.lower()
        if not 20 <= len(t) <= 110 or "@" in t or re.search(r"\d{5,}", t) or any(x in tl for x in ("link", "http", "cobrar")):
            continue
        s = sum(k_ in tl for k_ in chaves)
        if s and (canal not in melhor or (s, -len(t)) > (melhor[canal][0], -len(melhor[canal][1]))):
            melhor[canal] = (s, t, seg)
    ordem = sorted(melhor.items(), key=lambda kv: (-kv[1][0], len(kv[1][1])))
    out, segs = [], set()
    for canal, (_, t, seg) in ordem:  # primeiro um por segmento; se faltar, completa
        if seg not in segs:
            segs.add(seg)
            out.append((t, canal.split("|")[0].strip(), seg))
    return out[:n]


def cap_intencao(txt):
    it = ui.intencao(fonte)
    if it is None:
        return False
    tp = texto_puro(txt)
    prosa(ui.md_inline(tp[0]) if tp else "")
    g = it.set_index("grupo")
    a, b = st.columns([1, 1.25], gap="large", vertical_alignment="center")
    if {"Mostra o preço", "Não mostra o preço"} <= set(g.index):
        s, n = g.loc["Mostra o preço"], g.loc["Não mostra o preço"]
        mx = max(s.pct, n.pct, .01)
        a.html(f'<div class="duo"><p class="rot" style="margin:0">Com preço × sem preço</p>'
               f'<div><b>{ui.pct(s.pct, 0)}</b><i style="width:{s.pct / mx * 100:.0f}%"></i><span>dos comentários mostram vontade de '
               f'comprar quando o post <b style="display:inline;font:inherit;font-weight:600">mostra o preço</b></span>'
               f'<small>{int(s.posts)} posts</small></div>'
               f'<div class="s"><b>{ui.pct(n.pct, 0)}</b><i style="width:{n.pct / mx * 100:.0f}%"></i><span>quando não mostra</span>'
               f'<small>{int(n.posts)} posts</small></div></div>')
    fm = it[~it.grupo.str.contains("preço")]
    if len(fm):
        import altair as alt
        fm = fm.assign(cor=["#b02d63" if "Humor" in x else "#1f9e55" for x in fm.grupo], rot=[ui.pct(x, 0) for x in fm.pct])
        base_ = alt.Chart(fm).encode(
            y=alt.Y("grupo:N", sort=list(fm.grupo), title=None, axis=alt.Axis(labelLimit=200, labelFontSize=13, labelColor="#14231b",
                                                                                ticks=False, domain=False, labelPadding=8)),
            x=alt.X("pct:Q", axis=None, scale=alt.Scale(domain=[0, max(fm.pct) * 1.25])))
        ch = (base_.mark_bar(cornerRadiusEnd=4, height=22).encode(
            color=alt.Color("cor:N", scale=None),
            tooltip=[alt.Tooltip("grupo:N", title="Formato"), alt.Tooltip("pct:Q", title="Comentários com intenção de compra", format=".0%"),
                     alt.Tooltip("posts:Q", title="Posts")])
            + base_.mark_text(align="left", dx=6, font="JetBrains Mono", fontSize=13, color="#14231b").encode(text="rot:N"))
        with b:
            st.html('<p class="rot" style="margin:0">Por formato: % dos comentários com intenção de compra</p>')
            st.altair_chart(ch.properties(height=52 * len(fm)).configure_view(strokeWidth=0).configure(font="Lexend", background="transparent"))
            st.html('<p class="cred">' + E(" · ".join(f"{x.grupo}: {int(x.posts)} posts" for x in fm.itertuples()))
                    + '. O formato que mais dá curtida é o que menos gera pergunta de compra.</p>')
    falas = ui.tentar(_falas, fonte["db"], ui.versao(fonte["db"]))
    if falas:
        st.html('<div class="bloco"><h3>Como é um comentário de quem quer comprar</h3><span>comentários reais de clientes, sem o nome</span></div>')
        st.html('<div class="falas">' + "".join(
            f'<div class="fala"><p>{E(t)}</p><span>cliente de {E(neg)} · {E(ui.valor_nome(seg))}</span></div>' for t, neg, seg in falas) + "</div>")
    prosa(*[ui.md_inline(p) for p in tp[1:]])
    ver_numeros(txt)


def cap_padroes_b(txt):
    blocos = [(re.match(r"^\*\*(\d+)\. (.+?)\*\*\s*(.*)$", b, flags=re.S), b) for b in paragrafos(txt)]
    if not any(m for m, _ in blocos) or R is None:
        return False
    prosa("Oito coisas separam os posts do top dos posts comuns nesta base. O número grande é o lift: quantas vezes a "
          "característica aparece mais (ou menos) no top.")
    n_dest = 0
    for m, b in blocos:
        if not m:
            lead = re.match(r"^\*\*(.+?)\*\*\s*(.*)$", b, flags=re.S)
            if lead:
                nota(lead.group(1).rstrip(":"), f"<p>{ui.md_inline(lead.group(2))}</p>")
            continue
        i, tit, corpo = int(m.group(1)), m.group(2), m.group(3)
        lift = re.search(r"lift (\d+(?:,\d+)?)", corpo)
        f1 = re.search(r"(\d+(?:,\d+)?)% d[oa] top contra (\d+(?:,\d+)?)% d[oa] controle", corpo)
        f2 = re.search(r"(\d+(?:,\d+)?)% d[oa] controle e (\d+(?:,\d+)?)% d[oa] top", corpo)
        top_, ctl = (br(f1.group(1)), br(f1.group(2))) if f1 else (br(f2.group(2)), br(f2.group(1))) if f2 else (None, None)
        baixo = bool(lift) and br(lift.group(1)) < 1
        num_ = (f'<div class="n">{lift.group(1)}<span class="x">×</span><small>{"menos" if baixo else "mais"} no top</small></div>'
                if lift else '<div class="n"></div>')
        chips = ui.chip("frágil", "c-warn") if "frágil" in tit.lower() else ""
        h = (f'<div class="ach {"dn" if baixo else ""}">{num_}<div><h3>{E(tit.rstrip("."))}</h3><p>{ui.md_inline(corpo)}</p>'
             f'{barras(top_ / 100, ctl / 100, "top", "controle") if top_ is not None else ""}<div>{chips}</div></div></div>')
        posts = [x for x, _ in posts_por_id(ids_dos_links(corpo), (R, fonte))]
        with st.container(key=f"achado_{i}"):
            if not posts:
                st.html(f'<div style="max-width:740px">{h}</div>')
                continue
            a, c_ = st.columns([1.3, 1], gap="large")
            a.html(h)
            with c_:
                if n_dest < 2 and len(posts) > 1:
                    n_dest += 1
                    destaque(posts[0], fonte, f"pb{i}")
                    miniaturas(posts[1:], fonte, f"pb{i}", 3)
                else:
                    miniaturas(posts, fonte, f"pb{i}", 3)


def cap_casos(txt):
    casos = [m for m in (re.match(r"^\*\*(.+?)\s*\((.+?)\)\.\*\*\s*(.*)$", x, flags=re.S) for x in itens(txt)) if m]
    if not casos:
        return False
    RA, fA = ui.ranking(ui.FOCOS["A"]), ui.FOCOS["A"]  # estes posts vêm da base antiga (a do outro foco)
    prosa("Estes quatro negócios vêm da base antiga e ficam fora da estatística. Valem como exemplo para olhar de perto: "
          "três que funcionam e um que mostra o limite de só ensinar.")
    for i, m in enumerate(casos, 1):
        nome, meta, corpo = m.groups()
        plat, _, resto = meta.partition(",")
        contra = corpo.lower().startswith("contraexemplo")
        posts = posts_por_id(ids_dos_links(corpo), (RA, fA), (R, fonte))
        cab = (f'<div class="rkp"><div class="pos">{i}</div><div><h3>{E(nome)}</h3><div class="quem"><span class="plat">{E(plat.strip())}</span>'
               f'<span>{E(resto.strip())}</span>{ui.chip("contraexemplo", "c-bad") if contra else ""}</div>'
               f'<p class="porque">{ui.md_inline(corpo)}</p></div></div>')
        with st.container(key=f"caso_{i}"):
            if not posts:
                st.html(cab)
                continue
            a, b = st.columns([1.3, 1], gap="large")
            with a:
                st.html(cab)
                for row, f_ in posts[1:2]:
                    miniaturas([row], f_, f"cs{i}")
            with b:
                destaque(posts[0][0], posts[0][1], f"cs{i}")


def cap_recs(txt):
    recs = [re.match(r"^\*\*(.+?)\*\*\s*(.*)$", x, flags=re.S) for x in itens(txt)]
    if not recs or not all(recs):
        return False
    prosa("Se o dono do negócio só puder levar uma página deste playbook, é esta.")
    st.html('<div class="recs">' + "".join(
        f'<div class="rc"><b>{i}</b><div><h3>{E(m.group(1).rstrip("."))}</h3><p>{ui.md_inline(m.group(2))}</p></div></div>'
        for i, m in enumerate(recs, 1)) + "</div>")


# trecho do título no markdown -> (rótulo no sumário, título que afirma, função)
CAPS = {
    "A": [("Como ler", "Como ler", "Três passos e quatro selos para ler os números", cap_como_ler),
          ("diferencia o top", "O que o top faz diferente", "Quem ensina a fazer a conta aparece mais no top", cap_padroes_a),
          ("Mercado × Ads", "Mercado × Ads", "O que dá curtida no mercado não é o que dá clique nos Ads", cap_ads),
          ("Perfis em destaque", "Perfis em destaque", "Quem engaja acima do próprio tamanho", cap_perfis),
          ("YouTube Shorts", "YouTube", "No YouTube, mostrar o negócio por dentro se destaca", cap_youtube),
          ("criativos", "As 5 pautas", "Cinco pautas prontas para o @impulsostone", cap_criativos),
          ("Próximo passo", "Próximo passo", "O próximo passo é um piloto em Ads", cap_passos),
          ("Limitações", "Limitações", "O que este playbook não prova", cap_limites)],
    "B": [("Metodologia", "Como ler", "Como chegamos a estes números", cap_metodo_b),
          ("descoberta principal", "Curtida não é pedido", "O que dá curtida não é o que dá pedido", cap_intencao),
          ("Padrões", "O que o top faz diferente", "Humor e bastidor se destacam. Foto de produto é o básico.", cap_padroes_b),
          ("Perfis em destaque", "Perfis em destaque", "Quem engaja acima do próprio tamanho", cap_perfis),
          ("Estudos de caso", "Estudos de caso", "Quatro negócios para olhar de perto", cap_casos),
          ("recomendações", "5 recomendações", "Cinco recomendações para o lojista", cap_recs),
          ("Limitações", "Limitações", "O que este playbook não prova", cap_limites)],
}
CAPA = {
    "A": ("Ensinar a conta engaja. Convidar a participar gera clique.", "clique",
          "Finanças explicadas na prática são o que mais separa o top dos posts comuns no Instagram. Mas reação não é clique: nos "
          "Ads do Impulso, ganha o post com gente de verdade e convite para participar. No fim, cinco pautas prontas para testar."),
    "B": ("O que dá curtida não é o que dá pedido", "pedido",
          "Humor da rotina e bastidor fazem o post de um pequeno negócio aparecer. Preço à mostra é o que faz o cliente perguntar "
          "como comprar. São dois trabalhos diferentes, e o lojista precisa dos dois."),
}

# ---------------------------------------------------------------- página
fonte = ui.fonte_atual()
k = fonte["id"]
md = ui.secao_md(fonte["playbook"], "")
if not md.strip():
    ui.titulo("Playbook", grifo="Playbook")
    ui.sem_dados(fonte, "playbook")
    st.stop()

st.html(CSS)
ui.estilo_embeds()
partes = re.split(r"^## +(.+)$", md, flags=re.M)  # [intro, título, corpo, título, corpo…]
secoes = []
for t, txt in zip(partes[1::2], partes[2::2]):
    t = t.strip()
    c = next((c for c in CAPS[k] if c[0].lower() in t.lower()), None)
    secoes.append((c[1], c[2], c[3], txt) if c else (re.sub(r"^\d+\.\s*", "", t),) * 2 + (None, txt))
R, ps, pf = ui.ranking(fonte), ui.padroes(fonte), ui.ler_csv(fonte["perfis"])
uso, vistos = {"ig": 0, "yt": 0}, set()

# capa
m1 = re.search(r"^# +(.+)$", partes[0], flags=re.M)
intro = re.sub(r"^# +.+$", "", partes[0], count=1, flags=re.M).strip()
if sum(1 for s in secoes if s[2]) >= 3:
    h1, grifo, fina = CAPA[k]
    h1 = E(h1).replace(E(grifo), f'<span class="mk">{E(grifo)}</span>')
else:
    h1, fina = E(m1.group(1) if m1 else "Playbook"), ui.md_inline(intro)
base_md = next((l for l in intro.splitlines() if l.startswith("Base:")), "")
base_txt = " e ".join(re.findall(r"\*\*(.+?)\*\*", base_md))
info = ui.base_info(fonte)
if not base_txt and info:
    base_txt = " e ".join(f"{ui.num(n)} posts no {ui.PLAT_NOME.get(p, p)}" for p, n in sorted(info[0].items())) + f", de {ui.num(info[1])} perfis"
meta = [f"Atualizado em <b>{datetime.date.fromtimestamp(os.path.getmtime(fonte['playbook'])).strftime('%d/%m/%Y')}</b>"]
if base_txt:
    meta.append(f"Base: <b>{E(base_txt)}</b>")
if info and len(info[2]) == 10:
    meta.append(f"Coleta em <b>{ui.data_br(info[2])}</b>")
meta.append(f"Leitura de <b>{max(1, round(len(md.split()) / 200))} min</b>")
st.html(f'<header class="pb-capa"><div class="k">Playbook · Foco {k} · {E(fonte["nome"])}</div><h1>{h1}</h1>'
        f'<p class="fina">{fina}</p><div class="meta">' + "".join(f"<span>{x}</span>" for x in meta) + "</div></header>")

lado, corpo = st.columns([1, 4.3], gap="large")
with lado, st.container(key="pb_rail"):
    st.html('<nav class="pb-toc"><b>Neste playbook</b>' + "".join(
        f'<a href="#cap-{i}" class="{"on" if i == 1 else ""}"><i>{i:02d}</i>{E(s[0])}</a>' for i, s in enumerate(secoes, 1)) + "</nav>" + SPY,
        unsafe_allow_javascript=True)
    modo = st.radio("Mostrar posts", ["embed", "local"], key="pb_modo",
                    format_func={"embed": "Embed do Instagram", "local": "Prévia local"}.get)
    st.html('<p class="nota-modo">O embed vem direto do Instagram e precisa de internet. A prévia local usa a mídia salva na coleta.</p>')
with corpo:
    for i, (rotulo, titulo_, fn, txt) in enumerate(secoes, 1):
        st.html(f'<header class="cap c{i}" id="cap-{i}"><span>{i:02d} · {E(rotulo)}</span><h2>{E(titulo_)}</h2></header>')
        if fn is None or fn(txt) is False:
            st.markdown(txt)
