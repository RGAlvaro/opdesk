/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#18212f",
        muted: "#637083",
        line: "#d9e2ec",
        surface: "#f6f8fb",
        brand: "#1b6b5f",
        accent: "#b94a48",
      },
      boxShadow: {
        panel: "0 16px 48px rgba(24, 33, 47, 0.08)",
      },
    },
  },
  plugins: [],
};
