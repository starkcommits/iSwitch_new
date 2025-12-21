<template>
  <div class="max-w-4xl mx-auto p-6">
    <div class="mb-8">
      <h1 class="text-3xl font-bold tracking-tight">Settings</h1>
      <p class="text-muted-foreground mt-2">Manage your account and operational settings.</p>
    </div>

    <Tabs default-value="profile" class="space-y-4">
      <TabsList>
        <TabsTrigger value="profile">Profile</TabsTrigger>
        <TabsTrigger value="onboard">Merchant Onboard</TabsTrigger>
        <TabsTrigger value="wallet">Wallet Recharge</TabsTrigger>
      </TabsList>
      
      <!-- Profile Tab -->
      <TabsContent value="profile" class="space-y-4">
        <div class="rounded-xl border bg-card text-card-foreground shadow-sm p-6 space-y-6">
          <div>
            <h3 class="text-lg font-semibold">Admin Profile</h3>
            <p class="text-sm text-muted-foreground mt-1">Your system administrator details.</p>
          </div>

          <div class="space-y-4 max-w-2xl">
            <div class="space-y-2">
              <label class="text-sm font-medium leading-none">Name</label>
              <input
                type="text"
                v-model="profile.name"
                disabled
                class="flex h-10 w-full rounded-md border border-input bg-muted px-3 py-2 text-sm ring-offset-background opacity-50 cursor-not-allowed"
              />
            </div>

            <div class="space-y-2">
              <label class="text-sm font-medium leading-none">Email</label>
              <input
                type="email"
                v-model="profile.email"
                disabled
                class="flex h-10 w-full rounded-md border border-input bg-muted px-3 py-2 text-sm ring-offset-background opacity-50 cursor-not-allowed"
              />
            </div>
            
            <div class="space-y-2">
              <label class="text-sm font-medium leading-none">Role</label>
              <input
                type="text"
                v-model="profile.role"
                disabled
                class="flex h-10 w-full rounded-md border border-input bg-muted px-3 py-2 text-sm ring-offset-background opacity-50 cursor-not-allowed"
              />
            </div>
          </div>
        </div>
      </TabsContent>

      <!-- Merchant Onboard Tab -->
      <TabsContent value="onboard" class="space-y-4">
        <div class="rounded-xl border bg-card text-card-foreground shadow-sm p-6 space-y-6">
          <div>
            <h3 class="text-lg font-semibold">Onboard New Merchant</h3>
            <p class="text-sm text-muted-foreground mt-1">Create a new merchant account and user.</p>
          </div>

          <div class="space-y-4 max-w-2xl">
            <div class="space-y-2">
              <label class="text-sm font-medium leading-none">Company Name</label>
              <input
                type="text"
                v-model="onboard.company_name"
                placeholder="Acme Corp"
                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              />
            </div>

            <div class="space-y-2">
              <label class="text-sm font-medium leading-none">Email</label>
              <input
                type="email"
                v-model="onboard.email"
                placeholder="admin@acme.com"
                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              />
            </div>
            
            <div class="space-y-2">
              <label class="text-sm font-medium leading-none">Password</label>
              <input
                type="password"
                v-model="onboard.password"
                placeholder="********"
                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              />
            </div>

             <div class="space-y-2">
              <label class="text-sm font-medium leading-none">PAN Card (Optional)</label>
              <input
                type="text"
                v-model="onboard.pancard"
                placeholder="AAAAA0000A"
                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              />
            </div>

            <div class="pt-4 space-y-2">
              <div v-if="onboardSuccess" class="p-3 text-sm text-green-600 bg-green-50 border border-green-200 rounded-md">
                {{ onboardSuccess }}
              </div>
              <div v-if="onboardError" class="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md">
                {{ onboardError }}
              </div>
              <Button @click="createMerchant" :loading="onboardLoading">
                Create Merchant
              </Button>
            </div>
          </div>
        </div>
      </TabsContent>

      <!-- Wallet Recharge Tab -->
      <TabsContent value="wallet" class="space-y-4">
        <div class="rounded-xl border bg-card text-card-foreground shadow-sm p-6 space-y-6">
          <div>
            <h3 class="text-lg font-semibold">Wallet Recharge</h3>
            <p class="text-sm text-muted-foreground mt-1">Credit funds to a merchant's wallet.</p>
          </div>

          <div class="space-y-4 max-w-2xl">
            <div class="space-y-2">
              <label class="text-sm font-medium leading-none">Select Merchant</label>
              <select 
                v-model="recharge.merchant_id" 
                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              >
                <option value="" disabled>Select a merchant</option>
                <option v-for="m in merchantList" :key="m.name" :value="m.name">
                   {{ m.company_name }} ({{ m.company_email }})
                </option>
              </select>
            </div>

            <div class="space-y-2">
              <label class="text-sm font-medium leading-none">Amount (INR)</label>
              <input
                type="number"
                v-model="recharge.amount"
                placeholder="0.00"
                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              />
            </div>

            <div class="pt-4 space-y-2">
              <div v-if="rechargeSuccess" class="p-3 text-sm text-green-600 bg-green-50 border border-green-200 rounded-md">
                 {{ rechargeSuccess }}
              </div>
              <div v-if="rechargeError" class="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md">
                 {{ rechargeError }}
              </div>
              <Button @click="processRecharge" :loading="rechargeLoading">
                Recharge Wallet
              </Button>
            </div>
          </div>
        </div>
      </TabsContent>
    </Tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { call, Button } from 'frappe-ui'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

