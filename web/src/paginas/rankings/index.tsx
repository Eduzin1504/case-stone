// /rankings: corrida de barras de posts e criadores. As linhas se reordenam (motion layout) ao trocar filtro ou métrica.
import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { AnimatePresence, LayoutGroup, motion } from "motion/react";
import { scaleLinear, scaleLog } from "d3-scale";
import { useRankings } from "../../api/hooks";
import type { ItemRanking, ParamsRanking } from "../../api/tipos";
import { Botao, BotaoExportar, Erro, Esqueleto, Miniatura, Seg, TituloPagina, Vazio, useLinkDoPost } from "../../componentes";
import { useFoco } from "../../contexto/Foco";
import { nomePlataforma, nomePorte } from "../../util/formato";
import { useEntrou } from "../../util/useEntrou";
import "./rankings.css";

type Tipo = ParamsRanking["tipo"];
type Metrica = NonNullable<ParamsRanking["metrica"]>;

const METRICAS: { valor: Metrica; rotulo: string }[] = [
  { valor: "vezes", rotulo: "× o esperado" },
  { valor: "er", rotulo: "Engajamento (ER)" },
  { valor: "comentarios", rotulo: "Comentários" },
];
const FRASE: Record<Metrica, string> = { vezes: "vezes o esperado", er: "engajamento (ER)", comentarios: "comentários" };
const EXPLICA: Record<Metrica, string> = {
  vezes: "quantas vezes o resultado passou do esperado para o tamanho do perfil",
  er: "curtidas e comentários divididos pelo alcance",
  comentarios: "total de comentários",
};
const NA_CORRIDA = 12;
const BUSCADOS = 50;

/** Largura da barra em % para cada item. Escala log quando a métrica é "× o esperado" ou quando o 1º esmagaria o resto. */
export function escalaBarras(valores: number[], forcarLog: boolean) {
  const pos = valores.filter((v) => v > 0);
  const max = Math.max(...pos, 0);
  const min = Math.min(...pos);
  if (!pos.length) return { log: false, largura: (_: number) => 0 };
  const log = (forcarLog || max / min > 25) && max > min;
  const s = log ? scaleLog().domain([min / 2, max]).range([6, 100]).clamp(true) : scaleLinear().domain([0, max]).range([0, 100]);
  return { log, largura: (v: number) => (v > 0 ? s(v) : 0) };
}

