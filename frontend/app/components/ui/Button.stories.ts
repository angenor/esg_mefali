import type { Meta, StoryObj } from '@storybook/vue3';
import { within, userEvent, expect, fn } from '@storybook/test';
import { h } from 'vue';
import Button from './Button.vue';
import { BUTTON_VARIANTS, BUTTON_SIZES } from './registry';
import type { ButtonVariant, ButtonSize } from './registry';

// Type explicite des args : le type discrimine iconOnly rend le Meta<typeof Button>
// mal compatible avec Storybook v8 + slots. On declare un type aplati equivalent.
type ButtonStoryArgs = {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  disabled?: boolean;
  iconOnly?: boolean;
  ariaLabel?: string;
  type?: 'button' | 'submit' | 'reset';
  onClick?: (event: MouseEvent) => void;
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const meta: Meta<ButtonStoryArgs> = {
  title: 'UI/Button',
  // Cast : Storybook v8 Meta<Args> attend ConcreteComponent<any> ; Vue SFC typed
  // est une DefineSetupFnComponent. Le cast est inerte au runtime.
  component: Button as unknown as Meta<ButtonStoryArgs>['component'],
  tags: ['autodocs'],
  parameters: { a11y: { disable: false } },
  argTypes: {
    variant: { control: 'select', options: [...BUTTON_VARIANTS] },
    size: { control: 'select', options: [...BUTTON_SIZES] },
    loading: { control: 'boolean' },
    disabled: { control: 'boolean' },
    iconOnly: { control: 'boolean' },
    ariaLabel: { control: 'text' },
    type: { control: 'select', options: ['button', 'submit', 'reset'] },
  },
  args: {
    onClick: fn(),
  },
  render: (args) => ({
    components: { Button },
    setup: () => ({ args }),
    template: `<Button v-bind="args" @click="args.onClick">Signer et figer</Button>`,
  }),
};

export default meta;
type Story = StoryObj<ButtonStoryArgs>;

/* ===========================================================================
 * 1. Matrice 4 variants x 3 sizes = 12 stories (showcase exhaustif).
 * =========================================================================*/

export const PrimarySm: Story = { args: { variant: 'primary', size: 'sm' } };
export const PrimaryMd: Story = {
  args: { variant: 'primary', size: 'md' },
  play: async ({ canvasElement, args }) => {
    const canvas = within(canvasElement);
    const btn = canvas.getByRole('button');
    await userEvent.click(btn);
    await expect(args.onClick).toHaveBeenCalledTimes(1);
  },
};
export const PrimaryLg: Story = { args: { variant: 'primary', size: 'lg' } };

export const SecondarySm: Story = { args: { variant: 'secondary', size: 'sm' } };
export const SecondaryMd: Story = {
  args: { variant: 'secondary', size: 'md' },
  play: async ({ canvasElement, args }) => {
    const canvas = within(canvasElement);
    const btn = canvas.getByRole('button');
    btn.focus();
    // WCAG 2.1.1 : Space declenche click sur <button> natif.
    await userEvent.keyboard(' ');
    await expect(args.onClick).toHaveBeenCalled();
  },
};
export const SecondaryLg: Story = { args: { variant: 'secondary', size: 'lg' } };

export const GhostSm: Story = { args: { variant: 'ghost', size: 'sm' } };
export const GhostMd: Story = { args: { variant: 'ghost', size: 'md' } };
export const GhostLg: Story = { args: { variant: 'ghost', size: 'lg' } };

export const DangerSm: Story = { args: { variant: 'danger', size: 'sm' } };
export const DangerMd: Story = { args: { variant: 'danger', size: 'md' } };
export const DangerLg: Story = { args: { variant: 'danger', size: 'lg' } };

/* ===========================================================================
 * 2. Etats : Loading / Disabled + play functions validation bloquage click.
 * =========================================================================*/

export const Loading: Story = {
  args: { variant: 'primary', loading: true },
  play: async ({ canvasElement, args }) => {
    const canvas = within(canvasElement);
    const btn = canvas.getByRole('button');
    await expect(btn).toHaveAttribute('aria-busy', 'true');
    await userEvent.click(btn);
    // Click bloque : handleClick retourne sans emit.
    await expect(args.onClick).not.toHaveBeenCalled();
  },
};

export const Disabled: Story = {
  args: { variant: 'primary', disabled: true },
  play: async ({ canvasElement, args }) => {
    const canvas = within(canvasElement);
    const btn = canvas.getByRole('button');
    await expect(btn).toHaveAttribute('aria-disabled', 'true');
    btn.focus();
    await userEvent.keyboard('{Enter}');
    await userEvent.keyboard(' ');
    await expect(args.onClick).not.toHaveBeenCalled();
  },
};

/* ===========================================================================
 * 3. Icon slots : #iconLeft / #iconRight / icon-only (ariaLabel obligatoire).
 * =========================================================================*/

// SVG icon stub (remplace par Lucide 10.21). Taille h-4 w-4 pour sizes sm+md.
const ArrowRightIcon = () =>
  h(
    'svg',
    {
      class: 'h-4 w-4',
      viewBox: '0 0 24 24',
      fill: 'none',
      stroke: 'currentColor',
      'stroke-width': '2',
      'stroke-linecap': 'round',
      'stroke-linejoin': 'round',
    },
    [h('path', { d: 'M5 12h14M13 6l6 6-6 6' })],
  );

const CloseIcon = () =>
  h(
    'svg',
    {
      class: 'h-4 w-4',
      viewBox: '0 0 24 24',
      fill: 'none',
      stroke: 'currentColor',
      'stroke-width': '2',
      'stroke-linecap': 'round',
      'stroke-linejoin': 'round',
    },
    [h('path', { d: 'M18 6 6 18M6 6l12 12' })],
  );

export const IconLeft: Story = {
  args: { variant: 'primary' },
  render: (args) => ({
    components: { Button, ArrowRightIcon },
    setup: () => ({ args }),
    template: `
      <Button v-bind="args" @click="args.onClick">
        <template #iconLeft><ArrowRightIcon /></template>
        Continuer
      </Button>
    `,
  }),
};

export const IconRight: Story = {
  args: { variant: 'primary' },
  render: (args) => ({
    components: { Button, ArrowRightIcon },
    setup: () => ({ args }),
    template: `
      <Button v-bind="args" @click="args.onClick">
        Suivant
        <template #iconRight><ArrowRightIcon /></template>
      </Button>
    `,
  }),
};

export const IconOnly: Story = {
  args: { variant: 'ghost', iconOnly: true, ariaLabel: 'Fermer le modal' },
  render: (args) => ({
    components: { Button, CloseIcon },
    setup: () => ({ args }),
    template: `
      <Button v-bind="args" @click="args.onClick">
        <template #iconLeft><CloseIcon /></template>
      </Button>
    `,
  }),
};

/* ===========================================================================
 * 4. Dark mode + focus visible (validation AC7).
 * =========================================================================*/

export const DarkMode: Story = {
  args: { variant: 'primary' },
  globals: { theme: 'dark' },
  parameters: { backgrounds: { default: 'dark' } },
};

export const FocusVisible: Story = {
  args: { variant: 'secondary' },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const btn = canvas.getByRole('button');
    btn.focus();
    await expect(btn).toHaveFocus();
  },
};

