import type { Meta, StoryObj } from '@storybook/vue3';
import { within, expect, fn } from '@storybook/test';
import ImpactProjectionPanel from './ImpactProjectionPanel.vue';

const meta = {
  title: 'Gravity/ImpactProjectionPanel',
  component: ImpactProjectionPanel,
  tags: ['autodocs'],
  argTypes: {
    state: {
      control: 'select',
      options: ['computing', 'computed-safe', 'computed-blocked', 'published'],
    },
  },
  args: {
    migrationId: 'mig-2026-04-21',
    thresholdPercent: 20,
    impactPercent: 12,
    impactedEntities: 145,
    onPublish: fn(),
    onCancel: fn(),
  },
} satisfies Meta<typeof ImpactProjectionPanel>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Computing: Story = { args: { state: 'computing' } };
export const ComputedSafe: Story = { args: { state: 'computed-safe', impactPercent: 12 } };
export const ComputedBlocked: Story = {
  args: { state: 'computed-blocked', impactPercent: 38 },
  play: async ({ canvasElement }) => {
    const alert = await within(canvasElement).findByRole('alert');
    await expect(alert).toBeInTheDocument();
  },
};
export const Published: Story = { args: { state: 'published' } };
export const DarkMode: Story = {
  args: { state: 'computed-safe' },
  globals: { theme: 'dark' },
  parameters: { backgrounds: { default: 'dark' } },
};
