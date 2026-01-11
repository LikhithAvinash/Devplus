/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // Enable dark mode manually if needed, or rely on system/default dark styles
  theme: {
    extend: {
      colors: {
        // Custom colors to match the dark theme in the image
        dark: {
          bg: '#0f172a', // Slate 900
          card: '#1e293b', // Slate 800
          text: '#f8fafc', // Slate 50
          muted: '#94a3b8', // Slate 400
        }
      }
    },
  },
  plugins: [],
}
