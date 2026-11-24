// Formatação pt-BR de números. Use sempre estas funções: nenhum número cru na interface.
//   fmtNum(1129239) → "1,1 mi" · fmtPct(4.366) → "437%" · fmtVezes(5677) → "5,7 mil×" · fmtData("2026-07-03") → "03/07/2026"

const nf = (n: number, casas: number) => n.toLocaleString("pt-BR", { maximumFractionDigits: casas });
const VAZIO = "–";

/** Número compacto: 1.664 → "1,7 mil"; 98.458.100 → "98,5 mi". */
export function fmtNum(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return VAZIO;
  const a = Math.abs(n);
  if (a >= 1e9) return `${nf(n / 1e9, 1)} bi`;
  if (a >= 1e6) return `${nf(n / 1e6, 1)} mi`;
  if (a >= 1e4) return `${nf(n / 1e3, 0)} mil`;
  if (a >= 1e3) return `${nf(n / 1e3, 1)} mil`;
  return nf(n, a < 10 && !Number.isInteger(n) ? 1 : 0);
}

/** Número inteiro por extenso: 11021 → "11.021". */
export function fmtInt(n: number | null | undefined): string {
  return n == null ? VAZIO : Math.round(n).toLocaleString("pt-BR");
}

/** Fração → percentual: 4.366 → "437%"; 0.0254 → "2,5%"; 0.59 → "59%". */
export function fmtPct(fracao: number | null | undefined): string {
  if (fracao == null || Number.isNaN(fracao)) return VAZIO;
  const p = fracao * 100;
  return `${nf(p, Math.abs(p) >= 10 ? 0 : 1)}%`;
}

/** Vezes o esperado (ou lift): 5677 → "5,7 mil×"; 2.4 → "2,4×"; 0.64 → "0,64×". */
export function fmtVezes(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return VAZIO;
  if (v >= 1000) return `${fmtNum(v)}×`;
  return `${nf(v, v >= 100 ? 0 : v >= 1 ? 1 : 2)}×`;
}

/** ISO → "03/07/2026". */
export function fmtData(iso: string | null | undefined): string {
  if (!iso) return VAZIO;
  const [a, m, d] = iso.slice(0, 10).split("-");
  return d && m && a ? `${d}/${m}/${a}` : iso;
}

export const NOME_PLATAFORMA: Record<string, string> = { instagram: "Instagram", youtube: "YouTube", todas: "Todas" };
export const NOME_PORTE: Record<string, string> = { micro: "micro", medio: "médio", grande: "grande" };
export const nomePlataforma = (p: string | null | undefined) => (p ? NOME_PLATAFORMA[p] ?? p : VAZIO);
export const nomePorte = (p: string | null | undefined) => (p ? NOME_PORTE[p] ?? p : VAZIO);

/** Texto livre do modelo: troca o travessão por vírgula (" — " → ", "). */
export const semTravessao = (t: string) => t.replace(/\s+[—–]\s+/g, ", ");
