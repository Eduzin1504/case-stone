// Linha do tempo dos posts de um criador (SVG + d3-scale). Com "vezes o esperado": eixo log e linha do esperado (1×).
// Sem (criador que não concorre): mostra o ER de cada post. Hover mostra o post; clique abre o painel.
import { useEffect, useRef, useState } from "react";
import { scaleLinear, scaleLog, scaleTime } from "d3-scale";
import type { PontoSerie, PostResumo } from "../../api/tipos";
import { Miniatura } from "../../componentes";
import { fmtData, fmtPct, fmtVezes } from "../../util/formato";
import { useEntrou } from "../../util/useEntrou";

const ALT = 280;
const M = { t: 18, r: 18, b: 30, l: 52 };
const dia = (iso: string) => new Date(`${iso.slice(0, 10)}T12:00:00`);
const fmtMes = (d: Date) => d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });

export function LinhaDoTempo({ serie, posts, onAbrir }: { serie: PontoSerie[]; posts: PostResumo[]; onAbrir: (id: string) => void }) {
  const caixa = useRef<HTMLDivElement>(null);
  const entrou = useEntrou(caixa);
  const [larg, setLarg] = useState(0);
  const [ativo, setAtivo] = useState<string | null>(null);
  useEffect(() => {
    const el = caixa.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setLarg(el.clientWidth));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const pontos = serie.filter((p) => p.data);
  const comVezes = pontos.some((p) => p.vezes != null);
  const valor = (p: PontoSerie) => (comVezes ? p.vezes : p.er);
  const fmt = comVezes ? fmtVezes : fmtPct;
  const medidos = pontos.filter((p) => valor(p) != null && (!comVezes || valor(p)! > 0));
  const foraDaConta = comVezes ? pontos.filter((p) => p.vezes == null) : [];
  const vs = medidos.map((p) => valor(p)!);
  const datas = pontos.map((p) => dia(p.data).getTime());

  const x = scaleTime().domain([Math.min(...datas), Math.max(...datas)]).range([M.l, Math.max(larg - M.r, M.l + 1)]);
  if (x.domain()[0].getTime() === x.domain()[1].getTime()) x.domain([new Date(datas[0] - 864e5), new Date(datas[0] + 864e5)]);
  const base = ALT - M.b - (foraDaConta.length ? 22 : 0);
  const y = comVezes
    ? scaleLog().domain([Math.min(...vs, 0.5), Math.max(...vs, 2)]).range([base, M.t]).nice()
    : scaleLinear().domain([0, Math.max(...vs, 0.001)]).range([base, M.t]).nice();
  const marcasY = y.ticks(4).filter((t, _i, a) => !comVezes || a.length <= 5 || Number.isInteger(Math.log10(t)));
  const marcasX = larg < 520 ? x.domain() : x.ticks(Math.min(6, Math.floor(larg / 110)));

  const post = (id: string) => posts.find((p) => p.id === id);
  const pAtivo = pontos.find((p) => p.id === ativo);
  const dica = pAtivo && post(pAtivo.id);
  const xAtivo = pAtivo ? x(dia(pAtivo.data)) : 0;

  return (
    <div ref={caixa} className="criador-tempo">
      {larg > 0 && (
        <svg width={larg} height={ALT} role="img" aria-label={`Linha do tempo de ${pontos.length} posts, de ${fmtData(pontos[0]?.data)} a ${fmtData(pontos[pontos.length - 1]?.data)}. Os posts estão na grade abaixo.`} aria-describedby="criador-grade">
          {marcasY.map((t) => (
            <g key={t}>
              <line x1={M.l} x2={larg - M.r} y1={y(t)} y2={y(t)} className="criador-tempo-grade" />
              <text x={M.l - 8} y={y(t)} dy="0.32em" textAnchor="end" className="criador-tempo-eixo">{fmt(t)}</text>
            </g>
          ))}
          {marcasX.map((t) => (
            <text key={+t} x={x(t)} y={ALT - 8} textAnchor={larg < 520 ? (t === marcasX[0] ? "start" : "end") : "middle"} className="criador-tempo-eixo">{fmtMes(t)}</text>
          ))}
          {comVezes && (
            <g>
              <line x1={M.l} x2={entrou ? larg - M.r : M.l} y1={y(1)} y2={y(1)} className="criador-tempo-esperado" />
            </g>
          )}
          {foraDaConta.length > 0 && <text x={M.l - 8} y={base + 22} dy="0.32em" textAnchor="end" className="criador-tempo-eixo">fora</text>}
          {foraDaConta.map((p) => (
            <circle key={p.id} cx={x(dia(p.data))} cy={base + 22} r={ativo === p.id ? 6 : 4} className="criador-tempo-fora"
              onPointerEnter={() => setAtivo(p.id)} onPointerLeave={() => setAtivo(null)} onClick={() => onAbrir(p.id)} />
          ))}
          {[...medidos].sort((a, b) => +a.top - +b.top).map((p, i) => (
            <circle
              key={p.id} cx={x(dia(p.data))} cy={y(valor(p)!)} r={(p.top ? 8 : 5) + (ativo === p.id ? 3 : 0)}
              className={`criador-tempo-ponto${p.top ? " criador-tempo-ponto--top" : ""}`}
              style={{ opacity: entrou ? 1 : 0, transitionDelay: `${Math.min(i * 12, 600)}ms` }}
              tabIndex={p.top ? 0 : undefined} role={p.top ? "button" : undefined}
              aria-label={p.top ? `Post do top de ${fmtData(p.data)}, ${fmt(valor(p))}. Abrir` : undefined}
              onPointerEnter={() => setAtivo(p.id)} onPointerLeave={() => setAtivo(null)}
              onFocus={() => setAtivo(p.id)} onBlur={() => setAtivo(null)}
              onClick={() => onAbrir(p.id)} onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), onAbrir(p.id))}
            />
          ))}
        </svg>
      )}
      {pAtivo && (
        <div className="criador-tempo-dica" style={{ left: Math.max(8, Math.min(xAtivo - 120, larg - 248)), top: pAtivo.vezes == null && comVezes ? base - 96 : Math.max(0, y(valor(pAtivo) ?? 1) - 106) }}>
          <span className="criador-tempo-dica-foto"><Miniatura src={dica?.thumb} alt="" reserva="" /></span>
          <span className="criador-tempo-dica-texto">
            <b className="corta-2">{dica?.titulo || dica?.gancho || "Post"}</b>
            <span className="t-sec">{fmtData(pAtivo.data)} · {pAtivo.vezes != null ? `${fmtVezes(pAtivo.vezes)} o esperado` : `ER ${fmtPct(pAtivo.er)}`}{pAtivo.top ? " · top" : ""}</span>
          </span>
        </div>
      )}
      <p className="criador-tempo-legenda t-pequeno t-sec">
        <span><i className="criador-tempo-marca criador-tempo-marca--top" /> post do top</span>
        <span><i className="criador-tempo-marca" /> outros posts</span>
        {comVezes && <span>Linha tracejada: o esperado (1×)</span>}
        {foraDaConta.length > 0 && <span><i className="criador-tempo-marca criador-tempo-marca--fora" /> fora da conta do esperado ({foraDaConta.length})</span>}
        <span>{comVezes ? "Altura: vezes o esperado, em escala comprimida (logarítmica)." : "Altura: engajamento (ER) de cada post."}</span>
      </p>
    </div>
  );
}
