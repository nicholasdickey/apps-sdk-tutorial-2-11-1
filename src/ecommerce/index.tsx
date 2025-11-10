import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { App, type CartItem, type PizzazShopAppProps } from "../pizzaz-shop/app";

export type EcommerceAppProps = Omit<PizzazShopAppProps, "defaultCartItems"> & {
  defaultCartItems?: CartItem[];
};

const container = document.getElementById("ecommerce-root");

if (!container) {
  throw new Error("Missing root element: ecommerce-root");
}

createRoot(container).render(
  <BrowserRouter>
    <App defaultCartItems={[]} />
  </BrowserRouter>
);

export default App;
