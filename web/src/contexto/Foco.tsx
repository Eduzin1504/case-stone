// Foco da análise (A: Impulso → empreendedor · B: Negócio → cliente).
// Uso: const { foco, setFoco, focos, info } = useFoco();
//   foco      "A" | "B" (enquanto ninguém escolheu vale "A", e `escolhido` é false: o AppShell manda para "/")
//   setFoco   grava em localStorage ("pauta.foco"); as consultas refazem sozinhas (o foco está na chave de todo hook)
//   focos     resposta de GET /focos ([] enquanto carrega); info = o item do foco atual
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/cliente";
import type { Foco, InfoFoco } from "../api/tipos";

type Valor = { foco: Foco; escolhido: boolean; setFoco: (f: Foco) => void; focos: InfoFoco[]; info: InfoFoco | undefined; carregando: boolean; erro: Error | null; recarregar: () => void };
const Ctx = createContext<Valor | null>(null);
const CHAVE = "pauta.foco";

function salvo(): Foco | null {
  try {
    const s = localStorage.getItem(CHAVE);
    return s === "A" || s === "B" ? s : null;
  } catch {
    return null;
  }
}

export function FocoProvider({ children }: { children: ReactNode }) {
  const [escolha, setEscolha] = useState<Foco | null>(salvo);
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["focos"], queryFn: () => api.get<InfoFoco[]>("/focos"), staleTime: Infinity });
  const setFoco = useCallback((f: Foco) => {
    setEscolha(f);
    try { localStorage.setItem(CHAVE, f); } catch { /* ignora */ }
  }, []);
  const valor = useMemo<Valor>(() => {
    const foco = escolha ?? "A";
    const focos = data ?? [];
    return { foco, escolhido: escolha !== null, setFoco, focos, info: focos.find((f) => f.id === foco), carregando: isLoading, erro: error, recarregar: () => void refetch() };
  }, [escolha, data, isLoading, error, refetch, setFoco]);
  return <Ctx.Provider value={valor}>{children}</Ctx.Provider>;
}

export function useFoco(): Valor {
  const v = useContext(Ctx);
  if (!v) throw new Error("useFoco fora do FocoProvider");
  return v;
}
