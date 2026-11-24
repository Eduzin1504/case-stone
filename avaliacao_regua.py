"""Avaliação da régua de "alto desempenho": ER puro (R1) × outlier (R2) × modelo misto (R3) × régua adotada (R4).
Uso: .venv/bin/python avaliacao_regua.py   -> escreve data/avaliacao_regua.md e data/avaliacao_regua_estratos.csv
Só lê o stone.db (modo read-only); o ranking é montado em memória com pipeline.ranquear."""
import json, sqlite3, time, warnings, datetime as dt
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
import pipeline as P

RNG = np.random.default_rng(0)
F_FULL = "y ~ logF + logIdade + C(formato)"
ESTR = ["plataforma", "porte"]
out = []  # linhas do markdown


def ler():
    for i in range(6):  # outro processo regrava o banco em paralelo
        try:
            c = sqlite3.connect("file:data/stone.db?mode=ro", uri=True, timeout=30)
            r = [pd.read_sql(f"select * from {t}", c) for t in ("videos", "canais", "categorias")]
            c.close()
            return r
        except Exception as e:
            print("retry leitura:", e); time.sleep(3)
    raise SystemExit("não consegui ler o stone.db")


def prep(d):  # mesmas transformações de P.residuo_modelo
    return d.assign(y=np.log1p(d.likes + d.comentarios), logF=np.log(d.inscritos.clip(lower=1)),
                    logIdade=np.log1p(d.idade_dias.fillna(30)),
                    formato=np.where(d.plataforma == "youtube",
                                     pd.cut(d.duracao_s.fillna(30), [-1, 15, 30, 60, 1e9],
                                            labels=["0-15s", "15-30s", "30-60s", ">60s"]).astype(str),
                                     d.tipo.fillna("x")))


def ajusta(g, formula=F_FULL, metodos=("bfgs", "powell", "lbfgs")):
    """Modelo misto com intercepto aleatório por criador. Devolve o 1º ajuste não degenerado (llf finita, var. criador > 0)."""
    for mt in metodos:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            try:
                m = smf.mixedlm(formula, g, groups=g["channel_id"]).fit(method=mt)
            except Exception:
                continue
        if np.isfinite(m.llf) and m.cov_re.iloc[0, 0] > 1e-8:
            m.metodo, m.avisos = mt, sorted({str(x.message)[:60] for x in w})
            m.re = {k: v.iloc[0] for k, v in m.random_effects.items()}
            return m
    return None


def resid_misto(d, formula=F_FULL):
    r = pd.Series(np.nan, index=d.index)
    for _, g in d.groupby("plataforma"):
        m = ajusta(g, formula)
        if m is not None:
            r[g.index] = g.y - m.fittedvalues
    return r


def top_de(d, col, q=0.9, cap=None):
    """Top por estrato: score >= quantil q do estrato; depois, se cap, no máx. `cap` posts por criador."""
    d = d[d[col].notna()]
    cand = d[d[col] >= d.groupby(ESTR)[col].transform(lambda x: x.quantile(q))]
    if cap:
        cand = cand.sort_values(col, ascending=False).groupby("channel_id").head(cap)
    return set(cand.video_id)


def sp(a, b):
    return a.rank().corr(b.rank())


def sp_ic(a, b, B=2000):
    a, b = np.asarray(a, float), np.asarray(b, float)
    n = len(a)
    if n < 5:
        return np.nan, np.nan, np.nan
    rs = []
    for _ in range(B):
        i = RNG.integers(0, n, n)
        rs.append(pd.Series(a[i]).rank().corr(pd.Series(b[i]).rank()))
    return sp(pd.Series(a), pd.Series(b)), *np.nanpercentile(rs, [2.5, 97.5])


def jac(a, b):
    return len(a & b) / len(a | b) if a | b else np.nan


def wilson(k, n):
    if not n:
        return ""
    p, z = k / n, 1.96
    c, h = (p + z * z / (2 * n)) / (1 + z * z / n), z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return f"{c - h:.0%}–{c + h:.0%}"


def tab(rows, cols):
    out.append("| " + " | ".join(cols) + " |")
    out.append("|" + "---|" * len(cols))
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    out.append("")


def H(s):
    out.append(f"\n## {s}\n")


# ---------------------------------------------------------------- dados
v, canais, cat = ler()
exc = pd.read_csv("data/veredictos.csv")
excluidos = set(exc[exc.decisao == "excluir"].id)
julgados = set(exc.id)
fora_aud = pd.read_csv("data/auditoria_canais_fora.csv").canal.tolist()
cat = cat.drop_duplicates("video_id", keep="last")
rel_mpe = {a: json.loads(b).get("relevante_mpe") for a, b in zip(cat.video_id, cat.rubrica)}
foco_a = getattr(P, "elegivel_foco_a", lambda r: r.get("relevante_mpe"))  # filtro que o pipeline usa na base elegível
relevancia = {a: foco_a(json.loads(b)) for a, b in zip(cat.video_id, cat.rubrica)}
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    df = prep(P.ranquear(v, canais, excluidos, relevancia)).reset_index(drop=True)
df["rel"] = df.video_id.map(rel_mpe)
df["focoa"] = df.video_id.map(relevancia)
df["grupo_cat"] = df.video_id.map(dict(zip(cat.video_id, cat.grupo)))
df["exc"] = df.channel_id.isin(excluidos)
df["julgado"] = df.channel_id.isin(julgados)
df["fora"] = df.canal.apply(lambda x: any(str(x).startswith(k) for k in fora_aud))
df["n_posts"] = df.groupby("channel_id").video_id.transform("size")
el0 = df[df.n_posts >= 5]            # base "cega": só exige 5 posts por criador (sem exclusões nem rótulos)
el = df[df.elegivel]                  # base elegível da régua adotada
df["resid3"] = resid_misto(el0)       # R3: modelo misto convergido, base cega
df["resid4m"] = resid_misto(el)       # modelo misto convergido na base elegível
df["log_out"] = np.log(df.outlier.where(df.outlier > 0))
el0, el = df[df.n_posts >= 5], df[df.elegivel]

