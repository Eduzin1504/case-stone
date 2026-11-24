# Pauta Impulso em React: desenho e contrato

Data: 24/11/2026. Entrega do case: 25/11/2026. Aprovado pelo usuário no chat ("faça com React, tudo agora; só a conversa em linguagem natural fica para a fase 2").

## Por quê
A interface em Streamlit foi julgada simples, sem destaque e com cara de IA. O usuário respondeu 30 perguntas de design (abaixo) e escolheu um site próprio. O Streamlit atual (`app.py`, porta 8501) continua no ar como plano B da demo e NÃO deve ser alterado.

## Metas, não metas, antimetas
- Metas: um produto com cara de app de criador, mídia em primeiro plano, navegação clara, dados que se desenham; tudo que existe hoje no Streamlit mais as funcionalidades novas escolhidas.
- Não metas (fase 2): conversa em linguagem natural; login; deploy em nuvem.
- Antimetas: inventar números; quebrar o Streamlit ou o pipeline; grade de cartões idênticos, rótulos minúsculos em caixa alta sobre toda seção, gradiente em texto, vidro fosco, emoji como ícone.

## Escolhas do usuário (as 30 respostas)
| Tema | Escolha |
|---|---|
| Direção | App de criador: mídia em primeiro plano, pouco texto |
| Tema | Claro e escuro, com botão de alternar (persistir a escolha) |
| Cor | Lima em blocos: lima como fundo de cartões e seções de destaque, texto floresta |
| Identidade | Comprovante de maquininha (checagens, resumos), etiqueta de preço (números-chave, selos), carimbo (top, aprovado, confirmado) |
| Títulos | Anton, caixa alta |
| Texto | Lexend |
| Números | Na fonte do título (Anton), grandes como manchete |
| Navegação | Barra lateral |
| Focos | Porta de entrada: a primeira tela pergunta o que a pessoa quer responder; depois o foco fica no cabeçalho, trocável |
| Início | Feed de destaques: posts que mais superaram o esperado, cada um com o porquê |
| Densidade | Equilibrada |
| Cantos | Misto: mídia e botões arredondados; dados e tabelas retos |
| Card de post | Miniatura + rodapé (criador, ER, vezes o esperado) |
| Catálogo | Mosaico: posts do top maiores, alturas variadas |
| Hover no post | Ficha rápida ao lado (métricas e etiquetas), sem sair da grade |
| Detalhe do post | Painel lateral que desliza da direita; a grade continua visível |
| Prévia | Moldura de celular |
| Padrões | Barras pareadas (top × controle) |
| Rankings | Corrida de barras animada, que se reordena ao trocar filtro |
| Criador | Página tipo perfil de rede social: cabeçalho, números, grade dos posts |
| Visualizações novas | Esperado × real (dispersão); mapa de temas (retângulos proporcionais); anatomia de um post do top; funil curtida → pedido (Foco B) |
| Avaliar meu post | Medidor + recomendações (com marcas "média dos comuns" e "média do top") |
| Pauta do agente | Storyboard: quadro a quadro de cada cena ou slide |
| Funcionalidades novas | Comparar dois posts; coleções; busca por ideia; exportar; histórico das avaliações. (Conversa em linguagem natural: fase 2) |
| Movimento | Dados que se desenham ao entrar na tela (barras crescem, números contam) |
| Micro-interações | Card que levanta no hover; miniatura que cresce até virar o detalhe; progresso narrado na avaliação |
| Tom | Direto e neutro |
| Ícones | Sem ícones: tipografia e cor |
| Tecnologia | React + API |

## Abordagens consideradas
1. Tudo de uma vez em React + API (escolhida pelo usuário, com agentes em paralelo).
2. Duas fases, com as funcionalidades novas depois da entrega (minha recomendação; o usuário preferiu fazer tudo agora, deixando só a conversa em linguagem natural para a fase 2).
3. Site estático sem framework + API mínima (descartada: coleções, histórico e comparação ficam difíceis de manter).

