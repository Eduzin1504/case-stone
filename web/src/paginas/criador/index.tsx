// /criadores/:id: perfil do criador, no jeito de um perfil de rede social.
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useCriador } from "../../api/hooks";
import type { PostResumo } from "../../api/tipos";
import { Botao, Chip, Erro, Esqueleto, Etiqueta, NumeroConta, PostCard, Secao, Seletor, Vazio, useAbrirPost } from "../../componentes";
import { fmtInt, fmtNum, fmtPct, fmtVezes, nomePlataforma, nomePorte } from "../../util/formato";
import { LinhaDoTempo } from "./LinhaDoTempo";
import "./criador.css";

const FAIXA: Record<string, string> = { micro: "perfil pequeno", medio: "perfil médio", grande: "perfil grande" };
type Ordem = "recentes" | "vezes" | "er" | "comentarios";
const ORDENS: { valor: Ordem; rotulo: string }[] = [
  { valor: "recentes", rotulo: "Mais recentes" },
  { valor: "vezes", rotulo: "Mais acima do esperado" },
  { valor: "er", rotulo: "Maior engajamento" },
  { valor: "comentarios", rotulo: "Mais comentados" },
];
const chave: Record<Ordem, (p: PostResumo) => number> = {
  recentes: (p) => (p.publicado ? Date.parse(p.publicado) : 0),
  vezes: (p) => p.vezes ?? -1,
  er: (p) => p.er ?? -1,
  comentarios: (p) => p.comentarios,
};
const PASSO = 30;

export default function Criador() {
  const { id } = useParams();
  const { data, isLoading, error, refetch } = useCriador(id);
  const abrir = useAbrirPost();
  const [soTop, setSoTop] = useState(false);
  const [ordem, setOrdem] = useState<Ordem>("recentes");
  const [visiveis, setVisiveis] = useState(PASSO);

  const posts = useMemo(() => {
    const l = (data?.posts ?? []).filter((p) => !soTop || p.top);
    return [...l].sort((a, b) => chave[ordem](b) - chave[ordem](a));
  }, [data, soTop, ordem]);

  const voltar = <Botao variante="fantasma" tamanho="p" para="/rankings">← Voltar ao ranking</Botao>;
  if (isLoading) return <><div>{voltar}</div><Esqueleto altura={220} /><Esqueleto tipo="cards" n={6} /></>;
  if (error) return <><div>{voltar}</div><Erro erro={error} onTentar={refetch} /></>;
  if (!data) return <><div>{voltar}</div><Vazio titulo="Criador não encontrado" acao={<Botao para="/rankings">Ver o ranking de criadores</Botao>}>Esse perfil não está na base deste foco. Troque o foco ou escolha outro criador no ranking.</Vazio></>;

  const c = data.resumo;
  const [nome, ...resto] = c.nome.split("|").map((s) => s.trim());
  const complemento = resto.join(" · ");
  const inicial = [...(nome || c.nome).normalize("NFKD")].find((ch) => /[\p{L}\p{N}]/u.test(ch))?.toUpperCase() ?? "?";
  const concorre = c.vezes != null;
  const nTop = data.posts.filter((p) => p.top).length;

  return (
    <>
      <div className="nao-imprimir">{voltar}</div>

      <header className="criador-cab">
        <span className="criador-avatar" aria-hidden>{inicial}</span>
        <div className="criador-id">
          <h1 className="t-titulo criador-nome">{nome || c.nome}</h1>
          {complemento && <p className="criador-complemento">{complemento}</p>}
          <p className="criador-linha">
            <b>{nomePlataforma(c.plataforma)}</b>
            <span>{fmtNum(c.seguidores)} seguidores</span>
            <span>{FAIXA[c.porte] ?? `perfil ${nomePorte(c.porte)}`}</span>
          </p>
          {data.bio && <p className="criador-bio corta-3">{data.bio}</p>}
          <div className="linha">
            <Botao variante="contorno" tamanho="p" href={c.url}>Abrir no {nomePlataforma(c.plataforma)}</Botao>
          </div>
        </div>
      </header>

      <div className="criador-numeros">
        <div className="criador-num">
          <NumeroConta valor={c.n_posts} formato={fmtInt} className="t-titulo criador-num-valor" />
          <span>posts na base</span>
        </div>
        <div className="criador-num">
          <NumeroConta valor={c.n_top} formato={fmtInt} className="t-titulo criador-num-valor" />
          <span>{c.n_top === 1 ? "post no top" : "posts no top"}</span>
        </div>
        {c.er_mediano != null && (
          <div className="criador-num">
            <NumeroConta valor={c.er_mediano} formato={fmtPct} className="t-titulo criador-num-valor" />
            <span>engajamento mediano (ER)</span>
          </div>
        )}
        <div className="criador-num criador-num--chave">
          {concorre
            ? <Etiqueta valor={fmtVezes(c.vezes)} rotulo="o esperado para o tamanho" tamanho="g" />
            : <p className="criador-fora"><b>Fora da disputa do top.</b> Os posts deste perfil não entraram na conta do esperado, então não há “vezes o esperado” para mostrar. Os outros números continuam valendo.</p>}
        </div>
      </div>

      {(c.tema || c.formato) && (
        <div className="linha">
          {c.tema && <Chip rotulo="Tema mais frequente">{c.tema}</Chip>}
          {c.formato && <Chip rotulo="Formato mais frequente">{c.formato}</Chip>}
        </div>
      )}

      {data.serie.length > 1 && (
        <Secao
          titulo="Post a post" bloco="superficie"
          sub={concorre || data.serie.some((s) => s.vezes != null) ? "Cada ponto é um post. Acima da linha, rendeu mais que o esperado para o tamanho do perfil." : "Cada ponto é um post. Este perfil não concorre ao top, então a altura mostra o engajamento."}
        >
          <LinhaDoTempo serie={data.serie} posts={data.posts} onAbrir={abrir} />
        </Secao>
      )}

      <Secao
        titulo="Posts"
        sub={`${fmtInt(posts.length)} ${soTop ? "no top" : "na base"}`}
        acao={
          <div className="linha criador-filtros">
            <Chip ativo={soTop} onClick={() => { setSoTop(!soTop); setVisiveis(PASSO); }}>Só top{nTop ? ` (${nTop})` : ""}</Chip>
            <Seletor rotulo="Ordenar" esconderRotulo valor={ordem} onChange={(v) => setOrdem(v as Ordem)} opcoes={ORDENS} />
          </div>
        }
      >
        {posts.length ? (
          <>
            <div className="criador-grade" id="criador-grade">
              {posts.slice(0, visiveis).map((p) => <PostCard key={p.id} post={p} variante="compacto" semCriador />)}
            </div>
            {posts.length > visiveis && (
              <div className="linha criador-mais">
                <Botao variante="contorno" onClick={() => setVisiveis(visiveis + PASSO)}>Mostrar mais {Math.min(PASSO, posts.length - visiveis)}</Botao>
                <span className="t-sec t-pequeno">{visiveis} de {fmtInt(posts.length)}</span>
              </div>
            )}
          </>
        ) : (
          <Vazio titulo="Nenhum post no top" acao={<Botao onClick={() => setSoTop(false)}>Ver todos os posts</Botao>}>Este perfil não tem posts no top desta base.</Vazio>
        )}
      </Secao>
    </>
  );
}
