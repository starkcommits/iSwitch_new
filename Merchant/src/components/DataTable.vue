<template>
  <div class="w-full">
    <div class="flex items-center py-4" v-if="title || $slots.actions">
      <h3 class="text-lg font-semibold tracking-tight">{{ title }}</h3>
      <div class="ml-auto flex items-center gap-2">
        <slot name="actions"></slot>
      </div>
    </div>
    
    <div class="rounded-md border bg-card text-card-foreground shadow-sm overflow-hidden max-w-full">
      <div class="relative w-full overflow-x-auto">
        <table class="w-full caption-bottom text-sm">
          <thead class="[&_tr]:border-b">
            <tr class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
              <th 
                v-for="column in columns" 
                :key="column.key"
                class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0 whitespace-nowrap"
                :class="{ 'cursor-pointer select-none hover:text-foreground': column.sortable }"
                @click="column.sortable && handleSort(column.key)"
              >
                <div class="flex items-center gap-1">
                  <span>{{ column.label }}</span>
                  <svg v-if="column.sortable" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="opacity-50">
                    <path d="M7 15l5 5 5-5" v-if="sortKey === column.key && sortOrder === 'desc'" />
                    <path d="M7 9l5-5 5 5" v-else-if="sortKey === column.key && sortOrder === 'asc'" />
                    <path d="M8 9l4-4 4 4M8 15l4 4 4-4" v-else />
                  </svg>
                </div>
              </th>
            </tr>
          </thead>
          <tbody class="[&_tr:last-child]:border-0">
            <tr 
              v-for="(row, index) in paginatedData" 
              :key="index"
              class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted"
            >
              <td 
                v-for="column in columns" 
                :key="column.key"
                class="p-4 align-middle [&:has([role=checkbox])]:pr-0 whitespace-nowrap"
              >
                <slot :name="`cell-${column.key}`" :row="row" :value="row[column.key]">
                  <span v-if="column.type === 'badge'" 
                    class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold border"
                    :class="getBadgeVariant(row[column.key])"
                  >
                    {{ formatBadgeText(row[column.key]) }}
                  </span>
                  <span v-else-if="column.type === 'currency'">
                    {{ formatCurrency(row[column.key]) }}
                  </span>
                  <span v-else-if="column.type === 'date'">
                    {{ formatDate(row[column.key]) }}
                  </span>
                  <span v-else-if="column.type === 'datetime'">
                    {{ formatDateTime(row[column.key]) }}
                  </span>
                  <span v-else>
                    {{ row[column.key] }}
                  </span>
                </slot>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <div class="flex items-center justify-between px-2 py-4" v-if="pagination">
      <div class="text-sm text-muted-foreground">
        Showing {{ startIndex + 1 }} to {{ endIndex }} of {{ data.length }} entries
      </div>
      <div class="flex items-center space-x-2">
        <button 
          class="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-8 w-8 p-0"
          :disabled="currentPage === 1"
          @click="goToPage(currentPage - 1)"
        >
          <span class="sr-only">Go to previous page</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
        
        <div class="flex items-center gap-1">
          <button 
            v-for="page in visiblePages" 
            :key="page"
            class="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 w-8"
            :class="page === currentPage ? 'bg-primary text-primary-foreground hover:bg-primary/90' : 'border border-input bg-background hover:bg-accent hover:text-accent-foreground'"
            @click="goToPage(page)"
          >
            {{ page }}
          </button>
        </div>
        
        <button 
          class="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-8 w-8 p-0"
          :disabled="currentPage === totalPages"
          @click="goToPage(currentPage + 1)"
        >
          <span class="sr-only">Go to next page</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  title: String,
  columns: {
    type: Array,
    required: true
  },
  data: {
    type: Array,
    required: true
  },
  pagination: {
    type: Boolean,
    default: true
  },
  perPage: {
    type: Number,
    default: 10
  }
})

const currentPage = ref(1)
const sortKey = ref('')
const sortOrder = ref('asc')

const totalPages = computed(() => Math.ceil(props.data.length / props.perPage))

const startIndex = computed(() => (currentPage.value - 1) * props.perPage)
const endIndex = computed(() => Math.min(startIndex.value + props.perPage, props.data.length))

const paginatedData = computed(() => {
  let data = [...props.data]
  
  if (sortKey.value) {
    data.sort((a, b) => {
      const aVal = a[sortKey.value]
      const bVal = b[sortKey.value]
      
      if (sortOrder.value === 'asc') {
        return aVal > bVal ? 1 : -1
      } else {
        return aVal < bVal ? 1 : -1
      }
    })
  }
  
  return data.slice(startIndex.value, endIndex.value)
})

const visiblePages = computed(() => {
  const pages = []
  const maxVisible = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
  let end = Math.min(totalPages.value, start + maxVisible - 1)
  
  if (end - start < maxVisible - 1) {
    start = Math.max(1, end - maxVisible + 1)
  }
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  return pages
})

const handleSort = (key) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'asc'
  }
}

const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value)
}

const formatDate = (value) => {
  if (!value) return '-'
  return new Date(value).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const formatDateTime = (value) => {
  if (!value) return '-'
  return new Date(value).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getBadgeVariant = (value) => {
  const status = value?.toLowerCase() || ''
  
  // Transaction types (for Ledger)
  if (status === 'credit') {
    return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300 border-green-200'
  }
  if (status === 'debit') {
    return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300 border-blue-200'
  }
  
  // Order statuses
  // Success states
  if (status === 'processed' || status === 'success') {
    return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300 border-green-200'
  }
  
  // Processing/Pending states
  if (status === 'processing' || status === 'pending' || status === 'queued') {
    return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300 border-yellow-200'
  }
  
  // Failed/Cancelled states
  if (status === 'cancelled' || status === 'reversed' || status === 'failed') {
    return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300 border-red-200'
  }
  
  // Default
  return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300 border-gray-200'
}

const formatBadgeText = (value) => {
  if (!value) return ''
  // Convert to Camel case: first letter uppercase, rest lowercase
  return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase()
}
</script>

<style scoped>
/* Removed custom styles in favor of Tailwind classes */
</style>
