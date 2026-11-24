# Conteúdo de alto engajamento para MPEs: Case Impulso Stone · Inteli Academy

**Pergunta:** quais características de conteúdo, formato e perfil de criador aparecem nas publicações de maior
engajamento para micro e pequenos empreendedores, e como transformar isso em criativos para o @impulsostone?

**Dois focos de análise:**
- **Foco A, "Impulso → empreendedor":** conteúdo que engaja donos de pequeno negócio. Base `data/stone.db`
  (Instagram e YouTube Shorts). Resumo no [PLAYBOOK.md](PLAYBOOK.md).
- **Foco B, "Negócio → cliente":** como o pequeno negócio engaja o cliente final dele. Coleta nova no Instagram
  (`foco_b.py`, base `data/foco_b.db`). Resumo no [PLAYBOOK_B.md](PLAYBOOK_B.md).

A rubrica do VLM tem o campo `publico_alvo`, que separa os dois focos post a post.

**Evidência dupla (Foco A):** cada padrão do mercado é cruzado com os dados internos do Impulso (Meta Ads e
relatório do Instagram) e recebe um selo: **confirmado**, **contradito**, **inconclusivo** ou **só mercado**.

## Como rodar
```bash
uv venv --python 3.12 .venv && uv pip install -r requirements.txt
cp .env.example .env                              # YOUTUBE_API_KEY, APIFY_TOKEN, FEITA_API_KEY
.venv/bin/python pipeline.py check                # testa as chaves

# Foco A · 1. perfis
.venv/bin/python pipeline.py discover             # YouTube: 10 buscas de Shorts -> data/canais.csv
.venv/bin/python pipeline.py triagem              # LLM classifica relevância MPE, tipo de criador e segmento
.venv/bin/python pipeline.py ig_discover          # Instagram: sementes + mesmos @ dos canais do YouTube
.venv/bin/python pipeline.py ig_discover --expandir   # + autores de posts em hashtags de MPE
.venv/bin/python pipeline.py triagem data/perfis_ig.csv
# Foco A · 2. posts
.venv/bin/python pipeline.py collect              # Shorts (YouTube Data API v3)
.venv/bin/python pipeline.py ig_collect           # posts do Instagram (Apify), mesmas tabelas
.venv/bin/python pipeline.py rank                 # ER, resíduo do modelo, top e controle (lê data/veredictos.csv)
.venv/bin/python pipeline.py ig_midia             # baixa mp4/imagens do top+controle (URLs da Apify expiram)
# Foco A · 3. análise
.venv/bin/python pipeline.py categorize           # rubrica via VLM (retoma de onde parou)
.venv/bin/python pipeline.py categorize --so-thumb   # só thumbnail + texto, para os vídeos que o VLM não abriu
.venv/bin/python pipeline.py rank                 # de novo: tira do top os posts que a rubrica marcou fora do Foco A
.venv/bin/python pipeline.py analyze              # lift top x controle -> data/achados.csv, data/perfis_destaque.csv
.venv/bin/python pipeline.py cruzar               # selo mercado x Ads -> data/padroes_selados.csv
.venv/bin/python pipeline.py validate --gerar     # posts para rotular à mão
.venv/bin/python pipeline.py validate             # kappa por campo
.venv/bin/python avaliacao_regua.py               # compara as réguas -> data/avaliacao_regua.md (só lê o stone.db)
.venv/bin/python gerar_playbook.py                # monta o PLAYBOOK.md a partir de data/

# Foco B (cada etapa confere o gasto na Apify e para em US$ 4,50)
.venv/bin/python foco_b.py descobrir              # posts de 11 hashtags de negócio local -> autores
.venv/bin/python foco_b.py triar                  # DeepSeek: é negócio real? -> data/b_perfis.csv
.venv/bin/python foco_b.py coletar                # posts dos aprovados -> data/foco_b.db, mais rank e mídia
.venv/bin/python foco_b.py rank                   # mesma régua do Foco A, por porte
.venv/bin/python foco_b.py midia                  # capas, imagens e vídeos dos candidatos
.venv/bin/python foco_b.py categorizar            # rubrica B: imagens + legenda; --metodo video usa o Gemini
.venv/bin/python foco_b.py comentarios            # intenção de compra nos comentários (regex + DeepSeek)
.venv/bin/python foco_b.py analisar               # lift, perfis em destaque, segmento -> data/b_*.csv

# agente e interface
.venv/bin/python agent.py gerar_criativo "Reels de Natal para salão de beleza" --segment beleza
.venv/bin/python mcp_server.py                    # servidor MCP (stdio)
.venv/bin/streamlit run app.py                    # interface, em http://localhost:8501

# testes
.venv/bin/python test_logic.py
.venv/bin/python test_foco_b.py
.venv/bin/python test_app.py                      # interface nos dois focos, com e sem os arquivos do Foco B
```

