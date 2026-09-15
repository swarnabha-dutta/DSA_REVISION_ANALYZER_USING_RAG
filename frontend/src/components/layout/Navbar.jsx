import {
  Link,
  useLocation,
} from "react-router-dom";

function Navbar({
  theme = "dark",
  onToggleTheme,
}) {
  const location = useLocation();

  function isActive(path) {
    // Overview
    if (path === "/") {
      return location.pathname === "/";
    }

    // Patterns should remain active
    // inside individual pattern pages.
    if (path === "/patterns") {
      return (
        location.pathname === "/patterns" ||
        location.pathname.startsWith(
          "/pattern/"
        )
      );
    }

    // AI Search
    return location.pathname === path;
  }

  return (
    <header className="navbar">

      {/* =========================
                BRAND
               ========================= */}

      <Link
        to="/"
        className="brand"
      >
        <div className="brand-mark">
          ⌘
        </div>

        <div className="brand-copy">
          <strong>
            DSA
          </strong>

          <span>
            REVISION ANALYZER
          </span>
        </div>
      </Link>

      {/* =========================
                NAVIGATION
               ========================= */}

      <nav className="navbar-nav">

        <Link
          to="/"
          className={
            isActive("/")
              ? "active"
              : ""
          }
        >
          Overview
        </Link>

        <Link
          to="/search"
          className={
            isActive("/search")
              ? "active"
              : ""
          }
        >
          <span className="search-symbol">
            ⌕
          </span>

          AI Search
        </Link>

        <Link
          to="/patterns"
          className={
            isActive("/patterns")
              ? "active"
              : ""
          }
        >
          Patterns
        </Link>

        {/* =========================
                    THEME TOGGLE
                   ========================= */}

        <button
          type="button"
          className="theme-toggle"
          onClick={onToggleTheme}
          aria-label={
            theme === "dark"
              ? "Switch to light theme"
              : "Switch to dark theme"
          }
          title={
            theme === "dark"
              ? "Switch to light theme"
              : "Switch to dark theme"
          }
        >
          {theme === "dark"
            ? "☀"
            : "☾"}
        </button>

      </nav>
    </header>
  );
}

export default Navbar;