// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          bg: "#0b0f12",
          card: "#12181d",
          border: "#1f2a33",
          accent: "#10b981",
          accent2: "#7c3aed",
        },
      },
      boxShadow: { soft: "0 6px 24px rgba(0,0,0,0.35)" },
      borderRadius: { xl2: "1rem" },
    },
  },
  plugins: [],
};
