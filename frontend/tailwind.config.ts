import type { Config } from 'tailwindcss'

export default {
  content: [
    './components/**/*.{vue,ts}',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './composables/**/*.ts',
    './plugins/**/*.ts',
    './app.vue',
  ],
  theme: {
    extend: {
      colors: {
        // Design system ESG Mefali
        brand: {
          green: '#10B981',
          blue: '#3B82F6',
          purple: '#8B5CF6',
          orange: '#F59E0B',
          red: '#EF4444',
        },
        surface: {
          bg: '#F9FAFB',
          text: '#111827',
        },
      },
    },
  },
} satisfies Config
