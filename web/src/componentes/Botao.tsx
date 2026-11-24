// Botão em pílula. Vira <Link> com `para`, <a target=_blank> com `href`, senão <button>.
//   <Botao onClick={salvar}>Salvar</Botao>
//   <Botao variante="lima" tamanho="g" para="/catalogo">Ver o catálogo →</Botao>
//   <Botao variante="contorno" href={post.url}>Abrir no Instagram</Botao>
// variante: "primario" (padrão) | "lima" (no máximo um por tela) | "contorno" | "fantasma" · tamanho: "p" | "m" | "g"
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Link } from "react-router-dom";

type Props = {
  variante?: "primario" | "lima" | "contorno" | "fantasma";
  tamanho?: "p" | "m" | "g";
  para?: string;
  href?: string;
  ocupado?: boolean; // desabilita e mostra "…" (use em mutações)
  children: ReactNode;
} & Omit<ButtonHTMLAttributes<HTMLButtonElement>, "children">;

export function Botao({ variante = "primario", tamanho = "m", para, href, ocupado, className = "", children, ...resto }: Props) {
  const cls = `botao botao--${variante} botao--${tamanho} ${className}`;
  if (para) return <Link to={para} className={cls}>{children}</Link>;
  if (href) return <a href={href} target="_blank" rel="noreferrer" className={cls}>{children}<span aria-hidden> ↗</span></a>;
  return (
    <button type="button" {...resto} className={cls} disabled={resto.disabled || ocupado} aria-busy={ocupado || undefined}>
      {children}{ocupado ? " …" : ""}
    </button>
  );
}
