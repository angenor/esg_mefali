<!--
  ui/Drawer.vue — primitive UI Phase 0 Story 10.18 (1ere wrapper Reka UI).
  Wrapper Reka UI DialogRoot + DialogPortal + DialogOverlay + DialogContent.
  Drawer CONSULTATIF (role="complementary", aria-modal="false") != Modal bloquant (SignatureModal).
  Lecon 10.14 HIGH-2 capitalisee infra : override ARIA explicite sur DialogContent.
  4 sides x 3 sizes desktop + mobile fullscreen auto < md (768 px) CSS-only.
  Focus trap opt-in (default false — drawer permet navigation DOM externe).
  3 chemins fermeture composables (Escape + overlay click + close button).
  ScrollArea Reka UI integree pour contenu scrollable (AC13).
-->
<script setup lang="ts">
import { computed, useId } from 'vue';
import EsgIcon from './EsgIcon.vue';
import {
  DialogRoot,
  DialogPortal,
  DialogOverlay,
  DialogContent,
  DialogClose,
  DialogTitle,
  DialogDescription,
  ScrollAreaRoot,
  ScrollAreaViewport,
  ScrollAreaScrollbar,
  ScrollAreaThumb,
} from 'reka-ui';
import type { DrawerSide, DrawerSize } from './registry';

interface DrawerProps {
  open: boolean;
  title: string;
  description?: string;
  side?: DrawerSide;
  size?: DrawerSize;
  trapFocus?: boolean;
  closeOnEscape?: boolean;
  closeOnOverlayClick?: boolean;
  showCloseButton?: boolean;
  closeLabel?: string;
}

const props = withDefaults(defineProps<DrawerProps>(), {
  description: undefined,
  side: 'right',
  size: 'md',
  trapFocus: false,
  closeOnEscape: true,
  closeOnOverlayClick: true,
  showCloseButton: true,
  closeLabel: 'Fermer le panneau',
});

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void;
}>();

const titleId = useId();
const descId = useId();

const sideIsHorizontal = computed<boolean>(
  () => props.side === 'right' || props.side === 'left',
);

// Position desktop (md+) — mobile fullscreen ignore side via CSS-only
const sidePositionClasses = computed<string>(() => {
  switch (props.side) {
    case 'right':
      return 'md:right-0 md:left-auto md:top-0 md:bottom-auto md:h-full';
    case 'left':
      return 'md:left-0 md:right-auto md:top-0 md:bottom-auto md:h-full';
    case 'top':
      return 'md:top-0 md:bottom-auto md:left-0 md:right-0 md:w-full';
    case 'bottom':
      return 'md:bottom-0 md:top-auto md:left-0 md:right-0 md:w-full';
  }
  return '';
});

// Dimension desktop — width pour right/left, height pour top/bottom.
// Garde-fou max-w-[50vw] / max-h-[50vh] desktop large (piege #30).
const sizeClasses = computed<string>(() => {
  if (sideIsHorizontal.value) {
    switch (props.size) {
      case 'sm':
        return 'md:w-[320px] md:max-w-[50vw]';
      case 'md':
        return 'md:w-[480px] md:max-w-[50vw]';
      case 'lg':
        return 'md:w-[560px] md:max-w-[50vw]';
    }
  } else {
    switch (props.size) {
      case 'sm':
        return 'md:h-[320px] md:max-h-[50vh]';
      case 'md':
        return 'md:h-[480px] md:max-h-[50vh]';
      case 'lg':
        return 'md:h-[560px] md:max-h-[50vh]';
    }
  }
  return '';
});

// Mobile base CSS-only (piege #29) — override au-dela de md.
// HIGH-1 10.18 post-review : side="bottom" et side="top" basculent en
// pattern bottom-sheet / top-sheet natif (iOS UISheetPresentationController,
// Android BottomSheetDialog) au lieu de fullscreen neutre. Border-radius
// top-arrondi sur bottom, bottom-arrondi sur top, max-h 85vh, laisse
// affordance « glisser pour fermer » implicite. side=right|left restent
// fullscreen mobile (viewport deja plein sans distinction visuelle utile).
const mobileBaseClasses = computed<string>(() => {
  if (props.side === 'bottom') {
    return 'bottom-0 left-0 right-0 top-auto w-full h-auto max-h-[85vh] rounded-t-xl md:rounded-none md:inset-auto md:max-h-none';
  }
  if (props.side === 'top') {
    return 'top-0 left-0 right-0 bottom-auto w-full h-auto max-h-[85vh] rounded-b-xl md:rounded-none md:inset-auto md:max-h-none';
  }
  return 'inset-0 w-full h-full md:inset-auto';
});

