"""O que o site grava: coleções e histórico de avaliações, em data/app.db (SQLite próprio) e data/avaliacoes/ (miniaturas).
É a única escrita da API. PAUTA_APP_DB e PAUTA_AVALIACOES trocam os caminhos (usado nos testes)."""
import contextlib
import datetime
import json
import os
import sqlite3
import subprocess
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO = {".mp4", ".mov", ".webm"}
IMAGEM = {".jpg", ".jpeg", ".png", ".webp"}
ESQUEMA = """
create table if not exists colecoes (id integer primary key autoincrement, nome text not null, nota text not null default '',
  foco text not null, criada_em text not null);
create table if not exists colecao_posts (colecao_id integer not null, post_id text not null, adicionado_em text not null,
  primary key (colecao_id, post_id));
create table if not exists avaliacoes (id text primary key, criada_em text not null, foco text, plataforma text, legenda text,
  nota integer, metodo text, thumb text, resultado text not null);
"""


def caminho_db():
    return os.getenv("PAUTA_APP_DB") or f"{RAIZ}/data/app.db"


def pasta_avaliacoes():
    return os.getenv("PAUTA_AVALIACOES") or f"{RAIZ}/data/avaliacoes"


@contextlib.contextmanager
def banco():
    os.makedirs(os.path.dirname(caminho_db()), exist_ok=True)
    c = sqlite3.connect(caminho_db(), timeout=10)
    c.row_factory = sqlite3.Row
    c.executescript(ESQUEMA)
    try:
        yield c
        c.commit()
    finally:
        c.close()


def agora():
    return datetime.datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------- coleções (posts = lista de ids; a API resolve)
def _colecao(c, linha):
    ids = [r[0] for r in c.execute("select post_id from colecao_posts where colecao_id = ? order by adicionado_em, rowid", (linha["id"],))]
    return dict(linha, id=str(linha["id"]), posts=ids)  # id em texto: é como o front compara e monta a rota


def colecoes(foco=None):
    with banco() as c:
        linhas = c.execute("select * from colecoes where ? is null or foco = ? order by id desc", (foco, foco)).fetchall()
        return [_colecao(c, l) for l in linhas]


def colecao(cid):
    with banco() as c:
        l = c.execute("select * from colecoes where id = ?", (cid,)).fetchone()
        return _colecao(c, l) if l else None


def criar_colecao(nome, nota, foco):
    with banco() as c:
        cid = c.execute("insert into colecoes (nome, nota, foco, criada_em) values (?, ?, ?, ?)", (nome, nota, foco, agora())).lastrowid
    return colecao(cid)


def editar_colecao(cid, nome=None, nota=None):
    with banco() as c:
        c.execute("update colecoes set nome = coalesce(?, nome), nota = coalesce(?, nota) where id = ?", (nome, nota, cid))
    return colecao(cid)


def apagar_colecao(cid):
    with banco() as c:
        c.execute("delete from colecao_posts where colecao_id = ?", (cid,))
        return c.execute("delete from colecoes where id = ?", (cid,)).rowcount > 0


def por_post(cid, post_id):
    with banco() as c:
        c.execute("insert or ignore into colecao_posts values (?, ?, ?)", (cid, post_id, agora()))
    return colecao(cid)


def tirar_post(cid, post_id):
    with banco() as c:
        c.execute("delete from colecao_posts where colecao_id = ? and post_id = ?", (cid, post_id))
    return colecao(cid)


# ---------------------------------------------------------------- histórico de avaliações
def miniatura(aid, arquivos):
    """Miniatura do que foi enviado (1ª imagem, ou um quadro do início do vídeo) -> nome do arquivo, ou None.
    O nome que o usuário deu ao arquivo só serve para saber a extensão; o caminho usa o id gerado aqui."""
    if not arquivos:
        return None
    ext = os.path.splitext(arquivos[0][0])[1].lower()
    destino = f"{pasta_avaliacoes()}/{aid}.jpg"
    try:
        from PIL import Image
        os.makedirs(pasta_avaliacoes(), exist_ok=True)
        with tempfile.TemporaryDirectory() as d:
            origem = f"{d}/entrada{ext if ext in VIDEO | IMAGEM else '.bin'}"
            open(origem, "wb").write(arquivos[0][1])
            if ext in VIDEO:
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "0.5", "-i", origem, "-frames:v", "1", f"{d}/quadro.jpg"],
                               capture_output=True, timeout=60)
                origem = f"{d}/quadro.jpg"
            im = Image.open(origem).convert("RGB")
            im.thumbnail((400, 800))
            im.save(destino, "JPEG", quality=80)
        return f"{aid}.jpg"
    except Exception:
        return None


def salvar_avaliacao(aid, legenda, resultado, arquivos):
    thumb = miniatura(aid, arquivos)
    with banco() as c:
        c.execute("insert or replace into avaliacoes values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (aid, agora(), resultado.get("foco"), resultado.get("plataforma"), legenda, resultado.get("nota"),
                   resultado.get("metodo"), thumb, json.dumps(resultado, ensure_ascii=False, default=str)))
    return thumb


def _avaliacao(l, completo=False):
    d = dict(l)
    resultado = json.loads(d.pop("resultado"))
    d["thumb"] = f"/midia/avaliacoes/{d['thumb']}" if d["thumb"] else None
    d["estado"] = "pronto"  # só avaliação terminada entra no histórico
    return dict(d, resultado=resultado) if completo else d


def avaliacoes():
    with banco() as c:
        return [_avaliacao(l) for l in c.execute("select * from avaliacoes order by criada_em desc")]


def avaliacao(aid):
    with banco() as c:
        l = c.execute("select * from avaliacoes where id = ?", (aid,)).fetchone()
        return _avaliacao(l, completo=True) if l else None
