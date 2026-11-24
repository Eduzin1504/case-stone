// Imagem de capa com reserva desenhada quando falta ou não carrega (miniaturas do Instagram expiram).
//   <Miniatura src={post.thumb} alt={post.titulo} reserva={post.plataforma} />
// Preenche o elemento pai (100% × 100%, object-fit: cover): dê o tamanho e o raio no pai.
import { useState } from "react";

export function Miniatura({ src, alt, reserva = "sem capa" }: { src: string | null | undefined; alt: string; reserva?: string }) {
  const [falhou, setFalhou] = useState(false);
  if (!src || falhou) return <span className="mini-reserva" role="img" aria-label={alt}><span>{reserva}</span></span>;
  return <img className="mini" src={src} alt={alt} loading="lazy" decoding="async" onError={() => setFalhou(true)} />;
}
