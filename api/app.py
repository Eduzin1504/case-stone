"""Pauta Impulso: API FastAPI (contrato em docs/superpowers/specs/2026-11-24-pauta-react-design.md).

Subir: ./rodar.sh  (uvicorn api.app:app --port 8600). Bancos principais só leitura; escrita só em data/app.db e
data/avaliacoes/."""
import contextlib
import os
import sys
import threading
import uuid
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as ErroHTTP

from api import dados, guardado, link as L, trabalhos

RAIZ = dados.RAIZ
os.chdir(RAIZ)  # avaliar.py, agent.py e pipeline.py usam caminhos relativos ("data/...")
sys.path.insert(0, RAIZ) if RAIZ not in sys.path else None
DIST = Path(RAIZ, "web", "dist")
LIMITE = 200 * 1024 * 1024  # mesmo teto do avaliar.py
MODOS = ("analisar", "recomendar", "gerar_criativo")


class Resposta(JSONResponse):
    def render(self, content):
        return super().render(dados.limpar(content))


@contextlib.asynccontextmanager
async def ao_subir(_):
    threading.Thread(target=dados.aquecer, daemon=True).start()  # ranking do YouTube, índice da busca e médias
    yield


app = FastAPI(title="Pauta Impulso", default_response_class=Resposta, lifespan=ao_subir)
app.add_middleware(CORSMiddleware, allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?", allow_methods=["*"],
                   allow_headers=["*"])

if SENHA := os.getenv("SITE_SENHA"):  # deploy público: o navegador pede a senha (HTTP Basic); local fica sem
    import base64
    import secrets
    from fastapi.responses import Response

    @app.middleware("http")
    async def pede_senha(req: Request, seguir):
        try:
            dada = base64.b64decode(req.headers.get("authorization", "")[6:]).decode().partition(":")[2]
        except Exception:
            dada = ""
        if req.url.path.startswith("/mcp") and req.query_params.get("chave"):  # MCP: claude.ai não deixa pôr header
            dada = req.query_params["chave"]
        if secrets.compare_digest(dada.encode(), SENHA.encode()):
            return await seguir(req)
        return Response("Senha necessária.", 401, {"WWW-Authenticate": 'Basic realm="Fora da Curva", charset="UTF-8"'})
api = APIRouter(prefix="/api")


@app.exception_handler(ErroHTTP)
def erro_http(_, e):
    return Resposta({"erro": str(e.detail)}, status_code=e.status_code)


@app.exception_handler(RequestValidationError)
def erro_parametro(_, e):
    campos = ", ".join(str(x["loc"][-1]) for x in e.errors())
    return Resposta({"erro": f"Parâmetro inválido: {campos}"}, status_code=400)


@app.exception_handler(Exception)
def erro_interno(_, e):
    return Resposta({"erro": f"Erro interno ({type(e).__name__}). Tente de novo."}, status_code=500)


def foco_ok(foco):
    k = str(foco or "A").upper()
    if k not in dados.FOCOS:
        raise HTTPException(400, "O foco deve ser A ou B.")
    return k


def achar(coisa, o_que="post"):
    if coisa is None:
        raise HTTPException(404, f"Não encontramos este {o_que} na base deste foco.")
    return coisa


def um_de(valor, opcoes, nome):
    if valor not in opcoes:
        raise HTTPException(400, f"{nome} deve ser um de: {', '.join(opcoes)}.")
    return valor


# ---------------------------------------------------------------- leitura
@api.get("/saude")
def saude():
    return {"ok": True}


@api.get("/focos")
def focos():
    return dados.focos()


@api.get("/posts")
def posts(foco: str = "A", plataforma: str | None = None, formato: str | None = None, tema: str | None = None,
          porte: str | None = None, so_top: bool = False, com_video: bool = False, q: str | None = None,
          ordem: str = "destaques", offset: int = 0, limit: int = 24):
    um_de(ordem, ("destaques", *dados.ORDENS), "ordem")
    return dados.posts(foco_ok(foco), plataforma, formato, tema, porte, so_top, com_video, q, ordem, max(0, offset),
                       max(1, min(limit, 200)))


@api.get("/posts/{id}")
def post(id: str, foco: str = "A"):
    # sem o id neste foco, vale o do outro (o playbook do Foco B cita posts da base do A); `foco` na resposta é o real
    k = foco_ok(foco)
    return achar(dados.detalhe(k, id) or dados.detalhe("B" if k == "A" else "A", id))


@api.get("/destaques")
def destaques(foco: str = "A", limit: int = 12):
    return dados.destaques(foco_ok(foco), max(1, min(limit, 60)))


