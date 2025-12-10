<template>
  <div class="settlements-page">
    <div class="page-header">
      <h1 class="page-title">Settlements</h1>
      <div class="header-actions">
        <button 
          @click="exportSettlements"
          class="inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          Export
        </button>
      </div>
    </div>

    <!-- Stats -->
    <div class="settlement-stats">
      <div class="stat-card glass-card">
        <div class="stat-label">Pending Settlements</div>
        <div class="stat-value">₹1,250.00</div>
        <div class="stat-desc">To be settled by tomorrow</div>
      </div>
      <div class="stat-card glass-card">
        <div class="stat-label">Last Settlement</div>
        <div class="stat-value">₹12,450.00</div>
        <div class="stat-desc">Settled on Dec 05, 2024</div>
      </div>
      <div class="stat-card glass-card">
        <div class="stat-label">Total Settled</div>
        <div class="stat-value">₹1,25,480.00</div>
        <div class="stat-desc">Lifetime processed volume</div>
      </div>
    </div>

    <!-- Data Table -->
    <DataTable
      :columns="settlementColumns"
      :data="settlements"
      :per-page="10"
    >
      <template #cell-status="{ value }">
        <span class="badge" :class="'badge-' + value">{{ value }}</span>
      </template>

      <template #cell-actions="{ row }">
        <button class="action-btn" @click="viewSettlement(row)">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M1 8s3-5 7-5 7 5 7 5-3 5-7 5-7-5-7-5z" />
            <circle cx="8" cy="8" r="2" />
          </svg>
        </button>
      </template>
    </DataTable>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import DataTable from '@/components/DataTable.vue'

// Settlement columns
const settlementColumns = [
  { key: 'id', label: 'Settlement ID', sortable: true },
  { key: 'amount', label: 'Amount', type: 'currency', sortable: true },
  { key: 'fee', label: 'Fee', type: 'currency', sortable: true },
  { key: 'tax', label: 'Tax', type: 'currency', sortable: true },
  { key: 'net', label: 'Net Amount', type: 'currency', sortable: true },
  { key: 'status', label: 'Status', type: 'badge', sortable: true },
  { key: 'date', label: 'Date', type: 'date', sortable: true },
  { key: 'actions', label: 'Actions' }
]

// Sample settlement data
const settlements = ref([
  {
    id: 'SET-001234',
    amount: 12500.00,
    fee: 50.00,
    tax: 9.00,
    net: 12441.00,
    status: 'success',
    date: '2024-12-05T10:00:00'
  },
  {
    id: 'SET-001233',
    amount: 8560.00,
    fee: 34.24,
    tax: 6.16,
    net: 8519.60,
    status: 'success',
    date: '2024-12-04T10:00:00'
  },
  {
    id: 'SET-001232',
    amount: 15200.00,
    fee: 60.80,
    tax: 10.94,
    net: 15128.26,
    status: 'success',
    date: '2024-12-03T10:00:00'
  },
  {
    id: 'SET-001231',
    amount: 4500.00,
    fee: 18.00,
    tax: 3.24,
    net: 4478.76,
    status: 'processing',
    date: '2024-12-06T10:00:00'
  }
])

const exportSettlements = () => {
  console.log('Export settlements')
}

const viewSettlement = (settlement) => {
  console.log('View settlement:', settlement)
}
</script>

<style scoped>
.settlements-page {
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

.settlement-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  padding: 1.5rem;
  border-radius: var(--radius-lg);
}

.stat-label {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 0.25rem;
}

.stat-desc {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
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
}
</style>
