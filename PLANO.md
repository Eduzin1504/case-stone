# Plano de tasks: Case Impulso Stone

Entrega: 25/11/2026, presencial. Arquitetura: https://claude.ai/artifact/Hv5KCvEBBwMzeBwRpPtbUR

## Decisões T0 (23/11)
- **Instagram:** Apify, com Instaloader como plano B. É scraping de dados públicos, então fica documentado como limitação
- **Dados internos** (relatório e Ads): entram no playbook e nos slides só agregados (CTR, % de views). Os links da conta de anúncios não aparecem
- **Lead:** inscrição ou engajamento no Impulso (@impulsostone). Cliente Stone fica como desdobramento
- **v0:** reaproveitada. O código de YouTube, ranking, kappa, agente e MCP vem de `_arquivo/case_v0`
- **LLM/VLM:** Feita.ai (`gemini-3.8-flash` para vídeo); Gemini grátis como fallback

Cada task lista as **decisões** que tomamos quando chegarmos nela e o critério de **pronto**.
Caminho crítico: T0 → T1 → T3 → T4/T5 → T6 → T7 → T8 → T9 → T11 → T12 → T15 → T18 → T20

## Anti-slop (relatório `reports/AI slop e processos de design.md`, 23/11)
O agente segue o Double Diamond, em vez de só responder a um prompt:
- **Descobrir (T2, T11):** o corpus próprio com CTR dos Ads, os posts orgânicos e as referências de mercado com métrica. Os pares bom/ruim são a âncora ("Empreendedor(a), queremos…" com 8,82% × "Vender mais não é sorte" com 0,77%)
- **Definir (T14):** os campos de especificidade ficam no contrato (segmento, dor concreta, data ou ocasião, número em R$ ou prazo). Sem eles, o agente pede antes de gerar
- **Desenvolver (T15):** de 8 a 10 ganchos por ângulos distintos (pergunta, número, bastidor, erro comum, depoimento, convite), com probabilidades verbalizadas (Verbalized Sampling). Mantém 1 ou 2 de baixa probabilidade
- **Proibições (T15):** `antislop.checar()` roda depois da geração, em código. Jargão, clichê, motivacional vazio, "não é só X, é Y", emojis e travessões em excesso e falta de algo concreto voltam como feedback para reescrever. A lista é recalculada na T11 contra posts reais de MEIs
- **Crítica (T15):** juiz cego de outra família de modelo, com rubrica decomposta, um critério por vez. Inclui o teste de troca de marca: se outra marca pudesse postar, reprova
- **Coletivo (T17):** similaridade entre os criativos do lote, para os 5 do playbook não convergirem
- **Escopo:** o agente escreve roteiro, legenda e carrossel para pessoas reais gravarem. Não gera rostos sintéticos de empreendedores

## Nova régua de alto desempenho (decidida em 23/11, após a auditoria)
Base: `reports/Métricas de engajamento em redes.md` e o teste em `teste_modelo_misto.py`.
- **Métrica reportada:** continua o ER do TAPI, (curtidas + comentários) ÷ seguidores
- **Base elegível:**
  - só canais validados no artifact https://claude.ai/artifact/Y9MqCcVX9PUAnQi9SwhXHs (coleção `veredictos`)
  - post que a rubrica não marcou como irrelevante (`relevante_mpe`) nem como voltado ao consumidor final (`publico_alvo`)
  - criador com 5 posts ou mais e post com 7 dias ou mais
- **Seleção do top:** top 10% por plataforma × faixa, pelo resíduo do modelo misto `log1p(curtidas+comentários) ~ log(seguidores) + formato + log(idade) + (1|criador)`, com no máximo 3 posts por criador
- **Perfis em destaque:** ordenados pelo efeito do criador no modelo, que já vem encolhido para perfis com poucos posts
- **Evidência para o slide:** a elasticidade em relação aos seguidores é 0,36 no IG e 0,39 no YT, contra o 1,0 que o ER assume; o criador explica cerca de 55% da variância (base sem filtros). Na base elegível, `data/avaliacao_regua.md` dá b ≈ 0,37 e ICC de 0,49 a 0,54
- **Feito em 24/11:** top novo categorizado; padrões, cruzamento, perfis e playbook recalculados; README e interface atualizados. Falta só o deck (T20)
- **Avaliação (`data/avaliacao_regua.md`):** a régua nova tira o viés de tamanho e a concentração, mas o modelo misto não supera o outlier simples fora da amostra. Fica declarado como limitação no README

