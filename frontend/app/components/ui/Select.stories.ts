import type { Meta, StoryObj } from '@storybook/vue3';
import { within, userEvent, expect, fn } from '@storybook/test';
import Select from './Select.vue';
import { FORM_SIZES } from './registry';
import type { FormSize } from './registry';
import { asStorybookComponent } from '../../types/storybook';

type SelectOption = { value: string; label: string; disabled?: boolean };

type SelectStoryArgs = {
  modelValue?: string | string[];
  label?: string;
  options?: SelectOption[];
  placeholder?: string;
  error?: string;
  hint?: string;
  required?: boolean;
  disabled?: boolean;
  size?: FormSize;
  multiple?: boolean;
  'onUpdate:modelValue'?: (value: string | string[]) => void;
};

const SECTORS: SelectOption[] = [
  { value: 'agri', label: 'Agriculture' },
  { value: 'energy', label: 'Energie' },
  { value: 'waste', label: 'Recyclage / Dechets' },
  { value: 'transport', label: 'Transport (bientot)', disabled: true },
  { value: 'industry', label: 'Industrie' },
];

const ODDS: SelectOption[] = [
  { value: '8', label: 'ODD 8 — Travail decent' },
  { value: '9', label: 'ODD 9 — Innovation' },
  { value: '10', label: 'ODD 10 — Inclusion financiere' },
  { value: '12', label: 'ODD 12 — Production responsable' },
  { value: '13', label: 'ODD 13 — Climat' },
  { value: '17', label: 'ODD 17 — Partenariats' },
];

const meta: Meta<SelectStoryArgs> = {
  title: 'UI/Select',
  component: asStorybookComponent<SelectStoryArgs>(Select),
  tags: ['autodocs'],
  parameters: { a11y: { disable: false } },
  argTypes: {
    size: { control: 'select', options: [...FORM_SIZES] },
    required: { control: 'boolean' },
    disabled: { control: 'boolean' },
    multiple: { control: 'boolean' },
  },
  args: {
    label: 'Secteur d activite',
    options: SECTORS,
    modelValue: '',
    placeholder: '-- Selectionner un secteur --',
    'onUpdate:modelValue': fn(),
  },
  render: (args) => ({
    components: { Select },
    setup: () => ({ args }),
    template: `<div class="p-4 max-w-md bg-surface-bg dark:bg-surface-dark-bg"><Select v-bind="args" @update:modelValue="args['onUpdate:modelValue']" /></div>`,
  }),
};

export default meta;
type Story = StoryObj<SelectStoryArgs>;

/* =====================================================================
 * 1. Matrice 4 states x 3 sizes = 12 stories.
 * ===================================================================*/

export const DefaultSm: Story = { args: { size: 'sm', label: 'Secteur (sm)' } };
export const DefaultMd: Story = {
  args: { size: 'md', label: 'Secteur (md)' },
  play: async ({ canvasElement, args }) => {
    const canvas = within(canvasElement);
    const sel = canvas.getByLabelText(/Secteur/);
    await userEvent.selectOptions(sel, 'energy');
    await expect(args['onUpdate:modelValue']).toHaveBeenCalledWith('energy');
  },
};
export const DefaultLg: Story = { args: { size: 'lg', label: 'Secteur (lg)' } };

export const SelectedSm: Story = { args: { size: 'sm', modelValue: 'agri' } };
export const SelectedMd: Story = { args: { size: 'md', modelValue: 'agri' } };
export const SelectedLg: Story = { args: { size: 'lg', modelValue: 'agri' } };

export const ErrorSm: Story = {
  args: { size: 'sm', error: 'Secteur obligatoire', modelValue: '' },
};
export const ErrorMd: Story = {
  args: { size: 'md', error: 'Secteur obligatoire', modelValue: '' },
};
export const ErrorLg: Story = {
  args: { size: 'lg', error: 'Secteur obligatoire', modelValue: '' },
};

export const DisabledSm: Story = { args: { size: 'sm', disabled: true } };
export const DisabledMd: Story = { args: { size: 'md', disabled: true } };
export const DisabledLg: Story = { args: { size: 'lg', disabled: true } };

/* =====================================================================
 * 2. Multiple + DisabledOption + variantes.
 * ===================================================================*/

export const Multiple: Story = {
  args: {
    label: 'ODD cibles (selection multiple)',
    options: ODDS,
    modelValue: ['8', '13'],
    multiple: true,
    hint: 'Cmd/Ctrl + clic pour selection multiple',
  },
};

export const DisabledOption: Story = {
  args: {
    label: 'Secteur (option disabled)',
    options: SECTORS,
    hint: 'Transport sera active en Phase 2',
  },
};

export const Required: Story = {
  args: {
    label: 'Secteur d activite',
    required: true,
    hint: 'Influence le scoring ESG sectoriel UEMOA',
  },
};

export const WithHint: Story = {
  args: {
    label: 'Type d entreprise',
    options: [
      { value: 'sarl', label: 'SARL' },
      { value: 'sa', label: 'SA' },
      { value: 'sas', label: 'SAS' },
      { value: 'ei', label: 'Entreprise individuelle' },
    ],
    hint: 'Selon Acte Uniforme OHADA',
  },
};

export const DarkMode: Story = {
  args: { label: 'Secteur (dark)' },
  globals: { theme: 'dark' },
  parameters: { backgrounds: { default: 'dark' } },
};

export const ShowcaseGrid: Story = {
  render: () => ({
    components: { Select },
    setup() {
      return { sizes: FORM_SIZES, sectors: SECTORS, odds: ODDS };
    },
    template: `
      <div class="space-y-6 p-4 bg-surface-bg dark:bg-surface-dark-bg">
        <div v-for="size in sizes" :key="size" class="space-y-2">
          <h3 class="text-sm font-semibold text-surface-text dark:text-surface-dark-text capitalize">
            Size: {{ size }}
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Select :size="size" label="Default" :options="sectors" placeholder="-- Choisir --" />
            <Select :size="size" label="Selectionne" :options="sectors" modelValue="agri" />
            <Select :size="size" label="Error" :options="sectors" error="Obligatoire" />
            <Select :size="size" label="Disabled" :options="sectors" disabled />
          </div>
        </div>
      </div>
    `,
  }),
};
