<script setup>
import { DialogDescription } from 'radix-vue'
import { cn } from '@/lib/utils'

const props = defineProps({
  asChild: { type: Boolean, default: false },
  class: { type: String, default: '' },
})
</script>

<template>
  <DialogDescription
    v-bind="props"
    :class="cn('text-sm text-muted-foreground', props.class)"
  >
    <slot />
  </DialogDescription>
</template>
