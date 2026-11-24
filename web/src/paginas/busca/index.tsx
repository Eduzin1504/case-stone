// Busca por ideia (P1): descreva a ideia ou cole um texto; a API devolve os posts mais parecidos, as palavras que casaram
// e a força do casamento (0 a 1). A consulta fica na URL (?q=).
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { useBusca } from "../../api/hooks";
import type { Foco, ResultadoBusca } from "../../api/tipos";
import { Botao, Campo, Chip, Erro, Esqueleto, PostCard, TituloPagina, Vazio } from "../../componentes";
import { useFoco } from "../../contexto/Foco";
import { fmtPct } from "../../util/formato";
import { useEntrou } from "../../util/useEntrou";
import "./busca.css";

// consultas conferidas na API: todas devolvem resultado no foco correspondente
const EXEMPLOS: Record<Foco, string[]> = {
  A: ["como precificar", "pix na maquininha", "black friday loja", "fluxo de caixa", "separar dinheiro da casa e do negócio"],
  B: ["bolo de aniversário", "promoção de banho e tosa", "corte de cabelo", "marmita fitness", "unhas decoradas"],
};

/** Por que casou: barra com a força (0 a 1) e as palavras da consulta encontradas no post. */
function Casamento({ r }: { r: ResultadoBusca }) {
  const ref = useRef<HTMLDivElement>(null);
  const entrou = useEntrou(ref);
  return (
    <div className="busca-casou" ref={ref}>
      <span className="busca-forca" role="img" aria-label={`Força do casamento: ${fmtPct(r.score)}`}>
        <span className="busca-forca-barra" style={{ width: `${Math.min(r.score, 1) * 100}%`, transform: entrou ? "none" : "scaleX(0)" }} />
      </span>
      <b className="busca-forca-num" aria-hidden>{fmtPct(r.score)}</b>
      {r.casou.length > 0 && (
        <span className="busca-palavras">
          <span className="t-sec">casou em</span>
          {r.casou.map((c) => <mark key={c}>{c}</mark>)}
        </span>
      )}
    </div>
  );
}

export default function Busca() {
  const { foco } = useFoco();
  const [params, setParams] = useSearchParams();
  const q = params.get("q") ?? "";
  const [texto, setTexto] = useState(q);
  useEffect(() => setTexto(q), [q]);
  const buscar = (valor: string) =>
    setParams((p) => {
      const n = new URLSearchParams(p);
      if (valor.trim()) n.set("q", valor.trim());
      else n.delete("q");
      return n;
    });
  const enviar = (e: FormEvent) => { e.preventDefault(); buscar(texto); };

  const curta = q.trim().length > 0 && q.trim().length < 2;
  const soTop = params.get("top") === "1";
  const alternarTop = () => setParams((p) => { const n = new URLSearchParams(p); if (soTop) n.delete("top"); else n.set("top", "1"); return n; });
  const { data, isLoading, error, refetch } = useBusca(q, 24, soTop);
  const exemplos = EXEMPLOS[foco];
  const primeiros = data?.slice(0, 4) ?? [];
  const resto = data?.slice(4) ?? [];

  return (
    <>
      <TituloPagina titulo="Busca" grifo="por ideia" sub="Escreva o assunto do post que você quer fazer. A busca traz o que já foi publicado sobre ele e como se saiu." />

      <form className="busca-form" onSubmit={enviar} role="search">
        <Campo className="busca-campo" rotulo="Descreva a ideia ou cole um texto" esconderRotulo tamanho="g" type="search" autoFocus={!q}
          placeholder="Descreva a ideia ou cole um texto" value={texto} onChange={(e) => setTexto(e.target.value)} />
        <Botao type="submit" tamanho="g">Buscar</Botao>
      </form>

      {!q && (
        <section className="busca-exemplos bloco-lima" aria-label="Exemplos de busca">
          <p className="t-h3">Sem ideia de por onde começar? Tente uma destas.</p>
          <ul>
            {exemplos.map((ex) => (
              <li key={ex}>
                <button type="button" onClick={() => buscar(ex)}><span>{ex}</span><span aria-hidden>→</span></button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {q && (
        <div className="linha busca-chips">
          <Chip ativo={soTop} onClick={alternarTop}>Só o top</Chip>
          <span className="t-sec t-pequeno">Outras ideias</span>
          {exemplos.filter((ex) => ex !== q).map((ex) => <Chip key={ex} onClick={() => buscar(ex)}>{ex}</Chip>)}
        </div>
      )}

      {curta && <Vazio titulo="Escreva um pouco mais" marca="?">A busca precisa de pelo menos duas letras.</Vazio>}
      {isLoading && <Esqueleto tipo="linhas" n={6} />}
      {error && <Erro erro={error} onTentar={refetch} />}

      {data?.length === 0 && (
        <Vazio titulo={soTop ? "Nada parecido no top" : "Nada parecido na base"} acao={soTop ? <Botao variante="contorno" tamanho="p" onClick={alternarTop}>Buscar em todos os posts</Botao> : exemplos.slice(0, 3).map((ex) => <Botao key={ex} variante="contorno" tamanho="p" onClick={() => buscar(ex)}>{ex}</Botao>)}>
          Nenhum post deste foco fala de “{q}”. Use menos palavras, troque por um sinônimo ou escreva o assunto em vez da frase inteira. Ou comece por um exemplo.
        </Vazio>
      )}

      {data && data.length > 0 && (
        <section className="busca-resultados" aria-label="Resultados">
          <p className="busca-conta" aria-live="polite">
            <b>{data.length}</b> {data.length === 1 ? "post parecido" : "posts mais parecidos"} com “{q}”
            {soTop ? " no top" : ` · ${data.filter((r) => r.post.top).length} do top`}
          </p>
          <ul className="busca-primeiros">
            {primeiros.map((r, i) => (
              <li key={r.post.id}>
                <span className="busca-posicao" aria-hidden>{i + 1}</span>
                <PostCard post={r.post} variante="compacto" />
                <Casamento r={r} />
              </li>
            ))}
          </ul>
          {resto.length > 0 && (
            <ul className="busca-lista">
              {resto.map((r, i) => (
                <li key={r.post.id}>
                  <PostCard post={r.post} variante="linha" posicao={i + 5} />
                  <Casamento r={r} />
                </li>
              ))}
            </ul>
          )}
          <p className="t-sec t-pequeno">
            A força vai de 0 a 100%: quanto do texto do post tem a ver com as palavras da busca. A lista vem do mais parecido para o menos; entre posts de força próxima, os do top aparecem antes.
          </p>
        </section>
      )}
    </>
  );
}
