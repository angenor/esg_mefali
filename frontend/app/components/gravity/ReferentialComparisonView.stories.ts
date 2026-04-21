import type { Meta, StoryObj } from '@storybook/vue3';
import { fn } from '@storybook/test';
import ReferentialComparisonView from './ReferentialComparisonView.vue';

const SAMPLE_ROWS = [
  {
    id: 'c1',
    label: 'Politique anti-corruption',
    verdicts: { UEMOA: 'pass', GCF: 'pass', IFC: 'reported' } as const,
  },
  {
    id: 'c2',
    label: 'Plan genre',
    verdicts: { UEMOA: 'fail', GCF: 'reported', IFC: 'na' } as const,
  },
  {
    id: 'c3',
    label: 'Empreinte carbone publiee',
    verdicts: { UEMOA: 'reported', GCF: 'pass', IFC: 'pass' } as const,
  },
] as const;

const meta = {
  title: 'Gravity/ReferentialComparisonView',
  component: ReferentialComparisonView,
  tags: ['autodocs'],
  argTypes: {
    state: { control: 'select', options: ['loading', 'loaded', 'partial', 'error'] },
    variant: { control: 'inline-radio', options: ['compact', 'fullpage'] },
  },
  args: {
    activeReferentials: ['UEMOA', 'GCF', 'IFC'],
    rows: SAMPLE_ROWS,
    variant: 'fullpage',
    onRetry: fn(),
  },
} satisfies Meta<typeof ReferentialComparisonView>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Loading: Story = { args: { state: 'loading' } };
export const Loaded: Story = { args: { state: 'loaded' } };
export const Partial: Story = { args: { state: 'partial' } };
export const Error: Story = { args: { state: 'error' } };
export const Compact: Story = { args: { state: 'loaded', variant: 'compact' } };
export const FullPage: Story = { args: { state: 'loaded', variant: 'fullpage' } };
export const DarkMode: Story = {
  args: { state: 'loaded' },
  globals: { theme: 'dark' },
  parameters: { backgrounds: { default: 'dark' } },
};
