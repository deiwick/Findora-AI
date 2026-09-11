/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        dark: {
          900: '#07090e',
          800: '#0e121a',
          700: '#151b26',
          600: '#1e2636',
          500: '#2a344a',
        },
        neon: {
          blue: '#00d2ff',
          green: '#00f59b',
          amber: '#ffb300',
          red: '#ff3b5c',
          purple: '#9d4edd',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'neon-blue': '0 0 20px -5px rgba(0, 210, 255, 0.3)',
        'neon-green': '0 0 20px -5px rgba(0, 245, 155, 0.3)',
        'neon-red': '0 0 20px -5px rgba(255, 59, 92, 0.3)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
      },
      animation: {
        'pulse-subtle': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(0, 210, 255, 0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(0, 210, 255, 0.6)' },
        }
      }
    },
  },
  plugins: [],
}
