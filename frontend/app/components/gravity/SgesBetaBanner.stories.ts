import type { Meta, StoryObj } from '@storybook/vue3';
import { fn } from '@storybook/test';
import SgesBetaBanner from './SgesBetaBanner.vue';

const meta = {
  title: 'Gravity/SgesBetaBanner',
  component: SgesBetaBanner,
  tags: ['autodocs'],
  argTypes: {
    reviewStatus: {
      control: 'select',
      options: [
        'beta-pending-review',
        'beta-review-requested',
        'beta-review-validated',
        'beta-review-rejected',
        'post-beta-ga',
      ],
    },
  },
  args: {
    sgesId: 'sges-beta-001',
    onRequestReview: fn(),
  },
} satisfies Meta<typeof SgesBetaBanner>;

export default meta;
type Story = StoryObj<typeof meta>;

export const BetaPendingReview: Story = { args: { reviewStatus: 'beta-pending-review' } };
export const BetaReviewRequested: Story = { args: { reviewStatus: 'beta-review-requested' } };
export const BetaReviewValidated: Story = { args: { reviewStatus: 'beta-review-validated' } };
export const BetaReviewRejected: Story = { args: { reviewStatus: 'beta-review-rejected' } };
export const PostBetaGA: Story = { args: { reviewStatus: 'post-beta-ga' } };
export const DarkMode: Story = {
  args: { reviewStatus: 'beta-pending-review' },
  globals: { theme: 'dark' },
  parameters: { backgrounds: { default: 'dark' } },
};
