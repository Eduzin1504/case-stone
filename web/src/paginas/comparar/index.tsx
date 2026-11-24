// /comparar?a=&b=: dois posts lado a lado. Sem um dos lados, mostra o seletor (o lado já escolhido fica fixo).
import { useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useBusca, useComparar, usePost, usePosts } from "../../api/hooks";
import type { PostDetalhe } from "../../api/tipos";
import { Botao, BotaoExportar, Campo, Carimbo, Erro, Esqueleto, Midia, Miniatura, MolduraCelular, PostCard, Secao, TituloPagina, Vazio } from "../../componentes";
import { fmtNum, fmtPct, fmtVezes, nomePlataforma } from "../../util/formato";
import { useEntrou } from "../../util/useEntrou";
import { leitura, resumir } from "./resumo";
import "./comparar.css";

type Lado = "a" | "b";

export default function Comparar() {
  const [params, setParams] = useSearchParams();
  const a = params.get("a");
  const b = params.get("b");
  const definir = (novo: Partial<Record<Lado, string | null>>) => {
    const q = new URLSearchParams(params);
    (Object.keys(novo) as Lado[]).forEach((k) => (novo[k] ? q.set(k, novo[k]!) : q.delete(k)));
    setParams(q);
  };

  if (!a || !b) {
    return (
      <>
        <TituloPagina titulo="Comparar" grifo="dois posts" sub="Escolha um post para cada lado. A comparação mostra as métricas, o que a leitura achou de diferente e o que os dois têm em comum." />
        <div className="comparar-escolha">
          <Seletor lado="a" id={a} outro={b} definir={definir} />
          <span className="comparar-versus t-titulo" aria-hidden>×</span>
          <Seletor lado="b" id={b} outro={a} definir={definir} />
        </div>
      </>
    );
  }
  return <Comparacao a={a} b={b} definir={definir} />;
}

function Seletor({ lado, id, outro, definir }: { lado: Lado; id: string | null; outro: string | null; definir: (n: Partial<Record<Lado, string | null>>) => void }) {
  const [q, setQ] = useState("");
  const buscando = q.trim().length >= 2;
  const escolhido = usePost(id);
  const busca = useBusca(q, 8);
  const sugestoes = usePosts({ ordem: "destaques", limit: 8 });
  const fonte = buscando ? busca : sugestoes;
  const itens = (buscando ? busca.data?.map((r) => r.post) : sugestoes.data?.itens)?.filter((p) => p.id !== outro) ?? [];
  const letra = lado.toUpperCase();

  if (id) {
    const p = escolhido.data;
    return (
      <section className="comparar-slot comparar-slot--fixo" aria-label={`Lado ${letra}, escolhido`}>
        <span className="comparar-letra t-titulo">{letra}</span>
        {escolhido.isLoading ? <Esqueleto altura={180} /> : escolhido.error || !p ? <Erro erro={escolhido.error} titulo="Não achamos esse post" onTentar={() => definir({ [lado]: null })} /> : (
          <div className="comparar-fixo">
            <span className="comparar-fixo-foto"><Miniatura src={p.thumb} alt={p.titulo} reserva={nomePlataforma(p.plataforma)} /></span>
            <div className="pilha">
              <p className="t-h3 corta-3">{p.titulo || p.gancho}</p>
              <p className="t-sec t-pequeno">{p.canal} · {nomePlataforma(p.plataforma)} · {p.formato}</p>
              <div><Botao variante="contorno" tamanho="p" onClick={() => definir({ [lado]: null })}>Trocar este post</Botao></div>
            </div>
          </div>
        )}
      </section>
    );
  }
  return (
    <section className="comparar-slot" aria-label={`Lado ${letra}, a escolher`}>
      <span className="comparar-letra t-titulo">{letra}</span>
      <Campo rotulo={`Buscar o post do lado ${letra}`} esconderRotulo tamanho="g" type="search" placeholder="Busque por ideia, tema ou criador" value={q} onChange={(e) => setQ(e.target.value)} />
      <p className="t-sec t-pequeno">{buscando ? `Resultados para “${q.trim()}”` : "Ou comece por um destaque do top"}</p>
      {fonte.isLoading ? <Esqueleto tipo="linhas" n={5} />
        : fonte.error ? <Erro erro={fonte.error} onTentar={fonte.refetch} />
        : !itens.length ? <Vazio titulo="Nada encontrado">Tente outras palavras, como o tema do post ou o nome do criador.</Vazio>
        : <div className="comparar-resultados">{itens.map((p) => <PostCard key={p.id} post={p} variante="linha" semFicha onAbrir={() => definir({ [lado]: p.id })} />)}</div>}
    </section>
  );
}

