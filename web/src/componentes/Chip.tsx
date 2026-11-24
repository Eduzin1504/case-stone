// Chip: par rótulo/valor da leitura ("Gancho · curiosidade") ou filtro clicável.
//   <Chip rotulo="Tema">finanças</Chip>
//   <Chip ativo={so_top} onClick={() => setSoTop(!so_top)}>Só o top</Chip>
//   <Chip onRemover={() => limpar("tema")}>finanças</Chip>
import type { ReactNode } from "react";

type Props = { rotulo?: string; ativo?: boolean; onClick?: () => void; onRemover?: () => void; children: ReactNode };

export function Chip({ rotulo, ativo, onClick, onRemover, children }: Props) {
  const dentro = (
    <>
      {rotulo && <span className="chip-rotulo">{rotulo}</span>}
      <span>{children}</span>
    </>
  );
  if (onClick) return <button type="button" className={`chip chip--botao${ativo ? " chip--ativo" : ""}`} aria-pressed={ativo} onClick={onClick}>{dentro}</button>;
  return (
    <span className={`chip${ativo ? " chip--ativo" : ""}`}>
      {dentro}
      {onRemover && <button type="button" className="chip-x" aria-label="Remover filtro" onClick={onRemover}>×</button>}
    </span>
  );
}
