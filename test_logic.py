"""Checagem da lógica que não depende de API: python test_logic.py"""
import pandas as pd

import pipeline as P

assert P.duracao_s("PT1M5S") == 65 and P.duracao_s("PT45S") == 45 and P.duracao_s("P0D") == 0
assert P.kappa(list("aabb"), list("aabb")) == 1.0 and P.kappa(list("aabb"), list("bbaa")) < 0

v = pd.DataFrame(dict(video_id=list("abcdefghij"), channel_id=["c1"] * 5 + ["c2"] * 5,
                      likes=[10, 10, 10, 10, 50, 100, 100, 100, 100, 100], comentarios=[0] * 10, plataforma="youtube"))
c = pd.DataFrame(dict(channel_id=["c1", "c2"], titulo=["pequeno", "grande"], inscritos=[100, 10_000], porte=["p", "g"],
                      plataforma="youtube", segmento="geral", tipo_criador="especialista"))
r = P.ranquear(v, c)
assert r.iloc[0].video_id == "e"             # er 0.5 vence o canal grande (er 0.01)
assert r.set_index("video_id").outlier["e"] == 5.0  # 5x a mediana do próprio canal
assert r.groupby("porte").top.any().all()         # cada faixa tem o seu top
assert r[r.porte == "p"].grupo.value_counts().to_dict() == {"top": 1, "controle": 1}  # controle = tamanho do top, fora dele
assert r.set_index("video_id").url["a"].startswith("https://www.youtube.com/shorts/")

df = pd.DataFrame(dict(plataforma="youtube", grupo=["top"] * 4 + ["controle"] * 4, tem_rosto=[True, True, True, False] + [True, False, False, False]))
lt = P.lift_table(df, ["tem_rosto"]).query("plataforma == \"todas\"").set_index("valor")
assert lt.loc["True", "lift"] == 3.0 and lt.loc["True", "n_top"] == 3
assert P.selo(1.5, 0.5) == "confirmado" and P.selo(1.5, -0.5) == "contradito"
assert P.selo(1.5, None) == "só mercado" and P.selo(1.0, 0.5) == "inconclusivo"
print("ok")

# nova régua: canal excluído e post irrelevante não entram no top; no máximo 3 posts por criador
v2 = pd.DataFrame(dict(video_id=[f"x{i}" for i in range(30)], channel_id=["a"] * 10 + ["b"] * 10 + ["z"] * 10,
                       likes=[1000] * 10 + list(range(10, 110, 10)) + [5000] * 10, comentarios=[0] * 30, plataforma="youtube"))
c2 = pd.DataFrame(dict(channel_id=["a", "b", "z"], titulo=["A", "B", "Z"], inscritos=[1000, 1000, 1000], porte="m",
                       plataforma="youtube", segmento="geral", tipo_criador="especialista"))
r2 = P.ranquear(v2, c2, excluidos={"z"}, relevancia={"x19": False})
assert not r2[r2.channel_id == "z"].top.any() and not r2[r2.channel_id == "z"].elegivel.any()
assert not r2.set_index("video_id").top["x19"]
assert r2[r2.top].groupby("channel_id").size().max() <= P.MAX_POR_CRIADOR
assert "top_er_puro" in r2 and r2.er.notna().all()  # ER do TAPI continua calculado
print("ok régua nova")

# Foco A: post que fala com o consumidor final (ou fora do tema) não é elegível; rubrica antiga sem o campo é tolerada
assert P.elegivel_foco_a({"relevante_mpe": True}) and P.elegivel_foco_a({"relevante_mpe": True, "publico_alvo": "ambos"})
assert not P.elegivel_foco_a({"relevante_mpe": True, "publico_alvo": "consumidor_final"})
assert not P.elegivel_foco_a({"relevante_mpe": False}) and not P.elegivel_foco_a({"publico_alvo": "nenhum"})
rub = {"x0": {"relevante_mpe": True, "publico_alvo": "consumidor_final"}, "x1": {"relevante_mpe": True, "publico_alvo": "donos_de_negocio"}}
r3 = P.ranquear(v2, c2, relevancia={k: P.elegivel_foco_a(x) for k, x in rub.items()}).set_index("video_id")
assert not r3.elegivel["x0"] and not r3.top["x0"] and r3.grupo["x0"] is None and r3.elegivel["x1"]
# "todas" pesa as plataformas por igual: 100% do top numa e 0% na outra = 50%, mesmo com tamanhos diferentes
d2 = pd.DataFrame(dict(plataforma=["instagram"] * 2 + ["youtube"] * 8, grupo=["top", "controle"] + ["top"] * 4 + ["controle"] * 4,
                       tem_rosto=[True, False] + [False] * 4 + [True, True, False, False]))
lt2 = P.lift_table(d2, ["tem_rosto"]).query("plataforma == \"todas\"").set_index("valor")
assert lt2.loc["True", "freq_top"] == 0.5 and lt2.loc["True", "freq_resto"] == 0.25
print("ok foco A")

# DeepSeek às vezes embrulha a resposta em {"properties": {...}}: valida_json desembrulha; schema ecoado segue sendo erro
from pydantic import BaseModel, ValidationError


class _T(BaseModel):
    ok: bool


assert P.valida_json('{"ok": true}', _T).ok and P.valida_json('{"properties": {"ok": true}}', _T).ok
try:
    P.valida_json('{"properties": {"ok": {"type": "boolean"}}, "required": ["ok"]}', _T)
    raise SystemExit("schema ecoado deveria falhar")
except ValidationError:
    pass
print("ok valida_json")
