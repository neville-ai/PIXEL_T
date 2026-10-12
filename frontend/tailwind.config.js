/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#F4FAFC',
          100: '#EAF4F8',
          600: '#2C6C88',
          700: '#1C5B76',
          800: '#164B65',
          900: '#0F3D56',
        },
        accent: {
          50: '#F2FBFA',
          100: '#E6F7F6',
          500: '#29B8B8',
          600: '#18A6A6',
          700: '#147F80',
        },
        neutral: {
          50: '#F7FAFC',
          100: '#EAF0F3',
          200: '#D9E4EA',
          300: '#CBD5E1',
          400: '#94A3B8',
          600: '#64748B',
          700: '#334A59',
          900: '#172B3A',
          950: '#0F1F2A',
        },
        semantic: {
          success: '#2E8B70',
          warning: '#D99A2B',
          error: '#C94A4A',
          info: '#2878A8',
        },
        dark: {
          bg: '#0B1720',
          surface: '#10232E',
          elevated: '#142B37',
          border: '#29404C',
          text: '#EAF4F8',
          textMuted: '#A9BBC5',
          accentSurface: '#123A3B',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      borderRadius: {
        sm: '6px',
        md: '8px',
        lg: '12px',
        xl: '16px',
      },
      spacing: {
        1: '4px',
        2: '8px',
        3: '12px',
        4: '16px',
        6: '24px',
        8: '32px',
        10: '40px',
        12: '48px',
        16: '64px',
      },
    },
  },
  plugins: [],
}
