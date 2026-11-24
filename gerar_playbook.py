"""Monta PLAYBOOK.md a partir de data/ (achados, selos, validação, perfis em destaque e criativos do agente)."""
import json

import pandas as pd

D = "data"
ach = pd.read_csv(f"{D}/achados.csv", dtype={"valor": str})
sel = pd.read_csv(f"{D}/padroes_selados.csv", dtype={"valor": str})
val = pd.read_csv(f"{D}/validacao_resultado.csv").set_index("campo").kappa
pf = pd.read_csv(f"{D}/perfis_destaque.csv")
cri = json.load(open(f"{D}/criativos_playbook.json"))
NOMES = {"segmento": "Segmento do perfil", "tema_principal": "Tema", "formato_video": "Formato", "pilar_impulso": "Pilar",
         "tipo_cta": "Tipo de CTA", "tipo_hook": "Gancho", "duracao_faixa": "Duração", "tem_cta": "Tem CTA",
         "tem_rosto": "Rosto", "tom": "Tom", "convite_participacao": "Convite à participação",
         "gatilho_identificacao": "Gatilho", "generico": "Genérico", "texto_na_tela": "Texto na tela"}


def br(x, casas=1):
    return f"{x:.{casas}f}".replace(".", ",")


VALOR = {"gestao_financas": "finanças e contabilidade", "vendas_marketing": "vendas e marketing", "True": "sim",
         "False": "não", "alimentacao": "alimentação", "servicos": "serviços"}


def conf(campo):
    if campo in ("segmento", "duracao_faixa", "porte", "tipo_post"):
        return "dado objetivo"
    k = val.get(campo)
    return "não validado" if pd.isna(k) else f"{'alta' if k >= .6 else 'média' if k >= .4 else 'baixa'} (κ {br(k, 2)})"


ig = ach[(ach.plataforma == "instagram") & (ach.n_top >= 5) & ach.lift.notna()]
mais = ig[ig.lift >= 1.5].sort_values("lift", ascending=False).head(10)
menos = ig[(ig.lift <= 0.65)].sort_values("lift").head(6)
n1 = pd.read_csv(f"{D}/achados_youtube_n1.csv", dtype={"valor": str}).set_index(["campo", "valor"]).lift
yt = ach[(ach.plataforma == "youtube") & (ach.n_top >= 5) & (ach.lift >= 1.5) & (ach.campo != "porte")].copy()
yt["lift_n1"] = [n1.get((c, v)) for c, v in zip(yt.campo, yt.valor)]
yt_atual = yt.sort_values("lift", ascending=False).head(6)
yt = yt[yt.lift_n1 >= 1.5].sort_values("lift", ascending=False).head(6)  # só o que se mantém nos dois métodos

PLAT = {"todas": "Geral", "instagram": "Instagram", "youtube": "YouTube"}
GEN = sel[(sel.plataforma == "todas") & (sel.campo == "generico") & (sel.valor == "True")].iloc[0]
SEM_GAT = sel[(sel.plataforma == "todas") & (sel.campo == "gatilho_identificacao") & (sel.valor == "nenhum")].iloc[0]
SEM_CTA = ach[(ach.plataforma == "instagram") & (ach.campo == "tem_cta") & (ach.valor == "False")].iloc[0]
import sqlite3  # posts do Instagram na amostra atual com rubrica (antes era um número fixo no texto)
N_IG = sqlite3.connect(f"{D}/stone.db").execute(
    "select count(*) from ranking r join categorias c using (video_id) where r.plataforma = 'instagram' and r.amostra").fetchone()[0]
YT_VIDEO, YT_TOTAL = sqlite3.connect(f"{D}/stone.db").execute(
    "select sum(c.fonte = 'video'), count(*) from ranking r join categorias c using (video_id) "
    "where r.plataforma = 'youtube' and r.amostra").fetchone()

