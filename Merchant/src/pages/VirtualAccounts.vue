<template>
    <div class="p-6 space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold tracking-tight">Virtual Accounts</h1>
          <p class="text-muted-foreground mt-2">Manage your virtual bank accounts.</p>
        </div>
        <button
          class="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4"
        >
          Request New Account
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>

      <!-- Data Table -->
      <div v-else class="rounded-md border bg-card">
        <div class="relative w-full overflow-auto">
          <table class="w-full caption-bottom text-sm">
            <thead class="[&_tr]:border-b">
              <tr class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Account Number</th>
                <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">IFSC Code</th>
                <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Status</th>
                <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Merchant Name</th>
              </tr>
            </thead>
            <tbody class="[&_tr:last-child]:border-0">
              <tr 
                v-for="account in virtualAccounts" 
                :key="account.name"
                class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted"
              >
                <td class="p-4 align-middle font-mono font-medium">{{ account.account_number }}</td>
                <td class="p-4 align-middle">{{ account.ifsc }}</td>
                <td class="p-4 align-middle">
                  <span 
                    class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold"
                    :class="{
                      'bg-green-100 text-green-800 border-green-200': account.status === 'Active',
                      'bg-yellow-100 text-yellow-800 border-yellow-200': account.status === 'Inactive',
                      'bg-red-100 text-red-800 border-red-200': account.status === 'Frozen',
                      'bg-secondary text-secondary-foreground': !['Active', 'Inactive', 'Frozen'].includes(account.status)
                    }"
                  >
                    {{ account.status }}
                  </span>
                </td>
                <td class="p-4 align-middle">{{ account.merchant_name }}</td>
              </tr>
              <tr v-if="virtualAccounts.length === 0">
                <td colspan="4" class="p-4 align-middle text-center text-muted-foreground">
                  No virtual accounts found.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { call } from 'frappe-ui'

const loading = ref(true)
const virtualAccounts = ref([])


const fetchVirtualAccounts = async () => {
  try {
    const response = await call('iswitch.merchant_portal_api.get_virtual_accounts')
    // Handle both wrapped and unwrapped responses
    let data = response
    if (response.message && typeof response.message === 'object' && !Array.isArray(response.message)) {
      data = response.message
    }
    
    if (data.success && Array.isArray(data.accounts)) {
      virtualAccounts.value = data.accounts
    } else if (Array.isArray(data)) { // Legacy fallback
      virtualAccounts.value = data
    }
  } catch (error) {
    console.error('Error fetching virtual accounts:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchVirtualAccounts()
})
</script>
