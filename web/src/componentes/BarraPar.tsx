// Barras pareadas top × controle: a de cima (verde) é a frequência no top; a de baixo (cinza), no grupo de controle.
// As barras crescem ao entrar na tela.
//   <BarraPar rotulo={p.rotulo} top={p.freq_top} controle={p.freq_controle} lift={p.lift} selo={p.selo} fragil={p.fragil} max={0.6} />
// top/controle são frações (0.25 = 25%). `max` fixa a escala para comparar várias barras (padrão: o maior dos dois).
// `acao` (opcional) aparece à direita do rótulo (ex.: um botão "ver exemplos"). Use <LegendaBarraPar /> uma vez por lista.
import { useRef, type ReactNode } from "react";
import { fmtPct, fmtVezes } from "../util/formato";
import { useEntrou } from "../util/useEntrou";
import { Selo } from "./Selo";

type Props = {
  rotulo: ReactNode; top: number; controle: number; max?: number; lift?: number | null;
  selo?: string | null; fragil?: boolean; acao?: ReactNode; nomeTop?: string; nomeControle?: string;
};

export function BarraPar({ rotulo, top, controle, max, lift, selo, fragil, acao, nomeTop = "top", nomeControle = "controle" }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const entrou = useEntrou(ref);
  const m = max ?? Math.max(top, controle, 0.0001);
  // a barra ocupa a fração do espaço que sobra depois do número (56px), para o valor ficar colado na ponta dela
  const larg = (v: number) => `calc((100% - 56px) * ${entrou ? Math.min(1, v / m) : 0})`;
  const baixo = lift != null && lift < 1;
  return (
    <div ref={ref} className={`barrapar${lift === undefined ? " barrapar--sem-lift" : ""}`}>
      <div className="barrapar-cab">
        <span className="barrapar-rotulo">{rotulo}</span>
        {selo && <Selo tipo={selo} />}
        {fragil && <Selo tipo="frágil" />}
        {acao}
      </div>
      <div className="barrapar-barras" role="img" aria-label={`${nomeTop}: ${fmtPct(top)}; ${nomeControle}: ${fmtPct(controle)}`}>
        <div className="barrapar-linha">
          <span className="barrapar-barra barrapar-barra--top" style={{ width: larg(top) }} />
          <span className="barrapar-valor">{fmtPct(top)}</span>
        </div>
        <div className="barrapar-linha">
          <span className="barrapar-barra barrapar-barra--controle" style={{ width: larg(controle) }} />
          <span className="barrapar-valor barrapar-valor--sec">{fmtPct(controle)}</span>
        </div>
      </div>
      {lift !== undefined && (
        <div className={`barrapar-lift${baixo ? " barrapar-lift--baixo" : ""}`} title="Quantas vezes aparece mais no top que no grupo de controle">
          {fmtVezes(lift)}
        </div>
      )}
    </div>
  );
}

export function LegendaBarraPar({ nomeTop = "No top", nomeControle = "No grupo de controle" }: { nomeTop?: string; nomeControle?: string }) {
  return (
    <p className="barrapar-legenda">
      <span><i className="barrapar-amostra barrapar-barra--top" />{nomeTop}</span>
      <span><i className="barrapar-amostra barrapar-barra--controle" />{nomeControle}</span>
      <span>O número à direita é quantas vezes aparece mais no top.</span>
    </p>
  );
}
