"""Teste do MCP por HTTP (site + MCP no mesmo processo, servir.py). Uso: .venv/bin/python test_mcp_http.py URL SENHA
Ex.: .venv/bin/python test_mcp_http.py https://fdc.56-124-7-252.sslip.io/mcp <senha>"""
import asyncio, base64, sys
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client


async def main(url, senha):
    assert httpx.post(url, json={}).status_code == 401, "sem senha deveria dar 401"
    for http in (create_mcp_http_client(headers={"Authorization": "Basic " + base64.b64encode(f"x:{senha}".encode()).decode()}), None):
        u = url if http else f"{url}?chave={senha}"  # header (Claude Code) e ?chave= (claude.ai)
        async with streamable_http_client(u, http_client=http) as (r, w), ClientSession(r, w) as s:
            await s.initialize()
            nomes = [t.name for t in (await s.list_tools()).tools]
            res = await s.call_tool("destaques", {"foco": "A", "limit": 2})
            assert not res.is_error and "briefing_criativo" in nomes, (res, nomes)
            print("ok", "header" if http else "?chave=", len(nomes), "tools")


asyncio.run(main(sys.argv[1], sys.argv[2]))
