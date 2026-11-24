// A visualização do resultado de uma avaliação. Serve para a avaliação recém-feita e para a aberta pelo histórico.
import { useRef, useState, type ReactNode } from "react";
import type { PadraoCasado, ResultadoAvaliacao } from "../../api/tipos";
import { BotaoExportar, Carimbo, Comprovante, Miniatura, NumeroConta, PostCard, Secao, Selo } from "../../componentes";
import { fmtData, fmtInt, fmtVezes, nomePlataforma, semTravessao } from "../../util/formato";
import { useEntrou } from "../../util/useEntrou";

const METODOS: Record<string, string> = {
  video_gemini: "vídeo inteiro, com áudio",
  quadros_deepseek: "quadros do vídeo, sem áudio",
  imagens_deepseek: "imagens do post",
  texto_deepseek: "só o texto",
};
export const nomeMetodo = (m: string | null | undefined) => (m ? METODOS[m] ?? m.replace(/_/g, " ") : "–");
export const dataHora = (iso: string | null | undefined) => (iso ? `${fmtData(iso)}${iso.length > 15 ? ` ${iso.slice(11, 16)}` : ""}` : "–");

function Medidor({ nota, medias }: { nota: number; medias: ResultadoAvaliacao["medias"] | undefined }) {
  const ref = useRef<HTMLDivElement>(null);
  const entrou = useEntrou(ref);
  const marca = (v: number | null | undefined, nome: string, lado: "cima" | "baixo") =>
    v != null && (
      <span className={`avaliar-marca avaliar-marca--${lado}${v > 50 ? " avaliar-marca--dir" : ""}`} style={{ left: `${Math.max(0, Math.min(100, v))}%` }}>
        <i />
        <span>{nome} <b>{fmtInt(v)}</b></span>
      </span>
    );
  return (
    <div
      ref={ref} className="avaliar-medidor" role="img"
      aria-label={`Nota ${fmtInt(nota)} de 100. Média dos posts comuns: ${fmtInt(medias?.comuns)}. Média do top: ${fmtInt(medias?.top)}.`}
    >
      <div className="avaliar-trilho">
        <span className="avaliar-enche" style={{ width: entrou ? `${Math.max(0, Math.min(100, nota))}%` : 0 }} />
      </div>
      {marca(medias?.comuns, "média dos comuns", "baixo")}
      {marca(medias?.top, "média do top", "cima")}
    </div>
  );
}

function ListaPadroes({ titulo, itens, vazio }: { titulo: string; itens: PadraoCasado[]; vazio: string }) {
  const [todos, setTodos] = useState(false);
  const LIMITE = 6;
  const visiveis = todos ? itens : itens.slice(0, LIMITE);
  return (
    <div className="avaliar-padroes-col">
      <h3 className="t-h3">{titulo} <span className="t-sec">({itens.length})</span></h3>
      {itens.length === 0 && <p className="t-sec">{vazio}</p>}
      <ul>
        {visiveis.map((p) => {
          const mais = p.lift >= 1;
          return (
            <li key={p.campo + p.valor} className="avaliar-padrao">
              <span className="avaliar-padrao-nome">{p.rotulo}{p.fragil && <> <Selo tipo="frágil" /></>}</span>
              <span className={`avaliar-padrao-efeito${mais ? "" : " avaliar-padrao-efeito--menos"}`}>
                <span>{mais ? "aparece mais no top" : "aparece menos no top"}</span>
                <b>{fmtVezes(p.lift)}</b>
              </span>
            </li>
          );
        })}
      </ul>
      {itens.length > LIMITE && (
        <button type="button" className="avaliar-mais" onClick={() => setTodos(!todos)} aria-expanded={todos}>
          {todos ? "Mostrar menos" : `Mostrar todos (${itens.length})`}
        </button>
      )}
    </div>
  );
}

function BarraNota({ rotulo, valor, mediana }: { rotulo: string; valor: number; mediana: number | null }) {
  const ref = useRef<HTMLDivElement>(null);
  const entrou = useEntrou(ref);
  return (
    <div ref={ref} className="avaliar-vs">
      <span className="avaliar-vs-rotulo">{rotulo}</span>
      <span className="avaliar-vs-valor t-num">{fmtInt(valor)}</span>
      <div className="avaliar-vs-trilho" role="img" aria-label={`${rotulo}: você ${fmtInt(valor)}; mediana do top ${mediana == null ? "sem dado" : fmtInt(mediana)}; escala de 0 a 10`}>
        <span className="avaliar-vs-enche" style={{ width: entrou ? `${Math.min(100, valor * 10)}%` : 0 }} />
        {mediana != null && <i className="avaliar-vs-marca" style={{ left: `${Math.min(100, mediana * 10)}%` }} />}
      </div>
      <span className="avaliar-vs-top t-pequeno t-sec">top {mediana == null ? "–" : fmtInt(mediana)}</span>
    </div>
  );
}

type Props = { resultado: ResultadoAvaliacao; thumb?: string | null; criadaEm?: string | null; acoes?: ReactNode };

