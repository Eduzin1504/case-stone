# Criativos renderizados (carrossel PNG + Reels animatic)

## Por quê
O agente entrega roteiro em texto; o cliente (Stone/Impulso) lê, mas não *vê* o post. Objetivo: transformar cada
criativo em peça visual pronta para olhar e baixar, na plataforma e pelo MCP. Não é exigência do TAPI; é tangibilidade.

## Metas / não-metas / anti-metas
- Meta: as 5 pautas do playbook e qualquer resposta nova do agente viram carrossel (PNGs 1080×1350) ou Reels animatic (MP4 1080×1920).
- Meta: mesma função serve API (tela Criar) e MCP.
- Não-meta: filmagem real, publicação no Instagram, edição dos slides na tela.
- Anti-meta: rosto sintético de empreendedor (regra do PLANO); "cara de IA"; custo variável na VPS; derrubar o container (700 MB).

## Abordagens consideradas
- **A (escolhida): template de marca, sem IA de mídia.** Custo ~0, previsível, on-brand. Reels fica tipográfico.
- B: A + imagem de IA na capa/fundo (Feita, ~US$ 0,04/imagem, selo "ilustração feita com IA"). Fica para depois.
- C: vídeo gerado (Seedance/Veo, US$ 1–2/peça, assíncrono, risco de 503). Só como teste com saldo grátis, ver abaixo.

## Design
- `render_criativo.py` (um arquivo): `renderizar(criativo) -> [caminhos]`.
  - Entrada: o `Criativo` que já existe (`formato`, `gancho`, `roteiro`, `cta`) + `dados.cenas(roteiro)` para os quadros.
  - Texto do quadro: o trecho entre aspas da cena (fala/texto do slide); sem aspas, a cena inteira. Indicações de direção ("texto grande, fundo limpo") não vão para a peça.
  - Carrossel (formato casa `carross|estátic|slide|card`): Pillow, 1080×1350, Lexend (TTF OFL no repo), Sherwood `#004132` / lima `#c7f93c` / `#efefef`, logo `web/src/marca/impulso-stone-*.png`, capa em lima com o gancho, último slide com o CTA, rodapé @impulsostone + nº do slide.
  - Reels: mesmos quadros em 1080×1920; duração de cada quadro pela marca de tempo da cena (`0-4s`), senão 3 s; ffmpeg (já no Dockerfile) junta em MP4 sem áudio.
  - Saída em `data/render/<hash do criativo>/`; se já existe, devolve sem refazer (cache por conteúdo).
- API: `GET /criativos/render?...` ou campo `pecas` na resposta do agente com URLs servidas por `StaticFiles` em `/midia/render`.
- Tela Criar: o storyboard mostra as PNGs/MP4 no lugar dos cartões de texto (texto continua acessível como legenda/alt) + "Baixar".
- MCP: ferramenta `renderizar_criativo(criativo)` devolve as imagens (ImageContent) e as URLs.
- As 5 pautas são pré-renderizadas localmente e versionadas, para a demo não depender da VPS.
- Uma checagem: `__main__` com assert renderizando a pauta 1 e 2 (nº de PNGs = nº de cenas; MP4 existe e dura ≈ soma dos tempos).

## Restrições
- VPS: 700 MB RAM, ~3,7 GB disco. Pillow + ffmpeg cabem; render sob demanda com cache, um por vez.
- Sem custo de API no caminho A.

## Teste opcional de vídeo (C) com US$ 2
Uma conta nova da Feita com ~US$ 2 livres dá ~1 Reels de 30 s em Seedance 2.0 mini 480p (~US$ 1,05), ou ~8–10 clipes de 5 s.
Melhor uso: 1 clipe de abertura de ~5 s sem rosto por pauta (≈ US$ 0,90 no total), colado antes do animatic. Testar 1 clipe antes.

## Fica com o construtor
Layout fino dos slides (tamanhos de fonte, quebra de linha), nome exato da rota, posição do botão Baixar.
