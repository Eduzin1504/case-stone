// Dispersão log-log: cada post é um ponto; a diagonal é "igual ao esperado"; o top fica em destaque.
import { useMemo, useRef, useState, type PointerEvent } from "react";
import { scaleLog } from "d3-scale";
import { useEsperadoReal } from "../../api/hooks";
import { Erro, Esqueleto, Secao, Vazio, useAbrirPost } from "../../componentes";
import { fmtInt, fmtNum, fmtVezes } from "../../util/formato";
import { useEntrou } from "../../util/useEntrou";
import { useLargura } from "./useLargura";

const GUIAS = [1, 10, 100, 1000];
const potencias = ([a, b]: number[]) => {
  const out: number[] = [];
  for (let e = Math.ceil(Math.log10(a)); e <= Math.floor(Math.log10(b)); e++) out.push(10 ** e);
  return out;
};
const mediana = (v: number[]) => { const s = [...v].sort((a, b) => a - b); return s.length ? s[Math.floor(s.length / 2)] : null; };

export function EsperadoReal({ plataforma }: { plataforma?: string }) {
  const { data, isLoading, error, refetch } = useEsperadoReal(plataforma);
  const caixa = useRef<HTMLDivElement>(null);
  const W = useLargura(caixa);
  const entrou = useEntrou(caixa);
  const abrir = useAbrirPost();
  const [ativo, setAtivo] = useState<number | null>(null);

  const estreito = W < 560;
  const H = Math.round(Math.min(620, Math.max(340, W * 0.6)));
  const m = { e: estreito ? 54 : 60, d: 14, c: 14, b: 46 };

  const g = useMemo(() => {
    const brutos = (data?.pontos ?? []).filter((p) => p.real > 0 && p.esperado > 0);
    if (!brutos.length || !W) return null;
    const ex = [Math.min(...brutos.map((p) => p.esperado)) * 0.7, Math.max(...brutos.map((p) => p.esperado)) * 1.4];
    const ey = [Math.min(...brutos.map((p) => p.real)) * 0.7, Math.max(...brutos.map((p) => p.real)) * 2];
    const x = scaleLog().domain(ex).range([m.e, W - m.d]);
    const y = scaleLog().domain(ey).range([H - m.b, m.c]);
    // o top por último, para ficar por cima
    const pts = [...brutos].sort((a, b) => Number(a.top) - Number(b.top)).map((p) => ({ ...p, px: x(p.esperado), py: y(p.real), vezes: p.real / p.esperado }));
    const tops = pts.filter((p) => p.top);
    const campeao = tops.reduce<number | null>((m2, p, i) => (m2 == null || p.vezes > tops[m2].vezes ? i : m2), null);
    const teclado = new Set([...tops].sort((a, b) => b.vezes - a.vezes).slice(0, 20).map((p) => p.id));
    return { x, y, ex, ey, pts, nTop: tops.length, med: mediana(tops.map((p) => p.vezes)), campeao: campeao == null ? null : pts.indexOf(tops[campeao]), teclado };
  }, [data, W, H, m.e]);

  const mover = (e: PointerEvent<SVGSVGElement>) => {
    if (!g) return;
    const r = e.currentTarget.getBoundingClientRect();
    const mx = e.clientX - r.left, my = e.clientY - r.top;
    let melhor: number | null = null, dMin = 18;
    g.pts.forEach((p, i) => {
      const d = Math.hypot(p.px - mx, p.py - my) - (p.top ? 5 : 0); // o top ganha no empate
      if (d < dMin) { dMin = d; melhor = i; }
    });
    setAtivo(melhor);
  };

  const foco = g && (ativo ?? g.campeao) != null ? g.pts[(ativo ?? g.campeao)!] : null;
  const titulo = g?.med ? `Metade do top passou de ${fmtVezes(g.med)} o esperado` : "Esperado × real";

  return (
    <Secao titulo={titulo} sub="Cada ponto é um post. Quanto mais acima da diagonal, mais o post rendeu além do que o perfil costuma render.">
      {isLoading && <Esqueleto altura={420} />}
      {error && <Erro erro={error} onTentar={refetch} />}
      {data && !data.pontos.length && <Vazio titulo="Sem pontos">Nenhum post desta plataforma concorre ao top. Troque a plataforma acima.</Vazio>}
      <div ref={caixa} className="mapa-er">
        {g && (
          <>
            <svg
              width={W} height={H} role="group" aria-label={`Dispersão de ${fmtInt(g.pts.length)} posts: engajamento esperado no eixo horizontal, real no vertical. ${g.nTop} são do top.`}
              onPointerMove={mover} onPointerLeave={() => setAtivo(null)} onClick={() => ativo != null && abrir(g.pts[ativo].id)} style={{ cursor: ativo != null ? "pointer" : "default" }}
            >
              <defs><clipPath id="mapa-er-clip"><rect x={m.e} y={m.c} width={W - m.e - m.d} height={H - m.c - m.b} /></clipPath></defs>
              <rect className="mapa-er-fundo" x={m.e} y={m.c} width={W - m.e - m.d} height={H - m.c - m.b} />
              {potencias(g.ey).map((t) => (
                <g key={`y${t}`}>
                  <line className="mapa-grade" x1={m.e} x2={W - m.d} y1={g.y(t)} y2={g.y(t)} />
                  <text className="mapa-eixo" x={m.e - 8} y={g.y(t)} dy="0.32em" textAnchor="end">{fmtNum(t)}</text>
                </g>
              ))}
              {potencias(g.ex).map((t) => (
                <g key={`x${t}`}>
                  <line className="mapa-grade" x1={g.x(t)} x2={g.x(t)} y1={m.c} y2={H - m.b} />
                  <text className="mapa-eixo" x={g.x(t)} y={H - m.b + 18} textAnchor="middle">{fmtNum(t)}</text>
                </g>
              ))}
              <text className="mapa-eixo mapa-eixo--nome" x={W - m.d} y={H - 6} textAnchor="end">esperado para o perfil (curtidas + comentários) →</text>
              <text className="mapa-eixo mapa-eixo--nome" x={m.e + 8} y={m.c + 16}>↑ real</text>

              <g clipPath="url(#mapa-er-clip)">
                {GUIAS.filter((k) => g.ex[0] * k < g.ey[1]).map((k) => {
                  const x1 = Math.max(g.ex[0], g.ey[0] / k), x2 = Math.min(g.ex[1], g.ey[1] / k);
                  // rótulo deitado sobre a linha, a 72% do caminho
                  const xa = g.x(x1), ya = g.y(x1 * k), xb = g.x(x2), yb = g.y(x2 * k);
                  const lx = xa + (xb - xa) * 0.72, ly = ya + (yb - ya) * 0.72;
                  const ang = (Math.atan2(yb - ya, xb - xa) * 180) / Math.PI;
                  return (
                    <g key={k} className={`mapa-er-guia${k === 1 ? " mapa-er-guia--igual" : ""}`} style={{ opacity: entrou ? 1 : 0 }}>
                      <line x1={xa} y1={ya} x2={xb} y2={yb} />
                      <text x={lx} y={ly} dy={-6} textAnchor="middle" transform={`rotate(${ang} ${lx} ${ly})`}>{k === 1 ? "igual ao esperado" : `${fmtInt(k)}×${estreito ? "" : " o esperado"}`}</text>
                    </g>
                  );
                })}
                <g className="mapa-er-pontos" style={{ opacity: entrou ? 1 : 0 }}>
                  {g.pts.filter((p) => !p.top).map((p) => <circle key={p.id} className="mapa-er-comum" cx={p.px} cy={p.py} r={estreito ? 1.8 : 2.4} />)}
                </g>
                <g className="mapa-er-pontos mapa-er-pontos--top" style={{ opacity: entrou ? 1 : 0 }}>
                  {g.pts.map((p, i) => p.top && (
                    <circle
                      key={p.id} className="mapa-er-top" cx={p.px} cy={p.py} r={estreito ? 3.4 : 4.6}
                      {...(g.teclado.has(p.id) ? {
                        tabIndex: 0, role: "button", "aria-label": `${p.canal}: ${fmtVezes(p.vezes)} o esperado. Abrir o post.`,
                        onFocus: () => setAtivo(i), onBlur: () => setAtivo(null),
                        onKeyDown: (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); abrir(p.id); } },
                      } : {})}
                    />
                  ))}
                </g>
                {foco && (
                  <g className="mapa-er-foco" style={{ opacity: entrou ? 1 : 0 }}>
                    {/* o conceito, desenhado: da linha do esperado até onde o post chegou */}
                    <line x1={foco.px} x2={foco.px} y1={g.y(foco.esperado)} y2={foco.py} />
                    <circle className="mapa-er-foco-base" cx={foco.px} cy={g.y(foco.esperado)} r={3} />
                    <circle cx={foco.px} cy={foco.py} r={estreito ? 6 : 8} />
                  </g>
                )}
              </g>
            </svg>
            {foco && (
              <div
                className={`mapa-dica${ativo == null ? " mapa-dica--fixa" : ""}${estreito ? " mapa-dica--abaixo" : ""}`} role="tooltip"
                // em tela estreita a dica fica embaixo do gráfico, para não cobrir os pontos nem sair da tela
                style={estreito ? undefined : { left: foco.px, top: foco.py, transform: `translate(${foco.px > W * 0.55 ? "calc(-100% - 14px)" : "14px"}, ${foco.py > H * 0.6 ? "calc(-100% + 10px)" : "-10px"})` }}
              >
                <p className="mapa-dica-nome">{foco.canal}</p>
                <p className="mapa-dica-num">{fmtVezes(foco.vezes)} <span>o esperado</span></p>
                <p>Real: <b>{fmtNum(foco.real)}</b> · Esperado: <b>{fmtNum(foco.esperado)}</b></p>
                <p className="t-sec">{foco.top ? "Post do top" : "Post comum"}{ativo != null ? " · clique para abrir" : " · o maior salto da base"}</p>
              </div>
            )}
          </>
        )}
      </div>
      {g && (
        <>
          <p className="mapa-legenda">
            <span><i className="mapa-bola mapa-bola--top" />Post do top ({fmtInt(g.nTop)})</span>
            <span><i className="mapa-bola" />Outros posts que concorrem ({fmtInt(g.pts.length - g.nTop)})</span>
            <span><i className="mapa-traco" />Igual ao esperado</span>
            <span><i className="mapa-traco mapa-traco--guia" />10×, 100×, 1.000× o esperado</span>
          </p>
          <p className="mapa-leitura">
            <b>Como ler:</b> o traço vertical liga o que era esperado para o perfil ao que o post de fato rendeu. Esse salto é o "× o esperado" que aparece em todo o site.
            Os eixos são logarítmicos: cada linha da grade vale dez vezes a anterior. Passe o mouse num ponto para ver o criador e clique para abrir o post.
          </p>
          <p className="t-pequeno t-sec mapa-nota">{data?.nota.slice(Math.max(0, data.nota.indexOf("Mostrando")))}</p>
        </>
      )}
    </Secao>
  );
}
