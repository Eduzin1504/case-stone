// Anatomia de um post do top: os trechos (gancho, o que explica a atenção, chamada para ação) numa faixa de tempo, com a mídia ao lado.
// Vídeo: faixa em SVG com eixo de tempo. Imagem e carrossel (sem duração): os trechos em sequência, sem eixo.
import { useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { scaleLinear } from "d3-scale";
import { useAnatomia, useBusca, useDestaques, usePost } from "../../api/hooks";
import type { PostResumo, TrechoAnatomia, VizAnatomia } from "../../api/tipos";
import { Botao, Campo, Erro, Esqueleto, Etiqueta, Midia, Miniatura, MolduraCelular, Secao, Vazio, useAbrirPost } from "../../componentes";
import { fmtPct, fmtVezes, nomePlataforma } from "../../util/formato";
import { useEntrou } from "../../util/useEntrou";
import { useLargura } from "./useLargura";

type Trecho = TrechoAnatomia;
const seg = (s: number) => `${Math.round(s)} s`;

function Faixa({ trechos, duracao }: { trechos: Trecho[]; duracao: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const W = useLargura(ref);
  const entrou = useEntrou(ref);
  const x = scaleLinear().domain([0, duracao]).range([0, W]);
  const marcas = [...new Set([0, ...trechos.flatMap((t) => [t.inicio_s ?? 0, t.fim_s ?? duracao]), duracao])].sort((a, b) => a - b);
  // rótulos de tempo colados demais somem (o último sempre fica)
  const visiveis = marcas.filter((t, i) => i === marcas.length - 1 || (x(marcas[i + 1]) - x(t) > 30 && x(duracao) - x(t) > 52));
  return (
    <div ref={ref} className="mapa-faixa">
      {W > 0 && (
        <svg width={W} height={96} role="img" aria-label={`Faixa de tempo de ${seg(duracao)}: ${trechos.map((t, i) => `${i + 1}. ${t.rotulo}, de ${seg(t.inicio_s ?? 0)} a ${seg(t.fim_s ?? duracao)}${t.aproximado ? " (aproximado)" : ""}`).join("; ")}`}>
          <defs>
            <pattern id="mapa-hachura" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <rect className="mapa-hachura-fundo" width="7" height="7" />
              <line className="mapa-hachura-risco" x1="0" y1="0" x2="0" y2="7" />
            </pattern>
          </defs>
          <g className="mapa-faixa-anima" style={{ transform: `scaleX(${entrou ? 1 : 0})` }}>
            {trechos.map((t, i) => {
              const x0 = x(t.inicio_s ?? 0), x1 = x(t.fim_s ?? duracao);
              return <rect key={i} className={t.aproximado ? "mapa-trecho mapa-trecho--aprox" : "mapa-trecho"} x={x0 + 1} y={26} width={Math.max(3, x1 - x0 - 2)} height={44} />;
            })}
          </g>
          {trechos.map((t, i) => <text key={i} className="mapa-faixa-num" x={Math.min(W - 12, x(t.inicio_s ?? 0) + 1)} y={18}>{i + 1}</text>)}
          {visiveis.map((t) => <text key={t} className="mapa-eixo" x={x(t)} y={90} textAnchor={t === 0 ? "start" : t === duracao ? "end" : "middle"}>{seg(t)}</text>)}
        </svg>
      )}
    </div>
  );
}

function Cartao({ t, n, comTempo }: { t: Trecho; n: number; comTempo: boolean }) {
  const semCta = /chamada/i.test(t.rotulo) && /^(nenhum|nenhuma|não|nao)?$/i.test(t.texto.trim());
  // sem duração (imagem/carrossel) não existem "3 primeiros segundos"
  const rotulo = comTempo ? t.rotulo : t.rotulo.replace(/, nos \d+ primeiros segundos/, "");
  return (
    <li className={`mapa-cartao${t.aproximado ? " mapa-cartao--aprox" : ""}`}>
      <span className="mapa-cartao-num" aria-hidden>{n}</span>
      <div className="mapa-cartao-corpo">
        <p className="t-h3">{rotulo}</p>
        <p className="t-mono t-sec">
          {comTempo && t.inicio_s != null && t.fim_s != null && <span className="mapa-tempo">{seg(t.inicio_s)} a {seg(t.fim_s)}</span>}
          {t.aproximado && <span className="mapa-aprox">aproximado</span>}
        </p>
        {semCta ? <p className="t-sec">Este post não pede nada a quem assiste.</p>
          : t.itens?.length ? <ul className="mapa-cartao-itens">{t.itens.map((x) => <li key={x}>{x}</li>)}</ul>
          : <p className="mapa-cartao-fala">{n === 1 ? `“${t.texto}”` : /chamada/i.test(t.rotulo) ? `Pede para: ${t.texto}` : t.texto}</p>}
      </div>
    </li>
  );
}

function Escolha({ posts, atual, onEscolher }: { posts: PostResumo[]; atual: string | null; onEscolher: (id: string) => void }) {
  return (
    <ul className="mapa-escolha">
      {posts.map((p) => (
        <li key={p.id}>
          <button type="button" className="mapa-escolha-op" aria-pressed={p.id === atual} onClick={() => onEscolher(p.id)}>
            <span className="mapa-escolha-thumb"><Miniatura src={p.thumb} alt="" reserva={nomePlataforma(p.plataforma)} /></span>
            <span className="mapa-escolha-texto">
              <b className="corta-1">{p.canal}</b>
              <span className="t-sec">{p.formato} · {fmtVezes(p.vezes)}</span>
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}

function Corpo({ a }: { a: VizAnatomia & { nota?: string } }) {
  const { data: detalhe } = usePost(a.post.id);
  const abrir = useAbrirPost();
  const trechos = a.trechos;
  const comTempo = a.duracao_s != null && a.duracao_s > 0;
  const temAprox = trechos.some((t) => t.aproximado);
  const p = a.post;
  return (
    <div className="mapa-anat">
      <div className="mapa-anat-midia">
        <MolduraCelular largura={290}>
          <Midia midia={detalhe?.midia ?? { tipo: "capa" }} thumb={p.thumb} titulo={p.titulo} url={p.url} plataforma={p.plataforma} />
        </MolduraCelular>
      </div>
      <div className="mapa-anat-lado">
        <div className="mapa-anat-cab">
          <div>
            <p className="t-titulo mapa-anat-canal">{p.canal}</p>
            <p className="t-sec">{nomePlataforma(p.plataforma)} · {p.formato}{comTempo ? ` · ${seg(a.duracao_s!)}` : ""} · ER {fmtPct(p.er)}</p>
          </div>
          <Etiqueta valor={fmtVezes(p.vezes)} rotulo="o esperado" tom="papel" />
        </div>
        {comTempo
          ? <Faixa trechos={trechos} duracao={a.duracao_s!} />
          : <p className="mapa-semtempo">{p.formato} não tem duração: os trechos abaixo estão na ordem em que aparecem, sem eixo de tempo.</p>}
        <ol className={`mapa-cartoes${comTempo ? "" : " mapa-cartoes--seq"}`}>
          {trechos.map((t, i) => <Cartao key={i} t={t} n={i + 1} comTempo={comTempo} />)}
        </ol>
        <p className="mapa-legenda">
          {trechos.some((t) => !t.aproximado) && <span><i className="mapa-amostra" />Medido na leitura do vídeo</span>}
          {temAprox && <span><i className="mapa-amostra mapa-amostra--aprox" />Aproximado: a leitura não mediu o momento exato</span>}
        </p>
        {a.nota && <p className="t-pequeno t-sec">{a.nota}</p>}
        <div><Botao variante="contorno" tamanho="p" onClick={() => abrir(p.id)}>Abrir a ficha completa do post →</Botao></div>
      </div>
    </div>
  );
}

export function Anatomia() {
  const [params, setParams] = useSearchParams();
  const [q, setQ] = useState("");
  const destaques = useDestaques(12);
  const busca = useBusca(q, 24);
  const buscando = q.trim().length >= 2;
  const achados = (busca.data ?? []).map((r) => r.post).filter((p) => p.top).slice(0, 12);
  const lista = buscando ? achados : (destaques.data ?? []).map((d) => d.post);
  const id = params.get("anat") ?? destaques.data?.[0]?.post.id ?? null;
  const escolher = (novo: string) => setParams((p) => { const n = new URLSearchParams(p); n.set("anat", novo); return n; }, { replace: true });
  const { data, isLoading, error, refetch } = useAnatomia(id);

  const titulo = data ? `Como ${data.post.canal} prende a atenção` : "Anatomia de um post do top";
  return (
    <Secao titulo={titulo} sub="Escolha um post do top para ver como ele é montado: como abre, o que segura a atenção e o que pede no fim.">
      <div className="mapa-anat-busca nao-imprimir">
        <Campo rotulo="Buscar um post do top" esconderRotulo placeholder="Buscar um post do top por ideia: fluxo de caixa, preço, bastidor" value={q} onChange={(e) => setQ(e.target.value)} />
        {destaques.isLoading && <Esqueleto altura={72} />}
        {destaques.error && !buscando && <Erro erro={destaques.error} onTentar={destaques.refetch} />}
        {buscando && busca.data && !achados.length && <p className="t-sec t-pequeno">Nenhum post do top bate com essa busca. Tente outra ideia ou apague para voltar aos destaques.</p>}
        {lista.length > 0 && <Escolha posts={lista} atual={id} onEscolher={escolher} />}
      </div>
      {isLoading && <Esqueleto altura={460} />}
      {error && <Erro erro={error} onTentar={refetch} />}
      {!id && destaques.data && <Vazio titulo="Nenhum post para mostrar">Este foco ainda não tem posts em destaque. Busque um post pelo campo acima.</Vazio>}
      {data && (data.trechos.length ? <Corpo key={data.post.id} a={data} /> : <Vazio titulo="Sem leitura deste post">Este post ainda não foi lido em detalhe. Escolha outro na lista acima.</Vazio>)}
    </Secao>
  );
}
