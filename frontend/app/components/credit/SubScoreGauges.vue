<script setup lang="ts">
defineProps<{
  solvabilityScore: number
  greenImpactScore: number
}>()
</script>

<template>
  <div class="grid grid-cols-2 gap-6">
    <div class="flex flex-col items-center">
      <ScoreGauge :score="solvabilityScore" label="Solvabilite" size="md" />
    </div>
    <div class="flex flex-col items-center">
      <ScoreGauge :score="greenImpactScore" label="Impact Vert" size="md" />
    </div>
  </div>
</template>
