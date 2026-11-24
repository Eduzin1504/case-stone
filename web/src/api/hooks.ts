// Um hook por rota do contrato. O foco atual entra sozinho em toda chamada (?foco=A|B) e na chave do cache.
// Consultas devolvem o objeto do react-query: { data, isLoading, isError, error, refetch }.
//   const { data, isLoading, error } = usePosts({ so_top: true, limit: 24 });
//   if (isLoading) return <Esqueleto />;  if (error) return <Erro erro={error} />;
// Mutações devolvem { mutate, mutateAsync, isPending, error } e já invalidam as listas afetadas.
import { keepPreviousData, useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Params } from "./cliente";
import { useFoco } from "../contexto/Foco";
import type * as T from "./tipos";

/** Hook genérico para qualquer GET: useApi<Tipo>("/rota", { parametros }, ligado?). */
export function useApi<R>(caminho: string, params: Params = {}, ligado = true) {
  const { foco } = useFoco();
  const p = { foco, ...params };
  return useQuery({ queryKey: [caminho, p], queryFn: () => api.get<R>(caminho, p), enabled: ligado });
}

// ---------- posts ----------
/** GET /posts. Mantém a página anterior na tela enquanto o filtro novo carrega. */
export function usePosts(filtros: T.FiltrosPosts = {}) {
  const { foco } = useFoco();
  const p = { foco, ...filtros };
  return useQuery({ queryKey: ["/posts", p], queryFn: () => api.get<T.PaginaPosts>("/posts", p), placeholderData: keepPreviousData });
}
/** GET /posts paginado ("carregar mais"): data.pages[].itens; fetchNextPage(); hasNextPage. */
export function usePostsInfinito(filtros: Omit<T.FiltrosPosts, "offset"> = {}, porPagina = 24) {
  const { foco } = useFoco();
  const p = { foco, ...filtros, limit: porPagina };
  return useInfiniteQuery({
    queryKey: ["/posts", "infinito", p],
    queryFn: ({ pageParam }) => api.get<T.PaginaPosts>("/posts", { ...p, offset: pageParam }),
    initialPageParam: 0,
    getNextPageParam: (ultima, todas) => {
      const vistos = todas.reduce((n, pg) => n + pg.itens.length, 0);
      return vistos < ultima.total ? vistos : undefined;
    },
  });
}
/** GET /posts/{id}. Passe null/undefined para não buscar. */
export const usePost = (id: string | null | undefined) => useApi<T.PostDetalhe>(`/posts/${id}`, {}, !!id);
/** GET /destaques. */
export const useDestaques = (limit = 12) => useApi<T.Destaque[]>("/destaques", { limit });
/** GET /busca. Só busca com 2+ caracteres. */
export const useBusca = (q: string, limit = 24, so_top = false) =>
  useApi<T.ResultadoBusca[]>("/busca", { q: q.trim(), limit, so_top: so_top || undefined }, q.trim().length >= 2);

// ---------- criadores, rankings, comparação ----------
export const useCriadores = (filtros: T.FiltrosCriadores = {}) => useApi<T.CriadorResumo[]>("/criadores", filtros);
export const useCriador = (id: string | null | undefined) => useApi<T.CriadorDetalhe>(`/criadores/${id}`, {}, !!id);
/** GET /rankings. Mantém a lista anterior enquanto a nova carrega (a corrida de barras reordena sem piscar). */
export function useRankings(params: T.ParamsRanking) {
  const { foco } = useFoco();
  const p = { foco, ...params };
  return useQuery({ queryKey: ["/rankings", p], queryFn: () => api.get<T.ItemRanking[]>("/rankings", p), placeholderData: keepPreviousData });
}
export const useComparar = (a: string | null | undefined, b: string | null | undefined) => useApi<T.Comparacao>("/comparar", { a, b }, !!a && !!b);

// ---------- padrões, ads, visualizações ----------
export const usePadroes = (plataforma?: string) => useApi<T.RespostaPadroes>("/padroes", { plataforma });
/** GET /ads (só existe no Foco A; no B a consulta fica desligada). */
export function useAds() {
  const { foco } = useFoco();
  return useQuery({ queryKey: ["/ads"], queryFn: () => api.get<T.Ad[]>("/ads"), enabled: foco === "A" });
}
export const useEsperadoReal = (plataforma?: string) => useApi<T.VizEsperadoReal>("/viz/esperado-real", { plataforma });
export const useTemas = (plataforma?: string) => useApi<T.VizTema[]>("/viz/temas", { plataforma });
export const useAnatomia = (id: string | null | undefined) => useApi<T.VizAnatomia>(`/viz/anatomia/${id}`, {}, !!id);
/** GET /viz/funil (só Foco B; no A fica desligada). */
export function useFunil() {
  const { foco } = useFoco();
  return useQuery({ queryKey: ["/viz/funil"], queryFn: () => api.get<T.VizFunil>("/viz/funil", { foco: "B" }), enabled: foco === "B" });
}

