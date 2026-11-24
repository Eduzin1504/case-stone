// Porta de entrada: a primeira tela pergunta para quem é a análise. Fica FORA do AppShell.
// Dois cartões neutros e inteiros clicáveis, um por foco, com 3 posts reais do top e o achado do nº 1.
// O lima só aparece no hover; o último foco usado ganha a etiqueta "último acesso". Escolher leva ao Início.
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useApi } from "../../api/hooks";
import type { Destaque, InfoFoco } from "../../api/tipos";
import { Erro, Esqueleto, Marca, Miniatura } from "../../componentes";
import { useFoco } from "../../contexto/Foco";
import { fmtData, fmtInt, fmtVezes } from "../../util/formato";
import "./entrada.css";

const motivo = (porque: string) => {
  const m = porque.split(";")[0].trim();
  return m.charAt(0).toLowerCase() + m.slice(1);
};

function Porta({ f, ultimo, entrar }: { f: InfoFoco; ultimo: boolean; entrar: () => void }) {
  const { data } = useApi<Destaque[]>("/destaques", { foco: f.id, limit: 3 });
  const primeiro = data?.[0];
  return (
    <button type="button" className="entrada-porta" onClick={entrar} aria-label={`Entrar no foco ${f.id}: ${f.nome}`}>
      <span className="entrada-foco">
        <span className="entrada-letra" aria-hidden>{f.id}</span>
        <span className="entrada-nome">{f.nome}</span>
        {ultimo && <span className="entrada-tag">último acesso</span>}
      </span>
      <span className="entrada-pergunta">{f.pergunta}</span>
      <span className="entrada-thumbs" aria-hidden>
        {data
          ? data.map((d) => (
              <span key={d.post.id} className="entrada-thumb">
                <Miniatura src={d.post.thumb} alt="" />
                <span className="entrada-vezes">{fmtVezes(d.post.vezes)}</span>
              </span>
            ))
          : [0, 1, 2].map((i) => <span key={i} className="entrada-thumb" />)}
      </span>
      {primeiro ? (
        <span className="entrada-achado"><b>{fmtVezes(primeiro.post.vezes)}</b> o esperado. O nº 1: {motivo(primeiro.porque)}.</span>
      ) : (
        <span className="entrada-numeros">{fmtInt(f.base.posts)} posts · {fmtInt(f.base.top)} no top</span>
      )}
      <span className="entrada-seta">Entrar →</span>
    </button>
  );
}

export default function Entrada() {
  const { focos, foco, escolhido, setFoco, carregando, erro, recarregar } = useFoco();
  const navigate = useNavigate();
  useEffect(() => { document.title = "Fora da Curva"; }, []);
  const coleta = focos.map((f) => f.base.coletado_em).filter(Boolean).sort().at(-1);

  return (
    <main className="entrada">
      <header className="entrada-cabeca"><Marca className="marca--linha" tom="escura" /></header>

      <div>
        <h1 className="t-titulo entrada-titulo">Para quem é a análise?</h1>
        <p className="entrada-linha">Encontramos os posts que passaram do esperado para o tamanho do perfil e explicamos o porquê.</p>
      </div>

      {carregando && <Esqueleto altura={260} />}
      {!carregando && focos.length === 0 && (
        <Erro titulo="Não foi possível carregar os focos" erro={erro ?? "Confira se a API está no ar."} onTentar={recarregar} />
      )}

      <div className="entrada-portas">
        {focos.map((f) => (
          <Porta key={f.id} f={f} ultimo={escolhido && f.id === foco} entrar={() => { setFoco(f.id); navigate("/inicio"); }} />
        ))}
      </div>

      <footer className="entrada-pe">
        <span>Proposta de estudante · Inteli × Impulso Stone</span>
        {coleta && <span>Base coletada até {fmtData(coleta)}</span>}
      </footer>
    </main>
  );
}
