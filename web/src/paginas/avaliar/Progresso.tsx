// Progresso narrado de um trabalho em segundo plano (avaliar e agente): etapas concluídas com ✓, a atual animada.
// Também usado por ../criar.
import { useEffect, useState } from "react";
import "./progresso.css";

export function Progresso({ etapas, desde, titulo = "Avaliando", estimativa = "Leva cerca de 1 minuto." }: { etapas: string[]; desde: number; titulo?: string; estimativa?: string }) {
  const [agora, setAgora] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setAgora(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);
  const s = Math.max(0, Math.round((agora - desde) / 1000));
  return (
    <section className="avaliar-progresso bloco-lima" aria-live="polite">
      <h2 className="t-titulo t-h1">{titulo}</h2>
      <ol className="avaliar-etapas">
        {etapas.length === 0 && <li className="avaliar-etapa avaliar-etapa--atual"><span className="avaliar-etapa-marca" aria-hidden /><span>Enviando o pedido</span></li>}
        {etapas.map((e, i) => {
          const atual = i === etapas.length - 1;
          return (
            <li key={i} className={`avaliar-etapa${atual ? " avaliar-etapa--atual" : ""}`} aria-current={atual ? "step" : undefined}>
              <span className="avaliar-etapa-marca" aria-hidden>{atual ? "" : "✓"}</span>
              <span>{e}{!atual && <span className="so-leitor"> (concluída)</span>}</span>
            </li>
          );
        })}
      </ol>
      <p className="avaliar-tempo">{estimativa} <span className="t-mono">{s} s</span></p>
    </section>
  );
}