TOPS = {
    "R1 ER puro": set(df[df.top_er_puro].video_id),
    "R2 outlier": top_de(df, "outlier"),
    "R3 modelo misto": top_de(el0, "resid3"),
    "R1 + máx 3 (sem filtros)": top_de(el0, "er", cap=3),
    "R2 + máx 3 (sem filtros)": top_de(el0, "outlier", cap=3),
    "R3 + máx 3 (sem filtros)": top_de(el0, "resid3", cap=3),
    "R2 + máx 3 + elegível": top_de(el, "outlier", cap=3),
    "R4m modelo convergido + máx 3 + elegível": top_de(el, "resid4m", cap=3),
    "R4 adotada (pipeline)": set(df[df.top].video_id),
}
# autochecagem: minha função de top reproduz a do pipeline
# (empates no resíduo podem trocar posts do mesmo criador; por isso a tolerância)
_t = top_de(el, "resid", cap=P.MAX_POR_CRIADOR)
assert len(_t) == len(TOPS["R4 adotada (pipeline)"]) and jac(_t, TOPS["R4 adotada (pipeline)"]) > 0.95, "top_de diverge de P.ranquear"

out.append("# Avaliação da régua de alto desempenho (R1 ER puro × R2 outlier × R3 modelo misto × R4 adotada)\n")
out.append(f"Gerado por `avaliacao_regua.py` em {dt.datetime.now():%d/%m/%Y %H:%M}. Base: {len(df)} posts com curtidas públicas, "
           f"{df.channel_id.nunique()} criadores ({df.groupby('plataforma').size().to_dict()}); base elegível: {len(el)} posts, "
           f"{el.channel_id.nunique()} criadores; rótulos de relevância: {len(relevancia)} posts; canais excluídos: {len(excluidos)}.\n")
out.append("**Atualização de 24/11, depois deste relatório:** o problema do item 7 foi corrigido. `pipeline.residuo_modelo` agora tenta "
           "`bfgs`, depois `powell` e `lbfgs`, exige convergência e variância do criador maior que zero, e imprime o caminho usado. "
           "A tabela da seção 0 abaixo é recalculada a cada rodada e mostra que o pipeline usa o modelo misto nas duas plataformas "
           "(correlação 1,000 com o ajuste convergido). Três rodadas seguidas de `rank` deram o mesmo top: 47 posts no Instagram e "
           "203 no YouTube. O item 7 e o parágrafo de abertura da seção 0 descrevem o comportamento anterior à correção.")
out.append("")
out.append("O texto do resumo e do veredito foi escrito sobre a execução de 24/11/2026 (495 rótulos); as tabelas são recalculadas a cada rodada "
           "e podem variar na última casa enquanto a categorização avança.\n")
out.append("@@RESUMO@@")

# ---------------------------------------------------------------- 0. o que o pipeline realmente calcula
H("0. Checagem prévia: o que a R4 do pipeline calcula de fato")
out.append("`P.residuo_modelo` ajusta com `method=\"lbfgs\"` e, se der exceção, cai num plano B: resíduo = log-engajamento − mediana do criador "
           "(isto é, o log do outlier, sem seguidores, formato nem idade). Comparação do resíduo do pipeline com (i) um ajuste convergido "
           "do mesmo modelo (bfgs/powell) e (ii) o plano B:\n")
rows, FALLBACK = [], {}
for p, g in el.groupby("plataforma"):
    b = g.y - g.groupby("channel_id").y.transform("median")
    FALLBACK[p] = bool(np.allclose(g.resid, b))
    rows.append([p, len(g), g.channel_id.nunique(), int(g.efeito_criador.notna().sum()),
                 f"{g.resid.corr(g.resid4m):.3f}", f"{g.resid.corr(b):.3f}",
                 "PLANO B (modelo misto não foi usado)" if FALLBACK[p] else "modelo misto"])
tab(rows, ["plataforma", "n posts elegíveis", "criadores", "posts com efeito_criador", "r(pipeline, modelo convergido)",
           "r(pipeline, plano B)", "o que o pipeline usou"])

# ---------------------------------------------------------------- 1. viés de tamanho
H("1. Viés de tamanho")
out.append("Spearman entre o score do post e o nº de seguidores do criador (0 = sem viés). O nº de seguidores é um retrato único por criador, "
           "então o n efetivo é o nº de criadores, não o de posts.\n")
SC = [("ER (R1)", "er"), ("outlier (R2)", "outlier"), ("resíduo modelo misto (R3)", "resid3"),
      ("resíduo do pipeline (R4)", "resid"), ("resíduo modelo convergido, base elegível", "resid4m")]
