import {
  Routes,
  Route,
  Navigate,
} from "react-router-dom";

import Navbar from "./components/layout/Navbar";
import PageBackground from "./components/layout/PageBackground";

import Dashboard from "./pages/Dashboard";
import Patterns from "./pages/Patterns";
import Pattern from "./pages/Pattern";
import Revision from "./pages/Revision";
import Search from "./pages/Search";

function App({
  theme,
  onToggleTheme,
}) {
  return (
    <div
      className="app-shell"
      data-theme={theme}
    >
      {/* Global background */}
      <PageBackground />

      {/* Global navbar */}
      <Navbar
        theme={theme}
        onToggleTheme={onToggleTheme}
      />

      <main className="app-content">
        <Routes>

          {/* =========================
                        OVERVIEW
                       ========================= */}

          <Route
            path="/"
            element={<Dashboard />}
          />

          {/* =========================
                        ALL PATTERNS
                       ========================= */}

          <Route
            path="/patterns"
            element={<Patterns />}
          />

          {/* =========================
                        SINGLE PATTERN
                       ========================= */}

          <Route
            path="/pattern/:patternId"
            element={<Pattern />}
          />

          {/* =========================
                        AI REVISION
                       ========================= */}

          <Route
            path="/revision/:videoId"
            element={<Revision />}
          />

          {/* =========================
                        AI SEARCH
                       ========================= */}

          <Route
            path="/search"
            element={<Search />}
          />

          {/* =========================
                        FALLBACK
                       ========================= */}

          <Route
            path="*"
            element={
              <Navigate
                to="/"
                replace
              />
            }
          />

        </Routes>
      </main>
    </div>
  );
}

export default App;