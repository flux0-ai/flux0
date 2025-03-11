import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./app";
import "./index.css";

const container = document.getElementById("root");
if (!container) throw new Error("No container element");
createRoot(container).render(
  <StrictMode>
    <App />,
  </StrictMode>,
);