**Interface (`app.py`, Streamlit):** o seletor "Foco da análise" troca entre "Impulso → empreendedor" e
"Negócio → cliente". As abas são Agente, Ranking, Perfis em destaque, Padrões, Base e método e Playbook. O agente
gera criativos só para o Foco A. As outras abas mostram o foco escolhido.

## Base de dados

### Foco A (`data/stone.db`)

| | YouTube (Shorts) | Instagram |
|---|---|---|
| Fonte | YouTube Data API v3 (oficial) | Apify `apify/instagram-scraper` (dados públicos) |
| Perfis com posts | 100 canais | 28 perfis |
| Posts coletados | 11.025 | 682 (460 Reels, 172 carrosséis, 50 imagens) |
| Posts no ranking (curtidas públicas) | 11.021 | 655 |
| Base elegível da régua | 8.743 posts de 82 canais | 583 posts de 25 perfis |
| Período | 22/11/2025 a 09/11/2026 | 28/11/2025 a 09/11/2026 |
| Coleta | 23/11/2026 (`coletado_em`) | 23/11/2026 |

**Seleção de perfis**, que o TAPI pede que cada estudante defina e justifique:
1. **YouTube:** 10 buscas de Shorts com termos de MPE (`KEYWORDS`), região BR, últimos 12 meses. As buscas trouxeram
   385 canais. 166 passaram no mínimo de 1.000 inscritos e 30 vídeos.
2. **Instagram:** a busca da Apify por palavra-chave não funcionou ("MEI" trouxe contas alemãs, como "mein"), e o
   `relatedProfiles` vem vazio sem login. Por isso a lista foi montada assim:
   1. Sementes: os parceiros do relatório do Impulso e os embaixadores Stone.
   2. Os mesmos @ dos canais de MPE do YouTube.
   3. Autores de posts recentes em 7 hashtags de MPE (`IG_HASHTAGS`).
   Também aqui o mínimo é de 1.000 seguidores e 30 posts.
3. **Triagem por LLM (Claude Haiku 5.5):** a partir do nome e da bio, define se o perfil fala com dono de pequeno
   negócio, o tipo de criador (empreendedor real, especialista ou instituição) e o segmento. O resultado ficou em
   103 canais e 34 perfis (`perfis.csv`). Os parceiros do Impulso entram sempre.
4. **Validação humana de canais:** 80 canais têm veredito em `data/veredictos.csv`. 74 vieram do artifact de
   validação e 6 da auditoria manual do top. São 58 "manter", 8 "dúvida" e 14 "excluir" (13 do YouTube e 1 do
   Instagram). Os canais excluídos somam 2.180 posts do YouTube e 32 do Instagram, que ficam fora da base elegível.
5. **Faixas de tamanho da aula 1:** micro até 10 mil seguidores, médio de 10 mil a 100 mil, grande acima disso.

**Critérios dos posts:**
- Janela de 14 a 365 dias antes da coleta, para que as métricas já estejam estabilizadas.
- Short é um vídeo de até 180 s. A coleta usa a playlist `UUSH…`.
- No Instagram, posts fixados e collabs de outros donos ficam de fora.

### Foco B (`data/foco_b.db`)

| | Instagram |
|---|---|
| Fonte | Apify `apify/instagram-scraper` (dados públicos) |
| Perfis | 28 negócios (16 micro, 11 médios, 1 grande) |
| Segmentos | alimentação 8, moda/varejo 8, beleza 5, pet 4, outro 2, serviços 1 |
| Posts coletados | 1.013 (693 Reels, 155 carrosséis, 165 imagens) |
| Posts no ranking (curtidas públicas) | 848 |
| Base elegível da régua | 731 posts de 25 perfis (15 micro, 9 médios, 1 grande) |
| Comentários de clientes | 2.464, em 531 posts |
| Período | 06/12/2025 a 24/11/2026 |
| Coleta | 24/11/2026 |