## Estado em 24/11
**Pronto**
- **Dois focos.** Foco A, "Impulso → empreendedor" (`data/stone.db`, `PLAYBOOK.md`). Foco B, "Negócio → cliente" (`foco_b.py`, `data/foco_b.db`, `PLAYBOOK_B.md`). O campo `publico_alvo` da rubrica separa os dois
- **Validação de canais:** 80 vereditos em `data/veredictos.csv` (74 do artifact e 6 da auditoria); 14 canais excluídos
- **Régua nova aplicada:** top de 47 posts de 19 criadores no Instagram e 203 posts de 76 criadores no YouTube, com controle do mesmo tamanho. A régua antiga fica na coluna `top_er_puro`
- **Avaliação da régua:** `avaliacao_regua.py` e `data/avaliacao_regua.md`
- **Categorização do Foco A:** Instagram com 92 de 94 posts do top e do controle. YouTube com os 332 da amostra do lift, sendo 70 em vídeo e 262 por thumbnail e texto
- **Foco B:** 28 negócios, 1.013 posts, 62 no top e 62 no controle, 124 com rubrica por imagens e legenda, intenção de compra nos comentários
- **Interface:** `app.py` com seletor de foco e as abas Agente, Ranking, Perfis em destaque, Padrões, Base e método e Playbook; `test_app.py`
- **Documentação:** README, DEMO e este plano atualizados

**Pendente**
- Recategorizar em vídeo o YouTube (262 posts da amostra) e o Foco B (só 20 dos 124 posts foram vistos em vídeo) quando a cota do Gemini renovar. Depois, rodar de novo `analyze`, `cruzar` e `foco_b.py analisar`
- Validação humana da amostra nova. O kappa atual vem de 10 posts da amostra anterior, e o Foco B não tem validação
- Slides e ensaio (T20)
- Opcional: decidir se o canal Tudo de Laço sai (está na auditoria como fora do perfil, ficou como "dúvida" e tem 3 posts no top)

---

## Fase 0 · Fundação (dom 22/11)

- [x] **T0. Alinhamentos bloqueantes** · 15 min
  - Decisões: rota do Instagram liberada no kickoff; se os dados internos podem aparecer no playbook e nos slides; se o lead é inscrição no Impulso ou cliente Stone; se reaproveitamos a v0 (`_arquivo/case_v0`)
  - Pronto: respostas registradas no topo deste arquivo

- [x] **T1. Setup do projeto e chaves** · 30 min · depende de T0
  - Decisões: estrutura de pastas; quais chaves (YouTube obrigatória; Apify e `FEITA_API_KEY` já no `.env`; Gemini grátis vira fallback)
  - Feita.ai (testado em 23/11): gateway compatível com a OpenAI em `https://api.feita.ai/gateway/v1`. **Os US$ 100 (10.000 créditos) valem só para `deepseek/deepseek-v4.1-flash-1017`** (texto + imagem, sem vídeo); o resto sai de um saldo livre de ~US$ 1,08, conferido em 23/11 em `GET /v1/me`. Precisa de header `User-Agent` (sem ele, o Cloudflare devolve 403 com o código 1010)
  - Pronto: ambiente instalado e um comando `check` passando com todas as chaves

## Fase 1 · Dados (dom 22/11)

- [x] **T2. Base interna do Impulso** · 1 h · depende de T0
  - Decisões: critério de alto e baixo desempenho nos Ads (CTR); quais criativos entram; se baixamos as imagens dos anúncios para aplicar a rubrica
  - Pronto: `impulso_interno.csv` com os posts orgânicos e os criativos de Ads, métricas e rótulo

