// Resumo da comparação em 2–3 frases, montado só das diferenças que a API devolve (sem modelo).
import type { Comparacao, Diferenca } from "../../api/tipos";
import { fmtPct, fmtVezes } from "../../util/formato";

export const NUMERICAS = ["Vezes o esperado", "ER", "Curtidas", "Comentários", "Views", "Seguidores"];
const lista = (xs: string[]) => (xs.length > 1 ? `${xs.slice(0, -1).join(", ")} e ${xs[xs.length - 1]}` : xs[0] ?? "");
const curta = (d: Diferenca) => d.a.length <= 28 && d.b.length <= 28 && !/\/10$/.test(d.a);

/** Diferenças de leitura (categóricas): tira as métricas e as notas, que têm visual próprio. */
export function leitura(c: Comparacao) {
  const notas = new Set(c.a.notas.map((n) => n.rotulo));
  return c.diferencas.filter((d) => !NUMERICAS.includes(d.rotulo) && !notas.has(d.rotulo));
}

export function resumir(c: Comparacao): string[] {
  const { a, b } = c;
  const frases: string[] = [];
  if (a.vezes != null && b.vezes != null) {
    const [l, lv, pv] = a.vezes >= b.vezes ? ["A", a.vezes, b.vezes] as const : ["B", b.vezes, a.vezes] as const;
    const er = a.er != null && b.er != null && a.er !== b.er ? ` No engajamento, ${(a.er > b.er ? "A" : "B") === l ? "também leva" : `quem leva é o ${a.er > b.er ? "A" : "B"}`}: ${fmtPct(Math.max(a.er, b.er))} contra ${fmtPct(Math.min(a.er, b.er))}.` : "";
    frases.push(`O post ${l} foi mais longe: ${fmtVezes(lv)} o esperado para o tamanho do perfil, contra ${fmtVezes(pv)}.${er}`);
  } else if (a.vezes != null || b.vezes != null) {
    frases.push(`Só o post ${a.vezes != null ? "A" : "B"} concorre ao top (${fmtVezes(a.vezes ?? b.vezes)} o esperado); o outro ficou fora da conta, então a comparação direta vale pelo engajamento: ${fmtPct(a.er)} em A e ${fmtPct(b.er)} em B.`);
  } else if (a.er != null && b.er != null) {
    frases.push(`Nenhum dos dois concorre ao top. No engajamento, A tem ${fmtPct(a.er)} e B tem ${fmtPct(b.er)}.`);
  }
  const l = leitura(c);
  const dif = l.filter((d) => !d.igual);
  const igu = l.filter((d) => d.igual);
  const ex = dif.filter(curta).slice(0, 3).map((d) => `${d.rotulo.toLowerCase()} (${d.a} em A, ${d.b} em B)`);
  if (dif.length) frases.push(`A leitura muda em ${dif.length} de ${l.length} pontos${ex.length ? `, entre eles ${lista(ex)}` : ""}.`);
  else if (l.length) frases.push(`Na leitura, os dois são iguais nos ${l.length} pontos avaliados.`);
  const com = igu.filter((d) => curta(d) && d.a !== "não").slice(0, 3).map((d) => `${d.rotulo.toLowerCase()} (${d.a})`);
  if (dif.length && com.length) frases.push(`Em comum: ${lista(com)}.`);
  return frases;
}
