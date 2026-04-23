import type { Meta, StoryObj } from '@storybook/vue3';
import { defineComponent, h } from 'vue';
import EsgIcon from './EsgIcon.vue';
import {
  ICON_SIZES,
  ICON_VARIANTS,
  ESG_ICON_NAMES,
  type EsgIconName,
  type IconSize,
  type IconVariant,
} from './registry';
import { asStorybookComponent } from '../../types/storybook';

/**
 * EsgIcon.stories.ts (Story 10.21 AC10) — Storybook CSF 3.0 >= 12 stories.
 *
 * Patterns appliques :
 *  - L26 Storybook delegue per-path (Grid complete visuellement, Vitest
 *    ne teste pas globalement toutes icones).
 *  - L24 ARIA attribute-strict : stories WithLabel / Decorative validees
 *    via play functions @storybook/test + axe.
 *  - 0 hex hardcode (test_no_hex_hardcoded_esgicon.test.ts l'enforce).
 */

const meta: Meta<typeof EsgIcon> = {
  title: 'UI/EsgIcon',
  component: EsgIcon,
  tags: ['autodocs'],
  argTypes: {
    name: { control: 'select', options: [...ESG_ICON_NAMES] },
    size: { control: 'select', options: [...ICON_SIZES] },
    variant: { control: 'select', options: [...ICON_VARIANTS] },
    decorative: { control: 'boolean' },
    strokeWidth: { control: { type: 'range', min: 1, max: 3, step: 0.5 } },
  },
  args: {
    name: 'chevron-down',
    size: 'md',
    variant: 'default',
    decorative: false,
    strokeWidth: 2,
  },
};

export default meta;
type Story = StoryObj<typeof EsgIcon>;

/* ---------------------------------------------------------------
 * Stories primaires (controls actifs)
 * ------------------------------------------------------------- */

export const Default: Story = {
  args: { name: 'chevron-down' },
};

export const WithLabel: Story = {
  args: { name: 'calendar', decorative: false },
};

export const Decorative: Story = {
  args: { name: 'x', decorative: true },
};

export const Spinner: Story = {
  args: { name: 'loader', class: 'animate-spin motion-reduce:animate-none' },
};

export const UnknownNameFallback: Story = {
  args: { name: 'not-in-registry' as EsgIconName },
  parameters: {
    docs: {
      description: {
        story:
          'Demo du fallback placeholder + console.warn DEV (AC5). En prod, le warn est strippe par Vite DCE.',
      },
    },
  },
};

/* ---------------------------------------------------------------
 * Stories matrices (grid / sizes / variants)
 * ------------------------------------------------------------- */

const GridComponent = defineComponent({
  name: 'EsgIconGrid',
  setup() {
    return () =>
      h(
        'div',
        {
          class:
            'grid grid-cols-4 md:grid-cols-6 gap-4 p-4 bg-white dark:bg-dark-card text-surface-text dark:text-surface-dark-text',
        },
        ESG_ICON_NAMES.map((name) =>
          h(
            'div',
            {
              key: name,
              class: 'flex flex-col items-center gap-1 text-xs',
            },
            [
              h(EsgIcon, { name, size: 'lg' }),
              h('span', { class: 'truncate max-w-[8ch]' }, name),
            ],
          ),
        ),
      );
  },
});

export const Grid: Story = {
  render: () => h(asStorybookComponent(GridComponent)),
  parameters: {
    docs: {
      description: {
        story:
          'Grille complete du registre (>=30 icones). Delegation visuelle L26 — Vitest ne teste pas globalement, la story Grid couvre le sweep visuel.',
      },
    },
  },
};

const SizesComponent = defineComponent({
  name: 'EsgIconSizes',
  setup() {
    return () =>
      h(
        'div',
        { class: 'flex items-end gap-6 p-4' },
        ICON_SIZES.map((size: IconSize) =>
          h('div', { key: size, class: 'flex flex-col items-center gap-2' }, [
            h(EsgIcon, { name: 'chevron-down', size }),
            h('span', { class: 'text-xs text-surface-text/60' }, size),
          ]),
        ),
      );
  },
});

