"""Checagem determinística de slop nos criativos (roda antes do juiz LLM, sem custo).

Base: reports/AI slop e processos de design.md
- proibições checadas em código, não só no prompt (Antislop, Wikipedia "Signs of AI writing")
- especificidade obrigatória: nicho, número/R$, data, pessoa ou dor concreta (NN/g, Hintze et al.)
- teste de troca de marca ("onliness", Neumeier) fica no juiz LLM: ver PROMPT_TROCA_MARCA
"""
import re

# ponytail: lista inicial é inferência de praticante; recalcular contra posts reais de MEIs (estilo Antislop) na T11
PROIBIDAS = {
    "jargão de coach": r"\b(alavan(c|qu)\w*|potencializ\w*|desbloqu\w*|transform\w* (o |seu |sua )?(seu |sua )?(negócio|vida)|"
                       r"jornada empreendedora|mindset|sinergia|disruptiv\w*|próximo nível|descubra o poder)\b",
    "abertura clichê": r"\b(no mundo (atual|de hoje)|nos dias de hoje|em um mundo cada vez mais|você sabia que)\b",
    "motivacional vazio": r"\b(não é sorte|acredite (em você|no seu)|o sucesso (é|está)|nunca desista|seja imparável)\b",
    "não é só X, é Y": r"\bnão (é|são) (só|apenas)\b[^.?!]{0,60}\b(é|são|mas)\b",
}
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
ESPECIFICO = re.compile(
    r"(r\$\s?\d|\d+\s?(%|reais|mil|dias|clientes|vendas|pedidos)|\b\d{1,2}/\d{1,2}\b|"
    r"\b(marmita|salão|manicure|lanchonete|padaria|brechó|ateliê|loja|mercadinho|confeitaria|"
    r"maquininha|pix|fiado|black friday|natal|dia das mães|festa junina|capital de giro|fim d[oe] ano|dezembro|13º|"
    r"pró-labore|estoque|encomenda|delivery|beleza|unha|cabelo|barbearia|feira|boleto|nota fiscal|mei)\b)", re.I)

PROMPT_TROCA_MARCA = ("Troque mentalmente 'Impulso Stone' por um banco qualquer. O post continua fazendo sentido "
                      "igualzinho? Se sim, responda generico=true.")


def checar(texto: str) -> list[str]:
    """Problemas encontrados; lista vazia = passou. Mensagens já servem de feedback para o redator."""
    t = texto.lower()
    out = [f"tirar {nome}: “{m.group(0)}”" for nome, rx in PROIBIDAS.items() if (m := re.search(rx, t))]
    if len(EMOJI.findall(texto)) > 3:
        out.append("no máximo 3 emojis")
    if texto.count("—") > 1:
        out.append("no máximo 1 travessão")
    if not ESPECIFICO.search(texto):
        out.append("falta algo concreto: um nicho, um valor em R$, um número, uma data ou um item do dia a dia (pix, fiado)")
    return out


if __name__ == "__main__":
    ruim = "Vender mais não é sorte, é estratégia! 💪🚀✨🔥 Acredite no seu negócio e alavanque sua jornada empreendedora."
    bom = "Você que vende marmita: quanto sobrou no fim do mês? Conta aqui nos comentários."
    r = checar(ruim)
    assert any("jargão" in p for p in r) and any("motivacional" in p for p in r) and any("emoji" in p for p in r), r
    assert checar(bom) == [], checar(bom)
    assert checar("Alavanque suas vendas de marmita")[0].startswith("tirar jargão")
    assert checar("Dicas para crescer com consistência.") == [
        "falta algo concreto: um nicho, um valor em R$, um número, uma data ou um item do dia a dia (pix, fiado)"]
    print("ok:", r)
