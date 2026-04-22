import type { Meta, StoryObj } from '@storybook/vue3';
import { h } from 'vue';
import Badge from './Badge.vue';
import {
  VERDICT_STATES,
  LIFECYCLE_STATES,
  ADMIN_CRITICALITIES,
  BADGE_SIZES,
} from './registry';
import type {
  VerdictState,
  LifecycleState,
  AdminCriticality,
  BadgeSize,
} from './registry';
import { asStorybookComponent } from '../../types/storybook';

/* ===========================================================================
 * Stubs SVG inline Lucide (STUB: remplace Lucide Story 10.21).
 * Chaque state a son icone mappee ; les stubs heritent de currentColor via
 * stroke="currentColor" + fill="none" — pas de hex hardcode (AC6).
 * =========================================================================*/

const stubSvg = (paths: ReturnType<typeof h>[]) =>
  h(
    'svg',
    {
      viewBox: '0 0 24 24',
      fill: 'none',
      stroke: 'currentColor',
      'stroke-width': 2,
      'stroke-linecap': 'round',
      'stroke-linejoin': 'round',
    },
    paths,
  );

// <!-- STUB: remplace par <CheckCircle /> Lucide Story 10.21 -->
const IconCheckCircle = () =>
  stubSvg([
    h('circle', { cx: 12, cy: 12, r: 10 }),
    h('path', { d: 'M9 12l2 2 4-4' }),
  ]);

// <!-- STUB: remplace par <XCircle /> Lucide Story 10.21 -->
const IconXCircle = () =>
  stubSvg([
    h('circle', { cx: 12, cy: 12, r: 10 }),
    h('path', { d: 'M15 9l-6 6M9 9l6 6' }),
  ]);

// <!-- STUB: remplace par <AlertTriangle /> Lucide Story 10.21 -->
const IconAlertTriangle = () =>
  stubSvg([
    h('path', { d: 'M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z' }),
    h('path', { d: 'M12 9v4M12 17h.01' }),
  ]);

// <!-- STUB: remplace par <Minus /> Lucide Story 10.21 -->
const IconMinus = () => stubSvg([h('path', { d: 'M5 12h14' })]);

