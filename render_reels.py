"""Monta um Reels de marca: clipes de fundo (Feita) + texto do roteiro + cartão de CTA.

Cada bloco do roteiro vira {texto, prompt, segundos}; o clipe vem de feita_video
(com cache), o texto entra numa faixa Sherwood com destaque em lima, e o ffmpeg
junta tudo com o cartão final. Uso: .venv/bin/python render_reels.py  (pauta 2)
"""
import os
import re
import subprocess

from PIL import Image, ImageDraw, ImageFont

import feita_video

W, H = 720, 1280
SHERWOOD, LIMA, BRANCO = "#004132", "#c7f93c", "#efefef"
FONTE = "web/src/marca/fonts/Lexend.ttf"
SAIDA = os.path.join(os.getenv("DATA_DIR", "data"), "render", "feita")


def fonte(tam, peso=600):
    f = ImageFont.truetype(FONTE, tam)
    f.set_variation_by_axes([peso])
    return f


def quebrar(dr, texto, f, max_w):
    linhas, atual = [], ""
    for p in texto.split():
        t = (atual + " " + p).strip()
        if dr.textlength(t, font=f) <= max_w:
            atual = t
        else:
            linhas.append(atual)
            atual = p
    return linhas + [atual]


def overlay(texto, rotulo, caminho):
    """PNG transparente com a faixa de texto embaixo e a marca em cima. texto=None: só a marca."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    if texto:
        f_rot, f_txt = fonte(40, 800), fonte(36, 650)
        margem, larg = 42, W - 2 * 42
        linhas = quebrar(dr, texto, f_txt, larg - 48)
        alt_txt = len(linhas) * 48 + (70 if rotulo else 12) + 36
        y0 = H - 108 - alt_txt
        dr.rounded_rectangle([margem - 15, y0, W - margem + 15, y0 + alt_txt], 27,
                             fill=(0, 65, 50, 225))
        y = y0 + 24
        if rotulo:
            dr.text((margem + 9, y), rotulo, font=f_rot, fill=LIMA)
            y += 57
        for ln in linhas:
            dr.text((margem + 9, y), ln, font=f_txt, fill=BRANCO)
            y += 48
    f_marca = fonte(28, 700)
    marca = "@impulsostone"
    x = W - dr.textlength(marca, font=f_marca) - 36
    dr.text((x + 2, 38), marca, font=f_marca, fill=(0, 65, 50, 160))
    dr.text((x, 36), marca, font=f_marca, fill=BRANCO)
    im.save(caminho)


def cartao_cta(caminho_png, caminho_mp4, texto=None, fala=None, segundos=4):
    """Cartão final em lima com o CTA, virado em MP4 parado. 'Comenta X' vira a palavra gigante."""
    texto = texto or "Se inscreve no Impulso — é de graça."
    im = Image.new("RGB", (W, H), LIMA)
    dr = ImageDraw.Draw(im)
    f1, f2 = fonte(84, 800), fonte(40, 650)
    m = re.search(r"[Cc]omenta\s+([A-ZÀ-Ü]{2,})\b", texto)
    y = H // 2 - 240
    if m:
        dr.text((60, y), "Comenta", font=f2, fill=SHERWOOD)
        dr.text((60, y + 60), m.group(1), font=f1, fill=SHERWOOD)
        texto = re.sub(r"^\s*\([^)]*\)\s*\+?\s*", "", texto[m.end():].strip(" .,;")) or "e se inscreve no Impulso — é de graça."
        y += 200
    for i, ln in enumerate(quebrar(dr, texto, f2, W - 120)):
        dr.text((60, y + i * 52), ln, font=f2, fill=SHERWOOD)
    logo = Image.open("web/src/marca/impulso-stone-escura.png").convert("RGBA")
    alt = 160
    logo = logo.resize((int(alt * logo.width / logo.height), alt))
    im.paste(logo, (60, H - alt - 130), logo)
    dr.text((60, H - 100), "@impulsostone", font=f2, fill=SHERWOOD)
    im.save(caminho_png)
    _parte_estatica(caminho_png, caminho_mp4, fala, segundos)


def dur_audio(caminho):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", caminho], capture_output=True, text=True).stdout.strip())


AUDIO = ["-c:a", "aac", "-ar", "44100", "-ac", "2"]  # igual em todas as partes para o concat -c copy funcionar


def _parte_estatica(caminho_png, caminho_mp4, fala, segundos):
    """PNG parado virando MP4, com narração se houver."""
    if fala:
        dur = dur_audio(fala) + 0.6
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", caminho_png, "-i", fala,
                        "-filter_complex", "[1:a]apad[a]", "-map", "0:v", "-map", "[a]",
                        "-t", str(dur), "-r", "24", "-pix_fmt", "yuv420p", *AUDIO, caminho_mp4], check=True)
    else:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", caminho_png,
                        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", str(segundos),
                        "-r", "24", "-pix_fmt", "yuv420p", *AUDIO, "-shortest", caminho_mp4], check=True)


def cartao_texto(texto, rotulo, caminho_png, caminho_mp4, fala=None, segundos=6):
    """Cena extra sem clipe de IA: a mesma faixa de texto sobre fundo Sherwood parado (custo zero)."""
    overlay(texto, rotulo, caminho_png)
    fundo = Image.new("RGBA", (W, H), SHERWOOD)
    fundo.alpha_composite(Image.open(caminho_png))
    fundo.convert("RGB").save(caminho_png)
    _parte_estatica(caminho_png, caminho_mp4, fala, segundos)


def montar(blocos, nome, cta_texto=None, progresso=lambda _: None, narrar=True, faixa=True):
    os.makedirs(SAIDA, exist_ok=True)
    partes = []
    for i, b in enumerate(blocos):
        png = os.path.join(SAIDA, f"{nome}_ov{i}.png")
        parte = os.path.join(SAIDA, f"{nome}_p{i}.mp4")
        fala = feita_video.gerar_fala(b["texto"]) if narrar else None
        if b.get("prompt"):
            progresso(f"Gerando o clipe {i + 1} de {sum(1 for x in blocos if x.get('prompt'))} na Feita")
            clipe = feita_video.gerar_clipe(b["prompt"], segundos=b["segundos"])
            overlay(b["texto"] if faixa else None, b.get("rotulo") if faixa else None, png)
            dur = dur_audio(fala) + 0.6 if fala else b["segundos"]
            som = ["-i", fala] if fala else ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
            # o clipe roda em loop até a fala terminar
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", clipe, "-i", png, *som,
                            "-filter_complex", f"[0:v]scale={W}:{H}[v];[v][1:v]overlay=0:0[vo];[2:a]apad[a]",
                            "-map", "[vo]", "-map", "[a]", "-t", str(dur),
                            "-r", "24", "-pix_fmt", "yuv420p", *AUDIO, parte], check=True)
        else:
            cartao_texto(b["texto"], b.get("rotulo"), png, parte, fala, b.get("segundos", 6))
        partes.append(parte)
    progresso("Montando o vídeo final")
    cta_png, cta_mp4 = os.path.join(SAIDA, f"{nome}_cta.png"), os.path.join(SAIDA, f"{nome}_cta.mp4")
    cartao_cta(cta_png, cta_mp4, texto=cta_texto, fala=feita_video.gerar_fala(cta_texto) if narrar and cta_texto else None)
    partes.append(cta_mp4)
    lista = os.path.join(SAIDA, f"{nome}_lista.txt")
    with open(lista, "w") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in partes)
    final = os.path.join(SAIDA, f"{nome}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", lista, "-c", "copy", final], check=True)
    return final


def _palavras(fala_mp3):
    """Timestamps por palavra da narração, via o Whisper local do projeto."""
    import transcrever
    audio = transcrever._pcm(fala_mp3)
    segs, _ = transcrever._modelo().transcribe(audio, language="pt", beam_size=1, word_timestamps=True)
    return [(w.start, w.end, w.word.strip()) for s in segs for w in s.words]


def _png_grupo(texto, caminho):
    """Legenda estilo Reels: caixa alta, branco com contorno Sherwood, centrada."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    f = fonte(54, 800)
    linhas = quebrar(dr, texto.upper(), f, W - 120)
    y = int(H * 0.64) - len(linhas) * 34
    for ln in linhas:
        x = (W - dr.textlength(ln, font=f)) / 2
        dr.text((x, y), ln, font=f, fill="#ffffff", stroke_width=7, stroke_fill=SHERWOOD)
        y += 68
    im.save(caminho)


