<script setup lang="ts">
import { useUiStore } from '~/stores/ui'

const uiStore = useUiStore()

onMounted(() => {
  uiStore.initTheme()
})
</script>

<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
  <ToastNotification />
</template>
