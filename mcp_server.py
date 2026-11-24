"""Servidor MCP do Fora da Curva (case Stone). Rode: .venv/bin/python mcp_server.py (stdio).

Tudo aqui lê a base local e não gasta crédito de LLM: quem redige os criativos é o próprio cliente (Claude),
a partir do briefing que `briefing_criativo` monta com os achados, selos e posts de referência da aplicação.
`conteudo_mpe` (redação no servidor, gasta crédito da Feita) só aparece com MCP_PERMITE_LLM=1.

Claude Code: claude mcp add fora-da-curva -- /caminho/.venv/bin/python /caminho/mcp_server.py
"""
import json
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # agent/pipeline usam caminhos relativos ("data/...")
sys.path.insert(0, os.getcwd())

from fastapi import HTTPException  # noqa: E402
from mcp.server.mcpserver import MCPServer  # noqa: E402
from mcp.server.mcpserver.exceptions import ToolError  # noqa: E402

import agent as AG  # noqa: E402
from api import app as API, dados  # noqa: E402

mcp = MCPServer("fora-da-curva", instructions=(
    "Base de posts de alto engajamento para micro e pequenos empreendedores (MPE). Foco A: conteúdo que engaja donos "
    "de pequeno negócio (público do Impulso Stone). Foco B: como o pequeno negócio engaja o cliente final. "
    "Para criar posts, chame briefing_criativo e escreva os criativos seguindo o briefing ao pé da letra."))


def _ok(fn, *a):
    """Chama a função da API; erro de parâmetro vira mensagem legível para o modelo. NaN/inf viram null."""
    try:
        return dados.limpar(fn(*a))
    except HTTPException as e:
        raise ToolError(str(e.detail)) from None


# ---------------------------------------------------------------- consulta (mesmas funções da API do site)
@mcp.tool()
def focos() -> list:
    """Os dois focos da análise (A: Impulso -> empreendedor; B: negócio -> cliente) com números de cada um."""
    return _ok(API.focos)


@mcp.tool()
def destaques(foco: str = "A", limit: int = 12) -> list:
    """Posts que mais passaram do engajamento esperado para o perfil, um por criador, com o porquê."""
    return _ok(API.destaques, foco, limit)


@mcp.tool()
def buscar_posts(q: str, foco: str = "A", limit: int = 20, so_top: bool = False) -> list:
    """Busca posts por ideia/tema em linguagem natural (ex.: "precificação de marmita"). so_top=True só alto desempenho."""
    return _ok(API.busca, foco, q, limit, so_top)


@mcp.tool()
def post(id: str, foco: str = "A") -> dict:
    """Detalhe de um post: métricas, quanto passou do esperado, gancho, categorias e leitura do vídeo."""
    return _ok(API.post, id, foco)


@mcp.tool()
def padroes(foco: str = "A", plataforma: str | None = None) -> dict:
    """Padrões do conteúdo de alto desempenho (lift top x resto) com selo: confirmado, contradito, só mercado.
    Cada padrão traz até 3 exemplos (id e canal); use post(id) para o detalhe."""
    d = _ok(API.padroes, foco, plataforma)
    for i in d.get("itens", []):  # ponytail: exemplos completos são ~80 KB; o modelo pede o detalhe com post(id)
        i["exemplos"] = [{k: x.get(k) for k in ("id", "canal", "titulo") if k in x} for x in (i.get("exemplos") or [])[:3]]
    return d


@mcp.tool()
def playbook(foco: str = "A") -> dict:
    """Playbook editorial gerado a partir da análise (recomendações práticas com evidência)."""
    return _ok(API.playbook, foco)


@mcp.tool()
def criadores(foco: str = "A", plataforma: str | None = None, porte: str | None = None) -> list:
    """Criadores/perfis da base com desempenho (efeito do criador, posts no top, tema e formato principais)."""
    return _ok(API.criadores, foco, plataforma, porte)


# ---------------------------------------------------------------- criativos: o cliente redige
CHECAGEM = """Antes de entregar, confira cada criativo (é a mesma checagem que a aplicação faz):
- gancho com força >= {hook} de 10 (mediana do gancho dos posts de alto desempenho neste recorte);
- chamada para ação clara;
- nada genérico (nota < 6 de 10 em "serve para qualquer público"): fale com um nicho, uma data ou uma dor real;
- convida o empreendedor a participar (contar, perguntar, responder);
- tom próximo, acolhedor, educativo e sem jargão;
- inspirado_em só com video_ids da lista de referências.
Se algum item falhar, reescreva o criativo antes de responder."""


@mcp.tool()
def briefing_criativo(pedido: str, mode: str = "gerar_criativo", segment: str | None = None,
                      filters: dict | None = None) -> dict:
    """Monta o briefing completo para VOCÊ (o modelo cliente) escrever os criativos, sem gastar crédito no servidor.

    pedido: o que criar (ex.: "Reels sobre aceitar Pix na maquininha").
    mode: gerar_criativo (3 criativos) | recomendar (3-5 recomendações) | analisar (resposta sem criativos).
    segment: alimentação | beleza | varejo | serviços (opcional).
    filters: {"porte": "micro|medio|grande", "plataforma": "youtube|instagram", "pilar": str,
              "periodo_dias": int, "tema": str, "formato": str} (opcional).
    Devolve prompt (siga-o), formato_resposta (JSON schema), checagem e as referências usadas.
    """
    e = AG.Entrada(mode=mode, query=pedido, segment=segment, filters=AG.Filtros(**(filters or {})))
    achados, refs, n_top, hook_ref, relaxados = AG.recuperar(e)
    s = dict(entrada=e, achados=achados, refs=refs, n_top=n_top, relaxados=relaxados)
    hook = f"{hook_ref:.0f}" if hook_ref == hook_ref else "7"
    return dados.limpar(dict(
        prompt=AG.prompt_redacao(s) + "\n\nResponda no formato_resposta (JSON).",
        formato_resposta=AG.Redacao.model_json_schema(),
        checagem=CHECAGEM.format(hook=hook),
        posts_no_top=n_top, filtros_relaxados=relaxados,
        referencias=[r.model_dump() for r in refs]))


@mcp.prompt()
def criar_criativos(pedido: str, segmento: str = "") -> str:
    """Cria 3 criativos para o Instagram do Impulso Stone com base nos dados do Fora da Curva."""
    b = briefing_criativo(pedido, segment=segmento or None)
    return f"""{b['prompt']}

{b['checagem']}

Formato da resposta (JSON schema):
{json.dumps(b['formato_resposta'], ensure_ascii=False)}"""


if os.getenv("MCP_PERMITE_LLM") == "1":  # gasta crédito da Feita (deepseek) no servidor
    @mcp.tool()
    def conteudo_mpe(mode: str, query: str, segment: str | None = None, filters: dict | None = None) -> dict:
        """Igual ao briefing_criativo, mas o servidor redige e checa (LLM da aplicação). Gasta crédito."""
        return AG.run(mode, query, segment, filters)


if __name__ == "__main__":
    mcp.run()
