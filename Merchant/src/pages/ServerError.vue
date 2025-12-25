<template>
  <div class="h-full flex items-center justify-center p-4">
    <div class="max-w-md w-full text-center">
      <div class="mb-8">
        <h1 class="text-9xl font-bold text-gray-900 opacity-10">500</h1>
        <h2 class="text-3xl font-bold text-gray-900 -mt-12 relative z-10">Server Error</h2>
        <p class="text-gray-600 mt-4 relative z-10">
          Something went wrong on our end. Please try again later.
        </p>
      </div>
      
      <div class="flex flex-col sm:flex-row gap-3 justify-center relative z-10">
        <Button @click="reload" variant="solid" size="lg">
          <template #prefix>
            <RefreshCw class="w-4 h-4" />
          </template>
          Reload Page
        </Button>
        <Button @click="goHome" variant="subtle" size="lg">
          <template #prefix>
            <Home class="w-4 h-4" />
          </template>
          Go to Dashboard
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Button } from 'frappe-ui'
import { Home, RefreshCw } from 'lucide-vue-next'
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const reload = () => {
  window.location.reload()
}
</script>