rows = []
for p, g in df.groupby("plataforma"):
    for nome, col in SC:
        d = g[g[col].notna()]
        rows.append([p, nome, f"{sp(d[col], d.inscritos):+.2f}", len(d), d.channel_id.nunique()])
tab(rows, ["plataforma", "score", "rho com seguidores", "n posts", "n criadores"])
out.append("Participação de cada porte no top 10% se o corte fosse global dentro da plataforma (sem estratificar por porte), "
           "comparada à participação na base:\n")
rows = []
for p, g in df.groupby("plataforma"):
    for nome, col in SC[:3] + SC[4:]:
        d = g[g[col].notna()]
        t = d[d[col] >= d[col].quantile(0.9)]
        rows.append([p, nome, len(t)] + [f"{(t.porte == po).mean():.0%} (base {(d.porte == po).mean():.0%})" for po in ("micro", "medio", "grande")])
tab(rows, ["plataforma", "score", "n top", "micro", "médio", "grande"])

# ---------------------------------------------------------------- 2. concentração
H("2. Concentração do top (por régua × estrato)")
out.append("Célula: n posts no top · nº de criadores · fatia do maior criador · HHI (soma dos quadrados das fatias; 1 = um criador só; "
           "1/nº de criadores = distribuição uniforme). O limite por criador é aplicado depois do corte de 10%, então as réguas com "
           "\"máx 3\" ficam bem abaixo de 10% da base.\n")
estr_rows, piv = [], {}
for nome, ids in TOPS.items():
    t = df[df.video_id.isin(ids)]
    for (p, po), g in t.groupby(ESTR):
        s = g.channel_id.value_counts(normalize=True)
        nl = int(g.rel.notna().sum())
        estr_rows.append(dict(regua=nome, plataforma=p, porte=po, n_top=len(g), n_base_estrato=int(((df.plataforma == p) & (df.porte == po)).sum()),
                              criadores=len(s), fatia_maior=round(s.iloc[0], 3), hhi=round((s ** 2).sum(), 3), n_rotulados=nl,
                              pct_relevante=round((g.rel == True).sum() / nl, 3) if nl else np.nan,  # noqa: E712
                              pct_canal_excluido=round(g.exc.mean(), 3), pct_canal_fora_auditoria=round(g.fora.mean(), 3)))
        piv[(nome, f"{p[:2]}/{po}")] = f"{len(g)} · {len(s)} · {s.iloc[0]:.0%} · {(s ** 2).sum():.2f}"
E = pd.DataFrame(estr_rows)
E.to_csv("data/avaliacao_regua_estratos.csv", index=False)
cols = [f"{p[:2]}/{po}" for p in ("instagram", "youtube") for po in ("micro", "medio", "grande")]
tab([[nome] + [piv.get((nome, c), "-") for c in cols] for nome in TOPS], ["régua"] + cols)
rows = []
for nome in TOPS:
    e = E[E.regua == nome]
    for p, g in e.groupby("plataforma"):
        w = g.n_top / g.n_top.sum()
        rows.append([nome, p, int(g.n_top.sum()), f"{g.n_top.sum() / g.n_base_estrato.sum():.1%}", int(df[df.video_id.isin(TOPS[nome]) & (df.plataforma == p)].channel_id.nunique()),
                     f"{(g.fatia_maior * w).sum():.0%}", f"{(g.hhi * w).sum():.2f}"])
out.append("Resumo por plataforma (médias dos estratos ponderadas pelo n do top):\n")
tab(rows, ["régua", "plataforma", "n top", "% da base", "criadores distintos", "fatia do maior (média)", "HHI (média)"])

# ---------------------------------------------------------------- 3. relevância
H("3. Precisão de relevância com os rótulos disponíveis")
ctrl = df[df.grupo_cat == "controle"]
out.append("Rótulos: `relevante_mpe` da rubrica (VLM, não é julgamento humano); canais excluídos em `veredictos.csv` (decisao = excluir); "
           "canais fora do perfil em `auditoria_canais_fora.csv`. Ressalvas de leitura: (1) a cobertura de rótulos é desigual entre réguas "
           "porque a categorização foi feita sobre tops antigos e novos; (2) a auditoria manual foi feita sobre os tops por ER, então canais que só "
           "aparecem em outros tops não foram auditados (o viés favorece as réguas novas); (3) as réguas com \"elegível\" e a R4 já removem, por "
           "construção, os canais excluídos e os posts rotulados como irrelevantes: para elas o % relevante é circular e não mede a régua. "
           "A comparação limpa do score é a das linhas \"sem filtros\". \"Foco A\" = critério que o pipeline usa hoje para a base elegível "
           "(relevante_mpe não falso e publico_alvo diferente de consumidor final/nenhum, quando preenchido).\n")
out.append("Taxa de referência (posts do grupo de controle categorizados, sorteados fora do top): " + "; ".join(
    f"{p}: {(g.rel == True).mean():.0%} relevantes, {(g.focoa == True).mean():.0%} Foco A (n={len(g)})" for p, g in ctrl.groupby("plataforma")) + ".\n")  # noqa: E712
