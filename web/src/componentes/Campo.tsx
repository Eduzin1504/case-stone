// Campo de texto com rótulo. Aceita as props de <input> (ou de <textarea> com `multilinha`).
//   <Campo rotulo="Nome da coleção" value={nome} onChange={(e) => setNome(e.target.value)} />
//   <Campo rotulo="Legenda ou roteiro" multilinha rows={5} dica="Opcional" value={txt} onChange={…} />
//   <Campo rotulo="Buscar por ideia" tamanho="g" esconderRotulo placeholder="ex.: separar o dinheiro da casa e do negócio" … />
import { useId, type InputHTMLAttributes, type TextareaHTMLAttributes } from "react";

type Comum = { rotulo: string; dica?: string; erro?: string | null; tamanho?: "m" | "g"; esconderRotulo?: boolean };
type Props =
  | (Comum & { multilinha?: false } & Omit<InputHTMLAttributes<HTMLInputElement>, "size">)
  | (Comum & { multilinha: true } & TextareaHTMLAttributes<HTMLTextAreaElement>);

export function Campo(props: Props) {
  const id = useId();
  const { rotulo, dica, erro, tamanho = "m", esconderRotulo, className = "", multilinha, ...resto } = props;
  const comum = { id, className: `campo-entrada campo-entrada--${tamanho}`, "aria-invalid": !!erro || undefined, "aria-describedby": erro || dica ? `${id}-d` : undefined };
  return (
    <div className={`campo ${className}`}>
      <label htmlFor={id} className={esconderRotulo ? "so-leitor" : "campo-rotulo"}>{rotulo}</label>
      {multilinha
        ? <textarea {...(resto as TextareaHTMLAttributes<HTMLTextAreaElement>)} {...comum} />
        : <input {...(resto as InputHTMLAttributes<HTMLInputElement>)} {...comum} />}
      {(erro || dica) && <p id={`${id}-d`} className={erro ? "campo-dica t-alerta" : "campo-dica"}>{erro || dica}</p>}
    </div>
  );
}
