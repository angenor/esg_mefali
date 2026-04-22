import type { Meta, StoryObj } from '@storybook/vue3';
import { within, userEvent, expect, fn } from '@storybook/test';
import Textarea from './Textarea.vue';
import { FORM_SIZES } from './registry';
import type { FormSize } from './registry';
import { asStorybookComponent } from '../../types/storybook';

type TextareaStoryArgs = {
  modelValue?: string;
  label?: string;
  placeholder?: string;
  error?: string;
  hint?: string;
  required?: boolean;
  disabled?: boolean;
  readonly?: boolean;
  size?: FormSize;
  rows?: number;
  maxlength?: number;
  showCounter?: boolean;
  'onUpdate:modelValue'?: (value: string) => void;
};

const meta: Meta<TextareaStoryArgs> = {
  title: 'UI/Textarea',
  component: asStorybookComponent<TextareaStoryArgs>(Textarea),
  tags: ['autodocs'],
  parameters: { a11y: { disable: false } },
  argTypes: {
    size: { control: 'select', options: [...FORM_SIZES] },
    rows: { control: { type: 'number', min: 1, max: 20 } },
    maxlength: { control: { type: 'number', min: 50, max: 2000 } },
    showCounter: { control: 'boolean' },
    required: { control: 'boolean' },
    disabled: { control: 'boolean' },
  },
  args: {
    label: 'Justification alignement taxonomie UEMOA',
    modelValue: '',
    rows: 5,
    maxlength: 400,
    showCounter: true,
    'onUpdate:modelValue': fn(),
  },
  render: (args) => ({
    components: { Textarea },
    setup: () => ({ args }),
    template: `<div class="p-4 max-w-md bg-surface-bg dark:bg-surface-dark-bg"><Textarea v-bind="args" @update:modelValue="args['onUpdate:modelValue']" /></div>`,
  }),
};

export default meta;
type Story = StoryObj<TextareaStoryArgs>;

/* =====================================================================
 * 1. Matrice 4 states x 3 sizes = 12 stories.
 * ===================================================================*/

export const DefaultSm: Story = { args: { size: 'sm', label: 'Commentaire (sm)' } };
export const DefaultMd: Story = { args: { size: 'md', label: 'Commentaire (md)' } };
export const DefaultLg: Story = { args: { size: 'lg', label: 'Commentaire (lg)' } };

export const FilledSm: Story = {
  args: { size: 'sm', modelValue: 'Contenu deja rempli a 50 chars...' },
};
export const FilledMd: Story = {
  args: { size: 'md', modelValue: 'Contenu deja rempli a 50 chars...' },
};
export const FilledLg: Story = {
  args: { size: 'lg', modelValue: 'Contenu deja rempli a 50 chars...' },
};

export const ErrorSm: Story = {
  args: { size: 'sm', error: 'Trop court (min 20 caracteres)', modelValue: 'abc' },
};
export const ErrorMd: Story = {
  args: { size: 'md', error: 'Trop court (min 20 caracteres)', modelValue: 'abc' },
};
export const ErrorLg: Story = {
  args: { size: 'lg', error: 'Trop court (min 20 caracteres)', modelValue: 'abc' },
};

export const DisabledSm: Story = { args: { size: 'sm', disabled: true, modelValue: 'Lecture seule' } };
export const DisabledMd: Story = { args: { size: 'md', disabled: true, modelValue: 'Lecture seule' } };
export const DisabledLg: Story = { args: { size: 'lg', disabled: true, modelValue: 'Lecture seule' } };

/* =====================================================================
 * 2. Compteur 3 seuils (AC4 — triple defense spec 018).
 * ===================================================================*/

export const CounterBelow350Gray: Story = {
  args: {
    label: 'Compteur < 350 (gray)',
    modelValue: 'a'.repeat(100),
    hint: '100 chars — largement sous le seuil',
  },
};

export const CounterAt350Orange: Story = {
  args: {
    label: 'Compteur 360 (orange)',
    modelValue: 'a'.repeat(360),
    hint: 'Passe orange a partir de 350 — texte auxiliaire',
  },
};

export const CounterAt400Red: Story = {
  args: {
    label: 'Compteur 400 (rouge + aria-live)',
    modelValue: 'a'.repeat(400),
    hint: 'Limite atteinte — role=status aria-live=polite',
  },
  play: async ({ canvasElement, args }) => {
    const canvas = within(canvasElement);
    const ta = canvas.getByLabelText(/Compteur 400/);
    // Simule paste 10 caracteres supplementaires — doit etre tronque a 400.
    await userEvent.type(ta, 'abcdefghij');
    // Le compteur reste a 400 (ni 401+).
    await expect(args['onUpdate:modelValue']).toHaveBeenCalled();
    const lastCall = (args['onUpdate:modelValue'] as ReturnType<typeof fn>).mock.calls.at(-1);
    const lastValue = lastCall?.[0] as string;
    await expect(lastValue.length).toBe(400);
  },
};

export const CounterHidden: Story = {
  args: {
    label: 'Sans compteur (showCounter=false)',
    modelValue: 'Commentaire optionnel',
    showCounter: false,
    rows: 3,
  },
};

/* =====================================================================
 * 3. Autres variantes.
 * ===================================================================*/

export const Required: Story = {
  args: {
    label: 'Description du projet',
    required: true,
    hint: '400 caracteres maximum — soyez concis',
  },
};

export const Readonly: Story = {
  args: {
    label: 'Justification signee',
    modelValue: 'Ce projet s aligne sur les ODD 8 et 13 via...',
    readonly: true,
  },
};

export const LargeMaxlength: Story = {
  args: {
    label: 'Resume executif (1500 chars)',
    maxlength: 1500,
    rows: 8,
    hint: 'Limite etendue pour resumes detailles',
  },
};

export const DarkMode: Story = {
  args: { label: 'Commentaire (dark)', modelValue: 'Test dark' },
  globals: { theme: 'dark' },
  parameters: { backgrounds: { default: 'dark' } },
};

export const ShowcaseGrid: Story = {
  render: () => ({
    components: { Textarea },
    setup() {
      return { sizes: FORM_SIZES };
    },
    template: `
      <div class="space-y-6 p-4 bg-surface-bg dark:bg-surface-dark-bg">
        <div v-for="size in sizes" :key="size" class="space-y-2">
          <h3 class="text-sm font-semibold text-surface-text dark:text-surface-dark-text capitalize">
            Size: {{ size }}
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Textarea :size="size" label="Default" />
            <Textarea :size="size" label="Error" error="Obligatoire" :modelValue="'x'" />
            <Textarea :size="size" label="At 400" :modelValue="'a'.repeat(400)" />
            <Textarea :size="size" label="Disabled" disabled />
          </div>
        </div>
      </div>
    `,
  }),
};
