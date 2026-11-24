// Funil curtida → pedido (só Foco B): etapas em escala comprimida, intenção por formato, com preço × sem preço e comentários reais.
import { useRef } from "react";
import { scaleLog } from "d3-scale";
import { useFunil } from "../../api/hooks";
import type { VizFunil } from "../../api/tipos";
import { Botao, Erro, Esqueleto, NumeroConta, Secao, Selo, Vazio } from "../../componentes";
import { useFoco } from "../../contexto/Foco";
import { fmtInt, fmtPct, fmtVezes } from "../../util/formato";
import { useEntrou } from "../../util/useEntrou";

const LINHA = 84;

function Etapas({ etapas }: { etapas: VizFunil["etapas"] }) {
  const ref = useRef<HTMLDivElement>(null);
  const entrou = useEntrou(ref);
  const vals = etapas.map((e) => Math.max(1, e.valor));
  // largura em escala log: em escala linear a última etapa teria 0,03% da primeira e sumiria
  const larg = scaleLog().domain([Math.min(...vals) / 4, Math.max(...vals)]).range([0, 100]);
  const meia = (i: number) => larg(vals[Math.min(i, vals.length - 1)]) / 2;
  return (
    <div ref={ref} className="mapa-funil">
      <svg className="mapa-funil-svg" viewBox={`0 0 100 ${LINHA * etapas.length}`} preserveAspectRatio="none" aria-hidden style={{ height: LINHA * etapas.length }}>
        {etapas.map((e, i) => {
          const a = meia(i), b = meia(i + 1), y = i * LINHA;
          return (
            <polygon
              key={e.rotulo} className={`mapa-funil-etapa${i === etapas.length - 1 ? " mapa-funil-etapa--fim" : ""}`}
              points={`${50 - a},${y} ${50 + a},${y} ${50 + b},${y + LINHA - 4} ${50 - b},${y + LINHA - 4}`}
              style={{ opacity: entrou ? 1 : 0, transitionDelay: `${i * 140}ms` }}
            />
          );
        })}
      </svg>
      <ol className="mapa-funil-rotulos">
        {etapas.map((e, i) => (
          <li key={e.rotulo} style={{ height: LINHA }}>
            <span className="t-num">{fmtInt(e.valor)}</span>
            <span>
              <b>{e.rotulo}</b>
              {i > 0 && etapas[i - 1].valor > 0 && <span className="t-sec t-pequeno"> · {fmtPct(e.valor / etapas[i - 1].valor)} da etapa anterior</span>}
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}

function Formatos({ itens }: { itens: VizFunil["por_formato"] }) {
  const ref = useRef<HTMLUListElement>(null);
  const entrou = useEntrou(ref);
  const max = Math.max(...itens.map((f) => f.pct_intencao), 0.01);
  return (
    <ul ref={ref} className="mapa-formatos">
      {itens.map((f) => (
        <li key={f.formato} className={f.n < 5 ? "mapa-formato mapa-formato--fragil" : "mapa-formato"}>
          <span className="mapa-formato-nome">{f.formato} <span className="t-sec t-pequeno">{f.n} {f.n === 1 ? "post" : "posts"}</span>{f.n < 5 && <Selo tipo="frágil" />}</span>
          <span className="mapa-formato-trilho" role="img" aria-label={`${fmtPct(f.pct_intencao)} dos comentários com intenção de compra`}>
            <i style={{ width: `${(f.pct_intencao / max) * 100}%`, transform: `scaleX(${entrou ? 1 : 0})` }} />
          </span>
          <span className="mapa-formato-num">{fmtPct(f.pct_intencao)}</span>
        </li>
      ))}
    </ul>
  );
}

export function Funil() {
  const { foco, setFoco } = useFoco();
  const { data, isLoading, error, refetch } = useFunil();

  if (foco !== "B")
    return (
      <Vazio titulo="O funil é do outro foco" marca="B" acao={<Botao variante="lima" onClick={() => setFoco("B")}>Trocar para Negócio → cliente</Botao>}>
        Curtida não é pedido: esta visualização mede intenção de compra nos comentários dos clientes de pequenos negócios. Essa leitura só foi feita na base do foco Negócio → cliente.
      </Vazio>
    );
  if (isLoading) return <Esqueleto altura={460} />;
  if (error) return <Erro erro={error} onTentar={refetch} />;
  if (!data || !data.etapas.length) return <Vazio titulo="Sem dados do funil">Os comentários deste foco ainda não foram lidos.</Vazio>;

  const { preco } = data;
  const [primeira, ultima] = [data.etapas[0], data.etapas[data.etapas.length - 1]];
  const razao = preco.com != null && preco.sem ? preco.com / preco.sem : null;
  const pouco = Math.min(preco.n_com ?? 0, preco.n_sem ?? 0) < 30;
  return (
    <>
      <Secao titulo={`De ${fmtInt(primeira.valor)} curtidas, ${fmtInt(ultima.valor)} comentários de quem quer comprar`} sub="Cada degrau é uma etapa mais perto do pedido. A largura está em escala comprimida (logarítmica) para o último degrau não sumir; os números escritos são os reais.">
        <Etapas etapas={data.etapas} />
      </Secao>

      {preco.com != null && preco.sem != null && (
        <Secao bloco="lima" titulo="Mostrar o preço muda a conversa" sub="Fatia dos comentários que perguntam preço, endereço, entrega ou dizem que querem.">
          <div className="mapa-preco">
            <div>
              <p className="t-titulo t-mega"><NumeroConta valor={preco.com} formato={fmtPct} /></p>
              <p className="t-h3">com preço no post</p>
              <p className="t-sec t-pequeno">{preco.n_com} posts</p>
            </div>
            <span className="mapa-preco-x" aria-hidden>×</span>
            <div>
              <p className="t-titulo t-mega mapa-preco-sem"><NumeroConta valor={preco.sem} formato={fmtPct} /></p>
              <p className="t-h3">sem preço</p>
              <p className="t-sec t-pequeno">{preco.n_sem} posts</p>
            </div>
            <div className="mapa-preco-aviso">
              {razao && <p className="t-h3">{fmtVezes(razao)} mais intenção de compra quando o preço aparece.</p>}
              {pouco && <p><Selo tipo="frágil" /> Amostra pequena: só {preco.n_com} posts mostram o preço. É um indício para testar, não uma regra.</p>}
            </div>
          </div>
        </Secao>
      )}

      {data.por_formato.length > 0 && (
        <Secao titulo="Intenção de compra por formato" sub="Fatia dos comentários com intenção de compra, em cada formato de post. Formato com menos de 5 posts fica marcado como frágil.">
          <Formatos itens={[...data.por_formato].sort((a, b) => b.pct_intencao - a.pct_intencao)} />
        </Secao>
      )}

      {data.comentarios.length > 0 && (
        <Secao titulo="Como soa um pedido" sub="Comentários reais de clientes, como foram escritos.">
          <div className="mapa-citacoes">
            {data.comentarios.slice(0, 4).map((c) => (
              <figure key={c.texto} className="mapa-citacao">
                <blockquote>“{c.texto}”</blockquote>
                <figcaption>{c.negocio}{c.segmento ? ` · ${c.segmento}` : ""}</figcaption>
              </figure>
            ))}
          </div>
        </Secao>
      )}
      {data.nota && <p className="t-pequeno t-sec mapa-nota">{data.nota}</p>}
    </>
  );
}
