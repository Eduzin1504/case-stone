// Os capítulos do playbook. O texto vem do markdown da API; os blocos visuais, dos hooks estruturados.
// A escolha do capítulo é pelo `rotulo` que a API devolve; rótulo desconhecido cai no capítulo genérico (texto + "ver os números").
import { useRef, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { useAds, useCriador, useCriadores, useCriativos, useFunil, usePadroes } from "../../api/hooks";
import type { Capitulo, CriadorResumo, Padrao, Playbook, RespostaAgente } from "../../api/tipos";
import {
  BarraPar, Botao, Chip, Comprovante, Erro, Esqueleto, Etiqueta, LegendaBarraPar, Markdown, MolduraCelular, NumeroConta, Selo, Vazio,
} from "../../componentes";
import { useFoco } from "../../contexto/Foco";
import { fmtData, fmtInt, fmtNum, fmtPct, fmtVezes, nomePlataforma, nomePorte } from "../../util/formato";
import { useEntrou } from "../../util/useEntrou";
import { idsDosLinks, itens, Minis, Nota, paragrafos, PostTocavel, Preguica, separar, VerNumeros } from "./pecas";

type Props = { cap: Capitulo; pb: Playbook };
const dec = (s: string) => Number(s.replace(",", "."));

// ======================================================================= como ler
function Regua() {
  return (
    <ol className="playbook-regua">
      <li>
        <div className="playbook-regua-il playbook-regua-il--fracao" aria-hidden><span>curtidas + comentários</span><i /><span>seguidores</span></div>
        <span className="playbook-regua-n">1</span>
        <p className="t-h3">Medimos o engajamento</p>
        <p className="t-sec">A nota de cada post é o ER: curtidas mais comentários, divididos pelos seguidores do perfil.</p>
      </li>
      <li>
        <div className="playbook-regua-il playbook-regua-il--barras" aria-hidden><span><i />esperado</span><span><i />o que o post fez</span></div>
        <span className="playbook-regua-n">2</span>
        <p className="t-h3">Comparamos com o esperado</p>
        <p className="t-sec">Um modelo estima quanto cada post deveria engajar pelo tamanho do perfil, formato, idade do post e histórico do criador. Assim perfil pequeno não leva vantagem.</p>
      </li>
      <li>
        <div className="playbook-regua-il playbook-regua-il--dez" aria-hidden>{Array.from({ length: 10 }, (_, i) => <i key={i} />)}</div>
        <span className="playbook-regua-n">3</span>
        <p className="t-h3">Ficamos com o top 10%</p>
        <p className="t-sec">São os posts que mais passaram do esperado, em cada plataforma e faixa de tamanho. Cada criador entra com no máximo 3 posts.</p>
      </li>
    </ol>
  );
}

// desenho do selo: dois quadrados (mercado, Ads) ou cinco pontos (frágil)
function Par({ m, a }: { m: "sim" | "nao" | "vazio"; a: "sim" | "nao" | "vazio" }) {
  return (
    <span className="playbook-par" aria-hidden>
      <span><i className={`playbook-q playbook-q--${m}`} />mercado</span>
      <span><i className={`playbook-q playbook-q--${a}`} />Ads</span>
    </span>
  );
}
const Pontos = ({ cheios, total = 5 }: { cheios: number; total?: number }) => (
  <span className="playbook-par" aria-hidden>
    <span>{Array.from({ length: total }, (_, i) => <i key={i} className={`playbook-q playbook-q--${i < cheios ? "sim" : "vazio"}`} />)}</span>
  </span>
);

function ComoLer({ cap }: Props) {
  const { foco } = useFoco();
  const selos: [ReactNode, ReactNode, string][] = foco === "A"
    ? [
        [<Par m="sim" a="sim" />, <Selo tipo="confirmado" />, "Funciona no mercado e também nos Ads do Impulso."],
        [<Par m="sim" a="nao" />, <Selo tipo="contradito" />, "Mercado e Ads apontam em direções opostas."],
        [<Par m="sim" a="vazio" />, <Selo tipo="só mercado" />, "Aparece no mercado, mas ainda não foi testado nos Ads."],
        [<Pontos cheios={3} />, <Selo tipo="frágil" />, "Menos de 5 posts do top sustentam o padrão. É pista, não regra."],
      ]
    : [
        [<Pontos cheios={1} total={10} />, <span className="playbook-termo">top</span>, "Os posts que mais passaram do esperado para o tamanho do perfil."],
        [<Pontos cheios={0} total={10} />, <span className="playbook-termo">controle</span>, "Posts comuns, sorteados fora do top. É com eles que o top é comparado."],
        [<Pontos cheios={2} total={2} />, <span className="playbook-termo">intenção de compra</span>, "Comentário de cliente que pergunta preço, endereço ou entrega, ou diz que quer."],
        [<Pontos cheios={3} />, <Selo tipo="frágil" />, "Menos de 5 posts do top sustentam o achado. É pista, não regra."],
      ];
  return (
    <>
      <p className="playbook-leitura">Todo número deste playbook sai da mesma régua. Ela tem três passos.</p>
      <Regua />
      <Markdown texto={separar(cap.markdown).texto} className="playbook-leitura" />
      <ul className="playbook-selos">
        {selos.map(([desenho, nome, texto]) => (
          <li key={texto}>{desenho}{nome}<p className="t-pequeno">{texto}</p></li>
        ))}
      </ul>
    </>
  );
}

// ======================================================================= padrões (Foco A: dados estruturados)
// todos no mesmo modelo: texto + barras à esquerda, miniaturas dos exemplos à direita
function Achado({ p, max }: { p: Padrao; max: number }) {
  const [nome, valor] = /: (?!(não|sim)$)/.test(p.rotulo) ? p.rotulo.split(": ") : [null, p.rotulo];
  return (
    <article className="playbook-achado">
      <div className="playbook-achado-texto">
        <Etiqueta valor={fmtVezes(p.lift)} rotulo="mais no top" tamanho="m" tom="papel" />
        <h3 className="t-titulo playbook-achado-titulo">{nome && <small>{nome}</small>}{valor}</h3>
        <p>Aparece em <b>{fmtPct(p.freq_top)}</b> dos posts do top e em <b>{fmtPct(p.freq_controle)}</b> dos posts comuns. São {fmtInt(p.n_top)} posts do top.</p>
        <div className="playbook-semlift">
          <BarraPar rotulo={p.confianca ? `Confiança da leitura: ${p.confianca}` : "Com que frequência aparece"} top={p.freq_top} controle={p.freq_controle} max={max} selo={p.selo} fragil={p.fragil} nomeControle="comuns" />
        </div>
      </div>
      <div className="playbook-achado-posts"><Minis posts={p.exemplos} /></div>
    </article>
  );
}

function usePadroesFortes(plataforma: string, n: number) {
  const q = usePadroes(plataforma);
  const validos = (q.data?.itens ?? []).filter((p) => p.lift != null && p.n_top >= 5);
  const mais = validos.filter((p) => p.lift! >= 1.5).sort((a, b) => b.lift! - a.lift!).slice(0, n);
  const menos = validos.filter((p) => p.lift! <= 0.65).sort((a, b) => a.lift! - b.lift!).slice(0, 6);
  return { ...q, mais, menos };
}

function PadroesA({ cap }: Props) {
  const { mais, menos, isLoading, error, refetch } = usePadroesFortes("instagram", 8);
  const max = Math.max(...mais.map((p) => Math.max(p.freq_top, p.freq_controle)), 0.1);
  const leitura = cap.markdown.split("**Leitura para o Impulso:**")[1];
  return (
    <>
      <p className="playbook-leitura">Comparamos os posts do top com posts comuns dos mesmos perfis, no Instagram. O número na etiqueta diz quantas vezes cada característica aparece mais no top. Ao lado de cada achado estão posts reais do top com aquela característica: toque para ver.</p>
      {isLoading && <Esqueleto tipo="linhas" n={4} />}
      {error && <Erro erro={error} onTentar={refetch} />}
      {!isLoading && !error && !mais.length && <Markdown texto={separar(cap.markdown).texto} className="playbook-leitura" />}
      <div className="playbook-achados">
        {mais.map((p) => (
          <Preguica key={p.campo + p.valor} altura={300}><Achado p={p} max={max} /></Preguica>
        ))}
      </div>
      {menos.length > 0 && (
        <div className="playbook-menos">
          <h3 className="t-titulo t-h2">O que aparece menos no top</h3>
          <LegendaBarraPar nomeControle="Nos posts comuns" />
          {menos.map((p) => <BarraPar key={p.campo + p.valor} rotulo={p.rotulo} top={p.freq_top} controle={p.freq_controle} lift={p.lift} selo={p.selo} fragil={p.fragil} nomeControle="comuns" />)}
        </div>
      )}
      {leitura && <Nota titulo="Leitura para o Impulso"><Markdown texto={leitura.trim()} /></Nota>}
      <VerNumeros md={cap.markdown.split("**Leitura para o Impulso:**")[0]} />
    </>
  );
}

// ======================================================================= padrões (Foco B: achados numerados do texto, com os posts citados)
function PadroesB({ cap, pb }: Props) {
  const blocos = cap.markdown.split(/\n\s*\n/).map((b) => b.trim()).filter(Boolean);
  const achados = blocos.map((b) => /^\*\*(\d+)\. (.+?)\*\*\s*([\s\S]*)$/.exec(b));
  if (!achados.some(Boolean)) return <Generico cap={cap} pb={pb} />;
  return (
    <>
      <p className="playbook-leitura">O número na etiqueta é o lift: quantas vezes a característica aparece mais (ou menos) no top do que no grupo de controle.</p>
      <div className="playbook-achados">
        {blocos.map((b, k) => {
          const m = achados[k];
          if (!m) {
            const lead = /^\*\*(.+?)\*\*\s*([\s\S]*)$/.exec(b);
            return lead ? <Nota key={k} titulo={lead[1].replace(/:$/, "")}><Markdown texto={lead[2]} /></Nota> : <Markdown key={k} texto={b} className="playbook-leitura" />;
          }
          const [, , titulo, corpo] = m;
          const lift = /lift (\d+(?:,\d+)?)/.exec(corpo);
          const f1 = /(\d+(?:,\d+)?)% d[oa] top contra (\d+(?:,\d+)?)% d[oa] controle/.exec(corpo);
          const f2 = /(\d+(?:,\d+)?)% d[oa] controle e (\d+(?:,\d+)?)% d[oa] top/.exec(corpo);
          const par = f1 ? [dec(f1[1]), dec(f1[2])] : f2 ? [dec(f2[2]), dec(f2[1])] : null;
          const baixo = !!lift && dec(lift[1]) < 1;
          const links = idsDosLinks(corpo);
          return (
            <Preguica key={k} altura={260}>
              <article className={`playbook-achado${links.length ? "" : " playbook-achado--so"}`}>
                <div className="playbook-achado-texto">
                  {lift && <Etiqueta valor={fmtVezes(dec(lift[1]))} rotulo={baixo ? "menos no top" : "mais no top"} tamanho="m" tom="papel" />}
                  <h3 className="t-titulo playbook-achado-titulo">{titulo.replace(/\.$/, "")}</h3>
                  <Markdown texto={corpo} />
                  {par && <div className="playbook-semlift"><BarraPar rotulo="No top × no controle" top={par[0] / 100} controle={par[1] / 100} fragil={/frágil/i.test(titulo)} /></div>}
                </div>
                {links.length > 0 && (
                  <div className="playbook-achado-posts">
                    <Minis ids={links.map((l) => l.id)} />
                  </div>
                )}
              </article>
            </Preguica>
          );
        })}
      </div>
    </>
  );
}

// ======================================================================= mercado × ads
function BarrasAds() {
  const { data: ads, isLoading, error, refetch } = useAds();
  const ref = useRef<HTMLDivElement>(null);
  const entrou = useEntrou(ref); // o ref fica num nó que existe desde a primeira renderização
  const lista = [...(ads ?? [])].sort((a, b) => b.ctr - a.ctr);
  const max = lista[0]?.ctr ?? 1;
  return (
    <div ref={ref} className="pilha">
      {isLoading && <Esqueleto tipo="linhas" n={5} />}
      {error && <Erro erro={error} onTentar={refetch} />}
      {!isLoading && !error && !lista.length && <Vazio titulo="Sem Ads nesta base">Os anúncios do Impulso só existem no Foco A.</Vazio>}
      {lista.length > 0 && <p className="t-pequeno t-sec">Taxa de clique (CTR) dos {lista.length} anúncios da conta, do maior para o menor. Verde: CTR alto. Cinza: médio. Magenta: baixo.</p>}
      <ol className="playbook-ads">
        {lista.map((a) => (
          <li key={a.criativo} className={`playbook-ad playbook-ad--${a.desempenho}`}>
            <span className="playbook-ad-nome">{a.criativo}<small>{a.marcas?.length ? a.marcas.join(" · ") : "sem gatilho de identificação"}</small></span>
            <span className="playbook-ad-trilho"><i style={{ width: `${(a.ctr / max) * 100}%`, transform: entrou ? "none" : "scaleX(0)" }} /></span>
            <b>{a.ctr.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%</b>
          </li>
        ))}
      </ol>
    </div>
  );
}

const DUPLA: [string, string][] = [["gatilho_identificacao", "pessoa_real"], ["convite_participacao", "True"], ["generico", "True"], ["gatilho_identificacao", "nenhum"]];

function MercadoAds({ cap }: Props) {
  const { data, isLoading, error, refetch } = usePadroes("todas");
  const linhas = DUPLA.map(([c, v]) => data?.itens.find((p) => p.campo === c && p.valor === v)).filter((p): p is Padrao => !!p);
  const max = Math.max(...linhas.map((p) => Math.max(p.freq_top, p.freq_controle)), 0.1);
  const ps = paragrafos(cap.markdown);
  const tese = ps.find((p) => /reação não é clique/i.test(p));
  return (
    <>
      <p className="playbook-leitura">O mercado mede reação: curtida e comentário. Os Ads do Impulso medem clique. Colocamos os dois lado a lado para ver onde concordam.</p>
      <Preguica altura={560}>
        <div className="playbook-lados">
          <section>
            <h3 className="t-titulo t-h2">No mercado: o que engaja</h3>
            <LegendaBarraPar nomeControle="Nos posts comuns" />
            {isLoading && <Esqueleto tipo="linhas" n={4} />}
            {error && <Erro erro={error} onTentar={refetch} />}
            {linhas.map((p) => <BarraPar key={p.campo + p.valor} rotulo={p.rotulo} top={p.freq_top} controle={p.freq_controle} lift={p.lift} selo={p.selo} fragil={p.fragil} max={max} nomeControle="comuns" />)}
          </section>
          <section>
            <h3 className="t-titulo t-h2">Nos Ads: o que gera clique</h3>
            <BarrasAds />
          </section>
        </div>
      </Preguica>
      {tese && (
        <blockquote className="playbook-floresta playbook-citacao">
          <p className="t-titulo">Reação não é clique</p>
          <Markdown texto={tese.replace(/^\*\*.+?\*\*\s*/, "")} />
        </blockquote>
      )}
      <Markdown texto={ps.filter((p) => p !== tese).join("\n\n")} className="playbook-leitura" />
      <VerNumeros md={separar(cap.markdown).tabelas} />
    </>
  );
}

// ======================================================================= perfis em destaque (ranking editorial)
function Perfil({ c, pos, destaque }: { c: CriadorResumo; pos: number; destaque: boolean }) {
  const { data, isLoading } = useCriador(c.id);
  const posts = [...(data?.posts ?? [])].sort((a, b) => Number(b.top) - Number(a.top) || (b.vezes ?? 0) - (a.vezes ?? 0)).slice(0, destaque ? 3 : 4);
  const [nome, ...desc] = c.nome.split("|").map((s) => s.trim());
  const ig = c.plataforma === "instagram";
  return (
    <article className={`playbook-perfil${destaque ? " playbook-perfil--destaque" : ""}`}>
      <span className="playbook-perfil-pos" aria-label={`${pos}º lugar`}>{pos}</span>
      <div className="playbook-perfil-texto">
        <h4 className="playbook-perfil-nome">{nome}</h4>
        {desc.length > 0 && <p className="t-sec">{desc.join(" · ")}</p>}
        <p className="playbook-perfil-quem">
          <span className="playbook-plat">{nomePlataforma(c.plataforma)}</span>
          <a href={c.url} target="_blank" rel="noreferrer">{ig ? `@${c.id}` : "abrir o canal"} ↗</a>
          <span className="t-sec">perfil {nomePorte(c.porte)}, {fmtNum(c.seguidores)} {ig ? "seguidores" : "inscritos"}</span>
        </p>
        <p className="playbook-perfil-porque">
          Tem {c.n_top} {c.n_top > 1 ? "posts" : "post"} no top{c.n_top === 3 ? ", o limite por criador" : ""}.{" "}
          {c.tema && c.formato ? <>O que mais rende por lá: <b>{c.tema}</b>, em formato <b>{c.formato}</b>. </> : c.formato ? <>O formato que mais usa: <b>{c.formato}</b>. </> : null}
          Engaja <b>{fmtVezes(c.vezes).replace("×", " vezes")}</b> o esperado para o tamanho do perfil.
        </p>
        <p className="linha">
          {c.tema && <Chip rotulo="Tema">{c.tema}</Chip>}
          {c.formato && <Chip rotulo="Formato">{c.formato}</Chip>}
          {c.er_mediano != null && <Chip rotulo="ER mediano">{fmtPct(c.er_mediano)}</Chip>}
          <Chip>{fmtInt(c.n_posts)} posts na base</Chip>
        </p>
        {destaque && <Minis posts={posts.slice(1)} />}
        <Link className="playbook-seta nao-imprimir" to={`/criadores/${encodeURIComponent(c.id)}`}>Ver o perfil completo →</Link>
      </div>
      <div className="playbook-perfil-posts">
        {isLoading && <Esqueleto altura={destaque ? 420 : 180} />}
        {destaque && posts[0] ? <PostTocavel id={posts[0].id} plataforma={posts[0].plataforma} resumo={posts[0]} /> : <Minis posts={posts} />}
      </div>
    </article>
  );
}

function Perfis({ cap }: Props) {
  const { data, isLoading, error, refetch } = useCriadores();
  const lista = (data ?? []).filter((c) => c.vezes != null && c.n_top > 0); // já vem ordenado por vezes o esperado
  const grupos = (["instagram", "youtube"] as const).map((plat) => ({ plat, todos: lista.filter((c) => c.plataforma === plat) })).filter((g) => g.todos.length);
  const { texto, tabelas } = separar(cap.markdown);
  return (
    <>
      <p className="playbook-leitura">A ordem aqui não é de quem tem mais seguidores nem de quem tem mais curtidas. É de quem mais engaja acima do esperado para o próprio tamanho. Por isso perfil pequeno aparece na frente de perfil grande.</p>
      {isLoading && <Esqueleto tipo="linhas" n={4} />}
      {error && <Erro erro={error} onTentar={refetch} />}
      {!isLoading && !error && !grupos.length && <Vazio titulo="Nenhum perfil com post no top" acao={<Botao variante="contorno" para="/rankings">Ver os rankings</Botao>}>A lista de criadores desta base não tem perfis no top.</Vazio>}
      {grupos.map(({ plat, todos }) => {
        const n = plat === "instagram" ? 6 : 5;
        return (
          <section key={plat} className="playbook-ranking">
            <header className="playbook-ranking-cab">
              <h3 className="t-titulo t-h2">No {nomePlataforma(plat)}</h3>
              <span className="t-pequeno t-sec">os {Math.min(n, todos.length)} primeiros de {todos.length} perfis com post no top</span>
            </header>
            {todos.slice(0, n).map((c, i) => (
              <Preguica key={c.id} altura={i < 3 ? 560 : 300}><Perfil c={c} pos={i + 1} destaque={i < 3} /></Preguica>
            ))}
          </section>
        );
      })}
      {texto && <Nota titulo="Vale notar"><Markdown texto={texto.replace(/`[^`]+\.csv`/g, "na base")} /></Nota>}
      <VerNumeros md={tabelas} />
    </>
  );
}

// ======================================================================= YouTube (Foco A)
function YouTube({ cap }: Props) {
  const { mais, isLoading, error, refetch } = usePadroesFortes("youtube", 6);
  const max = Math.max(...mais.map((p) => Math.max(p.freq_top, p.freq_controle)), 0.05);
  const alvo = mais.find((p) => p.campo === "formato_video") ?? mais[0];
  const ps = paragrafos(cap.markdown);
  return (
    <>
      {ps.length > 1 && <Markdown texto={ps[ps.length - 1]} className="playbook-leitura playbook-lide" />}
      <p className="playbook-leitura">O YouTube entra como evidência complementar: a base é maior, mas só uma parte dos vídeos foi vista por inteiro.</p>
      {isLoading && <Esqueleto tipo="linhas" n={4} />}
      {error && <Erro erro={error} onTentar={refetch} />}
      {mais.length > 0 && (
        <div className="playbook-menos">
          <LegendaBarraPar nomeControle="Nos posts comuns" />
          {mais.map((p) => <BarraPar key={p.campo + p.valor} rotulo={<>{p.rotulo} <span className="t-sec t-pequeno">· {fmtInt(p.n_top)} posts no top</span></>} top={p.freq_top} controle={p.freq_controle} lift={p.lift} selo={p.selo} max={max} nomeControle="comuns" />)}
        </div>
      )}
      {alvo && alvo.exemplos.length > 0 && (
        <Preguica altura={520}>
          <div className="playbook-ranking-cab">
            <h3 className="t-titulo t-h2">{alvo.rotulo.replace(/^.+?: /, "")}, na prática</h3>
            <span className="t-pequeno t-sec">Shorts do top com essa característica. O vídeo só carrega no clique.</span>
          </div>
          <div className="playbook-vitrine">
            {alvo.exemplos.slice(0, 2).map((p) => <PostTocavel key={p.id} id={p.id} plataforma={p.plataforma} resumo={p} largura={260} />)}
            <Minis posts={alvo.exemplos.slice(2)} />
          </div>
        </Preguica>
      )}
      {ps[0] && <Markdown texto={ps[0].replace(/:$/, ".")} className="playbook-leitura playbook-miudo" />}
    </>
  );
}

// ======================================================================= as 5 pautas (Foco A)
function Legenda({ texto }: { texto: string }) {
  const [copiada, setCopiada] = useState(false);
  const copiar = async () => {
    try {
      await navigator.clipboard.writeText(texto);
      setCopiada(true);
      window.setTimeout(() => setCopiada(false), 2200);
    } catch { /* sem permissão de área de transferência: o texto continua selecionável */ }
  };
  return (
    <div className="playbook-legenda">
      <div className="entre">
        <h4 className="t-h3">Legenda pronta</h4>
        <span className="nao-imprimir" role="status"><Botao variante="contorno" tamanho="p" onClick={copiar}>{copiada ? "✓ Copiada" : "Copiar legenda"}</Botao></span>
      </div>
      <p>{texto}</p>
    </div>
  );
}

function Pauta({ r, n }: { r: RespostaAgente; n: number }) {
  const c = r.criativos[0];
  const video = !/carrossel/i.test(c.formato);
  const capa = (!video && /["“]([^"”]+)["”]/.exec(c.cenas[0]?.texto ?? "")?.[1]) || c.gancho;
  const refs = c.inspirado_em.map((id) => r.referencias.find((p) => p.id === id));
  return (
    <article className="playbook-pauta">
      <header className="playbook-pauta-cab">
        <span className="playbook-pauta-n" aria-hidden>{n}</span>
        <div>
          <h3 className="playbook-pauta-titulo">{r.pergunta}</h3>
          <p className="linha"><Chip rotulo="Formato">{c.formato}</Chip><Chip rotulo="Pilar">{c.pilar}</Chip></p>
        </div>
      </header>
      <div className="playbook-pauta-topo">
        <figure className="playbook-pauta-capa">
          <MolduraCelular largura={270}>
            <div className="playbook-mock bloco-lima">
              <span className="playbook-mock-conta">@impulsostone</span>
              <span className="playbook-mock-tipo">{video ? "Reels" : `Carrossel · 1 de ${c.cenas.length}`}</span>
              <p className={`t-titulo playbook-mock-texto${capa.length > 110 ? " playbook-mock-texto--g" : capa.length > 60 ? " playbook-mock-texto--m" : ""}`}>{capa}</p>
            </div>
          </MolduraCelular>
          <figcaption className="t-pequeno t-sec">{video ? "Abertura do vídeo, com o gancho na tela" : "Capa do carrossel"}</figcaption>
        </figure>
        <div className="playbook-pauta-gancho">
          <p className="t-pequeno t-sec">O gancho</p>
          <p className="playbook-gancho">{c.gancho}</p>
          <div className="playbook-floresta playbook-cta">
            <p className="t-pequeno">Chamada para ação</p>
            <p>{c.cta}</p>
          </div>
        </div>
      </div>
      <div>
        <h4 className="t-h3">O roteiro, quadro a quadro</h4>
        <ol className="playbook-quadros" tabIndex={0} aria-label={`Roteiro da pauta ${n}, ${c.cenas.length} quadros`}>
          {c.cenas.map((cena) => {
            const rot = cena.rotulo;
            return (
              <li key={cena.n} className="playbook-quadro">
                <span className="playbook-quadro-n">{cena.n}</span>
                <span className="t-mono">{cena.tempo}{rot ? ` · ${rot.toLowerCase()}` : ""}</span>
                <p>{cena.texto}</p>
              </li>
            );
          })}
        </ol>
      </div>
      <Legenda texto={c.legenda} />
      {refs.length > 0 && (
        <div>
          <h4 className="t-h3">Inspirado em posts reais do top</h4>
          <Minis posts={refs.filter((p) => !!p).map((p) => p!)} ids={c.inspirado_em.filter((_, i) => !refs[i])} />
        </div>
      )}
    </article>
  );
}

function Pautas(_: Props) {
  const { data, isLoading, error, refetch } = useCriativos();
  const pautas = (data ?? []).filter((r) => r.criativos.length);
  return (
    <>
      <p className="playbook-leitura">Cada pauta foi escrita pelo agente a partir de posts reais do top e checada em quatro pontos: chamada para ação, convite à participação, linguagem genérica e tom do Impulso. Está tudo pronto para usar: a capa, o roteiro na ordem, a legenda para copiar e os posts que serviram de referência.</p>
      {isLoading && <Esqueleto altura={420} />}
      {error && <Erro erro={error} onTentar={refetch} />}
      {!isLoading && !error && !pautas.length && <Vazio titulo="Nenhuma pauta salva" acao={<Botao para="/criar">Criar uma pauta</Botao>}>As pautas do playbook ainda não foram geradas.</Vazio>}
      {pautas.map((r, i) => <Preguica key={r.id} altura={900}><Pauta r={r} n={i + 1} /></Preguica>)}
    </>
  );
}

// ======================================================================= curtida não é pedido (Foco B)
function CurtidaPedido({ cap, pb }: Props) {
  const { data: f, isLoading, error, refetch } = useFunil();
  const ref = useRef<HTMLDivElement>(null);
  const entrou = useEntrou(ref);
  const ps = paragrafos(cap.markdown);
  const formatos = [...(f?.por_formato ?? [])].sort((a, b) => b.pct_intencao - a.pct_intencao);
  const maxF = Math.max(...formatos.map((x) => x.pct_intencao), 0.01);
  const minF = Math.min(...formatos.map((x) => x.pct_intencao));
  const etapas = f?.etapas ?? [];
  const lg = (v: number) => Math.log10(Math.max(v, 1));
  const falas = (pb.comentarios?.length ? pb.comentarios : f?.comentarios ?? []).slice(0, 4);
  return (
    <>
      {ps[0] && <Markdown texto={ps[0]} className="playbook-leitura" />}
      {isLoading && <Esqueleto altura={320} />}
      {error && <Erro erro={error} onTentar={refetch} />}
      {f && f.preco.com != null && (
        <div className="playbook-preco">
          <div className="bloco-lima playbook-preco-com">
            <NumeroConta valor={f.preco.com} formato={fmtPct} className="t-titulo playbook-enorme" />
            <p className="t-h3">dos comentários mostram vontade de comprar quando o post mostra o preço</p>
            <p className="t-mono">n = {fmtInt(f.preco.n_com)} posts</p>
          </div>
          <div className="playbook-preco-sem">
            <NumeroConta valor={f.preco.sem} formato={fmtPct} className="t-titulo playbook-enorme" />
            <p className="t-h3">quando o post não mostra o preço</p>
            <p className="t-mono">n = {fmtInt(f.preco.n_sem)} posts</p>
          </div>
        </div>
      )}
      <div ref={ref}>{f && (
        <div className="playbook-lados">
          {formatos.length > 0 && (
            <section>
              <h3 className="t-titulo t-h2">Por formato</h3>
              <p className="t-pequeno t-sec">Quanto dos comentários tem intenção de compra, em cada formato de post.</p>
              <ul className="playbook-formatos">
                {formatos.map((x) => (
                  <li key={x.formato} className={x.pct_intencao === minF ? "playbook-formato--min" : undefined}>
                    <span>{x.formato}<small>{fmtInt(x.n)} {x.n === 1 ? "post" : "posts"}</small></span>
                    <span className="playbook-ad-trilho"><i style={{ width: `${(x.pct_intencao / maxF) * 100}%`, transform: entrou ? "none" : "scaleX(0)" }} /></span>
                    <b>{fmtPct(x.pct_intencao)}</b>
                  </li>
                ))}
              </ul>
            </section>
          )}
          {etapas.length > 0 && (
            <section>
              <h3 className="t-titulo t-h2">Da curtida ao pedido</h3>
              <p className="t-pequeno t-sec">Cada degrau é muito menor que o anterior: as larguras estão em escala logarítmica.</p>
              <ol className="playbook-funil">
                {etapas.map((e, i) => (
                  <li key={e.rotulo} className={i === etapas.length - 1 ? "playbook-funil--fim" : undefined}>
                    <div><span>{e.rotulo}</span><b>{fmtInt(e.valor)}</b></div>
                    <span className="playbook-ad-trilho"><i style={{ width: `${(lg(e.valor) / lg(etapas[0].valor)) * 100}%`, transform: entrou ? "none" : "scaleX(0)" }} /></span>
                  </li>
                ))}
              </ol>
            </section>
          )}
        </div>
      )}</div>
      {falas.length > 0 && (
        <div>
          <h3 className="t-titulo t-h2">Como é um comentário de quem quer comprar</h3>
          <ul className="playbook-falas">
            {falas.map((c) => (
              <li key={c.texto}>
                <blockquote>{c.texto}</blockquote>
                <span className="t-pequeno t-sec">cliente de {c.negocio}{"segmento" in c && c.segmento ? ` · ${c.segmento}` : ""}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {ps.length > 1 && <Markdown texto={ps.slice(1).join("\n\n")} className="playbook-leitura" />}
      {f?.nota && <p className="playbook-leitura playbook-miudo">{f.nota}</p>}
      <VerNumeros md={separar(cap.markdown).tabelas} />
    </>
  );
}

// ======================================================================= estudos de caso (Foco B; posts da base do Foco A)
function Casos({ cap, pb }: Props) {
  const casos = itens(cap.markdown).map((x) => /^\*\*(.+?)\s*\((.+?)\)\.\*\*\s*([\s\S]*)$/.exec(x)).filter((m): m is RegExpExecArray => !!m);
  if (!casos.length) return <Generico cap={cap} pb={pb} />;
  return (
    <>
      <p className="playbook-leitura">Estes negócios vêm da base antiga e ficam fora da estatística. Valem como exemplo para olhar de perto.</p>
      <section className="playbook-ranking">
        {casos.map(([, nome, meta, corpo], i) => {
          const links = idsDosLinks(corpo);
          const [plat, ...resto] = meta.split(",");
          return (
            <Preguica key={nome} altura={520}>
              <article className="playbook-perfil playbook-perfil--destaque">
                <span className="playbook-perfil-pos" aria-hidden>{i + 1}</span>
                <div className="playbook-perfil-texto">
                  <h4 className="playbook-perfil-nome">{nome}</h4>
                  <p className="playbook-perfil-quem">
                    <span className="playbook-plat">{plat.trim()}</span>
                    <span className="t-sec">{resto.join(",").trim()}</span>
                    {/^contraexemplo/i.test(corpo) && <span className="selo selo--nao">contraexemplo</span>}
                  </p>
                  <Markdown texto={corpo} />
                </div>
                {links[0] && <div className="playbook-perfil-posts"><PostTocavel {...links[0]} foco="A" largura={240} /></div>}
              </article>
            </Preguica>
          );
        })}
      </section>
    </>
  );
}

// ======================================================================= listas numeradas (recomendações, próximo passo)
function Numerados({ cap, pb }: Props) {
  const lista = itens(cap.markdown);
  if (!lista.length) return <Generico cap={cap} pb={pb} />;
  return (
    <ol className="playbook-numerados">
      {lista.map((x, i) => {
        const m = /^\*\*(.+?)\*\*\s*([\s\S]*)$/.exec(x);
        return (
          <li key={i} className={`playbook-numerado${i === 0 ? " bloco-lima" : ""}`}>
            <span className="playbook-numerado-n" aria-hidden>{i + 1}</span>
            <div>
              {m && <h3 className="playbook-numerado-titulo">{m[1].replace(/\.$/, "")}</h3>}
              <Markdown texto={m ? m[2] : x} />
            </div>
          </li>
        );
      })}
    </ol>
  );
}

// ======================================================================= limitações
function Limitacoes({ cap }: Props) {
  const { info } = useFoco();
  const b = info?.base;
  return (
    <div className="playbook-limites">
      <Markdown texto={cap.markdown} className="playbook-limites-texto" />
      {b && (
        <Comprovante
          titulo="Base usada" sub={info.nome}
          linhas={[
            { rotulo: "Posts", valor: fmtInt(b.posts) },
            ...(b.por_plataforma.instagram ? [{ rotulo: "Instagram", valor: fmtInt(b.por_plataforma.instagram) }] : []),
            ...(b.por_plataforma.youtube ? [{ rotulo: "YouTube", valor: fmtInt(b.por_plataforma.youtube) }] : []),
            { rotulo: "Criadores", valor: fmtInt(b.criadores) },
          ]}
          total={{ rotulo: "No top", valor: fmtInt(b.top) }}
          rodape={<>coletado em {fmtData(b.coletado_em)}<br />padrão observado não é efeito medido</>}
        />
      )}
    </div>
  );
}

// ======================================================================= genérico
function Generico({ cap }: Props) {
  const { texto, tabelas } = separar(cap.markdown);
  return (
    <>
      <Markdown texto={texto} className="playbook-leitura" />
      <VerNumeros md={tabelas} />
    </>
  );
}

function ProximoPasso(p: Props) {
  return (
    <>
      <p className="playbook-leitura">Padrão observado não é efeito medido. O que fecha a conta é um teste pequeno, com dinheiro e público iguais aos dos Ads que já rodaram.</p>
      <Numerados {...p} />
    </>
  );
}

const POR_ROTULO: [RegExp, (p: Props) => ReactNode, "A" | "B" | null][] = [
  [/^como ler/i, ComoLer, null],
  [/top faz diferente/i, PadroesA, "A"],
  [/top faz diferente/i, PadroesB, "B"],
  [/mercado.*ads/i, MercadoAds, "A"],
  [/perfis/i, Perfis, null],
  [/^youtube/i, YouTube, "A"],
  [/pautas/i, Pautas, "A"],
  [/curtida/i, CurtidaPedido, "B"],
  [/estudos? de caso/i, Casos, null],
  [/recomenda/i, Numerados, null],
  [/pr[óo]ximo passo/i, ProximoPasso, null],
  [/limita/i, Limitacoes, null],
];

export function CorpoCapitulo(p: Props) {
  const { foco } = useFoco();
  const rotulo = p.cap.rotulo ?? p.cap.titulo;
  const C = POR_ROTULO.find(([re, , f]) => re.test(rotulo) && (!f || f === foco))?.[1] ?? Generico;
  return <C {...p} />;
}
