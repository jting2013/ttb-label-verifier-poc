/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        federal: {
          navy: "#24364b",
          blue: "#2f5f8f",
          ink: "#1d2733",
          line: "#d7dde5",
          mist: "#f4f7fa"
        }
      }
    }
  },
  plugins: []
};