/* ===========================================================================
 * 5. Showcase grid : matrice 4x3 visualisee d un coup pour QA visuel.
 * =========================================================================*/

export const ShowcaseGrid: Story = {
  render: () => ({
    components: { Button },
    setup() {
      return { variants: BUTTON_VARIANTS, sizes: BUTTON_SIZES };
    },
    template: `
      <div class="space-y-6 p-4 bg-surface-bg dark:bg-surface-dark-bg">
        <div v-for="variant in variants" :key="variant" class="space-y-2">
          <h3 class="text-sm font-semibold text-surface-text dark:text-surface-dark-text capitalize">
            {{ variant }}
          </h3>
          <div class="flex items-center gap-3 flex-wrap">
            <Button v-for="size in sizes" :key="size" :variant="variant" :size="size">
              {{ variant }} {{ size }}
            </Button>
            <Button :variant="variant" loading>Loading</Button>
            <Button :variant="variant" disabled>Disabled</Button>
          </div>
        </div>
      </div>
    `,
  }),
};

export const HierarchieJuridique: Story = {
  name: 'Hierarchie juridique FR40',
  render: () => ({
    components: { Button },
    template: `
      <div class="flex gap-3 p-4">
        <Button variant="primary">Signer et figer</Button>
        <Button variant="ghost">Enregistrer brouillon</Button>
        <Button variant="secondary">Annuler</Button>
      </div>
    `,
  }),
};
