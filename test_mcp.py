"""Teste do servidor MCP por stdio (sem rede, sem crédito): .venv/bin/python test_mcp.py"""
import asyncio, json, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    p = StdioServerParameters(command=".venv/bin/python", args=["mcp_server.py"])
    async with stdio_client(p) as (r, w), ClientSession(r, w) as s:
        await s.initialize()
        t = await s.list_tools(); print("tools:", [x.name for x in t.tools])
        pr = await s.list_prompts(); print("prompts:", [x.name for x in pr.prompts])
        def txt(res): return res.content[0].text if res.content else str(res.structured_content)
        for nome, args in [("focos", {}), ("destaques", {"foco": "A", "limit": 3}), ("buscar_posts", {"q": "precificação", "limit": 3}),
                           ("padroes", {"foco": "A"}), ("playbook", {"foco": "A"})]:
            res = await s.call_tool(nome, args)
            print(nome, "erro" if res.is_error else "ok", len(txt(res)), txt(res)[:120].replace("\n", " "))
        res = await s.call_tool("briefing_criativo", {"pedido": "Reels sobre aceitar Pix na maquininha", "segment": "alimentação"})
        b = json.loads(txt(res)); print("briefing:", "erro" if res.is_error else "ok", list(b), len(b["prompt"]), "chars,", len(b["referencias"]), "refs")
        print(b["checagem"].splitlines()[1])
        g = await s.get_prompt("criar_criativos", {"pedido": "carrossel sobre precificação para confeitaria"})
        print("prompt criar_criativos:", len(g.messages[0].content.text), "chars")
        res = await s.call_tool("destaques", {"foco": "Z"}); print("foco inválido ->", res.is_error, txt(res)[:80])
asyncio.run(main())
