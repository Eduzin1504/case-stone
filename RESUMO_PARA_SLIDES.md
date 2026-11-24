# Números finais para os slides (24/11/2026)

Fontes: `data/stone.db`, `data/foco_b.db`, `data/avaliacao_regua.md`, `data/padroes_selados.csv`, `data/b_achados.csv`, `data/b_analise.txt`.

## 1. Dois focos
- **Foco A, "Impulso → empreendedor":** conteúdo que engaja donos de pequeno negócio. Base `data/stone.db`, playbook `PLAYBOOK.md`.
- **Foco B, "Negócio → cliente":** como o pequeno negócio engaja o cliente final. Coleta nova de 28 negócios reais no Instagram, playbook `PLAYBOOK_B.md`.
- A rubrica do VLM ganhou o campo `publico_alvo`, que separa os dois.

## 2. Régua de alto desempenho (Foco A)
- O ER do TAPI, (curtidas + comentários) ÷ seguidores, continua sendo a métrica reportada.
- O top 10% por plataforma × porte sai do resíduo de um modelo misto, na base elegível, com no máximo 3 posts por criador.
- Base elegível: canal aprovado na validação humana (14 excluídos), post relevante para MPE e voltado a donos de negócio.
- Top final: Instagram 47 posts de 19 criadores; YouTube 203 posts de 76 criadores.

## 3. Antes × depois (auditoria do top)
| | Top por ER puro | Top novo |
|---|---|---|
| YouTube: posts em canais fora do perfil (excluídos na validação + auditoria) | 56% | 4% |
| YouTube: posts em canais excluídos na validação | 51% | 0% (pelo filtro) |
| YouTube: maior criador no top (plataforma inteira) | 14% | 1% |
| YouTube: maior criador no estrato "grande" | 56% | 7% |
| YouTube: relevantes para MPE (entre rotulados) | 68% | 100% (pelo filtro) |
| Instagram: maior criador no top | 24% | 6% |
| Instagram: relevantes para MPE | 77% | 100% (pelo filtro) |

## 4. Avaliação da régua (slide de método)
- O viés de tamanho some: a correlação do score com seguidores vai de −0,49 (Instagram) e −0,28 (YouTube) para perto de 0.
- O engajamento cresce com expoente de cerca de 0,37 em relação aos seguidores. O ER puro assume 1,0.
- O modelo misto não supera o outlier simples (post ÷ mediana do criador) em posts futuros. O ganho vem de comparar o post com o próprio criador, do limite por criador e do filtro da base.
- Com o limite por criador, o "top 10%" equivale a 1,8% da base do YouTube e a 7,2% da do Instagram.

## 5. Padrões do Foco A
- **Instagram:** segmento finanças e contabilidade 5,7×; tema finanças 4,3×; gancho com promessa 2,4×; carrossel 1,8×. Aparecem menos no top: tema vendas 0,48 e talking head 0,64.
- **YouTube:** gatilho pessoa real 3,8×; bastidores 2,9×; segmento alimentação 4,0×.
- "Pessoa real" e "convite à participação" seguem confirmados pelos Ads do Impulso.
- "Genérico" deixou de diferenciar o top (lift 1,01). A seção 2 do `PLAYBOOK.md` foi reescrita; reler antes de usar a tese "reação não é clique".

## 6. Foco B
- 62 posts no top e 62 no controle, de 23 negócios (alimentação, beleza, moda, pet).
- Humor ou trend 3,9×; mostrar o processo 1,7×; "produto em destaque" 0,58, porque é o post padrão de todos.
- **Curtida não é pedido:** posts de humor têm 2% de comentários com intenção de compra. Posts que mostram preço têm 59%, contra 9% dos que não mostram (só 10 posts; indício).

## 7. Limitações a declarar
- No YouTube, a maior parte da amostra nova foi vista por capa e texto (DeepSeek), não em vídeo: a cota grátis do Gemini acabou.
- No Foco B, o lift foi calculado com imagens e legenda; só 24 posts passaram pelo Gemini (20 em vídeo e 4 por imagens).
- A validação humana (kappa, 10 posts) é da amostra anterior.
- O canal Tudo de Laço ficou como "dúvida" na validação e tem 3 posts no top do YouTube; vale decidir antes de apresentar.
- A relevância para MPE é rotulada pelo VLM, e ainda passam posts fora do tema (por exemplo, política e fofoca em perfis de negócio).
- O Foco B cobre de 2 a 6 semanas por perfil e inclui a Black Friday.