**Seleção de perfis** (`foco_b.py`, `data/b_meta.json`, `data/b_log_descobrir.txt`):
1. **Descoberta:** 275 posts recentes de 11 hashtags de negócio local (`HASHTAGS`: padaria, confeitaria, salão,
   barbearia, loja de roupas, moda feminina, pet shop, marmitaria, hamburgueria, manicure, ateliê). São 242 autores.
   Uma pré-triagem por texto (DeepSeek) marcou 126 como prováveis negócios.
2. **Triagem (DeepSeek, com bio, categoria e legendas recentes):** 60 perfis triados e 42 aprovados. Para ser
   aprovado, o perfil precisa ser negócio real que vende ao consumidor final, ser brasileiro, não ser franquia nem
   marca grande, não falar com empreendedores (isso é Foco A), ser público, ter de 500 a 200 mil seguidores e 30
   posts ou mais.
3. **Inclusão:** até 28 perfis, em rodízio por segmento × porte, para dar variedade.

**Critérios dos posts:** últimos 365 dias, sem fixados e sem collabs. A coleta traz até 38 posts por perfil. Não há
idade mínima na coleta. A idade mínima de 7 dias entra na régua.

### Limitações da base
- **Curtidas ocultas:** posts com curtidas escondidas não entram no ranking. São 27 no Instagram e 4 no YouTube no
  Foco A, e 165 no Foco B.
- **Viés da amostra:** a amostra do Instagram do Foco A é menor e nasce de sementes e hashtags. A do Foco B nasce só
  de hashtags, então pega quem usa hashtag e posta bastante. O viés de seleção fica documentado.
- **Termos de uso:** a coleta do Instagram é scraping de dados públicos via Apify, rota citada no kickoff. Usamos só
  métricas públicas e o texto de comentários públicos. Não coletamos dados pessoais de seguidores.
- **Base interna:** a `impulso_interno.csv` (18 criativos de Ads e 1 post orgânico) foi rotulada a partir do texto do
  relatório de performance, não pelo VLM, porque as imagens dos anúncios não foram exportadas. Os links da conta de
  anúncios não são publicados.

## Metodologia

1. **Engajamento reportado:** `er = (curtidas + comentários) ÷ seguidores`, a fórmula do TAPI. Também calculamos o
   `outlier` (ER do post ÷ ER mediano do próprio perfil) e a `conversa` (comentários ÷ curtidas).
2. **Régua de alto desempenho** (`pipeline.py`: `ranquear`, `residuo_modelo`, `rank`). O ER continua sendo o número
   reportado, mas não escolhe mais o top.
   - **Base elegível:** canal não excluído na validação humana; post que o VLM não marcou como irrelevante para MPE
     nem como voltado ao consumidor final (`publico_alvo`); criador com 5 posts ou mais; post com 7 dias ou mais.
     Post ainda sem rubrica entra como candidato. Depois de categorizar, o `rank` roda de novo.
   - **Score:** resíduo do modelo misto `log1p(curtidas + comentários) ~ log(seguidores) + formato + log(idade) +
     (1|criador)`, ajustado por plataforma. O resíduo mede quanto o post superou o esperado para aquele criador,
     formato e idade.
   - **Top:** os 10% de maior resíduo em cada plataforma × porte, com no máximo 3 posts por criador.
   - **Controle:** sorteio na base elegível, fora do top, do mesmo tamanho do top em cada estrato.
   - **Régua antiga:** o top 10% por ER puro fica na coluna `top_er_puro`, para comparação.
   - **Perfis em destaque:** ordenados pelo efeito do criador no modelo, que já vem encolhido para quem tem poucos
     posts.
3. **Por que a régua mudou (auditoria).** No top por ER puro do YouTube, 56% dos posts estavam em canais fora do
   perfil: assistência técnica como entretenimento, cortes virais, marcas. Um único canal chegava a 56% do estrato
   YouTube grande. Os detalhes estão em `data/auditoria_canais_fora.csv` e em
   `research_notes/Métricas de engajamento em redes/diagnostico_dados.md`.
