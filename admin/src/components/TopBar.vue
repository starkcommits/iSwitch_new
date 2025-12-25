<template>
  <div class="border-b bg-background">
    <div class="flex h-16 items-center px-6 justify-between">
      <!-- Left: Mobile menu (hidden on desktop) -->
      <button
        @click="$emit('toggle-sidebar')"
        class="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 hover:bg-accent hover:text-accent-foreground h-9 w-9 md:hidden"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 12h18M3 6h18M3 18h18" />
        </svg>
      </button>

      <!-- Center: Empty spacer -->
      <div class="flex-1"></div>

      <!-- Right: Actions -->
      <div class="flex items-center gap-4">
        <!-- Wallet Balance -->
        <div class="flex items-center gap-2">
          <span class="text-sm text-muted-foreground hidden sm:inline">Wallet Balance:</span>
          <span class="text-sm font-semibold">{{ formatCurrency(walletBalance) }}</span>
        </div>

        <div class="h-6 w-px bg-border"></div>

        <!-- Theme Toggle -->
        <ThemeToggle />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { call } from 'frappe-ui'
import ThemeToggle from './ThemeToggle.vue'

const walletBalance = ref(0)
// ... keeping existing fetchWalletBalance and formatCurrency logic ...
// Fetch wallet balance
const fetchWalletBalance = async () => {
  try {
    const response = await call('iswitch.admin_portal_api.get_wallet_balance')
    if (response && response.wallet_balance !== undefined) {
      walletBalance.value = response.wallet_balance
    }
  } catch (error) {
    console.error('Error fetching wallet balance:', error)
  }
}

// Format currency in Indian Rupees
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount)
}

onMounted(() => {
  fetchWalletBalance()
})

defineEmits(['toggle-sidebar'])
</script>

<style scoped>
/* Minimal scoped styles, relying on Tailwind */
</style>
