// Número que conta de 0 até o valor quando entra na tela (uma vez). Sem animação se o usuário pediu menos movimento.
//   <NumeroConta valor={post.likes} />                       → "1,1 mi" (formato padrão: fmtNum)
//   <NumeroConta valor={post.er} formato={fmtPct} className="t-titulo t-mega" />
// É um <span>: o tamanho e a fonte vêm da classe (t-num, t-titulo t-mega…).
import { useEffect, useRef, useState } from "react";
import { animate } from "motion/react";
import { fmtNum } from "../util/formato";
import { semMovimento, useEntrou } from "../util/useEntrou";

type Props = { valor: number | null | undefined; formato?: (n: number) => string; duracao?: number; className?: string };

export function NumeroConta({ valor, formato = fmtNum, duracao = 0.9, className }: Props) {
  const ref = useRef<HTMLSpanElement>(null);
  const entrou = useEntrou(ref);
  const [atual, setAtual] = useState<number | null>(null); // null = mostra o valor final
  useEffect(() => {
    if (!entrou || valor == null || semMovimento()) return;
    const c = animate(0, valor, { duration: duracao, ease: [0.22, 1, 0.36, 1], onUpdate: setAtual, onComplete: () => setAtual(null) });
    return () => c.stop();
  }, [entrou, valor, duracao]);
  const final = valor == null ? "–" : formato(valor);
  return (
    <span ref={ref} className={className} style={{ fontVariantNumeric: "tabular-nums" }} aria-label={final}>
      {atual == null || valor == null ? final : formato(atual)}
    </span>
  );
}
