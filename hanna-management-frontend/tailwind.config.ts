import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      container: { // Add container configuration
        center: true, // Center the container by default
        padding: {
          DEFAULT: '1rem', // Default padding for all screen sizes
          sm: '2rem',    // Padding for small screens and up
          lg: '4rem',    // Padding for large screens and up
          xl: '5rem',    // Padding for extra large screens and up
          '2xl': '6rem', // Padding for 2xl screens and up
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
}
export default config
