// Tipos do contrato da API (prefixo /api). A API segue este arquivo.
// Conferido com a API na integração (24/11), incluindo os campos de api/CONTRATO_DESVIOS.md.
// Convenções: `er` e toda frequência/percentual são FRAÇÕES (4.37 = 437%; 0.25 = 25%); formate com fmtPct.
// `vezes` é "vezes o esperado" (5677 = 5,7 mil×) — formate com fmtVezes. Datas em ISO (AAAA-MM-DD).

export type Foco = "A" | "B";
export type Plataforma = "instagram" | "youtube";
export type Porte = "micro" | "medio" | "grande" | string;

// ---------- posts ----------
export type PostResumo = {
  id: string; foco: Foco; plataforma: Plataforma;
  formato: string; // "Reels" | "Carrossel" | "Imagem" | "Short"
  canal: string; canal_id: string; titulo: string; thumb: string | null; tem_video: boolean;
  er: number | null;
  vezes: number | null; // vezes o esperado; null se não concorre
  top: boolean; posicao_top: number | null; likes: number; comentarios: number; views: number | null;
  publicado: string | null; gancho: string | null; tema: string | null; tipo_gancho: string | null; porte: string | null; url: string;
};

export type Midia = {
  tipo: "youtube" | "video" | "imagens" | "capa" | "nenhuma";
  youtube_id?: string; video_url?: string; imagens?: string[];
};

export type Leitura = { rotulo: string; valor: string };
export type Nota = { rotulo: string; valor: number; mediana_top: number | null }; // escala 0 a 10

export type PostDetalhe = PostResumo & {
  midia: Midia; legenda: string; leitura: Leitura[]; notas: Nota[]; elementos: string[];
  criador: CriadorResumo | null; parecidos: PostResumo[];
  pct_intencao: number | null; // só Foco B: fração de comentários com intenção de compra
  seguidores: number | null; duracao_s: number | null; concorre: boolean;
  metodo_leitura: string | null; // "vídeo completo, com áudio" | "imagens do post" | "só a capa"
};

export type FiltrosPosts = {
  plataforma?: string; formato?: string; tema?: string; porte?: string;
  so_top?: boolean; com_video?: boolean; q?: string;
  ordem?: "destaques" | "vezes" | "er" | "comentarios" | "recentes";
  offset?: number; limit?: number;
};
export type OpcoesFiltros = { plataformas: string[]; formatos: string[]; temas: string[]; portes: string[] };
export type PaginaPosts = { total: number; itens: PostResumo[]; filtros: OpcoesFiltros };

export type Destaque = { post: PostResumo; porque: string };
export type ResultadoBusca = { post: PostResumo; score: number; casou: string[] };

// ---------- focos ----------
export type BaseFoco = { posts: number; criadores: number; top: number; por_plataforma: { instagram: number; youtube: number }; coletado_em: string | null };
export type InfoFoco = { id: Foco; nome: string; descricao: string; pergunta: string; base: BaseFoco };

// ---------- criadores ----------
export type CriadorResumo = {
  id: string; foco: Foco; nome: string; plataforma: string; seguidores: number; porte: string;
  vezes: number | null; n_top: number; n_posts: number; tema: string | null; formato: string | null; thumbs: string[]; url: string;
  er_mediano: number | null; comentarios: number;
};
export type PontoSerie = { id: string; data: string; er: number | null; vezes: number | null; top: boolean };
export type CriadorDetalhe = { resumo: CriadorResumo; bio: string; posts: PostResumo[]; serie: PontoSerie[] };
export type FiltrosCriadores = { plataforma?: string; porte?: string };

// ---------- rankings e comparação ----------
export type ParamsRanking = { tipo: "posts" | "criadores"; plataforma?: string; porte?: string; metrica?: "vezes" | "er" | "comentarios"; limit?: number };
export type ItemRanking = {
  posicao: number; id: string; nome: string; sub: string; thumb: string | null; valor: number; valor_fmt: string;
  thumbs?: string[]; // só em tipo=criadores: até 3 capas
};
export type Diferenca = { rotulo: string; a: string; b: string; igual: boolean };
export type Comparacao = { a: PostDetalhe; b: PostDetalhe; diferencas: Diferenca[] };

// ---------- padrões e ads ----------
export type TipoSelo = "confirmado" | "contradito" | "só mercado" | "inconclusivo" | string;
export type Padrao = {
  campo: string; valor: string; rotulo: string; grupo: string;
  freq_top: number; freq_controle: number; lift: number | null; n_top: number;
  selo: TipoSelo | null; fragil: boolean; exemplos: PostResumo[];
  confianca: string | null; // "alta" | "média" | "baixa" | "não validado" | "dado objetivo"
};
export type RespostaPadroes = { plataformas: string[]; itens: Padrao[]; plataforma: string /* a que foi usada (sem parâmetro, a API escolhe) */ };
export type Ad = {
  criativo: string; formato: string | null; ctr: number; desempenho: string | null; // ctr em % (8.82 = 8,82%)
  periodo: string | null; marcas: string[]; impressoes: number | null; engajamento: number | null; nota: string | null;
  confirma: string[]; // rótulos (iguais a Padrao.rotulo) dos padrões "confirmado" que o criativo tem
};

