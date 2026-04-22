import type { Meta, StoryObj } from '@storybook/vue3';
import { ref } from 'vue';
import Drawer from './Drawer.vue';
import {
  DRAWER_SIDES,
  DRAWER_SIZES,
} from './registry';
import type { DrawerSide, DrawerSize } from './registry';
import { asStorybookComponent } from '../../types/storybook';

/* ===========================================================================
 * Drawer.stories.ts — Story 10.18 (pattern co-localisation 10.14+10.15+10.16+10.17).
 * CSF 3.0 + autodocs + a11y (Storybook addon-a11y runtime = delegation portail
 * leçon 10.15 HIGH-2 capitalisée infra + piège #28 codemap).
 *
 * Pattern B (comptage runtime OBLIGATOIRE post-build jq storybook-static) — voir
 * Dev Agent Record Completion Notes du story file pour le chiffre exact.
 * =========================================================================*/

type DrawerStoryArgs = {
  open: boolean;
  title: string;
  description?: string;
  side?: DrawerSide;
  size?: DrawerSize;
  trapFocus?: boolean;
  closeOnEscape?: boolean;
  closeOnOverlayClick?: boolean;
  showCloseButton?: boolean;
};

const meta: Meta<DrawerStoryArgs> = {
  title: 'UI/Drawer',
  component: asStorybookComponent<DrawerStoryArgs>(Drawer),
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
    a11y: { disable: false },
  },
  argTypes: {
    open: { control: 'boolean' },
    side: { control: 'select', options: [...DRAWER_SIDES] },
    size: { control: 'select', options: [...DRAWER_SIZES] },
    trapFocus: { control: 'boolean' },
    closeOnEscape: { control: 'boolean' },
    closeOnOverlayClick: { control: 'boolean' },
    showCloseButton: { control: 'boolean' },
    title: { control: 'text' },
    description: { control: 'text' },
  },
  args: {
    open: true,
    title: 'Panneau latéral',
    side: 'right',
    size: 'md',
    trapFocus: false,
    closeOnEscape: true,
    closeOnOverlayClick: true,
    showCloseButton: true,
  },
  render: (args) => ({
    components: { Drawer },
    setup() {
      const localOpen = ref(args.open);
      return { args, localOpen };
    },
    template: `
      <div class="min-h-screen bg-surface-bg dark:bg-surface-dark-bg p-6">
        <p class="text-surface-text dark:text-surface-dark-text">
          Contenu principal — reste lisible/interactif (role="complementary", aria-modal="false").
        </p>
        <button
          type="button"
          class="mt-4 rounded bg-brand-green text-white px-3 py-2 text-sm"
          @click="localOpen = true"
        >
          Ouvrir le drawer
        </button>
        <Drawer
          v-bind="args"
          v-model:open="localOpen"
        >
          <p class="text-sm text-surface-text dark:text-surface-dark-text">
            Contenu du drawer (slot #default).
          </p>
        </Drawer>
      </div>
    `,
  }),
};

export default meta;
type Story = StoryObj<DrawerStoryArgs>;

/* ===========================================================================
 * 1. Matrice sides x sizes (6 stories base — 4 sides × focus md + 2 sizes).
 * =========================================================================*/

export const SideRightSm: Story = {
  args: { side: 'right', size: 'sm', title: 'Drawer droite · sm' },
};
export const SideRightMd: Story = {
  args: { side: 'right', size: 'md', title: 'Drawer droite · md (default)' },
};
export const SideRightLg: Story = {
  args: { side: 'right', size: 'lg', title: 'Drawer droite · lg' },
};
export const SideLeftMd: Story = {
  args: { side: 'left', size: 'md', title: 'Drawer gauche · md' },
};
export const SideTopMd: Story = {
  args: { side: 'top', size: 'md', title: 'Drawer haut · md' },
};
export const SideBottomMd: Story = {
  args: { side: 'bottom', size: 'md', title: 'Drawer bas · md' },
};

/* ===========================================================================
 * 2. Description + slots.
 * =========================================================================*/

export const WithDescription: Story = {
  args: {
    title: 'Sources RAG',
    description: 'Citations documentaires contextuelles — reste ouvert pendant la lecture.',
  },
};

export const WithFooter: Story = {
  render: (args) => ({
    components: { Drawer },
    setup() {
      const localOpen = ref(true);
      return { args, localOpen };
    },
    template: `
      <div class="min-h-screen bg-surface-bg dark:bg-surface-dark-bg p-6">
        <Drawer v-bind="args" v-model:open="localOpen">
          <p class="text-sm text-surface-text dark:text-surface-dark-text">Contenu</p>
          <template #footer>
            <div class="flex justify-end gap-2">
              <button type="button" class="rounded border border-gray-300 dark:border-dark-border px-3 py-2 text-sm text-surface-text dark:text-surface-dark-text">
                Annuler
              </button>
              <button type="button" class="rounded bg-brand-green text-white px-3 py-2 text-sm">
                Valider
              </button>
            </div>
          </template>
        </Drawer>
      </div>
    `,
  }),
  args: { title: 'Drawer avec footer actions' },
};

