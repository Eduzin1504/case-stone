// A resposta do agente: storyboard da pauta (modo gerar) e/ou explicação com achados e referências (analisar, recomendar).
import { useRef, useState, type KeyboardEvent } from "react";
import { useGerarVideo, useVideoCriativo } from "../../api/hooks";
import type { Criativo, PostResumo, RespostaAgente } from "../../api/tipos";
import { BarraPar, Botao, BotaoColecao, BotaoExportar, Comprovante, Etiqueta, LegendaBarraPar, Markdown, PostCard, Secao, Seg } from "../../componentes";
import { useFoco } from "../../contexto/Foco";
import { fmtInt, fmtVezes } from "../../util/formato";


const tipoCurto = (formato: string) => (/carross|estátic|estatic|card|slide/i.test(formato) ? "Carrossel" : /reel|short|vídeo|video/i.test(formato) ? "Reels" : formato.split(/[\s,(—-]/)[0] || "Pauta");

function Storyboard({ c }: { c: Criativo }) {
  const tira = useRef<HTMLOListElement>(null);
  const [grade, setGrade] = useState(false);
  const cenas = c.cenas;
  const andar = (d: number) => {
    const el = tira.current;
    if (!el) return;
    const passo = (el.firstElementChild as HTMLElement | null)?.offsetWidth ?? 260;
    el.scrollBy({ left: d * (passo + 16), behavior: "smooth" });
  };
  const tecla = (e: KeyboardEvent) => {
    const el = tira.current;
    if (!el) return;
    if (e.key === "ArrowRight") andar(1);
    else if (e.key === "ArrowLeft") andar(-1);
    else if (e.key === "Home") el.scrollTo({ left: 0, behavior: "smooth" });
    else if (e.key === "End") el.scrollTo({ left: el.scrollWidth, behavior: "smooth" });
    else return;
    e.preventDefault();
  };
  return (
    <div className="criar-story">
      <div className="criar-story-cab nao-imprimir" data-nao-exportar>
        <span className="t-sec t-pequeno">{fmtInt(cenas.length)} {cenas.length === 1 ? "quadro" : "quadros"}{grade ? "" : " · role ou use as setas do teclado"}</span>
        <span className="linha">
          <Botao variante="fantasma" tamanho="p" onClick={() => setGrade(!grade)} aria-pressed={grade}>{grade ? "Ver em tira" : "Ver todos de uma vez"}</Botao>
          {!grade && (
            <>
              <button type="button" className="criar-seta" onClick={() => andar(-1)} aria-label="Quadro anterior">←</button>
              <button type="button" className="criar-seta" onClick={() => andar(1)} aria-label="Próximo quadro">→</button>
            </>
          )}
        </span>
      </div>
      <ol
        ref={tira} className={`criar-tira${grade ? " criar-tira--grade" : ""}`} tabIndex={0} onKeyDown={tecla}
        aria-label={`Storyboard com ${cenas.length} quadros. Use as setas para percorrer.`}
      >
        {cenas.length === 0 && (
          <li className="criar-quadro criar-quadro--capa bloco-lima"><p className="criar-gancho t-titulo">{c.gancho}</p><p>{c.roteiro}</p></li>
        )}
        {cenas.map((cena, i) => {
          const capa = i === 0;
          const cta = !capa && (/\bcta\b|convite|fech/i.test(cena.rotulo ?? "") || /^cta\b/i.test(cena.texto));
          const longo = cena.texto.length > 420;
          return (
            <li key={i} className={`criar-quadro${capa ? " criar-quadro--capa bloco-lima" : ""}${cta ? " criar-quadro--cta" : ""}${longo ? " criar-quadro--longo" : ""}`}>
              <div className="criar-quadro-cab">
                <span className="criar-quadro-n" aria-label={`Quadro ${cena.n}`}>{cena.n}</span>
                {cena.tempo && <span className="criar-quadro-tempo t-mono">{cena.tempo}</span>}
              </div>
              {capa && <p className="criar-gancho t-titulo">{c.gancho}</p>}
              {cena.rotulo && <p className="criar-quadro-rotulo">{cena.rotulo}</p>}
              <p className="criar-quadro-texto">{cena.texto}</p>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

function VideoCriativo({ c }: { c: Criativo }) {
  // gera a peça pronta: clipes b-roll pela Feita + texto das cenas no template da marca
  const gerar = useGerarVideo();
  const [id, setId] = useState<string | null>(null);
  const { data: job } = useVideoCriativo(id);
  const url = job?.resultado?.url;
  if (url)
    return (
      <div className="criar-video">
        <video src={url} controls playsInline className="criar-video-player" aria-label="Reels gerado a partir do roteiro" />
        <a className="botao botao--contorno botao--p" href={url} download>Baixar MP4</a>
      </div>
    );
  const rodando = gerar.isPending || job?.estado === "rodando";
  const erro = gerar.error?.message ?? (job?.estado === "erro" ? job.erro : null);
  return (
    <div className="criar-video nao-imprimir" data-nao-exportar>
      <Botao variante="contorno" tamanho="p" disabled={rodando} onClick={() => gerar.mutateAsync(c).then((r) => setId(r.id))}>
        {rodando ? "Gerando o Reels…" : "Gerar o Reels com IA"}
      </Botao>
      <span className="t-pequeno t-sec" role="status">
        {rodando ? (job?.etapas.at(-1) ?? "Enviando o roteiro") + "… (uns 10 minutos)" : erro ?? "Clipes sem rosto pela Feita + texto das cenas no template da marca."}
      </span>
    </div>
  );
}

function Legenda({ texto }: { texto: string }) {
  const [estado, setEstado] = useState<"" | "ok" | "falhou">("");
  const copiar = async () => {
    try {
      await navigator.clipboard.writeText(texto);
      setEstado("ok");
    } catch {
      setEstado("falhou");
    }
    setTimeout(() => setEstado(""), 2200);
  };
  return (
    <div className="criar-legenda">
      <div className="entre">
        <h3 className="t-h3">Legenda</h3>
        <span data-nao-exportar className="nao-imprimir">
          <Botao variante={estado === "ok" ? "primario" : "contorno"} tamanho="p" onClick={copiar}>{estado === "ok" ? "✓ Copiado" : "Copiar legenda"}</Botao>
        </span>
      </div>
      <p className="criar-legenda-texto">{texto}</p>
      <span className="t-pequeno t-alerta" role="status">{estado === "falhou" ? "O navegador não deixou copiar. Selecione o texto e copie." : ""}</span>
    </div>
  );
}

function Referencias({ posts }: { posts: PostResumo[] }) {
  const { foco } = useFoco();
  // as referências são sempre do Foco A: fora dele o painel e as coleções não as conhecem, então o card abre o post original
  const fora = foco !== "A";
  return (
    <ul className="criar-refs">
      {posts.map((p) => (
        <li key={p.id}>
          <PostCard post={p} variante="compacto" semFicha={fora} onAbrir={fora ? () => window.open(p.url, "_blank", "noopener") : undefined} />
          {!fora && <span data-nao-exportar className="nao-imprimir"><BotaoColecao postId={p.id} tamanho="p" variante="fantasma" /></span>}
        </li>
      ))}
    </ul>
  );
}

function Pauta({ r }: { r: RespostaAgente }) {
  const [i, setI] = useState(0);
  const alvo = useRef<HTMLDivElement>(null);
  const c = r.criativos[Math.min(i, r.criativos.length - 1)];
  const inspirado = c.inspirado_em.map((id) => r.referencias.find((p) => p.id === id)).filter((p): p is PostResumo => !!p);
  const pendencias = (r.pendencias ?? "").trim();
  return (
    <section className="criar-pauta">
      <div className="criar-pauta-cab">
        {r.criativos.length > 1 && (
          <Seg
            rotulo="Opções de pauta" valor={String(i)} onChange={(v) => setI(Number(v))}
            opcoes={r.criativos.map((x, k) => ({ valor: String(k), rotulo: `Opção ${k + 1} · ${tipoCurto(x.formato)}` }))}
          />
        )}
        <BotaoExportar alvo={alvo} nome={`pauta-${r.id}-${i + 1}`} />
      </div>
      <div ref={alvo} className="criar-exporta" key={i}>
        <p className="criar-formato"><b>{c.formato}</b><span className="t-sec"> · pilar: {c.pilar}</span></p>
        <Storyboard c={c} />
        {tipoCurto(c.formato) === "Reels" && <VideoCriativo c={c} />}
        <div className="criar-abaixo">
          <div className="criar-textos">
            <div className="criar-cta">
              <p className="t-pequeno">Chamada para ação</p>
              <p className="criar-cta-texto">{c.cta}</p>
            </div>
            <Legenda texto={c.legenda} />
          </div>
          <Comprovante
            titulo="Checagem" sub={`${tipoCurto(c.formato)} · ${fmtInt(c.cenas.length)} quadros`}
            linhas={[
              { rotulo: "Referências reais", valor: `${inspirado.length} de ${c.inspirado_em.length}` },
              { rotulo: "Tentativas", valor: r.tentativas == null ? "–" : fmtInt(r.tentativas) },
              { rotulo: "Confiança", valor: r.baixa_confianca ? "baixa" : "normal", destaque: r.baixa_confianca },
              ...(r.filtros_relaxados.length ? [{ rotulo: "Filtros afrouxados", valor: r.filtros_relaxados.join(", ") }] : []),
              { rotulo: "Pendências", valor: pendencias ? "sim" : "nenhuma" },
            ]}
            total={{ rotulo: "Checagem", valor: pendencias ? "Pendente" : "OK" }}
            rodape={<>cada referência é um post real da base<br />revise antes de publicar</>}
          >
            {pendencias ? <p>{pendencias}</p> : null}
          </Comprovante>
        </div>
      </div>
      {inspirado.length > 0 && (
        <Secao titulo="Inspirado em" sub="Os posts reais da base que serviram de referência para esta opção.">
          <Referencias posts={inspirado} />
        </Secao>
      )}
    </section>
  );
}

function Achados({ r }: { r: RespostaAgente }) {
  const [todos, setTodos] = useState(false);
  const peso = (l: number) => Math.abs(Math.log(l || 1));
  const ordenados = [...r.achados].sort((a, b) => peso(b.lift ?? 1) - peso(a.lift ?? 1));
  const visiveis = todos ? ordenados : ordenados.slice(0, 6);
  const max = Math.max(...ordenados.map((a) => Math.max(a.freq_top, a.freq_controle)), 0.05);
  return (
    <Secao titulo="Achados" sub="Os padrões do recorte que sustentam a resposta: frequência no top e no grupo de controle." bloco="superficie">
      <LegendaBarraPar />
      <div>
        {visiveis.map((a) => (
          <BarraPar key={a.campo + a.valor} rotulo={a.rotulo} top={a.freq_top} controle={a.freq_controle} lift={a.lift} selo={a.selo} fragil={(a as typeof a & { fragil?: boolean }).fragil} max={max} />
        ))}
      </div>
      {ordenados.length > 6 && <div><Botao variante="fantasma" tamanho="p" onClick={() => setTodos(!todos)} aria-expanded={todos}>{todos ? "Mostrar menos" : `Mostrar os ${ordenados.length} achados`}</Botao></div>}
    </Secao>
  );
}

export function Resposta({ r }: { r: RespostaAgente }) {
  const gerar = r.modo === "gerar_criativo";
  const temPauta = r.criativos.length > 0;
  const aviso = (r.baixa_confianca || r.filtros_relaxados.length > 0) && (
    <p className="criar-aviso" role="note">
      {r.baixa_confianca && <><b>Baixa confiança.</b> Poucos posts da base bateram com o pedido: trate como ponto de partida. </>}
      {r.filtros_relaxados.length > 0 && <>Para achar referências, o agente afrouxou: {r.filtros_relaxados.join(", ")}.</>}
    </p>
  );
  // o texto cita os posts pelo id entre colchetes: troca pelo nome do canal, com link para o post original
  const texto = (r.explicacao ?? "").trim().replace(/\[([\w-]{6,})\](?!\()/g, (tudo, id: string) => {
    const p = r.referencias.find((x) => x.id === id);
    return p ? `[${p.canal.split("|")[0].trim()}](${p.url})` : tudo;
  });
  const explicacao = texto && <Markdown texto={texto} className="criar-md" />;
  const forte = [...r.achados].sort((a, b) => (b.lift ?? 0) - (a.lift ?? 0))[0];
  if (gerar)
    return (
      <div className="criar-resposta">
        {aviso}
        {temPauta ? <Pauta r={r} /> : explicacao}
        {temPauta && explicacao && (
          <details className="criar-porque">
            <summary>Por que esta pauta</summary>
            {explicacao}
          </details>
        )}
        {r.achados.length > 0 && <Achados r={r} />}
      </div>
    );
  return (
    <div className="criar-resposta">
      {aviso}
      <div className="criar-leitura">
        {explicacao}
        <aside className="criar-lateral">
          {forte && <Etiqueta tamanho="g" valor={fmtVezes(forte.lift)} rotulo={<>{forte.rotulo}: o achado mais forte do recorte</>} />}
          {r.referencias.length > 0 && (
            <>
              <h3 className="t-h3">Posts reais citados na resposta</h3>
              <Referencias posts={r.referencias} />
            </>
          )}
        </aside>
      </div>
      {r.achados.length > 0 && <Achados r={r} />}
      {temPauta && (
        <Secao titulo="Pauta sugerida">
          <Pauta r={r} />
        </Secao>
      )}
    </div>
  );
}
