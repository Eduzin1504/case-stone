import sqlite3, json, warnings, numpy as np, pandas as pd
import statsmodels.formula.api as smf
warnings.filterwarnings("ignore")
c = sqlite3.connect("data/stone.db")
r = pd.read_sql("select video_id, plataforma, porte, canal, inscritos, likes, comentarios, idade_dias, duracao_s, tipo, er, outlier, top, titulo, descricao from ranking", c)
cat = pd.read_sql("select video_id, rubrica from categorias", c)
cat["rel"] = cat.rubrica.map(lambda s: json.loads(s).get("relevante_mpe"))
r = r.merge(cat[["video_id", "rel"]].drop_duplicates("video_id"), on="video_id", how="left")
fora = pd.read_csv("data/auditoria_canais_fora.csv").canal.tolist()
r["fora"] = r.canal.apply(lambda x: any(str(x).startswith(k) for k in fora))
r["y"] = np.log1p(r.likes + r.comentarios)
r["logF"] = np.log(r.inscritos.clip(lower=1))
r["logIdade"] = np.log1p(r.idade_dias)
r["formato"] = np.where(r.plataforma == "youtube", pd.cut(r.duracao_s.fillna(30), [-1, 15, 30, 60, 1e9], labels=["0-15s", "15-30s", "30-60s", ">60s"]).astype(str), r.tipo.fillna("x"))
n_por = r.groupby("canal").video_id.transform("size")
r = r[n_por >= 5].copy()  # criador com pelo menos 5 posts

out = []
for p, g in r.groupby("plataforma"):
    m = smf.mixedlm("y ~ logF + C(formato) + logIdade", g, groups=g["canal"]).fit(method="lbfgs")
    g = g.copy()
    g["resid"] = g.y - m.fittedvalues  # já desconta o efeito do criador
    efeitos = {k: v.iloc[0] for k, v in m.random_effects.items()}
    g["efeito_criador"] = g.canal.map(efeitos)
    print(f"\n### {p}: {len(g)} posts, {g.canal.nunique()} criadores, convergiu={m.converged}")
    print(f"b (elasticidade engajamento x seguidores) = {m.params['logF']:.2f}  (ER assume b = 1)")
    print(f"variância entre criadores = {m.cov_re.iloc[0,0]:.2f} | variância residual dos posts = {m.scale:.2f}")
    top_cri = sorted(efeitos.items(), key=lambda kv: -kv[1])[:8]
    print("criadores com maior efeito (encolhido):", "; ".join(f"{k[:28]} {v:+.2f}" for k, v in top_cri))
    out.append(g)
r = pd.concat(out)

def top(g, col, cap=None):
    t = g[g[col] >= g[col].quantile(0.9)].sort_values(col, ascending=False)
    return t.groupby("canal").head(cap) if cap else t

print("\n| plataforma | faixa | régua | n top | criadores | maior criador | % canais fora | % irrelevante VLM (n cat.) | sobrepõe com ER |")
print("|---|---|---|---|---|---|---|---|---|")
for (p, po), g in r.groupby(["plataforma", "porte"]):
    base = set(top(g, "er").video_id)
    for nome, col, cap in [("ER (atual)", "er", None), ("outlier", "outlier", None), ("modelo", "resid", None), ("modelo + máx 3/criador", "resid", 3)]:
        t = top(g, col, cap); vc = t.canal.value_counts(); nc = t.rel.notna().sum()
        print(f"| {p} | {po} | {nome} | {len(t)} | {t.canal.nunique()} | {str(vc.index[0])[:20]} {vc.iloc[0]/len(t):.0%} | {t.fora.mean():.0%} | {(t.rel==False).sum()/nc:.0%} ({nc}) | {len(set(t.video_id)&base)/len(t):.0%} |" if nc else
              f"| {p} | {po} | {nome} | {len(t)} | {t.canal.nunique()} | {str(vc.index[0])[:20]} {vc.iloc[0]/len(t):.0%} | {t.fora.mean():.0%} | - | {len(set(t.video_id)&base)/len(t):.0%} |")

print("\n### Exemplos: top 6 por modelo (máx 3/criador), por plataforma")
for p, g in r.groupby("plataforma"):
    t = g.sort_values("resid", ascending=False).groupby("canal").head(3).head(6)
    for x in t.itertuples():
        print(f"- {p} | {x.canal[:24]} ({x.porte}) | resid {x.resid:+.2f} (≈{np.expm1(x.resid)+1:.1f}× o esperado) | ER {x.er*100:.1f}% | {(x.titulo or x.descricao or '')[:70]!r}")