rows = []
for nome, ids in TOPS.items():
    t = df[df.video_id.isin(ids)]
    for p, g in t.groupby("plataforma"):
        nl, k = int(g.rel.notna().sum()), int((g.rel == True).sum())  # noqa: E712
        circ = " (circular)" if ("eleg" in nome or "R4 " in nome) else ""
        rows.append([nome, p, len(g), f"{nl} ({nl / len(g):.0%})", (f"{k / nl:.0%} [{wilson(k, nl)}]{circ}" if nl >= 15 else "n<15"),
                     (f"{(g.focoa == True).sum() / nl:.0%}{circ}" if nl >= 15 else "n<15"), f"{g.exc.mean():.0%}", f"{g.fora.mean():.0%}", f"{g.julgado.mean():.0%}"])
tab(rows, ["régua", "plataforma", "n top", "n com rótulo (cobertura)", "% relevante entre rotulados [IC95 Wilson]", "% Foco A entre rotulados",
           "% do top em canal excluído", "% do top em canal fora (auditoria)", "% do top em canal com veredicto"])
out.append("Por estrato (plataforma × porte): `data/avaliacao_regua_estratos.csv`. Estratos com menos de 15 rotulados não sustentam conclusão.\n")

# ---------------------------------------------------------------- 4. fora da amostra
H("4. Teste fora da amostra (validade preditiva temporal)")
out.append("Criadores com ≥10 posts; para cada um, a metade mais antiga dos posts é treino e a metade mais recente é teste. "
           "Tudo é estimado só no treino. Ressalva: os posts de teste são sistematicamente mais novos que os de treino, então o termo de idade "
           "é extrapolado para fora da faixa do treino; por isso o modelo também é avaliado sem idade.\n")
s = df[df.n_posts >= 10].sort_values(["channel_id", "publicado"]).copy()
s["treino"] = s.groupby("channel_id").cumcount() < s.groupby("channel_id").video_id.transform("size") // 2
r4a, r4b, r4c, r4d = [], [], [], []
for p, g in s.groupby("plataforma"):
    tr, te = g[g.treino].copy(), g[~g.treino].copy()
    te["formato"] = te.formato.where(te.formato.isin(tr.formato.unique()), tr.formato.mode()[0])
    preds = {}
    mods = {}
    for nome, f in [("modelo misto (completo)", F_FULL), ("modelo misto sem idade", "y ~ logF + C(formato)"), ("modelo misto só log(seguidores)", "y ~ logF")]:
        m = mods[nome] = ajusta(tr, f)
        if m is not None:
            preds[nome] = m.predict(te) + te.channel_id.map(m.re)
    tr["er_"] = tr.er
    med_er = tr.groupby("channel_id").er.median()
    preds["baseline: ER mediano do criador × seguidores"] = np.log1p(te.channel_id.map(med_er) * te.inscritos)
    preds["baseline: mediana do log-engajamento do criador"] = te.channel_id.map(tr.groupby("channel_id").y.median())
    preds["baseline: média do log-engajamento do criador"] = te.channel_id.map(tr.groupby("channel_id").y.mean())
    ols = smf.ols("y ~ logF", tr).fit()
    preds["baseline: só log(seguidores), regressão simples"] = ols.predict(te)
    ref = (te.y - preds["baseline: mediana do log-engajamento do criador"]).abs()
    cod = te.channel_id.astype("category").cat.codes.values
    nc = cod.max() + 1
    for nome, pr in preds.items():
        e = (te.y - pr).abs()
        d = (e - ref).values
        sd, sn = np.bincount(cod, d, nc), np.bincount(cod, minlength=nc)
        bs = []
        for _ in range(2000):  # bootstrap por criador (cluster)
            i = RNG.integers(0, nc, nc)
            bs.append(sd[i].sum() / sn[i].sum())
        lo, hi = np.percentile(bs, [2.5, 97.5])
        r4a.append([p, nome, f"{e.mean():.3f}", f"{e.median():.3f}", f"{sp(pr, te.y):.3f}",
                    "ref." if "mediana do log" in nome else f"{d.mean():+.3f} [{lo:+.3f}; {hi:+.3f}]", len(te), nc])
    # (b) estabilidade do ranking de criadores
    mte = ajusta(te, F_FULL)
    cs = pd.DataFrame({"er_medio_tr": tr.groupby("channel_id").er.mean(), "er_medio_te": te.groupby("channel_id").er.mean(),
                       "er_mediano_tr": med_er, "er_mediano_te": te.groupby("channel_id").er.median(),
                       "efeito_tr": pd.Series(mods["modelo misto (completo)"].re) if mods["modelo misto (completo)"] is not None else np.nan,
                       "efeito_te": pd.Series(mte.re) if mte is not None else np.nan})
    for nome, a, b in [("ER médio do criador", "er_medio_tr", "er_medio_te"), ("ER mediano do criador", "er_mediano_tr", "er_mediano_te"),
                       ("efeito do criador encolhido (modelo misto)", "efeito_tr", "efeito_te")]:
        d = cs[[a, b]].dropna()
        r, lo, hi = sp_ic(d[a], d[b])
        r4b.append([p, nome, f"{r:.3f} [{lo:.2f}; {hi:.2f}]", len(d)])
    # (c1) corte congelado no treino aplicado ao teste
    mfull = mods["modelo misto (completo)"]
    tr["out_"], te["out_"] = tr.er / tr.channel_id.map(med_er), te.er / te.channel_id.map(med_er)
    te["er_"] = te.er
    tr["res_"] = tr.y - mfull.fittedvalues
    te["res_"] = te.y - preds["modelo misto (completo)"]
    msi = mods["modelo misto sem idade"]
    tr["res2_"], te["res2_"] = tr.y - msi.fittedvalues, te.y - preds["modelo misto sem idade"]
    # (c2) persistência por criador: fatia dos posts do criador no top, treino × teste (top do teste definido só com o teste)
    te["out_te"] = te.er / te.channel_id.map(te.groupby("channel_id").er.median())
    te["res_te"] = te.y - mte.fittedvalues if mte is not None else np.nan
    for nome, ctr, cte_congelado, cte_proprio in [("R1 ER puro", "er_", "er_", "er_"), ("R2 outlier", "out_", "out_", "out_te"),
                                                  ("R3 modelo misto", "res_", "res_", "res_te"), ("R3 sem idade", "res2_", "res2_", None)]:
        corte = tr.groupby("porte")[ctr].quantile(0.9)
        passa = te[cte_congelado] >= te.porte.map(corte)
        linha = [p, nome, f"{passa.mean():.1%}", int(passa.sum()), len(te)]
        if cte_proprio:
            ttr = tr[ctr] >= tr.porte.map(corte)
            tte = te[cte_proprio] >= te.porte.map(te.groupby("porte")[cte_proprio].quantile(0.9))
            a, b = ttr.groupby(tr.channel_id).mean(), tte.groupby(te.channel_id).mean()
            r, lo, hi = sp_ic(a, b.reindex(a.index))
            reinc = te[tte].channel_id.isin(tr[ttr].channel_id).mean()
            linha += [f"{r:.2f} [{lo:.2f}; {hi:.2f}]", f"{reinc:.0%}", f"{tr[ttr].channel_id.nunique()}/{nc}"]
        else:
            linha += ["-", "-", "-"]
        r4c.append(linha)
    r4d.append([p, len(tr), len(te), nc, f"{tr.idade_dias.median():.0f}", f"{te.idade_dias.median():.0f}"])