- [x] **T3. Lista de perfis (30+)** · 1–2 h · depende de T1
  - Decisões: fontes (5 parceiros do relatório, aba seguindo de Stone, Ton, Impulso e Sebrae, busca no YouTube, concorrentes); limites das faixas (a aula sugere micro até 10 mil, médio de 10 a 100 mil, grande acima); quantos perfis por plataforma e por segmento
  - Pronto: `perfis.csv` com as colunas origem, faixa, plataforma e segmento, revisado à mão
  - Feito (23/11): YouTube com 10 buscas de Shorts e 103 canais após a triagem por LLM. Instagram com sementes (parceiros e embaixadores), os mesmos @ dos canais do YouTube e autores de 7 hashtags de MPE, dando 34 perfis. A busca de perfis por palavra-chave na Apify não funcionou ("MEI" trouxe contas alemãs), e o `relatedProfiles` vem vazio sem login. Gasto na Apify: US$ 0,94

- [x] **T4. Coleta no YouTube** · 1 h · depende de T3
  - Decisões: definição de Short (duração máxima); janela de datas; máximo de vídeos por canal
  - Pronto: vídeos com 14 dias ou mais salvos na base, com a data da coleta

- [x] **T5. Coleta no Instagram** · 1–3 h · depende de T0 e T3
  - Decisões: rota; tipos de post (Reels, carrossel, imagem); volume por perfil; cache e backoff
  - Pronto: posts com legenda, tipo, data, curtidas, comentários e seguidores na base
  - **Logo após a coleta:** baixar a mídia (vídeo e imagens) dos candidatos ao top e ao controle, porque as URLs da Apify expiram. Isso alimenta o VLM na T9

- [x] **T6. Schema único e documentação da base** · 45 min · depende de T4 e T5
  - Decisões: campos do schema `Post`; armazenamento (SQLite, DuckDB ou Parquet)
  - Pronto: uma tabela com as duas plataformas e a seção "Base de dados" do README escrita (origem, período, volume, critérios, limitações)

## Fase 2 · Análise (seg 23/11)

- [x] **T7. Ranking** · 45 min · depende de T6
  - Decisões: métrica principal por plataforma (no YouTube, dividir por inscritos ou por views); top 10% por plataforma ou geral; métricas secundárias (outlier score, taxa de conversa)
  - Pronto: coluna `top` e amostra de controle do mesmo tamanho definidas
  - Atualizado (24/11): o top passou a sair da régua nova (seção acima). O ER puro fica em `top_er_puro`

- [x] **T8. Rubrica** · 45 min · depende de T2
  - Decisões: campos extras calibrados pelos Ads (convite à participação, gatilho de identificação, nota de genérico); como os temas se encaixam nos 5 pilares do Impulso; o texto do prompt
  - Pronto: schema Pydantic e prompt testados em 5 posts

- [x] **T9. Mídia e categorização** · 3–5 h, a maior parte rodando sozinha · depende de T7 e T8
  - **Onde entra o VLM.** YouTube: Gemini lê pela URL. Reels: vídeo pela Files API, ou frames (ffmpeg) + transcrição (faster-whisper). Carrossel e imagem: as imagens. Base interna: criativos exportados do Gerenciador de Anúncios
  - Testado na Feita: `gemini-3.8-flash` lê a URL do YouTube com áudio e mp4 em base64 (cerca de US$ 0,002 por vídeo curto); `qwen3.8-flash` lê só o mp4 em base64, mas não a URL do YouTube, e custa metade. Como a Feita lê o vídeo inteiro, o nível 2 sai quase de graça
  - Decisões: modelo e fallback; nível 1 (thumbnail + legenda) ou nível 2 (frames + transcrição); quantos posts categorizar
  - Pronto: top, controle e base interna categorizados, com a fonte usada registrada em cada post
  - Atualizado (24/11), régua nova: Instagram com 92 de 94 posts; YouTube com 332 posts, 70 em vídeo e 262 por thumbnail e texto, porque a cota grátis do Gemini acabou. Foco B com 124 posts por imagens e legenda
  - Feito (23/11), régua antiga: Instagram com 133 de 134 posts pelo Gemini vendo vídeo e imagens. YouTube com 106 pelo Gemini vendo o vídeo, parcial, e 358 de 360 em nível 1 pelo DeepSeek (thumbnail, título e descrição), na tabela separada `categorias_n1`. A comparação entre os métodos fica em `data/comparacao_metodos.csv`. O Gemini caiu (503) na Feita e no Google, e o plano grátis do Google tem limite de 20 requisições por dia

