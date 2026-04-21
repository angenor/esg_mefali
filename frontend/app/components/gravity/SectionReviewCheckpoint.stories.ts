import type { Meta, StoryObj } from '@storybook/vue3';
import { fn } from '@storybook/test';
import SectionReviewCheckpoint from './SectionReviewCheckpoint.vue';

const SECTIONS = [
  { id: 's1', title: 'Contexte entreprise' },
  { id: 's2', title: 'Budget detaille' },
  { id: 's3', title: 'Impact ESG' },
  { id: 's4', title: 'Plan de suivi' },
] as const;

const meta = {
  title: 'Gravity/SectionReviewCheckpoint',
  component: SectionReviewCheckpoint,
  tags: ['autodocs'],
  argTypes: {
    state: {
      control: 'select',
      options: ['locked', 'in-progress', 'all-reviewed', 'exporting', 'exported'],
    },
  },
  args: {
    amountUsd: 75_000,
    sections: SECTIONS,
    reviewed: [],
    onToggle: fn(),
    onExport: fn(),
  },
} satisfies Meta<typeof SectionReviewCheckpoint>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Locked: Story = { args: { state: 'locked' } };
export const InProgress: Story = {
  args: { state: 'in-progress', reviewed: ['s1', 's2'] },
};
export const AllReviewed: Story = {
  args: { state: 'all-reviewed', reviewed: ['s1', 's2', 's3', 's4'] },
};
export const Exporting: Story = {
  args: { state: 'exporting', reviewed: ['s1', 's2', 's3', 's4'] },
};
export const Exported: Story = {
  args: { state: 'exported', reviewed: ['s1', 's2', 's3', 's4'] },
};
export const DarkMode: Story = {
  args: { state: 'in-progress', reviewed: ['s1'] },
  globals: { theme: 'dark' },
  parameters: { backgrounds: { default: 'dark' } },
};
