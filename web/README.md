# Pauta Impulso · front (React)

Fundação pronta: shell, tokens, componentes compartilhados, cliente da API com tipos e hooks, dados de exemplo e páginas-esqueleto.
Especificação: `../docs/superpowers/specs/2026-11-24-pauta-react-design.md`.

## Rodar

```bash
npm install
npm run dev            # http://localhost:5173, com proxy de /api e /midia para a API em :8600
npm run dev:exemplos   # igual, mas SEM a API: responde com src/api/exemplos (VITE_EXEMPLOS=1)
npm run build          # tsc --noEmit + vite build → dist/
npx tsc --noEmit
```

- **Modo exemplos**: `VITE_EXEMPLOS=1 npm run dev` (ou `npm run dev:exemplos`, ou `VITE_EXEMPLOS=1` em `.env.local`). Todas as rotas do contrato respondem com uma amostra real dos bancos (38 posts do Foco A, 14 do B). Coleções, avaliações e respostas do agente funcionam na memória (somem ao recarregar); os jobs de avaliar/agente simulam o progresso em ~4 s. A barra lateral avisa quando o modo está ligado.
- **Vitrine**: abra `/_vitrine`. Todos os componentes, nos estados principais. Copie de `src/paginas/_vitrine/index.tsx`.
- Sem foco escolhido, toda rota volta para `/`. Escolha um foco na porta de entrada.
- Capturas de tela: `../.venv/bin/python scripts/capturas.py` (com o dev em modo exemplos no ar).
- A porta 5173 é fixa (`strictPort`): só um dev server por vez.

## Regras para quem faz páginas

1. Só edite `src/paginas/<sua pasta>/`. Componente que só a sua página usa fica na sua pasta. Não edite `src/componentes`, `src/styles`, `src/api`, `src/contexto` nem `App.tsx`: se faltar algo, faça local e relate.
2. A página é o `export default` de `src/paginas/<pasta>/index.tsx` e devolve só o conteúdo (um fragmento com `<TituloPagina>` e `<Secao>`s). O shell já dá a barra lateral, o espaçamento entre blocos (48px) e o `<PainelPost>`.
3. CSS puro num arquivo da sua pasta (`import "./catalogo.css"`), com classes prefixadas pelo nome da página (`.catalogo-filtros`). Cores **só** por variável de `styles/tokens.css`. Nada de hex solto, Tailwind ou CSS-in-JS.
4. Sem ícones e sem emoji: setas e marcas são tipográficas (→ × ✓ ↗). Sem bibliotecas novas sem necessidade real (já há `motion`, `d3-scale`, `d3-hierarchy`, `d3-shape`, `html-to-image`).
5. Números sempre pelas funções de `util/formato.ts`. `er`, frequências e percentuais vêm como **fração** (4.37 = 437%); `vezes` e `lift` são multiplicadores; `ctr` dos Ads já vem em %.
6. Toda consulta tem três estados: `<Esqueleto>` carregando, `<Erro erro={error} onTentar={refetch} />`, `<Vazio>` sem dados.
7. Forma: mídia e botões redondos (`--r-midia`, `--r-pilula`); dados, tabelas e barras retos (`--r-dado`). Lima em bloco: no máximo um por dobra (`<Secao bloco="lima">` ou `className="bloco-lima"`); texto sobre lima é sempre floresta (o bloco já troca as variáveis).
8. Proibido: grade de cartões idênticos sem hierarquia, rótulo minúsculo em caixa alta sobre cada seção, gradiente em texto, vidro fosco, borda colorida de um lado só em cartão.
9. Movimento: dados se desenham ao entrar na tela, uma vez (`useEntrou`, `<NumeroConta>`, `<BarraPar>`); curvas `var(--ease)`, sem bounce. `prefers-reduced-motion` já é respeitado globalmente (CSS e `MotionConfig`). O conteúdo tem de estar visível sem animação.
10. Teclado: tudo clicável é `<button>`, `<a>` ou componente daqui. O anel de foco é global; não o remova.

