"""Avaliar meu post: lê um post (vídeo, carrossel ou só a legenda) com a mesma rubrica da base e compara com o top.

Uso: .venv/bin/python avaliar.py <arquivo(s)> --legenda "..." --foco A|B --plataforma instagram|youtube [--video]

Caminho padrão: DeepSeek (Feita) com quadros do vídeo ou as imagens. --video tenta o Gemini com o vídeo inteiro
(com áudio) e cai para o DeepSeek se der erro. A nota mede "parecido com o top", não prevê resultado.
"""
import base64
import functools
import json
import math
import os
import sqlite3
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from pydantic import BaseModel

import foco_b as B
import pipeline as P
import transcrever as T

MAX_BYTES = 200 * 1024 * 1024
GANCHO = (0.0, 0.5, 1.0, 1.5, 2.0, 3.0)  # 6 quadros nos 3 primeiros segundos: o gancho decide o scroll
N_RESTO = 6  # e mais 6 espalhados pelo resto do vídeo
LADO = 768
VIDEO = {".mp4": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm"}
IMAGEM = {".jpg", ".jpeg", ".png", ".webp"}

FOCOS = {
    "A": dict(db=P.DB, csv=f"{P.DATA}/padroes_selados.csv", schema=P.Rubrica, carregar=P.carregar, notas=P.NOTAS,
              parecido=["formato_video", "tema_principal", "tipo_hook", "gatilho_identificacao", "tom", "pilar_impulso", "tipo_cta",
                        "convite_participacao", "prova_social", "tem_rosto"]),
    "B": dict(db=B.DBB, csv=f"{P.DATA}/b_achados.csv", schema=B.RubricaB, carregar=B.carregar_b, notas=B.NOTAS_B,
              parecido=["formato", "tipo_gancho", "tom", "tipo_cta", "mostra_processo", "rosto_do_dono", "cliente_aparece",
                        "mostra_preco", "tem_oferta_ou_prazo", "texto_na_tela"]),
}
# campos da conta (não do post): não dá para saber de um post avulso, ficam fora da comparação
FORA = {"segmento", "porte", "tipo_criador"}

# rótulos em linguagem simples: booleanos (se tem, se não tem) e categóricos (prefixo + valor)
ROTULO_BOOL = {
    "tem_rosto": ("Aparece rosto", "Sem rosto na tela"),
    "criador_e_empreendedor_real": ("Quem fala tem negócio próprio", "Quem fala não é dono de negócio"),
    "prova_social": ("Mostra prova social (resultados, clientes)", "Sem prova social"),
    "texto_na_tela": ("Texto na tela", "Sem texto na tela"),
    "usa_linguagem_regional": ("Jeito de falar regional", "Sem jeito de falar regional"),
    "tem_cta": ("Pede uma ação ao público", "Não pede nenhuma ação"),
    "oferta_ou_beneficio_explicito": ("Oferta ou benefício explícito", "Sem oferta explícita"),
    "convite_participacao": ("Convida o público a participar", "Não convida a participar"),
    "generico": ("Mensagem genérica, serviria para qualquer público", "Mensagem específica para o público"),
    "mostra_produto": ("Mostra o produto", "Não mostra o produto"),
    "mostra_preco": ("Mostra o preço", "Não mostra o preço"),
    "mostra_processo": ("Mostra como é feito", "Não mostra como é feito"),
    "rosto_do_dono": ("Dono ou equipe aparece de rosto", "Sem rosto do dono ou da equipe"),
    "cliente_aparece": ("Cliente real aparece", "Nenhum cliente aparece"),
    "tem_oferta_ou_prazo": ("Oferta ou prazo", "Sem oferta nem prazo"),
    "gatilho_sazonal": ("Usa data ou época do ano", "Sem data ou época do ano"),
    "convida_a_responder": ("Convida a responder nos comentários", "Não convida a responder"),
    "producao_alta": ("Produção caprichada (nota 7+)", "Produção simples (nota abaixo de 7)"),
    "desejo_alto": ("Dá muita vontade de comprar (nota 7+)", "Desperta pouco desejo (nota abaixo de 7)"),
}
ROTULO_CAT = {
    "formato_video": "Formato: {}", "formato": "Formato: {}", "tipo_hook": "Gancho com {}", "tipo_gancho": "Gancho: {}",
    "tema_principal": "Tema: {}", "tom": "Tom {}", "tipo_cta": "Chamada para ação: {}", "gatilho_identificacao": "Identificação: {}",
    "pilar_impulso": "Pilar: {}", "tipo_post": "Tipo de post: {}", "duracao_faixa": "Duração {}", "legenda_tamanho": "Legenda {}",
}
VALOR_LEGIVEL = {"media": "média", "pessoa_real": "pessoa real", "data_sazonal": "data ou época do ano", "nenhum": "nenhuma"}
ROTULO_NOTA = {
    "forca_hook_0a10": "Força do gancho", "ritmo_cortes_0a10": "Ritmo dos cortes", "clareza_mensagem_0a10": "Clareza da mensagem",
    "generico_0a10": "Quão genérico (menor é melhor)", "qualidade_producao_0a10": "Qualidade da produção",
    "apetite_ou_desejo_0a10": "Vontade de comprar",
}


# ---------- mídia ----------

def _jpg(entrada, saida, ss=None):
    """Um quadro (ou imagem) -> JPEG com o lado maior em até LADO px. Devolve os bytes, ou None se não saiu nada."""
    cmd = ["ffmpeg", "-v", "error", "-y"] + (["-ss", f"{ss:.2f}"] if ss is not None else []) + [
        "-i", entrada, "-frames:v", "1", "-q:v", "4",
        "-vf", f"scale='min({LADO},iw)':'min({LADO},ih)':force_original_aspect_ratio=decrease", saida]
    subprocess.run(cmd, capture_output=True, timeout=120)
    return open(saida, "rb").read() if os.path.exists(saida) and os.path.getsize(saida) else None


def duracao(caminho):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", caminho],
                       capture_output=True, text=True, timeout=60)
    try:
        return float(r.stdout.strip())
    except ValueError:
        raise ValueError("não consegui ler o vídeo (arquivo corrompido ou formato não suportado)")


