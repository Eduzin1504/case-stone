// Etiqueta de preço: o número-chave em Anton sobre lima, com o furo do barbante.
//   <Etiqueta valor={fmtVezes(post.vezes)} rotulo="o esperado" />
//   <Etiqueta valor="59%" rotulo="comentam querendo comprar" tamanho="g" tom="floresta" />
// tamanho: "p" | "m" | "g" · tom: "lima" (padrão) | "floresta" | "papel" (contorno, para quando já há lima na dobra)
import type { ReactNode } from "react";

type Props = { valor: ReactNode; rotulo?: ReactNode; tamanho?: "p" | "m" | "g"; tom?: "lima" | "floresta" | "papel"; className?: string };

export function Etiqueta({ valor, rotulo, tamanho = "m", tom = "lima", className = "" }: Props) {
  return (
    <span className={`etiqueta etiqueta--${tamanho} etiqueta--${tom} ${className}`}>
      <span className="etiqueta-valor">{valor}</span>
      {rotulo && <span className="etiqueta-rotulo">{rotulo}</span>}
    </span>
  );
}
