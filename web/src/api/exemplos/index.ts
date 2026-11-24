// Dados de exemplo para TODAS as rotas do contrato, usados quando VITE_EXEMPLOS=1.
// base.json é uma amostra REAL dos bancos (ver web/scripts/gerar_exemplos.py); o resto é montado aqui.
// Escritas (coleções, avaliações, agente) ficam só na memória: recarregar a página zera.
import bruto from "./base.json";
import { ErroApi, type Metodo, type Params } from "../cliente";
import { fmtVezes } from "../../util/formato";
import type * as T from "../tipos";

type Extra = {
  midia: T.Midia; legenda: string; leitura: T.Leitura[]; marcas: string[]; notas: Record<string, number>;
  elementos: string[]; duracao_s: number | null; pct_intencao: number | null; rub: Record<string, unknown>;
};
type Item = { resumo: T.PostResumo; extra: Extra };
type PadraoBruto = Omit<T.Padrao, "exemplos"> & { plataforma: string };
type RespostaBruta = Omit<T.RespostaAgente, "referencias"> & { referencias_ids: string[] };
type Base = {
  focos: Record<T.Foco, T.BaseFoco>;
  posts: Record<T.Foco, Item[]>;
  criadores: Record<T.Foco, Record<string, { resumo: T.CriadorResumo; bio: string; serie: T.PontoSerie[] }>>;
  medianas: Record<T.Foco, Record<string, number | null>>;
  rotulos_notas: Record<string, string>;
  padroes: Record<T.Foco, PadraoBruto[]>;
  temas: Record<T.Foco, T.VizTema[]>;
  esperado_real: Record<T.Foco, T.PontoEsperadoReal[]>;
  funil: Pick<T.VizFunil, "etapas" | "por_formato" | "comentarios">;
  kappa: T.Metodo["kappa"];
  playbook: { titulo: string; capitulos: T.Capitulo[] };
  criativos: RespostaBruta[];
  salvas: RespostaBruta[];
};
const base = bruto as unknown as Base;

const focoDe = (p: Params): T.Foco => (p.foco === "B" ? "B" : "A");
const itens = (f: T.Foco) => base.posts[f];
const resumos = (f: T.Foco) => itens(f).map((i) => i.resumo);
const achar = (id: string) => [...base.posts.A, ...base.posts.B].find((i) => i.resumo.id === id);
const naoAchou = (oque: string): never => {
  throw new ErroApi(`${oque} não encontrado.`, 404);
};
const unicos = (xs: (string | null)[]) => [...new Set(xs.filter((x): x is string => !!x))].sort();
const criador = (f: T.Foco, id: string) => base.criadores[f][id]?.resumo ?? null;

// ---------- montagem das respostas ----------
function detalhe(id: string): T.PostDetalhe {
  const it = achar(id) ?? naoAchou("Post");
  const { resumo: r, extra: e } = it;
  const med = base.medianas[r.foco];
  const iguais = (o: T.PostResumo) => (o.tema === r.tema ? 2 : 0) + (o.formato === r.formato ? 1 : 0) + (o.tipo_gancho === r.tipo_gancho ? 1 : 0);
  return {
    ...r,
    midia: e.midia,
    legenda: e.legenda,
    leitura: [...e.leitura, ...e.marcas.filter((m) => !e.leitura.some((l) => l.rotulo === m)).map((m) => ({ rotulo: m, valor: "sim" }))],
    notas: Object.entries(e.notas).map(([k, v]) => ({ rotulo: base.rotulos_notas[k] ?? k, valor: v, mediana_top: med[k] ?? null })),
    elementos: e.elementos,
    criador: criador(r.foco, r.canal_id),
    parecidos: resumos(r.foco).filter((o) => o.id !== r.id).sort((a, b) => iguais(b) - iguais(a)).slice(0, 6),
    pct_intencao: e.pct_intencao,
    seguidores: null, duracao_s: e.duracao_s ?? null, concorre: r.vezes != null,
    metodo_leitura: r.plataforma === "youtube" ? "capa e texto (DeepSeek)" : r.tem_video ? "vídeo completo (Gemini)" : "imagens e legenda (Gemini)",
  };
}

