// /criar: o agente. Três modos, respostas salvas (sem rede) ou pergunta nova (trabalho em segundo plano, ?job=ID).
// ?pergunta=… chega pré-preenchido (vindo de uma coleção).
import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useAgente, useAgenteSalvas, useOpcoesAgente, usePerguntarAgente, useVideosGerados } from "../../api/hooks";
import { ErroApi } from "../../api/cliente";
import type { ModoAgente, RespostaAgente } from "../../api/tipos";
import { Botao, Campo, Erro, Esqueleto, Seg, Seletor, TituloPagina, Vazio } from "../../componentes";
import { useFoco } from "../../contexto/Foco";
import { fmtData, nomePorte } from "../../util/formato";
import { Progresso } from "../avaliar/Progresso";
import { Resposta } from "./Resposta";
import "./criar.css";

const MODOS: { valor: ModoAgente; rotulo: string }[] = [
  { valor: "gerar_criativo", rotulo: "Gerar pauta" },
  { valor: "analisar", rotulo: "Analisar" },
  { valor: "recomendar", rotulo: "Recomendar" },
];
const SOBRE: Record<ModoAgente, string> = {
  gerar_criativo: "Descreva o post. O agente devolve opções de pauta em storyboard, com legenda e chamada para ação.",
  analisar: "Faça uma pergunta sobre o que diferencia o top. A resposta vem com os achados e os posts que a sustentam.",
  recomendar: "Peça uma recomendação editorial. O agente responde com base nos padrões e nas referências.",
};
const EXEMPLOS: Record<ModoAgente, string[]> = {
  gerar_criativo: [
    "Reels de Natal com dicas de vendas para quem vende comida em casa",
    "Carrossel de fim de ano sobre separar o dinheiro do negócio do dinheiro de casa",
    "Reels para manicure que atende em casa sobre cobrar o deslocamento",
  ],
  analisar: ["O que diferencia os carrosséis de alto engajamento no Instagram?", "Quais ganchos aparecem mais no top do YouTube?"],
  recomendar: ["Quais 3 pautas o Impulso deveria postar em dezembro?", "O que postar em janeiro para donos de salão de beleza?"],
};
const PORTES = ["micro", "medio", "grande"].map((p) => ({ valor: p, rotulo: `Criador ${nomePorte(p)}` }));
const PLATAFORMAS = [{ valor: "instagram", rotulo: "Instagram" }, { valor: "youtube", rotulo: "YouTube" }];

function Salvas({ modo, aoPerguntar }: { modo: ModoAgente; aoPerguntar: () => void }) {
  const { data, isLoading, error, refetch } = useAgenteSalvas();
  const [escolhida, setEscolhida] = useState<string | null>(null);
  if (isLoading) return <Esqueleto tipo="linhas" n={4} />;
  if (error) return <Erro erro={error} onTentar={refetch} />;
  const lista = (data ?? []).filter((r) => r.modo === modo);
  if (lista.length === 0)
    return (
      <Vazio titulo="Nenhuma resposta salva neste modo" acao={<Botao onClick={aoPerguntar}>Perguntar agora</Botao>}>
        As respostas ficam guardadas depois de cada pergunta. Faça a primeira.
      </Vazio>
    );
  const atual = lista.find((r) => r.id === escolhida) ?? lista[0];
  return (
    <>
      <ul className="criar-salvas" aria-label="Respostas salvas">
        {lista.map((r: RespostaAgente) => (
          <li key={r.id}>
            <button type="button" className={`criar-salva${r.id === atual.id ? " criar-salva--atual" : ""}`} aria-pressed={r.id === atual.id} onClick={() => setEscolhida(r.id)}>
              <span className="criar-salva-pergunta corta-3">{r.pergunta}</span>
              <span className="criar-salva-meta">{fmtData(r.em)}{r.segmento ? ` · ${r.segmento}` : ""}{r.criativos.length ? ` · ${r.criativos.length} ${r.criativos.length === 1 ? "opção" : "opções"}` : ""}</span>
            </button>
          </li>
        ))}
      </ul>
      <h2 className="criar-pergunta t-titulo t-h2">{atual.pergunta}</h2>
      <Resposta key={atual.id} r={atual} />
    </>
  );
}