def legendar(video, blocos, nome, max_palavras=3):
    """Queima legendas dinâmicas no vídeo final: a fala de cada bloco vira grupos de até 3 palavras
    sincronizados pelo Whisper. O cartão de CTA fica sem legenda (já é texto)."""
    offsets, t = [], 0.0
    for i in range(len(blocos)):
        offsets.append(t)
        t += dur_audio(os.path.join(SAIDA, f"{nome}_p{i}.mp4"))
    grupos = []
    for i, b in enumerate(blocos):
        ps = _palavras(feita_video.gerar_fala(b["texto"]))
        for j in range(0, len(ps), max_palavras):
            lote = ps[j:j + max_palavras]
            grupos.append((offsets[i] + lote[0][0], offsets[i] + lote[-1][1] + 0.15, " ".join(w for _, _, w in lote)))
    entradas, filtros, ant = [], [], "0:v"
    for g, (a, b, txt) in enumerate(grupos):
        png = os.path.join(SAIDA, f"{nome}_leg{g}.png")
        _png_grupo(txt, png)
        entradas += ["-i", png]
        saida = f"v{g}"
        filtros.append(f"[{ant}][{g + 1}:v]overlay=0:0:enable='between(t,{a:.2f},{b:.2f})'[{saida}]")
        ant = saida
    final = video.replace(".mp4", "_leg.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, *entradas,
                    "-filter_complex", ";".join(filtros), "-map", f"[{ant}]", "-map", "0:a",
                    "-r", "24", "-pix_fmt", "yuv420p", "-c:a", "copy", final], check=True)
    for g in range(len(grupos)):
        os.remove(os.path.join(SAIDA, f"{nome}_leg{g}.png"))
    return final