@api.get("/busca")
def busca(foco: str = "A", q: str = "", limit: int = 20, so_top: bool = False):
    return dados.busca(foco_ok(foco), q, max(1, min(limit, 100)), so_top) if q.strip() else []


@api.get("/criadores")
def criadores(foco: str = "A", plataforma: str | None = None, porte: str | None = None):
    return dados.criadores(foco_ok(foco), plataforma, porte)


@api.get("/criadores/{id}")
def criador(id: str, foco: str = "A"):
    return achar(dados.criador(foco_ok(foco), id), "criador")


@api.get("/rankings")
def rankings(foco: str = "A", tipo: str = "posts", plataforma: str | None = None, porte: str | None = None,
             metrica: str = "vezes", limit: int = 20):
    um_de(tipo, ("posts", "criadores"), "tipo")
    um_de(metrica, tuple(dados.FMT), "metrica")
    return dados.rankings(foco_ok(foco), tipo, plataforma, porte, metrica, max(1, min(limit, 100)))


@api.get("/comparar")
def comparar(a: str, b: str, foco: str = "A"):
    return achar(dados.comparar(foco_ok(foco), a, b))


@api.get("/padroes")
def padroes(foco: str = "A", plataforma: str | None = None):
    return dados.padroes(foco_ok(foco), plataforma)


@api.get("/ads")
def ads():
    return dados.ads()


@api.get("/viz/esperado-real")
def viz_esperado_real(foco: str = "A", plataforma: str | None = None):
    return dados.esperado_real(foco_ok(foco), plataforma)


@api.get("/viz/temas")
def viz_temas(foco: str = "A", plataforma: str | None = None):
    return dados.temas(foco_ok(foco), plataforma)


@api.get("/viz/anatomia/{id}")
def viz_anatomia(id: str, foco: str = "A"):
    return achar(dados.anatomia(foco_ok(foco), id))


@api.get("/viz/funil")
def viz_funil(foco: str = "B"):
    return dados.funil(foco_ok(foco))


@api.get("/criativos")
def criativos():
    return dados.criativos()


@api.get("/playbook")
def playbook(foco: str = "A"):
    return dados.playbook(foco_ok(foco))


@api.get("/metodo")
def metodo(foco: str = "A"):
    return dados.metodo(foco_ok(foco))


# ---------------------------------------------------------------- avaliar meu post
def _trabalho(tid):
    t = trabalhos.ver(tid)
    if not t:
        raise HTTPException(404, "Não encontramos este pedido. Ele pode ter sido feito antes de o servidor reiniciar.")
    return t


async def _entrada_avaliar(request):
    """multipart (arquivos[] ou arquivos, legenda, foco, plataforma, usar_video) ou JSON só com texto."""
    if "json" in request.headers.get("content-type", ""):
        return [], await request.json()
    form = await request.form(max_files=20)
    enviados = [a for a in form.getlist("arquivos") + form.getlist("arquivos[]") if hasattr(a, "read") and a.filename]
    if any((a.size or 0) > LIMITE for a in enviados):
        raise ValueError("arquivo acima de 200 MB")
    return [(a.filename, await a.read()) for a in enviados], {c: v for c, v in form.items() if isinstance(v, str)}


@api.post("/avaliar")
async def avaliar_post(request: Request):
    import avaliar as A
    # ponytail: o teto vale pelo Content-Length e pelo tamanho de cada arquivo; envio em pedaços sem Content-Length só é
    # barrado depois de recebido. Para expor na internet, pôr o limite no proxy.
    if int(request.headers.get("content-length") or 0) > LIMITE + 1024 * 1024:
        raise HTTPException(413, "Envio acima de 200 MB.")
    try:
        arquivos, campos = await _entrada_avaliar(request)
        legenda = str(campos.get("legenda") or "").strip()
        foco, plataforma = str(campos.get("foco") or "A").upper(), str(campos.get("plataforma") or "instagram").lower()
        usar_video = str(campos.get("usar_video") or "").lower() in ("1", "true", "on", "sim")
        link = str(campos.get("link") or "").strip()
        if link:
            if not L.ler(link):
                raise ValueError("o link precisa ser de um post do Instagram ou de um vídeo do YouTube")
            plataforma = L.ler(link)[0]
        if foco not in dados.FOCOS:
            raise ValueError("foco deve ser A ou B")
        if plataforma not in ("instagram", "youtube"):
            raise ValueError("plataforma deve ser instagram ou youtube")
        if not link and A.separar(arquivos)[0] == "texto" and not legenda:
            raise ValueError("envie um vídeo, imagens ou pelo menos a legenda")
    except ValueError as e:
        raise HTTPException(400, str(e)[:1].upper() + str(e)[1:])
    aid = uuid.uuid4().hex[:12]

    def tarefa(diz):
        nonlocal arquivos, legenda
        if link:
            diz("Baixando o post do link")
            arquivos, legenda_link, _ = L.baixar(link)
            legenda = legenda or legenda_link
        r = A.avaliar(arquivos, legenda, foco, plataforma, usar_video, progresso=diz)
        diz("Guardando no histórico")
        r["medias"] = dados.medias_nota(foco, plataforma)
        r["parecidos"] = [dict(p, post=dados.post_resumo(foco, p.get("video_id"))) for p in r.get("parecidos") or []]
        r["id"] = aid
        thumb = guardado.salvar_avaliacao(aid, legenda, r, arquivos)
        r["thumb"] = f"/midia/avaliacoes/{thumb}" if thumb else None
        return r

    return {"id": trabalhos.criar(tarefa, aid)}  # o mesmo id vale em /avaliar/{id} e em /avaliacoes/{id}


