// Painel de detalhe do post. Já está montado no <AppShell>: NÃO monte de novo nas páginas.
// Abre sozinho quando a URL tem ?post=<id> (é o que o <PostCard> faz ao clicar) e fecha com Esc, clique fora ou "Fechar".
// Para abrir de outro lugar:  const abrir = useAbrirPost();  abrir(post.id)
// Em telas estreitas ocupa a tela toda. A moldura do celular compartilha o layoutId com a miniatura do card de origem.
import { useEffect, useRef } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import { usePost } from "../api/hooks";
import type { PostDetalhe } from "../api/tipos";
import { fmtData, fmtNum, fmtPct, fmtVezes, nomePlataforma, nomePorte } from "../util/formato";
import { Botao } from "./Botao";
import { BotaoColecao } from "./BotaoColecao";
import { Carimbo } from "./Carimbo";
import { Chip } from "./Chip";
import { Erro, Esqueleto } from "./Estados";
import { Etiqueta } from "./Etiqueta";
import { Midia } from "./Midia";
import { MolduraCelular } from "./MolduraCelular";
import { NumeroConta } from "./NumeroConta";
import { PostCard, layoutIdDoPost } from "./PostCard";

/** Devolve uma função que abre (id) ou fecha (null) o painel mexendo só no parâmetro ?post=. */
export function useAbrirPost() {
  const [, setParams] = useSearchParams();
  return (id: string | null) =>
    setParams((p) => {
      const q = new URLSearchParams(p);
      if (id) q.set("post", id);
      else q.delete("post");
      return q;
    });
}

const EASE = [0.22, 1, 0.36, 1] as const;

export function PainelPost() {
  const [params] = useSearchParams();
  const id = params.get("post");
  const abrir = useAbrirPost();
  const fechar = () => abrir(null);
  const painel = useRef<HTMLElement>(null);
  const voltarPara = useRef<Element | null>(null);

  useEffect(() => {
    if (!id) return;
    voltarPara.current = voltarPara.current ?? document.activeElement;
    painel.current?.focus();
    const tecla = (e: KeyboardEvent) => e.key === "Escape" && fechar();
    document.addEventListener("keydown", tecla);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", tecla);
      document.body.style.overflow = "";
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);
  useEffect(() => {
    if (id) return;
    (voltarPara.current as HTMLElement | null)?.focus?.();
    voltarPara.current = null;
  }, [id]);

  return (
    <AnimatePresence>
      {id && (
        <motion.div key="fundo" className="painel-fundo" onClick={fechar} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }} />
      )}
      {id && (
        <motion.aside
          key="painel" ref={painel} className="painel" role="dialog" aria-modal="true" aria-label="Detalhe do post" tabIndex={-1}
          initial={{ x: "100%" }} animate={{ x: 0 }} exit={{ x: "100%" }} transition={{ duration: 0.25, ease: EASE }}
        >
          <Conteudo id={id} fechar={fechar} />
        </motion.aside>
      )}
    </AnimatePresence>
  );
}

function Conteudo({ id, fechar }: { id: string; fechar: () => void }) {
  const { data: post, isLoading, error, refetch } = usePost(id);
  return (
    <>
      <header className="painel-topo">
        <span className="t-pequeno t-sec">
          {post ? `${nomePlataforma(post.plataforma)} · ${post.formato}${post.publicado ? ` · ${fmtData(post.publicado)}` : ""}` : "Detalhe do post"}
        </span>
        <Botao variante="fantasma" tamanho="p" onClick={fechar}>Fechar ×</Botao>
      </header>
      <div className="painel-rolagem">
        {isLoading && (
          <div className="painel-cabeca">
            <MolduraCelular largura={300} layoutId={layoutIdDoPost(id)}><Esqueleto altura="100%" /></MolduraCelular>
            <div className="pilha"><Esqueleto altura={72} /><Esqueleto tipo="texto" n={4} /></div>
          </div>
        )}
        {error && <Erro erro={error} onTentar={refetch} />}
        {post && <Detalhe post={post} />}
      </div>
      {post && (
        <footer className="painel-acoes">
          <BotaoColecao postId={post.id} variante="primario" />
          <Botao variante="contorno" para={`/comparar?a=${encodeURIComponent(post.id)}`}>Comparar</Botao>
          <Botao variante="fantasma" href={post.url}>Abrir no {nomePlataforma(post.plataforma)}</Botao>
        </footer>
      )}
    </>
  );
}