B_ROLL = ("vertical 9:16 video, warm golden light, documentary handheld style, "
          "no faces visible, no people faces, no text, no words or letters on screen")

# ponytail: a Feita pré-reserva ~US$ 1,14 por clipe e cobra ~US$ 0,40; clipes de 4s, no máximo 5 por Reels
MAX_CLIPES, SEG_CLIPE = 5, 4


def prompts_broll(cenas, segmento=None):
    """O deepseek (crédito restrito, ~grátis) vira diretor de fotografia: um prompt de b-roll por cena,
    sem rosto e sem texto na tela, seguindo a regra do PLANO."""
    import json as _json
    pedido = (
        "Você é diretor de fotografia de Reels para pequenos negócios brasileiros"
        + (f" ({segmento})" if segmento else "") + ". Para cada cena do roteiro abaixo, escreva um prompt "
        "de b-roll em INGLÊS para um gerador de vídeo: ambiente, objetos e mãos em ação, SEM nenhum rosto "
        "visível e SEM texto ou letras na cena. Concreto e visual, 30-50 palavras. "
        'Responda só JSON: {"prompts": ["...", ...]} na mesma ordem.\n\n'
        + "\n".join(f"Cena {c['n']}: {c['texto']}" for c in cenas))
    r = feita_video._req("POST", "/chat/completions", feita_video.chaves()[0], {
        "model": "deepseek/deepseek-v4.1-flash-1017", "temperature": 0,
        "messages": [{"role": "user", "content": pedido}],
        "response_format": {"type": "json_object"}})
    ps = _json.loads(r["choices"][0]["message"]["content"])["prompts"]
    assert len(ps) == len(cenas), f"deepseek devolveu {len(ps)} prompts para {len(cenas)} cenas"
    return [p + ", " + B_ROLL for p in ps]


def fala(texto):
    """Só o que vai na tela: o trecho entre aspas da cena; sem aspas, a cena inteira."""
    m = re.findall(r"[''\"‘“]([^''\"’”]{10,})[''\"’”]", texto)
    return " ".join(m) if m else texto


