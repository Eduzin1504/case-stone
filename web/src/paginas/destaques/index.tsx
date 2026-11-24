// Destaques: feed vertical, um post por tela (como Reels/Shorts). Rola com o mouse, ↑ ↓ ou J K.
// O vídeo da tela visível toca sozinho, mudo (vídeo local: botão "Som"; YouTube: o próprio player); o anterior e os 2 seguintes já buscam o detalhe e baixam o vídeo (preload auto), para a rolagem não esperar.
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useDestaques, usePost } from "../../api/hooks";
import type { Destaque } from "../../api/tipos";
import { BotaoColecao, Botao, Erro, Esqueleto, Midia, Miniatura, Vazio, useAbrirPost } from "../../componentes";
import { fmtData, fmtInt, fmtPct, fmtVezes, nomePlataforma } from "../../util/formato";
import "./destaques.css";
import { piorCaso } from "./pior-caso";

// break-ui: ?dados=pior|vazio|um troca os dados do feed (só aparece com o parâmetro na URL; ninguém chega nele pela navegação)
const DADOS = new URLSearchParams(location.search).get("dados");
const MODOS = [["", "Dados reais"], ["pior", "Pior caso"], ["vazio", "Vazio"], ["um", "Um"]] as const;
function Alternador() {
  return (
    <nav className="breakui" aria-label="Dados de teste">
      {MODOS.map(([m, r]) => <a key={m} href={m ? `?dados=${m}` : "?dados="} aria-current={(DADOS ?? "") === m || undefined}>{r}</a>)}
    </nav>
  );
}

const motivo = (porque: string) => porque.split(";")[0].trim();

function VideoFeed({ src, poster, ativo, titulo, mudo, setMudo }: { src: string; poster?: string | null; ativo: boolean; titulo: string; mudo: boolean; setMudo: (m: boolean) => void }) {
  const v = useRef<HTMLVideoElement>(null);
  const barra = useRef<HTMLSpanElement>(null);
  const [pausado, setPausado] = useState(true);
  useEffect(() => {
    const el = v.current;
    if (!el) return;
    if (ativo) el.play().catch(() => {});
    else el.pause();
  }, [ativo]);
  const progresso = () => {
    const el = v.current;
    if (el && barra.current && el.duration) barra.current.style.transform = `scaleX(${el.currentTime / el.duration})`;
  };
  const pular = (e: React.MouseEvent<HTMLDivElement>) => {
    const el = v.current, r = e.currentTarget.getBoundingClientRect();
    if (el?.duration) { el.currentTime = ((e.clientX - r.left) / r.width) * el.duration; progresso(); }
  };
  return (
    <>
      <video ref={v} className="feed-video" src={src} poster={poster ?? undefined} muted={mudo} loop playsInline preload="auto" aria-label={titulo}
        onPlay={() => setPausado(false)} onPause={() => setPausado(true)} onTimeUpdate={progresso}
        onClick={(e) => (e.currentTarget.paused ? e.currentTarget.play() : e.currentTarget.pause())} />
      {pausado && ativo && <span className="feed-play" aria-hidden>▶</span>}
      <button type="button" className="feed-som" onClick={() => setMudo(!mudo)} aria-pressed={!mudo} aria-label={mudo ? "Ligar o som" : "Desligar o som"}>
        {mudo ? "🔇 Ativar som" : "🔊 Som ligado"}
      </button>
      <div className="feed-progresso" onClick={pular} role="slider" aria-label="Posição do vídeo" aria-valuemin={0} aria-valuemax={100} tabIndex={-1}>
        <span ref={barra} />
      </div>
    </>
  );
}

