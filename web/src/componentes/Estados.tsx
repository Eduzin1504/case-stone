// Estados de tela: vazio, erro e carregando.
//   <Vazio titulo="Nada por aqui" acao={<Botao onClick={limpar}>Limpar filtros</Botao>}>Nenhum post bate com esses filtros.</Vazio>
//   <Erro erro={error} onTentar={refetch} />
//   <Esqueleto tipo="cards" n={8} />  ·  <Esqueleto tipo="linhas" n={5} />  ·  <Esqueleto altura={240} />
import type { ReactNode } from "react";
import { Botao } from "./Botao";

export function Vazio({ titulo, children, acao, marca = "0" }: { titulo: string; children?: ReactNode; acao?: ReactNode; marca?: string }) {
  return (
    <div className="vazio">
      <span className="vazio-marca" aria-hidden>{marca}</span>
      <div className="vazio-texto">
        <p className="t-titulo t-h2">{titulo}</p>
        {children && <p className="t-sec">{children}</p>}
        {acao && <div className="linha" style={{ marginTop: "var(--e3)" }}>{acao}</div>}
      </div>
    </div>
  );
}

export function Erro({ erro, onTentar, titulo = "Não deu certo" }: { erro?: unknown; onTentar?: () => void; titulo?: string }) {
  const msg = erro instanceof Error ? erro.message : typeof erro === "string" ? erro : "Algo deu errado ao carregar.";
  return (
    <div className="erro" role="alert">
      <span className="erro-marca" aria-hidden>×</span>
      <div className="vazio-texto">
        <p className="t-h3">{titulo}</p>
        <p>{msg}</p>
        {onTentar && <div style={{ marginTop: "var(--e3)" }}><Botao variante="contorno" tamanho="p" onClick={onTentar}>Tentar de novo</Botao></div>}
      </div>
    </div>
  );
}

type PropsEsq = { tipo?: "bloco" | "cards" | "linhas" | "texto"; n?: number; altura?: number | string; largura?: number | string };

export function Esqueleto({ tipo = "bloco", n = 1, altura = 120, largura = "100%" }: PropsEsq) {
  const rotulo = <span className="so-leitor">Carregando…</span>;
  if (tipo === "cards")
    return (
      <div className="mosaico" role="status">
        {rotulo}
        {Array.from({ length: n }, (_, i) => <div key={i} className={`esq esq--card${i % 5 === 0 ? " pc--alto" : ""}`} />)}
      </div>
    );
  if (tipo === "linhas" || tipo === "texto")
    return (
      <div className="pilha" style={{ gap: tipo === "texto" ? 10 : 12 }} role="status">
        {rotulo}
        {Array.from({ length: n }, (_, i) => <div key={i} className="esq" style={{ height: tipo === "texto" ? 14 : 56, width: tipo === "texto" ? `${92 - ((i * 17) % 40)}%` : "100%" }} />)}
      </div>
    );
  return <div className="esq" role="status" style={{ height: altura, width: largura }}>{rotulo}</div>;
}
