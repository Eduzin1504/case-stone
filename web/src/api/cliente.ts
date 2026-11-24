// Cliente da API. Uso: api.get<PaginaPosts>("/posts", { foco: "A", so_top: true })
// Erros viram ErroApi com a mensagem do campo `erro` da resposta (já pronta para mostrar ao usuário).
// Com VITE_EXEMPLOS=1 nada vai para a rede: responde com src/api/exemplos.

export type Params = Record<string, string | number | boolean | null | undefined>;
export type Metodo = "GET" | "POST" | "PATCH" | "DELETE";

export class ErroApi extends Error {
  constructor(mensagem: string, public status: number) {
    super(mensagem);
    this.name = "ErroApi";
  }
}

export const EXEMPLOS = import.meta.env.VITE_EXEMPLOS === "1";

function montarUrl(caminho: string, params?: Params) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params ?? {})) if (v !== undefined && v !== null && v !== "") q.set(k, String(v));
  const s = q.toString();
  return `/api${caminho}${s ? `?${s}` : ""}`;
}

async function pedir<T>(metodo: Metodo, caminho: string, params?: Params, corpo?: unknown): Promise<T> {
  if (EXEMPLOS) {
    const { responder } = await import("./exemplos");
    await new Promise((r) => setTimeout(r, 220)); // deixa os estados de carregamento visíveis
    return responder(metodo, caminho, params ?? {}, corpo) as T;
  }
  const form = corpo instanceof FormData;
  let r: Response;
  try {
    r = await fetch(montarUrl(caminho, params), {
      method: metodo,
      headers: corpo !== undefined && !form ? { "Content-Type": "application/json" } : undefined,
      body: corpo === undefined ? undefined : form ? corpo : JSON.stringify(corpo),
    });
  } catch {
    throw new ErroApi("Não foi possível falar com o servidor. Confira se a API está no ar.", 0);
  }
  const dados: unknown = r.status === 204 ? null : await r.json().catch(() => null);
  if (!r.ok) {
    const msg = dados && typeof dados === "object" && "erro" in dados ? String((dados as { erro: unknown }).erro) : `Algo deu errado (${r.status}).`;
    throw new ErroApi(msg, r.status);
  }
  return dados as T;
}

export const api = {
  get: <T>(caminho: string, params?: Params) => pedir<T>("GET", caminho, params),
  post: <T>(caminho: string, corpo?: unknown, params?: Params) => pedir<T>("POST", caminho, params, corpo),
  patch: <T>(caminho: string, corpo?: unknown, params?: Params) => pedir<T>("PATCH", caminho, params, corpo),
  delete: <T>(caminho: string, params?: Params, corpo?: unknown) => pedir<T>("DELETE", caminho, params, corpo),
  url: montarUrl,
};
