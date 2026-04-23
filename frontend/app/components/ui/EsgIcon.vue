<script setup lang="ts">
/**
 * ui/EsgIcon.vue — Dispatcher iconographique projet unifie (Story 10.21).
 *
 * 23e et derniere primitive Epic 10 Phase 0 Fondations. 8e composant `ui/`.
 * Resout <EsgIcon name="..." /> vers un composant Lucide (named import
 * tree-shake) OU un SVG custom ESG (vite-svg-loader ?component) via un
 * registre frozen ICON_MAP: Record<EsgIconName, Component>.
 *
 * Patterns herites :
 *  - Lecon 24 §4quinquies (10.19) — ARIA attribute-strict valeurs literales
 *    (`aria-hidden="true"` string, pas boolean ; role="img" strict, pas mixin).
 *  - Lecon 25 §4sexies (10.20) generalisee — wrapper ne double-declare pas
 *    les props natives Lucide (`size`, `stroke-width` forward transparent).
 *  - Lecon 10.15 HIGH-2 — tokens `@theme` darken AA (brand-green AA post-darken
 *    cf. main.css, brand-red AA). Pas de hex inline dans ce fichier.
 *  - Piege #47 10.21 — named imports Lucide obligatoires (tree-shaking effectif
 *    ~1.5 KB/icone vs ~500 KB import * global). Jamais `import Lucide from`.
 *  - Piege #48 10.21 — sizing byte-identique via class parent (`h-4 w-4`),
 *    pas via prop `size` (casse le flex layout existant des primitives 10.15-20).
 *
 * Fallback warn dev-only (AC5) : si `name` absent de ICON_MAP, console.warn
 * en DEV (`import.meta.env.DEV`) + rendu placeholder cercle barre. Vite DCE
 * strippe le warn en prod (0 bloat). Pas de throw pour UX PME africaines.
 */
import { computed, h, type Component } from 'vue';
import {
  AlertCircle,
  AlertTriangle,
  Calendar,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Clock,
  Download,
  Edit,
  ExternalLink,
  Eye,
  EyeOff,
  FileText,
  Info,
  Link,
  Loader2,
  Minus,
  Plus,
  Search,
  Trash2,
  Upload,
  X,
  XCircle,
} from 'lucide-vue-next';
import EsgEffluents from '~/assets/icons/esg/effluents.svg?component';
import EsgBiodiversite from '~/assets/icons/esg/biodiversite.svg?component';
import EsgAuditSocial from '~/assets/icons/esg/audit-social.svg?component';
import EsgMobileMoney from '~/assets/icons/esg/mobile-money.svg?component';
import EsgTaxonomieUemoa from '~/assets/icons/esg/taxonomie-uemoa.svg?component';
import EsgSgesBetaSeal from '~/assets/icons/esg/sges-beta-seal.svg?component';
import type { EsgIconName, IconSize, IconVariant } from './registry';

interface EsgIconProps {
  name: EsgIconName;
  size?: IconSize;
  variant?: IconVariant;
  decorative?: boolean;
  strokeWidth?: number;
  class?: string;
}

const props = withDefaults(defineProps<EsgIconProps>(), {
  size: 'md',
  variant: 'default',
  decorative: false,
  strokeWidth: 2,
  class: '',
});