def instantes(dur, n=N_RESTO):
    """Denso no gancho (GANCHO, até 3 s) e n quadros espalhados entre 3 s e o fim (sem o último instante, que às vezes não decodifica)."""
    g = [t for t in GANCHO if t < dur] or [dur / 2]
    return g + ([3 + (dur - 3) * i / (n + 1) for i in range(1, n + 1)] if dur > 3.5 else [])


def quadros(video: bytes, ext=".mp4", n=N_RESTO):
    """Vídeo -> (lista de (instante em s, JPEG) em ordem, duração em s)."""
    with tempfile.TemporaryDirectory() as d:
        f = f"{d}/video{ext}"
        open(f, "wb").write(video)
        dur = duracao(f)
        qs = [(t, _jpg(f, f"{d}/q{i}.jpg", ss=t)) for i, t in enumerate(instantes(dur, n))]
    qs = [(t, q) for t, q in qs if q]
    if not qs:
        raise ValueError("não consegui extrair quadros do vídeo")
    return qs, dur


def reduzir(imagem: bytes, ext=".jpg"):
    with tempfile.TemporaryDirectory() as d:
        open(f"{d}/in{ext}", "wb").write(imagem)
        out = _jpg(f"{d}/in{ext}", f"{d}/out.jpg")
    if not out:
        raise ValueError("não consegui ler uma das imagens")
    return out


def data_url(dado: bytes, mime="image/jpeg"):
    return f"data:{mime};base64," + base64.b64encode(dado).decode()


