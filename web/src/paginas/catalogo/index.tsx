// Catálogo (P1): todos os posts do foco em mosaico, com filtros na URL (o link é compartilhável), rolagem infinita
// e modo de seleção para comparar dois posts. O clique abre o <PainelPost> (o PostCard já cuida disso e da ficha de hover).
import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { usePosts, usePostsInfinito } from "../../api/hooks";
import type { FiltrosPosts, PostResumo } from "../../api/tipos";
import { Botao, Campo, Chip, Erro, Esqueleto, Miniatura, PostCard, Seletor, TituloPagina, Vazio } from "../../componentes";
import { fmtInt, nomePlataforma, nomePorte } from "../../util/formato";
import "./catalogo.css";

const ORDENS = [
  { valor: "destaques", rotulo: "Destaques primeiro" },
  { valor: "vezes", rotulo: "Mais vezes o esperado" },
  { valor: "er", rotulo: "Maior ER" },
  { valor: "comentarios", rotulo: "Mais comentários" },
  { valor: "recentes", rotulo: "Mais recentes" },
];
// parâmetros da URL que são filtros (o `post` do painel não entra aqui)
const CHAVES = ["q", "plataforma", "formato", "tema", "porte", "top", "video", "ordem"] as const;
type Chave = (typeof CHAVES)[number];