@api.get("/avaliar/{id}")
def avaliar_estado(id: str):
    return _trabalho(id)


@api.get("/avaliacoes")
def avaliacoes():
    return guardado.avaliacoes()


@api.get("/avaliacoes/{id}")
def avaliacao(id: str):
    return achar(guardado.avaliacao(id), "registro no histórico (avaliação)")


# ---------------------------------------------------------------- agente
@api.post("/agente")
def agente(corpo: dict):
    modo, pergunta = corpo.get("modo") or "gerar_criativo", str(corpo.get("pergunta") or "").strip()
    um_de(modo, MODOS, "modo")
    if not pergunta:
        raise HTTPException(400, "Escreva o que você quer pedir ao agente.")
    filtros = {c: v for c, v in (corpo.get("filtros") or {}).items() if v not in (None, "", "todas", "todos")}
    segmento = corpo.get("segmento") if corpo.get("segmento") not in (None, "", "todos") else None

    tid = uuid.uuid4().hex[:12]

    def tarefa(diz):
        diz("Consultando a base e escolhendo referências reais")
        import agent  # import tardio: o grafo só carrega quando alguém pergunta
        diz("Escrevendo e checando (pode levar até 1 minuto)")
        try:
            saida = agent.run(modo, pergunta, segmento, filtros or None)
        except Exception as e:
            if type(e).__name__ == "ValidationError":  # filtro fora do contrato do agente
                raise ValueError("Filtro inválido para o agente (porte, plataforma, pilar, tema ou formato).")
            raise
        ultima = (dados.salvas() or [{}])[0]  # agent.run acabou de gravar em execucoes.jsonl
        mesma = ultima.get("pergunta") == pergunta and ultima.get("modo") == modo
        return dados.resposta_agente(saida, id=tid, em=guardado.agora(), modo=modo, pergunta=pergunta, segmento=segmento,
                                     tentativas=ultima.get("tentativas") if mesma else None,
                                     pendencias=ultima.get("pendencias", "") if mesma else "")

    return {"id": trabalhos.criar(tarefa, tid)}


@api.post("/criativos/video")
def criativo_video(corpo: dict):
    """Gera o Reels do criativo pela Feita (clipes b-roll + texto da marca). Cache por roteiro."""
    criativo = corpo.get("criativo") or {}
    if not str(criativo.get("roteiro") or "").strip():
        raise HTTPException(400, "Criativo sem roteiro.")
    import hashlib

    import render_reels
    nome = "reels_" + hashlib.sha1(criativo["roteiro"].encode()).hexdigest()[:12]
    pronto = os.path.join(render_reels.SAIDA, f"{nome}.mp4")

    def tarefa(diz):
        if not os.path.exists(pronto):
            render_reels.montar_criativo(criativo, nome, progresso=diz)
        return {"url": f"/midia/render/{nome}.mp4"}

    return {"id": trabalhos.criar(tarefa)}


@api.get("/criativos/video/{id}")
def criativo_video_estado(id: str):
    return _trabalho(id)


@api.get("/criativos/videos")
def criativos_videos():
    """Histórico dos Reels já gerados: casa os MP4 em data/render/feita com as pautas (playbook + salvas)."""
    import hashlib

    import render_reels
    vistos, saida = set(), []
    for r in (dados.salvas() or []) + (dados.criativos() or []):  # salvas primeiro: têm id para reabrir a pauta
        for c in r.get("criativos") or r.get("creatives") or []:
            if not c.get("roteiro"):
                continue
            nome = "reels_" + hashlib.sha1(c["roteiro"].encode()).hexdigest()[:12]
            arq = os.path.join(render_reels.SAIDA, f"{nome}.mp4")
            if nome not in vistos and os.path.exists(arq):
                vistos.add(nome)
                saida.append(dict(url=f"/midia/render/{nome}.mp4", titulo=r.get("pergunta") or r.get("pedido") or c.get("gancho", "")[:80],
                                  em=r.get("em"), gancho=c.get("gancho"), id=r.get("id"), modo=r.get("modo")))
    return saida


