/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // Extend Tailwind with Fluent UI design tokens
      colors: {
        'fluent-primary': '#0078d4',
        'fluent-secondary': '#2b88d8',
        'fluent-accent': '#ff6b35',
        'fluent-success': '#107c10',
        'fluent-warning': '#ff8c00',
        'fluent-error': '#d13438',
      },
      fontFamily: {
        'fluent': ['Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      maxWidth: {
        '8xl': '88rem',
      },
      screens: {
        'xs': '475px',
        '3xl': '1600px',
      }
    },
  },
  plugins: [],
}