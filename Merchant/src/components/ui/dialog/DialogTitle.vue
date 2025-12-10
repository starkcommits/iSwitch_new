<script setup>
import { DialogTitle } from 'radix-vue'
import { cn } from '@/lib/utils'

const props = defineProps({
  asChild: { type: Boolean, default: false },
  as: { type: null, default: 'h2' },
  class: { type: String, default: '' },
})
</script>

<template>
  <DialogTitle
    v-bind="props"
    :class="
      cn('text-lg font-semibold leading-none tracking-tight', props.class)
    "
  >
    <slot />
  </DialogTitle>
</template>
