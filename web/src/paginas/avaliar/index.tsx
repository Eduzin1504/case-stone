// /avaliar (envio, progresso narrado e resultado) e /avaliar/historico (ver Historico.tsx).
// O pedido em andamento fica na URL (?job=ID): dá para recarregar a página sem perder o acompanhamento.
import { useEffect, useMemo, useRef, useState, type DragEvent } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { useAvaliacao, useEnviarAvaliacao } from "../../api/hooks";
import { ErroApi } from "../../api/cliente";
import type { Plataforma } from "../../api/tipos";
import { Botao, Campo, Erro, Esqueleto, Midia, MolduraCelular, Seg, TituloPagina } from "../../componentes";
import { useFoco } from "../../contexto/Foco";
import { Historico } from "./Historico";
import { Progresso } from "./Progresso";
import { Resultado } from "./Resultado";
import "./avaliar.css";

const VIDEO = ["mp4", "mov", "webm"], IMAGEM = ["jpg", "jpeg", "png", "webp"];
const ACEITA = [...VIDEO, ...IMAGEM].map((e) => `.${e}`).join(",");
const MAX_MB = 200;
const ext = (f: File) => f.name.split(".").pop()?.toLowerCase() ?? "";
const ehVideo = (f: File) => VIDEO.includes(ext(f));

/** As mesmas regras da API, para avisar antes de enviar. Devolve a mensagem de erro ou null. */
export function validar(arquivos: File[]): string | null {
  const fora = arquivos.find((f) => !VIDEO.includes(ext(f)) && !IMAGEM.includes(ext(f)));
  if (fora) return `"${fora.name}" não é aceito. Use mp4, mov ou webm para vídeo; jpg, png ou webp para imagem.`;
  const videos = arquivos.filter(ehVideo).length;
  if (videos > 1) return "Envie só 1 vídeo por avaliação.";
  if (videos === 1 && arquivos.length > 1) return "Envie 1 vídeo ou imagens, não os dois juntos.";
  if (arquivos.length > 10) return `Você escolheu ${arquivos.length} imagens. O máximo é 10.`;
  const grande = arquivos.find((f) => f.size > MAX_MB * 1024 * 1024);
  if (grande) return `"${grande.name}" passa de ${MAX_MB} MB.`;
  return null;
}

function Previa({ arquivos, urls, legenda }: { arquivos: File[]; urls: string[]; legenda: string }) {
  return (
    <MolduraCelular largura={290} className="avaliar-celular">
      {arquivos.length === 0 ? (
        <div className={`avaliar-previa-vazia${legenda.trim() ? " avaliar-previa-vazia--texto" : ""}`}>
          {legenda.trim() ? <p>{legenda}</p> : <><p className="t-titulo">Prévia</p><p>O que você enviar aparece aqui.</p></>}
        </div>
      ) : ehVideo(arquivos[0]) ? (
        <video className="midia-quadro" src={urls[0]} controls playsInline muted preload="metadata" aria-label="Prévia do vídeo enviado" />
      ) : (
        <Midia midia={{ tipo: "imagens", imagens: urls }} titulo="Prévia do post" />
      )}
    </MolduraCelular>
  );
}

