import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./App";

import "./styles/theme.css";
import "./index.css";
import "./App.css";

export function Root() {
  const [theme, setTheme] = useState(() => {
    const savedTheme = localStorage.getItem("dsa-theme");

    if (savedTheme === "light" || savedTheme === "dark") {
      return savedTheme;
    }

    return "dark";
  });

  useEffect(() => {
    // Apply the selected theme globally.
    document.documentElement.dataset.theme = theme;
    document.body.dataset.theme = theme;

    // Remember the user's choice.
    localStorage.setItem("dsa-theme", theme);
  }, [theme]);

  function handleToggleTheme() {
    setTheme((currentTheme) =>
      currentTheme === "dark" ? "light" : "dark"
    );
  }

  return (
    <BrowserRouter>
      <App
        theme={theme}
        onToggleTheme={handleToggleTheme}
      />
    </BrowserRouter>
  );
}

ReactDOM.createRoot(
  document.getElementById("root")
).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);