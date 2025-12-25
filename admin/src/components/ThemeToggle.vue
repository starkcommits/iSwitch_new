<template>
  <button
    @click="toggleTheme"
    class="inline-flex h-9 w-9 items-center justify-center rounded-md border border-input bg-transparent shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50"
    aria-label="Toggle theme"
  >
    <Sun v-if="!isDark" class="h-4 w-4 transition-all" />
    <Moon v-else class="h-4 w-4 transition-all" />
  </button>
</template>

<script setup>
import { Sun, Moon } from 'lucide-vue-next'
import { useTheme } from '../composables/useTheme'

const { isDark, toggleTheme } = useTheme()
</script>
