// Largura atual de um elemento (para SVG responsivo desenhado em pixels reais).
import { useLayoutEffect, useState, type RefObject } from "react";

export function useLargura(ref: RefObject<Element | null>): number {
  const [w, setW] = useState(0);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    setW(el.getBoundingClientRect().width);
    const ro = new ResizeObserver(([e]) => setW(e.contentRect.width));
    ro.observe(el);
    return () => ro.disconnect();
  }, [ref]);
  return Math.floor(w);
}
