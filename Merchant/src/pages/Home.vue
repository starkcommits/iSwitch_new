<template>
  <div class="max-w-[1400px] mx-auto">
    <div class="dashboard-header">
      <div>
        <h1 class="page-title">Dashboard</h1>
        <p class="page-subtitle">Welcome back, {{ userName }}! Here's what's happening today.</p>
      </div>
      <!-- <div class="header-actions">
        <select class="period-selector">
          <option>Last 7 days</option>
          <option>Last 30 days</option>
          <option>Last 90 days</option>
          <option>This year</option>
        </select>
      </div> -->
    </div>

    <!-- Metrics Grid -->
    <div class="metrics-grid-four">
      <StatCard
        label="Total Orders"
        :value="metrics.transactions.toLocaleString()"
        :trend="0"
        :description="formatCurrency(metrics.totalOrdersAmount)"
        variant="info"
      >
        <template #icon>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <path d="M16 10a4 4 0 0 1-8 0"></path>
          </svg>
        </template>
      </StatCard>

      <StatCard
        label="Processed Orders"
        :value="metrics.processedOrders.toLocaleString()"
        :trend="0"
        :description="formatCurrency(metrics.totalRevenue)"
        variant="success"
      >
        <template #icon>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
        </template>
      </StatCard>

      <StatCard
        label="Pending Orders"
        :value="metrics.pendingOrders.toLocaleString()"
        :trend="0"
        :description="formatCurrency(metrics.totalPendingAmount)"
        variant="warning"
      >
        <template #icon>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
        </template>
      </StatCard>

      <StatCard
        label="Failed Orders"
        :value="metrics.cancelledOrders.toLocaleString()"
        :trend="0"
        :description="formatCurrency(metrics.totalCancelledAmount)"
        variant="destructive"
      >
        <template #icon>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="15" y1="9" x2="9" y2="15"></line>
            <line x1="9" y1="9" x2="15" y2="15"></line>
          </svg>
        </template>
      </StatCard>
    </div>

    <!-- Recent Transactions -->
    <div class="transactions-section">
      <div class="transactions-header">
        <h2 class="section-title">Recent Orders</h2>
      </div>

      <!-- Filters -->
      <div class="rounded-xl border bg-card text-card-foreground shadow-sm p-6 mb-6">
        <h3 class="text-lg font-semibold mb-4">Filters</h3>
        <div class="flex flex-wrap items-end gap-4">
          <div class="flex-1 min-w-[200px]">
            <label class="block text-sm font-medium text-muted-foreground mb-2">STATUS</label>
            <select v-model="filters.status" class="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2">
              <option value="">All Status</option>
              <option value="Queued">Queued</option>
              <option value="Processing">Processing</option>
              <option value="Processed">Processed</option>
              <option value="Cancelled">Cancelled</option>
              <option value="Reversed">Reversed</option>
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

      <!-- Data Table -->
      <DataTable
        :columns="transactionColumns"
        :data="filteredTransactions"
        :per-page="5"
      >
        <template #cell-customer="{ value }">
          <span class="font-medium">{{ value }}</span>
        </template>

      </DataTable>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { session } from '../data/session'
import StatCard from '@/components/StatCard.vue'
import DataTable from '@/components/DataTable.vue'
import { call } from 'frappe-ui'

const userName = computed(() => session.user || 'User')

// Filters
const filters = ref({
  status: '',
  fromDate: '',
  toDate: ''
})

// Wallet and metrics data
// Wallet and metrics data
const walletData = ref({
  balance: 0,
  status: 'Inactive'
})

const metrics = ref({
  totalRevenue: 0,
  transactions: 0,
  processedOrders: 0,
  pendingOrders: 0,
  cancelledOrders: 0,
  totalPendingAmount: 0,
  totalCancelledAmount: 0,
  totalOrdersAmount: 0
})

const statusData = ref({
  success: 0,
  pending: 0,
  failed: 0
})

// Fetch dashboard stats
const fetchDashboardStats = async () => {
  try {
    const response = await call('iswitch.merchant_portal_api.get_dashboard_stats')
    
    // Frappe wraps response in 'message' object
    const data = response?.message || response
    
    if (data) {
      // Update wallet data
      if (data.wallet) {
        walletData.value.balance = data.wallet.balance || 0
        walletData.value.status = data.wallet.status || 'Inactive'
      }
      
      // Update metrics with proper field mapping
      if (data.stats) {
        metrics.value = {
          totalRevenue: data.stats.total_processed_amount || 0,
          transactions: data.stats.total_orders || 0,
          processedOrders: data.stats.processed_orders || 0,
          pendingOrders: data.stats.pending_orders || 0,
          cancelledOrders: data.stats.cancelled_orders || 0,
          totalPendingAmount: data.stats.total_pending_amount || 0,
          totalCancelledAmount: data.stats.total_cancelled_amount || 0,
          totalOrdersAmount: data.stats.total_orders_amount || 0
        }

        // Update status data for charts
        statusData.value = {
          success: metrics.value.processedOrders,
          pending: metrics.value.pendingOrders,
          failed: metrics.value.cancelledOrders
        }
        
        // Retrigger chart render
        renderCharts()
      }
    }
  } catch (error) {
    console.error('Error fetching dashboard stats:', error)
    // Clear metrics on error
    metrics.value = {
      totalRevenue: 0,
      transactions: 0,
      processedOrders: 0,
      pendingOrders: 0,
      cancelledOrders: 0,
      totalPendingAmount: 0,
      totalCancelledAmount: 0
    }
  }
}

