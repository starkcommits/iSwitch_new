<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold tracking-tight text-foreground">Processors</h1>
        <p class="text-muted-foreground mt-1">Manage payment processors and integrations.</p>
      </div>
    </div>

    <!-- Processors Table -->
    <div class="rounded-xl border bg-card text-card-foreground shadow-sm overflow-hidden">
      <DataTable
        :columns="processorColumns"
        :data="processors"
        :per-page="20"
      >
        <template #cell-is_active="{ value }">
          <span 
            class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold"
            :class="{
              'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300': value,
              'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300': !value
            }"
          >
            {{ value ? 'Active' : 'Inactive' }}
          </span>
        </template>
        <template #cell-products="{ value }">
            <div class="flex flex-wrap gap-1">
                <span v-for="product in value" :key="product" class="inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80">
                    {{ product }}
                </span>
                <span v-if="!value || value.length === 0" class="text-muted-foreground italic">None</span>
            </div>
        </template>
      </DataTable>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import DataTable from '@/components/DataTable.vue'
import { call } from 'frappe-ui'

const processorColumns = [
  { key: 'integration_name', label: 'Name', sortable: true },
  { key: 'integration_type', label: 'Type', sortable: true },
  { key: 'api_endpoint', label: 'API Endpoint', sortable: true },
  { key: 'balance', label: 'Balance', type: 'currency', sortable: true },
  { key: 'is_active', label: 'Status', sortable: true },
  { key: 'products', label: 'Services', sortable: false }
]

const processors = ref([])
const loading = ref(false)

const fetchProcessors = async () => {
  loading.value = true
  try {
    const response = await call('iswitch.admin_portal_api.get_processors')
    const data = response?.message || response
    if (data && data.processors) {
      processors.value = data.processors
    }
  } catch (error) {
    console.error('Error fetching processors:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchProcessors()
})
</script>
