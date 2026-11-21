/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        giki: {
          50: '#f0f7ff',
          100: '#e0effe',
          200: '#b9ddfd',
          300: '#7cc2fb',
          400: '#36a2f7',
          500: '#0c85eb',
          600: '#0066c9',
          700: '#0152a3',
          800: '#064585',
          900: '#0b3b6f',
          950: '#07254a',
        },
      },
    },
  },
  plugins: [],
}