## Onde está cada coisa

```
src/
  main.tsx, App.tsx          provedores e rotas ("/" fora do shell; o resto dentro do AppShell)
  styles/tokens.css          TODAS as variáveis (claro e escuro via <html data-theme="claro|escuro">)
  styles/base.css            reset, utilitários (.t-titulo .t-mega .t-h1 .t-h2 .t-num .t-h3 .t-pequeno .t-sec .t-mono .grifo
                             .pilha .linha .entre .corta-1/2/3 .tabela .so-leitor .nao-imprimir), impressão
  styles/componentes.css     átomos · styles/post.css  PostCard, .mosaico, painel, mídia · styles/shell.css  barra lateral
  api/tipos.ts               tipos do contrato (fonte única)
  api/cliente.ts             api.get/post/patch/delete, ErroApi, EXEMPLOS
  api/hooks.ts               um hook por rota (o foco entra sozinho)
  api/exemplos/              base.json (amostra real) + index.ts (responde todas as rotas)
  contexto/Foco.tsx, Tema.tsx   useFoco(), useTema()
  util/formato.ts            fmtNum, fmtInt, fmtPct, fmtVezes, fmtData, nomePlataforma, nomePorte
  util/useEntrou.ts          useEntrou(ref) para animações de entrada
  componentes/               compartilhados (import de "../../componentes")
  paginas/<pasta>/index.tsx  entrada inicio catalogo busca rankings criador comparar padroes mapa metodo avaliar criar colecoes playbook
  paginas/_vitrine/          a vitrine
scripts/                     gerar_exemplos.py (refaz base.json) e capturas.py (capturas de tela)
public/exemplos/             miniaturas e mídias do modo exemplos (não vão para o dist fora dele)
```

Rotas → pasta: `/`→entrada · `/inicio`→inicio · `/catalogo`→catalogo · `/busca`→busca · `/rankings`→rankings · `/criadores/:id`→criador · `/comparar?a=&b=`→comparar · `/padroes`→padroes · `/mapa`→mapa · `/metodo`→metodo · `/avaliar` e `/avaliar/historico`→avaliar · `/criar`→criar · `/colecoes` e `/colecoes/:id`→colecoes · `/playbook`→playbook. Onde uma pasta atende duas rotas, decida com `useLocation().pathname` ou `useParams().id`.

## Contexto

```tsx
const { foco, setFoco, focos, info } = useFoco();   // foco: "A" | "B"; info = item de GET /focos do foco atual (info?.base.posts…)
const { tema, setTema, alternar } = useTema();       // "claro" | "escuro"
```

## Hooks (`src/api/hooks.ts`)

Consultas devolvem `{ data, isLoading, error, refetch }`; mutações, `{ mutate, mutateAsync, isPending, error }`.

