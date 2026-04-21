import type { Meta, StoryObj } from '@storybook/vue3';
import { fn } from '@storybook/test';
import SourceCitationDrawer from './SourceCitationDrawer.vue';

const LONG_CONTENT = [
  'Article 1. Les entreprises eligibles au financement de la BOAD ...',
  'Article 2. Les projets soumis doivent respecter les referentiels UEMOA.',
  'Article 3. Les beneficiaires doivent disposer d une politique anti-corruption.',
  'Article 4. Les rapports annuels incluent un volet ESG obligatoire.',
  'Article 5. Les sanctions en cas de non-conformite sont graduelles.',
  'Article 6. Les audits externes sont triennaux minimum.',
  'Article 7. Les plans de remediation sont soumis sous 60 jours.',
  'Article 8. La publication du bilan carbone devient obligatoire en 2027.',
].join('\n\n');

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
export const OpenWithLongContent: Story = {
  args: { state: 'open', sourceContent: LONG_CONTENT },
};
export const Loading: Story = { args: { state: 'loading' } };
export const Error: Story = { args: { state: 'error' } };
export const Closing: Story = { args: { state: 'closing' } };

export const DarkMode: Story = {
  args: { state: 'open', sourceContent: LONG_CONTENT },
  globals: { theme: 'dark' },
  parameters: { backgrounds: { default: 'dark' } },
};
