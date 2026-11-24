// Peças locais do playbook: leitura do markdown, montagem preguiçosa, post tocável com embed sob demanda, notas.
import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { useApi } from "../../api/hooks";
import type { Foco, Plataforma, PostDetalhe, PostResumo } from "../../api/tipos";
import { Esqueleto, Markdown, Midia, MolduraCelular, PostCard, useAbrirPost } from "../../componentes";
import { fmtPct, fmtVezes, nomePlataforma } from "../../util/formato";
import { REVELAR } from "../../util/useEntrou";

// ---------- markdown ----------
const ehTabela = (l: string) => /^\s*\|/.test(l);
const ehItem = (l: string) => /^\s*(?:[-*]|\d+\.)\s+/.test(l);

/** Separa o texto corrido das tabelas (que não aparecem como tabela: vão para "ver os números"). */
export function separar(md: string) {
  const linhas = md.replace(/\r/g, "").split("\n");
  return {
    texto: linhas.filter((l) => !ehTabela(l)).join("\n").trim(),
    tabelas: linhas.map((l) => (ehTabela(l) ? l : "")).join("\n").replace(/\n{3,}/g, "\n\n").trim(),
  };
}
/** Itens de lista (- ou 1.), sem o marcador. */
export const itens = (md: string) => md.split("\n").filter(ehItem).map((l) => l.replace(/^\s*(?:[-*]|\d+\.)\s+/, "").trim());
/** Parágrafos de prosa (sem tabelas nem listas). */
export const paragrafos = (md: string) =>
  separar(md).texto.split(/\n\s*\n/).map((b) => b.trim()).filter((b) => b && !b.split("\n").every(ehItem));

export type Ligacao = { id: string; plataforma: Plataforma; url: string };
/** Posts citados por link no texto (Instagram e YouTube). */
export function idsDosLinks(txt: string): Ligacao[] {
  const re = /https?:\/\/(?:www\.)?(?:instagram\.com\/(?:p|reel)\/([\w-]+)\/?|youtube\.com\/shorts\/([\w-]+)|youtu\.be\/([\w-]+))/g;
  const out: Ligacao[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(txt))) {
    const id = m[1] ?? m[2] ?? m[3];
    if (!out.some((x) => x.id === id)) out.push({ id, plataforma: m[1] ? "instagram" : "youtube", url: m[0] });
  }
  return out;
}

// ---------- montagem preguiçosa: o texto fica; a mídia só monta perto da tela (ou ao imprimir/exportar) ----------
export function Preguica({ children, altura = 420 }: { children: ReactNode; altura?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [perto, setPerto] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (perto || !el) return;
    const mostrar = () => setPerto(true);
    if (typeof IntersectionObserver === "undefined") return mostrar();
    const io = new IntersectionObserver((es) => es.some((e) => e.isIntersecting) && mostrar(), { rootMargin: "700px 0px" });
    io.observe(el);
    window.addEventListener(REVELAR, mostrar);
    window.addEventListener("beforeprint", mostrar);
    return () => {
      io.disconnect();
      window.removeEventListener(REVELAR, mostrar);
      window.removeEventListener("beforeprint", mostrar);
    };
  }, [perto]);
  if (perto) return <>{children}</>;
  return <div ref={ref} style={{ minHeight: altura }}><Esqueleto altura={altura} /></div>;
}

// ---------- embed oficial do Instagram, só no clique, no máximo 6 por página ----------
const MAX_EMBEDS = 6;
const Limite = createContext<{ usados: number; usar: () => void }>({ usados: 0, usar: () => {} });

export function LimiteEmbeds({ children }: { children: ReactNode }) {
  const [usados, setUsados] = useState(0);
  return <Limite.Provider value={{ usados, usar: () => setUsados((n) => n + 1) }}>{children}</Limite.Provider>;
}

