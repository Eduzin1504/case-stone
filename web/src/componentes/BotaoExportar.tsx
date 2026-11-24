// Exporta um pedaço da tela: "Baixar PNG" (html-to-image) e "Imprimir / salvar em PDF" (só aquele nó sai no papel).
//   const ref = useRef<HTMLDivElement>(null);
//   <BotaoExportar alvo={ref} nome="ranking-posts" />   …   <div ref={ref}>conteúdo</div>
// `semPng`: para áreas muito altas (o playbook inteiro), onde a imagem sairia enorme; fica só imprimir / PDF.
// Dica: o que não deve sair (botões, filtros) ganha className="nao-imprimir" (some na impressão) ou data-nao-exportar (some no PNG).
import { useState, type RefObject } from "react";
import { toPng } from "html-to-image";
import { REVELAR } from "../util/useEntrou";
import { Botao } from "./Botao";

type Props = { alvo: RefObject<HTMLElement | null>; nome?: string; tamanho?: "p" | "m"; semPng?: boolean };

const espera = (ms: number) => new Promise((r) => setTimeout(r, ms));
const externa = (n: HTMLElement) => n instanceof HTMLImageElement && !n.src.startsWith(location.origin) && !n.src.startsWith("data:");

export function BotaoExportar({ alvo, nome = "pauta-impulso", tamanho = "p", semPng }: Props) {
  const [ocupado, setOcupado] = useState(false);
  const [aviso, setAviso] = useState<string | null>(null);

  const revelar = async () => {
    window.dispatchEvent(new Event(REVELAR)); // termina de desenhar barras e números fora da tela
    await espera(1100);
  };

  const png = async () => {
    const no = alvo.current;
    if (!no) return;
    setOcupado(true);
    setAviso(null);
    try {
      await revelar();
      const opcoes = { pixelRatio: 2, cacheBust: true, backgroundColor: getComputedStyle(document.body).backgroundColor };
      const visivel = (n: HTMLElement) => !(n instanceof HTMLElement && (n.dataset?.naoExportar !== undefined || n.tagName === "IFRAME"));
      let url: string;
      try {
        url = await toPng(no, { ...opcoes, filter: visivel });
      } catch {
        // imagens de outro domínio sem CORS travam o canvas: tenta de novo sem elas
        url = await toPng(no, { ...opcoes, filter: (n) => visivel(n) && !externa(n) });
        setAviso("Algumas miniaturas de fora não puderam entrar na imagem.");
      }
      const a = document.createElement("a");
      a.href = url;
      a.download = `${nome}.png`;
      a.click();
    } catch {
      setAviso("Não foi possível gerar a imagem. Use Imprimir / salvar em PDF.");
    } finally {
      setOcupado(false);
    }
  };

  const imprimir = async () => {
    const no = alvo.current;
    if (!no) return;
    await revelar();
    no.setAttribute("data-imprimir", "");
    document.body.classList.add("imprimindo-no");
    const limpar = () => {
      no.removeAttribute("data-imprimir");
      document.body.classList.remove("imprimindo-no");
      window.removeEventListener("afterprint", limpar);
    };
    window.addEventListener("afterprint", limpar);
    window.print();
  };

  return (
    <span className="exportar nao-imprimir" data-nao-exportar>
      {!semPng && <Botao variante="contorno" tamanho={tamanho} onClick={png} ocupado={ocupado}>Baixar PNG</Botao>}
      <Botao variante={semPng ? "contorno" : "fantasma"} tamanho={tamanho} onClick={imprimir}>Imprimir / salvar em PDF</Botao>
      {aviso && <span className="t-pequeno t-sec" role="status">{aviso}</span>}
    </span>
  );
}
