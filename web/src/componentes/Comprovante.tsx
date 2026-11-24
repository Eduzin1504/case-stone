// Comprovante de maquininha: papel térmico com picote, fonte mono. Para checagens e resumos.
//   <Comprovante titulo="Base deste foco" linhas={[{ rotulo: "Posts", valor: "11.676" }, { rotulo: "Criadores", valor: "127" }]}
//                total={{ rotulo: "No top", valor: "250" }} rodape="coletado em 23/11/2026" />
// `children` entra entre as linhas e o total (texto livre). O papel é claro nos dois temas, de propósito.
import type { ReactNode } from "react";

export type LinhaComprovante = { rotulo: string; valor: ReactNode; destaque?: boolean };
type Props = { titulo: string; sub?: string; linhas?: LinhaComprovante[]; total?: LinhaComprovante; rodape?: ReactNode; children?: ReactNode; className?: string };

export function Comprovante({ titulo, sub, linhas = [], total, rodape, children, className = "" }: Props) {
  return (
    <div className={`comprovante-sombra ${className}`}>
      <div className="comprovante">
        <p className="comprovante-titulo">{titulo}</p>
        {sub && <p className="comprovante-sub">{sub}</p>}
        <hr />
        {linhas.length > 0 && (
          <dl>
            {linhas.map((l) => (
              <div key={l.rotulo} className={l.destaque ? "comprovante-destaque" : undefined}>
                <dt>{l.rotulo}</dt>
                <dd>{l.valor}</dd>
              </div>
            ))}
          </dl>
        )}
        {children && <div className="comprovante-livre">{children}</div>}
        {total && (
          <>
            <hr />
            <dl className="comprovante-total">
              <div>
                <dt>{total.rotulo}</dt>
                <dd>{total.valor}</dd>
              </div>
            </dl>
          </>
        )}
        {rodape && (
          <>
            <hr />
            <p className="comprovante-rodape">{rodape}</p>
          </>
        )}
      </div>
    </div>
  );
}