function EmbedInstagram({ id, url }: { id: string; url: string }) {
  const { usados, usar } = useContext(Limite);
  const [aberto, setAberto] = useState(false);
  const [estado, setEstado] = useState<"carregando" | "ok" | "falhou">("carregando");
  useEffect(() => {
    if (!aberto || estado !== "carregando") return;
    const t = window.setTimeout(() => setEstado("falhou"), 12000); // o iframe de fora não avisa erro: sem resposta em 12 s, mostra a saída
    return () => window.clearTimeout(t);
  }, [aberto, estado]);

  const fora = <a href={url} target="_blank" rel="noreferrer">Abrir no Instagram ↗</a>;
  if (!aberto)
    return (
      <p className="playbook-original nao-imprimir">
        <span>Ver o post original no Instagram</span>
        {usados >= MAX_EMBEDS
          ? <span className="t-sec">Limite de {MAX_EMBEDS} posts carregados nesta página. {fora}</span>
          : <button type="button" className="playbook-botao-linha" onClick={() => { usar(); setAberto(true); }}>Carregar do Instagram</button>}
      </p>
    );
  return (
    <div className="playbook-embed nao-imprimir">
      {estado === "falhou"
        ? <p className="playbook-embed-aviso">O Instagram não respondeu. {fora}</p>
        : <iframe src={`https://www.instagram.com/p/${id}/embed`} title="Post original no Instagram" loading="lazy" onLoad={() => setEstado("ok")} />}
      {estado === "carregando" && <p className="t-pequeno t-sec" role="status">Carregando do Instagram…</p>}
      {estado === "ok" && <p className="t-pequeno t-sec">Não apareceu? {fora}</p>}
    </div>
  );
}

// ---------- post tocável: a mídia na moldura de celular, com crédito e ações ----------
type PropsTocavel = {
  id: string; plataforma: Plataforma; url?: string; resumo?: PostResumo; largura?: number;
  foco?: Foco;       // quando o post vem da base do outro foco (estudos de caso)
};

export function PostTocavel({ id, plataforma, url, resumo, largura = 200, foco }: PropsTocavel) {
  const abrir = useAbrirPost();
  const { data, isLoading } = useApi<PostDetalhe>(`/posts/${id}`, foco ? { foco } : {});
  const p: PostResumo | undefined = data ?? resumo;
  const yt = plataforma === "youtube";
  const thumb = p?.thumb ?? (yt ? `https://i.ytimg.com/vi/${id}/hqdefault.jpg` : null);
  const titulo = p?.gancho || p?.titulo || `Post no ${nomePlataforma(plataforma)}`;
  const link = p?.url ?? url ?? (yt ? `https://www.youtube.com/shorts/${id}` : `https://www.instagram.com/p/${id}/`);
  const midia = yt ? { tipo: "youtube" as const, youtube_id: id } : data?.midia ?? { tipo: "capa" as const };

  return (
    <figure className="playbook-tocavel">
      <MolduraCelular largura={largura}>
        {!yt && isLoading && !thumb
          ? <Esqueleto altura="100%" />
          : <Midia midia={midia} thumb={thumb} titulo={titulo} url={link} plataforma={plataforma} />}
      </MolduraCelular>
      {thumb && <img className="playbook-capa-impressa" src={thumb} alt={titulo} loading="lazy" />}
      <figcaption>
        {p && <span className="playbook-tocavel-titulo corta-2">{titulo}</span>}
        <span className="t-mono playbook-credito">
          {[p?.canal?.split("|")[0].trim(), p?.er != null && `ER ${fmtPct(p.er)}`, p?.vezes != null && `${fmtVezes(p.vezes)} o esperado`].filter(Boolean).join(" · ") || nomePlataforma(plataforma)}
        </span>
        <span className="playbook-acoes nao-imprimir">
          {!foco && p && <button type="button" className="playbook-botao-linha" onClick={() => abrir(id)}>Ver a leitura deste post →</button>}
          {yt && <a href={link} target="_blank" rel="noreferrer">Abrir no YouTube ↗</a>}
        </span>
        {!yt && <EmbedInstagram id={id} url={link} />}
      </figcaption>
    </figure>
  );
}

/** Card compacto de um post conhecido só pelo id (citado por link no texto). Some se o post não está na base. */
function PostPorId({ id }: { id: string }) {
  const { data } = useApi<PostDetalhe>(`/posts/${id}`);
  return data ? <PostCard post={data} variante="compacto" /> : null;
}

export function Minis({ posts = [], ids = [] }: { posts?: PostResumo[]; ids?: string[] }) {
  if (!posts.length && !ids.length) return null;
  return (
    <div className="playbook-minis">
      {posts.map((p) => <PostCard key={p.id} post={p} variante="compacto" />)}
      {ids.map((id) => <PostPorId key={id} id={id} />)}
    </div>
  );
}

// ---------- caixas de texto ----------
export function Nota({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <aside className="playbook-nota">
      <p className="t-h3">{titulo}</p>
      {children}
    </aside>
  );
}

/** As tabelas do markdown, recolhidas. */
export function VerNumeros({ md, rotulo = "Ver os números" }: { md: string; rotulo?: string }) {
  if (!md.trim()) return null;
  return (
    <details className="playbook-numeros">
      <summary>{rotulo}</summary>
      <Markdown texto={md} />
    </details>
  );
}