4. **Lift:** `lift = freq_top ÷ freq_controle`. Mostra o que está associado ao top, e não o que é só comum no nicho.
   Só entram valores com 5 posts ou mais no top.
5. **Rubrica via VLM** (`Rubrica`, JSON validado por Pydantic). O campo `fonte` registra o que o modelo viu.
   - **Em vídeo:** Gemini Flash. No YouTube, o modelo assiste ao vídeo pela URL, com áudio. Nos Reels, recebe o mp4.
     Nos carrosséis, recebe as imagens. Sempre recebe também a legenda.
   - **Sem vídeo:** DeepSeek V4.1 Flash, com thumbnail, título e descrição. Foi o método da maior parte do YouTube
     na amostra nova (ver Resultados e Limitações).
   - `relevante_mpe` filtra posts fora do tema. `publico_alvo` tem quatro valores: donos de negócio, consumidor
     final, ambos ou nenhum. Consumidor final e nenhum saem da base elegível do Foco A.
   - Campos calibrados pelos Ads do Impulso: `convite_participacao`, `gatilho_identificacao`, `generico_0a10` e
     `pilar_impulso`.
6. **Cruzamento mercado × casa:** um padrão com lift ≥ 1,2 (ou ≤ 0,8) é comparado com a diferença de frequência entre
   os Ads de desempenho alto (7 criativos) e baixo (6). Se os dois apontam na mesma direção, o selo é confirmado. Se
   apontam em direções opostas, contradito. Se um dos lados é neutro, inconclusivo. Sem dado interno, só mercado.
7. **Validação da rubrica:** 10 posts do Instagram (5 do top e 5 do controle) rotulados à mão, às cegas, num artifact
   com as respostas da IA escondidas. Calculamos o kappa de Cohen por campo (`data/validacao_resultado.csv`). Essa
   validação é da amostra anterior à régua nova.
8. **Foco B** (`foco_b.py`):
   - **Régua:** a mesma do Foco A (`rankear`), por porte. Não há validação humana de canais nem filtro de
     `publico_alvo`. A triagem dos perfis faz esse papel.
   - **Rubrica B:** formato, gancho, CTA, tom, se mostra produto, preço, processo, cliente e rosto do dono. O lift
     usa um método único nos 124 posts: DeepSeek com até 5 imagens e a legenda.
   - **Intenção de compra:** comentários de clientes que perguntam preço, endereço, entrega ou dizem "quero",
     classificados por regex e DeepSeek. O indicador é a fração de comentários com intenção em cada post.
9. **Agente (LangGraph):** `recuperar` → `redigir` → `checar`.
   - `recuperar`: consulta determinística. Se sobram menos de 3 referências no top, solta os filtros um a um e marca
     `confidence_flag`.
   - `redigir`: usa o DeepSeek V4.1 Flash, no tom do Impulso, e prioriza os padrões confirmados.
   - `checar`: avalia gancho, CTA, genérico, convite e tom, e confere se as referências existem. Se falhar, o texto
     volta para reescrita, até 3 tentativas.
   - Ele fica exposto como a função `agent.run()`, como o servidor MCP `mcp_server.py` (tool `conteudo_mpe`) e na
     aba Agente da interface. O log fica em `data/execucoes.jsonl`.

## Resultados
Os resumos para o time estão no **[PLAYBOOK.md](PLAYBOOK.md)** (Foco A, com selos, perfis em destaque e criativos) e
no **[PLAYBOOK_B.md](PLAYBOOK_B.md)** (Foco B, com recomendações para o lojista).

### Foco A: tamanho do top e do controle (tabela `ranking`)

| Plataforma | Porte | Top (posts · criadores) | Controle (posts · criadores) |
|---|---|---|---|
| Instagram | micro | 11 · 5 | 11 · 4 |
| Instagram | médio | 26 · 9 | 26 · 10 |
| Instagram | grande | 10 · 5 | 10 · 5 |
| **Instagram** | **total** | **47 · 19** | **47 · 19** |
| YouTube | micro | 94 · 35 | 94 · 27 |
| YouTube | médio | 63 · 22 | 63 · 20 |
| YouTube | grande | 46 · 19 | 46 · 17 |
| **YouTube** | **total** | **203 · 76** | **203 · 64** |

