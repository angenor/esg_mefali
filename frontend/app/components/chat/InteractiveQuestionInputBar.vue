<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type {
  InteractiveQuestion,
  InteractiveQuestionAnswer,
} from '~/types/interactive-question'

interface Props {
  question: InteractiveQuestion
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
})

const emit = defineEmits<{
  (e: 'submit', payload: InteractiveQuestionAnswer): void
  (e: 'abandon-and-send', content: string): void
}>()

const isQcu = computed(() =>
  props.question.question_type === 'qcu' ||
  props.question.question_type === 'qcu_justification',
)
const isQcm = computed(() =>
  props.question.question_type === 'qcm' ||
  props.question.question_type === 'qcm_justification',
)
const requiresJustification = computed(() => props.question.requires_justification)

// Etat QCU
const selectedQcu = ref<string | null>(null)
// Etat QCM
const selectedQcm = ref<Set<string>>(new Set())
// Etat justification
const justification = ref('')
// Etat fallback texte libre
const showFallback = ref(false)
const fallbackText = ref('')

// Reset quand la question change
watch(
  () => props.question.id,
  () => {
    selectedQcu.value = null
    selectedQcm.value = new Set()
    justification.value = ''
    showFallback.value = false
    fallbackText.value = ''
  },
)

const selectedCount = computed(() => selectedQcm.value.size)

const canSubmit = computed(() => {
  if (props.loading) return false
  if (isQcu.value && !selectedQcu.value) return false
  if (isQcm.value) {
    const c = selectedCount.value
    if (c < props.question.min_selections || c > props.question.max_selections) return false
  }
  if (requiresJustification.value && justification.value.trim().length === 0) return false
  return true
})

function onClickQcu(optionId: string) {
  if (props.loading) return
  selectedQcu.value = optionId
  // QCU sans justification : submit immediat
  if (!requiresJustification.value) {
    doSubmit()
  }
}

function toggleQcm(optionId: string) {
  if (props.loading) return
  const next = new Set(selectedQcm.value)
  if (next.has(optionId)) {
    next.delete(optionId)
  } else if (next.size < props.question.max_selections) {
    next.add(optionId)
  }
  selectedQcm.value = next
}

function isQcmChecked(optionId: string): boolean {
  return selectedQcm.value.has(optionId)
}

function canCheckMoreQcm(): boolean {
  return selectedCount.value < props.question.max_selections
}

function doSubmit() {
  if (!canSubmit.value) return
  const values = isQcu.value
    ? [selectedQcu.value!]
    : Array.from(selectedQcm.value)
  emit('submit', {
    values,
    justification: requiresJustification.value ? justification.value : undefined,
  })
}

function revealFallback() {
  showFallback.value = true
}

function cancelFallback() {
  showFallback.value = false
  fallbackText.value = ''
}

function sendFallback() {
  const content = fallbackText.value.trim()
  if (!content || props.loading) return
  emit('abandon-and-send', content)
  fallbackText.value = ''
  showFallback.value = false
}

function onFallbackKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendFallback()
  }
}
</script>

