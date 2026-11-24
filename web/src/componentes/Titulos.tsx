// Título de página e seção.
//   <TituloPagina titulo="Catálogo" grifo="do top" sub="250 posts que passaram do esperado." acoes={<BotaoExportar … />} />
//     → <h1> em Anton caixa alta; `grifo` é a parte que ganha o bloco lima (opcional).
//   <Secao titulo="Posts parecidos" sub="mesmo tema, formato ou gancho" acao={<Botao variante="fantasma" para="/catalogo">Ver todos →</Botao>}>…</Secao>
//   <Secao titulo="Curtida não é pedido" bloco="lima">…</Secao>   bloco: "lima" (um por dobra) | "afundado" | "superficie"
// Dentro de um bloco lima, textos, títulos e linhas trocam para floresta sozinhos.
import type { ReactNode } from "react";

export function TituloPagina({ titulo, grifo, sub, acoes }: { titulo: string; grifo?: string; sub?: ReactNode; acoes?: ReactNode }) {
  return (
    <header className="titulo-pagina">
      <div>
        <h1 className="t-titulo t-h1">
          {titulo}
          {grifo && <> <span className="grifo">{grifo}</span></>}
        </h1>
        {sub && <p className="titulo-pagina-sub">{sub}</p>}
      </div>
      {acoes && <div className="linha nao-imprimir">{acoes}</div>}
    </header>
  );
}

type PropsSecao = { titulo?: string; sub?: ReactNode; acao?: ReactNode; bloco?: "lima" | "afundado" | "superficie"; id?: string; className?: string; children: ReactNode };

export function Secao({ titulo, sub, acao, bloco, id, className = "", children }: PropsSecao) {
  return (
    <section id={id} className={`secao${bloco ? ` secao--bloco secao--${bloco}` : ""} ${className}`}>
      {(titulo || acao) && (
        <div className="secao-cab">
          <div>
            {titulo && <h2 className="t-titulo t-h2">{titulo}</h2>}
            {sub && <p className="t-sec t-pequeno">{sub}</p>}
          </div>
          {acao}
        </div>
      )}
      {children}
    </section>
  );
}
