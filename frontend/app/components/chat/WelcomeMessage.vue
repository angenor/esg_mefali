<script setup lang="ts">
const mermaidDiagram = `graph TB
    A["🌿 Analyse ESG"] --> B["💰 Financement Vert"]
    A --> C["📊 Empreinte Carbone"]
    A --> D["📋 Plan d'Action"]
    style A fill:#10B981,stroke:#059669,color:#fff
    style B fill:#3B82F6,stroke:#2563EB,color:#fff
    style C fill:#8B5CF6,stroke:#7C3AED,color:#fff
    style D fill:#F59E0B,stroke:#D97706,color:#fff`
</script>

<template>
  <div class="flex flex-col items-center justify-center h-full px-6 py-12">
    <div class="max-w-lg text-center space-y-6">
      <!-- Logo / Titre -->
      <div class="w-16 h-16 mx-auto rounded-full bg-brand-green/10 flex items-center justify-center">
        <span class="text-2xl">🌍</span>
      </div>
      <h2 class="text-xl font-bold text-surface-text dark:text-surface-dark-text">
        Bienvenue sur ESG Mefali
      </h2>
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Votre conseiller IA en finance durable pour les PME africaines.
        Comment puis-je vous aider aujourd'hui ?
      </p>

      <!-- Diagramme de navigation Mermaid -->
      <div class="mt-6">
        <MermaidBlock :raw-content="mermaidDiagram" />
      </div>

      <!-- Actions rapides -->
      <div class="grid grid-cols-2 gap-3 mt-4">
        <div class="text-left p-3 rounded-lg border border-gray-200 dark:border-dark-border hover:border-brand-green dark:hover:border-brand-green transition-colors">
          <div class="text-sm font-medium text-surface-text dark:text-surface-dark-text">Analyse ESG</div>
          <div class="text-xs text-gray-400 mt-0.5">Evaluez votre conformite ESG</div>
        </div>
        <div class="text-left p-3 rounded-lg border border-gray-200 dark:border-dark-border hover:border-brand-blue dark:hover:border-brand-blue transition-colors">
          <div class="text-sm font-medium text-surface-text dark:text-surface-dark-text">Financement Vert</div>
          <div class="text-xs text-gray-400 mt-0.5">Trouvez des fonds climat</div>
        </div>
        <div class="text-left p-3 rounded-lg border border-gray-200 dark:border-dark-border hover:border-brand-purple dark:hover:border-brand-purple transition-colors">
          <div class="text-sm font-medium text-surface-text dark:text-surface-dark-text">Empreinte Carbone</div>
          <div class="text-xs text-gray-400 mt-0.5">Calculez vos emissions</div>
        </div>
        <div class="text-left p-3 rounded-lg border border-gray-200 dark:border-dark-border hover:border-brand-orange dark:hover:border-brand-orange transition-colors">
          <div class="text-sm font-medium text-surface-text dark:text-surface-dark-text">Plan d'Action</div>
          <div class="text-xs text-gray-400 mt-0.5">Creez votre feuille de route</div>
        </div>
      </div>
    </div>
  </div>
</template>