<template>
  <!-- Bottom sheet animé : slide-up à l'apparition -->
  <div
    class="iq-sheet relative rounded-t-3xl border-t border-x border-indigo-200/60 dark:border-indigo-700/40 bg-gradient-to-b from-indigo-50 via-white to-white dark:from-indigo-900/30 dark:via-dark-card dark:to-dark-card shadow-[0_-12px_40px_-8px_rgba(99,102,241,0.35)] dark:shadow-[0_-12px_40px_-8px_rgba(99,102,241,0.5)] overflow-hidden"
  >
    <!-- Accent gradient animé en haut -->
    <div class="iq-sheet__accent h-1.5 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-[length:200%_100%]" />

    <!-- Handle (poignée de bottom sheet) -->
    <div class="flex justify-center pt-2">
      <div class="w-10 h-1 rounded-full bg-gradient-to-r from-indigo-300 to-purple-300 dark:from-indigo-600 dark:to-purple-600" />
    </div>

    <div class="px-4 pt-2 pb-3">
      <!-- Badge + prompt de la question -->
      <div class="flex items-start gap-2.5 mb-3">
        <div
          class="flex-shrink-0 w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold shadow-md shadow-indigo-500/30"
        >
          ?
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-[10px] uppercase tracking-wider text-indigo-600 dark:text-indigo-400 font-bold mb-0.5">
            Question interactive
          </p>
          <p class="text-sm font-semibold text-surface-text dark:text-surface-dark-text leading-snug">
            {{ question.prompt }}
          </p>
        </div>
      </div>

      <!-- MODE FALLBACK : textarea reponse libre -->
      <div v-if="showFallback">
        <div
          class="rounded-2xl border-2 border-dashed border-indigo-300 dark:border-indigo-700 bg-white/80 dark:bg-dark-input/80 backdrop-blur-sm p-3"
        >
          <textarea
            v-model="fallbackText"
            :disabled="loading"
            rows="3"
            maxlength="2000"
            placeholder="Tapez votre reponse libre ici..."
            class="w-full resize-none bg-transparent text-sm text-surface-text dark:text-surface-dark-text placeholder-gray-400 focus:outline-none"
            @keydown="onFallbackKeydown"
          />
          <div class="flex items-center justify-between mt-2 pt-2 border-t border-dashed border-indigo-200 dark:border-indigo-800">
            <button
              type="button"
              class="text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 font-medium"
              :disabled="loading"
              @click="cancelFallback"
            >
              ← Revenir aux options
            </button>
            <button
              type="button"
              :disabled="!fallbackText.trim() || loading"
              class="px-4 py-1.5 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-xs font-semibold disabled:opacity-40 disabled:cursor-not-allowed hover:shadow-lg hover:shadow-indigo-500/30 transition-all"
              @click="sendFallback"
            >
              Envoyer
            </button>
          </div>
        </div>
      </div>

      <!-- MODE QCU : grille d'options -->
      <div v-else-if="isQcu" class="space-y-3">
        <div
          :class="[
            'grid gap-2',
            question.options.length === 2 ? 'sm:grid-cols-2' : '',
            question.options.length === 3 ? 'sm:grid-cols-3' : '',
            question.options.length >= 4 ? 'sm:grid-cols-2' : '',
          ]"
        >
          <button
            v-for="option in question.options"
            :key="option.id"
            type="button"
            role="radio"
            :aria-checked="selectedQcu === option.id"
            :disabled="loading"
            :class="[
              'group relative px-4 py-3 rounded-2xl border-2 text-left transition-all duration-200',
              'focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:focus:ring-offset-dark-card',
              selectedQcu === option.id
                ? 'border-indigo-500 bg-gradient-to-br from-indigo-500/15 to-purple-500/15 dark:from-indigo-500/25 dark:to-purple-500/25 shadow-lg shadow-indigo-500/20 scale-[1.02]'
                : 'border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card hover:border-indigo-400 dark:hover:border-indigo-600 hover:shadow-md hover:-translate-y-0.5',
              loading && 'opacity-60 cursor-wait',
            ]"
            @click="onClickQcu(option.id)"
          >
            <div class="flex items-start gap-2.5">
              <span
                v-if="option.emoji"
                class="text-2xl flex-shrink-0 transition-transform group-hover:scale-110"
              >
                {{ option.emoji }}
              </span>
              <div class="flex-1 min-w-0">
                <div
                  :class="[
                    'text-sm font-semibold leading-snug',
                    selectedQcu === option.id
                      ? 'text-indigo-700 dark:text-indigo-200'
                      : 'text-surface-text dark:text-surface-dark-text',
                  ]"
                >
                  {{ option.label }}
                </div>
                <div
                  v-if="option.description"
                  class="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2"
                >
                  {{ option.description }}
                </div>
              </div>
              <!-- Indicateur selection -->
              <div
                v-if="selectedQcu === option.id"
                class="flex-shrink-0 w-5 h-5 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-md"
              >
                <svg class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
          </button>
        </div>

        <!-- Justification optionnelle pour QCU -->
        <div
          v-if="requiresJustification"
          class="rounded-2xl border-2 border-indigo-200 dark:border-indigo-700/60 bg-white/80 dark:bg-dark-input/80 p-3"
        >
          <label class="block text-xs font-medium text-indigo-700 dark:text-indigo-300 mb-1">
            {{ question.justification_prompt || 'Raconte-nous pourquoi !' }}
          </label>
          <textarea
            v-model="justification"
            :disabled="loading"
            rows="2"
            maxlength="400"
            placeholder="Ta reponse en quelques mots..."
            class="w-full resize-none bg-transparent text-sm text-surface-text dark:text-surface-dark-text placeholder-gray-400 focus:outline-none"
          />
          <div class="flex items-center justify-between mt-1">
            <span class="text-[10px] text-gray-500 dark:text-gray-400">
              Limite 400 caracteres
            </span>
            <span
              :class="[
                'text-[10px] tabular-nums font-medium',
                justification.length > 350 ? 'text-orange-500' : 'text-gray-400 dark:text-gray-500',
              ]"
            >
              {{ justification.length }} / 400
            </span>
          </div>
          <button
            type="button"
            :disabled="!canSubmit"
            class="mt-2 w-full px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed hover:shadow-lg hover:shadow-indigo-500/30 transition-all"
            @click="doSubmit"
          >
            Valider ma reponse
          </button>
        </div>
      </div>

      <!-- MODE QCM : grille multi-sélection -->
      <div v-else-if="isQcm" class="space-y-3">
        <div class="grid gap-2 sm:grid-cols-2">
          <button
            v-for="option in question.options"
            :key="option.id"
            type="button"
            role="checkbox"
            :aria-checked="isQcmChecked(option.id)"
            :disabled="loading || (!isQcmChecked(option.id) && !canCheckMoreQcm())"
            :class="[
              'group relative px-4 py-3 rounded-2xl border-2 text-left transition-all duration-200',
              'focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:focus:ring-offset-dark-card',
              isQcmChecked(option.id)
                ? 'border-indigo-500 bg-gradient-to-br from-indigo-500/15 to-purple-500/15 dark:from-indigo-500/25 dark:to-purple-500/25 shadow-md'
                : 'border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card hover:border-indigo-400 dark:hover:border-indigo-600 hover:shadow-sm',
              (!isQcmChecked(option.id) && !canCheckMoreQcm()) && 'opacity-40 cursor-not-allowed',
              loading && 'cursor-wait',
            ]"
            @click="toggleQcm(option.id)"
          >
            <div class="flex items-start gap-2.5">
              <div
                :class="[
                  'flex-shrink-0 w-5 h-5 rounded-md border-2 flex items-center justify-center mt-0.5 transition-all',
                  isQcmChecked(option.id)
                    ? 'border-indigo-500 bg-gradient-to-br from-indigo-500 to-purple-600 shadow-sm'
                    : 'border-gray-300 dark:border-dark-border bg-white dark:bg-dark-card',
                ]"
              >
                <svg
                  v-if="isQcmChecked(option.id)"
                  class="w-3 h-3 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  stroke-width="4"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <span
                v-if="option.emoji"
                class="text-xl flex-shrink-0 transition-transform group-hover:scale-110"
              >
                {{ option.emoji }}
              </span>
              <div class="flex-1 min-w-0">
                <div
                  :class="[
                    'text-sm font-semibold leading-snug',
                    isQcmChecked(option.id)
                      ? 'text-indigo-700 dark:text-indigo-200'
                      : 'text-surface-text dark:text-surface-dark-text',
                  ]"
                >
                  {{ option.label }}
                </div>
                <div
                  v-if="option.description"
                  class="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2"
                >
                  {{ option.description }}
                </div>
              </div>
            </div>
          </button>
        </div>

        <!-- Justification optionnelle pour QCM -->
        <div
          v-if="requiresJustification"
          class="rounded-2xl border-2 border-indigo-200 dark:border-indigo-700/60 bg-white/80 dark:bg-dark-input/80 p-3"
        >
          <label class="block text-xs font-medium text-indigo-700 dark:text-indigo-300 mb-1">
            {{ question.justification_prompt || 'Raconte-nous pourquoi !' }}
          </label>
          <textarea
            v-model="justification"
            :disabled="loading"
            rows="2"
            maxlength="400"
            placeholder="Ta reponse en quelques mots..."
            class="w-full resize-none bg-transparent text-sm text-surface-text dark:text-surface-dark-text placeholder-gray-400 focus:outline-none"
          />
          <div class="flex items-center justify-between mt-1">
            <span class="text-[10px] text-gray-500 dark:text-gray-400">Limite 400 caracteres</span>
            <span
              :class="[
                'text-[10px] tabular-nums font-medium',
                justification.length > 350 ? 'text-orange-500' : 'text-gray-400 dark:text-gray-500',
              ]"
            >
              {{ justification.length }} / 400
            </span>
          </div>
        </div>

        <!-- Compteur + bouton Valider -->
        <div class="flex items-center justify-between gap-3">
          <div class="flex items-center gap-1.5 text-xs font-medium text-gray-600 dark:text-gray-300">
            <span
              class="inline-flex items-center justify-center min-w-[1.5rem] h-6 px-2 rounded-full bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 tabular-nums font-bold"
            >
              {{ selectedCount }}
            </span>
            <span>
              sur {{ question.max_selections }} max
              <span v-if="question.min_selections > 1">(min {{ question.min_selections }})</span>
            </span>
          </div>
          <button
            type="button"
            :disabled="!canSubmit"
            class="px-5 py-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed hover:shadow-lg hover:shadow-indigo-500/30 transition-all"
            @click="doSubmit"
          >
            Valider ma selection
          </button>
        </div>
      </div>

      <!-- Footer : "Repondre autrement" (uniquement en mode options) -->
      <div
        v-if="!showFallback"
        class="mt-3 pt-2 border-t border-gray-100 dark:border-dark-border/50 flex items-center justify-end"
      >
        <button
          type="button"
          :disabled="loading"
          class="group inline-flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 font-medium transition-colors disabled:opacity-50"
          @click="revealFallback"
        >
          <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
          </svg>
          <span>Repondre autrement</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Slide-up du bottom sheet lors de l'apparition */