// Profile
const profile = ref({
  name: '',
  email: '',
  role: ''
})

// Onboarding
const onboard = ref({
  company_name: '',
  email: '',
  password: '',
  pancard: ''
})
const onboardLoading = ref(false)
const onboardSuccess = ref('')
const onboardError = ref('')

// Wallet Recharge
const recharge = ref({
  merchant_id: '',
  amount: ''
})
const rechargeLoading = ref(false)
const rechargeSuccess = ref('')
const rechargeError = ref('')
const merchantList = ref([])

// Fetch admin profile
const fetchProfile = async () => {
  try {
    const response = await call('iswitch.admin_portal_api.get_admin_profile')
    const data = response?.message || response
    if (data) {
      profile.value = data
    }
  } catch (error) {
    console.error('Error fetching admin profile:', error)
  }
}

// Fetch merchant list for dropdown
const fetchMerchants = async () => {
    try {
        const response = await call('iswitch.admin_portal_api.get_merchants', { page_size: 100 }) // Load top 100 for now
        const data = response?.message || response
        if (data && data.merchants) {
            merchantList.value = data.merchants
        }
    } catch (error) {
        console.error('Error fetching merchants:', error)
    }
}

// Create new merchant
const createMerchant = async () => {
    onboardSuccess.value = ''
    onboardError.value = ''
    
    if (!onboard.value.company_name || !onboard.value.email || !onboard.value.password) {
        onboardError.value = "Please fill all required fields"
        return
    }
    
    onboardLoading.value = true
    try {
        const response = await call('iswitch.admin_portal_api.onboard_merchant', {
            company_name: onboard.value.company_name,
            email: onboard.value.email,
            password: onboard.value.password,
            pancard: onboard.value.pancard || 'PENDING'
        })
        
        if (response && (response.success || response.message?.success)) {
            onboardSuccess.value = "Merchant created successfully!"
            onboard.value = { company_name: '', email: '', password: '', pancard: '' }
            fetchMerchants() // Refresh list
        } else {
            onboardError.value = response.error || response.message?.error || "Failed to create merchant"
        }
    } catch (error) {
        console.error("Error creating merchant:", error)
        onboardError.value = "Error creating merchant: " + error.message
    } finally {
        onboardLoading.value = false
    }
}

// Process Wallet Recharge
const processRecharge = async () => {
    rechargeSuccess.value = ''
    rechargeError.value = ''

    if (!recharge.value.merchant_id || !recharge.value.amount || parseFloat(recharge.value.amount) <= 0) {
        rechargeError.value = "Please select a merchant and enter a valid positive amount"
        return
    }
    
    rechargeLoading.value = true
    try {
        const response = await call('iswitch.admin_portal_api.credit_wallet', {
            merchant_id: recharge.value.merchant_id,
            amount: parseFloat(recharge.value.amount)
        })
         if (response && (response.success || response.message?.success)) {
            rechargeSuccess.value = `Wallet recharged successfully! New Balance: ${response.new_balance || response.message?.new_balance}`
            recharge.value.amount = ''
        } else {
            rechargeError.value = response.error || response.message?.error || "Failed to recharge wallet"
        }
    } catch (error) {
         console.error("Error recharging wallet:", error)
         rechargeError.value = "Error recharging wallet: " + error.message
    } finally {
        rechargeLoading.value = false
    }
}

onMounted(() => {
  fetchProfile()
  fetchMerchants()
})
</script>
