<script setup lang="ts">
/**
 * `ui/Tabs.vue` (Story 10.19 AC7-AC12) — wrapper Reka UI `<TabsRoot>` + list/trigger/content.
 *
 * Fournit :
 *  - orientation `horizontal` (default) / `vertical` avec indicateurs underline
 *    (border-b-2 horizontal, border-l-2 vertical),
 *  - activationMode `automatic` (focus = active) / `manual` (focus + Enter/Space),
 *  - forceMount lazy (default false : tabpanel inactif non monte DOM) — piege #37
 *    codemap : prop presence Reka UI → `forceMount || undefined` requis,
 *  - ARIA role="tablist"/"tab"/"tabpanel" + aria-orientation + aria-selected natifs Reka UI,
 *  - keyboard ArrowLeft/Right (horizontal) / ArrowUp/Down (vertical) + Home/End + cycle
 *    infini + skip disabled natifs Reka UI,
 *  - slot `content-${tab.value}` par onglet + fallback slot par defaut.
 *
 * Voir :
 *  - docs/CODEMAPS/ui-primitives.md §3.7 Tabs (exemples Vue + pieges 35-40)
 *  - registry.ts TABS_ORIENTATIONS + TABS_ACTIVATION_MODES + types derives.
 */
import { computed } from 'vue';
import type { Component } from 'vue';
import { TabsContent, TabsList, TabsRoot, TabsTrigger } from 'reka-ui';
import type { TabsActivationMode, TabsOrientation } from './registry';

export interface TabItem {
  /** Identifiant canonique (string) — utilise comme modelValue + v-model key. */
  value: string;
  /** Libelle affiche dans le trigger (traductions UI assurees cote consommateur). */
  label: string;
  /**
   * Icone optionnelle (Vue component) affichee avant le label. Future-compat
   * Lucide 10.21 (migration mecanique SVG inline → `<ChevronDown />` etc.).
   */
  icon?: Component;
  /** Tab non-selectionnable (skippe keyboard + opacite reduite). */
  disabled?: boolean;
}

export interface TabsProps {
  /** Valeur de l'onglet actif (v-model). */
  modelValue: string;
  /** Liste des onglets (≥ 1 recommande, vide autorise — render no-op). */
  tabs: TabItem[];
  /** horizontal (default) ou vertical. */
  orientation?: TabsOrientation;
  /** automatic (default WAI-ARIA) ou manual (focus + Enter/Space). */
  activationMode?: TabsActivationMode;
  /**
   * Si true, tous les tabpanels sont rendus simultanement (l'inactif reste `hidden`).
   * Utile pour (a) eviter re-renders formulaires couteux, (b) searchability Ctrl+F.
   * Piege #37 : Reka UI traite forceMount comme prop presence → ici on passe
   * `forceMount || undefined` aux TabsContent pour desactiver proprement.
   */
  forceMount?: boolean;
  /** aria-label optionnel sur TabsList (recommande a11y si pas de contexte clair). */
  label?: string;
}

const props = withDefaults(defineProps<TabsProps>(), {
  orientation: 'horizontal',
  activationMode: 'automatic',
  forceMount: false,
  label: undefined,
});

defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();

defineSlots<{
  /** Slot dynamique `content-${tab.value}` injecte par onglet. */
  [key: `content-${string}`]: (props: { tab: TabItem }) => unknown;
  /** Fallback rendu si aucun slot nomme fourni pour l'onglet courant. */
  fallback?: (props: { tab: TabItem }) => unknown;
}>();

const orientationClasses = computed(() => {
  if (props.orientation === 'vertical') {
    return {
      root: 'flex flex-row gap-4',
      list: 'flex flex-col border-r border-gray-200 dark:border-dark-border',
      triggerBase:
        'px-4 py-2 -mr-px border-r-2 border-transparent text-left text-sm',
      triggerActive:
        'border-r-2 border-brand-green text-brand-green dark:text-brand-green dark:border-brand-green',
    } as const;
  }
  return {
    root: 'flex flex-col',
    list: 'flex flex-row border-b border-gray-200 dark:border-dark-border',
    triggerBase:
      'px-4 py-2 -mb-px border-b-2 border-transparent text-sm',
    triggerActive:
      'border-b-2 border-brand-green text-brand-green dark:text-brand-green dark:border-brand-green',
  } as const;
});

// Piege #37 : forceMount doit etre `undefined` (pas `false`) pour que Reka UI
// ne le considere pas comme active. On le calcule une fois ici pour clarte.
const forceMountProp = computed<true | undefined>(() =>
  props.forceMount ? true : undefined
);
</script>

<template>
  <TabsRoot
    :model-value="modelValue"
    :orientation="orientation"
    :activation-mode="activationMode"
    :class="['w-full', orientationClasses.root]"
    @update:model-value="(v: string | number) => $emit('update:modelValue', String(v))"
  >
    <TabsList
      :aria-label="label"
      :class="orientationClasses.list"
    >
      <TabsTrigger
        v-for="tab in tabs"
        :key="tab.value"
        :value="tab.value"
        :disabled="tab.disabled"
        :class="[
          orientationClasses.triggerBase,
          'text-surface-text dark:text-surface-dark-text hover:bg-gray-50 dark:hover:bg-dark-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-green dark:focus-visible:ring-brand-green motion-reduce:transition-none',
          modelValue === tab.value ? orientationClasses.triggerActive : '',
          tab.disabled ? 'opacity-50 cursor-not-allowed dark:opacity-50' : '',
        ]"
      >
        <component
          :is="tab.icon"
          v-if="tab.icon"
          class="mr-2 h-4 w-4 inline-block align-[-2px]"
          aria-hidden="true"
        />
        {{ tab.label }}
      </TabsTrigger>
    </TabsList>
    <TabsContent
      v-for="tab in tabs"
      :key="tab.value"
      :value="tab.value"
      :force-mount="forceMountProp"
      :tabindex="0"
      :class="[
        'p-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-green dark:focus-visible:ring-brand-green text-surface-text dark:text-surface-dark-text',
        orientation === 'vertical' ? 'flex-1' : '',
      ]"
    >
      <slot :name="`content-${tab.value}`" :tab="tab">
        <slot name="fallback" :tab="tab" />
      </slot>
    </TabsContent>
  </TabsRoot>
</template>