function Comparacao({ a, b, definir }: { a: string; b: string; definir: (n: Partial<Record<Lado, string | null>>) => void }) {
  const { data, isLoading, error, refetch } = useComparar(a, b);
  const alvo = useRef<HTMLDivElement>(null);
  const acoes = (
    <>
      <Botao variante="contorno" tamanho="p" onClick={() => definir({ a: b, b: a })}>Trocar lados ⇄</Botao>
      <BotaoExportar alvo={alvo} nome="comparacao" />
    </>
  );
  if (isLoading) return <><TituloPagina titulo="Comparar" grifo="dois posts" /><Esqueleto altura={520} /></>;
  if (error || !data) {
    return (
      <>
        <TituloPagina titulo="Comparar" grifo="dois posts" />
        <Erro erro={error} onTentar={refetch} />
        <div className="linha"><Botao variante="contorno" onClick={() => definir({ a: null, b: null })}>Escolher outros posts</Botao></div>
      </>
    );
  }

  const lei = leitura(data);
  const diferentes = lei.filter((d) => !d.igual);
  const iguais = lei.filter((d) => d.igual);
  const frases = resumir(data);
  const pa = data.a, pb = data.b;
  const metricas: { rotulo: string; a: number | null; b: number | null; fmt: (n: number | null) => string }[] = [
    { rotulo: "× o esperado", a: pa.vezes, b: pb.vezes, fmt: fmtVezes },
    { rotulo: "Engajamento (ER)", a: pa.er, b: pb.er, fmt: fmtPct },
    { rotulo: "Curtidas", a: pa.likes, b: pb.likes, fmt: fmtNum },
    { rotulo: "Comentários", a: pa.comentarios, b: pb.comentarios, fmt: fmtNum },
    { rotulo: "Views", a: pa.views, b: pb.views, fmt: fmtNum },
    { rotulo: "Comentários querendo comprar", a: pa.pct_intencao, b: pb.pct_intencao, fmt: fmtPct },
  ].filter((m) => m.a != null || m.b != null);
  const notas = pa.notas.map((n) => ({ rotulo: n.rotulo, a: n.valor, b: pb.notas.find((x) => x.rotulo === n.rotulo)?.valor ?? null }));

  return (
    <>
      <TituloPagina titulo="Comparar" grifo="dois posts" acoes={acoes} />
      <div ref={alvo} className="comparar-alvo">
        <div className="comparar-fixa" aria-hidden>
          <span className="corta-1"><b>A</b> {pa.canal}</span>
          <span className="corta-1">{pb.canal} <b>B</b></span>
        </div>

        <div className="comparar-palco">
          <Coluna lado="a" post={pa} onTrocar={() => definir({ a: null })} />
          <div className="comparar-meio">
            {metricas.map((m) => <Espelho key={m.rotulo} rotulo={m.rotulo} a={m.a} b={m.b} fmt={m.fmt} destaque />)}
            {notas.length > 0 && (
              <>
                <h2 className="t-titulo comparar-sub">Notas da leitura, de 0 a 10</h2>
                {notas.map((n) => <Espelho key={n.rotulo} rotulo={n.rotulo} a={n.a} b={n.b} fmt={(v) => (v == null ? "–" : String(v))} max={10} />)}
              </>
            )}
          </div>
          <Coluna lado="b" post={pb} onTrocar={() => definir({ b: null })} />
        </div>

        {frases.length > 0 && (
          <Secao titulo="Em resumo" bloco="lima">
            <div className="comparar-resumo">{frases.map((f) => <p key={f}>{f}</p>)}</div>
          </Secao>
        )}

        <Secao titulo="O que muda de um para o outro" sub={diferentes.length ? `${diferentes.length} de ${lei.length} pontos da leitura são diferentes` : undefined}>
          {diferentes.length ? (
            <ul className="comparar-difs">
              {diferentes.map((d) => (
                <li key={d.rotulo} className="comparar-dif">
                  <span className="comparar-dif-a">{d.a}</span>
                  <span className="comparar-dif-rotulo">{d.rotulo}</span>
                  <span className="comparar-dif-b">{d.b}</span>
                </li>
              ))}
            </ul>
          ) : <Vazio titulo="Leitura igual" marca="=">Nos pontos avaliados, os dois posts foram lidos do mesmo jeito. A diferença está nos números acima.</Vazio>}
          {iguais.length > 0 && (
            <p className="comparar-iguais t-pequeno">
              <b>Igual nos dois:</b> {iguais.map((d) => `${d.rotulo} (${d.a})`).join(" · ")}
            </p>
          )}
        </Secao>
      </div>
    </>
  );
}

