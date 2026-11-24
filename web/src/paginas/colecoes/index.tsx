// /colecoes (capas) e /colecoes/:id (os posts de uma coleção). As coleções são por foco.
import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useApagarColecao, useColecao, useColecoes, useCriarColecao, useEditarColecao, useRemoverPost } from "../../api/hooks";
import { ErroApi } from "../../api/cliente";
import type { Colecao } from "../../api/tipos";
import { Botao, BotaoExportar, Campo, Erro, Esqueleto, Miniatura, PostCard, TituloPagina, Vazio } from "../../componentes";
import { useFoco } from "../../contexto/Foco";
import { fmtData, fmtInt } from "../../util/formato";
import "./colecoes.css";

const nPosts = (n: number) => `${fmtInt(n)} ${n === 1 ? "post" : "posts"}`;
const COMO_SALVAR = "Abra qualquer post (no catálogo, na busca ou nos rankings) e use o botão Salvar, no painel que desliza da direita.";

/** A pergunta que vai pronta para o agente, citando os temas e os ganchos dos posts salvos. */
export function perguntaDaColecao(c: Colecao): string {
  const unicos = (xs: (string | null)[]) => [...new Set(xs.filter((x): x is string => !!x && x.trim().length > 0))];
  const temas = unicos(c.posts.map((p) => p.tema)).slice(0, 4);
  const ganchos = unicos(c.posts.map((p) => p.gancho)).slice(0, 3);
  return [
    `Pauta inspirada nos posts que salvei na coleção "${c.nome}".`,
    temas.length ? `Temas: ${temas.join(", ")}.` : "",
    ganchos.length ? `Ganchos que funcionaram: ${ganchos.map((g) => `"${g.replace(/\s+/g, " ").slice(0, 110)}"`).join("; ")}.` : "",
  ].filter(Boolean).join(" ");
}

function Capa({ c }: { c: Colecao }) {
  const [modo, setModo] = useState<"ver" | "renomear" | "apagar">("ver");
  const [nome, setNome] = useState(c.nome);
  const editar = useEditarColecao(), apagar = useApagarColecao();
  const thumbs = c.posts.slice(0, 4);
  const salvar = (e: FormEvent) => {
    e.preventDefault();
    const n = nome.trim();
    if (!n || n === c.nome) return setModo("ver");
    editar.mutate({ id: c.id, nome: n }, { onSuccess: () => setModo("ver") });
  };
  const erro = editar.error ?? apagar.error;
  return (
    <li className="colecoes-capa">
      <Link to={`/colecoes/${c.id}`} className="colecoes-capa-link" aria-label={`${c.nome}, ${nPosts(c.posts.length)}`}>
        <span className={`colecoes-mosaico colecoes-mosaico--${Math.min(thumbs.length, 4)}`}>
          {thumbs.map((p) => <span key={p.id}><Miniatura src={p.thumb} alt="" reserva={p.plataforma} /></span>)}
          {thumbs.length === 0 && <span className="colecoes-mosaico-vazio t-titulo">Vazia</span>}
        </span>
        {modo !== "renomear" && <span className="colecoes-capa-nome t-titulo">{c.nome}</span>}
      </Link>
      {modo === "renomear" && (
        <form className="colecoes-renomear" onSubmit={salvar}>
          <Campo rotulo="Novo nome" esconderRotulo value={nome} onChange={(e) => setNome(e.target.value)} autoFocus maxLength={80} onKeyDown={(e) => e.key === "Escape" && setModo("ver")} />
          <Botao tamanho="p" type="submit" ocupado={editar.isPending}>Salvar</Botao>
          <Botao tamanho="p" variante="fantasma" onClick={() => { setNome(c.nome); setModo("ver"); }}>Cancelar</Botao>
        </form>
      )}
      {modo === "apagar" ? (
        <div className="colecoes-confirma" role="alertdialog" aria-label={`Apagar a coleção ${c.nome}?`}>
          <span>Apagar esta coleção? Os posts continuam no catálogo.</span>
          <span className="linha">
            <Botao tamanho="p" className="colecoes-apagar" onClick={() => apagar.mutate(c.id)} ocupado={apagar.isPending} autoFocus>Apagar</Botao>
            <Botao tamanho="p" variante="fantasma" onClick={() => setModo("ver")}>Cancelar</Botao>
          </span>
        </div>
      ) : (
        <div className="colecoes-capa-pe">
          <span className="t-sec">{nPosts(c.posts.length)}</span>
          {modo === "ver" && (
            <span className="colecoes-capa-acoes">
              <button type="button" onClick={() => setModo("renomear")} aria-label={`Renomear ${c.nome}`}>Renomear</button>
              <button type="button" onClick={() => setModo("apagar")} aria-label={`Apagar ${c.nome}`}>Apagar</button>
            </span>
          )}
        </div>
      )}
      {c.nota && modo === "ver" && <p className="t-pequeno t-sec corta-2">{c.nota}</p>}
      {erro && <p className="t-pequeno t-alerta" role="alert">{erro.message}</p>}
    </li>
  );
}

