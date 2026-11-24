// Controle segmentado (escolha única entre poucas opções).
//   <Seg rotulo="Plataforma" valor={plat} onChange={setPlat} opcoes={[{ valor: "instagram", rotulo: "Instagram" }, { valor: "youtube", rotulo: "YouTube" }]} />
// `rotulo` é lido por leitores de tela (não aparece). tamanho: "p" | "m".
type Opcao<V extends string> = { valor: V; rotulo: string };
type Props<V extends string> = { opcoes: Opcao<V>[]; valor: V; onChange: (v: V) => void; rotulo: string; tamanho?: "p" | "m"; className?: string };

export function Seg<V extends string>({ opcoes, valor, onChange, rotulo, tamanho = "m", className = "" }: Props<V>) {
  return (
    <div role="radiogroup" aria-label={rotulo} className={`seg seg--${tamanho} ${className}`}>
      {opcoes.map((o) => (
        <button key={o.valor} type="button" role="radio" aria-checked={o.valor === valor} className="seg-op" onClick={() => onChange(o.valor)}>
          {o.rotulo}
        </button>
      ))}
    </div>
  );
}
