// /metodo: como o top é escolhido, os números da base, a confiabilidade da leitura automática, a avaliação da régua e as limitações.
import { useMemo, useRef, useState, type ReactNode } from "react";
import { AnimatePresence, motion } from "motion/react";
import { useMetodo } from "../../api/hooks";
import type { Metodo as TMetodo } from "../../api/tipos";
import { Botao, Comprovante, Erro, Esqueleto, Markdown, Secao, TituloPagina, Vazio } from "../../componentes";
import { useFoco } from "../../contexto/Foco";
import { fmtData } from "../../util/formato";
import { useEntrou } from "../../util/useEntrou";
import "./metodo.css";

const EASE = [0.22, 1, 0.36, 1] as const;
const LIMITE_KAPPA = 0.4;
const dec = (n: number) => n.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

// Desenhos esquemáticos dos passos da régua (ilustram a ideia; não são dados).
// ponytail: casados pela ordem dos passos que a API manda; se a API mudar a ordem ou o número de passos, rever aqui.
const DESENHOS: ReactNode[] = [
  <svg viewBox="0 0 120 64" aria-hidden><text x="60" y="24" textAnchor="middle" className="metodo-d-txt">curtidas + comentários</text><line x1="8" x2="112" y1="33" y2="33" className="metodo-d-traco" /><text x="60" y="52" textAnchor="middle" className="metodo-d-txt">seguidores</text></svg>,
  <svg viewBox="0 0 120 64" aria-hidden><line x1="10" y1="58" x2="110" y2="14" className="metodo-d-traco" />{[[24, 56], [38, 44], [52, 46], [66, 30], [84, 28], [98, 22]].map(([x, y]) => <circle key={x} cx={x} cy={y} r="3" className="metodo-d-apagado" />)}<line x1="58" y1="37" x2="58" y2="9" className="metodo-d-salto" /><circle cx="58" cy="9" r="5" className="metodo-d-forte" /></svg>,
  <svg viewBox="0 0 120 64" aria-hidden>{Array.from({ length: 10 }, (_, i) => <rect key={i} x={6 + i * 11} y={56 - (i + 1) * 4.6} width="8" height={(i + 1) * 4.6} className={i === 9 ? "metodo-d-forte" : "metodo-d-apagado"} />)}</svg>,
  <svg viewBox="0 0 120 64" aria-hidden>{[0, 1, 2].map((l) => [0, 1, 2, 3, 4].map((c) => <circle key={`${l}${c}`} cx={14 + c * 23} cy={14 + l * 18} r="6" className={c < 3 ? "metodo-d-forte" : "metodo-d-vazado"} />))}</svg>,
];

function Passos({ passos }: { passos: TMetodo["passos"] }) {
  return (
    <ol className="metodo-passos">
      {passos.map((p, i) => (
        <li key={p.titulo} className="metodo-passo">
          <span className="metodo-passo-num" aria-hidden>{i + 1}</span>
          <div className="metodo-passo-desenho">{DESENHOS[i]}</div>
          <h3 className="t-h3">{p.titulo}</h3>
          <p className="t-sec">{p.texto}</p>
        </li>
      ))}
    </ol>
  );
}

function Numeros({ numeros }: { numeros: TMetodo["numeros"] }) {
  const grupos = useMemo(() => {
    const m = new Map<string, TMetodo["numeros"]>();
    numeros.forEach((n) => m.set(n.nota ?? n.plataforma ?? "", [...(m.get(n.nota ?? n.plataforma ?? "") ?? []), n]));
    return [...m];
  }, [numeros]);
  return (
    <div className="metodo-numeros">
      {grupos.map(([nome, ns]) => {
        const [principal, ...resto] = ns;
        return (
          <div key={nome} className="metodo-plataforma">
            {nome && <h3 className="t-titulo metodo-plataforma-nome">{nome}</h3>}
            <p className="t-titulo metodo-mega">{principal.valor}</p>
            <p className="t-h3">{principal.rotulo.toLowerCase()}</p>
            <dl className="metodo-menores">
              {resto.map((n) => (
                <div key={n.rotulo} className={`metodo-menor${n.valor.length > 12 ? " metodo-menor--largo" : n.valor.length > 6 ? " metodo-menor--medio" : ""}`}>
                  <dd>{n.valor}</dd>
                  <dt>{n.rotulo}</dt>
                </div>
              ))}
            </dl>
          </div>
        );
      })}
    </div>
  );
}

