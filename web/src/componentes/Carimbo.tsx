// Carimbo redondo, borda dupla, levemente girado: TOP 10%, APROVADO, CONFIRMADO NOS ADS.
//   <Carimbo texto="TOP" sub="10%" />
//   <Carimbo texto="Confirmado" sub="nos Ads" tom="dados" tamanho={104} giro={6} />
//   <Carimbo texto="TOP" sub="nº 1" cheio />   (cheio: fundo lima, para ficar sobre foto)
// tom: "tinta" (padrão) | "dados" | "alerta" · tamanho em px (teto de 64; texto longo quebra em duas linhas) · giro em graus
// Use só onde informa: top, aprovado, confirmado.
type Props = { texto: string; sub?: string; tom?: "tinta" | "dados" | "alerta"; tamanho?: number; giro?: number; cheio?: boolean; className?: string };

export function Carimbo({ texto, sub, tom = "tinta", tamanho = 60, giro = -6, cheio, className = "" }: Props) {
  const longo = texto.length > 6;
  tamanho = Math.min(tamanho, longo ? 72 : 64);
  return (
    <span
      className={`carimbo carimbo--${tom}${cheio ? " carimbo--cheio" : ""}${longo ? " carimbo--longo" : ""} ${className}`}
      style={{ width: tamanho, height: tamanho, fontSize: tamanho * (longo ? 0.16 : 0.3), transform: `rotate(${giro}deg)` }}
    >
      <span className="carimbo-texto">{texto}</span>
      {sub && <span className="carimbo-sub">{sub}</span>}
    </span>
  );
}
