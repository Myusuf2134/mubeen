import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      // ── Colors ───────────────────────────────────────────────────────────
      // Solid values for backgrounds/text (opacity modifiers not needed).
      // Channel-tuple format for accents so `bg-mint/10` etc. work correctly.
      colors: {
        // Dark backgrounds
        page:     "#06120f",   // --bg-0
        raised:   "#0a1a16",   // --bg-1
        elevated: "#0f231d",   // --bg-2
        // Text ramp
        ink:        "#f0faf7", // --text-0
        "ink-dim":  "#b9cbc5", // --text-1
        "ink-muted":"#7c948c", // --text-2
        // Accents (with Tailwind opacity-modifier support via channel tuples)
        mint:       "rgb(var(--mint-ch) / <alpha-value>)",
        "mint-dim": "rgb(var(--mint-dim-ch) / <alpha-value>)",
        "mint-deep":"rgb(var(--mint-deep-ch) / <alpha-value>)",
        gold:       "rgb(var(--gold-ch) / <alpha-value>)",
      },

      // ── Typography ───────────────────────────────────────────────────────
      fontFamily: {
        sora:  ["Sora",  "sans-serif"],
        inter: ["Inter", "sans-serif"],
        amiri: ["Amiri", "serif"],
      },
      // Modular type scale — maps to CSS custom properties
      fontSize: {
        "step--1": ["var(--step--1)", { lineHeight: "1.5" }],
        "step-0":  ["var(--step-0)",  { lineHeight: "1.6" }],
        "step-1":  ["var(--step-1)",  { lineHeight: "1.5" }],
        "step-2":  ["var(--step-2)",  { lineHeight: "1.3" }],
        "step-3":  ["var(--step-3)",  { lineHeight: "1.2" }],
        "step-4":  ["var(--step-4)",  { lineHeight: "1.1" }],
        "step-5":  ["var(--step-5)",  { lineHeight: "1.08" }],
        "step-6":  ["var(--step-6)",  { lineHeight: "1.08" }],
      },

      // ── Radii ────────────────────────────────────────────────────────────
      borderRadius: {
        icon:       "10px",  // icon containers (feat-icon, brand-mark)
        row:        "14px",  // directory rows (.masjid-row)
        card:       "16px",  // feature cards (.feat-card)
        "card-lg":  "20px",  // glass cards, TV mock
        "card-xl":  "24px",  // CTA banner
      },

      // ── Shadows ──────────────────────────────────────────────────────────
      boxShadow: {
        glass:
          "0 20px 60px rgba(0,0,0,0.40), inset 0 1px 0 rgba(255,255,255,0.06)",
        "glass-hover":
          "0 24px 80px rgba(0,0,0,0.50), inset 0 1px 0 rgba(255,255,255,0.10)",
        "mint-glow":  "0 4px 20px rgba(94,234,212,0.22)",
        "mint-glow-lg": "0 6px 24px rgba(94,234,212,0.36)",
        "brand-mark": "0 4px 16px rgba(94,234,212,0.25)",
      },

      // ── Letter spacing ────────────────────────────────────────────────────
      letterSpacing: {
        sora: "-0.02em",
        caps: "0.06em",
      },
    },
  },
  plugins: [],
} satisfies Config;
