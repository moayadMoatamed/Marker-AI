import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f8f8f7",
          100: "#f0efed",
          200: "#e2e0db",
          300: "#c4c1ba",
          400: "#9d9990",
          500: "#7d7870",
          600: "#5f5b54",
          700: "#46433e",
          800: "#2d2b27",
          900: "#1a1816",
          950: "#0d0c0a",
        },
        accent: {
          50: "#f2f9f4",
          100: "#e0f1e5",
          200: "#bce2c5",
          300: "#8ccf9c",
          400: "#57b56d",
          500: "#35984c",
          600: "#267a38",
          700: "#20612e",
          800: "#1c4d27",
          900: "#184021",
          950: "#0a2211",
        },
        amber: {
          50: "#fef9f0",
          100: "#fdefd2",
          200: "#fbdaa4",
          300: "#f8c16c",
          400: "#f4a42e",
          500: "#ea940f",
          600: "#c97a09",
          700: "#a05f0b",
          800: "#824c11",
          900: "#6b3f13",
          950: "#3d2007",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "Consolas", "monospace"],
      },
      backgroundImage: {
        "dot-pattern":
          "radial-gradient(circle, rgba(26,24,22,0.06) 1px, transparent 1px)",
      },
      backgroundSize: {
        "dot-sm": "18px 18px",
      },
    },
  },
  plugins: [],
};

export default config;