def montar_criativo(criativo, nome, progresso=lambda _: None, faixa=True):
    """O fluxo real da plataforma: criativo do agente -> cenas -> prompts (deepseek) -> clipes (Feita)
    -> faixa de texto da marca -> MP4. A última cena com CTA vira o cartão lima."""
    from api import dados
    cenas = dados.cenas(criativo.get("roteiro"))
    cenas = [c for c in cenas if not (c["texto"].lower().startswith("b-roll") or "sugerido:" in c["texto"][:30].lower())]
    cta = criativo.get("cta")
    if cenas and "cta" in (cenas[-1].get("rotulo") or "").lower():
        cta = cta or fala(cenas[-1]["texto"])
        cenas = cenas[:-1]
    arq_prompts = os.path.join(SAIDA, f"{nome}_prompts.json")
    if os.path.exists(arq_prompts):  # o deepseek não é determinístico: sem isso o cache dos clipes falha
        import json as _json
        prompts = _json.load(open(arq_prompts))
    else:
        progresso("Escrevendo os prompts de cada cena com o DeepSeek")
        prompts = prompts_broll(cenas, criativo.get("segmento"))
        import json as _json
        os.makedirs(SAIDA, exist_ok=True)
        _json.dump(prompts, open(arq_prompts, "w"), ensure_ascii=False)
    blocos = [dict(texto=fala(c["texto"]), rotulo=re.sub(r"\s*\(.*\)$", "", c["rotulo"]) if c.get("rotulo") else None,
                   prompt=prompts[i] if i < MAX_CLIPES else None,
                   segundos=SEG_CLIPE if i < MAX_CLIPES else 6)
              for i, c in enumerate(cenas)]
    return montar(blocos, nome, cta_texto=cta, progresso=progresso, faixa=faixa)

PAUTA_2 = [
    dict(texto="Se você vende comida caseira, o Natal pode ser o seu melhor mês — ou o mês em que "
               "você trabalha dobrado e não vê o dinheiro sobrar.", rotulo=None, segundos=8,
         prompt="Cozy Brazilian home kitchen decorated for Christmas, wooden counter with homemade "
                "panettone, cakes in jars and artisanal sweets in clear packaging, warm fairy lights "
                "bokeh in background, female hands wearing oven mitts and apron carefully packing a "
                "cake jar with ribbon, slow gentle camera push-in, " + B_ROLL),
    dict(texto="Fechar encomenda sem saber quanto custa a sua hora. Você soma farinha, ovo, "
               "embalagem... e esquece o seu tempo na cozinha.", rotulo="ERRO 1", segundos=8,
         prompt="Close-up of hands writing in a small notebook next to baking ingredients, flour, "
                "eggs, packaging boxes and a calculator on a rustic wooden kitchen table, soft "
                "morning light from a window, shallow depth of field, " + B_ROLL),
    dict(texto="Aceitar tudo para a mesma data. Véspera de Natal tem limite de forno, de geladeira "
               "e de braço.", rotulo="ERRO 2", segundos=8,
         prompt="Busy home kitchen at Christmas rush, oven full of baking trays, kitchen timer, "
                "stacks of delivery boxes and packaged sweets piling up on the counter, hands "
                "quickly moving trays, energetic but warm atmosphere, " + B_ROLL),
    dict(texto="Não anotar o que vendeu. Sem anotar, você não sabe o que deu lucro e o que só deu "
               "cansaço.", rotulo="ERRO 3", segundos=8,
         prompt="Hands checking orders on a smartphone with blurred screen and writing sales in a "
                "paper notebook, jar with cash and coins nearby, cozy kitchen at night with warm "
                "lamp light, calm organized mood, " + B_ROLL),
]

if __name__ == "__main__":
    final = montar(PAUTA_2, "reels_pauta2")
    assert os.path.getsize(final) > 100_000, "MP4 final suspeito de vazio"
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", final], capture_output=True, text=True).stdout.strip()
    print(f"OK {final} ({float(d):.1f}s)")
    assert 30 <= float(d) <= 42, f"duração fora do esperado: {d}s"