// ---------- visualizações ----------
export type PontoEsperadoReal = { id: string; canal: string; esperado: number; real: number; top: boolean; plataforma: string };
export type VizEsperadoReal = { pontos: PontoEsperadoReal[]; nota: string };
export type VizTema = { tema: string; n_top: number; n_controle: number; pct_top: number; lift: number | null; pct_controle: number };
// inicio_s/fim_s são null em post sem duração (imagem, carrossel); `itens` só vem no trecho dos elementos
export type TrechoAnatomia = { rotulo: string; texto: string; inicio_s: number | null; fim_s: number | null; aproximado: boolean; itens?: string[] };
export type VizAnatomia = { post: PostResumo; duracao_s: number | null; trechos: TrechoAnatomia[]; nota: string };
export type VizFunil = {
  etapas: { rotulo: string; valor: number }[];
  por_formato: { formato: string; pct_intencao: number; n: number }[];
  preco: { com: number | null; sem: number | null; n_com: number; n_sem: number };
  comentarios: { texto: string; negocio: string; segmento: string }[];
  nota: string | null;
};

// ---------- jobs (avaliar e agente rodam em segundo plano) ----------
export type EstadoJob<T> = { estado: "rodando" | "pronto" | "erro"; etapas: string[]; resultado: T | null; erro: string | null };
export type IdJob = { id: string };

// ---------- avaliar meu post ----------
export type PadraoCasado = {
  campo: string; valor: string; rotulo: string; tem: boolean; lift: number; n_top: number;
  selo: TipoSelo | null; efeito: "ajuda" | "atrapalha"; fragil: boolean;
};
export type NotaVsTop = { campo: string; rotulo: string; valor: number; mediana_top: number };
export type ParecidoAvaliacao = {
  video_id: string; plataforma: Plataforma; canal: string; url: string; er: number; resid: number; titulo: string; motivo: string;
  post?: PostResumo | null; // quando a API conseguir montar o resumo (para usar PostCard)
};
export type ResultadoAvaliacao = {
  foco: Foco; plataforma: Plataforma; metodo: string; aviso: string;
  rubrica: Record<string, unknown>;
  nota: number; // 0 a 100
  nota_explicacao: string;
  padroes: PadraoCasado[]; notas_vs_top: NotaVsTop[]; parecidos: ParecidoAvaliacao[]; recomendacoes: string[];
  medias: { top: number | null; comuns: number | null };
  id: string; thumb: string | null; // o mesmo id do histórico; miniatura do que foi enviado
};
export type EnvioAvaliacao = { arquivos: File[]; legenda?: string; plataforma: Plataforma; usar_video?: boolean; link?: string };
export type AvaliacaoSalva = {
  id: string; criada_em: string; foco: Foco; plataforma: Plataforma; legenda: string;
  thumb: string | null; nota: number | null; estado: "rodando" | "pronto" | "erro"; metodo?: string;
};
export type AvaliacaoSalvaDetalhe = AvaliacaoSalva & { resultado: ResultadoAvaliacao | null };

// ---------- agente (criar pauta) ----------
export type ModoAgente = "analisar" | "recomendar" | "gerar_criativo";
export type FiltrosAgente = { porte?: string | null; plataforma?: string | null; pilar?: string | null; periodo_dias?: number | null; tema?: string | null; formato?: string | null };
export type PedidoAgente = { modo: ModoAgente; pergunta: string; segmento?: string | null; filtros?: FiltrosAgente };
export type Cena = { n: number; tempo: string | null; texto: string; rotulo: string | null }; // tempo: "0-3s", "Slide 2"…; rotulo: "capa", "GANCHO"…
export type Criativo = { formato: string; pilar: string; gancho: string; roteiro: string; legenda: string; cta: string; inspirado_em: string[]; cenas: Cena[] };
export type Achado = { selo: TipoSelo | null; campo: string; valor: string; rotulo: string; freq_top: number; freq_controle: number; lift: number | null; n_top: number; fragil: boolean };
export type OpcoesAgente = { segmentos: string[]; pilares: string[] };
export type RespostaAgente = {
  id: string; em: string; modo: ModoAgente; pergunta: string; segmento: string | null;
  achados: Achado[]; referencias: PostResumo[]; criativos: Criativo[];
  explicacao: string; // markdown
  baixa_confianca: boolean; filtros_relaxados: string[];
  tentativas: number | null; pendencias: string;
};

// ---------- coleções ----------
export type Colecao = { id: string; nome: string; nota: string; foco: Foco; posts: PostResumo[]; criada_em: string };
export type NovaColecao = { nome: string; nota?: string };

// ---------- playbook e método ----------
export type Capitulo = { id: string; titulo: string; markdown: string; rotulo: string; titulo_original: string };
export type Playbook = { titulo: string; linha_fina: string; atualizado: string | null; leitura_min: number; capitulos: Capitulo[]; comentarios?: { texto: string; negocio: string; segmento: string }[]; intro: string; titulo_original: string | null };
export type Metodo = {
  passos: { titulo: string; texto: string }[];
  numeros: { rotulo: string; valor: string; nota?: string; plataforma?: string }[];
  avaliacao_md: string;
  limitacoes: string[];
  kappa: { campo: string; concordancia: number; kappa: number; rotulo: string; n: number | null }[]; // mostre `rotulo`
  limitacoes_md: string; metodologia_md: string; avaliacao_nota: string | null;
};
export type Saude = { ok: boolean };