function Coluna({ lado, post, onTrocar }: { lado: Lado; post: PostDetalhe; onTrocar: () => void }) {
  return (
    <section className={`comparar-coluna comparar-coluna--${lado}`} aria-label={`Post ${lado.toUpperCase()}`}>
      <div className="comparar-coluna-topo">
        <span className="comparar-letra t-titulo">{lado.toUpperCase()}</span>
        {post.top && <Carimbo texto="TOP" sub={post.posicao_top ? `nº ${post.posicao_top}` : undefined} tamanho={56} giro={lado === "a" ? -9 : 8} />}
      </div>
      <MolduraCelular largura={240}>
        <Midia midia={post.midia} thumb={post.thumb} titulo={post.titulo} url={post.url} plataforma={post.plataforma} />
      </MolduraCelular>
      <div className="comparar-quem">
        <Link to={`/criadores/${encodeURIComponent(post.canal_id)}`} className="comparar-canal corta-2">{post.canal}</Link>
        <span className="t-sec t-pequeno">{nomePlataforma(post.plataforma)} · {post.formato}{post.seguidores ? ` · ${fmtNum(post.seguidores)} seguidores` : ""}</span>
        <div className="nao-imprimir"><Botao variante="fantasma" tamanho="p" onClick={onTrocar}>Trocar este post</Botao></div>
      </div>
    </section>
  );
}

/** Uma linha espelhada: valor e barra de A crescendo para a esquerda, de B para a direita, rótulo no meio. */
function Espelho({ rotulo, a, b, fmt, max, destaque }: { rotulo: string; a: number | null; b: number | null; fmt: (n: number | null) => string; max?: number; destaque?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const entrou = useEntrou(ref);
  const teto = max ?? Math.max(a ?? 0, b ?? 0);
  const larg = (v: number | null) => (entrou && v != null && teto > 0 ? `${Math.max((v / teto) * 100, v > 0 ? 2 : 0)}%` : "0%");
  const maior = destaque && a != null && b != null && a !== b ? (a > b ? "a" : "b") : null;
  return (
    <div ref={ref} className={`comparar-espelho${destaque ? " comparar-espelho--g" : ""}`}>
      <span className={`comparar-valor comparar-valor--a${maior === "a" ? " comparar-valor--maior" : ""}`}>{fmt(a)}{maior === "a" && <span className="so-leitor"> (maior)</span>}</span>
      <span className="comparar-rotulo">{rotulo}</span>
      <span className={`comparar-valor comparar-valor--b${maior === "b" ? " comparar-valor--maior" : ""}`}>{fmt(b)}{maior === "b" && <span className="so-leitor"> (maior)</span>}</span>
      <span className="comparar-trilho comparar-trilho--a"><span className={`comparar-barra${maior === "b" ? " comparar-barra--menor" : ""}`} style={{ width: larg(a) }} /></span>
      <span className="comparar-trilho comparar-trilho--b"><span className={`comparar-barra${maior === "a" ? " comparar-barra--menor" : ""}`} style={{ width: larg(b) }} /></span>
    </div>
  );
}
