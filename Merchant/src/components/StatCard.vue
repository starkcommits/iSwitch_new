<template>
  <div class="rounded-xl border bg-card text-card-foreground shadow-sm p-4 md:p-6 flex flex-col gap-3 md:gap-4">
    <div class="flex items-center justify-between">
      <div class="w-12 h-12 rounded-lg flex items-center justify-center text-white" :class="iconClass">
        <slot name="icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" />
          </svg>
        </slot>
      </div>
      <div v-if="trend !== 0" class="flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-semibold" :class="trendClass">
        <svg v-if="trend > 0" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
          <polyline points="17 6 23 6 23 12" />
        </svg>
        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" />
          <polyline points="17 18 23 18 23 12" />
        </svg>
        <span>{{ Math.abs(trend) }}%</span>
      </div>
    </div>
    
    <div class="flex flex-col gap-1">
      <div class="text-sm font-medium text-muted-foreground">{{ label }}</div>
      <div class="text-3xl font-bold tracking-tight">{{ formattedValue }}</div>
      <p class="text-xs text-muted-foreground">{{ description }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number],
    required: true
  },
  trend: {
    type: Number,
    default: 0
  },
  description: {
    type: String,
    default: ''
  },
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'success', 'warning', 'info', 'destructive'].includes(value)
  },
  prefix: {
    type: String,
    default: ''
  },
  suffix: {
    type: String,
    default: ''
  }
})

const formattedValue = computed(() => {
  return `${props.prefix}${props.value}${props.suffix}`
})

const iconClass = computed(() => {
  const variants = {
    primary: 'bg-gradient-to-br from-violet-500 to-purple-600',
    success: 'bg-gradient-to-br from-green-500 to-emerald-600',
    warning: 'bg-gradient-to-br from-amber-500 to-orange-600',
    info: 'bg-gradient-to-br from-blue-500 to-indigo-600',
    destructive: 'bg-gradient-to-br from-red-500 to-rose-600'
  }
  return variants[props.variant] || variants.primary
})

const trendClass = computed(() => {
  if (props.trend > 0) return 'bg-green-500/10 text-green-700 dark:text-green-400'
  if (props.trend < 0) return 'bg-red-500/10 text-red-700 dark:text-red-400'
  return 'bg-gray-500/10 text-gray-700 dark:text-gray-400'
})
</script>

<style scoped>
/* Minimal scoped styles, relying on Tailwind */
</style>
