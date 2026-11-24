# Playbook B — Como o pequeno negócio engaja o cliente dele no Instagram

Foco B do case Inteli Academy × Impulso Stone. O Foco A olha para conteúdo que fala com o dono do negócio; este aqui olha para o que o próprio negócio (padaria, salão, loja de bairro, pet shop, ateliê) posta para quem compra dele.

## Metodologia em 5 linhas

1. **Base:** 28 negócios reais brasileiros achados em 11 hashtags de negócio local (275 posts, 242 autores, 60 perfis triados, 42 aprovados). 1.013 posts coletados em 24/11/2026; 848 com curtidas visíveis; 731 elegíveis de 25 perfis (15 micro até 10 mil seguidores, 9 médios, 1 grande).
2. **Régua:** ER = (curtidas + comentários) ÷ seguidores é o número reportado. O "top" é o top 10% dentro de cada porte pelo resíduo de um modelo misto (quanto o post superou o esperado para aquele perfil, formato e idade), com no máximo 3 posts por perfil: 62 posts. Controle: 62 posts sorteados fora do top (seed 42).
3. **Rubrica:** os 124 posts foram lidos por um modelo de visão (DeepSeek: até 5 imagens + legenda). 117 são de fato o negócio falando com cliente (59 top, 58 controle). Lift = frequência no top ÷ frequência no controle.
4. **Intenção de compra:** 2.464 comentários de clientes que vieram junto dos posts; os 703 do top e do controle foram classificados (pergunta preço, endereço, entrega, "quero") por regex + DeepSeek.
5. **Limites:** amostra pequena e não aleatória, um único dia de coleta, correlação e não causa. Achado com menos de 5 posts no top está marcado como **frágil**. Detalhes no fim.

## A descoberta principal: o que dá curtida não é o que dá pedido

Os dois grupos têm a mesma taxa de intenção de compra nos comentários (top 15,2%, n = 55 posts; controle 14,2%, n = 32). Ou seja: viralizar não trouxe mais gente perguntando preço. O que muda a intenção de compra é outra coisa:

| O post… | Posts | Comentários com intenção de compra |
|---|---|---|
| mostra o preço | 10 | **59%** |
| não mostra o preço | 77 | 9% |
| formato humor/trend | 13 | 2% |
| formato produto em destaque | 45 | 17% |
| formato bastidor de produção | 13 | 20% |

Na base inteira (regex, 461 posts com comentário), legenda com preço: 27% dos comentários com intenção contra 9% sem preço (44 posts de 7 perfis). Em compensação, post com preço na legenda entra menos no top (4,7% contra 7,6%). São dois trabalhos diferentes, e o lojista precisa dos dois.

## Padrões (top × controle, n = 59 × 58)

