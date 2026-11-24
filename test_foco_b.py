"""Checagens mínimas do Foco B: regex de intenção de compra e régua do ranking. Rode: .venv/bin/python test_foco_b.py"""
import numpy as np
import pandas as pd

import foco_b as B


def test_intencao():
    for t in ["Quanto custa?", "qual o valor", "Vocês fazem entrega?", "quero 2", "Onde fica?", "aceita pix?", "tem no tamanho G?"]:
        assert B.INTENCAO.search(t), t
    for t in ["Lindo demais 😍", "Parabéns pelo trabalho", "@maria olha isso", "temos orgulho"]:
        assert not B.INTENCAO.search(t), t


def test_rankear():
    rng = np.random.default_rng(0)
    c = pd.DataFrame(dict(channel_id=[f"c{i}" for i in range(8)], titulo="x", inscritos=[800, 3000, 5000, 9000, 20000, 40000, 60000, 90000],
                          segmento="alimentação"))
    c["porte"] = c.inscritos.map(B.P.porte)
    v = pd.DataFrame(dict(video_id=[f"v{i}" for i in range(240)], channel_id=np.repeat(c.channel_id.values, 30),
                          likes=rng.lognormal(4, 1, 240).round(), comentarios=rng.poisson(3, 240), idade_dias=rng.integers(1, 300, 240),
                          tipo=rng.choice(["clips", "feed"], 240), plataforma="instagram", duracao_s=30.0))
    v.loc[0, "likes"] = None  # curtidas ocultas ficam fora
    df = B.rankear(v, c, 0.9)
    assert "v0" not in set(df.video_id)
    assert df[df.top].groupby("channel_id").size().max() <= 3
    assert (df[df.top].idade_dias >= 7).all()
    assert (df.grupo == "top").sum() == (df.grupo == "controle").sum() > 0
    assert not (df.top & (df.grupo == "controle")).any()


if __name__ == "__main__":
    test_intencao()
    test_rankear()
    print("ok")