.iq-sheet {
  animation: iq-slide-up 350ms cubic-bezier(0.22, 1, 0.36, 1);
  transform-origin: bottom center;
}

@keyframes iq-slide-up {
  from {
    opacity: 0;
    transform: translateY(100%);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Shimmer animé sur l'accent gradient */
.iq-sheet__accent {
  animation: iq-shimmer 4s ease-in-out infinite;
}

@keyframes iq-shimmer {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

/* Apparition en cascade des options (stagger) */
[role="radio"],
[role="checkbox"] {
  animation: iq-fade-in-up 400ms cubic-bezier(0.22, 1, 0.36, 1) backwards;
}

[role="radio"]:nth-child(1),
[role="checkbox"]:nth-child(1) { animation-delay: 100ms; }
[role="radio"]:nth-child(2),
[role="checkbox"]:nth-child(2) { animation-delay: 160ms; }
[role="radio"]:nth-child(3),
[role="checkbox"]:nth-child(3) { animation-delay: 220ms; }
[role="radio"]:nth-child(4),
[role="checkbox"]:nth-child(4) { animation-delay: 280ms; }
[role="radio"]:nth-child(5),
[role="checkbox"]:nth-child(5) { animation-delay: 340ms; }
[role="radio"]:nth-child(6),
[role="checkbox"]:nth-child(6) { animation-delay: 400ms; }
[role="radio"]:nth-child(7),
[role="checkbox"]:nth-child(7) { animation-delay: 460ms; }
[role="radio"]:nth-child(8),
[role="checkbox"]:nth-child(8) { animation-delay: 520ms; }

@keyframes iq-fade-in-up {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Pulse léger sur le badge de question */
@keyframes iq-pulse {
  0%, 100% {
    box-shadow: 0 4px 12px -2px rgba(99, 102, 241, 0.3);
  }
  50% {
    box-shadow: 0 4px 16px -2px rgba(168, 85, 247, 0.5);
  }
}

/* Reduced motion : respect des preferences utilisateur */
@media (prefers-reduced-motion: reduce) {
  .iq-sheet,
  .iq-sheet__accent,
  [role="radio"],
  [role="checkbox"] {
    animation: none;
  }
}
</style>
