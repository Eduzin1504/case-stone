// Caixa de pergunta do Início (estado vazio de chat), depois que o público já foi escolhido na porta de entrada.
// Abas em cima escolhem o que fazer; a caixa, o exemplo e as sugestões mudam com a aba. O foco vem da barra lateral.
// Enviar leva para a página certa e já começa: /criar?modo=…&pergunta=…&enviar=1, /busca?q=…, /avaliar (arquivos pelo state da rota).
// Link de post (Instagram ou YouTube) colado em qualquer aba: se o post já está na base, abre o painel dele; senão, vai
// para /avaliar com o link, e a API baixa e avalia o post.
import { useMemo, useRef, useState, type DragEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../api/cliente";
import { useAbrirPost } from "../../componentes";
import { useFoco } from "../../contexto/Foco";
import type { Foco } from "../../api/tipos";
import { fmtInt } from "../../util/formato";
import "./prompt.css";

type Modo = "pauta" | "analisar" | "recomendar" | "buscar" | "avaliar";
type Def = { rotulo: string; botao: string; exemplo: Record<Foco, string>; sugestoes: Record<Foco, string[]> };

const MODOS: Record<Modo, Def> = {
  pauta: {
    rotulo: "Gerar pauta", botao: "Gerar pauta →",
    exemplo: { A: "Descreva o post que você quer. Ex.: Reels de fim de ano para salão de beleza sobre organizar o caixa", B: "Descreva o post que você quer. Ex.: Reels de confeitaria para encomendas de Natal" },
    sugestoes: {
      A: ["Reels de fim de ano para salão de beleza sobre organizar o caixa", "Carrossel sobre separar o dinheiro do negócio do dinheiro de casa", "Post que convida o empreendedor a contar o maior aprendizado do ano"],
      B: ["Reels de bastidor para uma padaria artesanal", "Post de promoção de banho e tosa que gere pedido", "Carrossel com preço para uma confeitaria"],
    },
  },
  analisar: {
    rotulo: "Analisar", botao: "Analisar →",
    exemplo: { A: "Pergunte sobre o que engaja. Ex.: O que diferencia os carrosséis de alto engajamento no Instagram?", B: "Pergunte sobre o que engaja. Ex.: Que tipo de post de pet shop mais gera pedido?" },
    sugestoes: {
      A: ["O que diferencia os carrosséis de alto engajamento no Instagram?", "Que gancho mais aparece no top do YouTube?", "Posts sem rosto funcionam para finanças?"],
      B: ["Humor engaja, mas gera pedido?", "Mostrar o preço ajuda a vender?", "O que os salões do top fazem diferente?"],
    },
  },
  recomendar: {
    rotulo: "Recomendar", botao: "Recomendar →",
    exemplo: { A: "Peça recomendações. Ex.: Quais 3 pautas o Impulso deveria postar em dezembro?", B: "Peça recomendações. Ex.: O que uma confeitaria deveria postar na semana do Natal?" },
    sugestoes: {
      A: ["Quais 3 pautas o Impulso deveria postar em dezembro?", "Que formato usar para falar de pró-labore?", "Como chamar o empreendedor para comentar?"],
      B: ["O que uma confeitaria deveria postar no Natal?", "Como um salão pode gerar mais agendamentos?", "Que post de loja de roupa gera mais perguntas de preço?"],
    },
  },
  buscar: {
    rotulo: "Buscar por ideia", botao: "Buscar →",
    exemplo: { A: "Escreva uma ideia ou cole um texto. Ex.: como precificar", B: "Escreva uma ideia ou cole um texto. Ex.: bolo de aniversário" },
    sugestoes: { A: ["como precificar", "pix na maquininha", "black friday loja"], B: ["bolo de aniversário", "promoção de banho e tosa", "corte de cabelo antes e depois"] },
  },
  avaliar: {
    rotulo: "Avaliar meu post", botao: "Avaliar →",
    exemplo: { A: "Envie o vídeo ou as imagens acima e, se quiser, cole aqui a legenda ou o roteiro.", B: "Envie o vídeo ou as imagens acima e, se quiser, cole aqui a legenda." },
    sugestoes: { A: [], B: [] },
  },
};
const ORDEM: Modo[] = ["pauta", "analisar", "recomendar", "buscar", "avaliar"];
const AGENTE: Partial<Record<Modo, string>> = { pauta: "gerar_criativo", analisar: "analisar", recomendar: "recomendar" };
const ehVideo = (f: File) => f.type.startsWith("video/");

// mesmos padrões de api/link.py
const IG = /instagram\.com\/(?:[\w.]+\/)?(?:p|reels?|tv)\/([\w-]+)/i;
const YT = /(?:youtube\.com\/(?:shorts\/|watch\?(?:.*&)?v=|embed\/)|youtu\.be\/)([\w-]{11})/i;
type Link = { url: string; id: string; plataforma: "Instagram" | "YouTube" };
function lerLink(texto: string): Link | null {
  const url = texto.match(/https?:\/\/\S+|(?:www\.)?(?:instagram\.com|youtube\.com|youtu\.be)\/\S+/i)?.[0];
  if (!url) return null;
  const ig = url.match(IG), yt = url.match(YT);
  return ig ? { url, id: ig[1], plataforma: "Instagram" } : yt ? { url, id: yt[1], plataforma: "YouTube" } : null;
}

export function Prompt() {
  const { foco, info } = useFoco();
  const navigate = useNavigate();
  const [modo, setModo] = useState<Modo>("pauta");
  const [texto, setTexto] = useState("");
  const [arquivos, setArquivos] = useState<File[]>([]);
  const [aviso, setAviso] = useState<string | null>(null);
  const [sobre, setSobre] = useState(false);
  const campo = useRef<HTMLTextAreaElement>(null);
  const seletor = useRef<HTMLInputElement>(null);

  const abrirPost = useAbrirPost();
  const [buscando, setBuscando] = useState(false);
  const link = useMemo(() => lerLink(texto), [texto]);
  const def = MODOS[modo];
  const podeEnviar = link ? !buscando : modo === "avaliar" ? arquivos.length > 0 || texto.trim().length > 0 : texto.trim().length > 0;
  const resumoArquivos = useMemo(() => {
    if (!arquivos.length) return null;
    return arquivos.some(ehVideo) ? `1 vídeo: ${arquivos[0].name}` : `${arquivos.length} ${arquivos.length === 1 ? "imagem" : "imagens"}`;
  }, [arquivos]);

  const trocarModo = (m: Modo) => { setModo(m); setAviso(null); campo.current?.focus(); };
  const receber = (lista: File[]) => {
    if (!lista.length) return;
    const videos = lista.filter(ehVideo);
    if (videos.length > 1 || (videos.length === 1 && lista.length > 1)) { setAviso("Envie 1 vídeo ou até 10 imagens, sem misturar."); return; }
    if (lista.length > 10) { setAviso("No máximo 10 imagens por post."); return; }
    if (lista.some((f) => !ehVideo(f) && !f.type.startsWith("image/"))) { setAviso("Use vídeo (mp4, mov, webm) ou imagens (jpg, png, webp)."); return; }
    setAviso(null);
    setArquivos(lista);
  };
  const soltar = (e: DragEvent) => { e.preventDefault(); setSobre(false); receber([...e.dataTransfer.files]); };

  const analisarLink = async (l: Link) => {
    setBuscando(true);
    const naBase = await api.get(`/posts/${encodeURIComponent(l.id)}`, { foco }).then(() => true, () => false);
    setBuscando(false);
    if (naBase) return abrirPost(l.id);
    const resto = texto.replace(l.url, "").trim();
    navigate("/avaliar", { state: { arquivos: [], link: l.url, legenda: modo === "avaliar" ? resto : "", enviar: true } });
  };

  const enviar = () => {
    if (!podeEnviar) return;
    if (link) return void analisarLink(link);
    const q = texto.trim();
    if (modo === "buscar") return navigate(`/busca?q=${encodeURIComponent(q)}`);
    if (modo === "avaliar") return navigate("/avaliar", { state: { arquivos, legenda: q, enviar: true } });
    navigate(`/criar?modo=${AGENTE[modo]}&pergunta=${encodeURIComponent(q)}&enviar=1`);
  };

  return (
    <section className="prompt" aria-labelledby="prompt-titulo">
      <h1 id="prompt-titulo" className="t-titulo prompt-titulo">O que você quer descobrir?</h1>
      {info && <p className="prompt-sub">{info.pergunta}</p>}

      <div className="prompt-abas" role="tablist" aria-label="O que fazer">
        {ORDEM.map((m) => (
          <button key={m} type="button" role="tab" aria-selected={m === modo} className="prompt-aba" onClick={() => trocarModo(m)}>
            {MODOS[m].rotulo}
          </button>
        ))}
      </div>

      <form className={`prompt-caixa${sobre ? " prompt-caixa--sobre" : ""}`}
        onSubmit={(e) => { e.preventDefault(); enviar(); }}
        onDragOver={(e) => { if (modo === "avaliar") { e.preventDefault(); setSobre(true); } }}
        onDragLeave={() => setSobre(false)} onDrop={(e) => { if (modo === "avaliar") soltar(e); }}>
        {modo === "avaliar" && (
          <div className="prompt-anexo">
            <button type="button" className="prompt-anexo-botao" onClick={() => seletor.current?.click()}>
              {resumoArquivos ? "Trocar arquivos" : "+ Enviar vídeo ou imagens"}
            </button>
            <span>{resumoArquivos ?? "arraste aqui ou clique · 1 vídeo ou até 10 imagens"}</span>
            {resumoArquivos && <button type="button" className="prompt-anexo-tirar" onClick={() => setArquivos([])}>Tirar</button>}
            <input ref={seletor} type="file" hidden multiple accept="video/mp4,video/quicktime,video/webm,image/jpeg,image/png,image/webp"
              onChange={(e) => { receber([...(e.target.files ?? [])]); e.target.value = ""; }} />
          </div>
        )}
        <textarea ref={campo} id="prompt-texto" rows={3} value={texto}
          aria-label={def.rotulo} placeholder={def.exemplo[foco]}
          onChange={(e) => setTexto(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); enviar(); } }} />
        {link && (
          <p className="prompt-link" role="status">
            <span className="prompt-link-marca">Link do {link.plataforma}</span>
            Vamos analisar este post: se ele já está na base, abrimos a análise; se não, baixamos e avaliamos.
          </p>
        )}
        <div className="prompt-rodape">
          {info && <span className="prompt-base">{fmtInt(info.base.posts)} posts · {fmtInt(info.base.criadores)} criadores · {fmtInt(info.base.top)} no top</span>}
          <span className="prompt-espaco" />
          <button type="submit" className="prompt-enviar" disabled={!podeEnviar}>{link ? (buscando ? "Procurando…" : "Analisar post →") : def.botao}</button>
        </div>
      </form>

      {aviso && <p className="prompt-aviso" role="alert">{aviso}</p>}

      {def.sugestoes[foco].length > 0 && (
        <div className="prompt-sugestoes" aria-label="Sugestões">
          {def.sugestoes[foco].map((s) => (
            <button key={s} type="button" className="prompt-sugestao" onClick={() => { setTexto(s); campo.current?.focus(); }}>{s}</button>
          ))}
        </div>
      )}
    </section>
  );
}
