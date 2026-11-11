import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#fff7ed",
          100: "#ffedd5",
          200: "#fed7aa",
          300: "#fdba74",
          400: "#fb923c",
          500: "#f97316", // Vibrant warm amber-orange
          600: "#ea580c",
          700: "#c2410c",
          800: "#9a3412",
          900: "#7c2d12",
        },
        canvas: "var(--color-canvas)",
        panel: "var(--color-panel)",
        "panel-glass": "var(--color-panel-glass)",
        well: "var(--color-well)",
        "well-soft": "var(--color-well-soft)",
        control: "var(--color-control)",
        "control-hover": "var(--color-control-hover)",
        "row-hover": "var(--color-row-hover)",
        line: "var(--color-line)",
        "line-strong": "var(--color-line-strong)",
        "input-border": "var(--color-input-border)",
        backdrop: "var(--color-backdrop)",
        ink: {
          DEFAULT: "var(--color-ink)",
          2: "var(--color-ink-2)",
          3: "var(--color-ink-3)",
          muted: "var(--color-ink-muted)",
          subtle: "var(--color-ink-subtle)",
        },
        accent: {
          brand: "var(--accent-brand)",
          emerald: "var(--accent-emerald)",
          amber: "var(--accent-amber)",
          sky: "var(--accent-sky)",
          rose: "var(--accent-rose)",
          red: "var(--accent-red)",
          blue: "var(--accent-blue)",
          purple: "var(--accent-purple)",
        },
        tint: {
          brand: "var(--tint-brand-bg)",
          "brand-border": "var(--tint-brand-border)",
          emerald: "var(--tint-emerald-bg)",
          "emerald-border": "var(--tint-emerald-border)",
          amber: "var(--tint-amber-bg)",
          "amber-border": "var(--tint-amber-border)",
          sky: "var(--tint-sky-bg)",
          "sky-border": "var(--tint-sky-border)",
          rose: "var(--tint-rose-bg)",
          "rose-border": "var(--tint-rose-border)",
          blue: "var(--tint-blue-bg)",
          "blue-border": "var(--tint-blue-border)",
          purple: "var(--tint-purple-bg)",
          "purple-border": "var(--tint-purple-border)",
        },
      },
    },
  },
  plugins: [],
};
export default config;
