"use client";

/**
 * Last-resort boundary for failures in the root layout itself, where the
 * surrounding layout and error UI are unusable. This component must render its
 * own <html> and <body>.
 *
 * It is intentionally self-contained: no shared components, fonts or styles
 * that could themselves be the thing that failed.
 */
export default function GlobalError({ error, reset }) {
  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "2rem",
          fontFamily:
            "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif",
          backgroundColor: "#ffffff",
          color: "#1c1917",
        }}
      >
        <div style={{ maxWidth: "28rem", textAlign: "center" }}>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 600, margin: 0 }}>
            The application failed to load
          </h1>
          <p style={{ marginTop: "0.75rem", color: "#57534e" }}>
            An unexpected error occurred. Reloading the page may resolve it.
          </p>
          <button
            type="button"
            onClick={() => reset()}
            style={{
              marginTop: "1.5rem",
              padding: "0.625rem 1.25rem",
              border: 0,
              borderRadius: "0.375rem",
              backgroundColor: "#2e4d39",
              color: "#ffffff",
              fontSize: "0.875rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}
