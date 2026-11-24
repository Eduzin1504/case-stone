"""Servidor MCP do case Stone. Rode: python mcp_server.py (stdio)."""
from mcp.server.mcpserver import MCPServer

from agent import run

mcp = MCPServer("stone-conteudo-mpe")


@mcp.tool()
def conteudo_mpe(mode: str, query: str, segment: str | None = None, filters: dict | None = None) -> dict:
    """Analisa publicações de alto engajamento para micro e pequenos empreendedores e gera recomendações/criativos.

    mode: analisar | recomendar | gerar_criativo
    query: pergunta ou objetivo
    segment: alimentação | beleza | varejo | serviços (opcional)
    filters: {"porte": "pequeno|medio|grande", "periodo_dias": int, "tema": str, "formato": str} (opcional)
    Retorna findings, reference_posts, creatives (com inspirado_em), confidence_flag e explanation.
    """
    return run(mode, query, segment, filters)


if __name__ == "__main__":
    mcp.run()