function Enviar() {
  const { foco, info } = useFoco();
  const [q, setQ] = useSearchParams();
  const job = q.get("job");
  const [arquivos, setArquivos] = useState<File[]>([]);
  const [legenda, setLegenda] = useState("");
  const [plataforma, setPlataforma] = useState<Plataforma>("instagram");
  const [usarVideo, setUsarVideo] = useState(false);
  const [invalido, setInvalido] = useState<string | null>(null);
  const [sobre, setSobre] = useState(false);
  const [desde, setDesde] = useState(Date.now());
  const enviar = useEnviarAvaliacao();
  const { data: estado, error: erroJob, refetch } = useAvaliacao(job);

  const urls = useMemo(() => arquivos.map((f) => URL.createObjectURL(f)), [arquivos]);
  useEffect(() => () => urls.forEach((u) => URL.revokeObjectURL(u)), [urls]);

  const definirJob = (id: string | null) => {
    const n = new URLSearchParams(q);
    if (id) n.set("job", id); else n.delete("job");
    setQ(n);
  };
  const receber = (novos: File[]) => {
    if (!novos.length) return;
    // imagens soltas aos poucos se somam; qualquer outra combinação troca o que havia
    const junta = arquivos.length > 0 && ![...arquivos, ...novos].some(ehVideo) ? [...arquivos, ...novos] : novos;
    const erro = validar(junta);
    setInvalido(erro);
    if (!erro) setArquivos(junta);
  };
  const soltar = (e: DragEvent) => {
    e.preventDefault();
    setSobre(false);
    receber([...e.dataTransfer.files]);
  };
  const avaliar = async () => {
    setInvalido(null);
    setDesde(Date.now());
    try {
      const { id } = await enviar.mutateAsync({ arquivos, legenda, plataforma, usar_video: usarVideo });
      definirJob(id);
    } catch { /* o erro fica em enviar.error e aparece abaixo do botão */ }
  };
  // vindo da caixa da porta de entrada: arquivos e legenda chegam pelo state da rota e a avaliação já começa (uma vez só)
  const location = useLocation();
  const navegar = useNavigate();
  const autoEnviou = useRef(false);
  useEffect(() => {
    const st = location.state as { arquivos?: File[]; legenda?: string; link?: string; enviar?: boolean } | null;
    if (autoEnviou.current || job || !st?.enviar) return;
    autoEnviou.current = true;
    const arqs = st.arquivos ?? [];
    const leg = st.legenda ?? "";
    setArquivos(arqs); setLegenda(leg);
    navegar(location.pathname + location.search, { replace: true, state: null });
    const erro = arqs.length ? validar(arqs) : null;
    if (erro) { setInvalido(erro); return; }
    if (!arqs.length && !leg.trim() && !st.link) return;
    setDesde(Date.now());
    enviar.mutateAsync({ arquivos: arqs, legenda: leg, plataforma, usar_video: false, link: st.link })
      .then(({ id }) => definirJob(id)).catch(() => { /* aparece abaixo do botão */ });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const outro = () => {
    setArquivos([]); setLegenda(""); setInvalido(null); enviar.reset(); definirJob(null);
    window.scrollTo({ top: 0 });
  };

  const temVideo = arquivos.some(ehVideo);
  const podeEnviar = arquivos.length > 0 || legenda.trim().length > 0;
  const titulo = (
    <TituloPagina
      titulo="Avaliar" grifo="meu post"
      sub={<>Envie o post antes de publicar. A leitura compara com o top do {info?.nome ?? `Foco ${foco}`} e devolve uma nota e o que mudar.</>}
      acoes={<Botao variante="contorno" para="/avaliar/historico">Histórico →</Botao>}
    />
  );

  // ---- pedido em andamento ou terminado ----
  if (job) {
    if (erroJob) return <>{titulo}<Erro erro={erroJob} onTentar={() => refetch()} /><div className="linha"><Botao onClick={outro}>Avaliar outro</Botao><Botao variante="contorno" para="/avaliar/historico">Ver o histórico</Botao></div></>;
    if (!estado) return <>{titulo}<Esqueleto altura={320} /></>;
    if (estado.estado === "pronto" && estado.resultado) {
      const r = estado.resultado as typeof estado.resultado & { thumb?: string | null };
      return (
        <>
          {titulo}
          <Resultado resultado={r} thumb={r.thumb} criadaEm={new Date(desde - new Date().getTimezoneOffset() * 60000).toISOString()} acoes={<Botao onClick={outro}>Avaliar outro</Botao>} />
        </>
      );
    }
    if (estado.estado === "erro" || estado.estado === "pronto")
      return (
        <>
          {titulo}
          <Erro
            titulo="A avaliação não terminou" erro={estado.erro ?? "O modelo não devolveu um resultado."}
            onTentar={podeEnviar ? avaliar : () => definirJob(null)}
          />
          <div className="linha"><Botao variante="contorno" onClick={() => definirJob(null)}>Voltar ao envio</Botao></div>
        </>
      );
    return (
      <>
        {titulo}
        <div className="avaliar-andamento">
          {podeEnviar && <Previa arquivos={arquivos} urls={urls} legenda={legenda} />}
          <Progresso etapas={estado.etapas} desde={desde} />
        </div>
      </>
    );
  }

  // ---- envio ----
  const erroEnvio = enviar.error;
  return (
    <>
      {titulo}
      <div className="avaliar-envio">
        <div className="avaliar-form">
          <label
            className={`avaliar-solta${sobre ? " avaliar-solta--sobre" : ""}${arquivos.length ? " avaliar-solta--cheia" : ""}`}
            onDragOver={(e) => { e.preventDefault(); setSobre(true); }} onDragLeave={() => setSobre(false)} onDrop={soltar}
          >
            <input
              type="file" className="so-leitor" multiple accept={ACEITA}
              onChange={(e) => { receber([...(e.target.files ?? [])]); e.target.value = ""; }}
              aria-describedby="avaliar-regras"
            />
            {arquivos.length === 0 ? (
              <>
                <span className="t-titulo avaliar-solta-titulo">Solte o post aqui</span>
                <span className="avaliar-solta-ou">ou clique para escolher os arquivos</span>
              </>
            ) : (
              <>
                <span className="t-titulo avaliar-solta-titulo">{temVideo ? "1 vídeo" : `${arquivos.length} ${arquivos.length === 1 ? "imagem" : "imagens"}`}</span>
                <span className="avaliar-solta-ou corta-2">{arquivos.map((f) => f.name).join(" · ")}</span>
                <span className="avaliar-solta-ou">Solte ou clique para trocar{!temVideo && arquivos.length < 10 ? " ou somar imagens" : ""}</span>
              </>
            )}
            <span id="avaliar-regras" className="t-pequeno avaliar-solta-regras">1 vídeo (mp4, mov, webm) ou até 10 imagens (jpg, png, webp), até {MAX_MB} MB cada</span>
          </label>
          {invalido && <p className="avaliar-invalido" role="alert">{invalido}</p>}
          {arquivos.length > 0 && <div><Botao variante="fantasma" tamanho="p" onClick={() => { setArquivos([]); setInvalido(null); }}>× Tirar {arquivos.length > 1 ? "os arquivos" : "o arquivo"}</Botao></div>}

          <Campo
            rotulo="Legenda ou roteiro" multilinha rows={5} value={legenda} onChange={(e) => setLegenda(e.target.value)}
            placeholder="Cole a legenda, ou o roteiro se ainda não gravou."
            dica="Sem arquivo, a avaliação é feita só pelo texto."
          />
          <div className="avaliar-linha-plataforma">
            <span className="campo-rotulo" id="avaliar-plat">Onde vai publicar</span>
            <Seg rotulo="Onde vai publicar" valor={plataforma} onChange={setPlataforma} opcoes={[{ valor: "instagram", rotulo: "Instagram" }, { valor: "youtube", rotulo: "YouTube" }]} />
          </div>
          <details className="avaliar-avancado">
            <summary>Opções avançadas</summary>
            <label className="avaliar-opcao">
              <input type="checkbox" checked={usarVideo} onChange={(e) => setUsarVideo(e.target.checked)} />
              <span>Ler o vídeo inteiro, com áudio <span className="t-sec">(mais lento, cota limitada). Desligado, a leitura usa quadros do vídeo, sem áudio.</span></span>
            </label>
          </details>

          <div className="avaliar-enviar">
            <Botao variante="lima" tamanho="g" onClick={avaliar} disabled={!podeEnviar} ocupado={enviar.isPending}>Avaliar</Botao>
            <span className="t-pequeno t-sec">{podeEnviar ? "Leva cerca de 1 minuto." : "Envie um arquivo ou escreva o texto para avaliar."}</span>
          </div>
          {erroEnvio && (
            erroEnvio instanceof ErroApi && erroEnvio.status >= 400 && erroEnvio.status < 500
              ? <Erro titulo="Não foi possível enviar" erro={erroEnvio} />
              : <Erro erro={erroEnvio} onTentar={avaliar} />
          )}
        </div>
        <aside className={`avaliar-lado${podeEnviar ? "" : " avaliar-lado--vazio"}`} aria-label="Prévia do post">
          <Previa arquivos={arquivos} urls={urls} legenda={legenda} />
        </aside>
      </div>
    </>
  );
}

export default function Avaliar() {
  const { pathname } = useLocation();
  return pathname.replace(/\/$/, "").endsWith("/historico") ? <Historico /> : <Enviar />;
}
