"""Capturas da fundação (vitrine, shell, painel, ficha) nos dois temas, em 1400px e 400px.
Precisa do dev server no ar em modo exemplos:  VITE_EXEMPLOS=1 npm run dev
    ../.venv/bin/python scripts/capturas.py [filtro]
Salva em data/screens/react_fundacao_*.png."""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5173"
SAIDA = "/home/eduardo/fellow/Stone/data/screens/react_fundacao_"
filtro = sys.argv[1] if len(sys.argv) > 1 else ""
erros = []


def pagina(b, larg, tema, foco="A", alt=900, reduzido=False):
    ctx = b.new_context(viewport={"width": larg, "height": alt}, device_scale_factor=1, reduced_motion="reduce" if reduzido else "no-preference")
    ctx.add_init_script(f"localStorage.setItem('pauta.tema','{tema}');localStorage.setItem('pauta.foco','{foco}')")
    p = ctx.new_page()
    p.on("console", lambda m: m.type == "error" and erros.append(m.text[:300]))
    p.on("pageerror", lambda e: erros.append(str(e)[:300]))
    return p


def ir(p, rota, espera=1600):
    p.goto(BASE + rota, wait_until="networkidle")
    p.wait_for_timeout(espera)


def foto(p, nome, cheia=False):
    if filtro and filtro not in nome:
        return
    if cheia:  # rola até o fim para disparar as animações de entrada e as imagens preguiçosas
        h = p.evaluate("document.documentElement.scrollHeight")
        for y in range(0, h, 600):
            p.evaluate(f"window.scrollTo(0,{y})")
            p.wait_for_timeout(120)
        p.evaluate("window.scrollTo(0,0)")
        p.wait_for_timeout(900)
    p.screenshot(path=f"{SAIDA}{nome}.png", full_page=cheia)
    print("ok", nome)


with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome")
    for tema in ("claro", "escuro"):
        for larg in (1400, 400):
            p = pagina(b, larg, tema)
            ir(p, "/_vitrine")
            foto(p, f"vitrine_{tema}_{larg}", cheia=True)
            ir(p, "/inicio")
            foto(p, f"shell_{tema}_{larg}")
            if larg == 400:
                p.get_by_role("button", name="Menu").click()
                p.wait_for_timeout(500)
                foto(p, f"gaveta_{tema}_{larg}")
            ir(p, "/_vitrine?post=DkpnGeH5IRg", 2200)
            foto(p, f"painel_{tema}_{larg}")
            p.locator(".painel-rolagem").evaluate("e => e.scrollTo(0, 620)")
            p.wait_for_timeout(500)
            foto(p, f"painel_meio_{tema}_{larg}")
            p.locator(".painel-rolagem").evaluate("e => e.scrollTo(0, e.scrollHeight)")
            p.wait_for_timeout(500)
            foto(p, f"painel_fim_{tema}_{larg}")
            p.context.close()
        # ficha de hover, card levantado e clique que abre o painel
        p = pagina(b, 1400, tema)
        ir(p, "/_vitrine")
        card = p.locator(".mosaico .pc--mosaico").nth(2)
        card.scroll_into_view_if_needed()
        p.wait_for_timeout(500)
        card.hover()
        p.wait_for_timeout(700)
        foto(p, f"ficha_{tema}_1400")
        card.click()
        p.wait_for_timeout(150)
        foto(p, f"transicao_{tema}_1400")
        p.wait_for_timeout(1500)
        foto(p, f"painel_clique_{tema}_1400")
        assert "post=" in p.url, p.url
        p.keyboard.press("Escape")
        p.wait_for_timeout(700)
        assert "post=" not in p.url, "Esc não fechou o painel"
        # coleção: abrir a lista e salvar
        p.get_by_role("button", name="Salvar em coleção").first.scroll_into_view_if_needed()
        p.get_by_role("button", name="Salvar em coleção").first.click()
        p.wait_for_timeout(500)
        p.get_by_role("checkbox").first.click()
        p.wait_for_timeout(900)
        foto(p, f"colecao_{tema}_1400")
        p.context.close()
    # porta de entrada, foco B, carrossel no painel, foco de teclado
    p = pagina(b, 1400, "claro")
    ir(p, "/")
    foto(p, "entrada_claro_1400")
    ir(p, "/_vitrine?post=De2C0bCls1K", 2200)
    foto(p, "painel_carrossel_claro_1400")
    p.context.close()
    p = pagina(b, 1400, "escuro", foco="B")
    ir(p, "/_vitrine")
    foto(p, "vitrine_focoB_escuro_1400", cheia=True)
    p.context.close()
    p = pagina(b, 1400, "claro", reduzido=True)
    ir(p, "/_vitrine", 600)
    for _ in range(9):
        p.keyboard.press("Tab")
    foto(p, "foco_teclado_claro_1400")
    p.context.close()
    # sem foco escolhido → volta para a porta de entrada
    ctx = b.new_context()
    p = ctx.new_page()
    p.goto(BASE + "/catalogo", wait_until="networkidle")
    assert p.url.rstrip("/") == BASE, f"sem foco deveria redirecionar para /, foi {p.url}"
    print("ok redireciona sem foco")
    b.close()

print("\nERROS DE CONSOLE:" if erros else "\nsem erros de console")
for e in dict.fromkeys(erros):
    print(" -", e)
