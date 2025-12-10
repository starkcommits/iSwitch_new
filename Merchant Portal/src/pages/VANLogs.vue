<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold tracking-tight text-foreground">VAN Logs</h1>
        <p class="text-muted-foreground mt-1">Monitor Virtual Account Number (VAN) activity and logs.</p>
      </div>
      <div class="flex items-center gap-2">
        <button class="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2" @click="exportVANLogs">
          <svg class="mr-2 h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          Export
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="rounded-xl border bg-card text-card-foreground shadow-sm p-6 mb-6">
      <h3 class="text-lg font-semibold mb-4">Filters</h3>
      <div class="flex flex-wrap items-end gap-4">
        <div class="flex-1 min-w-[200px]">
          <label class="block text-sm font-medium text-muted-foreground mb-2">STATUS</label>
          <select v-model="filters.status" class="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2">
            <option value="">All Status</option>
            <option value="Success">Success</option>
            <option value="Pending">Pending</option>
            <option value="Failed">Failed</option>
          </select>
        </div>

        <div class="flex-1 min-w-[200px]">
          <label class="block text-sm font-medium text-muted-foreground mb-2">FROM DATE & TIME</label>
          <input 
            type="datetime-local" 
            v-model="filters.fromDate" 
            class="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          />
        </div>

        <div class="flex-1 min-w-[200px]">
          <label class="block text-sm font-medium text-muted-foreground mb-2">TO DATE & TIME</label>
          <input 
            type="datetime-local" 
            v-model="filters.toDate" 
            class="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          />
        </div>

        <button 
          class="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-6"
          @click="applyFilters"
        >
          Apply Filters
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="rounded-xl border bg-card text-card-foreground shadow-sm overflow-hidden">
      <DataTable
        :columns="vanColumns"
        :data="vanLogs"
        :per-page="10"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import DataTable from '@/components/DataTable.vue'
import { call } from 'frappe-ui'

// Filters
const filters = ref({
  status: '',
  fromDate: '',
  toDate: ''
})

const vanColumns = [
  { key: 'id', label: 'Transaction ID', sortable: true },
  { key: 'account_number', label: 'Account Number', sortable: true },
  { key: 'amount', label: 'Amount', type: 'currency', sortable: true },
  { key: 'type', label: 'Type', sortable: true },
  { key: 'utr', label: 'UTR', sortable: true },
  { key: 'status', label: 'Status', type: 'badge', sortable: true },
  { key: 'date', label: 'Date', type: 'datetime', sortable: true }
]

const vanLogs = ref([])
const loading = ref(false)

// Fetch VAN logs from API
const fetchVANLogs = async () => {
  loading.value = true
  try {
    const filterData = {
      status: filters.value.status || null,
      from_date: filters.value.fromDate || null,
      to_date: filters.value.toDate || null
    }

    const response = await call('iswitch.merchant_portal_api.get_van_logs', {
      filter_data: JSON.stringify(filterData),
      page: 1,
      page_size: 50
    })
    
    // Frappe wraps response in 'message' object
    const data = response?.message || response
    
    if (data && data.logs) {
      vanLogs.value = data.logs.map(log => ({
        id: log.id,
        account_number: log.account_number,
        amount: parseFloat(log.amount || 0),
        type: log.type,
        utr: log.utr || '-',
        status: log.status.toLowerCase(),
        opening_balance: parseFloat(log.opening_balance || 0),
        closing_balance: parseFloat(log.closing_balance || 0),
        remitter_name: log.remitter_name,
        remitter_account_number: log.remitter_account_number,
        remitter_ifsc_code: log.remitter_ifsc_code,
        date: log.date
      }))
    }
  } catch (error) {
    console.error('Error fetching VAN logs:', error)
    vanLogs.value = []
  } finally {
    loading.value = false
  }
}

const applyFilters = () => {
  fetchVANLogs()
}

const exportVANLogs = async () => {
  try {
    const filterData = {
      status: filters.value.status || null,
      from_date: filters.value.fromDate || null,
      to_date: filters.value.toDate || null
    }
    
    const queryParams = new URLSearchParams({
      filters: JSON.stringify(filterData)
    }).toString()
    
    window.location.href = `/api/method/iswitch.merchant_portal_api.export_van_logs_to_excel?${queryParams}`
  } catch (error) {
    console.error('Error exporting VAN logs:', error)
  }
}

// Fetch VAN logs when component mounts
onMounted(() => {
  fetchVANLogs()
})
</script>

<style scoped>
.space-y-6 > * + * {
  margin-top: 1.5rem;
}
</style>
