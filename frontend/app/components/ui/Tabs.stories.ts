import type { Meta, StoryObj } from '@storybook/vue3';
import { defineComponent, h, ref } from 'vue';
import Tabs from './Tabs.vue';
import {
  TABS_ACTIVATION_MODES,
  TABS_ORIENTATIONS,
} from './registry';
import type {
  TabsActivationMode,
  TabsOrientation,
} from './registry';
import { asStorybookComponent } from '../../types/storybook';

/* ===========================================================================
 * Tabs.stories.ts — Story 10.19 (pattern co-localisation 10.14-10.18).
 * CSF 3.0 + autodocs + a11y runtime.
 * Tabs n'est PAS portalise → moins de delegations necessaires vs Combobox.
 * =========================================================================*/

type TabItem = {
  value: string;
  label: string;
  icon?: ReturnType<typeof defineComponent>;
  disabled?: boolean;
};

type TabsStoryArgs = {
  modelValue: string;
  tabs: TabItem[];
  orientation?: TabsOrientation;
  activationMode?: TabsActivationMode;
  forceMount?: boolean;
  label?: string;
};

// Icone SVG inline placeholder (future migration Lucide 10.21 mecanique).
const IconPlaceholder = defineComponent({
  props: { d: { type: String, required: true } },
  render() {
    return h(
      'svg',
      {
        'aria-hidden': 'true',
        width: '16',
        height: '16',
        viewBox: '0 0 16 16',
        fill: 'none',
        stroke: 'currentColor',
      },
      [h('path', { d: this.d, 'stroke-width': '1.5', 'stroke-linecap': 'round' })],
    );
  },
});

const TABS_COMPARISON: TabItem[] = [
  { value: 'view', label: 'Vue comparative' },
  { value: 'detail', label: 'Détail par règle' },
  { value: 'history', label: 'Historique' },
];

const TABS_ADMIN: TabItem[] = [
  { value: 'n1', label: 'N1 — Revue' },
  { value: 'n2', label: 'N2 — Arbitrage' },
  { value: 'n3', label: 'N3 — Validation' },
  { value: 'audit', label: 'Audit log' },
];

const TABS_WITH_ICONS: TabItem[] = [
  {
    value: 'accueil',
    label: 'Accueil',
    icon: defineComponent({
      render: () => h(IconPlaceholder, { d: 'M2 8 L8 2 L14 8 M4 7 L4 14 L12 14 L12 7' }),
    }),
  },
  {
    value: 'stats',
    label: 'Statistiques',
    icon: defineComponent({
      render: () => h(IconPlaceholder, { d: 'M2 14 L2 2 M2 14 L14 14 M5 10 L5 12 M8 6 L8 12 M11 8 L11 12' }),
    }),
  },
  {
    value: 'params',
    label: 'Paramètres',
    icon: defineComponent({
      render: () => h(IconPlaceholder, { d: 'M8 2 L8 4 M8 12 L8 14 M2 8 L4 8 M12 8 L14 8 M5 5 L6 6 M10 10 L11 11' }),
    }),
  },
];

const meta: Meta<TabsStoryArgs> = {
  title: 'UI/Tabs',
  component: asStorybookComponent<TabsStoryArgs>(Tabs),
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
    a11y: { disable: false },
  },
  argTypes: {
    orientation: { control: 'select', options: [...TABS_ORIENTATIONS] },
    activationMode: {
      control: 'select',
      options: [...TABS_ACTIVATION_MODES],
    },
    forceMount: { control: 'boolean' },
    label: { control: 'text' },
  },
  args: {
    modelValue: 'view',
    tabs: TABS_COMPARISON,
    orientation: 'horizontal',
    activationMode: 'automatic',
    forceMount: false,
    label: 'Vue comparative',
  },
  render: (args) => ({
    components: { Tabs },
    setup() {
      const local = ref(args.modelValue);
      return { args, local };
    },
    template: `
      <div class="p-4 min-h-[300px] bg-surface-bg dark:bg-surface-dark-bg">
        <Tabs
          v-bind="args"
          :model-value="local"
          :tabs="args.tabs"
          @update:model-value="(v) => (local = v)"
        >
          <template v-for="tab in args.tabs" #[\`content-\${tab.value}\`] :key="tab.value">
            <div class="text-surface-text dark:text-surface-dark-text">
              Contenu de l'onglet <strong>{{ tab.label }}</strong>.
            </div>
          </template>
        </Tabs>
      </div>
    `,
  }),
};

export default meta;
type Story = StoryObj<TabsStoryArgs>;

export const Horizontal: Story = {
  args: {
    modelValue: 'view',
    tabs: TABS_COMPARISON,
    orientation: 'horizontal',
    label: 'Vue comparative',
  },
};

export const Vertical: Story = {
  args: {
    modelValue: 'n1',
    tabs: TABS_ADMIN,
    orientation: 'vertical',
    label: 'Peer-review admin',
  },
};

export const WithIcons: Story = {
  args: {
    modelValue: 'accueil',
    tabs: TABS_WITH_ICONS,
    label: 'Navigation avec icônes',
  },
};

export const Manual: Story = {
  args: {
    modelValue: 'view',
    tabs: TABS_COMPARISON,
    activationMode: 'manual',
    label: 'Activation manuelle (a11y screen reader)',
  },
};

export const LazyContent: Story = {
  args: {
    modelValue: 'view',
    tabs: TABS_COMPARISON,
    forceMount: false,
    label: 'Lazy content (default)',
  },
};

export const ForceMount: Story = {
  args: {
    modelValue: 'view',
    tabs: TABS_COMPARISON,
    forceMount: true,
    label: 'Force mount (tous les panels rendus)',
  },
};

export const Composed: Story = {
  args: {
    modelValue: 'view',
    tabs: TABS_COMPARISON,
    label: 'Contenu riche',
  },
  render: (args) => ({
    components: { Tabs },
    setup() {
      const local = ref(args.modelValue);
      return { args, local };
    },
    template: `
      <div class="p-4 bg-surface-bg dark:bg-surface-dark-bg">
        <Tabs
          v-bind="args"
          :model-value="local"
          :tabs="args.tabs"
          @update:model-value="(v) => (local = v)"
        >
          <template #content-view>
            <div class="space-y-2 text-surface-text dark:text-surface-dark-text">
              <h3 class="text-lg font-semibold">Vue comparative</h3>
              <p class="text-sm">Tableau multi-référentiels UEMOA vs CEDEAO.</p>
              <button type="button" class="inline-flex rounded bg-brand-green px-3 py-1 text-xs text-white">
                Exporter
              </button>
            </div>
          </template>
          <template #content-detail>
            <div class="text-surface-text dark:text-surface-dark-text">
              <h3 class="text-lg font-semibold">Détail par règle</h3>
              <ul class="list-disc list-inside text-sm">
                <li>Règle E-1 : émissions GES</li>
                <li>Règle S-3 : droits humains</li>
                <li>Règle G-2 : gouvernance</li>
              </ul>
            </div>
          </template>
          <template #content-history>
            <div class="text-surface-text dark:text-surface-dark-text">
              <h3 class="text-lg font-semibold">Historique</h3>
              <p class="text-sm">12 modifications depuis le 01/01/2026.</p>
            </div>
          </template>
        </Tabs>
      </div>
    `,
  }),
};

export const DarkMode: Story = {
  args: {
    modelValue: 'view',
    tabs: TABS_COMPARISON,
    label: 'Tabs — dark mode',
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