O top é 7,2% dos 655 posts do Instagram e 1,8% dos 11.021 do YouTube. O limite de 3 posts por criador explica a
diferença para os 10%.

### Foco A: régua antiga × régua nova (tabela `ranking`, colunas `top_er_puro` e `top`)

| | Top por ER puro | Top novo |
|---|---|---|
| YouTube: posts no top | 1.103 | 203 |
| YouTube: criadores no top | 50 | 76 |
| YouTube: fatia do maior criador | 14% | 1,5% |
| YouTube grande: fatia do maior criador | 56% | 7% |
| YouTube: posts em canais fora do perfil (excluídos ou listados na auditoria) | 56% | 4% |
| YouTube: posts em canais excluídos na validação | 51% | 0% |
| Instagram: posts no top | 67 | 47 |
| Instagram: criadores no top | 16 | 19 |
| Instagram: fatia do maior criador | 24% | 6% |
| Instagram micro: fatia do maior criador | 62% | 27% |

- Dos posts do top novo, 91 de 203 no YouTube e 28 de 47 no Instagram também estavam no top por ER puro.
- Os 4% que restam no YouTube são 9 posts de 3 canais listados na auditoria que ficaram como "manter" ou "dúvida"
  na validação.
- Entre os posts do top por ER puro que têm rubrica, 68% são relevantes para MPE no YouTube (347 rotulados) e 77% no
  Instagram (66 rotulados). No top novo esse número é 100% por construção, porque o filtro faz parte da régua.

### Foco A: avaliação da régua (`data/avaliacao_regua.md`, gerado por `avaliacao_regua.py`)
A avaliação compara quatro réguas: ER puro, outlier simples, modelo misto e a régua adotada.
- **Viés de tamanho.** O ER puro cai com o tamanho do criador: rho = −0,49 no Instagram e −0,28 no YouTube. Com o
  outlier ou com o resíduo do modelo, rho fica perto de 0. Os dois empatam.
- **Concentração.** O ganho vem do limite de 3 posts por criador, não do modelo. O HHI médio no YouTube vai de 0,22
  no ER puro para 0,04 com o limite, igual para outlier e modelo.
- **Elasticidade.** b ≈ 0,37 (Instagram: IC95 de 0,13 a 0,62; YouTube: de 0,22 a 0,49). O ER puro pressupõe b = 1,
  e os dados rejeitam isso. Cerca de metade da variância do log do engajamento é do criador (ICC de 0,49 a 0,54).
- **Previsão fora da amostra.** O modelo misto não supera a mediana do próprio criador. A diferença de erro (MAE em
  log) é −0,02 no Instagram, com IC95 de −0,11 a +0,06, e +0,03 no YouTube, com IC95 de −0,02 a +0,09. Os dois
  intervalos contêm 0.
- **Modelo × outlier simples.** Com a mesma base e o mesmo limite, os scores têm Spearman de 0,91 no Instagram e
  0,94 no YouTube. Os tops têm Jaccard de 0,74 e cerca de 0,68. Nenhum teste mostra que a lista do modelo é melhor.
- **Veredito.** A régua nova é melhor que o ER puro em viés de tamanho, concentração e canais fora do perfil. O que
  entrega o resultado é a normalização pelo próprio criador, o limite por criador e a base elegível. A escolha do
  modelo misto em vez do outlier simples não está sustentada pelos dados.

A avaliação foi gerada em 24/11 às 01:29, antes do último `rank`. Por isso os totais dela (48 posts no top do
Instagram, 198 no YouTube) diferem um pouco dos da tabela `ranking` de hoje (47 e 203).

### Foco A: base categorizada (tabela `categorias`, coluna `fonte`)

| Parcela | Posts com rubrica | O que o modelo viu |
|---|---|---|
| Instagram, top e controle | 92 de 94 | 52 em vídeo, 40 por imagens |
| YouTube, amostra do lift | 332 de 332 | 70 em vídeo, 259 por thumbnail + texto (DeepSeek), 3 por thumbnail |
| Tabela inteira | 883 | 503 em vídeo, 85 por imagens, 292 por thumbnail + texto (DeepSeek), 3 por thumbnail |

