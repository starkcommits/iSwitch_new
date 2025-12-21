<template>
  <div class="p-6 max-w-7xl mx-auto space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-3xl font-bold tracking-tight">Merchants</h2>
        <p class="text-muted-foreground mt-2">Manage merchants and their pricing configurations.</p>
      </div>
    </div>

    <!-- Merchants Table -->
    <div class="rounded-xl border bg-card text-card-foreground shadow-sm overflow-hidden">
        <div class="p-4 border-b bg-muted/40 flex items-center justify-between" v-if="selectedRows.length > 0">
            <span class="text-sm font-medium">{{ selectedRows.length }} selected</span>
            <div class="flex gap-2">
                <Button variant="outline" size="sm" @click="openBulkStatusUpdate">
                    Bulk Update Status
                </Button>
                <Button variant="outline" size="sm" @click="openBulkIntegrationUpdate">
                    Update Integration
                </Button>
            </div>
        </div>

      <DataTable
        :columns="merchantColumns"
        :data="merchants"
        :per-page="20"
        :selectable="true"
        @update:selection="selectedRows = $event"
      >
        <template #cell-status="{ value }">
          <span
            class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold"
            :class="{
              'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300': value === 'Approved',
              'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300': value === 'Submitted',
              'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300': value === 'Rejected' || value === 'Terminated',
              'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300': value === 'Draft'
            }"
          >
            {{ value }}
          </span>
        </template>
        <template #cell-wallet_balance="{ value }">
           ₹ {{ value }}
        </template>
        <template #cell-actions="{ row }">
          <Button variant="outline" size="sm" @click="editMerchant(row)">
            Edit
          </Button>
        </template>
      </DataTable>
    </div>
    <!-- Bulk Update Dialog -->
    <Dialog v-model:open="showBulkDialog">
      <DialogContent class="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Bulk Update {{ bulkAction === 'update_status' ? 'Status' : 'Integration' }}</DialogTitle>
          <DialogDescription>
             Update {{ selectedRows.length }} selected merchants.
          </DialogDescription>
        </DialogHeader>

        <div class="py-4">
             <div v-if="bulkAction === 'update_status'">
                <label class="block text-sm font-medium mb-2">New Status</label>
                <select v-model="bulkValue" class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2">
                    <option value="Draft">Draft</option>
                    <option value="Submitted">Submitted</option>
                    <option value="Approved">Approved</option>
                    <option value="Rejected">Rejected</option>
                    <option value="Terminated">Terminated</option>
                </select>
             </div>
             <div v-else-if="bulkAction === 'update_integration'">
                <label class="block text-sm font-medium mb-2">New Integration</label>
                <select v-model="bulkValue" class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2">
                    <option value="">Select Integration</option>
                    <option v-for="intg in integrations" :key="intg.name" :value="intg.name">
                        {{ intg.integration_name }}
                    </option>
                </select>
             </div>
        </div>

        <DialogFooter>
          <Button variant="outline" @click="showBulkDialog = false" :disabled="saving">Cancel</Button>
          <Button @click="performBulkUpdate" :loading="saving">Update All</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Edit Merchant Dialog -->
    <Dialog v-model:open="showEditDialog">
      <DialogContent class="sm:max-w-[900px] z-[9999]">
        <DialogHeader>
          <DialogTitle>Edit Merchant</DialogTitle>
          <DialogDescription>
            Update configuration for <span class="font-medium text-foreground">{{ editingMerchant?.company_name }}</span>
          </DialogDescription>
        </DialogHeader>
        
        <div class="mt-4 space-y-6" v-if="editingMerchant">
          <!-- Main Fields -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-medium mb-1">Status</label>
              <select v-model="editingMerchant.status" class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50">
                <option value="Draft">Draft</option>
                <option value="Submitted">Submitted</option>
                <option value="Approved">Approved</option>
                <option value="Rejected">Rejected</option>
                <option value="Terminated">Terminated</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Integration</label>
              <select v-model="editingMerchant.integration" class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50">
                <option value="">Select Integration</option>
                <option v-for="intg in integrations" :key="intg.name" :value="intg.name">
                  {{ intg.integration_name }}
                </option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Webhook URL</label>
              <input type="text" v-model="editingMerchant.webhook" class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50" />
            </div>
          </div>

          <!-- Product Pricing Table -->
          <div>
            <h4 class="text-sm font-medium mb-2">Product Pricing configuration</h4>
            <div class="rounded-md border max-h-[40vh] overflow-auto">
              <table class="w-full caption-bottom text-sm">
                <thead class="[&_tr]:border-b sticky top-0 bg-background z-10">
                  <tr class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                    <th class="h-10 px-4 text-left align-middle font-medium text-muted-foreground w-[150px]">Product</th>
                    <th class="h-10 px-4 text-left align-middle font-medium text-muted-foreground w-[120px]">Fee Type</th>
                    <th class="h-10 px-4 text-left align-middle font-medium text-muted-foreground w-[100px]">Fee</th>
                    <th class="h-10 px-4 text-left align-middle font-medium text-muted-foreground w-[120px]">Tax Type</th>
                    <th class="h-10 px-4 text-left align-middle font-medium text-muted-foreground w-[100px]">Tax Fee</th>
                    <th class="h-10 px-4 text-left align-middle font-medium text-muted-foreground">Range (Start - End)</th>
                    <th class="h-10 px-4 text-left align-middle font-medium text-muted-foreground w-[50px]"></th>
                  </tr>
                </thead>
                <tbody class="[&_tr:last-child]:border-0">
                  <tr v-for="(price, index) in editingMerchant.product_pricing || []" :key="index" class="border-b transition-colors hover:bg-muted/50">
                    <td class="p-2 align-middle font-medium">
                      <select v-model="price.product" class="h-8 w-full rounded border border-input bg-transparent px-2 text-xs">
                         <option value="" disabled>Select Product</option>
                         <option v-for="prod in products" :key="prod.name" :value="prod.name">
                           {{ prod.product_name }}
                         </option>
                      </select>
                    </td>
                    <td class="p-2 align-middle">
                      <select v-model="price.fee_type" class="h-8 w-full rounded border border-input bg-transparent px-2 text-xs">
                        <option value="Fixed">Fixed</option>
                        <option value="Percentage">Percentage</option>
                      </select>
                    </td>
                    <td class="p-2 align-middle">
                      <input type="number" step="0.01" v-model="price.fee" class="h-8 w-full rounded border border-input bg-transparent px-2 text-xs" />
                    </td>
                    <td class="p-2 align-middle">
                      <select v-model="price.tax_fee_type" class="h-8 w-full rounded border border-input bg-transparent px-2 text-xs">
                        <option value="Fixed">Fixed</option>
                        <option value="Percentage">Percentage</option>
                      </select>
                    </td>
                    <td class="p-2 align-middle">
                      <input type="number" step="0.01" v-model="price.tax_fee" class="h-8 w-full rounded border border-input bg-transparent px-2 text-xs" />
                    </td>
                    <td class="p-2 align-middle">
                      <div class="flex gap-1 items-center">
                        <input type="number" v-model="price.start_value" class="h-8 w-20 rounded border border-input bg-transparent px-2 text-xs" placeholder="Start" />
                        <span>-</span>
                        <input type="number" v-model="price.end_value" class="h-8 w-20 rounded border border-input bg-transparent px-2 text-xs" placeholder="End" />
                      </div>
                    </td>
                    <td class="p-2 align-middle">
                         <button @click="removePricingRow(index)" class="text-destructive hover:text-destructive/80">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
                         </button>
                    </td>
                  </tr>
                  <tr v-if="!editingMerchant.product_pricing?.length">
                    <td colspan="7" class="p-4 align-middle text-center text-muted-foreground">No pricing configured.</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="mt-2">
                 <Button variant="outline" size="sm" @click="addPricingRow">Add Pricing</Button>
            </div>
          </div>
        </div>

        <div class="mt-4 flex justify-end" v-if="validationError">
            <div class="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded border border-destructive/20">
                {{ validationError }}
            </div>
        </div>

        <DialogFooter class="mt-4">
          <Button variant="outline" @click="showEditDialog = false" :disabled="saving">Cancel</Button>
          <Button @click="saveMerchant" :loading="saving">Save Changes</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import DataTable from '@/components/DataTable.vue'
