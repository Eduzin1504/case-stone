// /padroes: o que o top faz diferente. Barras pareadas por grupo, exemplos que expandem no lugar e, no Foco A, os Ads.
import { useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { useAds, usePadroes } from "../../api/hooks";
import type { Ad, Padrao } from "../../api/tipos";
import {
  BarraPar, BotaoExportar, Botao, Carimbo, Chip, Erro, Esqueleto, Etiqueta, LegendaBarraPar, PostCard, Secao, Seg, Selo, TituloPagina, Vazio,
} from "../../componentes";
import { useFoco } from "../../contexto/Foco";
import { fmtPct, fmtVezes, nomePlataforma } from "../../util/formato";
import { useEntrou } from "../../util/useEntrou";
import "./padroes.css";

type Direcao = "todos" | "mais" | "menos";
const chave = (p: Padrao) => `${p.campo}:${p.valor}`;
const idGrupo = (g: string) => `grupo-${g.toLowerCase().normalize("NFD").replace(/[^a-z0-9]+/g, "-")}`;
const idDe = (p: Padrao) => `padrao-${chave(p).replace(/[^\p{L}\p{N}]+/gu, "-")}`;
const EASE = [0.22, 1, 0.36, 1] as const;

function Exemplos({ padrao }: { padrao: Padrao }) {
  if (!padrao.exemplos.length) return <p className="t-sec t-pequeno padroes-sem-exemplo">Nenhum post de exemplo guardado para este padrão.</p>;
  return (
    <div className="padroes-exemplos">
      {padrao.exemplos.map((p) => <PostCard key={p.id} post={p} variante="compacto" />)}
    </div>
  );
}

function Item({ padrao, max, aberto, onAlternar }: { padrao: Padrao; max: number; aberto: boolean; onAlternar: () => void }) {
  const n = padrao.exemplos.length;
  return (
    <div id={idDe(padrao)} className={`padroes-item${aberto ? " padroes-item--aberto" : ""}`}>
      <div className="padroes-item-cab" onClick={onAlternar}>
        <BarraPar
          rotulo={padrao.rotulo} top={padrao.freq_top} controle={padrao.freq_controle} lift={padrao.lift} selo={padrao.selo} fragil={padrao.fragil} max={max}
          nomeControle="posts comuns"
          acao={
            // o clique sobe para a linha inteira; o botão existe para o teclado e o leitor de tela
            <button type="button" className="padroes-ver" aria-expanded={aberto}>
              {aberto ? "fechar ×" : n ? `ver ${n} ${n === 1 ? "exemplo" : "exemplos"} →` : "sem exemplos"}
            </button>
          }
        />
      </div>
      <AnimatePresence initial={false}>
        {aberto && (
          <motion.div className="padroes-abre" data-sem-ficha initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.22, ease: EASE }}>
            <div className="padroes-abre-dentro">
              <p className="t-pequeno t-sec">
                Em {padrao.n_top} {padrao.n_top === 1 ? "post" : "posts"} do top ({fmtPct(padrao.freq_top)}), contra {fmtPct(padrao.freq_controle)} dos posts comuns.
                {padrao.lift == null && " Não apareceu no grupo de controle, por isso não há multiplicador."}
                {padrao.confianca && ` Leitura automática: confiança ${padrao.confianca}.`}
              </p>
              <Exemplos padrao={padrao} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function Destaques({ itens }: { itens: Padrao[] }) {
  const [primeiro, ...resto] = itens;
  return (
    <div className="padroes-destaques">
      <article className="padroes-heroi bloco-lima">
        <div className="padroes-heroi-texto">
          <Etiqueta tamanho="g" tom="floresta" valor={fmtVezes(primeiro.lift)} rotulo="mais no top" />
          <h2 className="t-titulo padroes-heroi-titulo">{primeiro.rotulo}</h2>
          <p>Aparece em {fmtPct(primeiro.freq_top)} do top e em {fmtPct(primeiro.freq_controle)} dos posts comuns.</p>
          <div className="linha"><Selo tipo={primeiro.selo} />{primeiro.fragil && <Selo tipo="frágil" />}</div>
        </div>
        {primeiro.exemplos.length > 0 && (
          <div className="padroes-heroi-posts">
            {primeiro.exemplos.map((p) => <PostCard key={p.id} post={p} variante="compacto" semFicha />)}
          </div>
        )}
      </article>
      {resto.map((p) => (
        <article key={chave(p)} className="padroes-vice">
          <p className="t-titulo padroes-vice-num">{fmtVezes(p.lift)}</p>
          <h2 className="t-h3">{p.rotulo}</h2>
          <BarraPar rotulo={<span className="so-leitor">{p.rotulo}</span>} top={p.freq_top} controle={p.freq_controle} selo={p.selo} fragil={p.fragil} nomeControle="posts comuns" />
        </article>
      ))}
    </div>
  );
}

function BarraAd({ ad, max, padroes, onIr }: { ad: Ad; max: number; padroes: Padrao[]; onIr: (p: Padrao) => void }) {
  const ref = useRef<HTMLLIElement>(null);
  const entrou = useEntrou(ref);
  const alto = ad.desempenho === "alto";
  return (
    <li ref={ref} className={`padroes-ad${alto ? " padroes-ad--alto" : ""}`}>
      <div className="padroes-ad-nome">
        <span className="padroes-ad-titulo">{ad.criativo}</span>
        <span className="t-pequeno t-sec">{[ad.formato, ad.periodo, ...ad.marcas.filter((m) => !ad.confirma.some((c) => c.toLowerCase().includes(m)))].filter(Boolean).join(" · ")}</span>
        {ad.confirma.length > 0 && (
          <span className="padroes-ad-confirma">
            {ad.confirma.map((rot) => {
              const p = padroes.find((x) => x.rotulo === rot);
              return p
                ? <button key={rot} type="button" className="selo selo--ok" onClick={() => onIr(p)} title="Ver este padrão na lista">✓ {rot}</button>
                : <span key={rot} className="selo selo--ok">✓ {rot}</span>;
            })}
          </span>
        )}
      </div>
      <div className="padroes-ad-trilho" role="img" aria-label={`CTR de ${fmtPct(ad.ctr / 100)}, desempenho ${ad.desempenho}`}>
        <span className="padroes-ad-barra" style={{ width: `${(ad.ctr / max) * 100}%`, transform: `scaleX(${entrou ? 1 : 0})` }} />
      </div>
      <span className="padroes-ad-ctr">{fmtPct(ad.ctr / 100)}</span>
    </li>
  );
}

function Ads({ confirmados, onIr }: { confirmados: Padrao[]; onIr: (p: Padrao) => void }) {
  const { data, isLoading, error, refetch } = useAds();
  const ads = useMemo(() => [...(data ?? [])].sort((a, b) => b.ctr - a.ctr), [data]);
  const max = Math.max(...ads.map((a) => a.ctr), 0.01);
  const nAlto = ads.filter((a) => a.desempenho === "alto").length;
  return (
    <Secao titulo="O que os Ads do Impulso confirmam" sub="Taxa de cliques (CTR) de cada criativo já veiculado, do maior para o menor. Em verde, os de alto desempenho." bloco="superficie">
      {isLoading && <Esqueleto tipo="linhas" n={6} />}
      {error && <Erro erro={error} onTentar={refetch} />}
      {data && ads.length === 0 && <Vazio titulo="Sem criativos">Nenhum criativo de Ads foi cadastrado para comparar.</Vazio>}
      {ads.length > 0 && (
        <div className="padroes-ads">
          <ol className="padroes-ads-lista">{ads.map((a) => <BarraAd key={a.criativo} ad={a} max={max} padroes={confirmados} onIr={onIr} />)}</ol>
          <aside className="padroes-ads-lado">
            <Carimbo texto="Confirmado" sub="nos Ads" tom="dados" tamanho={72} />
            <p className="t-h3">{nAlto} de {ads.length} criativos tiveram alto desempenho.</p>
            {confirmados.length > 0 ? (
              <>
                <p className="t-sec t-pequeno">Padrões do mercado que os Ads repetem nesta plataforma. O selo verde em cada anúncio diz qual deles ele tem.</p>
                <ul className="padroes-confirmados">
                  {confirmados.map((p) => (
                    <li key={chave(p)}>
                      <button type="button" onClick={() => onIr(p)}>
                        <b>{fmtVezes(p.lift)}</b><span>{p.rotulo}<small className="t-sec"> · em {ads.filter((a) => a.confirma.includes(p.rotulo)).length} anúncios</small></span><i aria-hidden>→</i>
                      </button>
                    </li>
                  ))}
                </ul>
              </>
            ) : <p className="t-sec t-pequeno">Nenhum padrão desta plataforma foi confirmado nos Ads até agora.</p>}
          </aside>
        </div>
      )}
    </Secao>
  );
}

export default function Padroes() {
  const { foco } = useFoco();
  const [plat, setPlat] = useState<string | undefined>();
  const [direcao, setDirecao] = useState<Direcao>("todos");
  const [selo, setSelo] = useState("");
  const [aberto, setAberto] = useState<string | null>(null);
  const [gruposMudados, setGruposMudados] = useState<Record<string, boolean>>({}); // só o que a pessoa abriu ou fechou
  const alvo = useRef<HTMLDivElement>(null);
  const { data, isLoading, error, refetch } = usePadroes(plat);

  const itens = data?.itens ?? [];
  const atual = plat ?? data?.plataforma ?? data?.plataformas[0] ?? "instagram";
  const destaques = useMemo(
    () => itens.filter((p) => p.lift != null && p.lift > 1 && !p.fragil && p.selo !== "inconclusivo").sort((a, b) => (b.lift ?? 0) - (a.lift ?? 0)).slice(0, 3),
    [itens],
  );
  const selos = useMemo(() => {
    const s = [...new Set(itens.map((p) => p.selo).filter((x): x is string => !!x))];
    return itens.some((p) => p.fragil) ? [...s, "frágil"] : s;
  }, [itens]);
  const visiveis = itens.filter((p) => {
    if (direcao === "mais" && !(p.lift == null ? p.freq_top > p.freq_controle : p.lift > 1)) return false;
    if (direcao === "menos" && !(p.lift != null && p.lift < 1)) return false;
    if (selo === "frágil") return p.fragil;
    return !selo || p.selo === selo;
  });
  const grupos = useMemo(() => {
    const m = new Map<string, Padrao[]>();
    visiveis.forEach((p) => m.set(p.grupo, [...(m.get(p.grupo) ?? []), p]));
    // grupos mais fortes primeiro (pelo maior multiplicador de um padrão não frágil); os dois primeiros começam abertos
    const forca = (ps: Padrao[]) => Math.max(0, ...ps.filter((p) => !p.fragil && p.lift != null).map((p) => p.lift!));
    return [...m].map(([grupo, ps]) => ({ grupo, ps: ps.sort((a, b) => (b.lift ?? Infinity) - (a.lift ?? Infinity)) })).sort((a, b) => forca(b.ps) - forca(a.ps));
  }, [visiveis]);
  const grupoAberto = (g: string, i: number) => gruposMudados[g] ?? (i < 2 || !!selo || direcao !== "todos");

  const limpar = () => { setDirecao("todos"); setSelo(""); };
  const irPara = (p: Padrao) => {
    limpar();
    setGruposMudados((m) => ({ ...m, [p.grupo]: true }));
    setAberto(chave(p));
    // espera a lista sem filtros renderizar antes de rolar
    setTimeout(() => document.getElementById(idDe(p))?.scrollIntoView({ behavior: "smooth", block: "center" }), 80);
  };

  return (
    <div ref={alvo} className="padroes">
      <TituloPagina
        titulo="O que o top faz" grifo="diferente"
        sub="Cada padrão compara dois grupos: os posts do top e os posts comuns do grupo de controle, sorteados na mesma base. O número grande diz quantas vezes o padrão aparece mais no top."
        acoes={<BotaoExportar alvo={alvo} nome={`padroes-foco-${foco}-${atual}`} />}
      />

      {data && data.plataformas.length > 1 && (
        <div className="linha nao-imprimir" data-nao-exportar>
          <Seg rotulo="Plataforma" valor={atual} onChange={(v) => { setPlat(v); setAberto(null); }} opcoes={data.plataformas.map((p) => ({ valor: p, rotulo: nomePlataforma(p) }))} />
        </div>
      )}

      {isLoading && <><Esqueleto altura={280} /><Esqueleto tipo="linhas" n={6} /></>}
      {error && <Erro erro={error} onTentar={refetch} />}
      {data && itens.length === 0 && (
        <Vazio titulo="Sem padrões aqui" acao={data.plataformas.length > 1 ? <Botao variante="contorno" onClick={() => setPlat(data.plataformas[0])}>Ver {nomePlataforma(data.plataformas[0])}</Botao> : undefined}>
          Não há posts lidos em detalhe suficientes nesta plataforma para comparar o top com o controle.
        </Vazio>
      )}

      {destaques.length > 0 && <Destaques itens={destaques} />}

      {itens.length > 0 && (
        <div className="padroes-barra">
          <div className="linha nao-imprimir" data-nao-exportar>
            <Seg tamanho="p" rotulo="Direção" valor={direcao} onChange={setDirecao} opcoes={[{ valor: "todos", rotulo: "Todos" }, { valor: "mais", rotulo: "Mais no top" }, { valor: "menos", rotulo: "Menos no top" }]} />
            {selos.length > 0 && (
              <span className="linha padroes-selos" role="group" aria-label="Filtrar por selo">
                {selos.map((s) => <Chip key={s} ativo={selo === s} onClick={() => setSelo(selo === s ? "" : s)}>{s}</Chip>)}
              </span>
            )}
          </div>
          <LegendaBarraPar nomeTop="Nos posts do top" nomeControle="Nos posts comuns (grupo de controle)" />
        </div>
      )}

      {itens.length > 0 && grupos.length === 0 && (
        <Vazio titulo="Nada com esses filtros" acao={<Botao variante="contorno" onClick={limpar}>Limpar filtros</Botao>}>Nenhum padrão bate com a direção e o selo escolhidos.</Vazio>
      )}

      {grupos.length > 1 && (
        <nav className="padroes-indice nao-imprimir" aria-label="Grupos de padrões" data-nao-exportar>
          {grupos.map(({ grupo, ps }) => (
            <a key={grupo} href={`#${idGrupo(grupo)}`} onClick={() => setGruposMudados((m) => ({ ...m, [grupo]: true }))}>{grupo} <span className="t-sec">{ps.length}</span></a>
          ))}
        </nav>
      )}

      {grupos.map(({ grupo, ps }, gi) => {
        const max = Math.max(...ps.map((p) => Math.max(p.freq_top, p.freq_controle)), 0.05);
        const abertoG = grupoAberto(grupo, gi);
        return (
          <Secao
            key={grupo} id={idGrupo(grupo)} titulo={grupo} className="padroes-grupo"
            sub={`${ps.length} ${ps.length === 1 ? "padrão" : "padrões"}, do mais ao menos presente no top`}
            acao={
              <Botao variante="fantasma" tamanho="p" className="nao-imprimir" aria-expanded={abertoG} aria-controls={`${idGrupo(grupo)}-lista`} onClick={() => setGruposMudados((m) => ({ ...m, [grupo]: !abertoG }))}>
                {abertoG ? "Recolher" : `Expandir (${ps.length})`}
              </Botao>
            }
          >
            <div id={`${idGrupo(grupo)}-lista`} className="padroes-grupo-lista" hidden={!abertoG}>
              {ps.map((p) => <Item key={chave(p)} padrao={p} max={max} aberto={aberto === chave(p)} onAlternar={() => setAberto(aberto === chave(p) ? null : chave(p))} />)}
            </div>
          </Secao>
        );
      })}

      {foco === "A" && <Ads confirmados={itens.filter((p) => p.selo === "confirmado")} onIr={irPara} />}
    </div>
  );
}