- [x] **T10. Validação manual** · 1,5 h · depende de T9
  - Decisões: amostra estratificada ou aleatória; quais campos validar
  - Pronto: 50 posts rotulados à mão, kappa por campo e a lista de campos pouco confiáveis
  - Feito (23/11): 10 posts do Instagram rotulados às cegas, no artifact UQmwZYnuTHR8j3PmAs7h9p. Campos confiáveis: texto na tela (kappa 1,0), CTA (0,60), tema (0,53), formato (0,46), gatilho (0,41). Campos fracos: pilar (0,22), gancho (0,04), convite à participação (−0,20)

- [x] **T11. Análise de padrões** · 1,5 h · depende de T9
  - Decisões: recortes (tema, formato, segmento, faixa); quais gráficos
  - Pronto: tabela de lift, perfis em destaque e gráficos para o playbook

- [x] **T12. Cruzamento mercado × casa** · 1 h · depende de T2, T9 e T11
  - Decisões: regra para classificar cada padrão como confirmado, só mercado ou contradito
  - Pronto: cada padrão relevante com o seu selo e as evidências

- [x] **T13. Intenção nos comentários** · opcional · depende de T5
  - Decisões: regex ou LLM; quantos comentários por post
  - Pronto: indicador de lead por post
  - Feito (24/11), só no Foco B: regex + DeepSeek nos comentários que a Apify traz junto do post (`foco_b.py comentarios`). No Foco A não foi feito

## Fase 3 · Agente (ter 24/11)

- [x] **T14. Contrato e função `run`** · 45 min · depende de T11
  - Decisões: modos (`analisar`, `recomendar`, `gerar_criativo` e talvez `avaliar_criativo`); campos extras na saída (selo de evidência, pilar)
  - Pronto: entrada e saída validadas com Pydantic

- [x] **T15. Grafo LangGraph** · 2–3 h · depende de T14
  - Decisões: grafo fixo ou ReAct; busca de referências por palavra-chave ou embeddings; o que o nó de checagem verifica (referências, tom de voz, CTA, genérico) e quantas tentativas
  - Pronto: os 3 ou 4 modos funcionando de ponta a ponta, com log em JSONL

- [x] **T16. Servidor MCP** · 30 min · depende de T15
  - Decisões: quantas tools expor
  - Pronto: chamado com sucesso a partir do Claude Desktop ou do MCP Inspector

## Fase 4 · Entregáveis (ter 24/11)

- [x] **T17. Playbook + 5 criativos** · 2 h · depende de T12 e T15
  - Decisões: formato (doc ou PDF); estrutura por pilar; quais criativos (incluir Natal e fim de ano?); se fazemos a versão para a lojista
  - Pronto: padrões com selo, exemplos reais, perfis em destaque e 5 criativos com referências
  - Atualizado (24/11): `PLAYBOOK.md` regerado com a régua nova; `PLAYBOOK_B.md` com as 5 recomendações para o lojista

- [x] **T18. README final** · 1 h · depende de todas as anteriores
  - Pronto: todas as seções pedidas no TAPI
  - Atualizado (24/11): dois focos, régua nova, avaliação da régua e limitações da categorização

- [x] **T19. Demo** · 1 h · depende de T16
  - Decisões: MCP ao vivo, Streamlit ou notebook; roteiro com 2 ou 3 perguntas
  - Pronto: roteiro ensaiado e funcionando offline caso a rede falhe
  - Atualizado (24/11): interface Streamlit com seletor de foco; roteiro no `DEMO.md` com um ponto do Foco B

- [ ] **T20. Slides e ensaio** · 2 h · depende de T17 e T19
  - Decisões: narrativa; incluir o plano de teste piloto em Ads
  - Pronto: deck fechado e um ensaio cronometrado

---

**Ordem de corte se atrasar:** T13 → Streamlit → fallback local → embeddings → versão para a lojista.
**Risco principal:** T5, a coleta do Instagram. Se travar, a análise segue só com o YouTube e uma amostra manual do Instagram.