tab(r4d, ["plataforma", "n posts treino", "n posts teste", "criadores", "idade mediana treino (dias)", "idade mediana teste (dias)"])
out.append("**(a) Previsão do log-engajamento dos posts de teste.** MAE em unidades de log (0,69 ≈ errar por um fator de 2). "
           "Δ MAE = diferença contra o baseline \"mediana do log-engajamento do criador\", com IC95 por bootstrap de criadores "
           "(negativo = melhor que o baseline; se o intervalo contém 0, não há diferença demonstrada).\n")
tab(r4a, ["plataforma", "previsor", "MAE", "erro abs. mediano", "Spearman(previsto, real)", "Δ MAE vs mediana do criador [IC95]", "n posts teste", "n criadores"])
out.append("**(b) Estabilidade do score do criador (treino × teste).** Spearman entre o score do criador calculado na metade antiga e na metade recente "
           "(IC95 por bootstrap de criadores). O efeito do criador no teste vem de um segundo ajuste do modelo só com o teste.\n")
tab(r4b, ["plataforma", "score do criador", "Spearman treino×teste [IC95]", "n criadores"])
out.append("**(c) Regressão à média.** Um post não se repete, então não dá para observar o mesmo post do top de novo. Duas medidas viáveis: "
           "(c1) corte do top 10% congelado no treino (por porte) e aplicado aos posts de teste com tudo do treino (mediana do criador, coeficientes): "
           "se a régua fosse estável, ~10% dos posts de teste passariam; (c2) persistência por criador: correlação entre a fatia dos posts do criador "
           "que entra no top no treino e no teste, e % dos posts do top do teste que vêm de criadores que já tinham post no top do treino.\n")
tab(r4c, ["plataforma", "régua", "(c1) % do teste acima do corte do treino", "n acima", "n teste", "(c2) Spearman fatia-no-top treino×teste [IC95]",
          "(c2) % do top do teste vindo de criadores já no top do treino", "criadores no top do treino / total"])

# ---------------------------------------------------------------- 5. parâmetros
H("5. Parâmetros do modelo")
out.append("b = elasticidade do engajamento em relação a seguidores (o ER puro pressupõe b = 1). ICC = variância entre criadores ÷ (entre criadores + residual). "
           "Como seguidores é constante por criador, b é identificado só pela comparação entre criadores; um modelo de efeitos fixos por criador não "
           "consegue estimá-lo (colinearidade perfeita).\n")
