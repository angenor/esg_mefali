import type { Meta, StoryObj } from '@storybook/vue3';
import { fn } from '@storybook/test';
import SourceCitationDrawer from './SourceCitationDrawer.vue';

const meta = {
  title: 'Gravity/SourceCitationDrawer',
  component: SourceCitationDrawer,
  tags: ['autodocs'],
  argTypes: {
    state: {
      control: 'select',
      options: ['closed', 'opening', 'open', 'loading', 'error', 'closing'],
    },
    sourceType: {
      control: 'select',
      options: ['rule', 'criterion', 'fact', 'template', 'intermediary', 'fund'],
    },
  },
  args: {
    sourceType: 'rule',
    sourceTitle: 'Decret UEMOA 2023-045',
    sourceUrl: 'https://uemoa.int/fr/textes/decret-2023-045',
    sourceAccessedAt: '2026-04-21T09:12:00Z',
    onClose: fn(),
    onRetry: fn(),
  },
} satisfies Meta<typeof SourceCitationDrawer>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Closed: Story = { args: { state: 'closed' } };
export const Opening: Story = { args: { state: 'opening' } };
export const Open: Story = { args: { state: 'open' } };
export const Loading: Story = { args: { state: 'loading' } };
export const Error: Story = { args: { state: 'error' } };
export const Closing: Story = { args: { state: 'closing' } };

export const DarkMode: Story = {
  args: { state: 'open' },
  globals: { theme: 'dark' },
  parameters: { backgrounds: { default: 'dark' } },
};