def separar(arquivos):
    """Valida a entrada -> ("video" | "imagens" | "texto", [(ext, bytes)])."""
    itens = [(os.path.splitext(nome)[1].lower(), dado) for nome, dado in arquivos]
    if any(len(dado) > MAX_BYTES for _, dado in itens):
        raise ValueError("arquivo acima de 200 MB")
    videos = [i for i in itens if i[0] in VIDEO]
    imagens = [i for i in itens if i[0] in IMAGEM]
    if len(videos) + len(imagens) < len(itens):
        raise ValueError("formato não aceito: use mp4, mov ou webm (vídeo) ou jpg, png ou webp (imagem)")
    if videos and (imagens or len(videos) > 1):
        raise ValueError("envie 1 vídeo OU de 1 a 10 imagens")
    if len(imagens) > 10:
        raise ValueError("no máximo 10 imagens")
    return ("video", videos) if videos else ("imagens", imagens) if imagens else ("texto", [])


# ---------- rubrica ----------

def prompt(foco, legenda, tipo):
    if foco == "A":
        return P.PROMPT.format(titulo=f"post em avaliação ({tipo})", descricao=legenda[:1500] or "(sem legenda)")
    return B.PROMPT_B.format(canal="negocio_em_avaliacao", segmento="não informado", seguidores="não informado", tipo=tipo,
                             legenda=legenda[:1500] or "(sem legenda)")


def ler_post(foco, tipo_midia, itens, legenda, tipo, usar_video, diz):
    """-> (rubrica dict, metodo, aviso, duração em s ou None)."""
    schema, aviso, dur = FOCOS[foco]["schema"], "", None
    texto = prompt(foco, legenda, tipo)
    if tipo_midia == "video":
        ext, dado = itens[0]
        diz("Extraindo quadros e transcrevendo o áudio")
        with ThreadPoolExecutor(2) as ex:  # quadros (ffmpeg) e fala (Whisper local) ao mesmo tempo
            fala = ex.submit(T.segmentos, dado)
            qs, dur = quadros(dado, ext)
            try:
                segs = fala.result()
            except Exception as e:  # sem Whisper o post ainda é lido pelos quadros
                segs, aviso = None, f"transcrição indisponível ({type(e).__name__}); "
        if usar_video:
            try:
                diz("Lendo o vídeo inteiro com a IA")
                rub = P.llm([{"type": "video_url", "video_url": {"url": data_url(dado, VIDEO[ext])}},
                             {"type": "text", "text": texto}], schema)
                return rub.model_dump(), "video_gemini", "", dur
            except Exception as e:  # cota do Gemini ou pico: segue pelos quadros (só o tipo do erro, nunca a mensagem crua)
                aviso += f"leitura do vídeo completo indisponível ({type(e).__name__}); "
        ng = sum(t <= 3 for t, _ in qs)
        nota = (f"ATENÇÃO: as {len(qs)} imagens são quadros, em ordem, de um vídeo de {dur:.0f} s; cada uma vem logo após "
                f"a linha com o seu instante. Os {ng} primeiros cobrem os 3 primeiros segundos: é o GANCHO, leia-os com atenção (texto na tela, "
                "rosto, movimento, o que aparece primeiro). Use a transcrição do áudio para o que é dito "
                "(principalmente a fala do gancho) e estime o ritmo pela mudança entre os quadros.\n"
                + (T.para_prompt(segs) if segs is not None else "Sem transcrição: deduza a fala pelo texto na tela e pela legenda.\n"))
        metodo = "quadros_deepseek"
        aviso += f"avaliado por {len(qs)} quadros" + (" e pela transcrição do áudio" if segs is not None else ", sem áudio")
    elif tipo_midia == "imagens":
        diz("Preparando as imagens")
        qs = [(None, reduzir(dado, ext)) for ext, dado in itens]
        nota, metodo = "", "imagens_deepseek"
    else:
        qs, metodo, aviso = [], "texto_deepseek", "avaliado só pelo texto, sem imagem nem vídeo"
        nota = ("ATENÇÃO: não há imagem nem vídeo. O texto abaixo é a legenda ou o roteiro do post: avalie por ele e marque "
                "false/0 no que for visual e não der para saber.\n")
    diz("Lendo o post com a IA")
    conteudo = []
    for t, q in qs:
        if t is not None:
            conteudo.append({"type": "text", "text": f"Quadro em {t:.1f} s" + (" (gancho)" if t <= 3 else "")})
        conteudo.append({"type": "image_url", "image_url": {"url": data_url(q)}})
    conteudo.append({"type": "text", "text": nota + texto})
    return P.llm(conteudo, schema, model=P.N1_MODEL).model_dump(), metodo, aviso, dur