rows, rows2 = [], []
for base_nome, base in [("elegível (a da R4)", el), ("≥5 posts, sem filtros", el0)]:
    for p, g in base.groupby("plataforma"):
        # como o pipeline ajusta (lbfgs)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            try:
                ml = smf.mixedlm(F_FULL, g, groups=g["channel_id"]).fit(method="lbfgs")
                deg = (not np.isfinite(ml.llf)) or ml.cov_re.iloc[0, 0] < 1e-8
                lb = f"b={ml.params['logF']:.2f}, var. criador={ml.cov_re.iloc[0, 0]:.3f}, llf={ml.llf:.0f}" + (" → DEGENERADO" if deg else "")
            except Exception as e:
                lb = f"exceção: {str(e)[:50]}"
            av = "; ".join(sorted({str(x.message)[:45] for x in w})) or "nenhum"
        for nome, f in [("completo", F_FULL), ("sem formato", "y ~ logF + logIdade"), ("sem idade", "y ~ logF + C(formato)")]:
            m = ajusta(g, f)
            if m is None:
                rows.append([base_nome, p, nome, "não ajustou"] + [""] * 7); continue
            lo, hi = m.conf_int().loc["logF"]
            vc = m.cov_re.iloc[0, 0]
            rows.append([base_nome, p, nome, m.metodo, f"{m.params['logF']:.2f} [{lo:.2f}; {hi:.2f}]", f"{vc:.2f}", f"{m.scale:.2f}",
                         f"{vc / (vc + m.scale):.2f}", len(g), g.channel_id.nunique(), "; ".join(m.avisos) or "nenhum"])
        # conferências independentes do modelo misto
        cm = g.groupby("channel_id").agg(y=("y", "mean"), logF=("logF", "first"))
        bt = smf.ols("y ~ logF", cm).fit()
        lo1, hi1 = bt.conf_int().loc["logF"]
        pc = smf.ols(F_FULL, g).fit(cov_type="cluster", cov_kwds={"groups": g.channel_id.astype("category").cat.codes})
        lo2, hi2 = pc.conf_int().loc["logF"]
        fe = smf.ols("y ~ C(channel_id) + logIdade + C(formato)", g).fit()
        col = "resid4m" if base is el else "resid3"
        gg = g.assign(fe=fe.resid)
        rows2.append([base_nome, p, lb, av, f"{bt.params['logF']:.2f} [{lo1:.2f}; {hi1:.2f}] (n={len(cm)} criadores)",
                      f"{pc.params['logF']:.2f} [{lo2:.2f}; {hi2:.2f}]", f"{sp(gg.fe, gg[col]):.3f}",
                      f"{jac(top_de(gg, 'fe'), top_de(gg, col)):.2f}", f"{g.groupby('channel_id').size().median():.0f}"])
tab(rows, ["base", "plataforma", "especificação", "otimizador que convergiu", "b [IC95]", "var. criador", "var. residual", "ICC", "n posts", "n criadores", "avisos"])
out.append("Conferências: ajuste com `lbfgs` (o que o pipeline usa); b por regressão entre criadores (média de y do criador ~ log seguidores); "
           "b por OLS agrupado com erro-padrão robusto por criador; e concordância do resíduo do modelo misto com o resíduo de um modelo de "
           "efeitos fixos por criador (dummies de criador + formato + idade), que não depende de b nem da variância do efeito aleatório.\n")
tab(rows2, ["base", "plataforma", "ajuste lbfgs (pipeline)", "avisos no lbfgs", "b entre criadores [IC95]", "b OLS cluster [IC95]",
            "Spearman resíduo misto × efeitos fixos", "Jaccard do top 10% (misto × efeitos fixos)", "posts por criador (mediana)"])

out.append("Fragilidade do otimizador do pipeline: mesmo ajuste `lbfgs` em 20 subamostras da base elegível, cada uma sem 0,5% dos posts sorteados. "
           "\"Degenerado\" = variância do criador zerada, verossimilhança infinita ou exceção ao calcular o resíduo; nesses casos o pipeline cai no plano B "
           "(log-engajamento − mediana do criador) sem avisar.\n")
rows = []
for p, g in el.groupby("plataforma"):
    deg = 0
    for i in range(20):
        gs = g.sample(frac=0.995, random_state=i)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                ml = smf.mixedlm(F_FULL, gs, groups=gs["channel_id"]).fit(method="lbfgs")
                _ = ml.fittedvalues
                deg += (not np.isfinite(ml.llf)) or ml.cov_re.iloc[0, 0] < 1e-8
            except Exception:
                deg += 1
    rows.append([p, len(g), f"{deg}/20"])
tab(rows, ["plataforma", "n posts elegíveis", "ajustes lbfgs degenerados"])

# ---------------------------------------------------------------- 6. sensibilidade
H("6. Sensibilidade da R4")
out.append("Jaccard = posts em comum ÷ posts na união (1 = tops idênticos). Referência: top 10% por estrato, máx. 3 por criador, base elegível. "
           "\"Pipeline\" usa o resíduo como o pipeline calcula hoje; \"convergido\" usa o modelo misto ajustado até convergir.\n")
df["resid_si"] = resid_misto(el, "y ~ logF + C(formato)")
df["resid_sf"] = resid_misto(el, "y ~ logF + logIdade")
el = df[df.elegivel]
rows = []
for p in ("instagram", "youtube"):
    g = el[el.plataforma == p]
    for rotulo, col in [("pipeline", "resid"), ("convergido", "resid4m")]:
        ref = top_de(g, col, cap=3)
        var = [("máx 2 por criador", top_de(g, col, cap=2)), ("máx 5 por criador", top_de(g, col, cap=5)), ("sem limite por criador", top_de(g, col)),
               ("top 15% (máx 3)", top_de(g, col, q=0.85, cap=3))]
        if col == "resid4m":
            var += [("sem covariável de idade", top_de(g, "resid_si", cap=3)), ("sem covariável de formato", top_de(g, "resid_sf", cap=3)),
                    ("trocar o modelo pelo outlier simples (R2 + máx 3 + elegível)", top_de(g, "outlier", cap=3)),
                    ("resíduo do pipeline em vez do convergido", top_de(g, "resid", cap=3)),
                    ("plano B do pipeline (log-engajamento − mediana do criador)",
                     top_de(g.assign(pb=g.y - g.groupby("channel_id").y.transform("median")), "pb", cap=3))]
        for nome, t in var:
            rows.append([p, rotulo, nome, len(ref), len(t), len(ref & t), f"{jac(ref, t):.2f}"])
