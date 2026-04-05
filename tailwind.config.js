/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        midnight: "#0b0f1a",
        surface: "#141929",
        accent: "#4f8ef7",
        violet: "#7c5cfc",
        success: "#34d399",
        amber: "#fbbf24",
        danger: "#f87171",
      },
      fontFamily: {
        sans: ["DM Sans", "sans-serif"],
        display: ["Playfair Display", "serif"],
      },
      boxShadow: {
        panel: "0 18px 50px rgba(0, 0, 0, 0.3)",
      },
    },
  },
  plugins: [],
};
