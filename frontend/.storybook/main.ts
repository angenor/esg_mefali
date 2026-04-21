import type { StorybookConfig } from '@storybook/vue3-vite';
import vue from '@vitejs/plugin-vue';
import { mergeConfig } from 'vite';

const config: StorybookConfig = {
  stories: ['../app/components/gravity/**/*.stories.@(ts|mdx)'],
  addons: [
    '@storybook/addon-essentials',
    '@storybook/addon-a11y',
    '@storybook/addon-interactions',
  ],
  framework: { name: '@storybook/vue3-vite', options: {} },
  docs: { autodocs: 'tag' },
  typescript: { check: false, reactDocgen: false },
  // Pivot documente docs/CODEMAPS/storybook.md §5 : @storybook/vue3-vite 8 ne charge
  // pas automatiquement le plugin Vue en mode `storybook build` (dev OK mais build KO).
  // Injection explicite via viteFinal + mergeConfig = parade minimale. A retirer si
  // Storybook 9 corrige le comportement (suivi upgrade section Upgrade strategy).
  viteFinal: async (config) =>
    mergeConfig(config, {
      plugins: [vue()],
      resolve: {
        alias: {
          '~': new URL('../app', import.meta.url).pathname,
          '@': new URL('../app', import.meta.url).pathname,
        },
      },
    }),
};

export default config;