## Arquitetura
- `api/` : FastAPI (Python, no `.venv` do projeto), porta **8600**. Só leitura sobre `data/stone.db` (Foco A) e `data/foco_b.db` (Foco B) e sobre os CSVs; escrita apenas em `data/app.db` (coleções e histórico de avaliações). Reaproveita `avaliar.py`, `agent.py` e a lógica de dados de `ui.py` (copiar as funções puras; não importar `streamlit`).
- `web/` : Vite + React 18 + TypeScript, porta **5173** em desenvolvimento, com proxy de `/api` e `/midia` para a 8600. Em produção, `npm run build` gera `web/dist`, servido pela própria API em `/`.
- Bibliotecas do front: `react-router-dom` (rotas), `@tanstack/react-query` (dados), `motion` (animações; `LayoutGroup`/`layoutId` para a miniatura que vira detalhe e para a corrida de barras), `d3-scale`, `d3-hierarchy`, `d3-shape` (cálculo das visualizações; desenhar em SVG com React), `html-to-image` (exportar PNG). CSS puro com variáveis (sem Tailwind, sem biblioteca de componentes).
- Um comando sobe tudo: `./rodar.sh` (API + front compilado em http://localhost:8600).

## Sistema visual (fonte única: `web/src/styles/tokens.css`)
- Cores (claro): `--floresta #00442f`, `--lima #c5ff1f`, `--lima-suave #d9ff66`, `--dados #1f9e55`, `--magenta #b02d63` (só "contradito", alerta e nota baixa), fundo `#f4f7f4`, superfície `#ffffff`, afundado `#e9efea`, texto `#14231b`, texto secundário `#536359`, linha `#dbe4dd`. Escuro: fundo `#07140e`, superfície `#0f2118`, afundado `#0b1a13`, texto `#e8f1ea`, secundário `#9db3a5`, linha `#21382c`; floresta de tinta vira lima (`#c5ff1f`) e os blocos lima continuam lima com texto `#00331f`. `data-theme` no `<html>`, salvo em `localStorage`, padrão pelo sistema.
- Tipos: Anton (títulos em caixa alta e números grandes), Lexend 400/500/600 (texto e interface), JetBrains Mono (só rótulos técnicos pequenos e o comprovante). Google Fonts.
- Forma: mídia e botões com raio 16–20px e pílulas; cartões de dados, tabelas e barras com raio 2–4px.
- Lima em blocos: no máximo um bloco lima por dobra de tela. Texto sobre lima sempre floresta.
- Identidade: `<Comprovante>` (papel térmico com picote, fonte mono), `<Etiqueta>` (número-chave em Anton sobre lima, com canto de etiqueta), `<Carimbo>` (círculo com borda dupla, levemente girado: TOP 10%, APROVADO, CONFIRMADO NOS ADS).
- Movimento: barras crescem e números contam ao entrar na tela (uma vez); cards levantam 4px no hover; miniatura → detalhe com `layoutId`; corrida de barras com `layout`. Curvas ease-out; nada de bounce. Respeitar `prefers-reduced-motion`. O conteúdo é visível sem animação (animação melhora, não esconde).
- Sem ícones. Setas e marcas são tipográficas (→, ×, ✓).
- Textos em português do Brasil, tom direto e neutro. Nomes de campos crus nunca aparecem (usar os rótulos da API).
- Acessibilidade: contraste 4,5:1, foco visível (anel lima), tudo operável por teclado, `alt` nas mídias.
- Largura: funciona em 1280px e em 400px (a barra lateral vira gaveta; o painel lateral vira tela cheia).

## Rotas do front
| Rota | Página | Dono |
|---|---|---|
| `/` | Porta de entrada (escolha do foco) | P1 |
| `/inicio` | Feed de destaques | P1 |
| `/catalogo` (+ `?post=ID` abre o painel) | Catálogo em mosaico, filtros, ficha no hover, painel lateral | P1 |
| `/busca` | Busca por ideia | P1 |
| `/rankings` | Corrida de barras (posts e criadores) | P2 |
| `/criadores/:id` | Página de perfil do criador | P2 |
| `/comparar?a=&b=` | Comparar dois posts | P2 |
| `/padroes` | Barras pareadas por grupo, com exemplos | P3 |
| `/mapa` | Visualizações novas: esperado × real, mapa de temas, anatomia, funil (B) | P3 |
| `/metodo` | Como escolhemos o top, números, avaliação da régua, limitações | P3 |
| `/avaliar` e `/avaliar/historico` | Avaliar meu post e histórico | P4 |
| `/criar` | Agente: pauta em storyboard, respostas salvas | P4 |
| `/colecoes` e `/colecoes/:id` | Coleções | P4 |
| `/playbook` | Playbook editorial | P5 |

O foco atual fica em contexto React + `localStorage` e vai em toda chamada como `?foco=A|B`.

## Componentes compartilhados (feitos pela fundação, usados por todas as páginas)
`AppShell` (barra lateral, cabeçalho com foco e tema), `PostCard` (variações `mosaico`, `compacto`, `linha`; aceita `layoutId`), `FichaRapida` (hover), `PainelPost` (detalhe lateral, aberto por `?post=`), `MolduraCelular` + `Midia` (YouTube embed, vídeo local, carrossel de imagens, capa), `Etiqueta`, `Carimbo`, `Comprovante`, `BarraPar` (top × controle animada), `NumeroConta`, `Chip`, `Selo` (confirmado, contradito, só mercado, frágil), `Botao`, `Seg` (controle segmentado), `Campo`, `Vazio`, `Erro`, `Esqueleto`, `BotaoColecao` (salvar post numa coleção), `BotaoExportar` (PNG do nó + imprimir em PDF), hooks `useFoco`, `useTema`, `useApi`.

## Contrato da API (prefixo `/api`; JSON; erros como `{erro: "mensagem para o usuário"}` com status 4xx/5xx)
Tipos em `web/src/api/tipos.ts` (a fundação escreve; a API segue):

```ts
type Foco = "A" | "B";
type PostResumo = { id: string; foco: Foco; plataforma: "instagram" | "youtube"; formato: string; // "Reels" | "Carrossel" | "Imagem" | "Short"
  canal: string; canal_id: string; titulo: string; thumb: string | null; tem_video: boolean;
  er: number | null; vezes: number | null; // vezes o esperado; null se não concorre
  top: boolean; posicao_top: number | null; likes: number; comentarios: number; views: number | null;
  publicado: string | null; gancho: string | null; tema: string | null; tipo_gancho: string | null; porte: string | null; url: string };
type Midia = { tipo: "youtube" | "video" | "imagens" | "capa" | "nenhuma"; youtube_id?: string; video_url?: string; imagens?: string[] };
type PostDetalhe = PostResumo & { midia: Midia; legenda: string; leitura: { rotulo: string; valor: string }[];
  notas: { rotulo: string; valor: number; mediana_top: number | null }[]; elementos: string[];
  criador: CriadorResumo | null; parecidos: PostResumo[]; pct_intencao: number | null; metodo_leitura: string | null };
type CriadorResumo = { id: string; foco: Foco; nome: string; plataforma: string; seguidores: number; porte: string;
  vezes: number | null; n_top: number; n_posts: number; tema: string | null; formato: string | null; thumbs: string[]; url: string };
type Padrao = { campo: string; valor: string; rotulo: string; grupo: string; freq_top: number; freq_controle: number;
  lift: number | null; n_top: number; selo: string | null; fragil: boolean; exemplos: PostResumo[] };
```

| Método e rota | Resposta |
|---|---|
| `GET /focos` | `[{id, nome, descricao, pergunta, base: {posts, criadores, top, por_plataforma: {instagram, youtube}, coletado_em}}]` |
| `GET /posts?foco&plataforma&formato&tema&porte&so_top&com_video&q&ordem&offset&limit` | `{total, itens: PostResumo[], filtros: {plataformas, formatos, temas, portes}}`; `ordem` = `destaques` (padrão) \| `vezes` \| `er` \| `comentarios` \| `recentes` |
| `GET /posts/{id}?foco` | `PostDetalhe` |
| `GET /destaques?foco&limit` | `[{post: PostResumo, porque: string}]` (o porquê é montado da rubrica, sem chamar modelo) |
| `GET /busca?foco&q&limit` | `[{post: PostResumo, score: number, casou: string[]}]` (TF-IDF sobre legenda, gancho, elementos e tema; sem rede) |
| `GET /criadores?foco&plataforma&porte` | `CriadorResumo[]` ordenado por `vezes` |
| `GET /criadores/{id}?foco` | `{resumo: CriadorResumo, bio, posts: PostResumo[], serie: [{id, data, er, vezes, top}]}` |
| `GET /rankings?foco&tipo=posts\|criadores&plataforma&porte&metrica=vezes\|er\|comentarios&limit` | `[{posicao, id, nome, sub, thumb, valor, valor_fmt}]` |
| `GET /comparar?foco&a&b` | `{a: PostDetalhe, b: PostDetalhe, diferencas: [{rotulo, a, b, igual}]}` |
| `GET /padroes?foco&plataforma` | `{plataformas: string[], itens: Padrao[]}` |
| `GET /ads` | `[{criativo, formato, ctr, desempenho}]` (só Foco A) |
| `GET /viz/esperado-real?foco&plataforma` | `{pontos: [{id, canal, esperado, real, top}], nota}` (amostra de até 1.500; todos os do top incluídos; escala log) |
| `GET /viz/temas?foco&plataforma` | `[{tema, n_top, n_controle, pct_top, lift}]` |
| `GET /viz/anatomia/{id}?foco` | `{post: PostResumo, duracao_s, trechos: [{rotulo, texto, inicio_s, fim_s, aproximado}]}` (montado da rubrica: gancho nos 3 primeiros segundos, elementos, CTA; marcar o que é aproximado) |
| `GET /viz/funil?foco=B` | `{etapas: [{rotulo, valor}], por_formato: [{formato, pct_intencao, n}], preco: {com, sem, n_com, n_sem}, comentarios: [{texto, negocio}]}` |
| `POST /avaliar` (multipart: `arquivos[]`, `legenda`, `foco`, `plataforma`, `usar_video`) | `{id}`; roda em segundo plano |
| `GET /avaliar/{id}` | `{estado: "rodando"\|"pronto"\|"erro", etapas: string[], resultado, erro}` (o `resultado` é a saída de `avaliar.avaliar` + `medias: {top, comuns}`) |
| `GET /avaliacoes` e `GET /avaliacoes/{id}` | histórico salvo em `data/app.db` (com miniatura do que foi enviado) |
| `POST /agente` `{modo, pergunta, segmento, filtros}`, `GET /agente/{id}`, `GET /agente/salvas` | job e respostas salvas de `data/execucoes.jsonl`; criativos com `cenas: [{n, tempo, texto}]` já separadas para o storyboard |
| `GET /criativos` | os 5 criativos do playbook, no mesmo formato |
| `GET/POST /colecoes`, `GET/PATCH/DELETE /colecoes/{id}`, `POST/DELETE /colecoes/{id}/posts` | coleções em `data/app.db`: `{id, nome, nota, foco, posts: PostResumo[], criada_em}` |
| `GET /playbook?foco` | `{titulo, linha_fina, atualizado, leitura_min, capitulos: [{id, titulo, markdown}], comentarios?}` (do `PLAYBOOK.md` / `PLAYBOOK_B.md`) |
| `GET /metodo?foco` | `{passos, numeros, avaliacao_md, limitacoes, kappa: [{campo, concordancia, kappa}]}` |
| `GET /saude` | `{ok: true}` |
| `/midia/a/…`, `/midia/b/…`, `/midia/thumbs/…` | arquivos de `data/midia`, `data/midia_b`, `static/thumbs` |

Regras da API: todos os números vêm dos bancos e CSVs; nada inventado. `thumb` do YouTube é `https://i.ytimg.com/vi/<id>/hqdefault.jpg`; do Instagram, `/midia/thumbs/<id>.jpg` quando existir, senão `null`. Campos ausentes viram `null`, nunca erro. CORS liberado para `localhost`. Testes em `api/test_api.py` cobrindo todas as rotas nos dois focos.

## Divisão do trabalho (cada agente só edita o que é seu)
- **API**: `api/**`, `rodar.sh`, `requirements.txt` (acrescentar fastapi, uvicorn, python-multipart).
- **Fundação**: `web/` inteiro na primeira onda (scaffold, tokens, shell, componentes compartilhados, cliente da API com tipos, rotas com páginas vazias, dados de exemplo para desenvolver sem a API).
- **P1 a P5** (segunda onda): só `web/src/paginas/<suas páginas>/**`. Componentes novos de uso de uma página ficam na pasta dela. Se faltar algo num componente compartilhado, criar um componente local e relatar; não editar `web/src/componentes/**` nem `tokens.css`.
- **Integração** (terceira onda): build, `rodar.sh`, capturas de tela de todas as rotas nos dois focos e nos dois temas, correções.

## Fora do escopo desta entrega
Conversa em linguagem natural; contas e login; hospedagem. O README e os slides são atualizados depois.