- No YouTube, a amostra do lift tem até 60 posts por grupo × porte (`YT_AMOSTRA`): 166 do top e 166 do controle,
  dos 406 posts do top e do controle.
- A tabela inteira inclui posts categorizados em rodadas anteriores, que hoje estão fora do top e do controle.
- `publico_alvo` nos 883 posts: 652 para donos de negócio, 65 para consumidor final, 13 para ambos e 153 para
  nenhum.

### Foco A: padrões por plataforma (`data/padroes_selados.csv`)
Contagem de selos na visão "todas": 2 confirmados, 1 contradito, 7 inconclusivos e 38 só mercado.

**Instagram** (47 posts no top × 45 no controle)
| Padrão | Lift | Posts no top | Selo | κ do campo |
|---|---|---|---|---|
| Segmento do perfil: gestão e finanças | 5,74 | 6 | só mercado | dado objetivo |
| Tema: finanças | 4,31 | 9 | só mercado | 0,53 |
| Gancho: promessa | 2,39 | 10 | só mercado | 0,04 |
| Tema: história de empreendedor | 1,91 | 10 | só mercado | 0,53 |
| Formato: carrossel/estático | 1,76 | 22 | só mercado | 0,46 |
| Gatilho: pessoa real | 1,50 | 11 | confirmado | 0,41 |
| Convite à participação | 1,48 | 17 | confirmado | −0,20 |
| Formato: talking head | 0,64 | 14 | só mercado | 0,46 |
| Tema: vendas | 0,48 | 5 | só mercado | 0,53 |

**YouTube** (166 × 166; 79% da amostra sem vídeo)
| Padrão | Lift | Posts no top | Selo | κ do campo |
|---|---|---|---|---|
| Pilar: comunidade | 6,00 | 6 | só mercado | 0,22 |
| Segmento do perfil: alimentação | 4,00 | 12 | só mercado | dado objetivo |
| Gatilho: pessoa real | 3,80 | 19 | confirmado | 0,41 |
| Formato: bastidores | 2,86 | 20 | só mercado | 0,46 |
| Convite à participação | 1,38 | 33 | confirmado | −0,20 |
| Formato: talking head | 0,75 | 92 | só mercado | 0,46 |
| Tipo de criador: instituição ou marca | 0,64 | 36 | só mercado | dado objetivo |
| Tom: técnico | 0,46 | 24 | só mercado | não validado |

**Evidência dupla**
- **Gatilho "pessoa real" e convite à participação:** confirmados pelos Ads nas duas plataformas. O campo do
  convite tem κ −0,20 na validação, então a medida no mercado tem confiança baixa.
- **Post sem gatilho de identificação:** contradito. Lift de 1,97 no mercado (9 posts no top, visão "todas"), mas é
  mais comum nos Ads de desempenho baixo.
- **Post genérico:** inconclusivo. Com a régua nova o lift é 1,01, ou seja, o genérico não diferencia o top. Na
  régua antiga o lift era 1,44 e o selo era contradito.

### Foco A: perfis em destaque (`data/perfis_destaque.csv`)
São 95 perfis com post no top: 19 no Instagram e 76 no YouTube. Os primeiros pelo efeito do criador:

| Plataforma | Perfil | Porte | Seguidores | Efeito do criador | Posts no top | Tema · formato mais comum |
|---|---|---|---|---|---|---|
| Instagram | Poliana Lira | médio | 63.978 | 2,06 | 3 | finanças · carrossel/estático |
| Instagram | Amanda Cichineli | médio | 14.130 | 1,50 | 3 | marketing · tutorial |
| Instagram | Indiânara Cörrêa | micro | 1.339 | 1,01 | 1 | história de empreendedor · carrossel/estático |
| YouTube | Luiz Vitale | micro | 4.290 | 3,78 | 3 | vendas · bastidores |
| YouTube | Felipe Ribeiro | micro | 1.310 | 2,60 | 3 | finanças · humor/esquete |
| YouTube | Andrius Dourado | micro | 1.760 | 2,26 | 3 | finanças · talking head |
| YouTube | Raissa Cardozo | médio | 10.700 | 2,03 | 3 | história de empreendedor · bastidores |