// ---------- avaliar meu post ----------
const INTERVALO_JOB = 1000;
/** POST /avaliar (multipart). mutateAsync({ arquivos, legenda, plataforma }) → { id }; acompanhe com useAvaliacao(id). */
export function useEnviarAvaliacao() {
  const { foco } = useFoco();
  return useMutation({
    mutationFn: (e: T.EnvioAvaliacao) => {
      const fd = new FormData();
      e.arquivos.forEach((a) => fd.append("arquivos", a));
      fd.append("legenda", e.legenda ?? "");
      fd.append("foco", foco);
      fd.append("plataforma", e.plataforma);
      fd.append("usar_video", String(e.usar_video ?? true));
      if (e.link) fd.append("link", e.link);
      return api.post<T.IdJob>("/avaliar", fd);
    },
  });
}
/** GET /avaliar/{id}. Consulta de novo a cada segundo enquanto estado = "rodando"; data.etapas narra o progresso. */
export function useAvaliacao(id: string | null | undefined) {
  const qc = useQueryClient();
  return useQuery({
    queryKey: ["/avaliar", id],
    queryFn: async () => {
      const r = await api.get<T.EstadoJob<T.ResultadoAvaliacao>>(`/avaliar/${id}`);
      if (r.estado !== "rodando") qc.invalidateQueries({ queryKey: ["/avaliacoes"] });
      return r;
    },
    enabled: !!id,
    refetchInterval: (q) => (q.state.data?.estado === "rodando" ? INTERVALO_JOB : false),
  });
}
/** GET /avaliacoes: histórico (todas, dos dois focos). */
export const useAvaliacoes = () => useQuery({ queryKey: ["/avaliacoes"], queryFn: () => api.get<T.AvaliacaoSalva[]>("/avaliacoes") });
export const useAvaliacaoSalva = (id: string | null | undefined) =>
  useQuery({ queryKey: ["/avaliacoes", id], queryFn: () => api.get<T.AvaliacaoSalvaDetalhe>(`/avaliacoes/${id}`), enabled: !!id });

// ---------- agente ----------
/** POST /agente. mutateAsync({ modo, pergunta, segmento, filtros }) → { id }; acompanhe com useAgente(id). */
export function usePerguntarAgente() {
  const { foco } = useFoco();
  return useMutation({ mutationFn: (p: T.PedidoAgente) => api.post<T.IdJob>("/agente", p, { foco }) });
}
/** GET /agente/{id}, repetindo enquanto roda. */
export function useAgente(id: string | null | undefined) {
  const qc = useQueryClient();
  return useQuery({
    queryKey: ["/agente", id],
    queryFn: async () => {
      const r = await api.get<T.EstadoJob<T.RespostaAgente>>(`/agente/${id}`);
      if (r.estado !== "rodando") qc.invalidateQueries({ queryKey: ["/agente/salvas"] });
      return r;
    },
    enabled: !!id,
    refetchInterval: (q) => (q.state.data?.estado === "rodando" ? INTERVALO_JOB : false),
  });
}
/** POST /criativos/video: gera o Reels do criativo pela Feita. mutateAsync(criativo) → { id }. */
export const useGerarVideo = () => useMutation({ mutationFn: (criativo: T.Criativo) => api.post<T.IdJob>("/criativos/video", { criativo }) });
/** GET /criativos/video/{id}, repetindo enquanto roda. */
export const useVideoCriativo = (id: string | null | undefined) =>
  useQuery({
    queryKey: ["/criativos/video", id],
    queryFn: () => api.get<T.EstadoJob<{ url: string }>>(`/criativos/video/${id}`),
    enabled: !!id,
    refetchInterval: (q) => (q.state.data?.estado === "rodando" ? INTERVALO_JOB : false),
  });
/** GET /agente/opcoes: segmentos e pilares aceitos como filtro. */
export const useOpcoesAgente = () => useQuery({ queryKey: ["/agente/opcoes"], queryFn: () => api.get<T.OpcoesAgente>("/agente/opcoes"), staleTime: Infinity });
export const useAgenteSalvas = () => useApi<T.RespostaAgente[]>("/agente/salvas");
export const useCriativos = () => useApi<T.RespostaAgente[]>("/criativos");

// ---------- coleções ----------
export const useColecoes = () => useApi<T.Colecao[]>("/colecoes");
export const useColecao = (id: string | null | undefined) => useApi<T.Colecao>(`/colecoes/${id}`, {}, !!id);

function useMutacaoColecao<V, R>(fn: (v: V, foco: T.Foco) => Promise<R>) {
  const qc = useQueryClient();
  const { foco } = useFoco();
  return useMutation({
    mutationFn: (v: V) => fn(v, foco),
    onSuccess: () => qc.invalidateQueries({ predicate: (q) => String(q.queryKey[0]).startsWith("/colecoes") }),
  });
}
/** POST /colecoes { nome, nota } → Colecao */
export const useCriarColecao = () => useMutacaoColecao((v: T.NovaColecao, foco) => api.post<T.Colecao>("/colecoes", v, { foco }));
/** PATCH /colecoes/{id} { nome?, nota? } → Colecao */
export const useEditarColecao = () => useMutacaoColecao((v: { id: string; nome?: string; nota?: string }) => api.patch<T.Colecao>(`/colecoes/${v.id}`, { nome: v.nome, nota: v.nota }));
/** DELETE /colecoes/{id} */
export const useApagarColecao = () => useMutacaoColecao((id: string) => api.delete<{ ok: boolean }>(`/colecoes/${id}`));
/** POST /colecoes/{id}/posts { post_id } → Colecao */
export const useAdicionarPost = () => useMutacaoColecao((v: { colecao: string; post: string }) => api.post<T.Colecao>(`/colecoes/${v.colecao}/posts`, { post_id: v.post }));
/** DELETE /colecoes/{id}/posts?post_id= → Colecao */
export const useRemoverPost = () => useMutacaoColecao((v: { colecao: string; post: string }) => api.delete<T.Colecao>(`/colecoes/${v.colecao}/posts`, { post_id: v.post }));

// ---------- playbook, método, saúde ----------
export const usePlaybook = () => useApi<T.Playbook>("/playbook");
export const useMetodo = () => useApi<T.Metodo>("/metodo");
export const useSaude = () => useQuery({ queryKey: ["/saude"], queryFn: () => api.get<T.Saude>("/saude"), retry: false });
