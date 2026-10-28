import { Component } from "react";

export default class ErrorBoundary extends Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <main
          role="alert"
          style={{
            display: "grid",
            minHeight: "100vh",
            placeContent: "center",
            gap: 12,
            padding: 24,
            background: "#020617",
            color: "#fecaca",
            fontFamily: "system-ui, sans-serif",
          }}
        >
          <h1 style={{ margin: 0, fontSize: 22 }}>The workspace could not load</h1>
          <p style={{ margin: 0, color: "#cbd5e1" }}>
            Reload the page. If the problem continues, check the browser console.
          </p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            style={{
              justifySelf: "start",
              padding: "10px 14px",
              border: 0,
              borderRadius: 8,
              background: "#0284c7",
              color: "#fff",
              font: "inherit",
              cursor: "pointer",
            }}
          >
            Reload workspace
          </button>
        </main>
      );
    }

    return this.props.children;
  }
}
