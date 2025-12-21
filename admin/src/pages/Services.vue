<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold tracking-tight text-foreground">Services</h1>
        <p class="text-muted-foreground mt-1">Manage active services and products.</p>
      </div>
    </div>

    <!-- Services Table -->
    <div class="rounded-xl border bg-card text-card-foreground shadow-sm overflow-hidden">
      <DataTable
        :columns="serviceColumns"
        :data="services"
        :per-page="20"
      >
        <template #cell-status="{ row }">
          <div class="flex items-center space-x-2">
            <Switch 
              :checked="row.is_active"
              @update:checked="(val) => toggleService(row, val)" 
            />
            <span class="text-sm font-medium" :class="row.is_active ? 'text-green-600' : 'text-gray-500'">
              {{ row.is_active ? 'Active' : 'Inactive' }}
            </span>
          </div>
        </template>
      </DataTable>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import DataTable from '@/components/DataTable.vue'
import { Switch } from '@/components/ui/switch'
import { call } from 'frappe-ui'

const serviceColumns = [
  { key: 'product_name', label: 'Service Name', sortable: true },
  { key: 'status', label: 'Status', sortable: false }
]

const services = ref([])
const loading = ref(false)

const fetchServices = async () => {
  loading.value = true
  try {
    const response = await call('iswitch.admin_portal_api.get_services')
    const data = response?.message || response
    if (data && data.services) {
      services.value = data.services.map(s => ({
        ...s,
        is_active: !!s.is_active
      }))
    }
  } catch (error) {
    console.error('Error fetching services:', error)
  } finally {
    loading.value = false
  }
}

const toggleService = async (service, newState) => {
  // Optimistic update
  const originalState = service.is_active
  service.is_active = newState
  
  try {
    await call('iswitch.admin_portal_api.toggle_service_status', {
      service_name: service.name,
      is_active: newState
    })
  } catch (error) {
    console.error('Error toggling service:', error)
    // Revert on error
    service.is_active = originalState
  }
}

onMounted(() => {
  fetchServices()
})
</script>