function Slide({ d, n, total, ativo, perto, mudo, setMudo }: { d: Destaque; n: number; total: number; ativo: boolean; perto: boolean; mudo: boolean; setMudo: (m: boolean) => void }) {
  const p = d.post;
  const { data: det } = usePost(perto ? p.id : null);
  const abrir = useAbrirPost();
  const titulo = p.titulo || p.gancho || "Post";
  const m = det?.midia;
  return (
    <section className="feed-slide" data-n={n} aria-label={`${n} de ${total}: ${titulo}`}>
      <div className="feed-palco">
        <div className="feed-tela">
          {m?.tipo === "youtube" && m.youtube_id && ativo
            ? <iframe className="feed-video" title={titulo} allow="autoplay; encrypted-media; picture-in-picture" allowFullScreen
                src={`https://www.youtube.com/embed/${m.youtube_id}?autoplay=1&mute=1&loop=1&playlist=${m.youtube_id}&rel=0&playsinline=1`} />
            : m?.tipo === "video" && m.video_url
            ? <VideoFeed src={m.video_url} poster={p.thumb} ativo={ativo} titulo={titulo} mudo={mudo} setMudo={setMudo} />
            : m ? <Midia midia={m} thumb={p.thumb} titulo={titulo} url={p.url} plataforma={p.plataforma} />
            : <Miniatura src={p.thumb} alt={titulo} reserva={nomePlataforma(p.plataforma)} />}

          <span className="feed-vezes"><b>{fmtVezes(p.vezes)}</b> o esperado</span>

          <div className="feed-legenda">
            <Link className="feed-canal" to={`/criadores/${encodeURIComponent(p.canal_id)}`}>{p.canal}</Link>
            <p className="feed-meta">{nomePlataforma(p.plataforma)} · {p.formato}{p.publicado ? ` · ${fmtData(p.publicado)}` : ""}</p>
            <p className="feed-porque">{motivo(d.porque)}</p>
            {p.gancho && <p className="feed-gancho">“{p.gancho}”</p>}
          </div>
        </div>

        <div className="feed-trilho">
          <span className="feed-pos">{n}/{total}</span>
          <div className="feed-num"><b>{fmtPct(p.er)}</b><span>ER</span></div>
          <div className="feed-num"><b>{fmtInt(p.likes)}</b><span>curtidas</span></div>
          <div className="feed-num"><b>{fmtInt(p.comentarios)}</b><span>comentários</span></div>
          <button type="button" className="feed-acao" onClick={() => abrir(p.id)}>Por dentro</button>
          <BotaoColecao postId={p.id} variante="contorno" tamanho="p" />
          <Link className="feed-acao" to={`/comparar?a=${encodeURIComponent(p.id)}`}>Comparar</Link>
          {p.url && <a className="feed-acao" href={p.url} target="_blank" rel="noreferrer">Original ↗</a>}
        </div>
      </div>
    </section>
  );
}

export default function Destaques() {
  const real = useDestaques(12);
  const { isLoading, error, refetch } = real;
  const data = DADOS && real.data ? piorCaso(real.data, DADOS) : real.data;
  const rolo = useRef<HTMLDivElement>(null);
  const [ativo, setAtivo] = useState(1);
  const [mudo, setMudo] = useState(true); // ligou o som num vídeo, os próximos já vêm com som

  // qual tela está visível
  useEffect(() => {
    const el = rolo.current;
    if (!el || !data?.length) return;
    const io = new IntersectionObserver(
      (es) => es.forEach((e) => e.isIntersecting && setAtivo(Number((e.target as HTMLElement).dataset.n))),
      { root: el, threshold: 0.6 },
    );
    el.querySelectorAll(".feed-slide").forEach((s) => io.observe(s));
    return () => io.disconnect();
  }, [data]);

  // ↑ ↓ / J K trocam de post
  useEffect(() => {
    const tecla = (e: KeyboardEvent) => {
      const alvo = e.target as HTMLElement;
      if (alvo.closest("input, textarea, select, [role=dialog], .midia--carrossel")) return;
      const d = e.key === "ArrowDown" || e.key === "j" ? 1 : e.key === "ArrowUp" || e.key === "k" ? -1 : 0;
      if (!d || !rolo.current) return;
      e.preventDefault();
      rolo.current.querySelector(`[data-n="${ativo + d}"]`)?.scrollIntoView({ behavior: "smooth" });
    };
    window.addEventListener("keydown", tecla);
    return () => window.removeEventListener("keydown", tecla);
  }, [ativo]);

  if (isLoading) return <Esqueleto altura={560} />;
  if (error) return <Erro erro={error} onTentar={refetch} />;
  if (!data?.length)
    return (
      <>{DADOS != null && <Alternador />}<Vazio titulo="Nenhum destaque ainda" acao={<Botao para="/catalogo">Abrir o catálogo</Botao>}>
        Este foco ainda não tem posts no top. Veja todos os posts no catálogo.
      </Vazio></>
    );

  return (
    <div className="feed" ref={rolo}>
      {DADOS != null && <Alternador />}
      <header className="feed-topo">
        <h1 className="t-titulo">Passou do <span className="grifo-inicio">esperado</span></h1>
        <p>Role para ver o próximo · ↑ ↓</p>
      </header>
      {data.map((d, i) => (
        <Slide key={d.post.id} d={d} n={i + 1} total={data.length} ativo={ativo === i + 1} perto={i + 1 >= ativo - 1 && i + 1 <= ativo + 2} mudo={mudo} setMudo={setMudo} />
      ))}
      <section className="feed-slide feed-fim" data-n={data.length + 1}>
        <p className="t-titulo">Esses são os {data.length} que mais passaram do esperado.</p>
        <Botao tamanho="g" para="/catalogo">Ver o catálogo completo →</Botao>
      </section>
    </div>
  );
}
