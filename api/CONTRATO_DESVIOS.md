# Desvios e esclarecimentos do contrato da API

Contrato: `docs/superpowers/specs/2026-11-24-pauta-react-design.md`. Onde o contrato deixava a forma em aberto, a API
segue `web/src/api/tipos.ts` (lido em 24/11, depois de escrito pela fundação). Nenhuma chave prometida foi removida.

## Desvios

1. **`/viz/anatomia/{id}`: `inicio_s` e `fim_s` podem ser `null`** (em `tipos.ts` são `number`). Acontece em post sem
   duração (imagem e carrossel: `duracao_s` é `null`), nos trechos que não são o gancho. Não há tempo para informar e a
   API não inventa. Em vídeo, os tempos vêm sempre em número: gancho de 0 a 3 s; "O que explica a atenção" do fim do
   gancho até 3 s antes do fim; "Chamada para ação" nos 3 s finais. Esses dois últimos são posição aproximada, não
   medida, e vêm com `aproximado: true`. O gancho só vem com `aproximado: false` quando a leitura foi do vídeo inteiro.
   Os elementos vêm num trecho só (`texto` com os itens separados por "; " e a chave extra `itens` com a lista), não um
   trecho por elemento: a rubrica não diz quando cada um aparece.
2. **`/viz/funil?foco=A`** devolve a mesma forma, vazia: listas vazias e `preco.com` / `preco.sem` = `null` (em
   `tipos.ts` são `number`). O funil só existe no Foco B.
3. **`/agente/{id}` (`resultado`), `/agente/salvas` e `/criativos`** usam o formato `RespostaAgente` de `tipos.ts`
   (`achados`, `referencias`, `criativos`, `explicacao`, `baixa_confianca`, `filtros_relaxados`), não as chaves em inglês
   do `agent.py` (`findings`, `reference_posts`, `creatives`…). As referências vêm como `PostResumo` do Foco A (o agente
   só trabalha com essa base), mesmo quando o pedido chega com `?foco=B`.
4. **`/metodo`**: `numeros` é lista plana `{rotulo, valor, nota, plataforma}` (`nota` = nome da plataforma; `valor` já
   formatado) e `limitacoes` é lista de frases em texto simples, como em `tipos.ts`. O markdown original vem em
   `limitacoes_md`. `kappa` vem vazio no Foco B (a validação manual foi feita só no Foco A).
5. **`/posts`: `porte` é o valor cru** (`micro`, `medio`, `grande`), em `PostResumo`, `CriadorResumo` e
   `filtros.portes`, porque o front traduz com `nomePorte`. O filtro `porte` aceita `medio` e `médio`.
6. **`/criadores`** lista todos os criadores da base (127 no A, 28 no B), não só os da lista de destaque; quem não
   concorre ao top tem `vezes: null` e fica no fim. `tema` e `formato` são os mais frequentes nos posts do criador.
   `n_posts` conta todos os posts do criador na base (o CSV de destaque conta só os elegíveis).
7. **`POST /avaliar`** aceita os arquivos no campo `arquivos` (como o front manda) ou `arquivos[]`, e também JSON
   quando é só texto. O `id` devolvido é o mesmo do histórico (`/avaliacoes/{id}`).
8. **`DELETE /colecoes/{id}/posts`** recebe o post em `?post_id=` (como o front manda), no corpo `{post_id}` ou no
   caminho (`/colecoes/{id}/posts/{post_id}`). `POST /colecoes` lê o foco de `?foco=` ou do corpo. `id` da coleção é
   texto.
9. **Rota a mais:** `/midia/avaliacoes/<id>.jpg` serve as miniaturas do que foi enviado para avaliar (`thumb` do
   histórico).

## Chaves a mais (não estão no contrato; podem ser ignoradas)

- `PostDetalhe`: `seguidores`, `duracao_s`, `concorre`.
- `CriadorResumo`: `er_mediano`, `comentarios`.
- `Padrao`: `confianca`. `/padroes`: `plataforma` (a que foi usada; sem o parâmetro, a primeira de `plataformas`).
- `/ads`: `periodo`, `marcas`, `impressoes`, `engajamento`, `nota`.
- `/viz/esperado-real` (pontos): `plataforma`. `/viz/temas`: `pct_controle`. `/viz/anatomia`: `nota`; trechos: `itens`.
- `/viz/funil`: `nota`; comentários: `segmento`.
- Cenas: `rotulo` (anotação curta da cena, como "capa" ou "GANCHO"). `RespostaAgente`: `tentativas`, `pendencias`;
  achados: `fragil`.
- `/playbook`: `titulo_original`, `intro`; capítulos: `rotulo`, `titulo_original`.
- `/metodo`: `metodologia_md`, `avaliacao_nota`, `limitacoes_md`; kappa: `rotulo`, `n`.
- Resultado do `/avaliar`: `id`, `thumb`; em `parecidos`, `post` (`PostResumo`). Histórico: `metodo`, `estado`.

## Convenções

- `er`, frequências e `pct_intencao` são frações (0,25 = 25%). `ctr` dos Ads vem em % (8,82), como no CSV.
- `vezes` = exp(`resid`), `null` quando o post não concorre ao top. Datas em ISO.
- `metodo_leitura`: "vídeo completo, com áudio", "imagens do post" ou "só a capa".
- `/padroes` sem `plataforma` usa a primeira de `plataformas` (Instagram). `selo` é `null` no Foco B.
- `/busca`: `score` de 0 a 1 (cosseno TF-IDF × fração das palavras da pergunta que casaram); `casou` traz as palavras
  como a pessoa digitou.
- Trabalhos de `/avaliar` e `/agente` ficam na memória do processo: somem se a API reiniciar (o histórico não).
