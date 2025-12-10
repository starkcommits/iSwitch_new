<template>
  <div 
    class="fixed inset-y-0 left-0 z-50 flex flex-col bg-background border-r border-border transition-all duration-300"
    :class="[isCollapsed ? 'w-20' : 'w-64', isMobile && !mobileOpen ? '-translate-x-full' : 'translate-x-0']"
  >
    <!-- Header -->
    <div class="h-16 flex items-center justify-between px-4 border-b border-border">
      <div class="flex items-center gap-2 overflow-hidden">
        <div class="w-8 h-8 rounded bg-primary flex items-center justify-center shrink-0">
          <svg class="w-5 h-5 text-primary-foreground" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
          </svg>
        </div>
        <span v-if="!isCollapsed" class="font-bold text-lg text-foreground whitespace-nowrap">iSwitch</span>
      </div>
      <button 
        @click="toggleCollapse"
        class="hidden md:block p-2 rounded-md hover:bg-muted text-muted-foreground transition-colors"
      >
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M15 18l-6-6 6-6" v-if="!isCollapsed"/>
          <path d="M9 18l6-6-6-6" v-else/>
        </svg>
      </button>
      <button 
        @click="$emit('close-mobile')"
        class="md:hidden p-2 rounded-md hover:bg-muted text-muted-foreground transition-colors"
      >
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 6L6 18M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 overflow-y-auto py-4 px-3 space-y-1">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="flex items-center gap-3 px-3 py-2 rounded-md transition-colors group relative"
        :class="isActive(item.path) ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted hover:text-foreground'"
        @click="isMobile && $emit('close-mobile')"
      >
        <component :is="item.icon" class="w-5 h-5 shrink-0" />
        <span 
          v-if="!isCollapsed" 
          class="text-sm font-medium whitespace-nowrap"
        >{{ item.label }}</span>
        
        <!-- Tooltip for collapsed state -->
        <div 
          v-if="isCollapsed && !isMobile" 
          class="absolute left-full ml-2 px-2 py-1 bg-popover text-popover-foreground text-xs rounded shadow-md opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50"
        >
          {{ item.label }}
        </div>
      </router-link>
    </nav>

    <!-- User Footer -->
    <div class="p-4 border-t border-border relative">
      <button 
        @click="toggleUserMenu"
        class="flex items-center gap-3 w-full hover:bg-accent rounded-md p-2 transition-colors"
      >
        <div class="w-9 h-9 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-sm font-medium text-white shrink-0">
          {{ userInitials }}
        </div>
        <div v-if="!isCollapsed" class="min-w-0 flex-1 text-left">
          <div class="text-sm font-medium text-foreground truncate">{{ userName }}</div>
          <div class="text-xs text-muted-foreground truncate">{{ userEmail }}</div>
        </div>
        <svg v-if="!isCollapsed" class="h-4 w-4 text-muted-foreground shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>

      <!-- User Dropdown Menu -->
      <div
        v-if="showUserMenu"
        class="absolute bottom-full left-4 right-4 mb-2 rounded-lg border bg-popover p-1 text-popover-foreground shadow-lg z-50"
      >
        <button
          @click="goToSettings"
          class="relative flex w-full cursor-pointer select-none items-center rounded-sm px-2 py-2 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground"
        >
          <svg class="mr-2 h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3" />
            <path d="M12 1v6m0 6v6M1 12h6m6 0h6M4.22 4.22l4.24 4.24m5.08 5.08l4.24 4.24M19.78 4.22l-4.24 4.24m-5.08 5.08l-4.24 4.24" />
          </svg>
          Settings
        </button>

        <div class="h-px bg-border my-1"></div>

        <button
          @click="handleLogout"
          class="relative flex w-full cursor-pointer select-none items-center rounded-sm px-2 py-2 text-sm outline-none transition-colors hover:bg-destructive/10 text-destructive"
        >
          <svg class="mr-2 h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" />
          </svg>
          Logout
        </button>
      </div>
    </div>
  </div>

  <!-- Mobile Overlay -->
  <div 
    v-if="isMobile && mobileOpen" 
    @click="$emit('close-mobile')"
    class="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 md:hidden"
  ></div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { session } from '@/data/session'
import { 
  LayoutDashboard, 
  ShoppingBag, 
  BookOpen, 
  FileText, 
  Settings,
  CreditCard,
  HelpCircle
} from 'lucide-vue-next'

const props = defineProps({
  mobileOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close-mobile'])

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/orders', label: 'Orders', icon: ShoppingBag },
  { path: '/virtual-accounts', label: 'Virtual Accounts', icon: CreditCard },
  { path: '/ledger', label: 'Ledger', icon: BookOpen },
  { path: '/van-logs', label: 'VAN Logs', icon: FileText },
  { path: '/support', label: 'Support', icon: HelpCircle },
  { path: '/settings', label: 'Settings', icon: Settings },
]

const route = useRoute()
const router = useRouter()
const isCollapsed = ref(false)
const isMobile = ref(false)
const showUserMenu = ref(false)

const userName = computed(() => session.user || 'User')
const userEmail = computed(() => session.user || 'user@example.com')
const userInitials = computed(() => {
  const name = userName.value
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
})

const isActive = (path) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

const checkMobile = () => {
  isMobile.value = window.matchMedia('(max-width: 768px)').matches
  if (!isMobile.value) {
    isCollapsed.value = false
  }
}

const toggleUserMenu = () => {
  showUserMenu.value = !showUserMenu.value
}

const goToSettings = () => {
  router.push('/settings')
  showUserMenu.value = false
  if (isMobile.value) {
    emit('close-mobile')
  }
}

const handleLogout = () => {
  session.logout.submit()
  showUserMenu.value = false
}

const handleClickOutside = (event) => {
  if (showUserMenu.value) {
    const userSection = event.target.closest('.p-4.border-t')
    if (!userSection) {
      showUserMenu.value = false
    }
  }
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* Scoped styles mainly for transition nuances if Tailwind doesn't cover */
</style>