L = ["# Playbook de conteúdo · Impulso Stone",
     "", "Padrões de conteúdo de alto engajamento para micro e pequenos empreendedores, cruzados com os Ads do Impulso.",
     f"Base: **655 posts de 28 perfis no Instagram** (top 10% vs. controle, {N_IG} analisados pelo Gemini vendo vídeo e imagens) "
     "e **11.021 Shorts de 100 canais no YouTube** (evidência complementar). Coleta em 23/11/2026.", "",
     "## Como ler este playbook", "",
     "- **Lift:** quantas vezes o padrão é mais comum no top 10% do que em posts comuns do mesmo perfil e faixa. "
     "Lift 2,0 significa o dobro.",
     "- **Selo:** compara o mercado com os Ads do Impulso. **Confirmado** quer dizer que o padrão funciona nos dois. "
     "**Contradito** quer dizer que eles apontam em direções opostas. **Só mercado** quer dizer que ainda não foi testado "
     "nos Ads.",
     "- **Confiança:** concordância entre a IA e uma revisão humana feita às cegas em 10 posts (kappa). Padrões de "
     "confiança baixa são hipóteses, não regras.", "",
     "## 1. O que mais diferencia o top no Instagram", "",
     "| Padrão | No top | Nos comuns | Lift | Confiança |", "|---|---|---|---|---|"]
for r in mais.itertuples():
    L.append(f"| {NOMES.get(r.campo, r.campo)}: **{VALOR.get(r.valor, r.valor)}** | {r.freq_top:.0%} | {r.freq_resto:.0%} | {br(r.lift)}× | {conf(r.campo)} |")
L += ["", "**O que aparece menos no top:**", ""]
for r in menos.itertuples():
    L.append(f"- {NOMES.get(r.campo, r.campo)} = {VALOR.get(r.valor, r.valor)}: {r.freq_top:.0%} no top contra {r.freq_resto:.0%} nos comuns (lift {br(r.lift, 2)})")
L += ["", "**Leitura para o Impulso:**", "",
      "- Finanças e gestão explicadas na prática, em tutorial ou carrossel que dá para salvar, são o eixo mais forte do "
      "top. Isso conversa direto com o pilar **educação financeira**.",
      f"- Post sem CTA aparece {'bem ' if SEM_CTA.lift <= 0.7 else 'um pouco ' if SEM_CTA.lift < 1 else 'não '}menos no top "
      f"({SEM_CTA.freq_top:.0%} contra {SEM_CTA.freq_resto:.0%}, lift {br(SEM_CTA.lift, 2)}). A confiança do campo CTA é {conf('tem_cta')}.",
      "- \"Vendas\" genérico e o talking head puro aparecem menos no top. O que se destaca é ensinar uma conta ou um "
      "processo concreto.", "",
      "## 2. Mercado × Ads do Impulso (evidência dupla)", "",
      "| Onde | Padrão | Mercado (lift) | Ads do Impulso | Selo | Confiança |", "|---|---|---|---|---|---|"]
for r in sel[sel.selo.isin(["confirmado", "contradito"])].itertuples():
    casa = "mais comum nos Ads de alto CTR" if r.dif_interna > 0 else "mais comum nos Ads de baixo CTR"
    L.append(f"| {PLAT[r.plataforma]} | {NOMES.get(r.campo, r.campo)}: **{VALOR.get(r.valor, r.valor)}** | {br(r.lift, 2)}× | {casa} | **{r.selo}** | {conf(r.campo)} |")
L += ["", "**O insight central é que reação não é clique.** " + (
      "Posts genéricos e motivacionais aparecem mais no top do mercado, que é medido por curtidas e comentários. "
      if GEN.lift >= 1.2 else
      f"No mercado, medido por curtidas e comentários, o post genérico não é penalizado: aparece no top na mesma "
      f"proporção que nos comuns (lift {br(GEN.lift, 2)}), e o post sem gatilho de identificação aparece até mais "
      f"(lift {br(SEM_GAT.lift, 2)}, {SEM_GAT.n_top} posts). ") +
      "Nos Ads do Impulso, os posts genéricos e motivacionais ficam abaixo de 1% de CTR "
      "(\"Vender mais não é sorte\", 0,77%; \"POV\", 0,97%). Para gerar inscrição, o post precisa de identificação "
      "(nicho, data ou dor) e de um próximo passo claro.", "",
      "**Convite à participação.** É o padrão confirmado. Os posts que chamam o empreendedor para participar têm os "
      "maiores CTRs da conta, acima de 8%. Mas na validação manual a IA foi mais restritiva que a revisão humana "
      "(κ −0,20: em 5 de 10 posts a revisão humana viu convite e a IA não). O sinal dos Ads é forte, mas a medida no "
      "mercado ainda não é confiável. "
      "**É a primeira hipótese a testar no piloto de Ads.**", "",
      "## 3. Perfis em destaque (Instagram)", "",
      "| Perfil | Faixa | Posts no top | Tema | Formato | Pilar |", "|---|---|---|---|---|---|"]
