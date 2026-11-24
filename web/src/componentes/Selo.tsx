// Selo do padrão: como o mercado se compara aos Ads do Impulso. Aceita o texto cru da API.
//   <Selo tipo={padrao.selo} />   <Selo tipo="frágil" />
// "confirmado" (verde) · "contradito" (magenta) · "só mercado" · "inconclusivo" · "frágil" (menos de 5 posts no top)
const MAPA: Record<string, { cls: string; texto: string; titulo: string }> = {
  confirmado: { cls: "ok", texto: "✓ confirmado nos Ads", titulo: "Funciona no mercado e nos Ads do Impulso" },
  contradito: { cls: "nao", texto: "× contradito nos Ads", titulo: "Mercado e Ads do Impulso apontam em direções opostas" },
  "só mercado": { cls: "neutro", texto: "só mercado", titulo: "Ainda não foi testado nos Ads do Impulso" },
  inconclusivo: { cls: "apagado", texto: "inconclusivo", titulo: "Não diferencia o top do grupo de controle" },
  frágil: { cls: "fragil", texto: "frágil", titulo: "Visto em menos de 5 posts do top: é um indício, vale testar" },
};

export function Selo({ tipo }: { tipo: string | null | undefined }) {
  if (!tipo) return null;
  const chave = tipo.toLowerCase().replace("so mercado", "só mercado").replace("so-mercado", "só mercado").replace("fragil", "frágil");
  const s = MAPA[chave] ?? { cls: "neutro", texto: tipo, titulo: tipo };
  return <span className={`selo selo--${s.cls}`} title={s.titulo}>{s.texto}</span>;
}
