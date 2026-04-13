import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import type { Plugin } from 'vite'

// Plugin pour simuler import.meta.client/server de Nuxt en environnement de test
function nuxtImportMetaPlugin(): Plugin {
  return {
    name: 'nuxt-import-meta',
    enforce: 'pre',
    transform(code, id) {
      if (id.includes('node_modules')) return
      if (!code.includes('import.meta.client') && !code.includes('import.meta.server')) return
      return code
        .replaceAll('import.meta.client', 'true')
        .replaceAll('import.meta.server', 'false')
    },
  }
}

export default defineConfig({
  plugins: [vue(), nuxtImportMetaPlugin()],
  test: {
    environment: 'happy-dom',
    setupFiles: ['tests/setup.ts'],
    include: ['tests/**/*.test.ts'],
  },
  resolve: {
    alias: {
      '~': new URL('./app', import.meta.url).pathname,
    },
  },
})
