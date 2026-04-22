import type { Meta, StoryObj } from '@storybook/vue3';
import { defineComponent, h, markRaw } from 'vue';
import Badge from './Badge.vue';
import {
  VERDICT_STATES,
  LIFECYCLE_STATES,
  ADMIN_CRITICALITIES,
  BADGE_SIZES,
  VERDICT_LABELS_FR,
  LIFECYCLE_LABELS_FR,
  ADMIN_LABELS_FR,
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
 * Patch HIGH-4 10.17 : composants-fonctions re-instancies a chaque render
 * (plus de `h(Icon)` pre-instancie au module-level — VNodes Vue sont single-use,
 * leur reuse cross-tree cause des renders vides).
 * Patch HIGH-7 10.17 : verdict.reported et admin.n2 utilisent des icones
 * DISTINCTES (ClipboardList vs UserCheck) — Regle 11 "couleur jamais seule"
 * repose aussi sur l'unicite semantique de l'icone par state.
 * Chaque stub herite de currentColor via stroke/fill — pas de hex hardcode (AC6).
 * =========================================================================*/

const defineStubIcon = (pathsBuilder: () => ReturnType<typeof h>[]) =>
  markRaw(
    defineComponent({
      name: 'StubIcon',
      setup() {
        return () =>
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
            pathsBuilder(),
          );
      },
    }),
  );

// <!-- STUB: remplace par <CheckCircle /> Lucide Story 10.21 (verdict.pass) -->
const IconCheckCircle = defineStubIcon(() => [
  h('circle', { cx: 12, cy: 12, r: 10 }),
  h('path', { d: 'M9 12l2 2 4-4' }),
]);

// <!-- STUB: remplace par <XCircle /> Lucide Story 10.21 (verdict.fail) -->
const IconXCircle = defineStubIcon(() => [
  h('circle', { cx: 12, cy: 12, r: 10 }),
  h('path', { d: 'M15 9l-6 6M9 9l6 6' }),
]);

// <!-- STUB: remplace par <ClipboardList /> Lucide Story 10.21 (verdict.reported) -->
// HIGH-7 patch : distinct de admin.n2 (UserCheck) pour eviter collision semantique.
const IconClipboardList = defineStubIcon(() => [
  h('rect', { x: 8, y: 3, width: 8, height: 4, rx: 1 }),
  h('path', { d: 'M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2' }),
  h('path', { d: 'M9 12h6M9 16h4' }),
]);

// <!-- STUB: remplace par <Minus /> Lucide Story 10.21 (verdict.na) -->
const IconMinus = defineStubIcon(() => [h('path', { d: 'M5 12h14' })]);

