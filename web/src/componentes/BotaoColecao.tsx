// "Salvar em coleção": abre uma lista das coleções do foco atual; clicar marca/desmarca o post; dá para criar uma nova ali mesmo.
//   <BotaoColecao postId={post.id} />        (variante e tamanho como no <Botao>)
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useAdicionarPost, useColecoes, useCriarColecao, useRemoverPost } from "../api/hooks";
import { Botao } from "./Botao";

type Props = { postId: string; variante?: "primario" | "lima" | "contorno" | "fantasma"; tamanho?: "p" | "m" | "g"; abreParaCima?: boolean };

export function BotaoColecao({ postId, variante = "contorno", tamanho = "m", abreParaCima = true }: Props) {
  const [aberto, setAberto] = useState(false);
  const [nome, setNome] = useState("");
  const caixa = useRef<HTMLDivElement>(null);
  const { data: colecoes, isLoading, error } = useColecoes();
  const adicionar = useAdicionarPost(), remover = useRemoverPost(), criar = useCriarColecao();
  const erro = error ?? adicionar.error ?? remover.error ?? criar.error;
  const salvoEm = (colecoes ?? []).filter((c) => c.posts.some((p) => p.id === postId)).length;

  useEffect(() => {
    if (!aberto) return;
    const fora = (e: MouseEvent) => caixa.current && !caixa.current.contains(e.target as Node) && setAberto(false);
    const esc = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      e.stopPropagation(); // fecha só a lista, não o painel do post
      setAberto(false);
    };
    document.addEventListener("mousedown", fora);
    document.addEventListener("keydown", esc, true);
    return () => {
      document.removeEventListener("mousedown", fora);
      document.removeEventListener("keydown", esc, true);
    };
  }, [aberto]);

  const criarESalvar = async (e: FormEvent) => {
    e.preventDefault();
    if (!nome.trim()) return;
    const nova = await criar.mutateAsync({ nome: nome.trim() });
    await adicionar.mutateAsync({ colecao: nova.id, post: postId });
    setNome("");
  };

  return (
    <div className="colecao-caixa" ref={caixa}>
      <Botao variante={variante} tamanho={tamanho} aria-expanded={aberto} aria-haspopup="dialog" onClick={() => setAberto(!aberto)}>
        {salvoEm > 0 ? `✓ Salvo em ${salvoEm}` : "Salvar em coleção"}
      </Botao>
      {aberto && (
        <div className={`colecao-lista${abreParaCima ? " colecao-lista--cima" : ""}`} role="dialog" aria-label="Salvar em coleção">
          <p className="t-h3">Salvar em coleção</p>
          {isLoading && <p className="t-sec t-pequeno">Carregando…</p>}
          {colecoes?.length === 0 && <p className="t-sec t-pequeno">Nenhuma coleção ainda. Crie a primeira abaixo.</p>}
          <ul>
            {colecoes?.map((c) => {
              const tem = c.posts.some((p) => p.id === postId);
              return (
                <li key={c.id}>
                  <button type="button" role="checkbox" aria-checked={tem} className="colecao-item" onClick={() => (tem ? remover : adicionar).mutate({ colecao: c.id, post: postId })}>
                    <span className="colecao-marca" aria-hidden>{tem ? "✓" : ""}</span>
                    <span className="corta-1">{c.nome}</span>
                    <span className="t-sec t-pequeno">{c.posts.length}</span>
                  </button>
                </li>
              );
            })}
          </ul>
          <form className="colecao-nova" onSubmit={criarESalvar}>
            <input aria-label="Nome da nova coleção" placeholder="Nova coleção" value={nome} onChange={(e) => setNome(e.target.value)} maxLength={60} />
            <Botao type="submit" tamanho="p" ocupado={criar.isPending} disabled={!nome.trim()}>Criar</Botao>
          </form>
          {erro && <p className="t-alerta t-pequeno" role="alert">{erro.message}</p>}
        </div>
      )}
    </div>
  );
}
