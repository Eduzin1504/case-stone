import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MotionConfig } from "motion/react";
import { FocoProvider } from "./contexto/Foco";
import App from "./App";
import "./styles/tokens.css";
import "./styles/base.css";
import "./styles/componentes.css";
import "./styles/post.css";
import "./styles/shell.css";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 60_000, refetchOnWindowFocus: false, retry: (n, e) => n < 1 && !(e instanceof Error && e.name === "ErroApi") } },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <MotionConfig reducedMotion="user">
            <FocoProvider>
              <App />
            </FocoProvider>
        </MotionConfig>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
