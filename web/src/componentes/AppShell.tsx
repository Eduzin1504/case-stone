// Casca do app: barra lateral (marca, foco, navegação, tema), área de conteúdo (<Outlet />) e o <PainelPost>.
// Já está nas rotas em App.tsx; as páginas só devolvem o próprio conteúdo:
//   export default function Catalogo() { return <><TituloPagina titulo="Catálogo" /> … </>; }
// Sem foco escolhido, redireciona para "/" (a porta de entrada, que fica FORA do shell).
// Em telas estreitas a barra vira gaveta, aberta pelo botão "Menu" do topo.
import { Component, Suspense, useEffect, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Link, NavLink, Navigate, Outlet, useLocation } from "react-router-dom";
import { EXEMPLOS } from "../api/cliente";
import { useFoco } from "../contexto/Foco";
import { fmtInt } from "../util/formato";
import { Erro, Esqueleto } from "./Estados";
import { PainelPost } from "./PainelPost";
import logoClara from "../marca/impulso-stone-clara.png";
import logoEscura from "../marca/impulso-stone-escura.png";

export const NAVEGACAO = [
  // pela pergunta de quem usa: o que está bombando? por que funciona? e o meu post?
  { grupo: "Descobrir", itens: [["/inicio", "Início"], ["/destaques", "Destaques"], ["/catalogo", "Catálogo"], ["/busca", "Busca"]] },
  { grupo: "Entender", itens: [["/playbook", "Playbook"], ["/padroes", "Padrões"], ["/rankings", "Rankings"], ["/mapa", "Mapa"]] },
  { grupo: "Criar", itens: [["/avaliar", "Avaliar meu post"], ["/criar", "Criar pauta"], ["/colecoes", "Coleções"]] },
] as const;

const OUTROS: [string, string][] = [["/avaliar/historico", "Histórico de avaliações"], ["/criadores/", "Criador"], ["/comparar", "Comparar"], ["/colecoes/", "Coleção"], ["/_vitrine", "Vitrine"], ["/metodo", "Método"]];

/** "Catálogo · Fora da Curva", pelo caminho (o item da navegação ou um dos OUTROS). */
export function tituloDaRota(pathname: string) {
  const nome = OUTROS.find(([p]) => pathname.startsWith(p))?.[1] ?? NAVEGACAO.flatMap((g): readonly (readonly [string, string])[] => g.itens).find(([p]) => p === pathname)?.[1];
  return nome ? `${nome} · Fora da Curva` : "Fora da Curva";
}

/** Logo Fora da Curva (o nome, a curva do esperado por baixo e o ponto acima dela) + logo oficial da Impulso Stone.
 *  Empilhado no menu lateral; "marca--linha" põe os dois lado a lado. tom "escura" para fundo claro. */
export function Marca({ className = "", tom = "clara" }: { className?: string; tom?: "clara" | "escura" }) {
  const texto = tom === "clara" ? "#ffffff" : "#004132";
  return (
    <span className={`marca marca--${tom} ${className}`} role="img" aria-label="Fora da Curva, Impulso Stone">
    <svg className="marca-fdc" viewBox="0 0 192 48" aria-hidden>
      <path d="M4 44C60 43 100 38 128 28S168 14 186 12" stroke={tom === "clara" ? "#c7f93c" : "#7fa61a"} strokeOpacity={tom === "clara" ? 0.5 : 1} strokeWidth="3" fill="none" strokeLinecap="round" />
      <circle cx="171" cy="6" r="6" fill={tom === "clara" ? "#c7f93c" : "#004132"} />
      <text x="0" y="32" fill={texto} fontFamily="'Bricolage Grotesque', sans-serif" fontWeight="800" fontSize="26" letterSpacing="-0.9">fora da curva</text>
    </svg>
    <img className="marca-impulso" src={tom === "clara" ? logoClara : logoEscura} alt="" />
    </span>
  );
}

/** Se uma página quebrar ao desenhar (ou o pedaço dela não baixar), mostra o erro no lugar da tela em branco. */
class Barreira extends Component<{ children: ReactNode; chave: string }, { erro: Error | null; chave: string }> {
  state = { erro: null as Error | null, chave: this.props.chave };
  static getDerivedStateFromError(erro: Error) { return { erro }; }
  static getDerivedStateFromProps(p: { chave: string }, s: { chave: string }) { return p.chave !== s.chave ? { erro: null, chave: p.chave } : null; }
  render() {
    if (!this.state.erro) return this.props.children;
    return <Erro titulo="Esta página não abriu" erro="Algo falhou ao montar a tela. Tente de novo; se continuar, confira se a API está no ar." onTentar={() => location.reload()} />;
  }
}

