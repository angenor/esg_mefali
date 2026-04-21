import type { StorybookConfig } from '@storybook/vue3-vite';

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
};

export default config;