**1. Humor do dia a dia do negócio é o que mais se destaca.** 20% do top contra 5% do controle (lift 3,9; 12 posts de 8 perfis diferentes). São piadas sobre a rotina que o cliente reconhece. Exemplos: PH Store, loja masculina com 3,4 mil seguidores, "Eu querendo bater a meta de novembro": 7.751 curtidas, 249 mil views ([link](https://www.instagram.com/p/Dfzn09yhGLf/)); Agrofox Pet Shop, "Mais um dia normal trabalhando em pet shop": 3.160 curtidas ([link](https://www.instagram.com/p/DeRrJI1vF6P/)); salão Paulinha Hair, "seu horário é às 14h, não é pra sair de casa às 14h" ([link](https://www.instagram.com/p/Dcbmt4JRL5u/)). Atenção: esses posts quase não geram pergunta de compra (2%).

**2. Só mostrar o produto pronto é o padrão de todo mundo, e não diferencia.** "Produto em destaque" é 76% do controle e 44% do top (lift 0,58; 26 posts no top). Não é que foto de produto atrapalhe: é o post normal. Quem só faz isso fica na média.

**3. Texto na tela ajuda.** 54% do top contra 35% do controle (lift 1,57; n = 32). Uma frase curta em cima do vídeo dizendo do que se trata. Ressalva: é o campo em que os dois modelos mais discordaram (kappa 0,22), então trate como indício.

**4. Mostrar o fazer.** "Mostra processo" aparece em 20% do top contra 12% do controle (lift 1,69; n = 12); formato bastidor, lift 1,47 (n = 9). É onde estão os maiores números absolutos da base: Andressa Cunha Doces (12,9 mil seguidores), mãos montando docinhos: 117.602 curtidas e 4,4 milhões de views ([link](https://www.instagram.com/p/De7P6hCJ-3a/)); Bendito Pão, montagem do pão caseiro: 41.114 curtidas e 1.252 comentários ([link](https://www.instagram.com/p/DeKVQYaM9MR/)); ateliê Costurando Laços cortando uma saia: 2.667 curtidas com 6 mil seguidores e 36% dos comentários pedindo o serviço ([link](https://www.instagram.com/p/DbBBc6lx9Kf/)).

**5. Abrir com curiosidade ou humor em vez de só o produto parado.** Gancho "curiosidade": lift 1,69 (n = 12); "humor": 2,16 (n = 11); "produto na tela": 0,76 (n = 31).

**6. Cliente de verdade aparecendo (só salão, por enquanto).** 14% do top contra 3% do controle (lift 3,9; n = 8), mas os 8 posts são de 4 salões de beleza. Vale para beleza: FAMA Cabeleireiros (3,5 mil seguidores), cliente mostrando o corte curto: 7.263 curtidas e 3.050 comentários ([link](https://www.instagram.com/p/Dfva_sApV_E/)). Para outros segmentos, sem evidência.

**7. Dica rápida para o cliente (frágil no limite).** Tutorial/dica: 8,5% contra 3,4% (lift 2,5; n = 5, 4 perfis). Zcoiffeur, "O segredo para um cabelo cheio de movimento": 22.736 curtidas, 1,36 milhão de views e 42% dos comentários com intenção ([link](https://www.instagram.com/p/De69nJci1Y_/)).

**8. Pedir "encomende" ou "chama no direct" não aumenta curtida.** CTA "encomendar": lift 0,57 (n = 7); "direct/WhatsApp": 0,56 (n = 4, frágil). 64% do top não pede nada. O pedido de compra funciona melhor no post de preço (ver a descoberta principal).

**Não fez diferença nesta base:** rosto do dono (lift 1,06), qualidade de produção (nota mediana 7 nos dois grupos), data sazonal (0,84), convidar a comentar (0,86), Reel × carrossel × foto dentro do top (o modelo já desconta o formato; no ER bruto, Reel e carrossel ficam em 0,5% e foto em 0,14%).

**Frágeis (menos de 5 posts no top, não use como regra):** formato oferta/promoção (lift 2,95; n = 3), CTA "link" (n = 4), CTA "visitar loja" (n = 2), vídeo acima de 60 s (n = 3), depoimento (n = 1), prova social (n = 1).

## Perfis em destaque

Ordenados pelo efeito do criador no modelo (engajam acima do esperado para o tamanho):

| Perfil | Segmento | Seguidores | ER mediano | O que mais faz |
|---|---|---|---|---|
| [@stylecompany.shop](https://www.instagram.com/stylecompany.shop/) | moda (streetwear, Passos-MG) | 6.891 | 5,2% | produto em destaque (só 12 posts elegíveis) |
| [@studio_mylenacosta](https://www.instagram.com/studio_mylenacosta/) | beleza (Estreito-MA) | 3.973 | 5,7% | bastidor do atendimento (11 posts elegíveis) |
| [@andressacunhadoces](https://www.instagram.com/andressacunhadoces/) | confeitaria (Mimoso do Sul-ES) | 12.869 | 1,1% | bastidor de produção |
| [@taina_gda](https://www.instagram.com/taina_gda/) | panificação artesanal | 2.822 | 1,8% | produto em destaque |
| [@benditopaoroo](https://www.instagram.com/benditopaoroo/) | padaria (Rondonópolis-MT) | 44.515 | 1,4% | bastidor de produção |
| [@agrofoxpetshop](https://www.instagram.com/agrofoxpetshop/) | pet shop (Maringá-PR) | 5.808 | 1,6% | humor/trend |
| [@petshopdogvida](https://www.instagram.com/petshopdogvida/) | pet shop (Cacoal-RO) | 1.906 | 1,5% | produto em destaque |

Lista completa em `data/b_perfis_destaque.csv`. Por segmento, ER mediano: pet 0,86% (4 perfis), alimentação 0,42% (8), beleza 0,34% (5), moda/varejo 0,24% (8). Com tão poucos perfis por segmento, a diferença é descritiva, não conclusiva.

## Estudos de caso da base antiga (qualitativos, fora da estatística)

- **Raissa Cardozo | Baker (YouTube, padaria na casa dos pais, 10,7 mil inscritos).** ER mediano de 1,1% em 190 Shorts. Os maiores são dias de produção sem roteiro: "Mais um dia de produção por aqui" teve 10.794 curtidas e 173 mil views ([link](https://www.youtube.com/shorts/64WoGLjmyx8)); a focaccia de 24 horas de fermentação, 5.771 curtidas e 240 mil views ([link](https://www.youtube.com/shorts/-Ll6_aYRv0E)). Mesmo padrão 4 daqui: mostrar o fazer.
- **Assistência Litimcell (YouTube, assistência técnica, 158 mil inscritos).** ER mediano de 2,2%, views medianas de 90 mil. O que explode são histórias de balcão: "Cliente achou a TV na rua e quis me vender" teve 116.852 curtidas e 3,15 milhões de views ([link](https://www.youtube.com/shorts/aBAMoP4rVwI)). O conserto vira história com começo, meio e fim.
- **Loja Casa Criativa (YouTube, tecidos e costura, 131 mil inscritos).** Contraexemplo: tutoriais bem feitos, mas ER mediano de 0,02% e cerca de 100 curtidas nos melhores ([exemplo](https://www.youtube.com/shorts/uvNqqfA9Mww)). Canal grande com conteúdo só instrutivo não garante resposta do público.
- **Paulo Oliveira Pintor (Instagram, 217 mil seguidores; YouTube, 65 mil).** ER mediano de 0,08% no Instagram, mas Reels de aplicação com 55 a 114 mil views; "Borracha líquida (cor telha)", com oferta de Black Friday, teve 890 curtidas e 114 mil views ([link](https://www.instagram.com/p/Dfb8xsfhKQO/)). Serviço que se explica mostrando o resultado na parede.

## 5 recomendações para o lojista

1. **Divida seus posts em dois tipos e não cobre de um o que é trabalho do outro.** Post para aparecer (humor da rotina, bastidor) traz gente nova e curtida. Post para vender (produto com preço) traz pergunta e pedido. Faça os dois toda semana.
2. **Quando o post é para vender, coloque o preço.** Na imagem ou na legenda. Nos posts com preço, 6 em cada 10 comentários eram de gente querendo comprar; sem preço, menos de 1 em 10. "Chama no direct para saber o valor" espanta cliente.
3. **Filme a mão na massa.** O doce sendo enrolado, o pão sendo montado, o tecido sendo cortado, o cabelo sendo finalizado. Celular na bancada, sem produção. Foi daí que saíram os maiores posts da base.
4. **Brinque com a sua rotina.** O cliente que atrasa, a meta do mês, o dia normal no pet shop. Uma frase na tela e o seu balcão de cenário. Foi o formato que mais se destacou, em 8 negócios diferentes.
5. **Escreva uma frase na tela logo no começo** dizendo o que a pessoa vai ver ("O corte ideal para rosto redondo", "Quero mimar meu pet, mas só tenho 20 reais"). Se você tem salão ou barbearia, mostre a cliente com o resultado (com autorização dela).

## Limitações

- **Amostra pequena e de conveniência.** 28 perfis vindos de hashtags (quem usa hashtag e já posta bastante); 25 entraram na régua. Só 1 perfil grande: o estrato "grande" tem 3 posts no top e 3 no controle. Um perfil (ateliê de crochê) e duas lojas de moda saíram por curtidas ocultas ou posts recentes demais; 165 posts (16%) têm curtidas ocultas.
- **Janela curta para quem posta muito.** Pedimos 12 meses, mas 38 posts cobrem só 2 a 6 semanas em vários perfis. A coleta foi em 24/11: Black Friday e fim de ano pesam.
- **A rubrica do lift foi feita sem ver o vídeo.** A cota gratuita do Gemini (20 chamadas por dia por modelo) cobriu só 24 posts, todos do top. Para não comparar top visto em vídeo com controle visto em foto, o lift usa um método único (DeepSeek: imagens + legenda) nos 124 posts. Nos 24 posts com os dois métodos, a concordância foi boa em formato (kappa 0,63), cliente aparece (0,88), preço (1,00) e processo (0,67), e fraca em texto na tela (0,22) e tipo de gancho (0,32). Som, fala e ritmo não entram.
- **Intenção de compra é uma amostra.** Até 12 comentários por post (os que a Apify devolve), 87 posts com comentário de cliente no top e controle. O cruzamento com preço tem 10 posts. Regex e LLM concordam em 89% (kappa 0,59). Comentário não é venda.
- **Correlação.** Lift não prova causa; o modelo misto explica 32% da variância pelo perfil (ICC), e um post viral pode ter razões que a rubrica não vê (áudio em alta, impulsionamento pago, que não conseguimos identificar).
- **Sem validação humana da rubrica B** (o Foco A tem; aqui não deu tempo).
