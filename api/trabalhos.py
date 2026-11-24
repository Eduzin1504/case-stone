"""Trabalhos em segundo plano (threads) para /avaliar e /agente, guardando as etapas do progresso."""
import threading
import uuid

# ponytail: trabalhos só na memória deste processo (somem ao reiniciar; os resultados do /avaliar ficam no histórico).
# Com mais de um worker do uvicorn, trocar por uma tabela em data/app.db.
_trabalhos = {}
MAXIMO = 200


def criar(fn, tid=None):
    """Roda fn(progresso) numa thread e devolve o id. ValueError vira mensagem para o usuário."""
    tid = tid or uuid.uuid4().hex[:12]
    t = _trabalhos[tid] = dict(estado="rodando", etapas=[], resultado=None, erro=None)
    while len(_trabalhos) > MAXIMO:
        _trabalhos.pop(next(iter(_trabalhos)))

    def rodar():
        try:
            t["resultado"] = fn(t["etapas"].append)
            t["estado"] = "pronto"
        except ValueError as e:
            t["erro"], t["estado"] = str(e), "erro"
        except Exception as e:  # rede, crédito ou API do modelo fora
            t["erro"], t["estado"] = f"Não deu para terminar agora ({type(e).__name__}: {str(e)[:300]})", "erro"

    threading.Thread(target=rodar, daemon=True).start()
    return tid


def ver(tid):
    return _trabalhos.get(tid)