// Runtime defense en profondeur (piege #32) : 3 paths disabled = utilisateur piege.
// Decision M-2 10.18 post-review : guarde `import.meta.env.DEV` CONSERVE.
// Rationale : en CI le test unit `test_drawer_behavior.test.ts` catche deja
// le scenario (Vitest tourne en mode DEV). En preview/prod le warn n'apporte
// pas de filet utile (consommateur averti ne lit pas la console). Le piege
// #32 codemap assume cette dette et reserve un audit preview manuel Phase 1.
if (import.meta.env.DEV) {
  if (
    !props.closeOnEscape &&
    !props.closeOnOverlayClick &&
    !props.showCloseButton
  ) {
    // eslint-disable-next-line no-console
    console.warn(
      '[ui/Drawer] 3 chemins fermeture desactives — risque utilisateur piege. ' +
        'Au moins 1 (closeOnEscape / closeOnOverlayClick / showCloseButton) doit rester actif.',
    );
  }
}

function handleOpenChange(value: boolean): void {
  emit('update:open', value);
}

// L-2 10.18 post-review : handlers typeds strictement (KeyboardEvent /
// PointerEvent) au lieu de Event generique. Meilleure DX + coherent Reka UI.
function handleEscapeKeyDown(e: KeyboardEvent): void {
  if (!props.closeOnEscape) {
    e.preventDefault();
  }
}

function handlePointerDownOutside(e: PointerEvent): void {
  if (!props.closeOnOverlayClick) {
    e.preventDefault();
  }
}
</script>

<template>
  <DialogRoot :open="open" @update:open="handleOpenChange">
    <DialogPortal>
      <!-- Overlay : opacite seule (pas backdrop-blur, piege #31 perf mobile).
           pointer-events conditionnel : auto si fermable au click, sinon none
           pour preserver interaction DOM dessous (sementique complementary). -->
      <DialogOverlay
        class="fixed inset-0 z-40 bg-black/50 dark:bg-black/70 motion-reduce:transition-none"
        :style="
          props.closeOnOverlayClick
            ? 'pointer-events: auto'
            : 'pointer-events: none'
        "
      />
      <!--
        DialogContent : OVERRIDE ARIA (AC3 + piege #27).
        role="complementary" remplace role="dialog" Reka UI default.
        aria-modal="false" explicite (drawer != modal bloquant).
        trap-focus passe au Reka UI natif (opt-in Q4 default false).
      -->
      <DialogContent
        role="complementary"
        aria-modal="false"
        :aria-labelledby="titleId"
        :aria-describedby="description ? descId : undefined"
        :trap-focus="trapFocus"
        :class="[
          'fixed z-50 flex flex-col bg-white dark:bg-dark-card shadow-xl border-gray-200 dark:border-dark-border motion-reduce:transition-none',
          mobileBaseClasses,
          sidePositionClasses,
          sizeClasses,
        ]"
        @escape-key-down="handleEscapeKeyDown"
        @pointer-down-outside="handlePointerDownOutside"
      >
        <!--
          Header sticky top — div au lieu de <header> pour eviter imbrication
          de landmark banner dans role="complementary" (axe landmark-banner-is-top-level).
        -->
        <div
          class="flex items-start justify-between border-b border-gray-200 dark:border-dark-border p-4"
        >
          <slot name="header">
            <div class="flex-1 min-w-0">
              <DialogTitle
                :id="titleId"
                class="text-base font-semibold text-surface-text dark:text-surface-dark-text"
              >
                {{ title }}
              </DialogTitle>
              <DialogDescription
                v-if="description"
                :id="descId"
                class="mt-1 text-sm text-surface-text/70 dark:text-surface-dark-text/70"
              >
                {{ description }}
              </DialogDescription>
            </div>
            <DialogClose
              v-if="showCloseButton"
              :aria-label="closeLabel"
              class="ml-2 rounded p-1 text-surface-text dark:text-surface-dark-text hover:bg-gray-100 dark:hover:bg-dark-hover focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-green"
            >
              <EsgIcon name="x" size="sm" decorative :stroke-width="1.5" />
            </DialogClose>
          </slot>
        </div>

        <!-- Contenu scrollable ScrollArea Reka UI (AC13 — pattern byte-identique SourceCitationDrawer) -->
        <ScrollAreaRoot class="flex-1 overflow-hidden">
          <ScrollAreaViewport class="h-full w-full p-4">
            <slot />
          </ScrollAreaViewport>
          <ScrollAreaScrollbar
            orientation="vertical"
            class="w-2 bg-gray-200 dark:bg-dark-border"
          >
            <ScrollAreaThumb class="bg-gray-400 dark:bg-dark-hover rounded" />
          </ScrollAreaScrollbar>
        </ScrollAreaRoot>

        <!-- Footer sticky bottom (optionnel) — div pour eviter landmark contentinfo imbrique. -->
        <div
          v-if="$slots.footer"
          class="border-t border-gray-200 dark:border-dark-border p-4"
        >
          <slot name="footer" />
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