for r in pf[pf.plataforma == "instagram"].head(6).itertuples():
    L.append(f"| {r.canal.split('|')[0].strip()} | {r.porte} | {r.n_top} | {r.tema} | {r.formato} | {r.pilar} |")
L += ["", "Indiânara Cörrêa, parceira do Impulso, entra no top com 1,3 mil seguidores. Isso confirma que microcriadoras "
      "com história real performam acima do seu tamanho.", "",
      "## 4. YouTube Shorts (evidência complementar)", "",
      "Os padrões abaixo aparecem tanto na parcela que o Gemini viu em vídeo quanto na parcela analisada por thumbnail "
      "(DeepSeek):" if len(yt) else
      f"Maiores lifts da amostra atual ({YT_VIDEO} de {YT_TOTAL} posts vistos em vídeo pelo Gemini; o restante por "
      "thumbnail, título e descrição, pelo DeepSeek). A comparação entre os dois métodos foi feita na amostra da régua "
      "anterior e não cobre esta:", ""]
for r in yt.itertuples():
    L.append(f"- {NOMES.get(r.campo, r.campo)} = **{VALOR.get(r.valor, r.valor)}**: lift {br(r.lift)}× vendo o vídeo, "
             f"{br(r.lift_n1)}× pela thumbnail")
for r in (yt_atual.itertuples() if not len(yt) else []):
    L.append(f"- {NOMES.get(r.campo, r.campo)} = **{VALOR.get(r.valor, r.valor)}**: lift {br(r.lift)}× "
             f"({r.n_top} posts no top)")
L += ["", "No YouTube, **bastidores** (mostrar o negócio por dentro) é o formato que mais se destaca.", "",
      "## 5. Cinco criativos para o @impulsostone", "",
      "Gerados pelo agente (`agent.py gerar_criativo`) com base nos posts reais do top e checados quanto a CTA, "
      "convite à participação, linguagem genérica e tom do Impulso. O roteiro completo está em "
      "`data/criativos_playbook.json`.", ""]
for i, r in enumerate(cri, 1):
    c = r["creatives"][0]
    refs = {p["video_id"]: p for p in r["reference_posts"]}
    L += [f"### {i}. {r['pedido']}", "", f"**Formato:** {c['formato']} · **Pilar:** {c['pilar']}", "",
          f"**Gancho:** {c['gancho']}", "", "**Roteiro:**", "", *[f"> {l}" for l in c["roteiro"].split("\n") if l.strip()], "",
          f"**Legenda:** {c['legenda'][:600]}{'…' if len(c['legenda']) > 600 else ''}", "", f"**CTA:** {c['cta']}", "",
          "**Inspirado em:** " + " · ".join(f"[{refs[v]['canal'][:40]}]({refs[v]['url']})" for v in c["inspirado_em"] if v in refs),
          ""]
L += ["## 6. Próximo passo: piloto em Ads", "",
      "1. Subir 3 criativos deste playbook como posts impulsionados, com o mesmo público e o mesmo orçamento dos Ads "
      "de setembro.",
      "2. Testar variações A/B de **convite à participação** contra a mesma peça sem convite. É o padrão confirmado e "
      "também o de menor confiança.",
      "3. Medir CTR e inscrições, além do engajamento, porque reação não é clique.",
      "4. Voltar com os resultados para a base interna. Assim o selo de cada padrão é atualizado com dados reais do "
      "Impulso.", "",
      "## Limitações", "",
      "- Os padrões são observados, não causais. O piloto em Ads é o que mede o efeito de verdade.",
      "- O Instagram é uma amostra de 28 perfis montada a partir de sementes e hashtags, coletada por scraping de dados "
      "públicos (Apify).",
      "- A validação manual tem só 10 posts. Pilar, gancho e convite tiveram kappa baixo.",
      "- No YouTube, só uma parte da amostra foi vista em vídeo. O resto foi analisado por thumbnail, título e "
      "descrição, e a comparação entre os métodos está em `data/comparacao_metodos.csv`."]
open("PLAYBOOK.md", "w").write("\n".join(L) + "\n")
print("PLAYBOOK.md:", len(L), "linhas")
