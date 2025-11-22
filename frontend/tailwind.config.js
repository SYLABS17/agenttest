/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#ecfeff",
          500: "#0ea5e9",
          600: "#0284c7"
        }
      }
    }
  },
  plugins: []
};