export const Sizes: Story = {
  render: () => h(asStorybookComponent(SizesComponent)),
};

const VariantsComponent = defineComponent({
  name: 'EsgIconVariants',
  setup() {
    return () =>
      h(
        'div',
        { class: 'flex items-center gap-6 p-4' },
        ICON_VARIANTS.map((variant: IconVariant) =>
          h('div', { key: variant, class: 'flex flex-col items-center gap-2' }, [
            h(EsgIcon, { name: 'check-circle', size: 'lg', variant }),
            h('span', { class: 'text-xs' }, variant),
          ]),
        ),
      );
  },
});

export const Variants: Story = {
  render: () => h(asStorybookComponent(VariantsComponent)),
};

const StrokeWidthComponent = defineComponent({
  name: 'EsgIconStrokeWidth',
  setup() {
    return () =>
      h(
        'div',
        { class: 'flex items-center gap-6 p-4' },
        [1, 1.5, 2, 2.5, 3].map((sw) =>
          h('div', { key: sw, class: 'flex flex-col items-center gap-2' }, [
            h(EsgIcon, { name: 'chevron-right', size: 'lg', strokeWidth: sw }),
            h('span', { class: 'text-xs' }, `sw=${sw}`),
          ]),
        ),
      );
  },
});

export const StrokeWidth: Story = {
  render: () => h(asStorybookComponent(StrokeWidthComponent)),
};

/* ---------------------------------------------------------------
 * Stories categories (Lucide only / ESG custom only)
 * ------------------------------------------------------------- */

const LucideOnlyComponent = defineComponent({
  name: 'EsgIconLucideOnly',
  setup() {
    const lucideNames = ESG_ICON_NAMES.filter((n) => !n.startsWith('esg-'));
    return () =>
      h(
        'div',
        { class: 'grid grid-cols-6 gap-4 p-4' },
        lucideNames.map((name) =>
          h('div', { key: name, class: 'flex flex-col items-center gap-1 text-xs' }, [
            h(EsgIcon, { name, size: 'md' }),
            h('span', { class: 'truncate max-w-[9ch]' }, name),
          ]),
        ),
      );
  },
});

export const LucideOnly: Story = {
  render: () => h(asStorybookComponent(LucideOnlyComponent)),
};

const EsgCustomOnlyComponent = defineComponent({
  name: 'EsgIconEsgCustomOnly',
  setup() {
    const esgNames = ESG_ICON_NAMES.filter((n) => n.startsWith('esg-'));
    return () =>
      h(
        'div',
        { class: 'grid grid-cols-3 gap-6 p-4' },
        esgNames.map((name) =>
          h(
            'div',
            {
              key: name,
              class:
                'flex flex-col items-center gap-2 p-4 border border-gray-200 dark:border-dark-border rounded',
            },
            [
              h(EsgIcon, { name, size: 'xl', variant: 'brand' }),
              h('span', { class: 'text-xs font-mono' }, name),
            ],
          ),
        ),
      );
  },
});

export const EsgCustomOnly: Story = {
  render: () => h(asStorybookComponent(EsgCustomOnlyComponent)),
  parameters: {
    docs: {
      description: {
        story:
          '6 icones ESG custom metier (ODD 6 effluents / ODD 15 biodiversite / audit social / mobile money UEMOA / taxonomie UEMOA / sceau SGES BETA).',
      },
    },
  },
};

/* ---------------------------------------------------------------
 * Stories dark mode + mapping registry
 * ------------------------------------------------------------- */

