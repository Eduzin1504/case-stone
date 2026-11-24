"""Checagem da lógica que não depende de API: python test_logic.py"""
import pandas as pd

import pipeline as P

assert P.duracao_s("PT1M5S") == 65 and P.duracao_s("PT45S") == 45 and P.duracao_s("P0D") == 0
assert P.kappa(list("aabb"), list("aabb")) == 1.0 and P.kappa(list("aabb"), list("bbaa")) < 0

v = pd.DataFrame(dict(video_id=list("abcdefghij"), channel_id=["c1"] * 5 + ["c2"] * 5,
                      likes=[10, 10, 10, 10, 50, 100, 100, 100, 100, 100], comentarios=[0] * 10))
c = pd.DataFrame(dict(channel_id=["c1", "c2"], titulo=["pequeno", "grande"], inscritos=[100, 10_000], porte=["p", "g"]))
r = P.ranquear(v, c)
assert r.iloc[0].video_id == "e"             # er 0.5 vence o canal grande (er 0.01)
assert r.set_index("video_id").outlier["e"] == 5.0  # 5x a mediana do próprio canal

df = pd.DataFrame(dict(grupo=["top"] * 4 + ["controle"] * 4, tem_rosto=[True, True, True, False] + [True, False, False, False]))
lt = P.lift_table(df, ["tem_rosto"]).set_index("valor")
assert lt.loc["True", "lift"] == 3.0 and lt.loc["True", "n_top"] == 3
print("ok")
