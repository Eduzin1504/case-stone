// Markdown mínimo para os textos que vêm da API (playbook, método, explicação do agente).
//   <Markdown texto={capitulo.markdown} />
//   <Markdown texto={md} tabelas="recolhidas" />   tabelas dentro de "Ver os números" · tabelas="ocultas" tira as tabelas
// Cobre: títulos (#, ##, ###), parágrafos, **negrito**, *itálico*, `código`, [links](url), listas (- e 1.), citações (>) e tabelas (| a | b |).
// ponytail: sem biblioteca; se aparecer markdown mais rico (imagens, listas aninhadas), trocar por uma.
import { Fragment, type ReactNode } from "react";

function inline(t: string): ReactNode[] {
  const out: ReactNode[] = [];
  const re = /\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`|\[(.+?)\]\((.+?)\)/g;
  let i = 0, m: RegExpExecArray | null, k = 0;
  while ((m = re.exec(t))) {
    if (m.index > i) out.push(t.slice(i, m.index));
    if (m[1]) out.push(<strong key={k++}>{inline(m[1])}</strong>);
    else if (m[2]) out.push(<em key={k++}>{m[2]}</em>);
    else if (m[3]) out.push(<code key={k++}>{m[3]}</code>);
    else out.push(<a key={k++} href={m[5]} target="_blank" rel="noreferrer">{m[4]}</a>);
    i = m.index + m[0].length;
  }
  if (i < t.length) out.push(t.slice(i));
  return out;
}

const celulas = (l: string) => l.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());

export function Markdown({ texto, className = "", tabelas = "visiveis" }: { texto: string; className?: string; tabelas?: "visiveis" | "recolhidas" | "ocultas" }) {
  const linhas = texto.replace(/\r/g, "").split("\n");
  const blocos: ReactNode[] = [];
  let i = 0;
  const ate = (teste: (l: string) => boolean) => {
    const ini = i;
    while (i < linhas.length && teste(linhas[i])) i++;
    return linhas.slice(ini, i);
  };
  while (i < linhas.length) {
    const l = linhas[i];
    const k = blocos.length;
    const h = /^(#{1,4})\s+(.*)$/.exec(l);
    if (!l.trim()) i++;
    else if (h) {
      const N = (["h2", "h3", "h4", "h4"] as const)[h[1].length - 1];
      blocos.push(<N key={k}>{inline(h[2])}</N>);
      i++;
    } else if (/^\s*\|/.test(l)) {
      const [cab, ...resto] = ate((x) => /^\s*\|/.test(x)).map(celulas);
      const corpo = resto.filter((r) => !r.every((c) => /^:?-+:?$/.test(c)));
      const tabela = (
        <div key={k} className="md-tabela"><table className="tabela">
          <thead><tr>{cab.map((c, j) => <th key={j}>{inline(c)}</th>)}</tr></thead>
          <tbody>{corpo.map((r, a) => <tr key={a}>{r.map((c, j) => <td key={j}>{inline(c)}</td>)}</tr>)}</tbody>
        </table></div>
      );
      if (tabelas === "recolhidas") blocos.push(<details key={k} className="md-numeros"><summary>Ver os números</summary>{tabela}</details>);
      else if (tabelas === "visiveis") blocos.push(tabela);
    } else if (/^\s*([-*]|\d+\.)\s+/.test(l)) {
      const ord = /^\s*\d+\./.test(l);
      const itens = ate((x) => /^\s*([-*]|\d+\.)\s+/.test(x) || (/^\s{2,}\S/.test(x) && !!x.trim()));
      const juntos: string[] = [];
      itens.forEach((x) => (/^\s*([-*]|\d+\.)\s+/.test(x) ? juntos.push(x.replace(/^\s*([-*]|\d+\.)\s+/, "")) : (juntos[juntos.length - 1] += " " + x.trim())));
      const L = ord ? "ol" : "ul";
      blocos.push(<L key={k}>{juntos.map((x, j) => <li key={j}>{inline(x)}</li>)}</L>);
    } else if (/^>\s?/.test(l)) {
      blocos.push(<blockquote key={k}>{inline(ate((x) => /^>\s?/.test(x)).map((x) => x.replace(/^>\s?/, "")).join(" "))}</blockquote>);
    } else {
      const par = ate((x) => !!x.trim() && !/^(#{1,4}\s|\s*\||\s*([-*]|\d+\.)\s+|>)/.test(x));
      if (!par.length) i++; // nunca fica parado numa linha
      blocos.push(<p key={k}>{par.map((x, j) => <Fragment key={j}>{j > 0 && " "}{inline(x)}</Fragment>)}</p>);
    }
  }
  return <div className={`md ${className}`}>{blocos}</div>;
}
