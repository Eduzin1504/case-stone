// Ficha rápida: aparece ao lado do card no hover (só com mouse; no toque não existe). O <PostCard> já usa sozinho.
// Uso direto, se precisar em outro elemento:
//   {ancora && <FichaRapida post={post} ancora={ancora} />}     ancora = elemento.getBoundingClientRect()
// Não aparece em toque nem em tela estreita, fecha ao rolar, e não abre dentro de um elemento com data-sem-ficha.
// Fica à direita da âncora; sem espaço, vai para a esquerda; nunca corta na borda da janela. Não captura o mouse.
import { useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import type { PostResumo } from "../api/tipos";
import { fmtNum, fmtPct, fmtVezes, nomePlataforma, nomePorte } from "../util/formato";
import { Chip } from "./Chip";
import { Etiqueta } from "./Etiqueta";

const LARGURA = 300, FOLGA = 12, MARGEM = 12;

export function FichaRapida({ post, ancora }: { post: PostResumo; ancora: DOMRect }) {
  const ref = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState<{ left: number; top: number } | null>(null);
  useLayoutEffect(() => {
    const alt = ref.current?.offsetHeight ?? 320;
    const cabeDireita = ancora.right + FOLGA + LARGURA + MARGEM <= window.innerWidth;
    const cabeEsquerda = ancora.left - FOLGA - LARGURA >= MARGEM;
    const left = cabeDireita ? ancora.right + FOLGA : cabeEsquerda ? ancora.left - FOLGA - LARGURA : Math.max(MARGEM, window.innerWidth - LARGURA - MARGEM);
    const top = Math.max(MARGEM, Math.min(ancora.top, window.innerHeight - alt - MARGEM));
    setPos({ left, top });
  }, [ancora]);

  return createPortal(
    <div ref={ref} className="ficha" role="tooltip" style={{ width: LARGURA, left: pos?.left ?? -9999, top: pos?.top ?? 0, opacity: pos ? 1 : 0 }}>
      <p className="t-pequeno t-sec">{nomePlataforma(post.plataforma)} · {post.formato}{post.top && post.posicao_top ? ` · nº ${post.posicao_top} do top` : ""}</p>
      <p className="ficha-titulo corta-2">{post.titulo || post.gancho}</p>
      <p className="t-pequeno">{post.canal}{post.porte ? ` · perfil ${nomePorte(post.porte)}` : ""}</p>
      {post.vezes != null && <Etiqueta valor={fmtVezes(post.vezes)} rotulo="o esperado" />}
      <dl className="ficha-nums">
        <div><dt>ER</dt><dd>{fmtPct(post.er)}</dd></div>
        <div><dt>Curtidas</dt><dd>{fmtNum(post.likes)}</dd></div>
        <div><dt>Comentários</dt><dd>{fmtNum(post.comentarios)}</dd></div>
        {post.views != null && <div><dt>Views</dt><dd>{fmtNum(post.views)}</dd></div>}
      </dl>
      {(post.tema || post.tipo_gancho) && (
        <div className="linha" style={{ gap: 6 }}>
          {post.tema && <Chip rotulo="Tema">{post.tema}</Chip>}
          {post.tipo_gancho && <Chip rotulo="Gancho">{post.tipo_gancho}</Chip>}
        </div>
      )}
      {post.gancho && <p className="ficha-gancho corta-3">“{post.gancho}”</p>}
    </div>,
    document.body,
  );
}