function Detalhe({ post }: { post: PostDetalhe }) {
  const c = post.criador;
  return (
    <>
      <div className="painel-cabeca">
        <div className="painel-celular">
          <MolduraCelular largura={300} layoutId={layoutIdDoPost(post.id)}>
            <Midia midia={post.midia} thumb={post.thumb} titulo={post.titulo} url={post.url} plataforma={post.plataforma} />
          </MolduraCelular>
          {post.top && <Carimbo className="painel-carimbo" texto="TOP" sub={post.posicao_top ? `nº ${post.posicao_top}` : "10%"} cheio tamanho={60} />}
        </div>
        <div className="painel-resumo">
          <h2 className="painel-titulo">{post.titulo || post.gancho}</h2>
          {post.vezes != null
            ? <Etiqueta tamanho="g" valor={fmtVezes(post.vezes)} rotulo="o esperado" />
            : <p className="t-sec t-pequeno">Este post não concorre ao top (fora da base elegível).</p>}
          <dl className="painel-nums">
            <div><dt>ER</dt><dd><NumeroConta valor={post.er} formato={fmtPct} /></dd></div>
            <div><dt>Curtidas</dt><dd><NumeroConta valor={post.likes} /></dd></div>
            <div><dt>Comentários</dt><dd><NumeroConta valor={post.comentarios} /></dd></div>
            {post.views != null && <div><dt>Views</dt><dd><NumeroConta valor={post.views} /></dd></div>}
            {post.pct_intencao != null && <div className="painel-num-largo"><dt>Comentários com intenção de compra</dt><dd><NumeroConta valor={post.pct_intencao} formato={fmtPct} /></dd></div>}
          </dl>
          <p className="t-pequeno t-sec">“× o esperado” compara com o que se previa para este perfil, formato e idade do post. ER = (curtidas + comentários) ÷ seguidores.</p>
        </div>
      </div>

      {post.gancho && (
        <figure className="painel-gancho">
          <blockquote>{post.gancho}</blockquote>
          <figcaption>Gancho, nos 3 primeiros segundos{post.tipo_gancho ? ` · ${post.tipo_gancho}` : ""}</figcaption>
        </figure>
      )}

      {post.leitura.length > 0 && (
        <section className="painel-secao">
          <h3 className="t-h3">O que a leitura automática viu</h3>
          <div className="linha" style={{ gap: 6 }}>
            {post.leitura.map((l, i) => (l.valor === "sim" ? <Chip key={i}>✓ {l.rotulo}</Chip> : <Chip key={i} rotulo={l.rotulo}>{l.valor}</Chip>))}
          </div>
          {post.metodo_leitura && <p className="t-pequeno t-sec">Lido por {post.metodo_leitura}.</p>}
        </section>
      )}

      {post.notas.length > 0 && (
        <section className="painel-secao">
          <h3 className="t-h3">Notas de 0 a 10</h3>
          <ul className="painel-notas">
            {post.notas.map((n) => (
              <li key={n.rotulo}>
                <span>{n.rotulo}</span>
                <span className="nota-trilho" role="img" aria-label={`${n.valor} de 10${n.mediana_top != null ? `; mediana do top ${n.mediana_top}` : ""}`}>
                  <span className="nota-barra" style={{ width: `${n.valor * 10}%` }} />
                  {n.mediana_top != null && <span className="nota-marca" style={{ left: `${n.mediana_top * 10}%` }} />}
                </span>
                <b>{n.valor}</b>
              </li>
            ))}
          </ul>
          <p className="t-pequeno t-sec">O traço marca a mediana do top.</p>
        </section>
      )}

      {post.elementos.length > 0 && (
        <section className="painel-secao">
          <h3 className="t-h3">O que explica a atenção</h3>
          <ol className="painel-elementos">
            {post.elementos.map((e, i) => <li key={i}>{e}</li>)}
          </ol>
        </section>
      )}

      {post.legenda && (
        <details className="painel-legenda">
          <summary>Legenda do post</summary>
          <p>{post.legenda}</p>
        </details>
      )}

      {c && (
        <Link to={`/criadores/${encodeURIComponent(c.id)}`} className="painel-criador">
          <span>
            <span className="t-pequeno t-sec">Quem publicou</span>
            <span className="painel-criador-nome">{c.nome}</span>
            <span className="t-pequeno">{fmtNum(c.seguidores)} seguidores · perfil {nomePorte(c.porte)} · {c.n_top} no top de {fmtNum(c.n_posts)} posts</span>
          </span>
          <span className="painel-criador-seta" aria-hidden>→</span>
        </Link>
      )}

      {post.parecidos.length > 0 && (
        <section className="painel-secao">
          <h3 className="t-h3">Posts parecidos</h3>
          <div className="painel-parecidos">
            {post.parecidos.map((p) => <PostCard key={p.id} post={p} variante="compacto" semFicha />)}
          </div>
        </section>
      )}
    </>
  );
}