export default function Catalogo() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const v = (k: Chave) => params.get(k) ?? "";
  const mudar = (k: Chave, valor: string) =>
    setParams((p) => {
      const q = new URLSearchParams(p);
      if (valor) q.set(k, valor);
      else q.delete(k);
      return q;
    }, { replace: true });
  const limpar = () =>
    setParams((p) => {
      const q = new URLSearchParams(p);
      CHAVES.forEach((k) => q.delete(k));
      return q;
    }, { replace: true });

  // busca por texto: o campo responde na hora; a URL (e a consulta) só depois de 350 ms sem digitar
  const [texto, setTexto] = useState(v("q"));
  const qUrl = v("q");
  useEffect(() => setTexto(qUrl), [qUrl]);
  useEffect(() => {
    if (texto === qUrl) return;
    const t = window.setTimeout(() => mudar("q", texto.trim()), 350);
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [texto]);

  const filtros: FiltrosPosts = {
    q: qUrl || undefined, plataforma: v("plataforma") || undefined, formato: v("formato") || undefined, tema: v("tema") || undefined,
    porte: v("porte") || undefined, so_top: v("top") === "1" || params.get("so_top") === "1" || undefined, com_video: v("video") === "1" || undefined,
    ordem: (v("ordem") || undefined) as FiltrosPosts["ordem"],
  };
  const { data, isLoading, error, refetch, fetchNextPage, hasNextPage, isFetchingNextPage } = usePostsInfinito(filtros, 36);
  const { data: base } = usePosts({ limit: 1 }); // opções dos filtros e total da base, estáveis enquanto os filtros mudam
  const op = base?.filtros;
  const posts = data?.pages.flatMap((p) => p.itens) ?? [];
  const total = data?.pages[0]?.total;

  // filtros ligados, com o texto de cada um (para o estado vazio dizer o que afrouxar)
  const ROTULO: Partial<Record<Chave, (x: string) => string>> = {
    q: (x) => `texto “${x}”`, plataforma: nomePlataforma, formato: (x) => x, tema: (x) => `tema ${x}`,
    porte: (x) => `perfil ${nomePorte(x)}`, top: () => "só o top", video: () => "com vídeo",
  };
  const ligados = CHAVES.flatMap((k) => (v(k) && ROTULO[k] ? [{ k, texto: ROTULO[k]!(v(k)) }] : []));

  // rolagem infinita: sentinela no fim da grade (o botão "Carregar mais" fica de reserva)
  const sentinela = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = sentinela.current;
    if (!el || !hasNextPage || typeof IntersectionObserver === "undefined") return;
    const io = new IntersectionObserver((es) => es[0].isIntersecting && !isFetchingNextPage && fetchNextPage(), { rootMargin: "700px" });
    io.observe(el);
    return () => io.disconnect();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage, posts.length]);

  // modo comparar: o clique marca em vez de abrir o painel; com dois marcados, segue para /comparar
  const [comparando, setComparando] = useState(false);
  const [escolhidos, setEscolhidos] = useState<PostResumo[]>([]);
  const marcar = (p: PostResumo) =>
    setEscolhidos((e) => (e.some((x) => x.id === p.id) ? e.filter((x) => x.id !== p.id) : e.length < 2 ? [...e, p] : [e[0], p]));
  const sairDoComparar = () => { setComparando(false); setEscolhidos([]); };
  const [filtrosAbertos, setFiltrosAbertos] = useState(false); // só importa em tela estreita

  return (
    <>
      <TituloPagina
        titulo="Catálogo" grifo={base ? `${fmtInt(base.total)} posts` : undefined}
        sub="Os posts do top aparecem maiores. Passe o mouse para ver a ficha e clique para ver o post por dentro."
      />

      <div className={`nao-imprimir catalogo-barra${filtrosAbertos ? " catalogo-barra--aberta" : ""}`} role="search" aria-label="Filtros do catálogo">
        <div className="catalogo-linha1">
          <Campo className="catalogo-busca" rotulo="Buscar no catálogo" esconderRotulo type="search" placeholder="Buscar por texto no post" value={texto} onChange={(e) => setTexto(e.target.value)} />
          <button type="button" className="catalogo-abrir" aria-expanded={filtrosAbertos} onClick={() => setFiltrosAbertos(!filtrosAbertos)}>
            Filtros{ligados.length > 0 ? ` (${ligados.length})` : ""}
          </button>
          <p className="catalogo-conta" aria-live="polite">
            <b>{total == null ? "…" : fmtInt(total)}</b> {total === 1 ? "post" : "posts"}
          </p>
        </div>
        <div className="catalogo-filtros">
          {op && op.plataformas.length > 1 && (
            <Seletor rotulo="Plataforma" esconderRotulo valor={v("plataforma")} onChange={(x) => mudar("plataforma", x)} todos="Todas as plataformas"
              opcoes={op.plataformas.map((p) => ({ valor: p, rotulo: nomePlataforma(p) }))} />
          )}
          <Seletor rotulo="Formato" esconderRotulo valor={v("formato")} onChange={(x) => mudar("formato", x)} todos="Todos os formatos" opcoes={op?.formatos ?? []} />
          <Seletor rotulo="Tema" esconderRotulo valor={v("tema")} onChange={(x) => mudar("tema", x)} todos="Todos os temas" opcoes={op?.temas ?? []} />
          <Seletor rotulo="Tamanho do perfil" esconderRotulo valor={v("porte")} onChange={(x) => mudar("porte", x)} todos="Todo tamanho de perfil"
            opcoes={(op?.portes ?? []).map((p) => ({ valor: p, rotulo: `Perfil ${nomePorte(p)}` }))} />
          <Chip ativo={v("top") === "1"} onClick={() => mudar("top", v("top") ? "" : "1")}>Só o top</Chip>
          <Chip ativo={v("video") === "1"} onClick={() => mudar("video", v("video") ? "" : "1")}>Com vídeo</Chip>
          <Seletor className="catalogo-ordem" rotulo="Ordenar por" esconderRotulo valor={v("ordem") || "destaques"} onChange={(x) => mudar("ordem", x === "destaques" ? "" : x)} opcoes={ORDENS} />
          <span className="catalogo-acoes">
            {(ligados.length > 0 || v("ordem")) && <Botao variante="fantasma" tamanho="p" onClick={limpar}>Limpar filtros</Botao>}
            <Chip ativo={comparando} onClick={() => (comparando ? sairDoComparar() : setComparando(true))}>Comparar dois</Chip>
          </span>
        </div>
      </div>

      {isLoading && <Esqueleto tipo="cards" n={12} />}
      {error && <Erro erro={error} onTentar={refetch} />}

      {data && posts.length === 0 && (
        <Vazio
          titulo="Nenhum post com esses filtros"
          acao={
            <>
              {ligados.map((l) => <Botao key={l.k} variante="contorno" tamanho="p" onClick={() => mudar(l.k, "")}>Tirar {l.texto} ×</Botao>)}
              <Botao tamanho="p" onClick={limpar}>Limpar filtros</Botao>
            </>
          }
        >
          {ligados.length > 1
            ? `Os ${ligados.length} filtros juntos não deixam passar nenhum post. Tire um deles, começando pelo mais específico.`
            : qUrl
              ? "Nenhum post tem esse texto. Use uma palavra só, ou procure pela ideia na Busca."
              : "Esse filtro não deixa passar nenhum post neste foco. Tire o filtro para ver o catálogo todo."}
        </Vazio>
      )}

      {posts.length > 0 && (
        <div className={`mosaico${comparando ? " catalogo-comparando" : ""}`}>
          {posts.map((p, i) => {
            const pos = escolhidos.findIndex((x) => x.id === p.id);
            return (
              <PostCard
                key={p.id} post={p} destaque={p.top && i % 9 === 0}
                onAbrir={comparando ? marcar : undefined} semFicha={comparando}
                selecionado={comparando ? pos >= 0 : undefined} marca={pos === 0 ? "A" : "B"}
              />
            );
          })}
        </div>
      )}

      {posts.length > 0 && (
        <div className="catalogo-fim" ref={sentinela}>
          <p className="t-sec t-pequeno">Mostrando {fmtInt(posts.length)} de {fmtInt(total)}</p>
          {hasNextPage
            ? <Botao variante="contorno" ocupado={isFetchingNextPage} onClick={() => fetchNextPage()}>Carregar mais</Botao>
            : <p className="t-sec t-pequeno">Você chegou ao fim.</p>}
        </div>
      )}

      {comparando && (
        <div className="catalogo-bandeja" role="region" aria-label="Comparar dois posts">
          <div className="catalogo-bandeja-vagas">
            {[0, 1].map((i) => (
              <span key={i} className={`catalogo-vaga${escolhidos[i] ? " catalogo-vaga--cheia" : ""}`}>
                {escolhidos[i] ? <Miniatura src={escolhidos[i].thumb} alt={`Escolhido ${i === 0 ? "A" : "B"}: post de ${escolhidos[i].canal}`} reserva={i === 0 ? "A" : "B"} /> : <span aria-hidden>{i === 0 ? "A" : "B"}</span>}
              </span>
            ))}
          </div>
          <p className="catalogo-bandeja-texto" aria-live="polite">
            {escolhidos.length === 0 && "Clique em dois posts."}
            {escolhidos.length === 1 && "Falta um post."}
            {escolhidos.length === 2 && "Dois escolhidos."}
          </p>
          <Botao variante="lima" disabled={escolhidos.length < 2}
            onClick={() => navigate(`/comparar?a=${encodeURIComponent(escolhidos[0].id)}&b=${encodeURIComponent(escolhidos[1].id)}`)}>
            Comparar →
          </Botao>
          <button type="button" className="catalogo-bandeja-sair" onClick={sairDoComparar}>Cancelar</button>
        </div>
      )}
    </>
  );
}