function porque(r: T.PostResumo): string {
  const partes = [
    r.tipo_gancho && `Abre com gancho de ${r.tipo_gancho}`,
    r.tema && `fala de ${r.tema}`,
    r.vezes && `e rendeu ${fmtVezes(r.vezes)} o que se esperava de um perfil ${r.porte === "medio" ? "médio" : r.porte}`,
  ].filter(Boolean);
  return partes.join(", ") + ".";
}

function posts(p: Params): T.PaginaPosts {
  const f = focoDe(p);
  const todos = resumos(f);
  const q = String(p.q ?? "").toLowerCase();
  let xs = todos.filter(
    (r) =>
      (!p.plataforma || r.plataforma === p.plataforma) && (!p.formato || r.formato === p.formato) && (!p.tema || r.tema === p.tema) &&
      (!p.porte || r.porte === p.porte) && (!p.so_top || r.top) && (!p.com_video || r.tem_video) &&
      (!q || `${r.titulo} ${r.canal} ${r.gancho ?? ""}`.toLowerCase().includes(q)),
  );
  const chave: Record<string, (r: T.PostResumo) => number> = {
    vezes: (r) => r.vezes ?? -1, er: (r) => r.er ?? -1, comentarios: (r) => r.comentarios,
    recentes: (r) => Date.parse(r.publicado ?? "2000-01-01"),
    destaques: (r) => (r.top ? 1e6 - (r.posicao_top ?? 999) : r.vezes ?? 0),
  };
  const k = chave[String(p.ordem ?? "destaques")] ?? chave.destaques;
  xs = [...xs].sort((a, b) => k(b) - k(a));
  const offset = Number(p.offset ?? 0), limit = Number(p.limit ?? 24);
  return {
    total: xs.length,
    itens: xs.slice(offset, offset + limit),
    filtros: { plataformas: unicos(todos.map((r) => r.plataforma)), formatos: unicos(todos.map((r) => r.formato)), temas: unicos(todos.map((r) => r.tema)), portes: unicos(todos.map((r) => r.porte)) },
  };
}

function busca(p: Params): T.ResultadoBusca[] {
  const termos = String(p.q ?? "").toLowerCase().split(/\s+/).filter((t) => t.length > 2);
  if (!termos.length) return [];
  return itens(focoDe(p))
    .map((i) => {
      const texto = `${i.resumo.titulo} ${i.resumo.gancho ?? ""} ${i.resumo.tema ?? ""} ${i.extra.legenda} ${i.extra.elementos.join(" ")}`.toLowerCase();
      const casou = termos.filter((t) => texto.includes(t));
      return { post: i.resumo, score: casou.length / termos.length, casou };
    })
    .filter((r) => r.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, Number(p.limit ?? 20));
}

function criadores(p: Params): T.CriadorResumo[] {
  return Object.values(base.criadores[focoDe(p)])
    .map((c) => c.resumo)
    .filter((c) => (!p.plataforma || c.plataforma === p.plataforma) && (!p.porte || c.porte === p.porte))
    .sort((a, b) => (b.vezes ?? 0) - (a.vezes ?? 0));
}