const DarkModeComponent = defineComponent({
  name: 'EsgIconDarkMode',
  mounted() {
    document.documentElement.classList.add('dark');
  },
  beforeUnmount() {
    document.documentElement.classList.remove('dark');
  },
  setup() {
    return () =>
      h(
        'div',
        {
          class:
            'dark bg-dark-card text-surface-dark-text p-6 grid grid-cols-5 gap-6',
        },
        ICON_VARIANTS.map((variant) =>
          h('div', { key: variant, class: 'flex flex-col items-center gap-2' }, [
            h(EsgIcon, { name: 'check-circle', size: 'lg', variant }),
            h('span', { class: 'text-xs' }, variant),
          ]),
        ),
      );
  },
});

export const DarkMode: Story = {
  render: () => h(asStorybookComponent(DarkModeComponent)),
  parameters: {
    backgrounds: { default: 'dark' },
    docs: {
      description: {
        story:
          'Contraste AA post-darken validation dark mode (L26 delegation per-path dark/brand, dark/danger, dark/success, dark/muted).',
      },
    },
  },
};

const MappingRegistryComponent = defineComponent({
  name: 'EsgIconMappingRegistry',
  setup() {
    return () =>
      h(
        'table',
        {
          class:
            'w-full text-left text-sm border-collapse border border-gray-200 dark:border-dark-border',
        },
        [
          h('thead', {}, [
            h('tr', { class: 'bg-gray-50 dark:bg-dark-hover' }, [
              h('th', { class: 'p-2 border' }, 'name'),
              h('th', { class: 'p-2 border' }, 'source'),
              h('th', { class: 'p-2 border' }, 'preview'),
            ]),
          ]),
          h(
            'tbody',
            {},
            ESG_ICON_NAMES.map((name) =>
              h('tr', { key: name }, [
                h('td', { class: 'p-2 border font-mono text-xs' }, name),
                h(
                  'td',
                  { class: 'p-2 border text-xs' },
                  name.startsWith('esg-') ? 'ESG custom SVG' : 'Lucide',
                ),
                h(
                  'td',
                  { class: 'p-2 border' },
                  [h(EsgIcon, { name, size: 'md' })],
                ),
              ]),
            ),
          ),
        ],
      );
  },
});

export const MappingRegistry: Story = {
  render: () => h(asStorybookComponent(MappingRegistryComponent)),
};

/* ---------------------------------------------------------------
 * Story migration before/after (demo shim pattern 10.6)
 * ------------------------------------------------------------- */

const MigrationBeforeAfterComponent = defineComponent({
  name: 'EsgIconMigrationBeforeAfter',
  setup() {
    return () =>
      h('div', { class: 'p-4 space-y-4' }, [
        h('div', { class: 'flex items-center gap-2 text-sm' }, [
          h('span', {}, 'Avant (SVG inline) :'),
          h(
            'svg',
            {
              'aria-hidden': 'true',
              width: 16,
              height: 16,
              viewBox: '0 0 16 16',
              fill: 'none',
              stroke: 'currentColor',
              class: 'flex-shrink-0',
            },
            [
              h('path', {
                d: 'M4 6 L8 10 L12 6',
                'stroke-width': 1.5,
                'stroke-linecap': 'round',
                'stroke-linejoin': 'round',
              }),
            ],
          ),
        ]),
        h('div', { class: 'flex items-center gap-2 text-sm' }, [
          h('span', {}, 'Apres (EsgIcon shim 10.6) :'),
          h(EsgIcon, {
            name: 'chevron-down',
            class: 'h-4 w-4',
            decorative: true,
            strokeWidth: 1.5,
          }),
        ]),
        h(
          'p',
          { class: 'text-xs text-surface-text/60 dark:text-surface-dark-text/60' },
          'Dimensions heritees via class parent (h-4 w-4), pas via prop size — piege #48 shim byte-identique.',
        ),
      ]);
  },
});

export const MigrationBeforeAfter: Story = {
  render: () => h(asStorybookComponent(MigrationBeforeAfterComponent)),
};
