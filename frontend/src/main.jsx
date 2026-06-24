import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./App.jsx";
import { ThemeProvider } from "./lib/theme.jsx";
import Toaster from "./components/Toaster.jsx";
import "./index.css";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <ThemeProvider>
        <Toaster>
          <App />
        </Toaster>
      </ThemeProvider>
    </BrowserRouter>
  </StrictMode>,
);