function rankings(p: Params): T.ItemRanking[] {
  const metrica = String(p.metrica ?? "vezes");
  const limit = Number(p.limit ?? 10);
  const pct = (v: number) => `${(v * 100).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
  if (p.tipo === "criadores") {
    return criadores(p).slice(0, limit).map((c, i) => ({
      posicao: i + 1, id: c.id, nome: c.nome, sub: `${c.n_top} no top · ${c.n_posts} posts`, thumb: c.thumbs[0] ?? null,
      valor: c.vezes ?? 0, valor_fmt: fmtVezes(c.vezes),
    }));
  }
  const val = (r: T.PostResumo) => (metrica === "er" ? r.er ?? 0 : metrica === "comentarios" ? r.comentarios : r.vezes ?? 0);
  return posts({ ...p, limit: 999, ordem: metrica }).itens.slice(0, limit).map((r, i) => ({
    posicao: i + 1, id: r.id, nome: r.titulo, sub: r.canal, thumb: r.thumb, valor: val(r),
    valor_fmt: metrica === "er" ? pct(val(r)) : metrica === "comentarios" ? val(r).toLocaleString("pt-BR") : fmtVezes(val(r)),
  }));
}

function padroes(p: Params): T.RespostaPadroes {
  const f = focoDe(p);
  const todos = base.padroes[f];
  const plataformas = unicos(todos.map((x) => x.plataforma));
  const plat = String(p.plataforma ?? (plataformas.includes("todas") ? "todas" : plataformas[0]));
  return {
    plataformas, plataforma: plat,
    itens: todos.filter((x) => x.plataforma === plat).map(({ plataforma: _p, ...x }) => ({
      ...x,
      exemplos: itens(f).filter((i) => i.resumo.top && String(i.extra.rub[x.campo]) === (x.valor === "True" ? "true" : x.valor === "False" ? "false" : x.valor)).slice(0, 3).map((i) => i.resumo),
    })),
  };
}

function anatomia(id: string): T.VizAnatomia {
  const it = achar(id) ?? naoAchou("Post");
  const dur = it.extra.duracao_s ?? null;
  const d = dur ?? 30;
  const el = it.extra.elementos;
  const passo = (d - 3 - 4) / Math.max(el.length, 1);
  return {
    post: it.resumo,
    duracao_s: dur, nota: "Só o gancho tem janela definida. Os outros trechos têm posição aproximada.",
    trechos: [
      { rotulo: "Gancho", texto: it.resumo.gancho ?? "", inicio_s: 0, fim_s: 3, aproximado: false },
      ...el.map((texto, i) => ({ rotulo: `Elemento ${i + 1}`, texto, inicio_s: Math.round(3 + i * passo), fim_s: Math.round(3 + (i + 1) * passo), aproximado: true })),
      { rotulo: "Chamada para ação", texto: String(it.extra.rub.tipo_cta ?? "nenhuma"), inicio_s: Math.round(d - 4), fim_s: Math.round(d), aproximado: true },
    ],
  };
}

function comparar(p: Params): T.Comparacao {
  const a = detalhe(String(p.a)), b = detalhe(String(p.b));
  const mapa = (d: T.PostDetalhe) => new Map(d.leitura.map((l) => [l.rotulo, l.valor]));
  const ma = mapa(a), mb = mapa(b);
  const rotulos = [...new Set([...ma.keys(), ...mb.keys()])];
  return {
    a, b,
    diferencas: [
      { rotulo: "Formato do post", a: a.formato, b: b.formato, igual: a.formato === b.formato },
      ...rotulos.map((r) => ({ rotulo: r, a: ma.get(r) ?? "não", b: mb.get(r) ?? "não", igual: (ma.get(r) ?? "não") === (mb.get(r) ?? "não") })),
    ],
  };
}

const FOCOS: T.InfoFoco[] = [
  { id: "A", nome: "Impulso → empreendedor", pergunta: "O que faz um post engajar donos de pequeno negócio?", descricao: "Conteúdo de criadores e marcas que falam com quem tem um pequeno negócio: o público do Impulso.", base: base.focos.A },
  { id: "B", nome: "Negócio → cliente", pergunta: "Como o pequeno negócio engaja o próprio cliente?", descricao: "Posts de 28 negócios reais (alimentação, beleza, moda, pet) falando com o cliente final.", base: base.focos.B },
];

const ADS: T.Ad[] = [
  { criativo: "Post \"Empreendedor(a), queremos...\" (2ª veiculação)", formato: "post impulsionado", ctr: 8.82, desempenho: "alto", periodo: null, marcas: [], impressoes: null, engajamento: null, nota: null, confirma: [] },
  { criativo: "Post Segmentação Beleza", formato: "post (leads)", ctr: 8.62, desempenho: "alto", periodo: null, marcas: [], impressoes: null, engajamento: null, nota: null, confirma: [] },
  { criativo: "Post \"Empreendedor(a), queremos...\" (1ª veiculação)", formato: "post impulsionado", ctr: 8.23, desempenho: "alto", periodo: null, marcas: [], impressoes: null, engajamento: null, nota: null, confirma: [] },
];

const METODO: Omit<T.Metodo, "kappa"> = {
  limitacoes_md: "", metodologia_md: "", avaliacao_nota: null,
  passos: [
    { titulo: "Coletar", texto: "655 posts de 27 perfis no Instagram e 11.021 Shorts de 100 canais no YouTube, todos de quem fala com pequenos negócios." },
    { titulo: "Filtrar a base", texto: "Só entram canais aprovados na validação humana (14 excluídos), posts relevantes para pequenos negócios e voltados a donos de negócio." },
    { titulo: "Comparar com o esperado", texto: "Um modelo misto estima o engajamento esperado para o perfil, o formato e a idade do post. O que importa é quantas vezes o post passou disso." },
    { titulo: "Escolher o top", texto: "Top 10% por plataforma e porte, com no máximo 3 posts por criador, para um perfil só não dominar a lista." },
    { titulo: "Ler e comparar", texto: "Um modelo de visão lê cada post do top e de um grupo de controle com a mesma rubrica. Os padrões são o que aparece mais no top." },
  ],
  numeros: [
    { rotulo: "Posts no top do YouTube", valor: "203", nota: "de 76 criadores" },
    { rotulo: "Posts no top do Instagram", valor: "47", nota: "de 19 criadores" },
    { rotulo: "Canais fora do perfil no top do YouTube", valor: "4%", nota: "eram 56% com o ER puro" },
    { rotulo: "Maior criador no top do YouTube", valor: "1%", nota: "eram 14% com o ER puro" },
    { rotulo: "Expoente do engajamento por seguidor", valor: "0,37", nota: "o ER puro assume 1,0" },
  ],
  avaliacao_md:
    "## O viés de tamanho some\n\nA correlação do score com seguidores vai de **−0,49** (Instagram) e **−0,28** (YouTube) para perto de 0.\n\n## O que o modelo não faz\n\nO modelo misto não supera o outlier simples (post ÷ mediana do criador) em posts futuros. O ganho vem de comparar o post com o próprio criador, do limite por criador e do filtro da base.\n\n- Com o limite por criador, o top 10% equivale a 1,8% da base do YouTube e a 7,2% da do Instagram.",
  limitacoes: [
    "No YouTube, a maior parte da amostra nova foi vista por capa e texto, não em vídeo.",
    "A validação humana (kappa, 10 posts) é da amostra anterior.",
    "A relevância para pequenos negócios é rotulada pelo modelo, e ainda passam posts fora do tema.",
    "O Foco B cobre de 2 a 6 semanas por perfil e inclui a Black Friday.",
  ],
};

// ---------- estado em memória ----------
let seq = 1;
const novoId = (p: string) => `${p}-${Date.now().toString(36)}-${seq++}`;
const agora = () => new Date().toISOString();

const colecoes: T.Colecao[] = [
  { id: "col-1", nome: "Ganchos com número", nota: "Para a pauta de dezembro.", foco: "A", criada_em: "2026-11-22T14:10:00", posts: resumos("A").filter((r) => r.tipo_gancho === "número").slice(0, 4) },
  { id: "col-2", nome: "Carrosséis de finanças", nota: "", foco: "A", criada_em: "2026-11-23T09:30:00", posts: resumos("A").filter((r) => r.formato === "Carrossel").slice(0, 3) },
  { id: "col-3", nome: "Humor que vende", nota: "Referências para o salão.", foco: "B", criada_em: "2026-11-23T18:00:00", posts: resumos("B").slice(0, 3) },
];
const colecao = (id: string) => colecoes.find((c) => c.id === id) ?? naoAchou("Coleção");

function resultadoAvaliacao(f: T.Foco, plataforma: T.Plataforma): T.ResultadoAvaliacao {
  const ps = base.padroes[f].filter((x) => x.lift != null && x.lift !== 1).slice(0, 14);
  const top = resumos(f).filter((r) => r.top).slice(0, 4);
  return {
    id: "exemplo", thumb: null,
    foco: f, plataforma, metodo: "leitura por 6 quadros do vídeo, sem áudio", aviso: "",
    rubrica: itens(f)[0].extra.rub,
    nota: 60,
    nota_explicacao: "Começa em 50. Cada característica do seu post que aparece mais no top soma até 11 pontos; cada uma que aparece menos no top subtrai na mesma medida. Padrão visto em menos de 5 posts do top vale metade. A nota mostra o quanto o post se parece com o top da nossa base; não é promessa de resultado.",
    padroes: ps.map((x, i) => ({ campo: x.campo, valor: x.valor, rotulo: x.rotulo, tem: i % 3 === 0, lift: x.lift ?? 1, n_top: x.n_top, selo: x.selo, efeito: (x.lift ?? 1) > 1 ? "ajuda" : "atrapalha", fragil: x.fragil })),
    notas_vs_top: [
      { campo: "forca_hook_0a10", rotulo: "Força do gancho", valor: 6, mediana_top: 8 },
      { campo: "ritmo_cortes_0a10", rotulo: "Ritmo dos cortes", valor: 7, mediana_top: 3 },
      { campo: "clareza_mensagem_0a10", rotulo: "Clareza da mensagem", valor: 8, mediana_top: 8 },
      { campo: "generico_0a10", rotulo: "Quão genérico (menor é melhor)", valor: 3, mediana_top: 2 },
    ],
    parecidos: top.map((r) => ({ video_id: r.id, plataforma: r.plataforma, canal: r.canal, url: r.url, er: r.er ?? 0, resid: Math.log(r.vezes ?? 1), titulo: r.titulo, motivo: `Em comum: Tema: ${r.tema}; Gancho com ${r.tipo_gancho}`, post: r })),
    recomendacoes: [
      "O gancho está com nota 6 contra mediana 8 do top: mantenha a cena de abertura, mas coloque nos primeiros 3 segundos um texto na tela com a promessa do vídeo, porque gancho com promessa aparece 2,4 vezes mais no top que no grupo de controle (10 posts do top).",
      "O post termina sem chamada para ação e o top pede \"segue\" 2,5 vezes mais que o grupo de controle (8 posts do top): feche o vídeo pedindo para seguir, amarrado ao que a pessoa acabou de ver.",
      "Você publicou sem legenda, e legenda curta aparece só 0,72 vez no top para cada 1 vez no grupo de controle (6 posts do top): escreva uma legenda contando a cena principal.",
      "O tema finanças já é o que mais aproxima este post do top (4,3 vezes mais frequente, 9 posts): conduza o vídeo como relato do seu próprio fechamento de caixa.",
    ],
    medias: { top: 66, comuns: 54 },
  };
}

type Job<R> = { criado: number; etapas: string[]; resultado: R };
const jobsAvaliar = new Map<string, Job<T.ResultadoAvaliacao> & { salva: T.AvaliacaoSalva }>();
const jobsAgente = new Map<string, Job<T.RespostaAgente>>();
const ETAPAS_AVALIAR = ["Recebendo os arquivos", "Separando os quadros do vídeo", "Lendo o post com a rubrica", "Comparando com os padrões do top", "Procurando posts parecidos", "Escrevendo as recomendações"];
const ETAPAS_AGENTE = ["Entendendo o pedido", "Buscando os achados do recorte", "Escolhendo posts de referência", "Escrevendo a pauta", "Checando contra os dados"];
const PASSO_MS = 700;

function estado<R>(j: Job<R>): T.EstadoJob<R> {
  const n = Math.floor((Date.now() - j.criado) / PASSO_MS) + 1;
  const pronto = n > j.etapas.length;
  return { estado: pronto ? "pronto" : "rodando", etapas: j.etapas.slice(0, Math.min(n, j.etapas.length)), resultado: pronto ? j.resultado : null, erro: null };
}

const historico: T.AvaliacaoSalvaDetalhe[] = [
  { id: "av-2", criada_em: "2026-11-24T09:27:00", foco: "A", plataforma: "instagram", legenda: "", thumb: resumos("A").find((r) => r.plataforma === "instagram")?.thumb ?? null, nota: 60, estado: "pronto", resultado: resultadoAvaliacao("A", "instagram") },
  { id: "av-1", criada_em: "2026-11-23T21:02:00", foco: "B", plataforma: "instagram", legenda: "Fornada nova saindo agora. Quem vem?", thumb: resumos("B")[1]?.thumb ?? null, nota: 71, estado: "pronto", resultado: { ...resultadoAvaliacao("B", "instagram"), nota: 71 } },
];

const comRefs = ({ referencias_ids, ...r }: RespostaBruta): T.RespostaAgente => ({
  ...r,
  referencias: referencias_ids.map((id) => achar(id)?.resumo).filter((x): x is T.PostResumo => !!x),
});

// ---------- roteador ----------
export function responder(metodo: Metodo, caminho: string, p: Params, corpo: unknown): unknown {
  const f = focoDe(p);
  const [, r1, r2, r3] = caminho.split("/"); // "/posts/abc" → ["", "posts", "abc"]
  const c = (corpo ?? {}) as Record<string, unknown>;
  const rota = `${metodo} /${r1}`;

  switch (rota) {
    case "GET /saude": return { ok: true };
    case "GET /focos": return FOCOS;
    case "GET /posts": return r2 ? detalhe(r2) : posts(p);
    case "GET /destaques": return resumos(f).filter((r) => r.top).sort((a, b) => (b.vezes ?? 0) - (a.vezes ?? 0)).slice(0, Number(p.limit ?? 12)).map((post) => ({ post, porque: porque(post) }));
    case "GET /busca": return busca(p);
    case "GET /criadores": {
      if (!r2) return criadores(p);
      const cr = base.criadores[f][r2] ?? base.criadores[f === "A" ? "B" : "A"][r2] ?? naoAchou("Criador");
      return { ...cr, posts: [...base.posts.A, ...base.posts.B].map((i) => i.resumo).filter((r) => r.canal_id === r2) } satisfies T.CriadorDetalhe;
    }
    case "GET /rankings": return rankings(p);
    case "GET /comparar": return comparar(p);
    case "GET /padroes": return padroes(p);
    case "GET /ads": return ADS;
    case "GET /viz":
      if (r2 === "esperado-real") return { pontos: base.esperado_real[f], nota: "Amostra de exemplo. Eixos em escala logarítmica: curtidas + comentários esperados para o perfil × o que o post teve." } satisfies T.VizEsperadoReal;
      if (r2 === "temas") return base.temas[f];
      if (r2 === "anatomia") return anatomia(r3);
      if (r2 === "funil") return { ...base.funil, preco: { com: 0.59, sem: 0.09, n_com: 10, n_sem: 107 }, nota: null } satisfies T.VizFunil;
      break;
    case "POST /avaliar": {
      const id = novoId("av");
      const fd = corpo instanceof FormData ? corpo : new FormData();
      const foco = fd.get("foco") === "B" ? "B" : "A";
      const plataforma = fd.get("plataforma") === "youtube" ? "youtube" : "instagram";
      jobsAvaliar.set(id, {
        criado: Date.now(), etapas: ETAPAS_AVALIAR, resultado: resultadoAvaliacao(foco, plataforma),
        salva: { id, criada_em: agora(), foco, plataforma, legenda: String(fd.get("legenda") ?? ""), thumb: null, nota: 60, estado: "pronto" },
      });
      return { id };
    }
    case "GET /avaliar": {
      const j = jobsAvaliar.get(r2) ?? naoAchou("Avaliação");
      const e = estado(j);
      if (e.estado === "pronto" && !historico.some((h) => h.id === r2)) historico.unshift({ ...j.salva, resultado: j.resultado });
      return e;
    }
    case "GET /avaliacoes": return r2 ? historico.find((h) => h.id === r2) ?? naoAchou("Avaliação") : historico.map(({ resultado: _r, ...h }) => h);
    case "POST /agente": {
      const id = novoId("ag");
      const modelo = comRefs(base.criativos[seq % base.criativos.length]);
      jobsAgente.set(id, { criado: Date.now(), etapas: ETAPAS_AGENTE, resultado: { ...modelo, id, em: agora(), modo: (c.modo as T.ModoAgente) ?? "gerar_criativo", pergunta: String(c.pergunta ?? modelo.pergunta), segmento: (c.segmento as string) ?? null } });
      return { id };
    }
    case "GET /agente":
      if (r2 === "salvas") return [...[...jobsAgente.values()].filter((j) => estado(j).estado === "pronto").map((j) => j.resultado).reverse(), ...base.salvas.map(comRefs)];
      return estado(jobsAgente.get(r2) ?? naoAchou("Resposta"));
    case "GET /criativos": return base.criativos.map(comRefs);
    case "GET /colecoes": return r2 ? colecao(r2) : colecoes.filter((x) => x.foco === f);
    case "POST /colecoes": {
      if (!r2) {
        if (!String(c.nome ?? "").trim()) throw new ErroApi("Dê um nome para a coleção.", 400);
        const nova: T.Colecao = { id: novoId("col"), nome: String(c.nome).trim(), nota: String(c.nota ?? ""), foco: f, posts: [], criada_em: agora() };
        colecoes.unshift(nova);
        return nova;
      }
      const col = colecao(r2);
      const post = achar(String(c.post_id))?.resumo ?? naoAchou("Post");
      if (!col.posts.some((x) => x.id === post.id)) col.posts = [post, ...col.posts];
      return col;
    }
    case "PATCH /colecoes": {
      const col = colecao(r2);
      if (typeof c.nome === "string") col.nome = c.nome;
      if (typeof c.nota === "string") col.nota = c.nota;
      return col;
    }
    case "DELETE /colecoes": {
      const col = colecao(r2);
      if (r3 === "posts") {
        const id = String(c.post_id ?? p.post_id);
        col.posts = col.posts.filter((x) => x.id !== id);
        return col;
      }
      colecoes.splice(colecoes.indexOf(col), 1);
      return { ok: true };
    }
    case "GET /playbook":
      return {
        titulo: f === "A" ? base.playbook.titulo : "Playbook · Negócio → cliente",
        linha_fina: f === "A" ? "Padrões de conteúdo de alto engajamento para micro e pequenos empreendedores, cruzados com os Ads do Impulso." : "O que faz o cliente final reagir, comentar e pedir, em 28 negócios reais.",
        atualizado: f === "A" ? "2026-11-24" : "2026-11-24",
        leitura_min: 9,
        capitulos: base.playbook.capitulos, intro: "", titulo_original: null,
        comentarios: f === "B" ? base.funil.comentarios : undefined,
      } satisfies T.Playbook;
    case "GET /metodo": return { ...METODO, kappa: base.kappa } satisfies T.Metodo;
  }
  throw new ErroApi(`Rota de exemplo não encontrada: ${metodo} ${caminho}`, 404);
}