/** Aviso no topo quando a API não responde (GET /focos falhou). "Tentar de novo" refaz todas as consultas. */
function AvisoApi() {
  const { erro, recarregar } = useFoco();
  const qc = useQueryClient();
  if (!erro) return null;
  return (
    <div className="shell-sem-api" role="alert">
      <Erro titulo="Sem conexão com a API" erro="Os dados não carregaram. Confira se o servidor está no ar (./rodar.sh) e tente de novo." onTentar={() => { recarregar(); qc.refetchQueries(); }} />
    </div>
  );
}

export function AppShell() {
  const { foco, escolhido, info, erro } = useFoco();
  const { pathname } = useLocation();
  const [gaveta, setGaveta] = useState(false);
  useEffect(() => setGaveta(false), [pathname]);
  useEffect(() => { document.title = tituloDaRota(pathname); }, [pathname]);
  useEffect(() => {
    if (!gaveta) return;
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setGaveta(false);
    document.addEventListener("keydown", esc);
    return () => document.removeEventListener("keydown", esc);
  }, [gaveta]);

  if (!escolhido && !pathname.startsWith("/_")) return <Navigate to="/" replace />;

  return (
    <div className="shell">
      <a className="pular" href="#conteudo">Pular para o conteúdo</a>
      <header className="shell-topo">
        <Link to="/inicio" aria-label="Fora da Curva: início"><Marca className="marca--linha" /></Link>
        <button type="button" className="shell-menu" aria-expanded={gaveta} aria-controls="lateral" onClick={() => setGaveta(!gaveta)}>
          {gaveta ? "Fechar" : "Menu"}
        </button>
      </header>
      {gaveta && <div className="shell-veu" onClick={() => setGaveta(false)} />}

      <aside id="lateral" className={`shell-lateral${gaveta ? " shell-lateral--aberta" : ""}`}>
        <Link to="/inicio" className="shell-marca" aria-label="Fora da Curva: início"><Marca /></Link>

        <Link to="/" className="shell-foco" title="Trocar o foco da análise">
          <span className="shell-foco-letra" aria-hidden>{foco}</span>
          <span className="shell-foco-texto">
            <span className="shell-foco-nome">{info?.nome ?? `Foco ${foco}`}</span>
            <span className="shell-foco-base">
              {info ? `${fmtInt(info.base.posts)} posts · ${fmtInt(info.base.criadores)} criadores` : erro ? "base indisponível" : "carregando a base…"}
            </span>
            <span className="shell-foco-trocar">Trocar foco →</span>
          </span>
        </Link>

        <nav aria-label="Principal" className="shell-nav">
          {NAVEGACAO.map((g) => (
            <div key={g.grupo}>
              <p className="shell-grupo">{g.grupo}</p>
              <ul>
                {g.itens.map(([para, rotulo]) => (
                  <li key={para}>
                    <NavLink to={para} className={({ isActive }) => `shell-link${isActive ? " shell-link--ativo" : ""}`}>{rotulo}</NavLink>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>

        <div className="shell-pe">
          {EXEMPLOS && <p className="shell-aviso">Modo exemplos: dados de amostra, sem a API.</p>}
          <NavLink to="/metodo" className={({ isActive }) => `shell-metodo${isActive ? " shell-link--ativo" : ""}`}>Como medimos (método) →</NavLink>
          <p className="shell-credito">Proposta de estudante · Inteli × Impulso Stone</p>
        </div>
      </aside>

      <main id="conteudo" className="shell-conteudo" tabIndex={-1}>
        <div className="shell-pagina">
          {/* sem a API, um aviso só no lugar da página (em vez de um erro por bloco) */}
          {erro ? <AvisoApi /> : (
            <Barreira chave={pathname}>
              <Suspense fallback={<Esqueleto altura={360} />}>
                <Outlet />
              </Suspense>
            </Barreira>
          )}
        </div>
      </main>
      <PainelPost />
    </div>
  );
}