// Piege #47 : named imports exclusifs, jamais `import * as Lucide`.
const ICON_MAP: Record<EsgIconName, Component> = {
  'chevron-down': ChevronDown,
  'chevron-up': ChevronUp,
  'chevron-left': ChevronLeft,
  'chevron-right': ChevronRight,
  check: Check,
  x: X,
  calendar: Calendar,
  clock: Clock,
  'alert-circle': AlertCircle,
  'alert-triangle': AlertTriangle,
  info: Info,
  'check-circle': CheckCircle2,
  'x-circle': XCircle,
  loader: Loader2,
  search: Search,
  plus: Plus,
  minus: Minus,
  edit: Edit,
  trash: Trash2,
  eye: Eye,
  'eye-off': EyeOff,
  download: Download,
  upload: Upload,
  'file-text': FileText,
  link: Link,
  'external-link': ExternalLink,
  'esg-effluents': EsgEffluents,
  'esg-biodiversite': EsgBiodiversite,
  'esg-audit-social': EsgAuditSocial,
  'esg-mobile-money': EsgMobileMoney,
  'esg-taxonomie-uemoa': EsgTaxonomieUemoa,
  'esg-sges-beta-seal': EsgSgesBetaSeal,
};

// AC4 sizing : mapping pixels forward vers Lucide `size` prop native.
// Coherent Tailwind h-3/h-4/h-5/h-6/h-8 consommable en parallele via `class`.
const SIZE_MAP: Record<IconSize, number> = {
  xs: 12,
  sm: 16,
  md: 20,
  lg: 24,
  xl: 32,
};

// AC6 variants : tokens `@theme` uniquement (pas de hex inline).
// dark: variants 8 occurrences minimum (4 variants colorees x 2 states) pour
// AC10 plancher `dark:` scan. Lucide `stroke="currentColor"` herite la classe.
const VARIANT_MAP: Record<IconVariant, string> = {
  default: 'text-current',
  brand: 'text-brand-green dark:text-brand-green hover:text-brand-green dark:hover:text-brand-green',
  danger: 'text-brand-red dark:text-brand-red hover:text-brand-red dark:hover:text-brand-red',
  success: 'text-verdict-pass dark:text-verdict-pass',
  muted: 'text-surface-text/60 dark:text-surface-dark-text/60',
};

// AC5 — Placeholder cercle barre rendu quand `name` inconnu du registre.
// Rendu immediat via `h()` sans fichier tiers (pas besoin de SVG import).
const PlaceholderIcon: Component = {
  name: 'EsgIconPlaceholder',
  render() {
    return h(
      'svg',
      {
        xmlns: 'http://www.w3.org/2000/svg',
        viewBox: '0 0 24 24',
        fill: 'none',
        stroke: 'currentColor',
        'stroke-width': 2,
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
      },
      [
        h('circle', { cx: 12, cy: 12, r: 10 }),
        h('line', { x1: 4.93, y1: 4.93, x2: 19.07, y2: 19.07 }),
      ],
    );
  },
};

// Lecon 25 generalisee : warn dev-only loud + placeholder rendu runtime.
// Vite DCE strippe le if en prod (0 bloat).
if (import.meta.env.DEV && !(props.name in ICON_MAP)) {

  console.warn(
    `[EsgIcon] Unknown icon name: "${props.name}". Falling back to placeholder.`,
  );
}

const resolvedComponent = computed<Component>(
  () => ICON_MAP[props.name] ?? PlaceholderIcon,
);
const pixelSize = computed<number>(() => SIZE_MAP[props.size]);
const variantClass = computed<string>(() => VARIANT_MAP[props.variant]);
const finalClass = computed<string>(() =>
  [variantClass.value, props.class].filter(Boolean).join(' '),
);

// L24 §4quinquies : ARIA attribute-strict valeurs litterales stringifiees.
// `aria-hidden` doit rester string `'true'`, pas boolean `true` (L24 piege
// capitalise 10.19). Mode decoratif vs semantique mutuellement exclusifs.
const ariaAttrs = computed<
  { 'aria-hidden': 'true' } | { role: 'img'; 'aria-label': string }
>(() =>
  props.decorative
    ? { 'aria-hidden': 'true' as const }
    : { role: 'img' as const, 'aria-label': props.name },
);
</script>

<template>
  <component
    :is="resolvedComponent"
    v-bind="ariaAttrs"
    :class="finalClass"
    :size="pixelSize"
    :stroke-width="strokeWidth"
  />
</template>
