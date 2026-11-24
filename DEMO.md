# Roteiro da demo (cerca de 6 min)

## Preparação (antes da apresentação)
1. Rode `.venv/bin/python pipeline.py check` para conferir as chaves.
2. No Claude Desktop, adicione o servidor MCP em `claude_desktop_config.json`:
```json
{"mcpServers": {"impulso-conteudo": {
  "command": "/home/eduardo/fellow/Stone/.venv/bin/python",
  "args": ["/home/eduardo/fellow/Stone/mcp_server.py"]
}}}
```
3. Reinicie o Claude Desktop e confira se a tool `conteudo_mpe` aparece.

## Interface (Streamlit)
- Abrir: `.venv/bin/streamlit run app.py`. A interface fica em `http://localhost:8501`.
- Sem rede: abra `http://localhost:8501/?offline=1` ou ligue "Usar respostas salvas". A tela mostra execuções reais do agente, lidas de `data/execucoes.jsonl`.
- No topo fica o seletor "Foco da análise", com "Impulso → empreendedor" (Foco A) e "Negócio → cliente" (Foco B). A linha abaixo dele mostra a base do foco escolhido.
- As abas são Agente, Ranking, Perfis em destaque, Padrões, Base e método e Playbook. O agente gera criativos só para o Foco A. As outras abas mudam com o foco.
- A tela chama a mesma `run()` do `agent.py` e do servidor MCP. O "comprovante" de cada criativo roda `antislop.checar()` em código e confere se as referências existem na base.

## As 3 perguntas (foco "Impulso → empreendedor", aba Agente)
1. **analisar:** "O que diferencia os posts de alto engajamento sobre finanças no Instagram?"
   - Mostra: os findings com lift e selo, e a explicação que cita os posts reais.
2. **recomendar:** "Quais 3 pautas o Impulso deveria postar em dezembro?"
   - Mostra: as recomendações ligadas aos padrões confirmados e o insight "reação não é clique".
3. **gerar_criativo:** "Carrossel de fim de ano sobre separar o dinheiro do negócio do dinheiro de casa"
   - Mostra: o criativo com gancho, slides, CTA de participação e "inspirado em" com links reais.
   - Clique num link para provar que a referência existe.

## O ponto do Foco B (foco "Negócio → cliente", aba Padrões)
4. Troque o seletor para "Negócio → cliente" e abra a aba Padrões.
   - Pergunta para a plateia: "O que faz o cliente curtir é o mesmo que faz o cliente pedir?"
   - Mostra: humor/trend com lift 3,93 (12 posts no top) e "produto em destaque" com lift 0,58, porque é o post padrão de todos.
   - Fecha com o achado do `PLAYBOOK_B.md` (aba Playbook): posts de humor têm 2% de comentários com intenção de compra. Posts que mostram o preço têm 59%, contra 9% dos que não mostram. São só 10 posts com preço, então é indício.
   - Diga a limitação: o lift do Foco B foi calculado com imagens e legenda, sem ver o vídeo.
5. Se sobrar tempo, volte ao Foco A. A aba Ranking compara o top atual com o top pelo ER puro. A aba Base e método tem a avaliação da régua.

## Se a rede ou a API falhar (plano B offline)
- Os criativos já gerados estão em `data/criativos_playbook.json`. O playbook com os 5 criativos está no `PLAYBOOK.md`.
- O Foco B não depende de rede: as abas leem `data/foco_b.db`, `data/b_achados.csv` e o `PLAYBOOK_B.md`.
- Todas as execuções do agente ficam em `data/execucoes.jsonl`, com a entrada e a saída completas.
- Pelo terminal, sem o Claude Desktop: `.venv/bin/python agent.py gerar_criativo "..." --segment beleza`.

## Mensagem de fechamento
"A base mostra o que engaja no mercado. Os Ads do Impulso mostram o que gera clique. O agente cruza os dois e escreve
no tom do Impulso. No Foco B, a mesma lição aparece do lado do lojista: curtida não é pedido. O próximo passo é o
piloto em Ads, para medir inscrição e não só curtida."