| Hook | Rota | `data` |
|---|---|---|
| `usePosts(filtros?)` | `GET /posts` | `PaginaPosts` `{ total, itens, filtros }` |
| `usePostsInfinito(filtros?, porPagina = 24)` | `GET /posts` paginado | `data.pages[].itens`, `fetchNextPage`, `hasNextPage` |
| `usePost(id)` | `GET /posts/{id}` | `PostDetalhe` |
| `useDestaques(limit = 12)` | `GET /destaques` | `Destaque[]` `{ post, porque }` |
| `useBusca(q, limit = 24)` | `GET /busca` (2+ letras) | `ResultadoBusca[]` `{ post, score, casou }` |
| `useCriadores(filtros?)` · `useCriador(id)` | `GET /criadores` · `/{id}` | `CriadorResumo[]` · `CriadorDetalhe` |
| `useRankings({ tipo, plataforma?, porte?, metrica?, limit? })` | `GET /rankings` | `ItemRanking[]` (mantém a lista anterior enquanto troca) |
| `useComparar(a, b)` | `GET /comparar` | `Comparacao` `{ a, b, diferencas }` |
| `usePadroes(plataforma?)` | `GET /padroes` | `RespostaPadroes` `{ plataformas, itens }` |
| `useAds()` | `GET /ads` (só Foco A) | `Ad[]` |
| `useEsperadoReal(plataforma?)` · `useTemas(plataforma?)` | `GET /viz/esperado-real` · `/viz/temas` | `VizEsperadoReal` · `VizTema[]` |
| `useAnatomia(id)` · `useFunil()` | `GET /viz/anatomia/{id}` · `/viz/funil` (só Foco B) | `VizAnatomia` · `VizFunil` |
| `useEnviarAvaliacao()` | `POST /avaliar` | `mutateAsync({ arquivos, legenda?, plataforma, usar_video? })` → `{ id }` |
| `useAvaliacao(id)` | `GET /avaliar/{id}` (repete a cada 1 s enquanto roda) | `EstadoJob<ResultadoAvaliacao>` `{ estado, etapas, resultado, erro }` |
| `useAvaliacoes()` · `useAvaliacaoSalva(id)` | `GET /avaliacoes` · `/{id}` | `AvaliacaoSalva[]` · `AvaliacaoSalvaDetalhe` |
| `usePerguntarAgente()` | `POST /agente` | `mutateAsync({ modo, pergunta, segmento?, filtros? })` → `{ id }` |
| `useAgente(id)` · `useAgenteSalvas()` · `useCriativos()` | `GET /agente/{id}` · `/agente/salvas` · `/criativos` | `EstadoJob<RespostaAgente>` · `RespostaAgente[]` |
| `useColecoes()` · `useColecao(id)` | `GET /colecoes` · `/{id}` | `Colecao[]` · `Colecao` |
| `useCriarColecao()` · `useEditarColecao()` · `useApagarColecao()` | `POST` · `PATCH` · `DELETE /colecoes` | `mutate({ nome, nota? })` · `mutate({ id, nome?, nota? })` · `mutate(id)` |
| `useAdicionarPost()` · `useRemoverPost()` | `POST` · `DELETE /colecoes/{id}/posts` | `mutate({ colecao, post })` |
| `usePlaybook()` · `useMetodo()` · `useSaude()` | `GET /playbook` · `/metodo` · `/saude` | `Playbook` · `Metodo` · `{ ok }` |
| `useApi<T>(caminho, params?, ligado?)` | qualquer `GET` | genérico |

## Componentes (`import { … } from "../../componentes"`)

Cada arquivo de `src/componentes` começa com um comentário de uso.

