// Dados de pior caso do feed (break-ui). Mesmo formato da API; entram no lugar de useDestaques via ?dados=pior|vazio|um.
// Valores plausíveis da base real: perfil com nome longo, contagens grandes, campos opcionais nulos, contagem 1.
import type { Destaque } from "../../api/tipos";

const PIORES: Partial<Destaque["post"]>[] = [
  { canal: "Ateliê Maria Aparecida Bolos & Doces Finos · Confeitaria Artesanal", likes: 12483901, comentarios: 184233, er: 12.4837, vezes: 1284.6 },
  { canal: "Jo", likes: 1, comentarios: 1, er: 0.004, vezes: 1.04, gancho: null, publicado: null },
  { canal: "Barbearia do Zé", likes: 0, comentarios: 0, er: null, vezes: null, url: "", formato: "Carrossel" },
  { canal: "@studiojuliananogueira.makeupartist.oficial" },
];
const PORQUE_LONGO = "Bastidor de produção que abre com o produto na tela e mostra o preço logo no primeiro segundo, com a dona falando direto com a câmera; ";

export function piorCaso(real: Destaque[], modo: string): Destaque[] {
  if (modo === "vazio") return [];
  if (modo === "um") return real.slice(0, 1);
  return real.map((d, i) => (i < PIORES.length
    ? { porque: i === 0 ? PORQUE_LONGO + d.porque : d.porque, post: { ...d.post, ...PIORES[i] } }
    : d));
}