function VideosGerados() {
  const { data } = useVideosGerados();
  if (!data?.length) return null;
  return (
    <section className="criar-videos" aria-label="Reels já gerados">
      <h2 className="t-h3">Reels já gerados</h2>
      <ul className="criar-videos-lista">
        {data.map((v) => (
          <li key={v.url} className="criar-videos-item">
            <video src={v.url} controls playsInline preload="metadata" className="criar-video-player" />
            <p className="corta-3">{v.titulo}</p>
            <a className="botao botao--fantasma botao--p" href={v.url} download>Baixar MP4</a>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function Criar() {
  const { foco } = useFoco();
  const [q, setQ] = useSearchParams();
  const job = q.get("job");
  const vinda = q.get("pergunta") ?? "";
  const modoVindo = q.get("modo") as ModoAgente | null;
  const [modo, setModo] = useState<ModoAgente>(modoVindo && ["gerar_criativo", "analisar", "recomendar"].includes(modoVindo) ? modoVindo : "gerar_criativo");
  const [fonte, setFonte] = useState<"salvas" | "agora">(vinda || job ? "agora" : "salvas");
  const [pergunta, setPergunta] = useState(vinda);
  const [segmento, setSegmento] = useState("");
  const [plataforma, setPlataforma] = useState("");
  const [porte, setPorte] = useState("");
  const [pilar, setPilar] = useState("");
  const [desde, setDesde] = useState(Date.now());
  const perguntar = usePerguntarAgente();
  const { data: estado, error: erroJob, refetch } = useAgente(job);

  const definirJob = (id: string | null) => {
    const n = new URLSearchParams(q);
    if (id) n.set("job", id); else n.delete("job");
    n.delete("pergunta");
    setQ(n);
  };
  const enviar = async () => {
    setDesde(Date.now());
    try {
      const { id } = await perguntar.mutateAsync({
        modo, pergunta: pergunta.trim(), segmento: segmento || null,
        filtros: { plataforma: plataforma || null, porte: porte || null, pilar: pilar || null },
      });
      definirJob(id);
    } catch { /* aparece abaixo do botão */ }
  };
  const rodando = !!job && !erroJob && (!estado || estado.estado === "rodando");
  const pronto = !!job && estado?.estado === "pronto" && !!estado.resultado;
  const { data: opcoes } = useOpcoesAgente();
  // vindo da caixa da porta de entrada com ?enviar=1: pergunta já sai rodando (uma vez só)
  const autoEnviou = useRef(false);
  useEffect(() => {
    if (autoEnviou.current || job || q.get("enviar") !== "1" || !vinda.trim()) return;
    autoEnviou.current = true;
    enviar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  // com a resposta pronta o formulário se recolhe e a tela rola até ela
  const respostaRef = useRef<HTMLHeadingElement>(null);
  useEffect(() => { if (pronto) respostaRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }); }, [pronto]);
  const erroEnvio = perguntar.error;

  return (
    <>
      <TituloPagina
        titulo="Criar" grifo="pauta"
        sub="Um agente que só escreve a partir de posts reais da base e confere o que escreveu antes de entregar."
      />
      {foco === "B" && (
        <p className="criar-aviso" role="note">
          <b>O agente usa a base do Foco A</b> (Impulso para o empreendedor). No Foco B ele continua funcionando, mas as referências e os padrões vêm de lá, e os cards abrem o post original.
        </p>
      )}

      <div className="criar-controles">
        <Seg rotulo="O que o agente faz" valor={modo} onChange={setModo} opcoes={MODOS} />
        <Seg rotulo="De onde vem a resposta" valor={fonte} onChange={setFonte} opcoes={[{ valor: "salvas", rotulo: "Respostas salvas" }, { valor: "agora", rotulo: "Perguntar agora" }]} />
      </div>

      {fonte === "salvas" ? (
        <Salvas modo={modo} aoPerguntar={() => setFonte("agora")} />
      ) : (
        <>
          {pronto && (
            <div className="linha nao-imprimir">
              <Botao variante="contorno" onClick={() => definirJob(null)}>← Fazer outro pedido</Botao>
            </div>
          )}
          {!rodando && !pronto && (
            <form className="criar-form" onSubmit={(e) => { e.preventDefault(); if (pergunta.trim()) enviar(); }}>
              <p className="t-sec">{SOBRE[modo]}</p>
              <Campo
                rotulo="Seu pedido" esconderRotulo multilinha rows={4} tamanho="g" value={pergunta} onChange={(e) => setPergunta(e.target.value)}
                placeholder={EXEMPLOS[modo][0]} maxLength={1200}
              />
              <div className="criar-exemplos">
                <span className="t-pequeno t-sec">Exemplos:</span>
                {EXEMPLOS[modo].map((e) => <button key={e} type="button" className="criar-exemplo" onClick={() => setPergunta(e)}>{e}</button>)}
              </div>
              <div className="criar-filtros">
                <Seletor rotulo="Segmento" valor={segmento} onChange={setSegmento} opcoes={opcoes?.segmentos ?? []} todos="Todos os segmentos" />
                <Seletor rotulo="Plataforma" valor={plataforma} onChange={setPlataforma} opcoes={PLATAFORMAS} todos="Todas" />
                <Seletor rotulo="Tamanho do criador" valor={porte} onChange={setPorte} opcoes={PORTES} todos="Todos os tamanhos" />
                <Seletor rotulo="Pilar" valor={pilar} onChange={setPilar} opcoes={opcoes?.pilares ?? []} todos="Todos os pilares" />
              </div>
              <div className="criar-enviar">
                <Botao variante="lima" tamanho="g" type="submit" disabled={!pergunta.trim()} ocupado={perguntar.isPending}>Perguntar ao agente</Botao>
                <span className="t-pequeno t-sec">Leva de 30 segundos a 1 minuto e usa crédito do modelo.</span>
              </div>
              {erroEnvio && (erroEnvio instanceof ErroApi && erroEnvio.status >= 400 && erroEnvio.status < 500
                ? <Erro titulo="Não foi possível enviar" erro={erroEnvio} />
                : <Erro erro={erroEnvio} onTentar={enviar} />)}
            </form>
          )}
          {job && erroJob && <Erro erro={erroJob} onTentar={() => refetch()} />}
          {rodando && (
            <div className="criar-andamento">
              <Progresso etapas={estado?.etapas ?? []} desde={desde} titulo="Escrevendo" estimativa="Leva de 30 segundos a 1 minuto." />
            </div>
          )}
          {job && estado?.estado === "erro" && (
            <Erro titulo="O agente não terminou" erro={estado.erro ?? "O modelo não devolveu uma resposta."} onTentar={pergunta.trim() ? enviar : () => definirJob(null)} />
          )}
          {job && estado?.estado === "pronto" && estado.resultado && (
            <>
              <h2 ref={respostaRef} className="criar-pergunta t-titulo t-h2">{estado.resultado.pergunta}</h2>
              <Resposta key={estado.resultado.id} r={estado.resultado} />
            </>
          )}
        </>
      )}
      <VideosGerados />
    </>
  );
}