def derivar(rub, foco, tipo, dur, legenda):
    """Rubrica + os mesmos campos derivados de P.carregar / B.carregar_b. tipo None = só texto (tipo e duração desconhecidos)."""
    post = dict(rub)
    n = len(legenda)
    post["legenda_tamanho"] = "curta" if n <= 100 else "media" if n <= 500 else "longa"
    if tipo:
        post["tipo_post"] = tipo
        post["duracao_faixa"] = "sem vídeo" if dur is None else "<15s" if dur <= 15 else "15-30s" if dur <= 30 else "30-60s" if dur <= 60 else ">60s"
    if foco == "A":
        post["generico"] = rub["generico_0a10"] >= 6
    else:
        post["producao_alta"] = rub["qualidade_producao_0a10"] >= 7
        post["desejo_alto"] = rub["apetite_ou_desejo_0a10"] >= 7
    return post


# ---------- padrões e nota ----------

def rotulo(campo, valor):
    if campo in ROTULO_BOOL:
        return ROTULO_BOOL[campo][0 if str(valor) == "True" else 1]
    return ROTULO_CAT.get(campo, campo + ": {}").format(VALOR_LEGIVEL.get(str(valor), valor))


def ler_padroes(foco, plataforma):
    """Padrões relevantes (lift >= 1,3 ou <= 0,75, n_top >= 3) da plataforma -> (lista de dicts, aviso)."""
    try:
        df = pd.read_csv(FOCOS[foco]["csv"], dtype={"valor": str})
    except FileNotFoundError:
        return [], f"sem padrões para comparar ({FOCOS[foco]['csv']} ausente)"
    aviso = ""
    if plataforma not in set(df.plataforma):
        outra = "todas" if "todas" in set(df.plataforma) else df.plataforma.iloc[0]
        aviso, plataforma = f"sem padrões de {plataforma} neste foco: comparado com os de {outra}", outra
    # ponytail: lift indefinido (valor que não aparece no controle) fica fora; entra quando houver intervalo de confiança
    df = df[(df.plataforma == plataforma) & ~df.campo.isin(FORA) & df.lift.notna() & (df.n_top >= 3)
            & ((df.lift >= 1.3) | (df.lift <= 0.75))]
    selo = df["selo"].fillna("só mercado") if "selo" in df else "só mercado"
    df = df.assign(selo=selo)[["campo", "valor", "lift", "n_top", "selo"]]
    return df.sort_values("lift", ascending=False).to_dict("records"), aviso


def casar(post, padroes):
    """Para cada padrão, se o post tem aquela característica."""
    return [dict(campo=p["campo"], valor=p["valor"], rotulo=rotulo(p["campo"], p["valor"]),
                 tem=p["campo"] in post and str(post[p["campo"]]) == str(p["valor"]),
                 lift=float(p["lift"]), n_top=int(p["n_top"]), selo=p["selo"],
                 efeito="ajuda" if p["lift"] > 1 else "atrapalha", fragil=int(p["n_top"]) < 5) for p in padroes]