// <!-- STUB: remplace par <FileText /> Lucide Story 10.21 (draft) -->
const IconFileText = () =>
  stubSvg([
    h('path', { d: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z' }),
    h('polyline', { points: '14 2 14 8 20 8' }),
  ]);

// <!-- STUB: remplace par <Snowflake /> Lucide Story 10.21 (snapshot_frozen) -->
const IconSnowflake = () =>
  stubSvg([
    h('path', { d: 'M12 2v20M2 12h20M5 5l14 14M19 5L5 19' }),
  ]);

// <!-- STUB: remplace par <PenLine /> Lucide Story 10.21 (signed) -->
const IconPenLine = () =>
  stubSvg([
    h('path', { d: 'M12 20h9' }),
    h('path', { d: 'M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4 12.5-12.5z' }),
  ]);

// <!-- STUB: remplace par <Download /> Lucide Story 10.21 (exported) -->
const IconDownload = () =>
  stubSvg([
    h('path', { d: 'M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4' }),
    h('polyline', { points: '7 10 12 15 17 10' }),
    h('line', { x1: 12, y1: 15, x2: 12, y2: 3 }),
  ]);

// <!-- STUB: remplace par <Send /> Lucide Story 10.21 (submitted) -->
const IconSend = () =>
  stubSvg([h('line', { x1: 22, y1: 2, x2: 11, y2: 13 }), h('polygon', { points: '22 2 15 22 11 13 2 9 22 2' })]);

// <!-- STUB: remplace par <Eye /> Lucide Story 10.21 (in_review) -->
const IconEye = () =>
  stubSvg([
    h('path', { d: 'M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z' }),
    h('circle', { cx: 12, cy: 12, r: 3 }),
  ]);

// <!-- STUB: remplace par <Check /> Lucide Story 10.21 (accepted) -->
const IconCheck = () => stubSvg([h('polyline', { points: '20 6 9 17 4 12' })]);

// <!-- STUB: remplace par <X /> Lucide Story 10.21 (rejected) -->
const IconX = () => stubSvg([h('line', { x1: 18, y1: 6, x2: 6, y2: 18 }), h('line', { x1: 6, y1: 6, x2: 18, y2: 18 })]);

// <!-- STUB: remplace par <RotateCcw /> Lucide Story 10.21 (withdrawn) -->
const IconRotateCcw = () =>
  stubSvg([
    h('polyline', { points: '1 4 1 10 7 10' }),
    h('path', { d: 'M3.51 15a9 9 0 102.13-9.36L1 10' }),
  ]);

// <!-- STUB: remplace par <CheckCircle2 /> Lucide Story 10.21 (n1) -->
const IconCheckCircle2 = () =>
  stubSvg([
    h('path', { d: 'M22 11.08V12a10 10 0 11-5.93-9.14' }),
    h('polyline', { points: '22 4 12 14.01 9 11.01' }),
  ]);

// <!-- STUB: remplace par <AlertOctagon /> Lucide Story 10.21 (n3) -->
const IconAlertOctagon = () =>
  stubSvg([
    h('polygon', { points: '7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2' }),
    h('path', { d: 'M12 8v4M12 16h.01' }),
  ]);

// Mapping state → icon stub (utilise dans render des stories).
const VERDICT_ICONS: Record<VerdictState, ReturnType<typeof h>> = {
  pass: h(IconCheckCircle),
  fail: h(IconXCircle),
  reported: h(IconAlertTriangle),
  na: h(IconMinus),
};

const LIFECYCLE_ICONS: Record<LifecycleState, ReturnType<typeof h>> = {
  draft: h(IconFileText),
  snapshot_frozen: h(IconSnowflake),
  signed: h(IconPenLine),
  exported: h(IconDownload),
  submitted: h(IconSend),
  in_review: h(IconEye),
  accepted: h(IconCheck),
  rejected: h(IconX),
  withdrawn: h(IconRotateCcw),
};

const ADMIN_ICONS: Record<AdminCriticality, ReturnType<typeof h>> = {
  n1: h(IconCheckCircle2),
  n2: h(IconAlertTriangle),
  n3: h(IconAlertOctagon),
};

const VERDICT_LABELS: Record<VerdictState, string> = {
  pass: 'Validé',
  fail: 'Non conforme',
  reported: 'À documenter',
  na: 'Non applicable',
};
const LIFECYCLE_LABELS: Record<LifecycleState, string> = {
  draft: 'Brouillon',
  snapshot_frozen: 'Figé',
  signed: 'Signé',
  exported: 'Exporté',
  submitted: 'Soumis',
  in_review: 'En revue',
  accepted: 'Accepté',
  rejected: 'Refusé',
  withdrawn: 'Retiré',
};
const ADMIN_LABELS: Record<AdminCriticality, string> = {
  n1: 'N1',
  n2: 'N2',
  n3: 'N3',
};

/* ===========================================================================
 * Meta Storybook CSF 3.0.
 * Args aplati : Storybook v8 + union discriminee Vue 3 mal compatible.
 * Le render reconstitue la prop `variant`/`state` a partir des args scalaires.
 * =========================================================================*/

type BadgeStoryArgs = {
  variant: 'verdict' | 'lifecycle' | 'admin';
  state: VerdictState | LifecycleState | AdminCriticality;
  size?: BadgeSize;
  conditional?: boolean;
};

const meta: Meta<BadgeStoryArgs> = {
  title: 'UI/Badge',
  component: asStorybookComponent<BadgeStoryArgs>(Badge),
  tags: ['autodocs'],
  parameters: { a11y: { disable: false } },
  argTypes: {
    variant: { control: 'select', options: ['verdict', 'lifecycle', 'admin'] },
    size: { control: 'select', options: [...BADGE_SIZES] },
    conditional: { control: 'boolean' },
  },
  args: {
    variant: 'verdict',
    state: 'pass',
    size: 'md',
  },
  render: (args) => ({
    components: { Badge },
    setup: () => ({ args }),
    template: `
      <div class="p-4 bg-surface-bg dark:bg-surface-dark-bg">
        <Badge v-bind="args">
          <template #icon>
            <component :is="iconFor(args)" />
          </template>
          {{ labelFor(args) }}
        </Badge>
      </div>
    `,
    methods: {
      iconFor(a: BadgeStoryArgs) {
        if (a.variant === 'verdict') return VERDICT_ICONS[a.state as VerdictState];
        if (a.variant === 'lifecycle') return LIFECYCLE_ICONS[a.state as LifecycleState];
        return ADMIN_ICONS[a.state as AdminCriticality];
      },
      labelFor(a: BadgeStoryArgs) {
        if (a.variant === 'verdict') return VERDICT_LABELS[a.state as VerdictState];
        if (a.variant === 'lifecycle') return LIFECYCLE_LABELS[a.state as LifecycleState];
        return ADMIN_LABELS[a.state as AdminCriticality];
      },
    },
  }),
};

export default meta;
type Story = StoryObj<BadgeStoryArgs>;

/* ===========================================================================
 * 1. Matrice verdict : 4 states × 3 sizes = 12 stories.
 * =========================================================================*/

export const VerdictPassSm: Story = { args: { variant: 'verdict', state: 'pass', size: 'sm' } };
export const VerdictPassMd: Story = { args: { variant: 'verdict', state: 'pass', size: 'md' } };
export const VerdictPassLg: Story = { args: { variant: 'verdict', state: 'pass', size: 'lg' } };
export const VerdictFailSm: Story = { args: { variant: 'verdict', state: 'fail', size: 'sm' } };
export const VerdictFailMd: Story = { args: { variant: 'verdict', state: 'fail', size: 'md' } };
export const VerdictFailLg: Story = { args: { variant: 'verdict', state: 'fail', size: 'lg' } };
export const VerdictReportedSm: Story = { args: { variant: 'verdict', state: 'reported', size: 'sm' } };
export const VerdictReportedMd: Story = { args: { variant: 'verdict', state: 'reported', size: 'md' } };
export const VerdictReportedLg: Story = { args: { variant: 'verdict', state: 'reported', size: 'lg' } };
export const VerdictNaSm: Story = { args: { variant: 'verdict', state: 'na', size: 'sm' } };
export const VerdictNaMd: Story = { args: { variant: 'verdict', state: 'na', size: 'md' } };
export const VerdictNaLg: Story = { args: { variant: 'verdict', state: 'na', size: 'lg' } };

/* ===========================================================================
 * 2. Verdict conditionnel italique (AC4 FR40 / Q21 Lot 4).
 * =========================================================================*/

export const VerdictPassConditional: Story = {
  args: { variant: 'verdict', state: 'pass', size: 'md', conditional: true },
};

/* ===========================================================================
 * 3. Showcase grid verdict (4 states cote a cote en md).
 * =========================================================================*/

export const VerdictShowcaseGrid: Story = {
  render: () => ({
    components: { Badge },
    setup: () => ({ VERDICT_STATES, VERDICT_ICONS, VERDICT_LABELS }),
    template: `
      <div class="flex flex-wrap gap-3 p-4 bg-surface-bg dark:bg-surface-dark-bg">
        <Badge v-for="s in VERDICT_STATES" :key="s" variant="verdict" :state="s">
          <template #icon><component :is="VERDICT_ICONS[s]" /></template>
          {{ VERDICT_LABELS[s] }}
        </Badge>
      </div>
    `,
  }),
};

/* ===========================================================================
 * 4. Matrice lifecycle : 9 states × md = 9 stories.
 * =========================================================================*/

export const LifecycleDraft: Story = { args: { variant: 'lifecycle', state: 'draft' } };
export const LifecycleSnapshotFrozen: Story = { args: { variant: 'lifecycle', state: 'snapshot_frozen' } };
export const LifecycleSigned: Story = { args: { variant: 'lifecycle', state: 'signed' } };
export const LifecycleExported: Story = { args: { variant: 'lifecycle', state: 'exported' } };
export const LifecycleSubmitted: Story = { args: { variant: 'lifecycle', state: 'submitted' } };
export const LifecycleInReview: Story = { args: { variant: 'lifecycle', state: 'in_review' } };
export const LifecycleAccepted: Story = { args: { variant: 'lifecycle', state: 'accepted' } };
export const LifecycleRejected: Story = { args: { variant: 'lifecycle', state: 'rejected' } };
export const LifecycleWithdrawn: Story = { args: { variant: 'lifecycle', state: 'withdrawn' } };

/* ===========================================================================
 * 5. Showcase grid lifecycle + dark mode lifecycle.
 * =========================================================================*/

export const LifecycleShowcaseGrid: Story = {
  render: () => ({
    components: { Badge },
    setup: () => ({ LIFECYCLE_STATES, LIFECYCLE_ICONS, LIFECYCLE_LABELS }),
    template: `
      <div class="flex flex-wrap gap-3 p-4 bg-surface-bg dark:bg-surface-dark-bg">
        <Badge v-for="s in LIFECYCLE_STATES" :key="s" variant="lifecycle" :state="s">
          <template #icon><component :is="LIFECYCLE_ICONS[s]" /></template>
          {{ LIFECYCLE_LABELS[s] }}
        </Badge>
      </div>
    `,
  }),
};

export const LifecycleDarkMode: Story = {
  parameters: { backgrounds: { default: 'dark' } },
  decorators: [
    () => ({
      template: `<div class="dark"><story /></div>`,
    }),
  ],
  render: () => ({
    components: { Badge },
    setup: () => ({ LIFECYCLE_STATES, LIFECYCLE_ICONS, LIFECYCLE_LABELS }),
    template: `
      <div class="flex flex-wrap gap-3 p-4 bg-surface-dark-bg">
        <Badge v-for="s in LIFECYCLE_STATES" :key="s" variant="lifecycle" :state="s">
          <template #icon><component :is="LIFECYCLE_ICONS[s]" /></template>
          {{ LIFECYCLE_LABELS[s] }}
        </Badge>
      </div>
    `,
  }),
};

/* ===========================================================================
 * 6. Matrice admin : 3 states × 2 sizes (sm + md) = 6 stories.
 * =========================================================================*/

export const AdminN1Sm: Story = { args: { variant: 'admin', state: 'n1', size: 'sm' } };
export const AdminN1Md: Story = { args: { variant: 'admin', state: 'n1', size: 'md' } };
export const AdminN2Sm: Story = { args: { variant: 'admin', state: 'n2', size: 'sm' } };
export const AdminN2Md: Story = { args: { variant: 'admin', state: 'n2', size: 'md' } };
export const AdminN3Sm: Story = { args: { variant: 'admin', state: 'n3', size: 'sm' } };
export const AdminN3Md: Story = { args: { variant: 'admin', state: 'n3', size: 'md' } };

/* ===========================================================================
 * 7. Showcase grid admin.
 * =========================================================================*/

export const AdminShowcaseGrid: Story = {
  render: () => ({
    components: { Badge },
    setup: () => ({ ADMIN_CRITICALITIES, ADMIN_ICONS, ADMIN_LABELS }),
    template: `
      <div class="flex flex-wrap gap-3 p-4 bg-surface-bg dark:bg-surface-dark-bg">
        <Badge v-for="s in ADMIN_CRITICALITIES" :key="s" variant="admin" :state="s">
          <template #icon><component :is="ADMIN_ICONS[s]" /></template>
          {{ ADMIN_LABELS[s] }}
        </Badge>
      </div>
    `,
  }),
};

/* ===========================================================================
 * 8. Exemples composes — Badge dans table, sidebar, dashboard (FR40 integration).
 * =========================================================================*/

export const ComposedInTable: Story = {
  render: () => ({
    components: { Badge },
    setup: () => ({ VERDICT_ICONS, VERDICT_LABELS }),
    template: `
      <table class="min-w-full text-sm bg-white dark:bg-dark-card">
        <thead><tr class="text-left border-b border-gray-200 dark:border-dark-border">
          <th class="p-2">Critère</th><th class="p-2">Verdict</th>
        </tr></thead>
        <tbody>
          <tr class="border-b border-gray-100 dark:border-dark-border">
            <td class="p-2 text-surface-text dark:text-surface-dark-text">Gouvernance ESG</td>
            <td class="p-2">
              <Badge variant="verdict" state="pass" size="sm">
                <template #icon><component :is="VERDICT_ICONS.pass" /></template>
                {{ VERDICT_LABELS.pass }}
              </Badge>
            </td>
          </tr>
          <tr>
            <td class="p-2 text-surface-text dark:text-surface-dark-text">Reporting GES</td>
            <td class="p-2">
              <Badge variant="verdict" state="reported" size="sm">
                <template #icon><component :is="VERDICT_ICONS.reported" /></template>
                {{ VERDICT_LABELS.reported }}
              </Badge>
            </td>
          </tr>
        </tbody>
      </table>
    `,
  }),
};

export const ComposedInSidebar: Story = {
  render: () => ({
    components: { Badge },
    setup: () => ({ LIFECYCLE_ICONS, LIFECYCLE_LABELS }),
    template: `
      <aside class="w-64 p-4 bg-white dark:bg-dark-card border-r border-gray-200 dark:border-dark-border">
        <h3 class="font-semibold text-surface-text dark:text-surface-dark-text mb-3">Mes dossiers</h3>
        <ul class="space-y-2">
          <li class="flex justify-between items-center text-sm">
            <span class="text-surface-text dark:text-surface-dark-text">Green Climate Fund</span>
            <Badge variant="lifecycle" state="signed" size="sm">
              <template #icon><component :is="LIFECYCLE_ICONS.signed" /></template>
              {{ LIFECYCLE_LABELS.signed }}
            </Badge>
          </li>
          <li class="flex justify-between items-center text-sm">
            <span class="text-surface-text dark:text-surface-dark-text">BOAD Agriculture</span>
            <Badge variant="lifecycle" state="in_review" size="sm">
              <template #icon><component :is="LIFECYCLE_ICONS.in_review" /></template>
              {{ LIFECYCLE_LABELS.in_review }}
            </Badge>
          </li>
        </ul>
      </aside>
    `,
  }),
};

export const ComposedDashboardHeader: Story = {
  render: () => ({
    components: { Badge },
    setup: () => ({ VERDICT_ICONS, VERDICT_LABELS }),
    template: `
      <div class="flex items-center gap-3 p-4 bg-white dark:bg-dark-card">
        <h2 class="text-lg font-semibold text-surface-text dark:text-surface-dark-text">
          Score ESG global
        </h2>
        <Badge variant="verdict" state="pass" size="lg">
          <template #icon><component :is="VERDICT_ICONS.pass" /></template>
          {{ VERDICT_LABELS.pass }}
        </Badge>
      </div>
    `,
  }),
};
