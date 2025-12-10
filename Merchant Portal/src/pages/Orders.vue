<template>
  <div class="orders-page">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-bold tracking-tight text-foreground">Orders</h1>
        <p class="text-muted-foreground mt-1">View and track all your transaction orders.</p>
      </div>
      <button 
        class="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2" 
        @click="exportOrders"
      >
        <svg class="mr-2 h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="7 10 12 15 17 10" />
          <line x1="12" y1="15" x2="12" y2="3" />
        </svg>
        Export
      </button>
    </div>

    <!-- Filters -->
    <div class="rounded-xl border bg-card text-card-foreground shadow-sm p-4 md:p-6 mb-6">
      <h3 class="text-lg font-semibold mb-4">Filters</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
        <div>
          <label class="block text-sm font-medium text-muted-foreground mb-2">STATUS</label>
          <select v-model="filters.status" class="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2">
            <option value="All Status">All Status</option>
            <option value="Queued">Queued</option>
            <option value="Processing">Processing</option>
            <option value="Processed">Processed</option>
            <option value="Cancelled">Cancelled</option>
            <option value="Reversed">Reversed</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-muted-foreground mb-2">FROM DATE & TIME</label>
          <input 
            type="datetime-local" 
            v-model="filters.fromDate" 
            class="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-muted-foreground mb-2">TO DATE & TIME</label>
          <input 
            type="datetime-local" 
            v-model="filters.toDate" 
            class="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          />
        </div>

        <button 
          class="w-full inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-6"
          @click="applyFilters"
        >
          Apply Filters
        </button>
      </div>
    </div>

    <!-- Data Table -->
    <DataTable
      :columns="orderColumns"
      :data="orders"
      :per-page="10"
    >
      <template #cell-customer="{ value }">
        <div class="customer-cell">
          <div class="customer-avatar">{{ value.charAt(0) }}</div>
          <span>{{ value }}</span>
        </div>
      </template>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import DataTable from '@/components/DataTable.vue'
import { call } from 'frappe-ui'

// Filters
const filters = ref({
  status: 'All Status',
  fromDate: '',
  toDate: ''
})

// Order columns
const orderColumns = [
  { key: 'id', label: 'ORDER ID', sortable: true },
  { key: 'customer', label: 'CUSTOMER', sortable: true },
  { key: 'amount', label: 'AMOUNT', type: 'currency', sortable: true },
  { key: 'fee', label: 'FEE', type: 'currency', sortable: true },
  { key: 'status', label: 'STATUS', type: 'badge', sortable: true },
  { key: 'utr', label: 'UTR', sortable: true },
  { key: 'date', label: 'DATE', type: 'datetime', sortable: true }
]

// Order data and pagination
const orders = ref([])
const totalOrders = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const loading = ref(false)

// Fetch orders from API
const fetchOrders = async () => {
  loading.value = true
  try {
    const filterData = {
      status: filters.value.status !== 'All Status' ? filters.value.status : null,
      from_date: filters.value.fromDate || null,
      to_date: filters.value.toDate || null
    }
    
    const response = await call('iswitch.merchant_portal_api.get_orders', {
      filter_data: JSON.stringify(filterData),
      page: currentPage.value,
      page_size: pageSize.value,
      sort_by: 'creation',
      sort_order: 'desc'
    })
    
    // Frappe wraps response in 'message' object
    const data = response?.message || response
    
    if (data && data.orders) {
      orders.value = data.orders.map(order => ({
        id: order.id,
        customer: order.customer || 'N/A',
        amount: parseFloat(order.amount || 0),
        fee: parseFloat(order.fee || 0),
        status: order.status,
        utr: order.utr || '-',
        date: order.date
      }))
      totalOrders.value = data.total || 0
    }
  } catch (error) {
    console.error('Error fetching orders:', error)
    orders.value = []
    totalOrders.value = 0
  } finally {
    loading.value = false
  }
}

// Filtered orders (API already handles filtering, this is for client-side refinement only)
const filteredOrders = computed(() => {
  let filtered = [...orders.value]
  
  // Only apply client-side filters if they are explicitly set
  // API handles the main filtering, this is just for additional refinement
  if (filters.value.status && filters.value.status !== 'All Status' && filters.value.status !== '') {
    filtered = filtered.filter(t => t.status.toLowerCase() === filters.value.status.toLowerCase())
  }
  
  if (filters.value.fromDate) {
    const fromDate = new Date(filters.value.fromDate)
    filtered = filtered.filter(t => new Date(t.date) >= fromDate)
  }
  
  if (filters.value.toDate) {
    const toDate = new Date(filters.value.toDate)
    filtered = filtered.filter(t => new Date(t.date) <= toDate)
  }
  
  return filtered
})

const applyFilters = () => {
  currentPage.value = 1 // Reset to first page when filtering
  fetchOrders()
}

const exportOrders = () => {
  try {
    const filterData = {
      status: filters.value.status !== 'All Status' ? filters.value.status : null,
      from_date: filters.value.fromDate || null,
      to_date: filters.value.toDate || null
    }
    
    const queryParams = new URLSearchParams({
      filters: JSON.stringify(filterData)
    }).toString()
    
    window.location.href = `/api/method/iswitch.merchant_portal_api.export_orders_to_excel?${queryParams}`
  } catch (error) {
    console.error('Error exporting orders:', error)
  }
}

const viewOrder = (order) => {
  console.log('View order:', order)
}

// Fetch orders when component mounts
onMounted(() => {
  fetchOrders()
})
</script>

<style scoped>
.orders-page {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text-primary);
}

.filters-section {
  padding: 1.5rem;
  display: flex;
  align-items: flex-end;
  gap: 1.5rem;
  flex-wrap: wrap;
  margin-bottom: 1.5rem;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
  min-width: 200px;
}

.filter-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.filter-select,
.filter-input {
  width: 100%;
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 0.625rem 1rem;
  color: var(--color-text-primary);
  font-size: 0.875rem;
  transition: all 0.2s ease;
}

.filter-select:focus,
.filter-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}

.customer-cell {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.customer-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.75rem;
  color: white;
  flex-shrink: 0;
}

.action-btn {
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 0.5rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn:hover {
  background: var(--color-bg-hover);
  color: var(--color-primary);
  border-color: var(--color-primary);
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .filters-section {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .filter-group {
    width: 100%;
  }
}
</style>
