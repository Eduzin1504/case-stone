// O card de post. Três variações:
//   <PostCard post={p} />                              mosaico (padrão): miniatura grande + rodapé (criador, ER, × o esperado)
//   <PostCard post={p} variante="compacto" />          pequeno, para "parecidos" e faixas horizontais
//   <PostCard post={p} variante="linha" posicao={3} /> linha de lista, com posição opcional em Anton
// Clique: sem `onAbrir`, navega para ?post=<id> na rota atual (o <PainelPost> do shell abre sozinho).
//         com `onAbrir`, chama a função e não navega (ex.: escolher um post para comparar).
// Seleção (modo comparar): `selecionado` (true/false) marca o card com contorno e aria-pressed; `marca` ("A", "B") aparece
//         no canto da miniatura. `semCriador` esconde o nome de quem publicou (perfil do criador).
// Mosaico: ponha os cards dentro de <div className="mosaico">; `destaque` faz o card ocupar 2×2 (use nos primeiros do top).
//          vídeos ficam mais altos sozinhos. A ficha rápida de hover já vem junto (`semFicha` desliga).
// layoutId: o mosaico usa `midia-post-<id>` para a miniatura crescer até o painel. Se o MESMO post aparecer duas vezes
//           na página como mosaico, passe layoutId={false} em um deles.
import { useEffect, useRef, useState, type MouseEvent, type PointerEvent } from "react";
import { Link, useLocation } from "react-router-dom";
import { motion } from "motion/react";
import type { PostResumo } from "../api/tipos";
import { fmtPct, fmtVezes, nomePlataforma } from "../util/formato";
import { Carimbo } from "./Carimbo";
import { FichaRapida } from "./FichaRapida";
import { Miniatura } from "./Miniatura";

type Props = {
  post: PostResumo;
  variante?: "mosaico" | "compacto" | "linha";
  destaque?: boolean;
  posicao?: number;
  layoutId?: string | false;
  onAbrir?: (post: PostResumo) => void;
  semFicha?: boolean;
  selecionado?: boolean;
  marca?: string;
  semCriador?: boolean;
  className?: string;
};

export const layoutIdDoPost = (id: string) => `midia-post-${id}`;

/** Endereço que abre o painel do post mantendo a rota e os outros parâmetros. */
export function useLinkDoPost() {
  const { pathname, search } = useLocation();
  return (id: string) => {
    const q = new URLSearchParams(search);
    q.set("post", id);
    return `${pathname}?${q}`;
  };
}

export function PostCard({ post, variante = "mosaico", destaque, posicao, layoutId, onAbrir, semFicha, selecionado, marca, semCriador, className = "" }: Props) {
  const link = useLinkDoPost();
  const ref = useRef<HTMLAnchorElement>(null);
  const espera = useRef<number>();
  const [ancora, setAncora] = useState<DOMRect | null>(null);
  const video = post.tem_video;
  // Card que nasce com o painel deste post já aberto (link direto, lista recarregada) fica sem layoutId:
  // senão ele tomaria o lugar da moldura do painel na animação compartilhada.
  const [nasceuAberto] = useState(() => new URLSearchParams(window.location.search).get("post") === post.id);
  const lid = layoutId === false || nasceuAberto ? undefined : layoutId ?? (variante === "mosaico" ? layoutIdDoPost(post.id) : undefined);

  const clique = (e: MouseEvent) => {
    setAncora(null);
    window.clearTimeout(espera.current);
    if (!onAbrir) return;
    e.preventDefault();
    onAbrir(post);
  };
  const entra = (e: PointerEvent) => {
    // só com mouse de verdade, em tela larga, e fora de áreas expandidas (lá a ficha cobriria a lista)
    if (semFicha || e.pointerType !== "mouse" || !matchMedia("(hover: hover) and (min-width: 901px)").matches || ref.current?.closest("[data-sem-ficha]")) return;
    espera.current = window.setTimeout(() => ref.current && setAncora(ref.current.getBoundingClientRect()), 260);
  };
  const sai = () => {
    window.clearTimeout(espera.current);
    setAncora(null);
  };

  useEffect(() => {
    if (!ancora) return;
    const fechar = () => setAncora(null);
    window.addEventListener("scroll", fechar, { capture: true, passive: true });
    return () => window.removeEventListener("scroll", fechar, { capture: true });
  }, [ancora]);

  const vezes = post.vezes != null && (
    <span className="pc-vezes"><b>{fmtVezes(post.vezes)}</b> o esperado</span>
  );
  const selo = <span className="pc-selo">{variante === "mosaico" ? `${nomePlataforma(post.plataforma)} · ${post.formato}` : post.formato}</span>;
  const rotulo = `${post.titulo || post.gancho || "Post"}, de ${post.canal}`;

  return (
    <>
      <Link
        ref={ref} to={link(post.id)} onClick={clique} onPointerEnter={entra} onPointerLeave={sai} aria-label={rotulo}
        role={selecionado !== undefined ? "button" : undefined} aria-pressed={selecionado}
        className={`pc pc--${variante}${destaque ? " pc--destaque" : ""}${video && variante === "mosaico" ? " pc--alto" : ""}${selecionado ? " pc--selecionado" : ""} ${className}`}
      >
        {variante === "linha" && posicao != null && <span className="pc-posicao">{posicao}</span>}
        <motion.span className="pc-midia" layoutId={lid} transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}>
          <Miniatura src={post.thumb} alt="" reserva={nomePlataforma(post.plataforma)} />
          {variante !== "linha" && selo}
          {post.top && variante === "mosaico" && (
            <Carimbo className="pc-carimbo" texto="TOP" sub={post.posicao_top ? `nº ${post.posicao_top}` : undefined} cheio tamanho={destaque ? 60 : 48} />
          )}
          {post.top && variante === "compacto" && <span className="pc-top">Top</span>}
          {selecionado && marca && <span className="pc-marca" aria-hidden>{marca}</span>}
        </motion.span>
        {variante === "linha" ? (
          <>
            <span className="pc-corpo">
              <span className="pc-titulo corta-1">{post.titulo || post.gancho}</span>
              <span className="pc-sub corta-1">{semCriador ? "" : `${post.canal} · `}{nomePlataforma(post.plataforma)} · {post.formato}{post.top ? " · top" : ""}</span>
            </span>
            <span className="pc-nums">
              {post.vezes != null && <b className="pc-num">{fmtVezes(post.vezes)}</b>}
              <span className="pc-sub">ER {fmtPct(post.er)}</span>
            </span>
          </>
        ) : (
          <span className="pc-rodape">
            {!semCriador && <span className="pc-criador corta-1">{post.canal}</span>}
            <span className="pc-metricas">
              {vezes}
              <span className="pc-er">ER {fmtPct(post.er)}</span>
            </span>
          </span>
        )}
      </Link>
      {ancora && <FichaRapida post={post} ancora={ancora} />}
    </>
  );
}