import { call, Button } from 'frappe-ui'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

const merchantColumns = [
  { key: 'company_name', label: 'Company', sortable: true },
  { key: 'company_email', label: 'Email', sortable: true },
  { key: 'status', label: 'Status', type: 'badge', sortable: true },
  { key: 'integration', label: 'Integration', sortable: true },
  { key: 'wallet_balance', label: 'Wallet Balance', sortable: true },
  { key: 'actions', label: 'Actions', sortable: false }
]

const merchants = ref([])
const integrations = ref([])
const products = ref([])
const loading = ref(false)
const saving = ref(false)
const showEditDialog = ref(false)
const editingMerchant = ref(null)
const validationError = ref('')

// Bulk Actions State
const selectedRows = ref([])
const showBulkDialog = ref(false)
const bulkAction = ref('') // 'update_status' or 'update_integration'
const bulkValue = ref('')

const fetchMerchants = async () => {
  loading.value = true
  try {
    const response = await call('iswitch.admin_portal_api.get_merchants')
    const data = response?.message || response
    if (data && data.merchants) {
      merchants.value = data.merchants
    }
  } catch (error) {
    console.error('Error fetching merchants:', error)
  } finally {
    loading.value = false
  }
}

const fetchIntegrations = async () => {
  try {
    const response = await call('iswitch.admin_portal_api.get_processors')
    const data = response?.message || response
    if (data && data.processors) {
      integrations.value = data.processors
    }
  } catch (error) {
    console.error('Error fetching integrations:', error)
  }
}

