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
    // Exclure les specs Playwright (extension .spec.ts sous tests/e2e/) —
    // Vitest et Playwright cohabitent dans le meme dossier tests/ (story 8.1).
    exclude: ['node_modules/**', 'dist/**', '.nuxt/**', 'tests/e2e/**'],
    // Compile-time type tests (AC5 Story 10.15) : `npm run test:typecheck`
    // execute uniquement les fichiers *.test-d.ts pour valider les directives
    // // @ts-expect-error (discrimination unions, invariants API).
    // ignoreSourceErrors : les erreurs TS pre-existantes dans app/composables/*
    // (dette technique hors scope 10.15) sont traitees comme warnings. Les vraies
    // erreurs sur les fichiers *.test-d.ts elles-memes restent bloquantes.
    typecheck: {
      include: ['tests/**/*.test-d.ts'],
      tsconfig: './tsconfig.json',
      ignoreSourceErrors: true,
    },
  },
  resolve: {
    alias: {
      '~': new URL('./app', import.meta.url).pathname,
    },
  },
})