// <!-- STUB: remplace par <FileText /> Lucide Story 10.21 (lifecycle.draft) -->
const IconFileText = defineStubIcon(() => [
  h('path', { d: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z' }),
  h('polyline', { points: '14 2 14 8 20 8' }),
]);

// <!-- STUB: remplace par <Snowflake /> Lucide Story 10.21 (lifecycle.snapshot_frozen) -->
const IconSnowflake = defineStubIcon(() => [
  h('path', { d: 'M12 2v20M2 12h20M5 5l14 14M19 5L5 19' }),
]);

// <!-- STUB: remplace par <PenLine /> Lucide Story 10.21 (lifecycle.signed) -->
const IconPenLine = defineStubIcon(() => [
  h('path', { d: 'M12 20h9' }),
  h('path', { d: 'M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4 12.5-12.5z' }),
]);

// <!-- STUB: remplace par <Download /> Lucide Story 10.21 (lifecycle.exported) -->
const IconDownload = defineStubIcon(() => [
  h('path', { d: 'M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4' }),
  h('polyline', { points: '7 10 12 15 17 10' }),
  h('line', { x1: 12, y1: 15, x2: 12, y2: 3 }),
]);

// <!-- STUB: remplace par <Send /> Lucide Story 10.21 (lifecycle.submitted) -->
const IconSend = defineStubIcon(() => [
  h('line', { x1: 22, y1: 2, x2: 11, y2: 13 }),
  h('polygon', { points: '22 2 15 22 11 13 2 9 22 2' }),
]);

// <!-- STUB: remplace par <Eye /> Lucide Story 10.21 (lifecycle.in_review) -->
const IconEye = defineStubIcon(() => [
  h('path', { d: 'M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z' }),
  h('circle', { cx: 12, cy: 12, r: 3 }),
]);

// <!-- STUB: remplace par <Check /> Lucide Story 10.21 (lifecycle.accepted) -->
const IconCheck = defineStubIcon(() => [h('polyline', { points: '20 6 9 17 4 12' })]);

// <!-- STUB: remplace par <X /> Lucide Story 10.21 (lifecycle.rejected) -->
const IconX = defineStubIcon(() => [
  h('line', { x1: 18, y1: 6, x2: 6, y2: 18 }),
  h('line', { x1: 6, y1: 6, x2: 18, y2: 18 }),
]);

// <!-- STUB: remplace par <RotateCcw /> Lucide Story 10.21 (lifecycle.withdrawn) -->
const IconRotateCcw = defineStubIcon(() => [
  h('polyline', { points: '1 4 1 10 7 10' }),
  h('path', { d: 'M3.51 15a9 9 0 102.13-9.36L1 10' }),
]);

// <!-- STUB: remplace par <CheckCircle2 /> Lucide Story 10.21 (admin.n1) -->
const IconCheckCircle2 = defineStubIcon(() => [
  h('path', { d: 'M22 11.08V12a10 10 0 11-5.93-9.14' }),
  h('polyline', { points: '22 4 12 14.01 9 11.01' }),
]);

// <!-- STUB: remplace par <UserCheck /> Lucide Story 10.21 (admin.n2) -->
// HIGH-7 patch : icone admin-specifique (profil utilisateur) distincte de ClipboardList (verdict.reported).
const IconUserCheck = defineStubIcon(() => [
  h('path', { d: 'M16 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2' }),
  h('circle', { cx: 8.5, cy: 7, r: 4 }),
  h('polyline', { points: '17 11 19 13 23 9' }),
]);

// <!-- STUB: remplace par <AlertOctagon /> Lucide Story 10.21 (admin.n3) -->
const IconAlertOctagon = defineStubIcon(() => [
  h('polygon', { points: '7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2' }),
  h('path', { d: 'M12 8v4M12 16h.01' }),
]);

// Mapping state -> component (PAS VNode — HIGH-4 patch). Fresh instance via
// <component :is="..." /> a chaque render, no stale-VNode reuse.
const VERDICT_ICONS = {
  pass: IconCheckCircle,
  fail: IconXCircle,
  reported: IconClipboardList,
  na: IconMinus,
} as const satisfies Record<VerdictState, unknown>;

const LIFECYCLE_ICONS = {
  draft: IconFileText,
  snapshot_frozen: IconSnowflake,
  signed: IconPenLine,
  exported: IconDownload,
  submitted: IconSend,
  in_review: IconEye,
  accepted: IconCheck,
  rejected: IconX,
  withdrawn: IconRotateCcw,
} as const satisfies Record<LifecycleState, unknown>;

const ADMIN_ICONS = {
  n1: IconCheckCircle2,
  n2: IconUserCheck,
  n3: IconAlertOctagon,
} as const satisfies Record<AdminCriticality, unknown>;

/* ===========================================================================
 * Meta Storybook CSF 3.0.
 * Patch HIGH-3 10.17 : helpers `iconFor`/`labelFor` migres dans `setup()` avec
 * narrowing propre (if variant === ...) au lieu de `as` casts via `methods:`.
 * =========================================================================*/

type BadgeStoryArgs = {
  variant: 'verdict' | 'lifecycle' | 'admin';
  state: VerdictState | LifecycleState | AdminCriticality;
  size?: BadgeSize;
  conditional?: boolean;
};

function resolveIcon(args: BadgeStoryArgs) {
  if (args.variant === 'verdict') {
    return VERDICT_ICONS[args.state as VerdictState] ?? IconMinus;
  }
  if (args.variant === 'lifecycle') {
    return LIFECYCLE_ICONS[args.state as LifecycleState] ?? IconFileText;
  }
  return ADMIN_ICONS[args.state as AdminCriticality] ?? IconCheckCircle2;
}

function resolveLabel(args: BadgeStoryArgs): string {
  if (args.variant === 'verdict') {
    return VERDICT_LABELS_FR[args.state as VerdictState] ?? '';
  }
  if (args.variant === 'lifecycle') {
    return LIFECYCLE_LABELS_FR[args.state as LifecycleState] ?? '';
  }
  return ADMIN_LABELS_FR[args.state as AdminCriticality] ?? '';
}

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
    setup: () => ({
      args,
      icon: resolveIcon(args),
      label: resolveLabel(args),
    }),
    template: `
      <div class="p-4 bg-surface-bg dark:bg-surface-dark-bg">
        <Badge v-bind="args">
          <template #icon>
            <component :is="icon" />
          </template>
          {{ label }}
        </Badge>
      </div>
    `,
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

/* 2. Verdict conditionnel italique (AC4 FR40 / Q21 Lot 4). */
export const VerdictPassConditional: Story = {
  args: { variant: 'verdict', state: 'pass', size: 'md', conditional: true },
};

/* 3. Showcase grid verdict (4 states cote a cote en md). */
export const VerdictShowcaseGrid: Story = {
  render: () => ({
    components: { Badge },
    setup: () => ({ VERDICT_STATES, VERDICT_ICONS, VERDICT_LABELS_FR }),
    template: `
      <div class="flex flex-wrap gap-3 p-4 bg-surface-bg dark:bg-surface-dark-bg">
        <Badge v-for="s in VERDICT_STATES" :key="s" variant="verdict" :state="s">
          <template #icon><component :is="VERDICT_ICONS[s]" /></template>
          {{ VERDICT_LABELS_FR[s] }}
        </Badge>
      </div>
    `,
  }),
};

/* 4. Matrice lifecycle : 9 states × md = 9 stories. */
export const LifecycleDraft: Story = { args: { variant: 'lifecycle', state: 'draft' } };
export const LifecycleSnapshotFrozen: Story = { args: { variant: 'lifecycle', state: 'snapshot_frozen' } };
export const LifecycleSigned: Story = { args: { variant: 'lifecycle', state: 'signed' } };
export const LifecycleExported: Story = { args: { variant: 'lifecycle', state: 'exported' } };
export const LifecycleSubmitted: Story = { args: { variant: 'lifecycle', state: 'submitted' } };
export const LifecycleInReview: Story = { args: { variant: 'lifecycle', state: 'in_review' } };
export const LifecycleAccepted: Story = { args: { variant: 'lifecycle', state: 'accepted' } };
export const LifecycleRejected: Story = { args: { variant: 'lifecycle', state: 'rejected' } };
export const LifecycleWithdrawn: Story = { args: { variant: 'lifecycle', state: 'withdrawn' } };

/* 5. Showcase grid lifecycle + dark mode lifecycle. */
export const LifecycleShowcaseGrid: Story = {
  render: () => ({
    components: { Badge },
    setup: () => ({ LIFECYCLE_STATES, LIFECYCLE_ICONS, LIFECYCLE_LABELS_FR }),
    template: `
      <div class="flex flex-wrap gap-3 p-4 bg-surface-bg dark:bg-surface-dark-bg">
        <Badge v-for="s in LIFECYCLE_STATES" :key="s" variant="lifecycle" :state="s">
          <template #icon><component :is="LIFECYCLE_ICONS[s]" /></template>
          {{ LIFECYCLE_LABELS_FR[s] }}
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
    setup: () => ({ LIFECYCLE_STATES, LIFECYCLE_ICONS, LIFECYCLE_LABELS_FR }),
    template: `
      <div class="flex flex-wrap gap-3 p-4 bg-surface-dark-bg">
        <Badge v-for="s in LIFECYCLE_STATES" :key="s" variant="lifecycle" :state="s">
          <template #icon><component :is="LIFECYCLE_ICONS[s]" /></template>
          {{ LIFECYCLE_LABELS_FR[s] }}
        </Badge>
      </div>
    `,
  }),
};

/* 6. Matrice admin : 3 states × 2 sizes (sm + md) = 6 stories. */
export const AdminN1Sm: Story = { args: { variant: 'admin', state: 'n1', size: 'sm' } };
export const AdminN1Md: Story = { args: { variant: 'admin', state: 'n1', size: 'md' } };
export const AdminN2Sm: Story = { args: { variant: 'admin', state: 'n2', size: 'sm' } };
export const AdminN2Md: Story = { args: { variant: 'admin', state: 'n2', size: 'md' } };
export const AdminN3Sm: Story = { args: { variant: 'admin', state: 'n3', size: 'sm' } };
export const AdminN3Md: Story = { args: { variant: 'admin', state: 'n3', size: 'md' } };

/* 7. Showcase grid admin. */
export const AdminShowcaseGrid: Story = {
  render: () => ({
    components: { Badge },
    setup: () => ({ ADMIN_CRITICALITIES, ADMIN_ICONS, ADMIN_LABELS_FR }),
    template: `
      <div class="flex flex-wrap gap-3 p-4 bg-surface-bg dark:bg-surface-dark-bg">
        <Badge v-for="s in ADMIN_CRITICALITIES" :key="s" variant="admin" :state="s">
          <template #icon><component :is="ADMIN_ICONS[s]" /></template>
          {{ ADMIN_LABELS_FR[s] }}
        </Badge>
      </div>
    `,
  }),
};

/* 8. Exemples composes — Badge dans table, sidebar, dashboard (FR40 integration). */
export const ComposedInTable: Story = {
  render: () => ({
    components: { Badge },
    setup: () => ({ VERDICT_ICONS, VERDICT_LABELS_FR }),
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
                {{ VERDICT_LABELS_FR.pass }}
              </Badge>
            </td>
          </tr>
          <tr>
            <td class="p-2 text-surface-text dark:text-surface-dark-text">Reporting GES</td>
            <td class="p-2">
              <Badge variant="verdict" state="reported" size="sm">
                <template #icon><component :is="VERDICT_ICONS.reported" /></template>
                {{ VERDICT_LABELS_FR.reported }}
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
    setup: () => ({ LIFECYCLE_ICONS, LIFECYCLE_LABELS_FR }),
    template: `
      <aside class="w-64 p-4 bg-white dark:bg-dark-card border-r border-gray-200 dark:border-dark-border">
        <h3 class="font-semibold text-surface-text dark:text-surface-dark-text mb-3">Mes dossiers</h3>
        <ul class="space-y-2">
          <li class="flex justify-between items-center text-sm">
            <span class="text-surface-text dark:text-surface-dark-text">Green Climate Fund</span>
            <Badge variant="lifecycle" state="signed" size="sm">
              <template #icon><component :is="LIFECYCLE_ICONS.signed" /></template>
              {{ LIFECYCLE_LABELS_FR.signed }}
            </Badge>
          </li>
          <li class="flex justify-between items-center text-sm">
            <span class="text-surface-text dark:text-surface-dark-text">BOAD Agriculture</span>
            <Badge variant="lifecycle" state="in_review" size="sm">
              <template #icon><component :is="LIFECYCLE_ICONS.in_review" /></template>
              {{ LIFECYCLE_LABELS_FR.in_review }}
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
    setup: () => ({ VERDICT_ICONS, VERDICT_LABELS_FR }),
    template: `
      <div class="flex items-center gap-3 p-4 bg-white dark:bg-dark-card">
        <h2 class="text-lg font-semibold text-surface-text dark:text-surface-dark-text">
          Score ESG global
        </h2>
        <Badge variant="verdict" state="pass" size="lg">
          <template #icon><component :is="VERDICT_ICONS.pass" /></template>
          {{ VERDICT_LABELS_FR.pass }}
        </Badge>
      </div>
    `,
  }),
};
