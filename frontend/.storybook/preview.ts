import '../app/assets/css/main.css';
import type { Preview } from '@storybook/vue3';

const preview: Preview = {
  globalTypes: {
    theme: {
      name: 'Theme',
      description: 'Toggle dark mode (classe .dark sur <html>)',
      defaultValue: 'light',
      toolbar: {
        icon: 'paintbrush',
        items: [
          { value: 'light', title: 'Light' },
          { value: 'dark', title: 'Dark' },
        ],
        dynamicTitle: true,
      },
    },
  },
  decorators: [
    (story, ctx) => {
      if (typeof document !== 'undefined') {
        document.documentElement.classList.toggle(
          'dark',
          ctx.globals.theme === 'dark'
        );
      }
      return story();
    },
  ],
  parameters: {
    backgrounds: {
      default: 'light',
      values: [
        { name: 'light', value: '#F9FAFB' },
        { name: 'dark', value: '#111827' },
      ],
    },
    a11y: {
      config: {
        rules: [
          // AAA warnings tolérés MVP (AC4 : A + AA seulement bloquants)
          { id: 'color-contrast-enhanced', enabled: false },
        ],
      },
    },
    controls: { expanded: true },
  },
};

export default preview;
