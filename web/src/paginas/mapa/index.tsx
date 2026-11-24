// /mapa: quatro visualizações, uma por aba (?v=esperado|temas|anatomia|funil).
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Seg, TituloPagina } from "../../componentes";
import { useFoco } from "../../contexto/Foco";
import { nomePlataforma } from "../../util/formato";
import { Anatomia } from "./Anatomia";
import { EsperadoReal } from "./EsperadoReal";
import { Funil } from "./Funil";
import { Temas } from "./Temas";
import "./mapa.css";

const ABAS = [
  { valor: "esperado", rotulo: "Esperado × real" },
  { valor: "temas", rotulo: "Mapa de temas" },
  { valor: "anatomia", rotulo: "Anatomia de um post" },
  { valor: "funil", rotulo: "Funil curtida → pedido" },
];

export default function Mapa() {
  const { info } = useFoco();
  const [params, setParams] = useSearchParams();
  const v = ABAS.some((a) => a.valor === params.get("v")) ? params.get("v")! : "esperado";
  const trocar = (valor: string) => setParams((p) => { const q = new URLSearchParams(p); q.set("v", valor); return q; }, { replace: true });

  const comDados = Object.entries(info?.base.por_plataforma ?? {}).filter(([, n]) => n > 0).map(([p]) => p);
  const plataformas = comDados.length > 1 ? [...comDados, "todas"] : comDados;
  const [plat, setPlat] = useState<string | null>(null);
  const atual = plat && plataformas.includes(plat) ? plat : plataformas[0];
  const paraApi = atual === "todas" ? undefined : atual;

  return (
    <>
      <TituloPagina titulo="Mapa" grifo="do top" sub="Quatro jeitos de enxergar a mesma base: quanto cada post passou do esperado, de que assunto o top fala, como um post do top é montado e o caminho da curtida até o pedido." />
      <div className="mapa-abas nao-imprimir">
        <Seg rotulo="Visualização" valor={v} onChange={trocar} opcoes={ABAS} />
        {(v === "esperado" || v === "temas") && plataformas.length > 1 && (
          <Seg tamanho="p" rotulo="Plataforma" valor={atual} onChange={setPlat} opcoes={plataformas.map((p) => ({ valor: p, rotulo: nomePlataforma(p) }))} />
        )}
      </div>
      {v === "esperado" && <EsperadoReal plataforma={paraApi} />}
      {v === "temas" && <Temas plataforma={paraApi} />}
      {v === "anatomia" && <Anatomia />}
      {v === "funil" && <Funil />}
    </>
  );
}
