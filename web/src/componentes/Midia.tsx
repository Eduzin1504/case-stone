// A mídia de um post, para qualquer tipo que a API devolve em `post.midia`. Preenche o pai (pensada para <MolduraCelular>).
//   <Midia midia={post.midia} thumb={post.thumb} titulo={post.titulo} url={post.url} plataforma={post.plataforma} />
// youtube  → capa com botão PLAY; ao clicar carrega o embed vertical (iframe youtube.com/embed/<id>)
// video    → <video controls> local (se o arquivo falhar, cai no estado "sem mídia")
// imagens  → carrossel com setas, contador e teclado (← →)
// capa     → só a miniatura, com link para o post original
// nenhuma  → estado "sem mídia" desenhado, com link externo
import { useState, type KeyboardEvent } from "react";
import type { Midia as TMidia, Plataforma } from "../api/tipos";
import { nomePlataforma } from "../util/formato";
import { Miniatura } from "./Miniatura";

type Props = { midia: TMidia; thumb?: string | null; titulo: string; url?: string; plataforma?: Plataforma };

export function Midia({ midia, thumb, titulo, url, plataforma }: Props) {
  const [tocando, setTocando] = useState(false);
  const [falhou, setFalhou] = useState(false);
  const [i, setI] = useState(0);
  const fora = url && (
    <a className="midia-fora" href={url} target="_blank" rel="noreferrer">Ver no {nomePlataforma(plataforma)} ↗</a>
  );

  if (midia.tipo === "youtube" && midia.youtube_id) {
    if (tocando)
      return (
        <>
        <img className="so-impressao midia-img" src={thumb ?? `https://i.ytimg.com/vi/${midia.youtube_id}/hqdefault.jpg`} alt={titulo} />
        <iframe
          className="midia-quadro" title={titulo} allowFullScreen
          src={`https://www.youtube.com/embed/${midia.youtube_id}?autoplay=1&rel=0&playsinline=1`}
          allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
        />
        </>
      );
    return (
      <div className="midia">
        <Miniatura src={thumb ?? `https://i.ytimg.com/vi/${midia.youtube_id}/hqdefault.jpg`} alt={titulo} reserva="YouTube" />
        <button type="button" className="midia-play" onClick={() => setTocando(true)} aria-label={`Assistir: ${titulo}`}>Play</button>
      </div>
    );
  }

  if (midia.tipo === "video" && midia.video_url && !falhou)
    return (
      <>
        {thumb && <img className="so-impressao midia-img" src={thumb} alt={titulo} />}
        <video className="midia-quadro" src={midia.video_url} poster={thumb ?? undefined} controls playsInline preload="metadata" aria-label={titulo} onError={() => setFalhou(true)} />
      </>
    );

  const imgs = midia.tipo === "imagens" ? midia.imagens ?? [] : [];
  if (imgs.length > 0) {
    const n = imgs.length;
    const ir = (d: number) => setI((v) => (v + d + n) % n);
    const tecla = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") ir(1);
      else if (e.key === "ArrowLeft") ir(-1);
      else return;
      e.preventDefault();
    };
    return (
      <div className="midia midia--carrossel" tabIndex={0} role="group" aria-roledescription="carrossel" aria-label={`${titulo}: imagem ${i + 1} de ${n}`} onKeyDown={tecla}>
        <img className="midia-img" src={imgs[i]} alt={`${titulo} (imagem ${i + 1} de ${n})`} />
        {n > 1 && (
          <>
            <button type="button" className="midia-seta midia-seta--ant" onClick={() => ir(-1)} aria-label="Imagem anterior">←</button>
            <button type="button" className="midia-seta midia-seta--prox" onClick={() => ir(1)} aria-label="Próxima imagem">→</button>
            <span className="midia-conta" aria-hidden>{i + 1}/{n}</span>
          </>
        )}
      </div>
    );
  }

  if (midia.tipo !== "nenhuma" && thumb && !falhou)
    return (
      <div className="midia">
        <Miniatura src={thumb} alt={titulo} reserva={nomePlataforma(plataforma)} />
        {fora}
      </div>
    );

  return (
    <div className="midia midia--sem">
      <p className="t-titulo">Sem mídia</p>
      <p>A mídia deste post não ficou guardada na base.</p>
      {fora}
    </div>
  );
}
