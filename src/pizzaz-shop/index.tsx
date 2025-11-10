import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { App } from "./app";

export * from "./app";

const container = document.getElementById("pizzaz-shop-root");

if (!container) {
  throw new Error("Missing root element: pizzaz-shop-root");
}

createRoot(container).render(
  <BrowserRouter>
    <App />
  </BrowserRouter>
);

export default App;
