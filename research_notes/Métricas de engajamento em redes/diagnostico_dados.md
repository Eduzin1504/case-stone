# Diagnóstico da fórmula de engajamento nos dados do case (gerado em 23/11/2026, a partir de data/stone.db)

Fonte: tabela `ranking` (11.676 posts com curtidas públicas), `categorias` (rubrica do VLM, campo relevante_mpe), `data/auditoria_canais_fora.csv` (13 canais fora do perfil, julgamento manual).

## 1. Viés de tamanho: correlação de Spearman entre a métrica e o nº de seguidores
- instagram: rho(ER, seguidores) = -0.49; rho(ER_views, seguidores) = -0.42; rho(outlier, seguidores) = -0.01; n=655
- youtube: rho(ER, seguidores) = -0.28; rho(ER_views, seguidores) = 0.22; rho(outlier, seguidores) = -0.03; n=11021

## 2. ER acima de 100% (curtidas+comentários > seguidores)
- instagram: 0.5% da base e 4.5% do top têm ER > 100%
- youtube: 0.5% da base e 4.5% do top têm ER > 100%

## 3. Views disponíveis por plataforma
- instagram: 67% dos posts têm views>0 (tipos: {'clips': 436})
- youtube: 100% dos posts têm views>0 (tipos: {})

## 4. Top 10% por métrica, dentro de cada plataforma × faixa
| plataforma | faixa | métrica | n top | % top em canais fora (manual) | % irrelevante VLM (n categorizados) | maior criador no top | sobreposição com top por ER |
|---|---|---|---|---|---|---|---|
| instagram | grande | er | 15 | 13% | 0% (14) | Alex do Pano |  O Rei  33% | 100% |
| instagram | grande | er_views | 14 | 0% | 0% (7) | João Paulo 50% | 43% |
| instagram | grande | outlier | 15 | 13% | 0% (12) | Rodrigo Almeida | Caix 33% | 73% |
| instagram | medio | er | 36 | 0% | 22% (36) | Poliana Lira | Contabi 44% | 100% |
| instagram | medio | er_views | 21 | 0% | 12% (8) | Walter Rodrigues 29% | 33% |
| instagram | medio | outlier | 36 | 0% | 18% (22) | Guilherme Pessoa | Ven 22% | 58% |
| instagram | micro | er | 16 | 0% | 44% (16) | Indiânara Cörrêa 62% | 100% |
| instagram | micro | er_views | 10 | 0% | 0% (2) | Ruth Almeida 40% | 10% |
| instagram | micro | outlier | 15 | 0% | 11% (9) | Vitor Melo | Especiali 33% | 47% |
| youtube | grande | er | 277 | 84% | 36% (45) | Assistência Litimcell 56% | 100% |
| youtube | grande | er_views | 277 | 60% | 0% (2) | Graxinha 58% | 23% |
| youtube | grande | outlier | 277 | 25% | 33% (48) | Canal do Consultor 24% | 35% |
| youtube | medio | er | 341 | 40% | 30% (61) | Raissa Cardozo l Baker 37% | 100% |
| youtube | medio | er_views | 341 | 6% | 7% (14) | Raissa Cardozo l Baker 22% | 31% |
| youtube | medio | outlier | 342 | 11% | 30% (61) | Aceleraí 15% | 43% |
| youtube | micro | er | 485 | 44% | 36% (175) | Gabriel Rossini 15% | 100% |
| youtube | micro | er_views | 484 | 10% | 7% (27) | Jouberto Delana 15% | 15% |
| youtube | micro | outlier | 453 | 22% | 34% (76) | Rodrigo - Santo Negóci 18% | 30% |

## 5. Concentração: quantos criadores somam metade do top (ER)
- instagram/grande: 2 criador(es) somam 50% do top; 5 criadores no top
- instagram/medio: 2 criador(es) somam 50% do top; 7 criadores no top
- instagram/micro: 1 criador(es) somam 50% do top; 4 criadores no top
- youtube/grande: 1 criador(es) somam 50% do top; 7 criadores no top
- youtube/medio: 2 criador(es) somam 50% do top; 18 criadores no top
- youtube/micro: 4 criador(es) somam 50% do top; 25 criadores no top

## 6. Top por ER com limite de 3 posts por criador
- instagram/grande: 15 → 13 posts, 5 criadores; posts de canais fora caem de 13% para 15%
- instagram/medio: 36 → 16 posts, 7 criadores; posts de canais fora caem de 0% para 0%
- instagram/micro: 16 → 9 posts, 4 criadores; posts de canais fora caem de 0% para 0%
- youtube/grande: 277 → 19 posts, 7 criadores; posts de canais fora caem de 84% para 47%
- youtube/medio: 341 → 45 posts, 18 criadores; posts de canais fora caem de 40% para 20%
- youtube/micro: 485 → 64 posts, 25 criadores; posts de canais fora caem de 44% para 28%

Notas de verificação:
- Seção 2: os percentuais coincidem por acaso, mas as contagens diferem. Instagram: 3 de 655 posts na base e 3 de 67 no top. YouTube: 50 de 11.021 na base e 50 de 1.103 no top. Todo post com ER > 100% está no top.
- Coluna "% irrelevante VLM" para er_views: quase nenhum post desse top foi categorizado (2 a 27 por grupo), porque a categorização foi feita sobre o top por ER. Por isso a comparação de relevância entre métricas vale de verdade só para ER e outlier.
- O "outlier" (ER do post ÷ mediana do perfil) é a única métrica sem correlação com o tamanho (rho perto de 0) e a que mais reduz a concentração. Ela não remove canais fora do perfil por si só (25% no YouTube grande).
