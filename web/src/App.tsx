// Rotas. Cada página é carregada sob demanda e mora em src/paginas/<pasta>/index.tsx (export default).
// "/" (porta de entrada) fica fora do shell; todo o resto usa o <AppShell> (barra lateral + <PainelPost>).
import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import { AppShell, Esqueleto, TituloPagina, Vazio, Botao } from "./componentes";

const Entrada = lazy(() => import("./paginas/entrada"));
const Inicio = lazy(() => import("./paginas/inicio"));
const Destaques = lazy(() => import("./paginas/destaques"));
const Catalogo = lazy(() => import("./paginas/catalogo"));
const Busca = lazy(() => import("./paginas/busca"));
const Rankings = lazy(() => import("./paginas/rankings"));
const Criador = lazy(() => import("./paginas/criador"));
const Comparar = lazy(() => import("./paginas/comparar"));
const Padroes = lazy(() => import("./paginas/padroes"));
const Mapa = lazy(() => import("./paginas/mapa"));
const Metodo = lazy(() => import("./paginas/metodo"));
const Avaliar = lazy(() => import("./paginas/avaliar"));
const Criar = lazy(() => import("./paginas/criar"));
const Colecoes = lazy(() => import("./paginas/colecoes"));
const Playbook = lazy(() => import("./paginas/playbook"));
const Vitrine = lazy(() => import("./paginas/_vitrine"));

function NaoEncontrada() {
  return (
    <>
      <TituloPagina titulo="Página" grifo="não encontrada" />
      <Vazio titulo="Esse endereço não existe" marca="404" acao={<Botao para="/inicio">Ir para o início</Botao>}>Confira o link ou volte para o início.</Vazio>
    </>
  );
}

export default function App() {
  return (
    <Suspense fallback={<div style={{ padding: 48 }}><Esqueleto altura={320} /></div>}>
      <Routes>
        <Route path="/" element={<Entrada />} />
        <Route element={<AppShell />}>
          <Route path="/inicio" element={<Inicio />} />
          <Route path="/destaques" element={<Destaques />} />
          <Route path="/catalogo" element={<Catalogo />} />
          <Route path="/busca" element={<Busca />} />
          <Route path="/rankings" element={<Rankings />} />
          <Route path="/criadores/:id" element={<Criador />} />
          <Route path="/comparar" element={<Comparar />} />
          <Route path="/padroes" element={<Padroes />} />
          <Route path="/mapa" element={<Mapa />} />
          <Route path="/metodo" element={<Metodo />} />
          {/* a mesma página atende as duas rotas: use useLocation().pathname / useParams().id para decidir o que mostrar */}
          <Route path="/avaliar" element={<Avaliar />} />
          <Route path="/avaliar/historico" element={<Avaliar />} />
          <Route path="/criar" element={<Criar />} />
          <Route path="/criar/historico" element={<Criar />} />
          <Route path="/colecoes" element={<Colecoes />} />
          <Route path="/colecoes/:id" element={<Colecoes />} />
          <Route path="/playbook" element={<Playbook />} />
          <Route path="/_vitrine" element={<Vitrine />} />
          <Route path="*" element={<NaoEncontrada />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
