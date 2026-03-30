<script setup lang="ts">
definePageMeta({
  layout: false,
})

const { register, login } = useAuth()

const form = reactive({
  email: '',
  password: '',
  full_name: '',
  company_name: '',
})
const error = ref('')
const loading = ref(false)

async function handleRegister() {
  error.value = ''
  loading.value = true
  try {
    await register({ ...form })
    await login(form.email, form.password)
    await navigateTo('/')
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Erreur lors de l'inscription"
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-surface-bg px-4">
    <div class="w-full max-w-md">
      <div class="bg-white rounded-2xl shadow-lg p-8">
        <div class="text-center mb-8">
          <h1 class="text-2xl font-bold text-surface-text">ESG Mefali</h1>
          <p class="text-gray-500 mt-2">Créer un compte</p>
        </div>

        <form @submit.prevent="handleRegister" class="space-y-4">
          <div v-if="error" class="bg-red-50 text-brand-red text-sm rounded-lg p-3">
            {{ error }}
          </div>

          <div>
            <label for="full_name" class="block text-sm font-medium text-gray-700 mb-1">
              Nom complet
            </label>
            <input
              id="full_name"
              v-model="form.full_name"
              type="text"
              required
              autocomplete="name"
              class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-green focus:border-transparent outline-none"
              placeholder="Amadou Diallo"
            />
          </div>

          <div>
            <label for="company_name" class="block text-sm font-medium text-gray-700 mb-1">
              Nom de l'entreprise
            </label>
            <input
              id="company_name"
              v-model="form.company_name"
              type="text"
              required
              class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-green focus:border-transparent outline-none"
              placeholder="EcoSolaire SARL"
            />
          </div>

          <div>
            <label for="email" class="block text-sm font-medium text-gray-700 mb-1">
              Adresse email
            </label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              required
              autocomplete="email"
              class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-green focus:border-transparent outline-none"
              placeholder="votre@email.com"
            />
          </div>

          <div>
            <label for="password" class="block text-sm font-medium text-gray-700 mb-1">
              Mot de passe
            </label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              required
              minlength="8"
              autocomplete="new-password"
              class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-green focus:border-transparent outline-none"
              placeholder="Minimum 8 caractères"
            />
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="w-full py-2.5 bg-brand-green text-white font-medium rounded-lg hover:bg-emerald-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ loading ? 'Inscription...' : "S'inscrire" }}
          </button>
        </form>

        <p class="text-center text-sm text-gray-500 mt-6">
          Déjà un compte ?
          <NuxtLink to="/login" class="text-brand-green font-medium hover:underline">
            Se connecter
          </NuxtLink>
        </p>
      </div>
    </div>
  </div>
</template>