function Kappa({ kappa }: { kappa: TMetodo["kappa"] }) {
  const ref = useRef<HTMLUListElement>(null);
  const entrou = useEntrou(ref);
  const itens = [...kappa].sort((a, b) => b.kappa - a.kappa);
  const min = Math.min(0, ...itens.map((k) => k.kappa));
  const pos = (v: number) => ((v - min) / (1 - min)) * 100; // posição em % no trilho, de `min` a 1
  const fracos = itens.filter((k) => k.kappa < LIMITE_KAPPA).length;
  return (
    <>
      <ul ref={ref} className="metodo-kappa">
        {itens.map((k) => {
          const fraco = k.kappa < LIMITE_KAPPA;
          const a = pos(Math.min(0, k.kappa)), b = pos(Math.max(0, k.kappa));
          return (
            <li key={k.campo} className={fraco ? "metodo-k metodo-k--fraco" : "metodo-k"}>
              <span className="metodo-k-nome">{k.rotulo ?? k.campo}{fraco && <span className="metodo-k-aviso">pouco confiável</span>}</span>
              <span className="metodo-k-trilho" role="img" aria-label={`Kappa ${dec(k.kappa)}; a IA e a pessoa concordaram em ${Math.round(k.concordancia * 100)}% dos posts`}>
                <i className="metodo-k-barra" style={{ left: `${a}%`, width: `${Math.max(0.6, b - a)}%`, transform: `scaleX(${entrou ? 1 : 0})`, transformOrigin: k.kappa < 0 ? "right" : "left" }} />
                <i className="metodo-k-zero" style={{ left: `${pos(0)}%` }} />
                <i className="metodo-k-limite" style={{ left: `${pos(LIMITE_KAPPA)}%` }} />
              </span>
              <span className="metodo-k-num">{dec(k.kappa)}</span>
              <span className="metodo-k-conc t-pequeno t-sec">concordam em {Math.round(k.concordancia * 100)}%{k.n ? ` de ${k.n} posts` : ""}</span>
            </li>
          );
        })}
      </ul>
      <p className="metodo-legenda">
        <span><i className="metodo-amostra" />Kappa: concordância entre a IA e uma pessoa, descontado o acaso (1 = sempre concordam; 0 = igual a sortear)</span>
        <span><i className="metodo-amostra metodo-amostra--limite" />Abaixo de {dec(LIMITE_KAPPA)}: pouco confiável ({fracos} de {itens.length})</span>
      </p>
    </>
  );
}

/** Três linhas tiradas do próprio texto da avaliação: o veredito e os dois primeiros achados do "Resumo". */
function resumoDe(md: string): string[] {
  const secao = /##\s*Resumo\s*\n([\s\S]*?)(?=\n##\s|$)/.exec(md)?.[1] ?? "";
  const itens = secao.split(/\n(?=\d+\.\s)/).map((l) => l.replace(/^\d+\.\s*/, "").trim()).filter(Boolean);
  const titulo = (t: string) => /^\*\*(.+?)\*\*/.exec(t)?.[1] ?? t.split(". ")[0];
  const veredito = itens.find((t) => /^\*\*Veredito/i.test(t));
  const outros = itens.filter((t) => t !== veredito).slice(0, veredito ? 2 : 3).map(titulo);
  return [...(veredito ? [veredito] : []), ...outros];
}

function Avaliacao({ md, nota }: { md: string; nota?: string | null }) {
  const [aberta, setAberta] = useState(false);
  const linhas = useMemo(() => resumoDe(md), [md]);
  return (
    <Secao titulo="A régua foi posta à prova" sub="Antes de adotar a régua, ela foi comparada com outras três formas de escolher o top. O resultado, sem maquiagem:" bloco="superficie">
      {nota && <p className="metodo-aviso">{nota}</p>}
      {linhas.length > 0 && (
        <ol className="metodo-resumo">
          {linhas.map((l, i) => <li key={i}><Markdown texto={l} /></li>)}
        </ol>
      )}
      <div>
        <Botao variante="contorno" aria-expanded={aberta} onClick={() => setAberta(!aberta)}>{aberta ? "Recolher a avaliação" : "Ler a avaliação completa"}</Botao>
      </div>
      <AnimatePresence initial={false}>
        {aberta && (
          <motion.div className="metodo-abre" initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.4, ease: EASE }}>
            <Markdown texto={md} className="metodo-md" />
          </motion.div>
        )}
      </AnimatePresence>
    </Secao>
  );
}

