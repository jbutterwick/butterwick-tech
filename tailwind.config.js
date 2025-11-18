// tailwind.config.js
const defaultTheme = require('tailwindcss/defaultTheme')

module.exports = {
  theme: {
    extend: {
      fontFamily: {
        abril: ['"Abril Fatface"', ...defaultTheme.fontFamily.sans],
        albert: ['"Albert Sans"', ...defaultTheme.fontFamily.sans],
        calistoga: ['"Calistoga"', ...defaultTheme.fontFamily.sans],
      }
    }
  },
}
