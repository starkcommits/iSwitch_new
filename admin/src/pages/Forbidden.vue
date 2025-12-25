<template>
  <div class="h-full flex items-center justify-center p-4">
    <div class="max-w-md w-full text-center">
      <div class="mb-8">
        <h1 class="text-9xl font-bold text-gray-900 opacity-10">403</h1>
        <h2 class="text-3xl font-bold text-gray-900 -mt-12 relative z-10">Access Denied</h2>
        <p class="text-gray-600 mt-4 relative z-10">
          You don't have permission to access this resource.
        </p>
      </div>
      
      <div class="flex flex-col sm:flex-row gap-3 justify-center relative z-10">
        <Button @click="goHome" variant="solid" size="lg">
          <template #prefix>
            <Home class="w-4 h-4" />
          </template>
          Go to Dashboard
        </Button>
        <Button @click="goBack" variant="subtle" size="lg">
          <template #prefix>
            <ArrowLeft class="w-4 h-4" />
          </template>
          Go Back
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Button } from 'frappe-ui'
import { Home, ArrowLeft } from 'lucide-vue-next'
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.back()
}
</script>
