// "Dados que se desenham": diz quando o elemento entrou na tela pela primeira vez.
//   const ref = useRef<HTMLDivElement>(null); const entrou = useEntrou(ref);
//   <div ref={ref} style={{ width: entrou ? "62%" : 0, transition: "width var(--dur-dados) var(--ease)" }} />
// Também vira true ao imprimir/exportar (evento "pauta:revelar"), para nada sair zerado no PNG ou no PDF.
import { useEffect, useState, type RefObject } from "react";

export const REVELAR = "pauta:revelar";

export function useEntrou(ref: RefObject<Element | null>, margem = "0px 0px -8% 0px"): boolean {
  const [entrou, setEntrou] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || entrou) return;
    const revelar = () => setEntrou(true);
    if (typeof IntersectionObserver === "undefined") return revelar();
    const io = new IntersectionObserver((es) => es.some((e) => e.isIntersecting) && revelar(), { rootMargin: margem });
    io.observe(el);
    window.addEventListener(REVELAR, revelar);
    window.addEventListener("beforeprint", revelar);
    return () => {
      io.disconnect();
      window.removeEventListener(REVELAR, revelar);
      window.removeEventListener("beforeprint", revelar);
    };
  }, [ref, entrou, margem]);
  return entrou;
}

export const semMovimento = () => typeof matchMedia !== "undefined" && matchMedia("(prefers-reduced-motion: reduce)").matches;
