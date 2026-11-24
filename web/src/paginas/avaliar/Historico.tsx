// /avaliar/historico: lista das avaliações salvas, linha de evolução da nota e a avaliação aberta (?id=).
import { useRef } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAvaliacaoSalva, useAvaliacoes } from "../../api/hooks";
import type { AvaliacaoSalva } from "../../api/tipos";
import { Botao, Erro, Esqueleto, Miniatura, Secao, TituloPagina, Vazio } from "../../componentes";
import { useFoco } from "../../contexto/Foco";
import { fmtInt, nomePlataforma } from "../../util/formato";
import { useEntrou } from "../../util/useEntrou";
import { Resultado, dataHora, nomeMetodo } from "./Resultado";

function Evolucao({ itens, foco }: { itens: AvaliacaoSalva[]; foco: string }) {
  const ref = useRef<SVGSVGElement>(null);
  const entrou = useEntrou(ref);
  const L = 640, A = 150, m = 26;
  const x = (i: number) => m + (i * (L - 2 * m)) / (itens.length - 1);
  // escala ajustada às notas (não começa em zero): a linha mostra a variação; os números estão em cada ponto
  const notas = itens.map((a) => a.nota ?? 0), lo = Math.min(...notas) - 6, hi = Math.max(...notas) + 6;
  const y = (n: number) => A - m - ((n - lo) / (hi - lo)) * (A - 2 * m);
  const pts = itens.map((a, i) => [x(i), y(a.nota ?? 0)] as const);
  const primeira = itens[0].nota ?? 0, ultima = itens[itens.length - 1].nota ?? 0;
  const dif = ultima - primeira;
  return (
    <div className="avaliar-evolucao">
      <div>
        <p className="t-titulo avaliar-evolucao-num">{dif > 0 ? "+" : dif < 0 ? "−" : ""}{fmtInt(Math.abs(dif))}</p>
        <p className="t-sec t-pequeno">pontos entre a primeira e a última das {itens.length} avaliações do Foco {foco}</p>
      </div>
      <svg ref={ref} viewBox={`0 0 ${L} ${A}`} role="img" aria-label={`Evolução da nota no Foco ${foco}: ${itens.map((a) => fmtInt(a.nota)).join(", ")}`}>
        <polyline
          points={pts.map((p) => p.join(",")).join(" ")} pathLength={1} className="avaliar-evolucao-linha"
          style={{ strokeDasharray: 1, strokeDashoffset: entrou ? 0 : 1 }}
        />
        {pts.map(([px, py], i) => (
          <g key={itens[i].id}>
            <circle cx={px} cy={py} r={i === pts.length - 1 ? 7 : 4.5} className="avaliar-evolucao-ponto" />
            <text x={px} y={py - 12} textAnchor="middle" className="avaliar-evolucao-rotulo">{fmtInt(itens[i].nota)}</text>
          </g>
        ))}
      </svg>
    </div>
  );
}

function Aberta({ id }: { id: string }) {
  const { data, isLoading, error, refetch } = useAvaliacaoSalva(id);
  const voltar = <Botao variante="contorno" para="/avaliar/historico">← Histórico</Botao>;
  return (
    <>
      <TituloPagina
        titulo="Avaliação" grifo="salva"
        sub={data ? <>{dataHora(data.criada_em)} · Foco {data.foco} · {nomePlataforma(data.plataforma)}{data.legenda ? <> · “{data.legenda.slice(0, 90)}{data.legenda.length > 90 ? "…" : ""}”</> : null}</> : undefined}
      />
      {isLoading && <Esqueleto altura={320} />}
      {error && <><Erro erro={error} onTentar={refetch} />{voltar}</>}
      {data && !data.resultado && (
        <Vazio titulo="Sem resultado guardado" marca="?" acao={<>{voltar}<Botao para="/avaliar">Avaliar outro</Botao></>}>
          {data.estado === "rodando" ? "Esta avaliação ainda está rodando." : "Esta avaliação não terminou, então não há nota para mostrar."}
        </Vazio>
      )}
      {data?.resultado && (
        <Resultado
          resultado={data.resultado} thumb={data.thumb} criadaEm={data.criada_em}
          acoes={<>{voltar}<Botao para="/avaliar">Avaliar outro</Botao></>}
        />
      )}
    </>
  );
}

export function Historico() {
  const [q] = useSearchParams();
  const id = q.get("id");
  const { foco } = useFoco();
  const { data, isLoading, error, refetch } = useAvaliacoes();
  if (id) return <Aberta id={id} />;

  const itens = data ?? [];
  const serie = itens.filter((a) => a.foco === foco && a.nota != null).sort((a, b) => a.criada_em.localeCompare(b.criada_em));
  return (
    <>
      <TituloPagina
        titulo="Histórico" grifo="das avaliações"
        sub="Tudo que você já avaliou, nos dois focos. Clique para reabrir o resultado."
        acoes={<Botao para="/avaliar">Avaliar um post</Botao>}
      />
      {isLoading && <Esqueleto tipo="linhas" n={4} />}
      {error && <Erro erro={error} onTentar={refetch} />}
      {data && itens.length === 0 && (
        <Vazio titulo="Nenhuma avaliação ainda" acao={<Botao para="/avaliar">Avaliar meu post</Botao>}>
          Envie um vídeo, imagens ou só o roteiro. A nota e as recomendações ficam guardadas aqui.
        </Vazio>
      )}
      {serie.length >= 2 && <Evolucao itens={serie} foco={foco} />}
      {itens.length > 0 && (
        <Secao>
          <ul className="avaliar-hist">
            {itens.map((a) => (
              <li key={a.id}>
                <Link className="avaliar-hist-item" to={a.estado === "rodando" ? `/avaliar?job=${a.id}` : `/avaliar/historico?id=${a.id}`}>
                  <span className="avaliar-hist-thumb"><Miniatura src={a.thumb} alt="" reserva="texto" /></span>
                  <span className="avaliar-hist-corpo">
                    <span className="avaliar-hist-legenda corta-2">{a.legenda || "Sem legenda"}</span>
                    <span className="t-pequeno t-sec">{dataHora(a.criada_em)} · {nomePlataforma(a.plataforma)}{a.metodo ? ` · ${nomeMetodo(a.metodo)}` : ""}</span>
                  </span>
                  <span className={`avaliar-hist-foco${a.foco === foco ? " avaliar-hist-foco--atual" : ""}`}>Foco {a.foco}</span>
                  <span className="avaliar-hist-nota t-titulo">
                    {a.nota != null ? fmtInt(a.nota) : a.estado === "rodando" ? "…" : "×"}
                    <span className="so-leitor">{a.nota != null ? " de 100" : a.estado === "rodando" ? "rodando" : "não terminou"}</span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </Secao>
      )}
    </>
  );
}
