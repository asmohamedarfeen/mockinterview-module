/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Google Meet inspired dark theme
        'meet-dark': '#202124',
        'meet-darker': '#171717',
        'meet-gray': '#3c4043',
        'meet-light-gray': '#5f6368',
        'meet-blue': '#1a73e8',
        'meet-red': '#ea4335',
        'meet-green': '#34a853',
      },
    },
  },
  plugins: [],
}
