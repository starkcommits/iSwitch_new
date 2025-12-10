<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold tracking-tight text-foreground">Ledger</h1>
        <p class="text-muted-foreground mt-1">View and manage your financial transactions.</p>
      </div>
      <button class="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2" @click="exportLedger">
        <svg class="mr-2 h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="7 10 12 15 17 10" />
          <line x1="12" y1="15" x2="12" y2="3" />
        </svg>
        Export
      </button>
    </div>

    <!-- Filters -->
    <div class="rounded-xl border bg-card text-card-foreground shadow-sm p-6 mb-6">
      <h3 class="text-lg font-semibold mb-4">Filters</h3>
      <div class="flex flex-wrap items-end gap-4">
        <div class="flex-1 min-w-[200px]">
          <label class="block text-sm font-medium text-muted-foreground mb-2">TRANSACTION TYPE</label>
          <select v-model="filters.type" class="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2">
            <option value="">All Types</option>
            <option value="Credit">Credit</option>
            <option value="Debit">Debit</option>
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
        :columns="ledgerColumns"
        :data="ledgerData"
        :per-page="10"
      >
        <template #cell-status="{ value }">
          <span 
            class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
            :class="{
              'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300': value === 'success',
              'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300': value === 'processing',
              'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300': value === 'failed'
            }"
          >
            {{ value.charAt(0).toUpperCase() + value.slice(1) }}
          </span>
        </template>
      </DataTable>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import DataTable from '@/components/DataTable.vue'
import { call } from 'frappe-ui'

// Filters
const filters = ref({
  type: '',
  fromDate: '',
  toDate: ''
})

const ledgerColumns = [
  { key: 'id', label: 'Ledger ID', sortable: true },
  { key: 'order_id', label: 'Order ID', sortable: true },
  { key: 'type', label: 'Transaction Type', type: 'badge', sortable: true },
  { key: 'transaction_amount', label: 'Transaction Amount', type: 'currency', sortable: true },
  { key: 'opening_balance', label: 'Opening Balance', type: 'currency', sortable: true },
  { key: 'closing_balance', label: 'Closing Balance', type: 'currency', sortable: true },
  { key: 'date', label: 'Date', type: 'datetime', sortable: true }
]

const ledgerData = ref([])
const loading = ref(false)

// Fetch ledger entries from API
const fetchLedger = async () => {
  loading.value = true
  try {
    const filterData = {
      type: filters.value.type || null,
      from_date: filters.value.fromDate || null,
      to_date: filters.value.toDate || null
    }

    const response = await call('iswitch.merchant_portal_api.get_ledger_entries', {
      filter_data: JSON.stringify(filterData),
      page: 1,
      page_size: 50
    })
    
    // Frappe wraps response in 'message' object
    const data = response?.message || response
    
    if (data && data.entries) {
      ledgerData.value = data.entries.map(entry => ({
        id: entry.id,
        order_id: entry.order_id || '-',
        type: entry.type.toLowerCase(),
        transaction_amount: parseFloat(entry.transaction_amount || 0),
        opening_balance: parseFloat(entry.opening_balance || 0),
        closing_balance: parseFloat(entry.closing_balance || 0),
        date: entry.date
      }))
    }
  } catch (error) {
    console.error('Error fetching ledger:', error)
    ledgerData.value = []
  } finally {
    loading.value = false
  }
}

const applyFilters = () => {
  fetchLedger()
}

const exportLedger = async () => {
  try {
    const filterData = {
      type: filters.value.type || null,
      from_date: filters.value.fromDate || null,
      to_date: filters.value.toDate || null
    }
    
    const queryParams = new URLSearchParams({
      filters: JSON.stringify(filterData)
    }).toString()
    
    window.location.href = `/api/method/iswitch.merchant_portal_api.export_ledger_to_excel?${queryParams}`
  } catch (error) {
    console.error('Error exporting ledger:', error)
  }
}

// Fetch ledger when component mounts
onMounted(() => {
  fetchLedger()
})

const viewEntry = (entry) => {
  console.log('Viewing entry:', entry)
}
</script>

<style scoped>
.space-y-6 > * + * {
  margin-top: 1.5rem;
}
</style>