/* ===========================================================================
 * 3. Dark mode (decorator appliquant la classe dark sur <html>).
 * =========================================================================*/

export const DarkMode: Story = {
  args: { title: 'Dark mode · drawer droite md' },
  decorators: [
    (story) => ({
      components: { story },
      mounted() {
        document.documentElement.classList.add('dark');
      },
      unmounted() {
        document.documentElement.classList.remove('dark');
      },
      template: '<story />',
    }),
  ],
};

/* ===========================================================================
 * 4. Focus trap opt-in (Q4 verrouillée).
 * =========================================================================*/

export const FocusTrapDisabled: Story = {
  args: {
    title: 'Focus trap OFF (default — consultation libre)',
    trapFocus: false,
  },
};

export const FocusTrapEnabled: Story = {
  args: {
    title: 'Focus trap ON (form critique opt-in)',
    trapFocus: true,
  },
};

/* ===========================================================================
 * 5. Chemins fermeture composables (AC5).
 * =========================================================================*/

export const CloseOnEscapeDisabled: Story = {
  args: {
    title: 'Escape désactivé',
    closeOnEscape: false,
    closeOnOverlayClick: true,
    showCloseButton: true,
  },
};

export const CloseOnOverlayClickDisabled: Story = {
  args: {
    title: 'Overlay click désactivé',
    closeOnEscape: true,
    closeOnOverlayClick: false,
    showCloseButton: true,
  },
};

export const NoCloseButton: Story = {
  args: {
    title: 'Close button retiré',
    showCloseButton: false,
    closeOnEscape: true,
    closeOnOverlayClick: true,
  },
};

export const AllClosingPathsDisabledWarn: Story = {
  args: {
    title: '3 chemins désactivés (console.warn dev-only — piège #32)',
    closeOnEscape: false,
    closeOnOverlayClick: false,
    showCloseButton: false,
  },
  parameters: {
    docs: {
      description: {
        story:
          'Anti-pattern documenté piège #32. Runtime console.warn dev-only alerte le développeur.',
      },
    },
  },
};

/* ===========================================================================
 * 6. Mobile fullscreen (viewport iphone6 — breakpoint <md piège #29).
 * =========================================================================*/

export const MobileFullscreen: Story = {
  args: {
    title: 'Mobile fullscreen auto (<md)',
    side: 'right',
    size: 'md',
  },
  parameters: {
    viewport: { defaultViewport: 'iphone6' },
  },
};

// H-1 10.18 post-review : bascule bottom-sheet / top-sheet mobile native
// (pattern iOS UISheetPresentationController / Android BottomSheetDialog).
export const MobileBottomSheet: Story = {
  args: {
    title: 'Mobile bottom-sheet (side=bottom, rounded-t-xl, max-h 85vh)',
    side: 'bottom',
    size: 'md',
    description: 'Pattern natif iOS/Android — affordance « glisser pour fermer ».',
  },
  parameters: {
    viewport: { defaultViewport: 'iphone6' },
    docs: {
      description: {
        story:
          'AC6 bottom-sheet bascule mobile. Sur viewport <md, side=bottom passe en pattern natif (bordure supérieure arrondie, max-height 85vh). Desktop (≥md) conserve le placement right/left classique via classes `md:*`.',
      },
    },
  },
};

export const MobileTopSheet: Story = {
  args: {
    title: 'Mobile top-sheet (side=top, rounded-b-xl, max-h 85vh)',
    side: 'top',
    size: 'md',
    description: 'Symétrie H-1 : top descend du haut (notifications, alertes).',
  },
  parameters: {
    viewport: { defaultViewport: 'iphone6' },
    docs: {
      description: {
        story:
          'AC6 top-sheet bascule mobile — cas d\'usage complémentaire au bottom-sheet (bannières système, alertes contextuelles).',
      },
    },
  },
};

// M-1 10.18 post-review : variante closeLabel i18n EN (story documentée
// pour préparation migration Growth Phase).
export const CloseLabelEnglish: Story = {
  args: {
    title: 'Close label i18n (EN)',
    closeLabel: 'Close panel',
    description: 'Demonstrates closeLabel prop for i18n-ready consumers.',
  },
  parameters: {
    docs: {
      description: {
        story:
          'M-1 capitalisation : prop closeLabel string par défaut « Fermer le panneau » (FR) — override possible pour i18n ou contextualisation (ex. « Fermer le panneau des sources »).',
      },
    },
  },
};

/* ===========================================================================
 * 7. Long scroll content (ScrollArea Reka UI AC13).
 * =========================================================================*/

