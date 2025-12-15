module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "rgb(var(--bg) / <alpha-value>)",
        fg: "rgb(var(--fg) / <alpha-value>)",
        card: "rgb(var(--card) / <alpha-value>)",
        border: "rgb(var(--border) / <alpha-value>)",
        muted: "rgb(var(--muted) / <alpha-value>)",
        accent: "rgb(var(--accent) / <alpha-value>)",
        danger: "rgb(var(--danger) / <alpha-value>)"
      },
      boxShadow: {
        soft: "0 10px 30px rgba(0,0,0,.25)",
        glow: "0 0 0 1px rgba(34,211,238,.25), 0 12px 24px rgba(34,211,238,.12)"
      },
      borderRadius: { xl2: "1.25rem" }
    }
  },
  plugins: []
}
