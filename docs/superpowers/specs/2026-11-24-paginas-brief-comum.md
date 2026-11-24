# Brief comum dos agentes de página (onda 2)

Você constrói páginas do front React da Pauta Impulso, em `/home/eduardo/fellow/Stone/web`. Outros quatro agentes estão construindo OUTRAS páginas ao mesmo tempo. Não peça confirmação a ninguém: construa, verifique com capturas de tela, itere e devolva um relatório.

## Leia antes (obrigatório, nesta ordem)
1. `/home/eduardo/fellow/Stone/docs/superpowers/specs/2026-11-24-pauta-react-design.md`: escolhas de design do usuário, sistema visual, rotas, contrato da API.
2. `/home/eduardo/fellow/Stone/web/README.md`: como rodar, hooks, componentes compartilhados com exemplos, regras.
3. `/home/eduardo/fellow/Stone/api/CONTRATO_DESVIOS.md`: o que a API real devolve de diferente/a mais e as unidades (er e frequências são frações; `vezes` e `lift` são multiplicadores; `ctr` dos Ads vem em %; `porte` vem cru, use `nomePorte`).
4. `web/src/api/tipos.ts`, `web/src/api/hooks.ts`, `web/src/componentes/index.ts` e a vitrine `web/src/paginas/_vitrine` (exemplos de uso de cada componente). Olhe também as capturas `data/screens/react_fundacao_api_mosaico_A.png`, `react_fundacao_api_painel_A.png`, `react_fundacao_vitrine_claro_1400.png` para absorver o visual já estabelecido.

## Regras de convivência
- Edite SOMENTE as pastas de página que são suas (listadas na sua tarefa), dentro de `web/src/paginas/`. Não edite `web/src/componentes/**`, `web/src/styles/**`, `web/src/api/**`, `web/src/contexto/**`, `App.tsx`, `package.json`, nem nada fora de `web/`. Se faltar algo num componente compartilhado, crie um componente local na sua pasta e relate. Se precisar de uma rota a mais na API ou de um campo que não existe, NÃO edite a API: contorne e relate.
- CSS da sua página fica num arquivo `.css` na sua pasta, com classes prefixadas pelo nome da página; cores e fontes só por variáveis de `tokens.css`. Sem bibliotecas novas (já existem: react-router-dom, @tanstack/react-query, motion, d3-scale, d3-hierarchy, d3-shape, html-to-image).
- A API real está no ar em `http://localhost:8600` (não a derrube, não a reinicie). Suba o SEU servidor de dev na porta indicada na sua tarefa: `cd web && npx vite --port <PORTA> --strictPort` (o proxy de `/api` e `/midia` já aponta para a 8600). Encerre só o seu processo ao terminar. Não use 5173, 8501 nem 8600.
- `npx tsc --noEmit` pode mostrar erros de páginas de outros agentes em construção: garanta zero erros NAS SUAS pastas.
- Teste com dados REAIS (API) nos dois focos (A e B), nos dois temas (claro e escuro), em 1400px e 400px. O foco e o tema ficam em `localStorage` (`pauta.foco`, `pauta.tema`): nas capturas, defina-os antes de carregar a página. Playwright: `/home/eduardo/fellow/Stone/.venv/bin/python`, `p.chromium.launch(channel="chrome")`; veja `web/scripts/capturas.py` como exemplo. Salve as capturas em `/home/eduardo/fellow/Stone/data/screens/react_<pagina>_*.png`, OLHE cada uma e faça ao menos duas rodadas de correção visual. Confira o console do navegador: zero erros.

## Barra de qualidade (o usuário rejeitou a versão anterior por ser "simples, sem destaque e com cara de IA")
- Direção: app de criador. Mídia em primeiro plano, pouco texto, hierarquia forte, contraste de escala (números enormes em Anton ao lado de texto pequeno), lima em BLOCOS (no máximo um bloco lima por dobra), identidade de comércio (use `Comprovante`, `Etiqueta`, `Carimbo` onde fizer sentido, sem exagero), cantos mistos (mídia/botões arredondados; dados retos), SEM ícones e sem emoji (tipografia e cor), dados que se desenham ao entrar na tela (use `useEntrou`, `NumeroConta`, `motion`), cards que levantam no hover.
- Proibido: grade de cartões idênticos sem hierarquia; rótulo minúsculo em caixa alta sobre toda seção; gradiente em texto; vidro fosco decorativo; borda colorida grossa de um lado só; tabelas cruas como visual principal (tabela só em "ver os números"); nomes de campos crus (`tipo_hook`); JSON na tela.
- Toda página tem os estados: carregando (`Esqueleto`), vazio (`Vazio`, com o que fazer), erro (`Erro` com tentar de novo). Nenhum número inventado: tudo vem da API. Texto em português do Brasil, direto e neutro, sem travessões, sem frases de efeito vazias.
- Acessível: teclado, foco visível, `alt`, contraste 4,5:1 nos dois temas, `prefers-reduced-motion`. O conteúdo aparece mesmo sem animação.
- Abrir um post: use `useAbrirPost()`/`PostCard` (o `PainelPost` já está montado no shell e abre com `?post=ID` em qualquer rota).

## Relatório final (curto)
O que cada página tem; o que foi verificado por captura (arquivos); componentes locais criados; o que faltou na API ou nos componentes compartilhados; pendências.