export const LongScrollContent: Story = {
  render: (args) => ({
    components: { Drawer },
    setup() {
      const localOpen = ref(true);
      const paragraphs = Array.from({ length: 40 }, (_, i) => `Paragraphe ${i + 1} — lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.`);
      return { args, localOpen, paragraphs };
    },
    template: `
      <div class="min-h-screen bg-surface-bg dark:bg-surface-dark-bg p-6">
        <Drawer v-bind="args" v-model:open="localOpen">
          <p
            v-for="(p, i) in paragraphs"
            :key="i"
            class="mb-3 text-sm text-surface-text dark:text-surface-dark-text"
          >{{ p }}</p>
        </Drawer>
      </div>
    `,
  }),
  args: { title: 'Long scroll content' },
};

/* ===========================================================================
 * 8. Composed examples — consommateurs futurs Phase 1+ (Epic 13/15/19).
 * =========================================================================*/

export const ComposedSourceCitation: Story = {
  render: (args) => ({
    components: { Drawer },
    setup() {
      const localOpen = ref(true);
      return { args, localOpen };
    },
    template: `
      <div class="min-h-screen bg-surface-bg dark:bg-surface-dark-bg p-6">
        <Drawer v-bind="args" v-model:open="localOpen">
          <dl class="space-y-3 text-sm text-surface-text dark:text-surface-dark-text">
            <div>
              <dt class="font-medium">Titre</dt>
              <dd>Décret UEMOA 2023-045</dd>
            </div>
            <div>
              <dt class="font-medium">URL</dt>
              <dd>
                <a href="https://uemoa.int/fr/textes/decret-2023-045" target="_blank" rel="noopener noreferrer" class="text-brand-blue underline">
                  https://uemoa.int/fr/textes/decret-2023-045
                </a>
              </dd>
            </div>
            <div>
              <dt class="font-medium">Extrait</dt>
              <dd class="mt-1 whitespace-pre-wrap rounded bg-gray-50 dark:bg-dark-input p-2 text-xs">
                « Toute PME du secteur éligible déclare ses activités… »
              </dd>
            </div>
          </dl>
        </Drawer>
      </div>
    `,
  }),
  args: {
    title: 'Source · règle',
    description: 'Citation FR71 — Perplexity-style',
    side: 'right',
    size: 'md',
  },
};

export const ComposedIntermediaryComparator: Story = {
  render: (args) => ({
    components: { Drawer },
    setup() {
      const localOpen = ref(true);
      return { args, localOpen };
    },
    template: `
      <div class="min-h-screen bg-surface-bg dark:bg-surface-dark-bg p-6">
        <Drawer v-bind="args" v-model:open="localOpen">
          <div class="grid grid-cols-3 gap-3 text-sm text-surface-text dark:text-surface-dark-text">
            <div class="rounded border border-gray-200 dark:border-dark-border p-3">
              <h3 class="font-semibold">BAD</h3>
              <p>Afrique Ouest · 10-500k EUR</p>
            </div>
            <div class="rounded border border-gray-200 dark:border-dark-border p-3">
              <h3 class="font-semibold">BOAD</h3>
              <p>UEMOA · 50k-2M EUR</p>
            </div>
            <div class="rounded border border-gray-200 dark:border-dark-border p-3">
              <h3 class="font-semibold">FNDE</h3>
              <p>Sénégal · 5-100k EUR</p>
            </div>
          </div>
        </Drawer>
      </div>
    `,
  }),
  args: {
    title: 'Comparaison intermédiaires',
    side: 'right',
    size: 'lg',
    trapFocus: false,
  },
};

export const ComposedPeerReviewThread: Story = {
  render: (args) => ({
    components: { Drawer },
    setup() {
      const localOpen = ref(true);
      return { args, localOpen };
    },
    template: `
      <div class="min-h-screen bg-surface-bg dark:bg-surface-dark-bg p-6">
        <Drawer v-bind="args" v-model:open="localOpen">
          <div class="space-y-3 text-sm text-surface-text dark:text-surface-dark-text">
            <div class="rounded border-l-2 border-brand-green bg-gray-50 dark:bg-dark-input p-3">
              <p class="text-xs text-surface-text/70 dark:text-surface-dark-text/70">Reviewer A · il y a 2 h</p>
              <p class="mt-1">« Critère 3 — score trop généreux, manque de preuves. »</p>
            </div>
            <div class="rounded border-l-2 border-brand-blue bg-gray-50 dark:bg-dark-input p-3">
              <p class="text-xs text-surface-text/70 dark:text-surface-dark-text/70">Admin N2 · il y a 1 h</p>
              <p class="mt-1">« Accord partiel — baisse à 0.6, commentaire ajouté. »</p>
            </div>
          </div>
        </Drawer>
      </div>
    `,
  }),
  args: {
    title: 'Thread peer-review N2',
    side: 'right',
    size: 'md',
  },
};