function Nova({ aoFechar }: { aoFechar: () => void }) {
  const [nome, setNome] = useState("");
  const [nota, setNota] = useState("");
  const [faltou, setFaltou] = useState(false);
  const criar = useCriarColecao();
  const enviar = (e: FormEvent) => {
    e.preventDefault();
    if (!nome.trim()) return setFaltou(true);
    criar.mutate({ nome: nome.trim(), nota: nota.trim() }, { onSuccess: aoFechar });
  };
  return (
    <form className="colecoes-nova bloco-lima" onSubmit={enviar}>
      <h2 className="t-titulo t-h2">Nova coleção</h2>
      <Campo rotulo="Nome" value={nome} onChange={(e) => { setNome(e.target.value); setFaltou(false); }} placeholder="ex.: Ganchos com número" autoFocus maxLength={80} erro={faltou ? "Dê um nome para a coleção." : null} />
      <Campo rotulo="Nota" value={nota} onChange={(e) => setNota(e.target.value)} placeholder="Para que serve (opcional)" maxLength={300} />
      <div className="linha">
        <Botao type="submit" ocupado={criar.isPending}>Criar coleção</Botao>
        <Botao variante="fantasma" onClick={aoFechar}>Cancelar</Botao>
      </div>
      {criar.error && <p className="t-alerta" role="alert">{criar.error.message}</p>}
    </form>
  );
}

function Lista() {
  const { foco, info } = useFoco();
  const { data, isLoading, error, refetch } = useColecoes();
  const [nova, setNova] = useState(false);
  const itens = [...(data ?? [])].sort((a, b) => Number(b.posts.length > 0) - Number(a.posts.length > 0)); // as com posts primeiro
  return (
    <>
      <TituloPagina
        titulo="Coleções" grifo={`do foco ${foco}`}
        sub={<>Posts que você separou para usar de referência{info ? <> em {info.nome}</> : null}. Cada foco tem as suas.</>}
        acoes={!nova && <Botao onClick={() => setNova(true)}>Nova coleção</Botao>}
      />
      {nova && <Nova aoFechar={() => setNova(false)} />}
      {isLoading && <Esqueleto tipo="cards" n={4} />}
      {error && <Erro erro={error} onTentar={refetch} />}
      {data && itens.length === 0 && !nova && (
        <Vazio titulo="Nenhuma coleção neste foco" acao={<><Botao onClick={() => setNova(true)}>Nova coleção</Botao><Botao variante="contorno" para="/catalogo">Ir para o catálogo</Botao></>}>
          {COMO_SALVAR} Dá para criar a coleção ali mesmo.
        </Vazio>
      )}
      {itens.length > 0 && <ul className="colecoes-capas">{itens.map((c) => <Capa key={c.id} c={c} />)}</ul>}
    </>
  );
}