function Limitacoes({ itens }: { itens: string[] }) {
  // cada limitação vem como "Título. Explicação."
  const partes = itens.map((t) => { const i = t.indexOf(". "); return i > 0 && i < 70 ? { titulo: t.slice(0, i), texto: t.slice(i + 2) } : { titulo: "", texto: t }; });
  return (
    <div className="metodo-limites">
      <Comprovante titulo="O que este estudo não garante" sub="leia antes de usar" total={{ rotulo: "Limitações", valor: String(itens.length) }}>
        <ol className="metodo-limites-indice">
          {partes.map((p, i) => <li key={i}>{p.titulo || p.texto.slice(0, 48)}</li>)}
        </ol>
      </Comprovante>
      <ol className="metodo-limites-lista">
        {partes.map((p, i) => (
          <li key={i}>
            <span className="metodo-limite-num" aria-hidden>{String(i + 1).padStart(2, "0")}</span>
            <div>
              {p.titulo && <p className="t-h3">{p.titulo}</p>}
              <p className="t-sec">{p.texto}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

export default function Metodo() {
  const { foco, info } = useFoco();
  const { data, isLoading, error, refetch } = useMetodo();
  const [metodologia, setMetodologia] = useState(false);

  return (
    <>
      <TituloPagina titulo="Como chegamos" grifo="nisso" sub="O top não é quem tem o maior engajamento. É quem mais passou do que era esperado para o próprio perfil. Aqui está a régua, o tamanho da base e o que ela não garante." />
      {isLoading && <><Esqueleto altura={220} /><Esqueleto tipo="linhas" n={5} /></>}
      {error && <Erro erro={error} onTentar={refetch} />}
      {data && (
        <>
          {data.passos.length > 0 && (
            <Secao titulo="A régua, em quatro passos" className="metodo-regua">
              <Passos passos={data.passos} />
              {data.metodologia_md && (
                <>
                  <div><Botao variante="fantasma" tamanho="p" aria-expanded={metodologia} onClick={() => setMetodologia(!metodologia)}>{metodologia ? "Recolher a metodologia" : "Ver a metodologia completa →"}</Botao></div>
                  <AnimatePresence initial={false}>
                    {metodologia && (
                      <motion.div className="metodo-abre" initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.35, ease: EASE }}>
                        <Markdown texto={data.metodologia_md} className="metodo-md" />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </>
              )}
            </Secao>
          )}

          {data.numeros.length > 0 && (
            <Secao titulo="O tamanho da base" sub={info ? `Foco ${info.nome}. Coleta de ${fmtData(info.base.coletado_em)}.` : undefined} bloco="lima">
              <Numeros numeros={data.numeros} />
            </Secao>
          )}

          <Secao titulo="Dá para confiar na leitura automática?" sub="Os padrões saem de uma IA que lê cada post. Para conferir, uma pessoa leu uma amostra dos mesmos posts e as duas leituras foram comparadas campo a campo.">
            {data.kappa.length > 0 ? <Kappa kappa={data.kappa} /> : (
              <Vazio titulo="Sem conferência humana neste foco" marca="?">
                {foco === "B"
                  ? "A validação por uma pessoa foi feita só no foco Impulso → empreendedor. Aqui a leitura da IA não foi conferida à mão: trate os padrões como indícios. As limitações abaixo trazem a comparação entre os dois modelos de leitura."
                  : "A leitura da IA ainda não foi comparada com a de uma pessoa nesta base."}
              </Vazio>
            )}
          </Secao>

          {data.avaliacao_md && <Avaliacao md={data.avaliacao_md} nota={data.avaliacao_nota} />}

          {data.limitacoes.length > 0 && (
            <Secao titulo="Limitações" sub="O que pode estar errado, na ordem em que mais pesa.">
              <Limitacoes itens={data.limitacoes} />
            </Secao>
          )}
        </>
      )}
    </>
  );
}
