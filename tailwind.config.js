// tailwind.config.js
const defaultTheme = require('tailwindcss/defaultTheme')

module.exports = {
  theme: {
    extend: {
      fontFamily: {
        abril: ['"Iowan Old Style"', '"New York"', 'Georgia', ...defaultTheme.fontFamily.serif],
        albert: [...defaultTheme.fontFamily.sans],
        calistoga: ['"Calistoga"', ...defaultTheme.fontFamily.sans],
      }
    }
  },
}