tab(rows, ["plataforma", "resíduo", "variação", "n ref.", "n variação", "em comum", "Jaccard"])
out.append("Concordância entre os scores na base elegível (Spearman, post a post):\n")
tab([[p, len(g), f"{sp(g.resid4m, g.log_out):.3f}", f"{sp(g.resid, g.log_out):.3f}", f"{sp(g.resid4m, g.er):.3f}", f"{sp(g.resid4m, g.resid_si):.3f}"]
     for p, g in el.groupby("plataforma")],
    ["plataforma", "n", "modelo convergido × outlier", "resíduo do pipeline × outlier", "modelo convergido × ER", "modelo com idade × sem idade"])
out.append("Sobreposição entre os tops das réguas (Jaccard, por plataforma):\n")
nomes = list(TOPS)
ab = {n: f"T{i + 1}" for i, n in enumerate(nomes)}
out.append("Legenda: " + "; ".join(f"{ab[n]} = {n}" for n in nomes) + ".\n")
for p in ("instagram", "youtube"):
    ids = set(df[df.plataforma == p].video_id)
    out.append(f"{p}:\n")
    tab([[ab[a]] + [f"{jac(TOPS[a] & ids, TOPS[b] & ids):.2f}" for b in nomes] for a in nomes], [""] + [ab[n] for n in nomes])

out.append("@@VEREDITO@@")