// Fetch recent transactions
const fetchRecentTransactions = async () => {
  try {
    const filterData = {
      status: filters.value.status || null,
      from_date: filters.value.fromDate || null,
      to_date: filters.value.toDate || null
    }
    
    const response = await call('iswitch.merchant_portal_api.get_orders', {
      filter_data: JSON.stringify(filterData),
      page: 1,
      page_size: 5,
      sort_by: 'creation',
      sort_order: 'desc'
    })
    
    // Frappe wraps response in 'message' object
    const data = response?.message || response
    
    if (data && data.orders) {
      recentTransactions.value = data.orders.map(order => ({
        id: order.id,
        customer: order.customer || 'N/A',
        amount: parseFloat(order.amount || 0),
        fee: parseFloat(order.fee || 0),
        status: order.status,
        utr: order.utr || '-',
        date: order.date
      }))
    }
  } catch (error) {
    console.error('Error fetching recent transactions:', error)
    recentTransactions.value = []
  }
}

// Chart canvases
const lineChartCanvas = ref(null)
const donutChartCanvas = ref(null)

// Transaction columns
const transactionColumns = [
  { key: 'id', label: 'ORDER ID', sortable: true },
  { key: 'customer', label: 'CUSTOMER', sortable: true },
  { key: 'amount', label: 'AMOUNT', type: 'currency', sortable: true },
  { key: 'fee', label: 'FEE', type: 'currency', sortable: true },
  { key: 'status', label: 'STATUS', type: 'badge', sortable: true },
  { key: 'utr', label: 'UTR', sortable: true },
  { key: 'date', label: 'DATE', type: 'datetime', sortable: true }
]

// Sample transaction data (initial empty state, populated by API)
const recentTransactions = ref([])

// Filtered transactions (now handled by backend, so just return recentTransactions)
const filteredTransactions = computed(() => {
  return recentTransactions.value
})

const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value)
}

const viewTransaction = (transaction) => {
  console.log('View transaction:', transaction)
}

const applyFilters = () => {
  console.log('Filters applied:', filters.value)
  fetchRecentTransactions()
}

const exportTransactions = async () => {
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
    console.error('Error exporting transactions:', error)
  }
}


// Simple chart rendering (placeholder - you can integrate Chart.js or similar)
const renderCharts = () => {
  // Line chart
  if (lineChartCanvas.value) {
    const ctx = lineChartCanvas.value.getContext('2d')
    const width = lineChartCanvas.value.width
    const height = lineChartCanvas.value.height
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height)
    
    // Draw gradient background
    const gradient = ctx.createLinearGradient(0, 0, 0, height)
    gradient.addColorStop(0, 'rgba(139, 92, 246, 0.1)')
    gradient.addColorStop(1, 'rgba(139, 92, 246, 0)')
    
    // Sample data points
    const points = [
      { x: 50, y: 200 },
      { x: 150, y: 150 },
      { x: 250, y: 180 },
      { x: 350, y: 120 },
      { x: 450, y: 140 },
      { x: 550, y: 80 },
      { x: 650, y: 100 }
    ]
    
    // Draw line
    ctx.beginPath()
    ctx.moveTo(points[0].x, points[0].y)
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(points[i].x, points[i].y)
    }
    ctx.strokeStyle = '#8b5cf6'
    ctx.lineWidth = 3
    ctx.stroke()
    
    // Fill area under line
    ctx.lineTo(points[points.length - 1].x, height)
    ctx.lineTo(points[0].x, height)
    ctx.closePath()
    ctx.fillStyle = gradient
    ctx.fill()
  }
  
  // Donut chart
  if (donutChartCanvas.value) {
    const ctx = donutChartCanvas.value.getContext('2d')
    const width = donutChartCanvas.value.width
    const height = donutChartCanvas.value.height
    const centerX = width / 2
    const centerY = height / 2
    const radius = Math.min(width, height) / 3
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height)
    
    // Data
    const data = [
      { value: statusData.value.success, color: '#10b981' },
      { value: statusData.value.pending, color: '#f59e0b' },
      { value: statusData.value.failed, color: '#ef4444' }
    ]
    
    const total = data.reduce((sum, item) => sum + item.value, 0)
    let currentAngle = -Math.PI / 2
    
    // Draw segments
    data.forEach(item => {
      const sliceAngle = (item.value / total) * 2 * Math.PI
      
      ctx.beginPath()
      ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle)
      ctx.arc(centerX, centerY, radius * 0.6, currentAngle + sliceAngle, currentAngle, true)
      ctx.closePath()
      ctx.fillStyle = item.color
      ctx.fill()
      
      currentAngle += sliceAngle
    })
  }
}

onMounted(() => {
  fetchDashboardStats()
  fetchRecentTransactions()
  renderCharts()
})
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2rem;
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 0.25rem;
}

.page-subtitle {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.period-selector {
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 0.625rem 1rem;
  color: var(--color-text-primary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.period-selector:focus {
  outline: none;
  border-color: var(--color-primary);
}


.metrics-grid-four {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.transactions-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.transactions-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.filters-section {
  padding: 1.5rem;
  display: flex;
  align-items: flex-end;
  gap: 1.5rem;
  flex-wrap: wrap;
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

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.chart-card {
  padding: 1.5rem;
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.chart-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.chart-legend {
  display: flex;
  gap: 1.5rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.chart-body {
  position: relative;
}

.chart-body canvas {
  width: 100% !important;
  height: auto !important;
}

.status-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-border);
}

.status-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.status-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-info {
  flex: 1;
}

.status-label {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  margin-bottom: 0.25rem;
}

.status-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text-primary);
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

@media (max-width: 1200px) {
  .metrics-grid-four {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .metrics-grid-four {
    grid-template-columns: 1fr;
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .status-stats {
    grid-template-columns: 1fr;
  }
  
  .filters-section {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .filter-group {
    width: 100%;
  }

  .transactions-header {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }
}
</style>

