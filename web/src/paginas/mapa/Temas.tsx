// Mapa de temas: retângulos com área = presença no top e cor = lift. Clique leva ao catálogo filtrado.
// ponytail: blocos em HTML posicionados pelo d3-hierarchy (não SVG), para o texto quebrar linha e o link ser um <a> de verdade.
import { useMemo, useRef } from "react";
import { Link } from "react-router-dom";
import { hierarchy, treemap } from "d3-hierarchy";
import { useTemas } from "../../api/hooks";
import type { VizTema } from "../../api/tipos";
import { Erro, Esqueleto, Secao, Vazio } from "../../componentes";
import { fmtPct, fmtVezes } from "../../util/formato";
import { useEntrou } from "../../util/useEntrou";
import { useLargura } from "./useLargura";

type No = { children?: VizTema[] } & Partial<VizTema>;
const AMOSTRAS = [{ cor: "magenta", pct: 36 }, { cor: "magenta", pct: 16 }, { cor: "dados", pct: 12 }, { cor: "dados", pct: 30 }, { cor: "dados", pct: 50 }];
const mistura = (cor: string, pct: number) => `color-mix(in srgb, var(--${cor}) ${Math.round(pct)}%, var(--superficie))`;

export function Temas({ plataforma }: { plataforma?: string }) {
  const { data, isLoading, error, refetch } = useTemas(plataforma);
  const caixa = useRef<HTMLDivElement>(null);
  const W = useLargura(caixa);
  const entrou = useEntrou(caixa);
  const temas = useMemo(() => (data ?? []).filter((t) => t.pct_top > 0), [data]);
  const H = W < 560 ? 540 : 480;

  const folhas = useMemo(() => {
    if (!temas.length || !W) return [];
    const raiz = hierarchy<No>({ children: temas }).sum((d) => d.pct_top ?? 0).sort((a, b) => (b.value ?? 0) - (a.value ?? 0));
    return treemap<No>().size([W, H]).paddingInner(4).round(true)(raiz).leaves();
  }, [temas, W, H]);

  const lifts = temas.map((t) => t.lift).filter((l): l is number => l != null);
  const maxL = Math.max(...lifts, 1.01), minL = Math.min(...lifts, 0.99);
  const cor = (lift: number | null | undefined) =>
    lift == null ? "var(--afundado)"
      : lift >= 1 ? mistura("dados", 10 + 40 * Math.min(1, (lift - 1) / (maxL - 1)))
      : mistura("magenta", 12 + 26 * Math.min(1, (1 - lift) / (1 - minL)));

  const maior = temas[0] && temas.reduce((a, b) => (b.pct_top > a.pct_top ? b : a));
  const firmes = temas.filter((t) => t.lift != null && t.n_top >= 5);
  const sobe = firmes.length ? firmes.reduce((a, b) => ((b.lift ?? 0) > (a.lift ?? 0) ? b : a)) : null;
  const titulo = !maior ? "Mapa de temas"
    : sobe && sobe.tema !== maior.tema && (sobe.lift ?? 0) > 1
      ? `${maior.tema} ocupa ${fmtPct(maior.pct_top)} do top; ${sobe.tema} aparece ${fmtVezes(sobe.lift)} mais que nos posts comuns`
      : `${maior.tema} ocupa ${fmtPct(maior.pct_top)} do top`;

  return (
    <Secao titulo={titulo} sub="O tamanho de cada bloco é a fatia do top que fala daquele assunto. A cor compara com os posts comuns.">
      {isLoading && <Esqueleto altura={420} />}
      {error && <Erro erro={error} onTentar={refetch} />}
      {data && !temas.length && <Vazio titulo="Sem temas">Não há posts do top lidos em detalhe nesta plataforma. Troque a plataforma acima.</Vazio>}
      <div ref={caixa} className="mapa-temas" style={{ height: temas.length ? H : 0 }}>
        {folhas.map((f, i) => {
          const t = f.data as VizTema;
          const w = f.x1 - f.x0, h = f.y1 - f.y0;
          const detalhe = `${t.tema}: ${fmtPct(t.pct_top)} do top (${t.n_top} posts)${t.pct_controle != null ? `, ${fmtPct(t.pct_controle)} dos posts comuns` : ""}${t.lift != null ? `, ${fmtVezes(t.lift)} mais no top` : ""}. Ver no catálogo.`;
          const tam = Math.max(15, Math.min(44, Math.sqrt(w * h) / 6.5));
          return (
            <Link
              key={t.tema} to={`/catalogo?tema=${encodeURIComponent(t.tema)}&top=1`} className={`mapa-tema${w < 96 || h < 84 ? " mapa-tema--mini" : ""}`} title={detalhe} aria-label={detalhe}
              style={{ left: f.x0, top: f.y0, width: w, height: h, background: cor(t.lift), opacity: entrou ? 1 : 0, transform: entrou ? "none" : "scale(0.94)", transitionDelay: `${i * 55}ms` }}
            >
              <span className="mapa-tema-nome" style={{ fontSize: tam * 0.62 }}>{t.tema}</span>
              <span className="mapa-tema-pct" style={{ fontSize: tam * 1.25 }}>{fmtPct(t.pct_top)}</span>
              {t.lift != null && <span className="mapa-tema-lift">{fmtVezes(t.lift)} mais no top{t.n_top < 5 ? " · frágil" : ""}</span>}
            </Link>
          );
        })}
      </div>
      {temas.length > 0 && (
        <>
          <p className="mapa-legenda">
            <span>Menos no top que nos comuns</span>
            <span className="mapa-escala" aria-hidden>{AMOSTRAS.map((a) => <i key={a.cor + a.pct} style={{ background: mistura(a.cor, a.pct) }} />)}</span>
            <span>Mais no top</span>
            <span>Área = fatia do top</span>
          </p>
          <p className="mapa-leitura">
            <b>Como ler:</b> bloco grande é assunto frequente no top; verde forte é assunto que aparece mais no top do que nos posts comuns (o número "× mais no top").
            Bloco grande e rosado é tema muito usado que não diferencia quem vai bem. Clique num bloco para ver os posts do top daquele tema.
          </p>
        </>
      )}
    </Secao>
  );
}
