import type { Meta, StoryObj } from '@storybook/vue3';
import { within, userEvent, expect, fn } from '@storybook/test';
import { h } from 'vue';
import Input from './Input.vue';
import { INPUT_TYPES, FORM_SIZES } from './registry';
import type { InputType, FormSize } from './registry';
import { asStorybookComponent } from '../../types/storybook';

type InputStoryArgs = {
  modelValue?: string | number;
  label?: string;
  placeholder?: string;
  error?: string;
  hint?: string;
  required?: boolean;
  disabled?: boolean;
  readonly?: boolean;
  size?: FormSize;
  type?: InputType;
  autocomplete?: string;
  inputmode?: 'text' | 'numeric' | 'decimal' | 'tel' | 'email' | 'url' | 'search' | 'none';
  'onUpdate:modelValue'?: (value: string) => void;
};

const meta: Meta<InputStoryArgs> = {
  title: 'UI/Input',
  component: asStorybookComponent<InputStoryArgs>(Input),
  tags: ['autodocs'],
  parameters: { a11y: { disable: false } },
  argTypes: {
    type: { control: 'select', options: [...INPUT_TYPES] },
    size: { control: 'select', options: [...FORM_SIZES] },
    required: { control: 'boolean' },
    disabled: { control: 'boolean' },
    readonly: { control: 'boolean' },
    label: { control: 'text' },
    placeholder: { control: 'text' },
    error: { control: 'text' },
    hint: { control: 'text' },
  },
  args: {
    label: 'Email professionnel',
    modelValue: '',
    placeholder: 'jean@entreprise.ci',
    'onUpdate:modelValue': fn(),
  },
  render: (args) => ({
    components: { Input },
    setup: () => ({ args }),
    template: `<div class="p-4 max-w-md bg-surface-bg dark:bg-surface-dark-bg"><Input v-bind="args" @update:modelValue="args['onUpdate:modelValue']" /></div>`,
  }),
};

export default meta;
type Story = StoryObj<InputStoryArgs>;

/* =====================================================================
 * 1. Matrice 4 states x 3 sizes = 12 stories (showcase exhaustif).
 * ===================================================================*/

export const DefaultSm: Story = { args: { size: 'sm', label: 'Email (sm)' } };
export const DefaultMd: Story = {
  args: { size: 'md', label: 'Email (md)' },
  play: async ({ canvasElement, args }) => {
    const canvas = within(canvasElement);
    const input = canvas.getByLabelText(/Email/);
    await userEvent.type(input, 'abc@test.ci');
    await expect(args['onUpdate:modelValue']).toHaveBeenCalled();
  },
};
export const DefaultLg: Story = { args: { size: 'lg', label: 'Email (lg)' } };

export const FocusSm: Story = {
  args: { size: 'sm', label: 'Focus sm', modelValue: 'focus' },
};
export const FocusMd: Story = {
  args: { size: 'md', label: 'Focus md', modelValue: 'focus' },
};
export const FocusLg: Story = {
  args: { size: 'lg', label: 'Focus lg', modelValue: 'focus' },
};

export const ErrorSm: Story = {
  args: { size: 'sm', label: 'Email', error: 'Format invalide', modelValue: 'nope' },
};
export const ErrorMd: Story = {
  args: { size: 'md', label: 'Email', error: 'Format invalide', modelValue: 'nope' },
};
export const ErrorLg: Story = {
  args: { size: 'lg', label: 'Email', error: 'Format invalide', modelValue: 'nope' },
};

export const DisabledSm: Story = { args: { size: 'sm', label: 'Disabled sm', disabled: true } };
export const DisabledMd: Story = { args: { size: 'md', label: 'Disabled md', disabled: true } };
export const DisabledLg: Story = { args: { size: 'lg', label: 'Disabled lg', disabled: true } };

/* =====================================================================
 * 2. Types HTML5 (7 natives supportes).
 * ===================================================================*/