O terceiro maior efeito do YouTube é do canal Tudo de Laço (2,33), que está na auditoria como fora do perfil e ficou
como "dúvida" na validação. Ele não entra na tabela acima.

### Validação manual da rubrica (κ, 10 posts, amostra anterior)
| Campo | κ |
|---|---|
| Texto na tela | 1,00 |
| CTA | 0,60 |
| Tema | 0,53 |
| Formato | 0,46 |
| Gatilho | 0,41 |
| Pilar | 0,22 |
| Gancho | 0,04 |
| Convite | −0,20 |

Os campos com κ abaixo de 0,4 entram no playbook como hipóteses.

**Vídeo × thumbnail no YouTube** (`data/comparacao_metodos.csv`): só 16 posts da amostra atual têm os dois métodos.
Neles, o tema concorda bem (κ 0,75). Gancho (0,29) e pilar (0,23) concordam mal.

### Foco B: resultados (`data/b_analise.txt`, `data/b_achados.csv`, `data/b_meta.json`)
- **Top e controle:** 62 posts no top e 62 no controle (micro 34, médio 25, grande 3 em cada grupo). O top tem
  posts de 23 negócios. Os 124 posts têm rubrica. 117 são de fato o negócio falando com o cliente: 59 do top e 58 do
  controle.
- **Modelo:** b = 0,75, com IC95 de 0,45 a 1,04, em 731 posts de 25 perfis. O perfil explica 32% da variância (ICC).
  Com 25 perfis o intervalo é largo e inclui 1. 49 dos 62 posts do top também estariam no top por ER puro.

**Padrões, top × controle**
| Padrão | No top | No controle | Lift | Posts no top |
|---|---|---|---|---|
| Formato: humor/trend | 20,3% | 5,2% | 3,93 | 12 |
| Cliente aparece | 13,6% | 3,4% | 3,93 | 8 |
| Formato: tutorial/dica | 8,5% | 3,4% | 2,46 | 5 |
| Mostra o processo | 20,3% | 12,1% | 1,69 | 12 |
| Texto na tela | 54,2% | 34,5% | 1,57 | 32 |
| Formato: produto em destaque | 44,1% | 75,9% | 0,58 | 26 |
| CTA: encomendar | 11,9% | 20,7% | 0,57 | 7 |

Segundo o `PLAYBOOK_B.md`, os 8 posts com cliente aparecendo são de 4 salões de beleza.

**Achado principal: curtida não é pedido.**
| Recorte | Posts com comentário de cliente | Comentários com intenção de compra |
|---|---|---|
| Top | 55 | 15,2% |
| Controle | 32 | 14,2% |
| Mostra o preço | 10 | 59,2% |
| Não mostra o preço | 77 | 9,0% |
| Formato humor/trend | 13 | 1,9% |
| Formato produto em destaque | 45 | 17,3% |
| Formato bastidor de produção | 13 | 19,6% |

- Humor/trend é o formato que mais se destaca no top, mas quase não gera comentário com intenção de compra.
- Top e controle têm a mesma taxa de intenção. Entrar no top não trouxe mais gente perguntando preço.
- Mostrar o preço concentra a intenção. São só 10 posts, então é indício, não regra.

**Perfis em destaque** (`data/b_perfis_destaque.csv`, 25 perfis). Os primeiros pelo efeito do criador:
@stylecompany.shop (moda, 6.891 seguidores, efeito 1,76), @studio_mylenacosta (beleza, 3.973, 1,67),
@andressacunhadoces (alimentação, 12.869, 1,15), @taina_gda (alimentação, 2.822, 1,05) e @benditopaoroo
(alimentação, 44.515, 0,99). Os dois primeiros têm só 12 e 11 posts elegíveis.

## Limitações e evolução
- **Observação, não causa.** Os padrões são observados, não causais. O próximo passo é um teste piloto em Ads com os
  padrões confirmados.
- **O modelo misto não supera o outlier simples.** Em previsão fora da amostra, o modelo não reduz o erro em relação
  à mediana do próprio criador. O ganho da régua vem da normalização pelo criador, do limite por criador e da base
  elegível. O outlier simples (post ÷ mediana do criador) com os mesmos filtros daria um resultado equivalente e
  mais fácil de explicar.
