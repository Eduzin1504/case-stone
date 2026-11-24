# Conteúdo de alto engajamento para MPEs — Case Stone / Inteli Academy

Pergunta: quais características de conteúdo, formato e perfil de criador aparecem nas publicações de maior engajamento voltadas a micro e pequenos empreendedores, e como transformar isso em criativos para a Stone?

## Como rodar
```bash
uv venv --python 3.12 .venv && uv pip install -r requirements.txt
cp .env.example .env            # preencha YOUTUBE_API_KEY e GEMINI_API_KEY
.venv/bin/python pipeline.py check
.venv/bin/python pipeline.py discover    # revise data/canais.csv (coluna incluir)
.venv/bin/python pipeline.py collect
.venv/bin/python pipeline.py rank
.venv/bin/python pipeline.py categorize  # retoma de onde parou (cache em SQLite)
.venv/bin/python pipeline.py analyze
.venv/bin/python pipeline.py validate --gerar   # preencha data/validacao.csv
.venv/bin/python pipeline.py validate
.venv/bin/python agent.py gerar_criativo "Reels sobre receber no Pix" --segment alimentação
.venv/bin/python mcp_server.py           # servidor MCP (stdio)
.venv/bin/python test_logic.py
```

## Base de dados
- **Fonte:** YouTube Data API v3 (oficial e gratuita). Shorts = vídeos de até 180 s. A coleta usa a playlist de Shorts do canal (`UUSH…`) e, se ela não existir, a playlist de uploads filtrada por duração.
- **Seleção de canais:** busca por palavras-chave de MPE (`KEYWORDS` em `pipeline.py`) + lista manual (`canais_manuais.txt`). Mínimo de 1.000 inscritos e 30 vídeos, revisão manual da coluna `incluir`, com porte pequeno (<50 mil), médio (<500 mil) e grande.
- **Janela:** publicações entre 14 e 365 dias antes da coleta (a data da coleta fica em `coletado_em`).
- **Limitações:** <!-- preencher: volume final, canais, % sem curtidas públicas, viés da busca do YouTube, Instagram fora da base -->

## Metodologia
1. **Engajamento:** `er = (curtidas + comentários) ÷ inscritos`. Alto desempenho = os 10% superiores (`top`).
2. **Outlier score:** `er` do post ÷ mediana do `er` do próprio canal (só canais com 5 ou mais vídeos). Isola o efeito do conteúdo da popularidade do criador.
3. **Rubrica:** o Gemini assiste o vídeo (link do YouTube) e devolve JSON validado por Pydantic (`Rubrica`). Se o vídeo falhar, ele usa a thumbnail mais título e descrição (coluna `fonte`). Duração e tamanho da legenda são calculados, não perguntados ao modelo.
4. **Controle e lift:** os vídeos do top 10% e uma amostra aleatória do mesmo tamanho do resto (seed 42) são categorizados. `lift = freq_top ÷ freq_resto` separa o que é associado ao sucesso do que é só comum no nicho.
5. **Validação:** 50 vídeos categorizados à mão, com concordância e kappa de Cohen por campo.
6. **Agente (LangGraph):** `recuperar` (consulta determinística à base) → `redigir` (LLM) → `checar`. A checagem descarta criativo sem `inspirado_em` válido e reavalia o gancho e o CTA pela rubrica; se o criativo fica abaixo da mediana do top, volta para reescrita (até 3 vezes). Cada execução é registrada em `data/execucoes.jsonl`.

## Resultados
<!-- preencher com data/achados.csv, notas.csv, perfis_destaque.csv, validacao_resultado.csv -->

## Limitações e evolução
- Padrões observados, não causais. Não há modelo preditivo (fora do escopo).
- Instagram não coletado: sem rota oficial gratuita sem app da Meta. Próximo passo: Business Discovery API com um app da Stone.
- Limites gratuitos do Gemini podem mudar; o pipeline faz cache, backoff e fallback para thumbnail.
