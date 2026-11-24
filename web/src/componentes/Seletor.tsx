// Lista de escolha (select nativo, com a cara do sistema).
//   <Seletor rotulo="Tema" valor={tema} onChange={setTema} opcoes={temas} todos="Todos os temas" />
// opcoes: strings ou { valor, rotulo }. `todos` acrescenta a opção vazia ("") no início.
import { useId } from "react";

type Opcao = string | { valor: string; rotulo: string };
type Props = { rotulo: string; valor: string; onChange: (v: string) => void; opcoes: Opcao[]; todos?: string; esconderRotulo?: boolean; className?: string };

export function Seletor({ rotulo, valor, onChange, opcoes, todos, esconderRotulo, className = "" }: Props) {
  const id = useId();
  return (
    <div className={`campo ${className}`}>
      <label htmlFor={id} className={esconderRotulo ? "so-leitor" : "campo-rotulo"}>{rotulo}</label>
      <span className="seletor">
        <select id={id} value={valor} onChange={(e) => onChange(e.target.value)}>
          {todos && <option value="">{todos}</option>}
          {opcoes.map((o) => {
            const op = typeof o === "string" ? { valor: o, rotulo: o } : o;
            return <option key={op.valor} value={op.valor}>{op.rotulo}</option>;
          })}
        </select>
      </span>
    </div>
  );
}
