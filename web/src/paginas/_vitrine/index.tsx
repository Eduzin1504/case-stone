// Vitrine (/_vitrine, fora do menu): todos os componentes compartilhados com dados de exemplo, nos estados principais.
// É a documentação viva da fundação. Copie os trechos daqui para as páginas.
import { useRef, useState } from "react";
import { usePadroes, usePost, usePosts } from "../../api/hooks";
import { ErroApi } from "../../api/cliente";
import {
  BarraPar, Botao, BotaoColecao, BotaoExportar, Campo, Carimbo, Chip, Comprovante, Erro, Esqueleto, Etiqueta, LegendaBarraPar, Markdown, Midia,
  MolduraCelular, NumeroConta, PostCard, Secao, Seg, Seletor, Selo, TituloPagina, Vazio, useAbrirPost,
} from "../../componentes";
import { useFoco } from "../../contexto/Foco";
import { fmtInt, fmtPct, fmtVezes } from "../../util/formato";
import "./vitrine.css";

const CORES = ["--floresta", "--lima", "--lima-suave", "--dados", "--magenta", "--fundo", "--superficie", "--afundado", "--texto", "--texto-2", "--linha", "--tinta"];

export default function Vitrine() {
  const { foco, setFoco, info } = useFoco();
  const abrir = useAbrirPost();
  const { data: pagina, isLoading, error, refetch } = usePosts({ limit: 40 });
  const { data: padroes } = usePadroes("instagram");
  const [seg, setSeg] = useState("instagram");
  const [tema2, setTema2] = useState("");
  const [soTop, setSoTop] = useState(true);
  const [texto, setTexto] = useState("");
  const alvo = useRef<HTMLDivElement>(null);

  const posts = pagina?.itens ?? [];
  const yt = posts.find((p) => p.plataforma === "youtube");
  const carrossel = posts.find((p) => p.formato === "Carrossel");
  const video = posts.find((p) => p.id === "DV14VREjmcx");
  const { data: dCarrossel } = usePost(carrossel?.id);
  const { data: dVideo } = usePost(video?.id);
  const barras = (padroes?.itens ?? []).filter((p) => p.lift != null).sort((a, b) => (b.lift ?? 0) - (a.lift ?? 0));
  const mostra = [...barras.slice(0, 4), ...barras.slice(-2)];
  const max = Math.max(...mostra.map((p) => Math.max(p.freq_top, p.freq_controle)), 0.1);

  return (
    <>
      <TituloPagina
        titulo="Vitrine" grifo="da fundação"
        sub="Todos os componentes compartilhados, com dados de exemplo. Passe o mouse, use o teclado, troque o foco."
        acoes={
          <>
            <Seg rotulo="Foco" valor={foco} onChange={setFoco} opcoes={[{ valor: "A", rotulo: "Foco A" }, { valor: "B", rotulo: "Foco B" }]} />
          </>
        }
      />

      <Secao titulo="Tipo e cor" sub="Anton para títulos e números; Lexend para texto; JetBrains Mono só em rótulo técnico e no comprovante.">
        <div className="vit-tipo">
          <div>
            <p className="t-titulo t-mega"><NumeroConta valor={5677} formato={fmtVezes} /></p>
            <p className="t-sec">.t-titulo .t-mega com &lt;NumeroConta&gt;: número-manchete ao lado de texto pequeno.</p>
          </div>
          <div className="pilha">
            <p className="t-titulo t-h1">Título <span className="grifo">de página</span></p>
            <p className="t-titulo t-h2">Título de seção</p>
            <p className="t-h3">Subtítulo em Lexend 600 (.t-h3)</p>
            <p>Texto corrido em Lexend 400. Direto e neutro, sem jargão. <span className="t-sec">Texto secundário (.t-sec).</span></p>
            <p className="t-mono">rótulo técnico em mono · 11.021 posts</p>
          </div>
        </div>
        <ul className="vit-cores">
          {CORES.map((c) => (
            <li key={c}><i style={{ background: `var(${c})` }} /><span className="t-mono">{c}</span></li>
          ))}
        </ul>
      </Secao>

      <Secao titulo="Controles" sub="Botao, Seg, Chip, Selo, Campo, Seletor">
        <div className="linha">
          <Botao>Primário</Botao>
          <Botao variante="lima">Lima</Botao>
          <Botao variante="contorno">Contorno</Botao>
          <Botao variante="fantasma">Fantasma</Botao>
          <Botao ocupado>Salvando</Botao>
          <Botao disabled>Desligado</Botao>
          <Botao variante="contorno" href="https://www.instagram.com/impulsostone/">Abrir no Instagram</Botao>
        </div>
        <div className="linha">
          <Botao tamanho="g" variante="lima" para="/catalogo">Ver o catálogo →</Botao>
          <Botao tamanho="g">Avaliar meu post</Botao>
          <Botao tamanho="p" variante="contorno">Pequeno</Botao>
        </div>
        <div className="linha">
          <Seg rotulo="Plataforma" valor={seg} onChange={setSeg} opcoes={[{ valor: "instagram", rotulo: "Instagram" }, { valor: "youtube", rotulo: "YouTube" }, { valor: "todas", rotulo: "Todas" }]} />
          <Seg tamanho="p" rotulo="Métrica" valor="vezes" onChange={() => {}} opcoes={[{ valor: "vezes", rotulo: "× o esperado" }, { valor: "er", rotulo: "ER" }, { valor: "comentarios", rotulo: "Comentários" }]} />
        </div>
        <div className="linha">
          <Chip rotulo="Tema">finanças</Chip>
          <Chip rotulo="Gancho">promessa</Chip>
          <Chip>✓ Texto na tela</Chip>
          <Chip ativo={soTop} onClick={() => setSoTop(!soTop)}>Só o top</Chip>
          <Chip onRemover={() => {}}>carrossel</Chip>
        </div>
        <div className="linha">
          <Selo tipo="confirmado" /><Selo tipo="contradito" /><Selo tipo="só mercado" /><Selo tipo="inconclusivo" /><Selo tipo="frágil" />
        </div>
        <div className="vit-campos">
          <Campo rotulo="Nome da coleção" placeholder="ex.: Ganchos com número" value={texto} onChange={(e) => setTexto(e.target.value)} dica="Aparece na lista de coleções." />
          <Campo rotulo="Campo com erro" defaultValue="" erro="Dê um nome para a coleção." />
          <Seletor rotulo="Tema" valor={tema2} onChange={setTema2} opcoes={pagina?.filtros.temas ?? []} todos="Todos os temas" />
          <Campo className="vit-largo" rotulo="Buscar por ideia" esconderRotulo tamanho="g" placeholder="Buscar por ideia: separar o dinheiro da casa e do negócio" />
          <Campo className="vit-largo" rotulo="Legenda ou roteiro" multilinha rows={3} placeholder="Cole aqui a legenda, ou o roteiro se ainda não gravou." />
        </div>
      </Secao>

      <Secao titulo="Identidade de pequeno comércio" sub="Etiqueta de preço para o número-chave, carimbo para o que foi conferido, comprovante para checagens e resumos.">
        <div className="vit-identidade">
          <div className="pilha" style={{ alignItems: "flex-start" }}>
            <Etiqueta tamanho="g" valor="5,7 mil×" rotulo="o esperado para este perfil" />
            <Etiqueta valor="2,4×" rotulo="mais no top" />
            <Etiqueta tamanho="p" valor="437%" rotulo="de ER" tom="papel" />
            <Etiqueta valor="59%" rotulo="comentam querendo comprar" tom="floresta" />
          </div>
          <div className="linha" style={{ gap: 28 }}>
            <Carimbo texto="TOP" sub="10%" tamanho={104} />
            <Carimbo texto="Aprovado" sub="na validação" tom="dados" tamanho={112} giro={7} />
            <Carimbo texto="Confirmado" sub="nos Ads" tamanho={120} giro={-5} />
            <Carimbo texto="Contradito" sub="nos Ads" tom="alerta" tamanho={112} giro={8} />
            <Carimbo texto="TOP" sub="nº 1" cheio />
          </div>
          <Comprovante
            titulo="Fora da Curva" sub={info?.nome}
            linhas={[
              { rotulo: "Posts lidos", valor: fmtInt(info?.base.posts) },
              { rotulo: "Instagram", valor: fmtInt(info?.base.por_plataforma.instagram) },
              { rotulo: "YouTube", valor: fmtInt(info?.base.por_plataforma.youtube) },
              { rotulo: "Criadores", valor: fmtInt(info?.base.criadores), destaque: true },
            ]}
            total={{ rotulo: "No top", valor: fmtInt(info?.base.top) }}
            rodape={<>coletado em {info?.base.coletado_em?.split("-").reverse().join("/")}<br />confira antes de usar</>}
          />
        </div>
      </Secao>

      <Secao titulo="Padrões do top" sub="BarraPar: as barras crescem ao entrar na tela. O número à direita é o lift." bloco="superficie">
        <LegendaBarraPar />
        <div>
          {mostra.map((p) => (
            <BarraPar key={p.campo + p.valor} rotulo={p.rotulo} top={p.freq_top} controle={p.freq_controle} lift={p.lift} selo={p.selo} fragil={p.fragil} max={max} />
          ))}
          {!padroes && <Esqueleto tipo="linhas" n={4} />}
        </div>
      </Secao>

      <Secao titulo="Curtida não é pedido" sub="Secao bloco=&quot;lima&quot;: no máximo um por dobra. Tudo dentro troca para floresta sozinho." bloco="lima">
        <div className="vit-lima">
          <p className="t-titulo t-mega"><NumeroConta valor={0.59} formato={fmtPct} /></p>
          <div className="pilha">
            <p className="t-h3">dos comentários em posts que mostram o preço têm intenção de compra. Nos que não mostram, 9%.</p>
            <p className="t-sec">Só 10 posts: é um indício, não uma regra.</p>
            <div className="linha"><Botao>Ver o funil</Botao><Botao variante="contorno">Como medimos</Botao><Selo tipo="frágil" /></div>
          </div>
        </div>
      </Secao>

      <Secao titulo="PostCard em mosaico" sub="Clique abre o painel (?post=). Passe o mouse para ver a ficha rápida. O primeiro usa `destaque`.">
        {isLoading && <Esqueleto tipo="cards" n={8} />}
        {error && <Erro erro={error} onTentar={refetch} />}
        <div className="mosaico">
          {posts.slice(0, 11).map((p, i) => <PostCard key={p.id} post={p} destaque={i === 0} />)}
        </div>
      </Secao>

      <Secao titulo="PostCard compacto e em linha">
        <div className="vit-compactos">
          {posts.slice(11, 18).map((p) => <PostCard key={p.id} post={p} variante="compacto" />)}
        </div>
        <div className="vit-linhas">
          {posts.slice(0, 5).map((p, i) => <PostCard key={p.id} post={p} variante="linha" posicao={i + 1} />)}
        </div>
      </Secao>

      <Secao titulo="Mídia na moldura" sub="Midia cobre os cinco tipos de `post.midia`: youtube, video, imagens, capa e nenhuma.">
        <div className="vit-celulares">
          {yt && <figure><MolduraCelular largura={210}><Midia midia={{ tipo: "youtube", youtube_id: yt.id }} thumb={yt.thumb} titulo={yt.titulo} url={yt.url} plataforma="youtube" /></MolduraCelular><figcaption>youtube</figcaption></figure>}
          {dVideo && <figure><MolduraCelular largura={210}><Midia midia={dVideo.midia} thumb={dVideo.thumb} titulo={dVideo.titulo} url={dVideo.url} plataforma={dVideo.plataforma} /></MolduraCelular><figcaption>video</figcaption></figure>}
          {dCarrossel && <figure><MolduraCelular largura={210}><Midia midia={dCarrossel.midia} thumb={dCarrossel.thumb} titulo={dCarrossel.titulo} url={dCarrossel.url} plataforma={dCarrossel.plataforma} /></MolduraCelular><figcaption>imagens (← →)</figcaption></figure>}
          {carrossel && <figure><MolduraCelular largura={210}><Midia midia={{ tipo: "capa" }} thumb={carrossel.thumb} titulo={carrossel.titulo} url={carrossel.url} plataforma={carrossel.plataforma} /></MolduraCelular><figcaption>capa</figcaption></figure>}
          <figure><MolduraCelular largura={210}><Midia midia={{ tipo: "nenhuma" }} titulo="Post sem mídia" url="https://www.instagram.com/" plataforma="instagram" /></MolduraCelular><figcaption>nenhuma</figcaption></figure>
        </div>
      </Secao>

      <Secao titulo="Estados" sub="Esqueleto, Vazio e Erro">
        <div className="vit-estados">
          <Esqueleto tipo="cards" n={4} />
          <div className="pilha"><Esqueleto tipo="linhas" n={3} /><Esqueleto tipo="texto" n={4} /></div>
        </div>
        <Vazio titulo="Nada por aqui" acao={<Botao variante="contorno">Limpar filtros</Botao>}>Nenhum post bate com esses filtros. Tire um filtro ou troque a plataforma.</Vazio>
        <Erro erro={new ErroApi("Não foi possível falar com o servidor. Confira se a API está no ar.", 0)} onTentar={() => {}} />
      </Secao>

      <Secao titulo="Ações" sub="BotaoColecao, BotaoExportar e useAbrirPost">
        <div className="linha">
          {posts[0] && <BotaoColecao postId={posts[0].id} abreParaCima={false} />}
          {posts[1] && <Botao variante="contorno" onClick={() => abrir(posts[1].id)}>Abrir o painel de um post</Botao>}
          <BotaoExportar alvo={alvo} nome="vitrine-exemplo" />
        </div>
        <div ref={alvo} className="vit-exportavel">
          <p className="t-titulo t-h2">O que sai no PNG</p>
          <div className="linha"><Etiqueta valor="4,3×" rotulo="tema finanças no top do Instagram" /><Carimbo texto="TOP" sub="10%" /></div>
          <BarraPar rotulo="Gancho com promessa" top={0.234} controle={0.098} lift={2.4} selo="só mercado" />
        </div>
      </Secao>

      <Secao titulo="Markdown" sub="Para os textos que vêm da API: playbook, método e a explicação do agente.">
        <Markdown texto={"## Como ler\n\nO **lift** diz quantas vezes o padrão é mais comum no top. Lift `2,0` é o dobro.\n\n- Confirmado: funciona no mercado e nos Ads.\n- Só mercado: ainda não testado.\n\n| Padrão | Top | Controle |\n|---|---|---|\n| Gancho com promessa | 23% | 10% |\n| Talking head | 21% | 33% |\n\n> Padrão com menos de 5 posts no top é um indício: vale testar."} />
      </Secao>
    </>
  );
}
