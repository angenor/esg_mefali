import type { Meta, StoryObj } from '@storybook/vue3';
import { within, userEvent, expect, fn } from '@storybook/test';
import SignatureModal from './SignatureModal.vue';

const meta = {
  title: 'Gravity/SignatureModal',
  component: SignatureModal,
  tags: ['autodocs'],
  parameters: { a11y: { disable: false } },
  argTypes: {
    state: {
      control: 'select',
      options: ['initial', 'ready', 'signing', 'signed', 'error'],
    },
  },
  args: {
    fundApplicationId: 'fa-demo-001',
    destinataireBailleur: 'GCF Secretariat',
    snapshotPreview: '{"sections": 4, "sha256": "…"}',
    onCancel: fn(),
    onSign: fn(),
    onSaveDraft: fn(),
  },
} satisfies Meta<typeof SignatureModal>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Initial: Story = {
  args: { state: 'initial' },
  play: async ({ canvasElement, args }) => {
    const canvas = within(document.body);
    const dialog = await canvas.findByRole('dialog');
    await expect(dialog).toBeInTheDocument();
    await userEvent.keyboard('{Escape}');
    await expect(args.onCancel).toHaveBeenCalled();
  },
};

export const Ready: Story = {
  args: { state: 'ready' },
};

export const Signing: Story = {
  args: { state: 'signing' },
};

export const Signed: Story = {
  args: { state: 'signed' },
};

export const Error: Story = {
  args: { state: 'error' },
  play: async () => {
    const alert = await within(document.body).findByRole('alert');
    await expect(alert).toBeInTheDocument();
  },
};

export const DarkMode: Story = {
  args: { state: 'ready' },
  globals: { theme: 'dark' },
  parameters: { backgrounds: { default: 'dark' } },
};
