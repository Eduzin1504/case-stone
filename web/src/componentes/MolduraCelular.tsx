// Moldura de celular para a prévia do post (tela 9:16). O conteúdo preenche a tela.
//   <MolduraCelular><Midia midia={post.midia} thumb={post.thumb} titulo={post.titulo} url={post.url} plataforma={post.plataforma} /></MolduraCelular>
// `largura` em px (padrão 300; em listas e comparações use 240). Nunca passa de 100% do pai nem de 75% da altura da janela. `layoutId` liga a animação miniatura → detalhe.
import type { ReactNode } from "react";
import { motion } from "motion/react";

export function MolduraCelular({ children, largura = 300, layoutId, className = "" }: { children: ReactNode; largura?: number; layoutId?: string; className?: string }) {
  return (
    <motion.div className={`celular ${className}`} style={{ width: `min(${largura}px, calc(75vh * 9 / 17.2))` }} layoutId={layoutId} transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}>
      <span className="celular-camera" aria-hidden />
      <div className="celular-tela">{children}</div>
    </motion.div>
  );
}
