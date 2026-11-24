"""Site + MCP por HTTP num processo só (VPS): uvicorn servir:app --port 7860. MCP em /mcp (streamable HTTP).

Mesma senha do site (SITE_SENHA): header "Authorization: Basic ..." ou ?chave=<senha> na URL do MCP (para clientes,
como o claude.ai, que não deixam pôr header). Local, sem SITE_SENHA, fica aberto como o site.
"""
import contextlib

from mcp.server.transport_security import TransportSecuritySettings

import mcp_server
from api.app import app

# ponytail: stateless = sem sessão em memória; um processo, sem fila. O Host público passa (a senha é o controle).
_mcp = mcp_server.mcp.streamable_http_app(
    stateless_http=True, transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False))
app.router.routes.insert(0, _mcp.routes[0])  # rota /mcp antes do catch-all do site
_ciclo_site = app.router.lifespan_context


@contextlib.asynccontextmanager
async def _ciclo(a):
    async with _ciclo_site(a), mcp_server.mcp.session_manager.run():
        yield

app.router.lifespan_context = _ciclo
