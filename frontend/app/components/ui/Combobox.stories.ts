import type { Meta, StoryObj } from '@storybook/vue3';
import { ref } from 'vue';
import Combobox from './Combobox.vue';
import { COMBOBOX_MODES } from './registry';
import { asStorybookComponent } from '../../types/storybook';

/* ===========================================================================
 * Combobox.stories.ts — Story 10.19 (pattern co-localisation 10.14-10.18).
 * CSF 3.0 + autodocs + a11y runtime (delegation portail lecon 10.15 HIGH-2
 * capitalisee infra + piege #28 10.18 + piege #38 IME composition guard 10.19).
 *
 * Pattern B (comptage runtime OBLIGATOIRE jq storybook-static) — voir Dev
 * Agent Record Completion Notes pour le chiffre exact.
 * =========================================================================*/

type ComboboxOption = {
  value: string;
  label: string;
  disabled?: boolean;
  group?: string;
};

type ComboboxStoryArgs = {
  modelValue: string | string[] | null;
  options: ComboboxOption[];
  label: string;
  multiple?: boolean;
  placeholder?: string;
  emptyLabel?: string;
  searchable?: boolean;
  disabled?: boolean;
  required?: boolean;
};

const PAYS_UEMOA: ComboboxOption[] = [
  { value: 'sn', label: 'Sénégal' },
  { value: 'ci', label: "Côte d'Ivoire" },
  { value: 'bf', label: 'Burkina Faso' },
  { value: 'tg', label: 'Togo' },
  { value: 'bj', label: 'Bénin' },
  { value: 'ml', label: 'Mali' },
  { value: 'ne', label: 'Niger' },
];

const PAYS_GROUPED: ComboboxOption[] = [
  { value: 'sn', label: 'Sénégal', group: 'UEMOA' },
  { value: 'ci', label: "Côte d'Ivoire", group: 'UEMOA' },
  { value: 'bf', label: 'Burkina Faso', group: 'UEMOA' },
  { value: 'cm', label: 'Cameroun', group: 'CEMAC' },
  { value: 'ga', label: 'Gabon', group: 'CEMAC' },
  { value: 'td', label: 'Tchad', group: 'CEMAC' },
  { value: 'eg', label: 'Égypte', group: 'Autres' },
  { value: 'ma', label: 'Maroc', group: 'Autres' },
];

const SECTEURS_50: ComboboxOption[] = Array.from({ length: 50 }, (_, i) => ({
  value: `sect-${i + 1}`,
  label: `Secteur ESG n°${i + 1}`,
}));

const meta: Meta<ComboboxStoryArgs> = {
  title: 'UI/Combobox',
  component: asStorybookComponent<ComboboxStoryArgs>(Combobox),
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
    a11y: { disable: false },
  },
  argTypes: {
    multiple: { control: 'boolean' },
    searchable: { control: 'boolean' },
    disabled: { control: 'boolean' },
    required: { control: 'boolean' },
    placeholder: { control: 'text' },
    emptyLabel: { control: 'text' },
    label: { control: 'text' },
  },
  args: {
    modelValue: null,
    options: PAYS_UEMOA,
    label: 'Pays',
    multiple: false,
    searchable: true,
    placeholder: 'Sélectionner...',
    emptyLabel: 'Aucun résultat',
  },
  render: (args) => ({
    components: { Combobox },
    setup() {
      const local = ref(args.modelValue);
      return { args, local };
    },
    template: `
      <div class="p-4 min-h-[400px] bg-surface-bg dark:bg-surface-dark-bg">
        <Combobox
          v-bind="args"
          :model-value="local"
          :options="args.options"
          @update:model-value="(v) => (local = v)"
        />
        <p class="mt-3 text-sm text-surface-text/60 dark:text-surface-dark-text/60">
          Valeur selectionnée : <code>{{ JSON.stringify(local) }}</code>
        </p>
      </div>
    `,
  }),
};

export default meta;
type Story = StoryObj<ComboboxStoryArgs>;

export const SingleSelect: Story = {
  args: {
    modelValue: null,
    options: PAYS_UEMOA,
    label: 'Pays UEMOA',
  },
};

export const MultipleSelect: Story = {
  args: {
    modelValue: ['sn', 'ci'],
    options: PAYS_UEMOA,
    label: 'Pays multi-selection',
    multiple: true,
  },
};

export const WithSearchAccents: Story = {
  args: {
    modelValue: null,
    options: PAYS_UEMOA.concat([
      { value: 'eg', label: 'Égypte' },
      { value: 'ga', label: 'Gabon' },
    ]),
    label: "Recherche insensible aux accents ('egypte' → Égypte)",
    placeholder: 'Essayez : cot, sen, egypte',
  },
};

export const Grouped: Story = {
  args: {
    modelValue: null,
    options: PAYS_GROUPED,
    label: 'Pays par zone monétaire',
    placeholder: 'Zone UEMOA / CEMAC / Autres',
  },
};

export const EmptyState: Story = {
  args: {
    modelValue: null,
    options: [],
    label: 'Combobox vide',
    emptyLabel: 'Aucun résultat',
  },
};

export const EmptyStateCustomSlot: Story = {
  args: {
    modelValue: null,
    options: [],
    label: 'Empty state custom',
  },
  render: (args) => ({
    components: { Combobox },
    setup() {
      const local = ref<string | null>(null);
      return { args, local };
    },
    template: `
      <div class="p-4 bg-surface-bg dark:bg-surface-dark-bg">
        <Combobox
          v-bind="args"
          :model-value="local"
          :options="args.options"
          @update:model-value="(v) => (local = v)"
        >
          <template #empty>
            <div class="p-4 text-center">
              <p class="text-sm text-surface-text/60 dark:text-surface-dark-text/60 mb-2">
                Aucun pays ne correspond à votre recherche.
              </p>
              <button
                type="button"
                class="inline-flex items-center rounded bg-brand-green px-3 py-1 text-xs text-white"
              >
                + Ajouter un pays
              </button>
            </div>
          </template>
        </Combobox>
      </div>
    `,
  }),
};

export const LongList: Story = {
  args: {
    modelValue: null,
    options: SECTEURS_50,
    label: '50 secteurs ESG',
    placeholder: 'Filtrer parmi 50 secteurs...',
  },
};

export const DarkMode: Story = {
  args: {
    modelValue: null,
    options: PAYS_UEMOA,
    label: 'Combobox — dark mode',
  },
  decorators: [
    () => ({
      template: `
        <div class="dark bg-surface-dark-bg p-4 min-h-[300px]">
          <story />
        </div>
      `,
    }),
  ],
};

export const Disabled: Story = {
  args: {
    modelValue: 'sn',
    options: PAYS_UEMOA,
    label: 'Combobox desactive',
    disabled: true,
  },
};

/* Preserve reference pour future extensions Reka UI ComboboxMode (si exposee
 * dans les stories via dropdown de control). Pattern registry usage (10.17). */
void COMBOBOX_MODES;