export default function Rankings() {
  const { info } = useFoco();
  const [tipo, setTipo] = useState<Tipo>("posts");
  const [metrica, setMetrica] = useState<Metrica>("vezes");
  const [plataforma, setPlataforma] = useState("");
  const [porte, setPorte] = useState("");
  const alvo = useRef<HTMLDivElement>(null);
  const entrou = useEntrou(alvo);
  const linkPost = useLinkDoPost();

  const { data, isLoading, error, refetch, isPlaceholderData } = useRankings({ tipo, metrica, plataforma: plataforma || undefined, porte: porte || undefined, limit: BUSCADOS });

  const duasPlataformas = !!info && info.base.por_plataforma.instagram > 0 && info.base.por_plataforma.youtube > 0;
  const itens = data ?? [];
  const corrida = itens.slice(0, NA_CORRIDA);
  const { log, largura } = escalaBarras(corrida.map((i) => i.valor), metrica === "vezes");
  const nomeMetrica = METRICAS.find((m) => m.valor === metrica)!.rotulo;
  const recorte = [tipo === "posts" ? "Posts" : "Criadores", FRASE[metrica], plataforma ? nomePlataforma(plataforma) : null, porte ? `perfil ${nomePorte(porte)}` : null].filter(Boolean).join(" · ");
  const limpar = () => { setPlataforma(""); setPorte(""); };

  return (
    <>
      <TituloPagina
        titulo="Corrida" grifo={tipo === "posts" ? "de posts" : "de criadores"}
        sub={`Quem está na frente em ${FRASE[metrica]}: ${EXPLICA[metrica]}. Troque a métrica ou o filtro e veja a fila se reordenar.`}
        acoes={<BotaoExportar alvo={alvo} nome={`ranking-${tipo}-${metrica}`} />}
      />

      <div className="rankings-controles nao-imprimir">
        <Seg rotulo="O que entra no ranking" valor={tipo} onChange={setTipo} opcoes={[{ valor: "posts", rotulo: "Posts" }, { valor: "criadores", rotulo: "Criadores" }]} />
        <Seg rotulo="Métrica" valor={metrica} onChange={setMetrica} opcoes={METRICAS} />
        {duasPlataformas && (
          <Seg rotulo="Plataforma" tamanho="p" valor={plataforma} onChange={setPlataforma} opcoes={[{ valor: "", rotulo: "Todas" }, { valor: "instagram", rotulo: "Instagram" }, { valor: "youtube", rotulo: "YouTube" }]} />
        )}
        <Seg rotulo="Tamanho do perfil" tamanho="p" valor={porte} onChange={setPorte} opcoes={[{ valor: "", rotulo: "Todo tamanho" }, { valor: "micro", rotulo: "Micro" }, { valor: "medio", rotulo: "Médio" }, { valor: "grande", rotulo: "Grande" }]} />
      </div>

      <div ref={alvo} className="rankings-pista" aria-busy={isPlaceholderData}>
      {isLoading ? <Esqueleto tipo="linhas" n={8} />
        : error ? <Erro erro={error} onTentar={refetch} />
        : !itens.length ? <Vazio titulo="Ninguém nesse recorte" acao={<Botao onClick={limpar}>Limpar filtros</Botao>}>Nenhum {tipo === "posts" ? "post" : "criador"} com essa combinação de plataforma e tamanho. Tire um dos filtros.</Vazio>
        : (
          <>
              <p className="rankings-recorte t-mono">{recorte} · {corrida.length} primeiros</p>
              <LayoutGroup>
                <ol className="rankings-lista">
                  <AnimatePresence mode="popLayout" initial={false}>
                    {corrida.map((item, i) => (
                      <motion.li
                        key={`${tipo}-${item.id}`} layout="position"
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
                        className={`rankings-item${i === 0 ? " rankings-item--1 bloco-lima" : i < 3 ? " rankings-item--podio" : ""}`}
                      >
                        <Linha item={item} tipo={tipo} thumbs={item.thumbs ?? []} largura={entrou ? largura(item.valor) : 0} para={tipo === "posts" ? linkPost(item.id) : `/criadores/${encodeURIComponent(item.id)}`} />
                      </motion.li>
                    ))}
                  </AnimatePresence>
                </ol>
              </LayoutGroup>
              {log && <p className="rankings-nota t-pequeno t-sec">Barras em escala comprimida (logarítmica): os primeiros estão tão à frente que, em escala comum, o resto sumiria. Compare pela ordem e pelo número, não pelo comprimento.</p>}
          </>
        )}
      </div>

      {itens.length > 0 && (
            <details className="rankings-numeros">
              <summary className="botao botao--contorno botao--m">Ver os números</summary>
              <table className="tabela">
                <caption className="so-leitor">{recorte}</caption>
                <thead><tr><th className="num">Posição</th><th>Criador</th><th>{tipo === "posts" ? "Post" : "Perfil"}</th><th className="num">{nomeMetrica}</th></tr></thead>
                <tbody>
                  {itens.map((i) => (
                    <tr key={i.id}>
                      <td className="num">{i.posicao}</td>
                      <td>{tipo === "criadores" ? <Link to={`/criadores/${encodeURIComponent(i.id)}`}>{i.nome}</Link> : i.nome}</td>
                      <td className="t-sec">{tipo === "posts" ? <Link to={linkPost(i.id)}>{i.sub}</Link> : i.sub}</td>
                      <td className="num">{i.valor_fmt}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </details>
      )}
    </>
  );
}

function Linha({ item, tipo, thumbs, largura, para }: { item: ItemRanking; tipo: Tipo; thumbs: string[]; largura: number; para: string }) {
  const fotos = thumbs.length ? thumbs : [item.thumb];
  return (
    <Link to={para} className="rankings-linha" aria-label={`${item.posicao}º, ${item.nome}, ${item.valor_fmt}. ${tipo === "posts" ? "Abrir o post" : "Ver o perfil"}`}>
      <span className="rankings-pos">{item.posicao}</span>
      <span className={`rankings-fotos${tipo === "criadores" ? " rankings-fotos--trio" : ""}`}>
        {fotos.map((t, k) => <span key={k} className="rankings-foto"><Miniatura src={t} alt="" reserva="" /></span>)}
      </span>
      <span className="rankings-corpo">
        <span className="rankings-nome corta-1">{item.nome}</span>
        <span className="rankings-sub corta-1">{item.sub}</span>
        <span className="rankings-trilho"><span className="rankings-barra" style={{ width: `${largura}%` }} /></span>
      </span>
      <span className="rankings-valor">{item.valor_fmt}</span>
    </Link>
  );
}
