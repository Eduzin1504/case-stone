# Statistical Methods for Fair Ranking of Social Media Post Performance (varying exposure, heavy tails)

Context: alternatives to ER = (likes + comments) / followers for ranking Instagram posts and YouTube Shorts from small-business creators. Notation used throughout: for post i by creator c, L = likes, C = comments, S = shares/saves, V = views/plays (reach if available), F = followers at posting time, a = post age in days.

## 1. Relative / within-creator performance (outlier score, within-creator z-scores, regression residuals)

### Takeaway
Industry "outlier scores" divide a post's views by the creator's typical views. 1of10 uses the median and vidIQ says it uses the average. The statistically cleaner versions are (a) a ratio to the creator's median at matched age, (b) a z-score of log engagement within the creator, and (c) a residual from log(engagement) ~ log(followers) + age + format, ideally with a creator random intercept. All three rank posts by how far they beat expectation, not by raw size.

### Cited Findings
- 1of10 defines its outlier score relative to the **channel median**: "A score of 7.1x means that video got 7.1 times more views than the channel typically gets." — [1of10 Chrome extension](https://1of10.com/chrome-extension)
- vidIQ says its score compares "a video's performance relative to the **average** performance of other videos on the same channel... within a similar timeframe." Example: a 10,000-view video on a channel that typically gets 1,000 views is 10x. Its colour bands are <2x, 2–5x, 5–10x and >10x. The help page gives no window length and no minimum-video rule. — [vidIQ Help: Outliers](https://intercom.help/vidiq/en/articles/9660010-outliers)
- Third-party write-ups recommend the median because one viral hit inflates the mean, and they note there is "no single universal definition" of an outlier score. Tools differ on which videos enter the baseline, mean vs median, and how many prior uploads are used. — [OverseerOS: outlier tools](https://www.overseeros.com/blog/best-youtube-outlier-tools); [BigIdeasDB](https://bigideasdb.com/how-to-find-outlier-videos-on-youtube)
- One tool (Vamos) shows an outlier score only after a creator has at least 10 posts. This is that tool's rule, not vidIQ's or 1of10's. — [Vamos: Outlier score](https://intercom.help/getvamos/en/articles/16934858-the-outlier-score)
- Szabo & Huberman model popularity on the log scale as ln N(t2) = ln r(t1,t2) + ln N(t1) + ξ, with additive noise ξ (mean 0). The residual mean and variance were independent of popularity (checked in 50 bins). This supports treating log-scale residuals as comparable across small and large items. — [Szabo & Huberman, arXiv 0811.0405](https://ar5iv.labs.arxiv.org/html/0811.0405)
- Social Media Prediction (SMP) challenge work uses each user's past posting sequence as prior knowledge for predicting the next post's popularity (Deep Temporal Context Networks). — [Wu et al., arXiv 1712.04443](https://arxiv.org/pdf/1712.04443)
- A 2024 SMP paper reports that implicit user factors (user influence similarity, user identity) measurably shift popularity distributions. The user effect is large, so it should be modeled or removed. — [arXiv 2410.09345](https://arxiv.org/html/2410.09345v1)
- A random intercept per grouping level separates "the within-speaker effect... from the between-speaker variation in baseline rate." The same logic applies with creators in place of speakers. lme4 fits random intercepts, including crossed (non-nested) factors such as creator × format. — [Trott, Mixed Effects lecture](https://seantrott.github.io/ucsd_css211/lectures/week7-mixed_models.html); [Bates et al., lme4, arXiv 1406.5823](https://arxiv.org/pdf/1406.5823)
- Follower count is not a neutral denominator. Engagement rate falls as followers grow: Markerly reports a like rate of about 8% under 1K followers vs 1.66% at 1–10M, and Buffer's 27M-post dataset shows a median of 5.2% at 0–1K vs 3.6% at 50–100K. A patent filing reports that a logarithmic regression fits this inverse relationship best. — [Marketing Dive/Markerly](https://www.marketingdive.com/news/brand-marketers-see-higher-engagement-with-micro-influencers-survey/418109/); [Buffer](https://buffer.com/resources/instagram-engagement-rate/); [USPTO 11615485](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11615485)

### Inferences
Candidate formulas. Each one is my synthesis built on the sources above.
- **Outlier score (median, age-matched):** `OS_i = (V_i(a*) + k) / (median_{j∈c, j≠i} V_j(a*) + k)`, where V(a*) is the metric at a fixed age a* (e.g., 7 days) and k is a small pseudo-count (e.g., 1–10) that keeps tiny accounts from dividing by ~0. Use the creator's previous N posts (e.g., 10–30) and exclude the post itself. Report log2(OS) so that 2x and 0.5x are symmetric. This suits ranking within a creator and works across creators because the ratio is unitless. Assumption: the creator's baseline is stationary over the window.
- **Within-creator robust z-score on the log scale:** `z_i = (log(1+E_i) − median_c log(1+E)) / (1.4826 · MAD_c log(1+E))`. It accounts for creators whose output is volatile (a 3x on a steady creator is rarer than a 3x on an erratic one). It is unstable when a creator has fewer than ~10 posts, so shrink MAD_c toward the pooled MAD in that case.
- **Expectation residual (cross-creator):** fit `log(1+E_i) = β0 + β1·log(F_c) + β2·g(a_i) + β3·format_i + u_c + ε_i`, with `u_c ~ N(0, σ_u²)` (lme4: `lmer(log1p(E) ~ log(F) + ns(age,3) + format + (1|creator))`). There are two scores:
  - `post_score_i = ε̂_i` (above or below that creator's own expected level). Use it to find "which posts worked".
  - `creator_score_c = û_c` (the BLUP, which is automatically shrunk toward 0 for creators with few posts). Use it to find "which creators over-perform for their size".
  - The fitted β1 is usually < 1, matching the ER-falls-with-followers finding above. Dividing by F implicitly assumes β1 = 1, which penalizes large accounts and rewards tiny ones. That is the core flaw of ER/followers.
- For count outcomes with many zeros (comments, shares on small accounts), a negative binomial GLMM with `offset(log(V))` or `log(F)` as a covariate is more defensible than a Gaussian model on log1p, e.g. `glmmTMB(C ~ log(F) + format + (1|creator) + offset(log(V)), family=nbinom2)`. (Inference; not verified against a specific source this session.)
- On YouTube Shorts and Instagram Reels, distribution is mostly non-follower (recommendation-driven), so **views are a better exposure denominator than followers** whenever they are available. Rate metrics then become L/V, C/V and S/V.

### Gaps
- No public, exact formula from 1of10 or vidIQ (window size, age adjustment, minimum posts). The two sources conflict on average vs median.
- No peer-reviewed paper was found that uses the term "popularity residual" for ranking posts. The SMP literature predicts log popularity using user features but does not publish residual-based rankings.
- No published log-log slope (β1) of engagement on followers for Instagram or YouTube Shorts was found. It needs to be estimated on the project's own data.

## 2. Empirical Bayes / Bayesian shrinkage for rates with small denominators

### Takeaway
Rates such as likes/views or comments/likes on small posts are noisy. Rank by a shrunk estimate (beta-binomial empirical Bayes posterior mean, Bayesian average) or by a conservative bound (Wilson lower bound) rather than the raw ratio. This prevents "3 likes out of 5 views = 60%" from topping the list.

### Cited Findings
- **Wilson score lower bound** (Evan Miller): `LB = [p̂ + z²/(2n) − z·sqrt( p̂(1−p̂)/n + z²/(4n²) )] / (1 + z²/n)`, where p̂ = pos/n and z = 1.96 for 95%. Miller rejects both "positive − negative" (it ignores proportion) and "positive/total" (it ignores sample size: 2/2 beats 100/101). The method is for binary outcomes. Miller also suggests dividing by page views or downloads for "top" lists, because non-raters carry information. — [Evan Miller, How Not To Sort By Average Rating](https://www.evanmiller.org/how-not-to-sort-by-average-rating.html)
- **Beta-binomial empirical Bayes** (David Robinson): the prior is X ~ Beta(α0, β0) and the per-unit estimate is `(H + α0) / (AB + α0 + β0)`. The prior is fit by maximum likelihood (`MASS::fitdistr`, dbeta) on units with enough data (AB ≥ 500 in the baseball example; method of moments is mentioned as an alternative). A beta-binomial MLE over all units (VGAM `dbetabinom.ab`) gives almost the same prior. Caveats: the prior is estimated from the same data, it works well with many units, and a single Beta assumes one population, so use a mixture or covariates (decade, team, pitcher) if the data are heterogeneous. — [Robinson, Understanding empirical Bayes estimation (source Rmd)](https://github.com/dgrtwo/dgrtwo.github.com/blob/master/_R/2015-10-01-empirical_bayes_baseball.Rmd); original post at http://varianceexplained.org/r/empirical_bayes_baseball/
- **Efron & Morris (1975), James-Stein:** `θ̂_i = ȳ + c·(y_i − ȳ)`, where c is the shrinking factor. For 18 players' averages after 45 at-bats, James-Stein gave a total squared error of 0.022 vs 0.077 for the raw averages, with about 80% shrinkage. Brown (2008) notes the formula assumes homoscedastic data, while real averages are heteroscedastic (different n), and proposes alternatives. — [Efron & Morris 1975, JASA (PDF)](https://www.medicine.mcgill.ca/epidemiology/hanley/bios602/MultilevelData/EfronMorrisJASA1975.pdf); [Brown 2008, arXiv 0803.3697](https://arxiv.org/pdf/0803.3697.pdf)
- **Bayesian average (IMDb historical Top 250):** `WR = (v/(v+m))·R + (m/(v+m))·C`, where v = number of votes, m = minimum-votes constant, R = the item's mean and C = the global mean. IMDb no longer discloses its current formula. — [Wikipedia: IMDb](https://en.wikipedia.org/wiki/IMDb); [IMDb Help: weighted average ratings](https://help.imdb.com/article/imdb/track-movies-tv/weighted-average-ratings/GWT2DSBYVT2F25SK)

### Inferences
How to apply these to posts (synthesis):
- **Like-through rate with shrinkage:** `LTR_i = (L_i + α0) / (V_i + α0 + β0)`. Fit (α0, β0) per platform × format (Reels vs carousel vs Shorts), and preferably per follower-size band, because baseline rates differ (see §1). The prior mean α0/(α0+β0) is the typical rate and α0+β0 acts as the pseudo-views. Posts with V ≪ α0+β0 get pulled to the typical rate.
- Use the same template for comments/views, shares/views, saves/reach, and **comments/likes** (conversation ratio, where the denominator is L).
- **Ranking with uncertainty:** rank by the posterior 10th percentile, `qbeta(0.10, L+α0, V−L+β0)`, the Bayesian analogue of the Wilson lower bound. This is conservative, which suits a "top posts" list where false positives are costly.
- Wilson LB has no prior, so it is simpler to implement in SQL. It needs no fitting but always penalizes small n, even when the rate is genuinely high. EB shrinks toward a realistic baseline instead of toward 0, which is better when most posts are small.
- If views are not available and followers must be used: L is not Binomial(F, p), since likes can come from non-followers and L can exceed F on viral Reels. The beta-binomial does not strictly apply there. Use the log-residual model from §1 instead.
- Shrinkage for the outlier ratio itself: compute log(OS) per post, then shrink each creator's log(OS) values toward 0 by `n_c/(n_c + k)`, as a James-Stein-style partial-pooling factor, when creators have few posts.
- **Implementation check** (any implementation should pass): a post with 2 likes / 2 views must rank below one with 900 likes / 1,000 views under both Wilson LB and EB.

### Gaps
- No published fitted Beta priors for Instagram or YouTube Shorts like/view rates were found. They must be fit on the project's data.
- No source was found that validates beta-binomial EB specifically on social media engagement. The method is transferred from ratings and sports.

## 3. Log transforms and percentile ranks for heavy-tailed popularity

### Takeaway
Popularity counts are roughly log-normal or heavy-tailed, so do all averaging, regression and z-scoring on log(1+x) and report percentiles or Spearman correlations. Raw-scale means and Pearson correlations are dominated by a few viral posts.

### Cited Findings
- Szabo & Huberman: on the log scale, early and later popularity correlate strongly. For YouTube, Pearson r is 0.92 at about day 5 vs day 30 on the log scale, but about 0.7 untransformed. For Digg it is 0.98 after hour 5. Residuals are near-Gaussian on the log scale, though formal tests reject normality (Jarque-Bera, Lilliefors). YouTube residuals are truncated from below and Digg residuals are slightly right-skewed. — [Szabo & Huberman](https://ar5iv.labs.arxiv.org/html/0811.0405)
- The paper measures error relatively, `QRE = ((N̂ − N)/N)²`, because absolute errors are meaningless across items of very different scale. — [Szabo & Huberman](https://ar5iv.labs.arxiv.org/html/0811.0405)
- The SMP Challenge normalizes popularity as `s = log2(r/d + 1)` (r = views, d = days since posting) "to suppress the large variations" (views range from 0 to millions), and evaluates with **Spearman rank correlation** and MAE. The dataset has 480K+ Flickr posts from 69K users. — [SMP Challenge 2019 overview, arXiv 1910.01795](https://arxiv.org/pdf/1910.01795)

### Inferences
- Default transform: `log1p(x)`, or log(x + k) with k ≈ the median count of a "dead" post, so that zeros do not dominate.
- Percentile within a peer group: `pct_i = rank(score_i within stratum) / n_stratum`, with strata such as platform × format × follower band (e.g., <1K, 1–10K, 10–100K) × month. This is robust to any monotone distortion and easy to explain to small-business users ("better than 85% of similar posts").
- Validate any new score by Spearman correlation with a downstream outcome (for example, the next post's performance, or profile visits), not by Pearson correlation.

### Gaps
- No source was found that fits the log-normal (vs power-law) shape specifically to Instagram likes or Shorts views for small accounts.

## 4. Age normalization (time since posting, stabilization, decay)

### Takeaway
Compare posts at a fixed age (e.g., value at day 7) or normalize by age. Raw counts favor older posts. How fast a metric stabilizes depends on the platform: news-like feeds saturate in about a day, while video keeps accruing for weeks.

### Cited Findings
- Digg stories saturate within about a day, and popularity changes little after about 2 days. About 10% prediction accuracy is reachable within about 2 hours. YouTube needs about 10 days for 10% accuracy because videos keep getting views. — [Szabo & Huberman](https://ar5iv.labs.arxiv.org/html/0811.0405)
- Constant-scaling model: `N̂(t_r) = α(t_i, t_r) · N(t_i)`, with `α = Σ[N_c(t_i)/N_c(t_r)] / Σ[N_c(t_i)/N_c(t_r)]²`, which is optimal for relative squared error. On a 7-day vs 30-day fit for YouTube, R = 0.77 with prefactor 2.13. — [Szabo & Huberman](https://ar5iv.labs.arxiv.org/html/0811.0405)
- SMP divides by days since posting inside the log, `log2(views/days + 1)`. This is a simple per-day rate, which implicitly assumes linear accrual. — [arXiv 1910.01795](https://arxiv.org/pdf/1910.01795)
- vidIQ compares against the channel's average "within a similar timeframe", which is an age-matching approach. — [vidIQ Help](https://intercom.help/vidiq/en/articles/9660010-outliers)

### Inferences
- Preferred approach: **fixed-age snapshot** (store each metric at, e.g., 48h and 7d), then compare posts only at the same age. If snapshots are not available, use the Szabo-Huberman scaling, `E_hat(7d) = E(a) · α(a→7d)`. Estimate α(a) empirically as the median ratio E(7d)/E(a) across posts with full history, per platform and format.
- Dividing by age (the SMP approach) over-rewards very young posts, since accrual is front-loaded. Use it only when every post is past the stabilization point.
- Exclude posts younger than a minimum age (e.g., 3 days for Instagram feed; longer for Shorts, which can resurface) from rankings, or flag them as provisional.

### Gaps
- No authoritative source was found for stabilization times specifically on Instagram (feed vs Reels) or YouTube Shorts. The Szabo-Huberman numbers are from 2008-era YouTube and Digg. Measure on the project's data.

## 5. Composite / weighted engagement indexes

### Takeaway
Weighted sums such as likes + 2·shares + 3·comments are widespread in industry and patents, but no validation study for the specific weights was found. Treat the weights as hypotheses. Prefer either separate shrunk rates or weights learned against an outcome.

### Cited Findings
- A patent filing normalizes likes, shares and comments and sums them with per-metric weights, without evidence that the weights are valid. — [USPTO 12387234](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12387234)
- Brandwatch/Unmetric lets users set the weights, with the rationale that shares are weighted higher because they "intentionally amplify audience reach". This is a design rationale, not an empirical test. — [Unmetric](https://unmetric.com/engagement)
- One arXiv case study uses reactions + 3×comments + 2×shares and finds comments contribute 83–93% of the score on top posts. This shows how a heavy weight on a high-variance component can dominate the ranking. — [arXiv 2610.31875](https://arxiv.org/pdf/2610.31875)

### Inferences
- With raw counts, the component with the largest variance × weight dominates the composite. Standardize each component first, `z_k = (log1p(x_k) − mean)/sd` within a stratum, then combine.
- Three defensible alternatives to arbitrary weights:
  1. **Inverse-frequency weights:** `w_k = 1 / median(x_k / V)`, so a comment "costs" what it is rare. This keeps the weights tied to the data rather than an opinion.
  2. **PCA first component** of the standardized log-rates (an unsupervised "general engagement" factor). Report the loadings.
  3. **Supervised weights:** regress a business outcome (profile visits, link clicks, follows, sales/DMs, or next-period follower growth) on the component rates. Use the coefficients as weights and check them on held-out creators.
- Report a weight-sensitivity check: the Spearman correlation between rankings under alternative weightings. If ρ > 0.9, the weights barely matter.

### Gaps
- No peer-reviewed validation of comment/share/like weights against business outcomes was found in this session.

## 6. Selection on the dependent variable, regression to the mean, and safeguards when comparing "top 10%" vs control

### Takeaway
Picking the top 10% by a noisy score guarantees that part of their apparent excellence is luck, so they will look worse on re-measurement (regression to the mean, "winner's curse"). Contrasting their features against a "bottom" or random group then confounds content traits with noise and with creator identity. Safeguards: shrinkage before selection, per-creator caps, within-creator stratified comparisons, held-out re-measurement, and mixed-effects models.

### Cited Findings
- Regression toward the mean: when the most extreme results are deliberately selected, later measurements of those units tend to be less extreme. Follow-up checks are warranted when an analysis selects extremes. — [Wikipedia: Regression toward the mean](https://en.wikipedia.org/wiki/Regression_toward_the_mean)
- van Zwet & Cator: focusing on "significant" or extreme results overestimates magnitude. The bias is especially severe at low signal-to-noise, and shrinkage is necessary to correct it. — [The Significance Filter, the Winner's Curse and the Need to Shrink, arXiv 2009.09440](https://arxiv.org/pdf/2009.09440)
- Winner's-curse corrections with empirical Bayes and local shrinkage are used for online A/B experiments (Meta). — [Breaking the Winner's Curse with Bayesian Hybrid Shrinkage, arXiv 2511.06318](https://arxiv.org/pdf/2511.06318)
- Efron & Morris show that shrunk estimates predict future performance better than raw ones (squared error 0.022 vs 0.077). This is direct evidence that raw extremes overstate true ability. — [Efron & Morris 1975](https://www.medicine.mcgill.ca/epidemiology/hanley/bios602/MultilevelData/EfronMorrisJASA1975.pdf)
- A random intercept per group separates within-group effects from between-group baseline differences. — [Trott, Mixed Effects](https://seantrott.github.io/ucsd_css211/lectures/week7-mixed_models.html)

### Inferences
Concrete safeguards (synthesis):
1. **Score before selecting:** rank on a shrunk score (EB rate or BLUP residual, §1–2), not the raw ratio. This alone removes most small-denominator "winners".
2. **Per-creator cap:** at most k posts (e.g., 2–3) per creator in the top set. Otherwise one large or prolific creator's style becomes the definition of a "top post".
3. **Within-creator matched control:** for each top post, compare it to the same creator's median-performing posts of the same format and period (top-decile vs middle-tercile, not vs bottom). This holds audience, niche and production constant, so differences are more plausibly about the content.
4. **Stratify** the top 10% by follower band and format, i.e. take the top 10% within each stratum.
5. **Out-of-sample check:** define "top" on metric A at day 2 and verify on metric B or at day 30. Or split by time, defining top creators on months 1–3 and checking months 4–6. Expect shrinkage, and report how much.
6. **Model, don't contrast:** estimate feature effects with `log1p(E) ~ features + log(F) + age + format + (1|creator)` on all posts, instead of a two-group comparison of extremes. Dichotomizing the outcome discards information and invites the selection bias above.
7. Avoid ceiling or floor artifacts: posts with near-zero engagement cannot fall further, and top posts cannot "regress up". Use the log scale and never select on a raw ratio with tiny denominators.

### Gaps
- No social-media-specific paper quantifying regression to the mean for "top posts" was found in this session. The evidence above is general statistics plus sports and A/B testing.
- The exact winner's-curse correction formulas in arXiv 2511.06318 were not extracted; only the search summary was seen.