def pontos(p):
    """Peso de um padrão: 10 x |ln(lift)|, com o lift limitado a 3 (ou 1/3). Frágil vale metade; contradito não conta."""
    if p["selo"] == "contradito":
        return 0.0
    w = 10 * min(abs(math.log(max(p["lift"], 1e-9))), math.log(3))
    return (w / 2 if p["fragil"] else w) * (1 if p["efeito"] == "ajuda" else -1)


def calcular_nota(padroes):
    """Só conta o que o post TEM: num campo como formato o post só pode ter um valor, então punir os ausentes
    seria punir toda escolha. -> (nota 0-100, explicação)."""
    tem = [p for p in padroes if p["tem"]]
    mais = sum(pontos(p) for p in tem if p["efeito"] == "ajuda")
    menos = -sum(pontos(p) for p in tem if p["efeito"] == "atrapalha")
    nota = max(0, min(100, round(50 + mais - menos)))
    return nota, (
        f"Começa em 50. Cada característica do seu post que aparece mais no top soma até 11 pontos (10 × |ln do lift|, lift limitado a 3); "
        f"cada uma que aparece menos no top subtrai na mesma medida. Padrão visto em menos de 5 posts do top vale metade. "
        f"Neste post: +{mais:.0f} de {sum(p['efeito'] == 'ajuda' for p in tem)} característica(s) que ajudam e "
        f"-{menos:.0f} de {sum(p['efeito'] == 'atrapalha' for p in tem)} que atrapalham. "
        "A nota mostra o quanto o post se parece com o top da nossa base; não é promessa de resultado.")


# ---------- comparação com a base ----------

@functools.lru_cache
def base(foco):
    """Posts categorizados do foco (top e controle), ou None se o banco não existir."""
    cfg = FOCOS[foco]
    if not os.path.exists(cfg["db"]):
        return None
    con = sqlite3.connect(f"file:{cfg['db']}?mode=ro", uri=True)
    try:
        return cfg["carregar"](con)
    except Exception:  # banco sem as tabelas esperadas
        return None
    finally:
        con.close()


def top_da_base(foco):
    df = base(foco)
    return df[df.grupo == "top"] if df is not None else pd.DataFrame()


def notas_vs_top(rub, foco, plataforma):
    top = top_da_base(foco)
    if top.empty:
        return []
    da_plat = top[top.plataforma == plataforma]
    top = da_plat if len(da_plat) >= 5 else top
    return [dict(campo=c, rotulo=ROTULO_NOTA.get(c, c), valor=int(rub[c]), mediana_top=float(top[c].median()))
            for c in FOCOS[foco]["notas"] if c in rub and c in top]


def parecidos(post, foco, plataforma, n=4):
    """Posts do top com mais campos coincidentes; mesma plataforma primeiro; no máximo um por criador."""
    top = top_da_base(foco)
    if top.empty:
        return []
    campos = [c for c in FOCOS[foco]["parecido"] if c in post and c in top]
    iguais = pd.DataFrame({c: top[c].astype(str) == str(post[c]) for c in campos})
    top = top.assign(_pts=iguais.sum(axis=1), _plat=top.plataforma == plataforma)
    top = top.sort_values(["_plat", "_pts", "resid"], ascending=False).drop_duplicates("channel_id").head(n)
    out = []
    for i, r in top.iterrows():
        comuns = [rotulo(c, post[c]) for c in campos if iguais.loc[i, c]][:3]
        titulo = (r.titulo or r.descricao or "").strip().split("\n")[0][:90]
        out.append(dict(video_id=r.video_id, plataforma=r.plataforma, canal=r.canal or r.channel_id, url=r.url,
                        er=round(float(r.er), 4), resid=round(float(r.resid), 2), titulo=titulo,
                        motivo="Em comum: " + "; ".join(comuns) if comuns else "Do top da mesma plataforma"))
    return out


# ---------- recomendações ----------

class Recomendacoes(BaseModel):
    recomendacoes: list[str]