@api.get("/agente/opcoes")
def agente_opcoes():
    return dados.opcoes_agente()


@api.get("/agente/salvas")
def agente_salvas():
    return dados.salvas()


@api.get("/agente/{id}")
def agente_estado(id: str):
    return _trabalho(id)


# ---------------------------------------------------------------- coleções
SEM_COLECAO = "Coleção não encontrada."


def _cid(id):
    if not id.isdigit():
        raise HTTPException(404, SEM_COLECAO)
    return int(id)


def _colecao(c):
    if c is None:
        raise HTTPException(404, SEM_COLECAO)
    posts_ = [p for p in (dados.post_resumo(c["foco"], i) for i in c["posts"]) if p]
    return dict(c, posts=posts_)


def _post_do_corpo(corpo, post_id=None):
    pid = post_id or (corpo or {}).get("post_id") or (corpo or {}).get("post") or (corpo or {}).get("id")
    if not isinstance(pid, str) or not pid:
        raise HTTPException(400, "Diga qual post (post_id).")
    return pid


@api.get("/colecoes")
def colecoes(foco: str | None = None):
    return [_colecao(c) for c in guardado.colecoes(foco_ok(foco) if foco else None)]


@api.post("/colecoes")
def colecao_criar(corpo: dict, foco: str | None = None):
    nome = str(corpo.get("nome") or "").strip()
    if not nome:
        raise HTTPException(400, "Dê um nome para a coleção.")
    return _colecao(guardado.criar_colecao(nome[:120], str(corpo.get("nota") or "")[:2000], foco_ok(corpo.get("foco") or foco)))


@api.get("/colecoes/{id}")
def colecao(id: str):
    return _colecao(guardado.colecao(_cid(id)))


@api.patch("/colecoes/{id}")
def colecao_editar(id: str, corpo: dict):
    id = _cid(id)
    nome, nota = corpo.get("nome"), corpo.get("nota")
    if nome is not None and not str(nome).strip():
        raise HTTPException(400, "O nome da coleção não pode ficar vazio.")
    return _colecao(guardado.editar_colecao(id, str(nome).strip()[:120] if nome is not None else None,
                                            str(nota)[:2000] if nota is not None else None))


@api.delete("/colecoes/{id}")
def colecao_apagar(id: str):
    if not guardado.apagar_colecao(_cid(id)):
        raise HTTPException(404, SEM_COLECAO)
    return {"ok": True}


@api.post("/colecoes/{id}/posts")
def colecao_por_post(id: str, corpo: dict):
    id = _cid(id)
    c = _colecao(guardado.colecao(id))
    pid = _post_do_corpo(corpo)
    achar(dados.linha(c["foco"], pid))  # só entra post que existe na base do foco da coleção
    return _colecao(guardado.por_post(id, pid))


@api.delete("/colecoes/{id}/posts")
@api.delete("/colecoes/{id}/posts/{post_id}")
def colecao_tirar_post(id: str, post_id: str | None = None, corpo: dict | None = None):
    id = _cid(id)
    _colecao(guardado.colecao(id))
    return _colecao(guardado.tirar_post(id, _post_do_corpo(corpo, post_id)))


@api.api_route("/{resto:path}", methods=["GET", "POST", "PATCH", "DELETE", "PUT"], include_in_schema=False)
def api_sem_rota(resto: str):
    raise HTTPException(404, "Esta rota não existe na API.")


# ---------------------------------------------------------------- arquivos: mídia e o site compilado
app.include_router(api)
for url, pasta in [("/midia/a", dados.FOCOS["A"]["midia"]), ("/midia/b", dados.FOCOS["B"]["midia"]),
                   ("/midia/thumbs", dados.THUMBS), ("/midia/avaliacoes", guardado.pasta_avaliacoes()),
                   ("/midia/render", os.path.join(dados.DATA, "render", "feita"))]:
    os.makedirs(pasta, exist_ok=True) if "avaliacoes" in url else None
    app.mount(url, StaticFiles(directory=pasta, check_dir=False))


@app.get("/{caminho:path}", include_in_schema=False)
def site(caminho: str):
    """O site compilado (web/dist), com volta para index.html nas rotas do React."""
    if not DIST.is_dir():
        raise HTTPException(404, "O site ainda não foi compilado: cd web && npm install && npm run build")
    arquivo = (DIST / caminho).resolve()
    if caminho and arquivo.is_file() and arquivo.is_relative_to(DIST.resolve()):
        return FileResponse(arquivo)
    return FileResponse(DIST / "index.html")