export const TypeEmail: Story = {
  args: { type: 'email', label: 'Email', autocomplete: 'email' },
};
export const TypePassword: Story = {
  args: {
    type: 'password',
    label: 'Mot de passe',
    autocomplete: 'current-password',
    required: true,
  },
};
export const TypeNumberInputmode: Story = {
  args: {
    type: 'number',
    label: 'Montant (FCFA)',
    inputmode: 'numeric',
    modelValue: 0,
    hint: 'Clavier numerique iOS/Android',
  },
};
export const TypeTel: Story = {
  args: {
    type: 'tel',
    label: 'Telephone',
    autocomplete: 'tel-national',
    placeholder: '+221 XX XXX XX XX',
  },
};
export const TypeSearch: Story = {
  args: { type: 'search', label: 'Recherche', placeholder: 'Rechercher un fonds...' },
};

/* =====================================================================
 * 3. Icon slots + etats variants.
 * ===================================================================*/

const MailIcon = () =>
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
    [
      h('rect', { x: 2, y: 4, width: 20, height: 16, rx: 2 }),
      h('path', { d: 'm22 7-10 5L2 7' }),
    ],
  );

const SearchIcon = () =>
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
    [h('circle', { cx: 11, cy: 11, r: 8 }), h('path', { d: 'm21 21-4.3-4.3' })],
  );

export const WithIconLeft: Story = {
  args: { type: 'email', label: 'Email', placeholder: 'jean@entreprise.ci' },
  render: (args) => ({
    components: { Input, MailIcon },
    setup: () => ({ args }),
    template: `
      <div class="p-4 max-w-md bg-surface-bg dark:bg-surface-dark-bg">
        <Input v-bind="args" @update:modelValue="args['onUpdate:modelValue']">
          <template #iconLeft><MailIcon /></template>
        </Input>
      </div>
    `,
  }),
};

export const WithIconRight: Story = {
  args: { type: 'search', label: 'Recherche', placeholder: 'Rechercher...' },
  render: (args) => ({
    components: { Input, SearchIcon },
    setup: () => ({ args }),
    template: `
      <div class="p-4 max-w-md bg-surface-bg dark:bg-surface-dark-bg">
        <Input v-bind="args" @update:modelValue="args['onUpdate:modelValue']">
          <template #iconRight><SearchIcon /></template>
        </Input>
      </div>
    `,
  }),
};

export const Required: Story = {
  args: {
    label: 'Nom complet',
    required: true,
    hint: 'Tel que sur CNI',
  },
};

export const Readonly: Story = {
  args: {
    label: 'Identifiant',
    modelValue: 'USR-8472',
    readonly: true,
    hint: 'Non modifiable apres creation',
  },
};

export const WithHintAndError: Story = {
  args: {
    label: 'Email',
    modelValue: 'nope',
    hint: 'Utilise pour les notifications',
    error: 'Format email invalide',
  },
};

/* =====================================================================
 * 4. Dark mode + Showcase grid.
 * ===================================================================*/

export const DarkMode: Story = {
  args: { label: 'Email (dark)', hint: 'Test dark mode' },
  globals: { theme: 'dark' },
  parameters: { backgrounds: { default: 'dark' } },
};

export const ShowcaseGrid: Story = {
  render: () => ({
    components: { Input },
    setup() {
      return { sizes: FORM_SIZES, types: INPUT_TYPES };
    },
    template: `
      <div class="space-y-6 p-4 bg-surface-bg dark:bg-surface-dark-bg">
        <div v-for="size in sizes" :key="size" class="space-y-2">
          <h3 class="text-sm font-semibold text-surface-text dark:text-surface-dark-text capitalize">
            Size: {{ size }}
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Input :size="size" label="Default" placeholder="Default" />
            <Input :size="size" label="Error" error="Invalide" modelValue="x" />
            <Input :size="size" label="Disabled" disabled />
            <Input :size="size" label="Readonly" readonly modelValue="fixed" />
          </div>
        </div>
      </div>
    `,
  }),
};
