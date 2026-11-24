// Playbook editorial (P5): a matéria longa de cada foco. Capa, sumário que acompanha a leitura, capítulos e exportação.
import { useEffect, useRef, useState } from "react";
import { usePlaybook } from "../../api/hooks";
import type { Capitulo } from "../../api/tipos";
import { Botao, BotaoExportar, Erro, Esqueleto, TituloPagina, Vazio } from "../../componentes";
import { useFoco } from "../../contexto/Foco";
import { fmtData, fmtInt } from "../../util/formato";
import { CorpoCapitulo } from "./capitulos";
import { LimiteEmbeds } from "./pecas";
import "./playbook.css";

const dois = (n: number) => String(n).padStart(2, "0");

/** O trecho do título que ganha o bloco lima: a última frase; se o título é uma frase só, as duas últimas palavras. */
function partirTitulo(t: string): [string, string] {
  const frases = t.match(/[^.!?]+[.!?]*/g)?.map((s) => s.trim()).filter(Boolean) ?? [t];
  if (frases.length > 1) return [frases.slice(0, -1).join(" "), frases[frases.length - 1]];
  const p = t.split(" ");
  return [p.slice(0, -2).join(" "), p.slice(-2).join(" ")];
}

function Progresso() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const medir = () => {
      const total = document.documentElement.scrollHeight - window.innerHeight;
      if (ref.current) ref.current.style.transform = `scaleX(${total > 0 ? Math.min(1, window.scrollY / total) : 0})`;
    };
    medir();
    window.addEventListener("scroll", medir, { passive: true });
    window.addEventListener("resize", medir);
    return () => {
      window.removeEventListener("scroll", medir);
      window.removeEventListener("resize", medir);
    };
  }, []);
  return <div className="playbook-progresso nao-imprimir" aria-hidden><div ref={ref} /></div>;
}

function Sumario({ caps }: { caps: Capitulo[] }) {
  const [atual, setAtual] = useState(caps[0]?.id);
  const [aberto, setAberto] = useState(false);
  useEffect(() => {
    if (typeof IntersectionObserver === "undefined") return;
    // uma faixa estreita perto do topo: o capítulo que a cruza é o que está sendo lido
    const io = new IntersectionObserver((es) => es.forEach((e) => e.isIntersecting && setAtual(e.target.id)), { rootMargin: "-18% 0px -74% 0px" });
    caps.forEach((c) => {
      const el = document.getElementById(c.id);
      if (el) io.observe(el);
    });
    // de volta à capa, o primeiro capítulo é o atual
    const capa = document.querySelector(".playbook-capa");
    const ioCapa = new IntersectionObserver((es) => es.some((e) => e.isIntersecting) && setAtual(caps[0]?.id), { rootMargin: "-18% 0px -74% 0px" });
    if (capa) ioCapa.observe(capa);
    return () => { io.disconnect(); ioCapa.disconnect(); };
  }, [caps]);

  const ir = (id: string) => {
    setAberto(false);
    const el = document.getElementById(id);
    el?.scrollIntoView({ behavior: "smooth", block: "start" });
    el?.focus({ preventScroll: true });
  };
  const i = Math.max(0, caps.findIndex((c) => c.id === atual));
  return (
    <nav className={`playbook-sumario nao-imprimir${aberto ? " playbook-sumario--aberto" : ""}`} aria-label="Capítulos">
      <button type="button" className="playbook-sumario-faixa" aria-expanded={aberto} onClick={() => setAberto(!aberto)}>
        <span><b>{dois(i + 1)}</b> {caps[i]?.rotulo ?? caps[i]?.titulo}</span>
        <span>{aberto ? "fechar" : `capítulos (${caps.length})`}</span>
      </button>
      <ol>
        {caps.map((c, k) => (
          <li key={c.id}>
            <a href={`#${c.id}`} aria-current={c.id === atual ? "true" : undefined} onClick={(e) => { e.preventDefault(); ir(c.id); }}>
              <b>{dois(k + 1)}</b>{c.rotulo ?? c.titulo}
            </a>
          </li>
        ))}
      </ol>
    </nav>
  );
}

export default function Playbook() {
  const { data: pb, isLoading, error, refetch } = usePlaybook();
  const { foco, info } = useFoco();
  const alvo = useRef<HTMLElement>(null);

  if (isLoading) return <div className="pilha"><Esqueleto altura={340} /><Esqueleto tipo="texto" n={6} /></div>;
  if (error) return <><TituloPagina titulo="Playbook" /><Erro erro={error} onTentar={refetch} /></>;
  if (!pb || !pb.capitulos.length)
    return (
      <>
        <TituloPagina titulo="Playbook" />
        <Vazio titulo="Este foco ainda não tem playbook" acao={<Botao para="/padroes">Ver os padrões</Botao>}>O texto do playbook não foi encontrado. Os padrões e o catálogo continuam disponíveis.</Vazio>
      </>
    );

  const [antes, grifo] = partirTitulo(pb.titulo);
  const b = info?.base;
  return (
    <LimiteEmbeds>
      <Progresso />
      <article ref={alvo} className="playbook">
        <header className="playbook-capa">
          <div className="playbook-capa-topo">
            <p className="t-sec">Playbook de conteúdo{info ? ` · ${info.nome}` : ""}</p>
            <BotaoExportar alvo={alvo} nome={`playbook-foco-${foco.toLowerCase()}`} semPng />
          </div>
          <h1 className="t-titulo playbook-titulo">{antes} <span className="playbook-grifo">{grifo}</span></h1>
          <div className="playbook-capa-pe">
            <div>
              <p className="playbook-fina">{pb.linha_fina}</p>
              {b && (
                <p className="playbook-base">
                  Base: {fmtInt(b.posts)} posts de {fmtInt(b.criadores)} perfis
                  {b.por_plataforma.youtube ? ` (${fmtInt(b.por_plataforma.instagram)} no Instagram, ${fmtInt(b.por_plataforma.youtube)} no YouTube)` : " no Instagram"}
                  , {fmtInt(b.top)} no top. Coleta em {fmtData(b.coletado_em)}.
                </p>
              )}
              <p className="playbook-meta"><span>Atualizado em <b>{fmtData(pb.atualizado)}</b></span><span><b>{pb.leitura_min} min</b> de leitura</span><span><b>{pb.capitulos.length}</b> capítulos</span></p>
            </div>
          </div>
        </header>

        <div className="playbook-corpo">
          <Sumario caps={pb.capitulos} />
          <div className="playbook-caps">
            {pb.capitulos.map((cap, i) => (
              <section key={cap.id} id={cap.id} className="playbook-cap" tabIndex={-1} aria-labelledby={`${cap.id}-t`}>
                <header className="playbook-cap-cab">
                  <span className="playbook-cap-n" aria-hidden>{dois(i + 1)}</span>
                  <div>
                    <p className="t-sec">{cap.rotulo ?? `Capítulo ${i + 1}`}</p>
                    <h2 id={`${cap.id}-t`} className="t-titulo playbook-cap-titulo">{cap.titulo}</h2>
                  </div>
                </header>
                <CorpoCapitulo cap={cap} pb={pb} />
              </section>
            ))}
          </div>
        </div>
      </article>
    </LimiteEmbeds>
  );
}