# ---------------------------------------------------------------- prosa
# Escrita a partir da execução de 24/11/2026 (base elegível ≈ 8.780 posts do YouTube e 592 do Instagram, 495 rótulos).
# Os números citados aqui são dessa execução; as tabelas são recalculadas a cada rodada. Se os dados mudarem, revisar o texto.
RESUMO = """## Resumo

1. **Viés de tamanho: resolvido tanto pelo outlier quanto pelo modelo.** O ER puro cai com o tamanho do criador (rho = −0,49 no Instagram, n = 655 posts/27 criadores; −0,28 no YouTube, n = 11.021/100). Outlier e resíduo do modelo ficam em rho ≈ 0 (entre −0,02 e +0,01). Empate entre R2 e R3.
2. **Concentração: o ganho vem do limite de 3 posts por criador, não do modelo.** HHI médio no YouTube: 0,22 (R1) → 0,09 (R2) → 0,07 (R3) → 0,04 com máx. 3, igual para outlier e modelo. Custo: o "top 10%" passa a ser ~1,9% da base do YouTube (≈ 200 de ~11 mil posts) e ~7% da do Instagram (48 de 655).
3. **Relevância: sem diferença demonstrada entre os scores.** Sem os filtros de elegibilidade e com máx. 3, o % relevante entre rotulados é ≈ 76% nos três scores no YouTube (ER / outlier / modelo; n entre 60 e 75 cada) e 84% / 87% / 87% no Instagram (n ≈ 38). Os 100% da R4 são circulares: a base elegível já remove os irrelevantes rotulados e os canais excluídos, e só cerca de um quarto do top da R4 no YouTube tinha rótulo (pouco mais de 50 de ≈ 200; a categorização estava em andamento).
4. **Fora da amostra, o modelo misto não bate a mediana do próprio criador.** Δ MAE (log) contra "mediana do log-engajamento do criador": −0,02 [IC95 −0,11; +0,06] no Instagram (331 posts, 26 criadores) e +0,03 [−0,02; +0,09] no YouTube (5.522 posts, 94 criadores). Os dois batem com folga a regressão só em seguidores (MAE 1,09 e 1,51).
5. **Score do criador: estabilidade equivalente.** Spearman treino×teste do efeito encolhido = 0,84 (Instagram) e 0,82 (YouTube); do ER mediano = 0,94 e 0,82. Os intervalos se sobrepõem.
6. **Elasticidade de seguidores b ≈ 0,37** (Instagram [0,13; 0,62], 25 criadores; YouTube [0,22; 0,49], 82 criadores): rejeita b = 1, que é a premissa do ER puro. Cerca de metade da variância do log-engajamento é do criador (ICC 0,49 a 0,54).
7. **Problema de implementação:** o `lbfgs` usado em `pipeline.residuo_modelo` degenera no YouTube em 16 de 20 subamostras da base elegível; quando isso acontece o pipeline troca, sem aviso, o modelo misto pelo log do outlier. Nas quatro rodadas feitas para este relatório, com minutos de diferença e a base elegível do YouTube variando entre 8.777 e 8.799 posts, o pipeline usou o modelo em duas e o plano B em duas; a seção 0 mostra qual caminho valeu na rodada gravada. O Instagram, onde se suspeitava do aviso de matriz singular, ajusta sem avisos (0 de 20).
8. **Modelo × outlier simples, com a mesma base e o mesmo limite:** os scores têm Spearman 0,91 (Instagram) e 0,94 (YouTube) e os tops têm Jaccard 0,74 e ≈ 0,68. Ou seja, cerca de 1 em cada 4 a 5 posts do top muda, mas nenhum teste desta avaliação mostra que a lista do modelo é melhor que a do outlier.
9. **Veredito:** a régua nova é melhor que o ER puro (viés de tamanho, concentração, canais fora do perfil). Dentro da régua nova, o que entrega o resultado é a normalização pelo próprio criador, o limite por criador e a base elegível; **o modelo misto não bate o outlier simples de forma material** em nenhum critério testado.
"""
VEREDITO = """
## 7. Veredito

**Onde a régua nova (R4) é comprovadamente melhor que o ER puro (R1)**
- Viés de tamanho: rho com seguidores vai de −0,49/−0,28 para ≈ 0 (seção 1).
- Concentração: fatia média do maior criador cai de 46% para 19% no Instagram e de 32% para 4% no YouTube; criadores distintos no top do YouTube sobem de 50 para 76 (seção 2).
- Canais fora do perfil: 51% do top por ER no YouTube está em canais excluídos na validação humana; com outlier ou modelo, 27–28%; com máx. 3, 16%; a R4 zera por construção (seção 3).
- A premissa do ER (engajamento proporcional a seguidores, b = 1) é rejeitada nas duas plataformas (b ≈ 0,37; seção 5).

**Onde o modelo misto é igual ao outlier simples**
- Viés de tamanho (ambos ≈ 0).
- Concentração depois do limite de 3 por criador (HHI 0,04–0,05 no YouTube, 0,16–0,19 no Instagram).
- Relevância entre rotulados, sem filtros (≈ 76% × ≈ 77% no YouTube, 87% × 87% no Instagram).
- Previsão fora da amostra: o modelo não reduz o erro em relação à mediana do criador (intervalos contêm 0 nas duas plataformas).
- Estabilidade do score do criador (efeito encolhido × ER mediano: intervalos sobrepostos).
- O resíduo do modelo misto é praticamente o resíduo de um modelo de efeitos fixos por criador (Spearman 0,998 a 1,000): o encolhimento e a elasticidade b não afetam a ordenação dos posts, porque seguidores é constante dentro do criador. O que diferencia o modelo do outlier são só formato e idade (e média em log no lugar da mediana).

**Onde o modelo tem alguma vantagem, pequena**
- Sem o limite por criador, concentra um pouco menos que o outlier (YouTube: HHI 0,07 × 0,09; 90 × 81 criadores).
- Num corte global (sem estratos), a mistura de portes fica mais próxima da base no YouTube (micro 53% × 63% do outlier, base 44%). Como a régua adotada estratifica por porte, isso não muda o resultado final.

**Onde é pior ou incerto**
- Robustez numérica: o ajuste `lbfgs` do pipeline degenera com frequência no YouTube e cai no plano B em silêncio. A régua publicada pode ser "modelo misto" numa rodada e "log do outlier" na seguinte; os dois tops têm Jaccard 0,74 (Instagram) e 0,76 a 0,80 (YouTube). Recomendação: trocar para `bfgs` (convergiu em todos os ajustes desta avaliação), checar variância do criador > 0 e registrar em log qual caminho foi usado.
- Covariável de idade: no teste temporal do YouTube, o corte de 10% do treino aplicado ao teste seleciona 19% dos posts com idade e 9% sem idade. O coeficiente de idade (posts mais antigos com mais engajamento) está confundido com tendência de calendário e não extrapola. Tirar a idade muda 25% do top do YouTube (Jaccard 0,75) e 6% do Instagram.
- Limite por criador: 2, 3 ou 5 mudam de 19% a 33% do top (Jaccard 0,67–0,81). O valor 3 é uma escolha, não um resultado.
- Tamanho do top: com máx. 3, o top do YouTube tem ≈ 200 posts de ≈ 76 criadores (de 82 elegíveis), isto é, quase todo criador elegível entra com seus 3 melhores posts. A régua deixa de escolher criadores e passa a escolher "os melhores posts de cada um"; isso é coerente com o objetivo (aprender com conteúdo, não com fama), mas não é mais um "top 10%".
- Relevância: os tops, por qualquer score, têm menos posts relevantes do que o grupo de controle categorizado (76–87% × 93–97%). O controle saiu da base elegível, o que infla a taxa dele, mas o sinal é que alto engajamento relativo atrai conteúdo fora do tema; o filtro de relevância é necessário e é ele (não o score) que garante a pertinência.

**Limitações a declarar**
1. Seguidores é um retrato de hoje; posts antigos foram publicados com outra base de seguidores. Não há série histórica.
2. O Instagram tem 25–26 criadores: o intervalo de b é largo ([0,13; 0,62]) e qualquer comparação por estrato tem n < 15 criadores.
3. `relevante_mpe` vem de um modelo de linguagem, não de avaliação humana; a cobertura de rótulos nos tops vai de cerca de 20% a 99% e não é aleatória (foi feita sobre tops anteriores).
4. A auditoria manual de canais foi feita sobre os tops por ER; canais que só aparecem nos tops novos não foram auditados.
5. O teste fora da amostra mede previsão de engajamento e estabilidade, não "qualidade" do conteúdo. Não existe rótulo externo de alto desempenho; nenhuma régua foi validada contra resultado de negócio.
6. Posts sem curtidas públicas ou de perfis sem contagem de seguidores ficam fora (31 posts); vídeos com menos de 14 dias não estão na base.

**Em uma frase:** a troca do ER puro por uma medida relativa ao próprio criador, com limite por criador e filtro de elegibilidade, está sustentada pelos dados; a escolha do modelo misto em vez do outlier simples não está, e hoje acrescenta um risco de instabilidade numérica que o outlier não tem.
"""
txt = "\n".join(out).replace("@@RESUMO@@", RESUMO).replace("@@VEREDITO@@", VEREDITO)
open("data/avaliacao_regua.md", "w").write(txt)
print(txt)