function Dentro({ id }: { id: string }) {
  const { data: c, isLoading, error, refetch } = useColecao(id);
  const editar = useEditarColecao(), remover = useRemoverPost();
  const [nota, setNota] = useState("");
  const [salva, setSalva] = useState(false);
  const alvo = useRef<HTMLDivElement>(null);
  const navegar = useNavigate();
  useEffect(() => { if (c) setNota(c.nota ?? ""); }, [c?.id, c?.nota]); // eslint-disable-line react-hooks/exhaustive-deps

  const voltar = <Botao variante="contorno" para="/colecoes">← Coleções</Botao>;
  if (isLoading) return <><TituloPagina titulo="Coleção" /><Esqueleto tipo="cards" n={6} /></>;
  if ((error instanceof ErroApi && error.status === 404) || (!error && !c))
    return <><TituloPagina titulo="Coleção" /><Vazio titulo="Essa coleção não existe mais" acao={voltar}>Ela pode ter sido apagada, ou o link está incompleto. Suas coleções estão na lista.</Vazio></>;
  if (error || !c) return <><TituloPagina titulo="Coleção" /><Erro erro={error} onTentar={refetch} /><div>{voltar}</div></>;

  const mudou = nota.trim() !== (c.nota ?? "").trim();
  const salvarNota = (e: FormEvent) => {
    e.preventDefault();
    editar.mutate({ id: c.id, nota: nota.trim() }, { onSuccess: () => { setSalva(true); setTimeout(() => setSalva(false), 2000); } });
  };
  return (
    <>
      <TituloPagina
        titulo={c.nome}
        sub={<>{nPosts(c.posts.length)} · Foco {c.foco} · criada em {fmtData(c.criada_em)}</>}
        acoes={voltar}
      />
      <form className="colecoes-nota" onSubmit={salvarNota}>
        <Campo rotulo="Nota da coleção" multilinha rows={2} value={nota} onChange={(e) => setNota(e.target.value)} placeholder="Para que serve esta coleção? O que os posts têm em comum?" maxLength={600} />
        <div className="linha">
          {mudou && <Botao tamanho="p" type="submit" ocupado={editar.isPending}>Salvar nota</Botao>}
          {mudou && <Botao tamanho="p" variante="fantasma" onClick={() => setNota(c.nota ?? "")}>Desfazer</Botao>}
          <span className="t-pequeno t-sec" role="status">{salva && !mudou ? "✓ Nota salva" : ""}</span>
          {editar.error && <span className="t-pequeno t-alerta" role="alert">{editar.error.message}</span>}
        </div>
      </form>

      {c.posts.length === 0 ? (
        <Vazio titulo="Coleção vazia" acao={<Botao para="/catalogo">Ir para o catálogo</Botao>}>{COMO_SALVAR}</Vazio>
      ) : (
        <>
          <div className="colecoes-acoes nao-imprimir">
            <Botao variante="lima" tamanho="g" onClick={() => navegar(`/criar?pergunta=${encodeURIComponent(perguntaDaColecao(c))}`)}>Criar pauta a partir desta coleção →</Botao>
            <BotaoExportar alvo={alvo} nome={`colecao-${c.nome.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`} tamanho="m" />
          </div>
          {remover.error && <Erro erro={remover.error} />}
          <div ref={alvo} className="colecoes-exporta">
            <p className="colecoes-exporta-titulo t-titulo t-h2">{c.nome}</p>
            <div className="mosaico">
              {c.posts.map((p, i) => (
                <div key={p.id} className={`colecoes-item${i === 0 && c.posts.length > 2 ? " colecoes-item--destaque" : p.tem_video ? " colecoes-item--alto" : ""}`}>
                  <PostCard post={p} destaque={i === 0 && c.posts.length > 2} />
                  <button
                    type="button" className="colecoes-remover" data-nao-exportar
                    onClick={() => remover.mutate({ colecao: c.id, post: p.id })} disabled={remover.isPending}
                    aria-label={`Remover da coleção: ${p.titulo || p.canal}`}
                  >× Remover</button>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </>
  );
}

export default function Colecoes() {
  const { id } = useParams();
  return id ? <Dentro id={id} /> : <Lista />;
}
