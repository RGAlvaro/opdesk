import React from "react";
import ReactDOM from "react-dom/client";

import { AppProviders } from "./app/AppProviders";
import { AppRouter } from "./app/AppRouter";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <AppProviders>
      <AppRouter />
    </AppProviders>
  </React.StrictMode>,
);
