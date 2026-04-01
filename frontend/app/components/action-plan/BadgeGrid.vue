<script setup lang="ts">
import type { Badge, BadgeType } from '~/types/actionPlan'

interface Props {
  badges: Badge[]
}

defineProps<Props>()

interface BadgeDefinition {
  type: BadgeType
  icon: string
  title: string
  description: string
}

const allBadges: BadgeDefinition[] = [
  {
    type: 'first_carbon',
    icon: '🌍',
    title: 'Premier bilan carbone',
    description: 'Réalisez votre premier bilan d\'émissions carbone',
  },
  {
    type: 'esg_above_50',
    icon: '⭐',
    title: 'Score ESG > 50',
    description: 'Obtenez un score ESG supérieur à 50/100',
  },
  {
    type: 'first_application',
    icon: '📄',
    title: 'Première candidature',
    description: 'Soumettez votre premier dossier de financement',
  },
  {
    type: 'first_intermediary_contact',
    icon: '🏦',
    title: 'Premier contact intermédiaire',
    description: 'Complétez votre premier contact avec un intermédiaire financier',
  },
  {
    type: 'full_journey',
    icon: '🏆',
    title: 'Parcours complet',
    description: 'Débloquez tous les badges précédents',
  },
]

function isUnlocked(badgeType: BadgeType, badges: Badge[]): boolean {
  return badges.some(b => b.badge_type === badgeType)
}

function getUnlockedDate(badgeType: BadgeType, badges: Badge[]): string | null {
  const badge = badges.find(b => b.badge_type === badgeType)
  if (!badge) return null
  return new Date(badge.unlocked_at).toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}
</script>

<template>
  <div class="bg-white dark:bg-dark-card rounded-xl border border-gray-200 dark:border-dark-border p-5">
    <h3 class="text-sm font-semibold text-surface-text dark:text-surface-dark-text mb-4">
      Badges
    </h3>
    <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
      <div
        v-for="def in allBadges"
        :key="def.type"
        :class="[
          'flex flex-col items-center text-center p-3 rounded-lg border transition-all',
          isUnlocked(def.type, badges)
            ? 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800'
            : 'bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-dark-border opacity-50',
        ]"
      >
        <span class="text-2xl mb-1" :class="{ 'grayscale': !isUnlocked(def.type, badges) }">
          {{ def.icon }}
        </span>
        <span class="text-xs font-medium text-surface-text dark:text-surface-dark-text">
          {{ def.title }}
        </span>
        <span
          v-if="isUnlocked(def.type, badges)"
          class="text-[10px] text-amber-600 dark:text-amber-400 mt-1"
        >
          {{ getUnlockedDate(def.type, badges) }}
        </span>
        <span v-else class="text-[10px] text-gray-400 dark:text-gray-500 mt-1">
          🔒 Verrouillé
        </span>
      </div>
    </div>
  </div>
</template>