- **O "top 10%" não é 10%.** Com o limite de 3 posts por criador, o top do YouTube é cerca de 2% da base (203 de
  11.021) e o do Instagram, 7% (47 de 655). No YouTube, 76 dos 82 criadores elegíveis têm post no top. A régua passa
  a escolher os melhores posts de cada criador. O valor 3 é uma escolha, não um resultado: trocar por 2 ou 5 muda de
  19% a 33% do top.
- **Estabilidade numérica.** A avaliação mostrou que o otimizador `lbfgs` falhava no YouTube em 16 de 20 subamostras
  e o pipeline caía num plano B sem avisar. O `pipeline.py` atual tenta `bfgs` primeiro e registra qual caminho usou.
  No ranking gravado, os 8.743 posts elegíveis do YouTube têm efeito do criador, isto é, o modelo ajustou. O
  `data/avaliacao_regua.md` ainda descreve o comportamento anterior.
- **Covariável de idade.** No teste temporal do YouTube, o corte de 10% do treino seleciona 19% dos posts de teste
  com a idade no modelo e 9% sem ela. O coeficiente de idade se confunde com tendência de calendário.
- **Seguidores são um retrato de hoje.** Posts antigos foram publicados com outra base de seguidores. Não há série
  histórica.
- **Poucos criadores no Instagram.** São 25 perfis elegíveis no Foco A e 25 no Foco B. Os intervalos são largos e a
  comparação por estrato tem menos de 15 criadores.
- **Categorização do YouTube sem vídeo.** Na amostra nova do YouTube, 262 dos 332 posts (79%) foram vistos por
  thumbnail e texto, não em vídeo. A cota grátis do Gemini acabou: as chaves novas têm 20 chamadas por dia por
  modelo. Campos que dependem de áudio e ritmo, como gancho, CTA e convite, ficam menos confiáveis nessa parcela.
- **Categorização do Foco B sem vídeo.** O lift do Foco B foi calculado com imagens e legenda (DeepSeek) nos 124
  posts. Só 24 posts, todos do top, passaram também pelo Gemini (20 em vídeo e 4 por imagens). Nesses 24, os dois
  métodos concordam em preço (κ 1,00), cliente aparece (0,88) e formato (0,63), e discordam em texto na tela (0,22)
  e gancho (0,32). Som, fala e ritmo não entram.
- **Validação humana é da amostra anterior.** O kappa vem de 10 posts do Instagram rotulados antes da régua nova.
  A amostra nova do Foco A não foi validada à mão, e a rubrica do Foco B não tem validação humana.
- **Relevância rotulada por VLM.** `relevante_mpe` e `publico_alvo` vêm de um modelo, não de avaliação humana. O
  filtro de relevância faz parte da régua, então o "100% relevante" do top novo é circular. A auditoria manual de
  canais foi feita sobre o top por ER; canais que só aparecem no top novo não foram auditados.
- **Janela curta do Foco B.** A coleta traz até 38 posts por perfil. Em 12 dos 28 perfis isso cobre 60 dias ou
  menos, e em 9 cobre até 6 semanas. A coleta foi em 24/11, então Black Friday e fim de ano pesam. 115 posts tinham
  menos de 7 dias e ficaram fora da régua.
- **Intenção de compra é amostra pequena.** A Apify devolve só parte dos comentários de cada post. 703 comentários
  do top e do controle foram classificados, em 87 posts. O cruzamento com preço tem 10 posts. Comentário não é venda.
- **Scraping de dados públicos.** As duas coletas do Instagram usam a Apify sobre dados públicos. Não é API oficial,
  e a rota pode mudar ou parar.
- **Crédito da Feita:** o crédito é restrito ao DeepSeek, que não lê vídeo. Por isso o vídeo depende da cota grátis
  do Gemini.
- **Mesmo modelo escreve e checa:** no agente, o DeepSeek redige e também faz a checagem. O ideal seria outro modelo
  checar.
- **Nenhuma régua foi validada contra resultado de negócio.** Não existe rótulo externo de alto desempenho. O teste
  fora da amostra mede previsão de engajamento, não qualidade do conteúdo.