PROMPT_REC = """Você orienta {quem} sobre um post que ainda vai ser publicado no {plataforma}.
Escreva de 3 a 5 recomendações práticas e específicas para ESTE post, em português do Brasil, tom próximo, sem jargão de marketing.
Regras:
- Cada recomendação é uma frase (no máximo duas) e cita o dado que a sustenta: o padrão com o lift e o número de posts do top, ou o exemplo parecido, ou a nota comparada à mediana do top.
- Diga o que mudar NESTE post, usando o conteúdo dele (gancho, tema, o que aparece). Nada de frase genérica que serviria para qualquer post.
- "lift 1,7" = aparece 1,7 vez mais no top que no grupo de controle. Explique assim, sem a palavra lift.
- Não prometa resultado: os padrões mostram o que o top tem em comum, não garantem alcance. Padrão com menos de 5 posts no top é só um indício: diga "vale testar".
- Não recomende piorar a qualidade, esconder o produto ou trocar o tema ou o segmento do negócio. Se um padrão for contraintuitivo ou não couber neste post, ignore.
- Não sugira dois formatos ou dois ganchos diferentes ao mesmo tempo.

Leitura do post (rubrica): {rubrica}
Método da leitura: {metodo}
Legenda: {legenda}
Características do post que aparecem MENOS no top: {atrapalham}
Padrões do top que o post NÃO tem: {faltam}
Características do post que já batem com o top: {tem}
Notas do post x mediana do top: {notas}
Posts do top parecidos: {parecidos}"""


def recomendacoes_fixas(padroes):
    """Sem o modelo: uma frase por campo, começando pelo que atrapalha e depois o que falta de mais forte."""
    uteis = [p for p in padroes if p["selo"] != "contradito" and p["campo"] not in ("producao_alta", "desejo_alto", "mostra_produto")]
    ruins = [p for p in uteis if p["tem"] and p["efeito"] == "atrapalha"]
    faltam = [p for p in uteis if not p["tem"] and p["efeito"] == "ajuda"]
    out, vistos = [], {p["campo"] for p in uteis if p["tem"] and p["efeito"] == "ajuda"}  # campo em que o post já acerta
    for p in sorted(ruins, key=lambda p: p["lift"]) + sorted(faltam, key=lambda p: (p["fragil"], -p["lift"])):
        if p["campo"] in vistos:
            continue
        vistos.add(p["campo"])
        lift = f"{p['lift']:.2f}".replace(".", ",")
        n = f"{p['n_top']} posts do top" + (", poucos casos: vale testar" if p["fragil"] else "")
        if p["tem"]:
            out.append(f"Seu post tem \"{p['rotulo']}\", que no top aparece {lift}× a frequência do grupo de controle, ou seja, menos ({n}). Veja se dá para mudar.")
        else:
            out.append(f"Teste \"{p['rotulo']}\": no top aparece {lift}× a frequência do grupo de controle ({n}).")
    return out[:5]


def recomendar(foco, plataforma, rub, metodo, legenda, padroes, notas, exemplos):
    def lista(ps):
        return "; ".join(f"{p['rotulo']} (lift {p['lift']}, {p['n_top']} posts do top{', frágil' if p['fragil'] else ''})" for p in ps) or "nenhum"
    ok = [p for p in padroes if p["selo"] != "contradito"]
    texto = PROMPT_REC.format(
        quem="um criador de conteúdo que fala com donos de pequenos negócios" if foco == "A" else "o dono de um pequeno negócio que fala com os clientes dele",
        plataforma=plataforma, rubrica=json.dumps(rub, ensure_ascii=False), metodo=metodo, legenda=legenda[:800] or "(sem legenda)",
        atrapalham=lista([p for p in ok if p["tem"] and p["efeito"] == "atrapalha"]),
        faltam=lista([p for p in ok if not p["tem"] and p["efeito"] == "ajuda"][:8]),
        tem=lista([p for p in ok if p["tem"] and p["efeito"] == "ajuda"]),
        notas="; ".join(f"{n['rotulo']}: {n['valor']} x {n['mediana_top']:g}" for n in notas) or "sem dados",
        parecidos="; ".join(f"@{e['canal']}: \"{e['titulo']}\" ({e['motivo']})" for e in exemplos) or "nenhum")
    try:
        recs = [r.strip() for r in P.llm(texto, Recomendacoes, model=P.N1_MODEL).recomendacoes if r.strip()][:5]
    except Exception:
        recs = []
    return recs if len(recs) >= 3 else recomendacoes_fixas(padroes)


