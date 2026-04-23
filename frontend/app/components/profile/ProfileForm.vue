<script setup lang="ts">
import type { CompanyProfile, SectorEnum } from '~/types/company'

const props = defineProps<{
  profile: CompanyProfile
  identityCompletion: number
  esgCompletion: number
  overallCompletion: number
  loading: boolean
}>()

const emit = defineEmits<{
  update: [field: string, value: string | number | boolean | null]
}>()

const sectorOptions: { value: SectorEnum; label: string }[] = [
  { value: 'agriculture', label: 'Agriculture' },
  { value: 'energie', label: 'Énergie' },
  { value: 'recyclage', label: 'Recyclage' },
  { value: 'transport', label: 'Transport' },
  { value: 'construction', label: 'Construction' },
  { value: 'textile', label: 'Textile' },
  { value: 'agroalimentaire', label: 'Agroalimentaire' },
  { value: 'services', label: 'Services' },
  { value: 'commerce', label: 'Commerce' },
  { value: 'artisanat', label: 'Artisanat' },
  { value: 'autre', label: 'Autre' },
]

const identityFields = [
  { field: 'company_name', label: "Nom de l'entreprise", type: 'text' as const },
  { field: 'sector', label: 'Secteur', type: 'select' as const, options: sectorOptions },
  { field: 'sub_sector', label: 'Sous-secteur', type: 'text' as const },
  { field: 'employee_count', label: "Nombre d'employés", type: 'number' as const },
  { field: 'annual_revenue_xof', label: "Chiffre d'affaires (FCFA)", type: 'number' as const },
  { field: 'year_founded', label: 'Année de création', type: 'number' as const },
  { field: 'city', label: 'Ville', type: 'text' as const },
  { field: 'country', label: 'Pays', type: 'text' as const },
]

const esgFields = [
  { field: 'has_waste_management', label: 'Gestion des déchets', type: 'boolean' as const },
  { field: 'has_energy_policy', label: 'Politique énergétique', type: 'boolean' as const },
  { field: 'has_gender_policy', label: 'Politique genre', type: 'boolean' as const },
  { field: 'has_training_program', label: 'Programme de formation', type: 'boolean' as const },
  { field: 'has_financial_transparency', label: 'Transparence financière', type: 'boolean' as const },
  { field: 'governance_structure', label: 'Gouvernance', type: 'text' as const },
  { field: 'environmental_practices', label: 'Pratiques environnementales', type: 'text' as const },
  { field: 'social_practices', label: 'Pratiques sociales', type: 'text' as const },
]

function getFieldValue(field: string): string | number | boolean | null {
  return (props.profile as Record<string, unknown>)[field] as string | number | boolean | null
}

function handleUpdate(field: string, value: string | number | boolean | null) {
  emit('update', field, value)
}
</script>

<template>
  <div class="space-y-8">
    <!-- Progression -->
    <div class="bg-white dark:bg-dark-card rounded-xl p-6 border border-gray-200 dark:border-dark-border">
      <ProfileProgress
        :identity-completion="identityCompletion"
        :esg-completion="esgCompletion"
        :overall-completion="overallCompletion"
      />
    </div>

    <!-- Indicateur de chargement -->
    <div v-if="loading" class="flex items-center justify-center py-4">
      <div class="w-5 h-5 border-2 border-brand-green border-t-transparent rounded-full animate-spin" />
      <span class="ml-2 text-sm text-gray-500 dark:text-gray-400">Mise à jour...</span>
    </div>

    <!-- Identité & Localisation -->
    <div>
      <h3 class="text-lg font-semibold text-gray-900 dark:text-surface-dark-text mb-4 flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-blue-500" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 110 2H4a1 1 0 010-2V4zm3 1h6v4H7V5zm6 6H7v2h6v-2z" clip-rule="evenodd" />
        </svg>
        Identité & Localisation
      </h3>
      <div class="space-y-2">
        <ProfileField
          v-for="f in identityFields"
          :key="f.field"
          :label="f.label"
          :field="f.field"
          :value="getFieldValue(f.field)"
          :type="f.type"
          :options="f.type === 'select' ? f.options : undefined"
          :is-manually-edited="profile.manually_edited_fields?.includes(f.field) ?? false"
          @update="handleUpdate"
        />
      </div>
    </div>

    <!-- Critères ESG -->
    <div>
      <h3 class="text-lg font-semibold text-gray-900 dark:text-surface-dark-text mb-4 flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-emerald-500" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
        </svg>
        Critères ESG
      </h3>
      <div class="space-y-2">
        <ProfileField
          v-for="f in esgFields"
          :key="f.field"
          :label="f.label"
          :field="f.field"
          :value="getFieldValue(f.field)"
          :type="f.type"
          :is-manually-edited="profile.manually_edited_fields?.includes(f.field) ?? false"
          @update="handleUpdate"
        />
      </div>
    </div>
  </div>
</template>