| Componente | Uso |
|---|---|
| `AppShell` | Já nas rotas. Barra lateral (marca, foco, navegação, tema), gaveta em telas estreitas, `<PainelPost>`. |
| `TituloPagina` | `<TituloPagina titulo="Catálogo" grifo="do top" sub="…" acoes={<BotaoExportar … />} />` |
| `Secao` | `<Secao titulo="Posts parecidos" sub="…" acao={…}>…</Secao>` · `bloco="lima" \| "afundado" \| "superficie"` |
| `PostCard` | `<div className="mosaico">{posts.map((p, i) => <PostCard key={p.id} post={p} destaque={i === 0} />)}</div>` · `variante="compacto"` · `variante="linha" posicao={3}` · `onAbrir={(p) => …}` troca o clique · `semFicha` · `layoutId={false}` |
| `FichaRapida` | Já embutida no `PostCard` (hover com mouse). Direto: `<FichaRapida post={p} ancora={el.getBoundingClientRect()} />` |
| `PainelPost` | Já montado. Abre com `?post=<id>`. De outro lugar: `const abrir = useAbrirPost(); abrir(id)` (`abrir(null)` fecha). `useLinkDoPost()` dá o href. |
| `MolduraCelular` | `<MolduraCelular largura={280}><Midia … /></MolduraCelular>` |
| `Midia` | `<Midia midia={post.midia} thumb={post.thumb} titulo={post.titulo} url={post.url} plataforma={post.plataforma} />` |
| `Miniatura` | `<Miniatura src={post.thumb} alt={post.titulo} reserva="Instagram" />` (preenche o pai; reserva desenhada se a imagem falhar) |
| `Etiqueta` | `<Etiqueta valor={fmtVezes(p.vezes)} rotulo="o esperado" tamanho="g" />` · `tom="lima" \| "floresta" \| "papel"` |
| `Carimbo` | `<Carimbo texto="TOP" sub="10%" />` · `<Carimbo texto="Confirmado" sub="nos Ads" tom="dados" tamanho={112} giro={6} />` · `cheio` sobre foto |
| `Comprovante` | `<Comprovante titulo="Base" linhas={[{ rotulo: "Posts", valor: "11.676" }]} total={{ rotulo: "No top", valor: "250" }} rodape="…" />` |
| `BarraPar` + `LegendaBarraPar` | `<BarraPar rotulo={p.rotulo} top={p.freq_top} controle={p.freq_controle} lift={p.lift} selo={p.selo} fragil={p.fragil} max={max} />` |
| `NumeroConta` | `<NumeroConta valor={post.likes} />` · `<NumeroConta valor={0.59} formato={fmtPct} className="t-titulo t-mega" />` |
| `Chip` | `<Chip rotulo="Tema">finanças</Chip>` · `<Chip ativo={x} onClick={…}>Só o top</Chip>` · `<Chip onRemover={…}>…</Chip>` |
| `Selo` | `<Selo tipo={padrao.selo} />` (confirmado, contradito, só mercado, inconclusivo, frágil) |
| `Botao` | `<Botao onClick={…}>Salvar</Botao>` · `variante="lima" \| "contorno" \| "fantasma"` · `tamanho="p" \| "g"` · `para="/rota"` · `href="https://…"` · `ocupado` |
| `Seg` | `<Seg rotulo="Plataforma" valor={v} onChange={setV} opcoes={[{ valor: "instagram", rotulo: "Instagram" }]} />` |
| `Campo` | `<Campo rotulo="Nome" value={v} onChange={…} dica="…" erro={…} />` · `multilinha` · `tamanho="g"` · `esconderRotulo` |
| `Seletor` | `<Seletor rotulo="Tema" valor={v} onChange={setV} opcoes={temas} todos="Todos os temas" />` |
| `Vazio` · `Erro` · `Esqueleto` | `<Vazio titulo="Nada por aqui" acao={…}>texto</Vazio>` · `<Erro erro={error} onTentar={refetch} />` · `<Esqueleto tipo="cards" n={8} />` (`"linhas"`, `"texto"`, ou `altura`) |
| `BotaoColecao` | `<BotaoColecao postId={post.id} />` |
| `BotaoExportar` | `const ref = useRef<HTMLDivElement>(null);` `<BotaoExportar alvo={ref} nome="ranking" />` … `<div ref={ref}>…</div>` (PNG e imprimir/PDF) |
| `Markdown` | `<Markdown texto={capitulo.markdown} />` (títulos, listas, negrito, links, citações, tabelas) |
| `Marca` | `<Marca />` o logotipo tipográfico (use na porta de entrada) |

Animação de entrada própria (gráficos em SVG):

```tsx
const ref = useRef<SVGSVGElement>(null);
const entrou = useEntrou(ref);          // true na primeira vez que aparece na tela (e ao exportar/imprimir)
<rect width={entrou ? largura : 0} style={{ transition: "width var(--dur-dados) var(--ease)" }} />
```

Corrida de barras e trocas de ordem: `motion` (`import { motion, AnimatePresence, LayoutGroup } from "motion/react"`) com `layout`.
A miniatura que cresce até o painel usa o layoutId `midia-post-<id>` (`layoutIdDoPost(id)`); não o reutilize para outra coisa.