# ---------- função pública ----------

def avaliar(arquivos: list[tuple[str, bytes]], legenda: str = "", foco: str = "A",
            plataforma: str = "instagram", usar_video: bool = False, progresso=None) -> dict:
    """Entrada inválida (formato, tamanho, post vazio) levanta ValueError com a mensagem para o usuário."""
    diz = progresso or (lambda _: None)
    foco, legenda = foco.upper(), (legenda or "").strip()
    if foco not in FOCOS:
        raise ValueError("foco deve ser A ou B")
    tipo_midia, itens = separar(arquivos or [])
    if tipo_midia == "texto" and not legenda:
        raise ValueError("envie um vídeo, imagens ou pelo menos a legenda")
    tipo = {"video": "short" if plataforma == "youtube" and foco == "A" else "reel",
            "imagens": "carrossel" if len(itens) > 1 else "imagem", "texto": None}[tipo_midia]
    rub, metodo, aviso, dur = ler_post(foco, tipo_midia, itens, legenda, tipo or "só texto", usar_video, diz)
    avisos = [aviso] if aviso else []
    if foco == "A" and not P.elegivel_foco_a(rub):
        avisos.append("este post parece falar com o cliente final, não com donos de negócio: experimente o Foco B")
    if foco == "B" and not rub["relevante_b"]:
        avisos.append("este post não parece ser um negócio falando com o cliente dele: experimente o Foco A")

    diz("Comparando com o top")
    post = derivar(rub, foco, tipo, dur, legenda)
    brutos, aviso_padroes = ler_padroes(foco, plataforma)
    padroes = casar(post, brutos)
    nota, explicacao = calcular_nota(padroes)
    notas = notas_vs_top(rub, foco, plataforma)
    exemplos = parecidos(post, foco, plataforma)
    if aviso_padroes:
        avisos.append(aviso_padroes)
    if base(foco) is None:
        avisos.append(f"base do foco {foco} indisponível: sem exemplos parecidos nem medianas do top")

    diz("Escrevendo as recomendações")
    recs = recomendar(foco, plataforma, rub, metodo, legenda, padroes, notas, exemplos)
    return dict(foco=foco, plataforma=plataforma, metodo=metodo, aviso="; ".join(avisos), rubrica=rub, nota=nota,
                nota_explicacao=explicacao, padroes=padroes, notas_vs_top=notas, parecidos=exemplos, recomendacoes=recs)


if __name__ == "__main__":
    import argparse
    import contextlib
    import sys
    ap = argparse.ArgumentParser(description="Avalia um post (1 vídeo, 1 a 10 imagens ou só a legenda) contra o top da base.")
    ap.add_argument("arquivos", nargs="*")
    ap.add_argument("--legenda", default="")
    ap.add_argument("--foco", default="A", choices=["A", "B"])
    ap.add_argument("--plataforma", default="instagram", choices=["instagram", "youtube"])
    ap.add_argument("--video", action="store_true", help="tenta o Gemini com o vídeo inteiro (com áudio)")
    a = ap.parse_args()
    with contextlib.redirect_stdout(sys.stderr):  # P.llm avisa trocas de modelo no stdout; o stdout daqui é só o JSON
        r = avaliar([(f, open(f, "rb").read()) for f in a.arquivos], a.legenda, a.foco, a.plataforma, a.video, progresso=print)
    print(json.dumps(r, ensure_ascii=False, indent=2))