const fetchProducts = async () => {
  try {
    const response = await call('iswitch.admin_portal_api.get_services')
    const data = response?.message || response
    if (data && data.services) {
      products.value = data.services
    }
  } catch (error) {
    console.error('Error fetching products:', error)
  }
}

const editMerchant = (merchant) => {
  console.log('Edit clicked for:', merchant)
  try {
      // Deep copy to avoid mutating the table directly
      editingMerchant.value = JSON.parse(JSON.stringify(merchant))
      if (!editingMerchant.value.product_pricing) {
         editingMerchant.value.product_pricing = []
      }
      validationError.value = ''
      showEditDialog.value = true
      console.log('Dialog should be open, showEditDialog:', showEditDialog.value)
  } catch (e) {
      console.error('Error in editMerchant:', e)
      alert('Error opening edit dialog: ' + e.message)
  }
}

// Bulk Actions Logic
const openBulkStatusUpdate = () => {
    bulkAction.value = 'update_status'
    bulkValue.value = 'Approved' // Default
    showBulkDialog.value = true
}

const openBulkIntegrationUpdate = () => {
    bulkAction.value = 'update_integration'
    bulkValue.value = ''
    showBulkDialog.value = true
}

const performBulkUpdate = async () => {
    if (!bulkValue.value) return
    
    saving.value = true
    try {
        const merchantNames = selectedRows.value.map(row => row.name)
        await call('iswitch.admin_portal_api.bulk_update_merchants', {
            merchants: JSON.stringify(merchantNames),
            action: bulkAction.value,
            value: bulkValue.value
        })
        
        showBulkDialog.value = false
        selectedRows.value = [] // clear selection
        await fetchMerchants()
    } catch (error) {
        console.error('Error performing bulk update:', error)
    } finally {
        saving.value = false
    }
}


const addPricingRow = () => {
    if (!editingMerchant.value.product_pricing) {
        editingMerchant.value.product_pricing = []
    }
    editingMerchant.value.product_pricing.push({
        product: '',
        fee_type: 'Percentage',
        fee: 0,
        tax_fee_type: 'Percentage',
        tax_fee: 18,
        start_value: 0,
        end_value: 0
    })
    validationError.value = ''
}

const removePricingRow = (index) => {
    editingMerchant.value.product_pricing.splice(index, 1)
    validationError.value = ''
}

const validatePricing = () => {
    validationError.value = ''
    const pricing = editingMerchant.value.product_pricing || []
    const productRanges = {}

    // Group by product
    for (const p of pricing) {
        if (!p.product) continue 
        if (!productRanges[p.product]) {
            productRanges[p.product] = []
        }
        productRanges[p.product].push({
            start: parseFloat(p.start_value) || 0,
            end: parseFloat(p.end_value) || 0
        })
    }

    // Check overlaps
    for (const product in productRanges) {
        const ranges = productRanges[product].sort((a, b) => a.start - b.start)
        
        for (let i = 0; i < ranges.length - 1; i++) {
            const current = ranges[i]
            const next = ranges[i+1]
            
            // Overlap if EndA >= StartB
            if (current.end >= next.start) {
                validationError.value = `Overlapping ranges detected for product '${product}': ${current.start}-${current.end} overlaps with ${next.start}-${next.end}`
                return false
            }
        }
    }
    return true
}

const saveMerchant = async () => {
  if (!editingMerchant.value) return
  
  if (!validatePricing()) {
      return
  }
  
  saving.value = true
  try {
    await call('iswitch.admin_portal_api.update_merchant', {
      merchant: editingMerchant.value.name,
      status: editingMerchant.value.status,
      integration: editingMerchant.value.integration,
      webhook: editingMerchant.value.webhook,
      pricing: JSON.stringify(editingMerchant.value.product_pricing || [])
    })
    
    showEditDialog.value = false
    await fetchMerchants() // Refresh list
  } catch (error) {
    console.error('Error updating merchant:', error)
    // Here you might want to show an alert or toast
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchMerchants()
  fetchIntegrations()
  fetchProducts()
})
</script>