export function Resultado({ resultado: r, thumb, criadaEm, acoes }: Props) {
  const alvo = useRef<HTMLDivElement>(null);
  const { top, comuns } = r.medias ?? { top: null, comuns: null };
  const faixa = top != null && r.nota >= top ? "top" : comuns != null && r.nota >= comuns ? "caminho" : "abaixo";
  const peso = (p: PadraoCasado) => Math.abs(Math.log(p.lift || 1));
  const ordenados = [...(r.padroes ?? [])].sort((a, b) => peso(b) - peso(a));
  const tem = ordenados.filter((p) => p.tem), naoTem = ordenados.filter((p) => !p.tem);
  const recs = (r.recomendacoes ?? []).map(semTravessao); // texto do modelo: sem travessão na tela

  return (
    <div ref={alvo} className="avaliar-resultado">
      <section className={`avaliar-hero bloco-lima avaliar-hero--${faixa}`}>
        <div className="avaliar-hero-nota">
          {thumb && <span className="avaliar-hero-thumb"><Miniatura src={thumb} alt="O que você enviou" /></span>}
          <div>
            <p className="t-h3">Sua nota</p>
            <p className="avaliar-nota t-titulo"><NumeroConta valor={r.nota} formato={fmtInt} /><span>/100</span></p>
          </div>
          {faixa === "top" && <Carimbo texto="Na faixa" sub="do top" tamanho={118} giro={-8} />}
          {faixa === "caminho" && <Carimbo texto="No caminho" tamanho={118} giro={7} />}
        </div>
        <div className="avaliar-hero-lado">
          <p className="avaliar-honesto">
            A nota mede o quanto o post se parece com o top da base. Não prevê resultado.
            {top != null && <> Um post do top costuma ficar perto da média do top ({fmtInt(top)}), não de 100.</>}
          </p>
          {r.nota_explicacao && (
            <details className="avaliar-conta">
              <summary>Como a nota é calculada</summary>
              <p>{semTravessao(r.nota_explicacao)}</p>
            </details>
          )}
        </div>
        <Medidor nota={r.nota} medias={r.medias} />
      </section>

      <div className="linha nao-imprimir" data-nao-exportar>
        {acoes}
        <BotaoExportar alvo={alvo} nome={`avaliacao-nota-${fmtInt(r.nota)}`} tamanho="m" />
      </div>

      {recs.length > 0 && (
        <Secao titulo="O que mudar" sub="Escritas a partir da leitura do seu post e dos padrões do top. Comece pela primeira.">
          <ol className="avaliar-recs">
            {recs.map((t, i) => (
              <li key={i} className="avaliar-rec">
                <span className="avaliar-rec-n" aria-hidden>{i + 1}</span>
                <p>{t}</p>
              </li>
            ))}
          </ol>
        </Secao>
      )}

      {ordenados.length > 0 && (
        <Secao titulo="Padrões do top no seu post" sub="O multiplicador diz quantas vezes a característica aparece mais (ou menos) no top que nos posts comuns. É uma comparação, não uma receita.">
          <div className="avaliar-padroes">
            <ListaPadroes titulo="Seu post tem" itens={tem} vazio="Nenhum dos padrões medidos apareceu no seu post." />
            <ListaPadroes titulo="Seu post não tem" itens={naoTem} vazio="Seu post tem todos os padrões medidos." />
          </div>
        </Secao>
      )}

      <div className="avaliar-fecho">
        {(r.notas_vs_top ?? []).length > 0 && (
          <Secao titulo="Você × mediana do top" sub="Notas de 0 a 10 dadas pela leitura. O traço marca a mediana dos posts do top." bloco="superficie">
            <div>
              {r.notas_vs_top.map((n) => <BarraNota key={n.campo} rotulo={n.rotulo} valor={n.valor} mediana={n.mediana_top} />)}
            </div>
          </Secao>
        )}
        <Comprovante
          titulo="Avaliação" sub={`Foco ${r.foco} · ${nomePlataforma(r.plataforma)}`}
          linhas={[
            { rotulo: "Leitura", valor: nomeMetodo(r.metodo) },
            { rotulo: "Padrões que tem", valor: fmtInt(tem.length) },
            { rotulo: "Padrões que não tem", valor: fmtInt(naoTem.length) },
            { rotulo: "Média dos comuns", valor: fmtInt(comuns) },
            { rotulo: "Média do top", valor: fmtInt(top) },
          ]}
          total={{ rotulo: "Nota", valor: fmtInt(r.nota) }}
          rodape={<>{criadaEm ? <>{dataHora(criadaEm)}<br /></> : null}mede semelhança com o top; não prevê resultado</>}
        >
          {r.aviso ? <p>Aviso: {r.aviso}.</p> : null}
        </Comprovante>
      </div>

      {(r.parecidos ?? []).length > 0 && (
        <Secao titulo="Posts do top parecidos" sub="Os mais próximos do seu na base. Clique para ver o post e a leitura completa.">
          <ul className="avaliar-parecidos">
            {r.parecidos.map((p) => (
              <li key={p.video_id}>
                {p.post
                  ? <PostCard post={p.post} variante="compacto" />
                  : <a className="avaliar-parecido-fora" href={p.url} target="_blank" rel="noreferrer">{p.canal}: {p.titulo} ↗</a>}
                <p className="t-pequeno t-sec">{semTravessao(p.motivo)}</p>
              </li>
            ))}
          </ul>
        </Secao>
      )}
    </div>
  );
}
