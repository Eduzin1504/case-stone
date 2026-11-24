# Literatura acadêmica: medição e normalização de engajamento em redes sociais, e vieses do engagement rate por seguidor

Convenção: **[verificado]** = li no texto primário ou numa página do publisher/autores nesta sessão. **[secundário]** = vem de comunicado de imprensa, resumo ou relato de terceiros. **[não verificado]** = memória do pesquisador ou snippet de busca, precisa ser conferido antes de citar como fato.

## (a) Como os papers definem "engagement" e "engagement rate"

### Takeaway
Não existe definição canônica. Os papers de marketing tratam engajamento como contagens absolutas de interações (likes, comentários), às vezes por post e às vezes por campanha. Na literatura de previsão de popularidade (CS/multimídia), o alvo costuma ser um contador de exposição/atenção (views) com transformação log e normalização por tempo, não por seguidores. O ER "(likes+comentários)/seguidores" é sobretudo uma convenção da indústria. Os papers acadêmicos mais citados usam pouco esse ER como variável dependente principal.

### Cited Findings
- **Khosla, Das Sarma & Hamid (WWW 2014), "What makes an image popular?"** Popularidade = **log das views dividido pelo tempo desde o upload** (views/dias, depois log). Os autores dizem que a distribuição resultante "resembles a Gaussian". Dados: ~2,3M imagens do Flickr. Seguidores não aparecem no denominador: entram como *feature* ("contacts"). [verificado] — [PDF](https://people.csail.mit.edu/khosla/papers/www2014_khosla.pdf); DOI 10.1145/2566486.2567996
- **SMP Challenge / SMPD (ACM Multimedia, Wu et al.).** Popularidade = "viewing count" normalizado com função log (cita Wu et al. 2016), porque as views vão "from zero to millions". Benchmark: ~486K posts de 69K usuários do Flickr, com timestamps cobrindo ~500 dias. Métricas oficiais: **MAE** e **SRC (Spearman)**. [verificado na overview 2024] — [arXiv 2405.10497](https://arxiv.org/html/2405.10497v1); [overview 2019, arXiv 1910.01795](https://arxiv.org/abs/1910.01795)
  - A fórmula exata do SMPD, que seria `score = log2(views/dias + 1)` (Wu et al. 2016), **não foi confirmada** nas páginas lidas. [não verificado]
  - Edição 2025 (track de vídeo): avaliação por **MAPE**. A solução vencedora usa log-transform e remoção de outliers. [secundário] — [arXiv 2507.00950](https://arxiv.org/html/2507.00950v1)
- **Wies, Bleier & Edeling (J. Marketing 2023, 87(3):383–405), "Finding Goldilocks Influencers".** Engajamento = interações dos seguidores (likes, comentários) com conteúdo patrocinado no Instagram, usando métricas "publicly visible and privately accessible" (inclui dados internos de campanha). A página da AMA não detalha a construção exata da DV. [secundário] — [AMA](https://www.ama.org/2022/10/11/finding-goldilocks-influencers-why-high-follower-count-may-not-be-the-best-driver-of-engagement-on-social-media/)
- **Hughes, Swaminathan & Brooks (J. Marketing 2019, 83(5):78–96).** Engajamento = comentários (no blog) e likes (no Facebook) em posts patrocinados. Dados: 57 campanhas (2012–2016), ~600 blogs, ~1.800 posts, via a agência The Motherhood, mais um experimento. Contexto citado: ER médio por post de influencer de 0,37% no Facebook e 0,05% no Twitter. [secundário] — [AMA](https://www.ama.org/2019/08/07/how-to-drive-better-engagement-from-sponsored-blogging/); DOI 10.1177/0022242919854374
- **Kim, Jiang, Nakada, Han & Wang (WWW 2020), "Multimodal Post Attentive Profiling for Influencer Marketing".** É um paper de **classificação de tópico de influenciadores**, não de engajamento. O dataset tem 33.935 influenciadores e 10.180.500 posts do Instagram, e o texto não define nem modela engagement rate. Não serve como fonte para definição de ER. Os mesmos autores têm outros trabalhos com previsão de engajamento, não verificados aqui. [verificado] — [PDF](https://jyunyu.csie.org/docs/pubs/www2020influencer_paper.pdf)
- **Hessel, Lee & Mimno (WWW 2017), "Cats and Captions vs. Creators and the Clock".** Alvo = upvotes no Reddit, tratado como **popularidade relativa**: comparam pares de posts da mesma comunidade enviados com até ~30 s de diferença. Isso neutraliza timing, comunidade e, em parte, o efeito do autor. [verificado] — [arXiv 1703.01725](https://arxiv.org/abs/1703.01725)

### Inferences
- Na tradição de CS, o padrão é "log(contagem de exposição/tempo)". Seguidores e audiência entram como covariável, não como denominador. O ER por seguidor é uma construção de marketing/indústria com pouca validação psicométrica.
- Para um sistema de ranking interno, isso sustenta usar o log da métrica como alvo, com seguidores/criador como controle e não como divisor.

### Gaps
- Não confirmei a fórmula exata do SMPD (Wu et al. 2016, AAAI/IJCAI?) nem a construção precisa da DV em Wies et al. Seria preciso ler o PDF completo (repositório KU Leuven: https://lirias.kuleuven.be/retrieve/722043).
- Não achei, nesta sessão, um paper revisado por pares que proponha e valide formalmente um "engagement rate" padronizado.

## (b) Problemas documentados com ER = (likes + comentários) ÷ seguidores

### Takeaway
Há quatro problemas bem documentados. (1) Engajamento e alcance não escalam linearmente com seguidores: o engajamento absoluto segue um U invertido (Wies et al.), e o ER por seguidor cai com o tamanho da conta (dados de indústria). (2) As contagens são heavy-tailed e exigem log. (3) Em plataformas algorítmicas, a maior parte das views vem de não-seguidores, então o denominador está errado. (4) O numerador e o denominador são manipuláveis (pods, seguidores falsos).

### Cited Findings
**1. Relação não linear entre seguidores e engajamento**
- Wies et al. (2023): **U invertido** entre número de seguidores e engajamento. Mais seguidores ampliam o alcance, mas sinalizam laço mais fraco (tie strength) e reduzem a probabilidade individual de engajar. Dados: **802 campanhas de Instagram, >1.700 influenciadores**, mais eye-tracking e experimentos de laboratório. Moderadores: a customização do conteúdo enfraquece o U invertido, e marcas pouco conhecidas atenuam o efeito do tamanho. A página da AMA não publica o ponto de virada em seguidores nem o tamanho de efeito. [secundário] — [AMA](https://www.ama.org/2022/10/11/finding-goldilocks-influencers-why-high-follower-count-may-not-be-the-best-driver-of-engagement-on-social-media/); [Goethe-Uni Frankfurt](https://www.wiwi.uni-frankfurt.de/en/research/research-news/details/article/mega-nano-the-answer-lies-somewhere-in-between.html)
- Dados de indústria, não revisados por pares, com interesse comercial: Markerly reporta like-rate de ~8% para contas com <1K seguidores, ~4% para 1K–10K e ~1,66% para 1M–10M. Later x Fohr (>3,5M posts) diz que o ER "steadily declines" conforme os seguidores crescem. [secundário] — [Digiday](https://digiday.com/marketing/micro-influencers/?noamp=mobile); [Later](https://later.com/blog/influencer-engagement-rate/)
- De Veirman, Cauberghe & Hudders (Int. J. Advertising 2017) **não mede ER**. É um experimento com perfis fictícios iguais e contagens de seguidores diferentes: mais seguidores aumentam a popularidade/likeability percebida e, por consequência, a liderança de opinião percebida. A divergência do produto modera o efeito [secundário]. O detalhe de que contas com muitos seguidores mas que seguem poucos perfis perdem likeability é **[não verificado]**, vem da memória do pesquisador. — [core.ac.uk PDF](https://core.ac.uk/download/55691871.pdf); [Uni Bremen blog](https://blogs.uni-bremen.de/inform/?p=122)

**2. Distribuições heavy-tailed**
- Khosla et al.: as views vão de zero a milhões. É preciso log e normalização temporal para obter uma distribuição aproximadamente gaussiana. [verificado] — [PDF](https://people.csail.mit.edu/khosla/papers/www2014_khosla.pdf)
- SMPD aplica log pelo mesmo motivo ("from zero to millions"). [verificado] — [arXiv 2405.10497](https://arxiv.org/html/2405.10497v1)

**3. O efeito do criador domina, e seguidores explicam pouco dentro do criador**
- Khosla et al. (Tabela 2): a feature "Mean Views" do usuário prevê a popularidade de uma imagem nova com ρ=0,75 (one-per-user, ~930K imagens/400K usuários). "Contacts" tem ρ=0,46 e 0,26 nos settings one-per-user e user-mix. No setting **user-specific** (100 usuários, modelo por usuário), as features sociais combinadas caem para **ρ=0,21**, e o conteúdo visual passa a pesar mais (+0,08 de ganho com fusão). O melhor resultado geral é ρ=0,81. [verificado] — [PDF](https://people.csail.mit.edu/khosla/papers/www2014_khosla.pdf)
- Hessel et al. (2017): com timing e comunidade controlados via pares, as features de conteúdo (visual + texto) "usually" superam as de identidade do autor. [verificado] — [arXiv 1703.01725](https://arxiv.org/abs/1703.01725)

**4. Alcance viral vindo de não-seguidores (feeds algorítmicos)**
- TikTok, estudo com data donation: só **10,3%** das views vieram de contas que o usuário já seguia, com mediana de ~10% estável ao longo do tempo. [secundário, via snippet] — [arXiv 2301.04945](https://arxiv.org/pdf/2301.04945)
- #TulsaFlop (TikTok, 2020): play count × likes, ρ=0,86. Play count × seguidores do autor, só **ρ=0,48**. [secundário, via snippet] — [arXiv 2012.07716](https://arxiv.org/pdf/2012.07716)
- Auditoria de conteúdo político no TikTok (arXiv 2026): usa plays normalizados por seguidor como proxy de alcance e reconhece que isso confunde distribuição algorítmica com comportamento da audiência. [secundário, via snippet] — [arXiv 2607.17356](https://arxiv.org/pdf/2607.17356)

**5. Manipulação: pods e engajamento falso**
- Weerasinghe, Flanigan, Stein, McCoy & Greenstadt (WWW 2020), "The Pod People": **111.455 contas** do Instagram anunciadas em **>400 pods** (sobretudo no Telegram). Os pods têm em média ~900 membros, e alguns chegam a 17K (o TechCrunch diz >10K, divergência). Construíram um classificador de posts com engajamento de pod. A participação em pod se associa a mais interação orgânica posterior, mas sem prova causal. Como é engajamento humano e manual, é difícil de detectar. [secundário] — [NYU](https://engineering.nyu.edu/news/researchers-use-machine-learning-unearth-underground-instagram-pods); [PDF](https://dev.engineering.nyu.edu/sites/default/files/2020-04/PodPeople.pdf); [Drexel](https://researchdiscovery.drexel.edu/esploro/outputs/journalArticle/The-Pod-People-Understanding-Manipulation-of/991021876911704721)

### Inferences
- **Inferência importante (não verificada no PDF):** se o engajamento *absoluto* segue um U invertido em seguidores (Wies et al.), então o engajamento *por seguidor* cai monotonicamente em boa parte da faixa. Rankear posts por ER favorece de forma sistemática contas pequenas, sem que o conteúdo seja melhor.
- Para Reels/Shorts/TikTok, dividir por seguidores mistura duas coisas: a qualidade do post e a decisão do algoritmo de distribuí-lo para não-seguidores. Um post viral de conta pequena pode ter ER >100%.
- Seguidores falsos inflam o denominador e derrubam o ER. Pods inflam o numerador, sobretudo comentários. Os dois enviesam o ER em direções opostas.
- Contas pequenas também têm ER com alta variância (poucos eventos), o que sugere shrinkage. Isso é inferência estatística, sem fonte específica nesta sessão.

### Gaps
- Não obtive coeficientes, ponto de virada nem tamanho de efeito de Wies et al. O PDF de acesso aberto pode estar em https://lirias.kuleuven.be/retrieve/722043.
- Não encontrei, nesta sessão, um paper acadêmico com uma regressão direta ER ~ log(seguidores) num corpus grande. A evidência de declínio monotônico do ER vem de dados de vendors.
- Não pesquisei literatura acadêmica específica sobre a prevalência de seguidores falsos (ex.: estudos de detecção de bots no Instagram).

## (c) Normalizações alternativas e abordagens de avaliação

### Takeaway
Os pesquisadores usam: (1) log-transform da contagem; (2) normalização por tempo de exposição (views/dia); (3) seguidores/criador como covariável em vez de divisor; (4) comparação dentro do criador ou dentro de pares (popularidade relativa, modelos user-specific); (5) métricas de avaliação baseadas em rank (Spearman), além de MAE/MAPE no log. Para pesos diferentes por tipo de interação (likes vs comentários vs shares), a literatura indica que são comportamentos distintos, mas não achei um esquema de pesos validado.

### Cited Findings
- **Log + tempo:** Khosla et al. usam log(views/dias desde o upload). [verificado] — [PDF](https://people.csail.mit.edu/khosla/papers/www2014_khosla.pdf)
- **Avaliação estratificada por usuário:** Khosla et al. avaliam em três settings (one-per-user, user-mix, user-specific). O peso relativo das features sociais e de conteúdo muda drasticamente entre eles (sociais combinadas: ρ=0,77, 0,66 e 0,21). Uma lição metodológica é que a performance "entre criadores" é dominada pelo tamanho da audiência, enquanto a performance "dentro do criador" mede o conteúdo. [verificado] — [PDF](https://people.csail.mit.edu/khosla/papers/www2014_khosla.pdf)
- **Popularidade relativa via pareamento:** Hessel et al. comparam pares de posts da mesma comunidade com ~30 s de diferença e tratam a tarefa como classificação pareada. [verificado] — [arXiv 1703.01725](https://arxiv.org/abs/1703.01725)
- **Métricas de rank:** SMP usa Spearman (SRC) e MAE sobre o score em log. A edição 2025 usa MAPE. [verificado] — [arXiv 2405.10497](https://arxiv.org/html/2405.10497v1); [arXiv 2507.00950](https://arxiv.org/html/2507.00950v1)
- **Tipos de interação como sinais diferentes:**
  - Kim & Yang (Public Relations Review 2017, 43(2):441–449), "Like, comment, and share on Facebook: How each behavior differs from the other". Like, comentário e share têm antecedentes diferentes. [citação verificada; achados detalhados não verificados] — DOI 10.1016/j.pubrev.2017.02.006
  - Pela memória do pesquisador, o like estaria ligado a apelo sensorial/visual, o comentário a apelo racional/interativo e o share a ambos mais conteúdo informativo. **[não verificado]**: o site retornou bloqueio.
  - Yang, Ren & Adomavicius (ISR 2019): liking e commenting em páginas de marca do Facebook têm antecedentes diferentes. [secundário] — [PDF Carlson/UMN](https://carlsonschool-d8.prd.umn.edu/sites/carlsonschool.umn.edu/files/2021-04/ISR%202019%20Customer%20Engagement%20on%20Facebook%20Business%20Pages.pdf)
  - Hughes et al. (2019) tratam comentários (blog) e likes (Facebook) como DVs separadas, e os efeitos se invertem por plataforma: incentivos aumentam o engajamento no blog e reduzem no Facebook, e a expertise não funciona no Facebook. [secundário] — [AMA](https://www.ama.org/2019/08/07/how-to-drive-better-engagement-from-sponsored-blogging/)
- **Sinais de vídeo curto:** no TikTok, o tempo de visualização pesa mais no algoritmo de recomendação do que o like. Seguir criadores também molda fortemente o For You feed. [secundário, via snippet] — [arXiv 2201.12271](https://arxiv.org/pdf/2201.12271)

### Inferences
- Recomendação prática derivada (não testada como pacote na literatura):
  - Alvo = `log1p(interações)` ou `log1p(views)`.
  - Comparar cada post com o histórico do próprio criador (z-score ou resíduo dentro do criador, como no setting user-specific de Khosla).
  - Quando houver dados de alcance/impressões, preferir `interações/alcance` a `interações/seguidores`.
  - Avaliar por Spearman dentro de estratos (faixa de seguidores, formato Reel vs carrossel).
  - Para contas com poucos posts, aplicar shrinkage do tipo empirical Bayes (beta-binomial) em direção à média do estrato.
- Os pesos de comentário vs like podem ser justificados qualitativamente (antecedentes diferentes), mas qualquer peso numérico seria arbitrário sem calibração com um outcome de negócio.

### Gaps
- Não encontrei nesta sessão papers que apliquem explicitamente **empirical Bayes/shrinkage** a ER de influenciadores, nem percentis dentro de estratos. Isso é técnica estatística padrão (ex.: Efron; estimação beta-binomial de CTR), mas não tenho citação primária coletada.
- O "engagement ladder" e a literatura sobre "low-effort vs high-effort engagement" não foram verificados.
- Não há estudo acadêmico verificado específico de **Instagram Reels/YouTube Shorts** sobre o papel dos seguidores. A evidência de vídeo curto aqui é toda do TikTok e vem de snippets de arXiv (2301.04945, 2012.07716, 2607.17356), sem leitura do texto completo.
- Não verifiquei o estudo de Rhee et al. sobre micro vs macro influenciadores, nem outros trabalhos de JMR e J. Advertising sobre o tema.
