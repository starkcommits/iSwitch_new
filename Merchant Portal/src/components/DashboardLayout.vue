<template>
  <div class="dashboard-layout">
    <Sidebar :mobile-open="mobileOpen" @close-mobile="mobileOpen = false" />
    <div class="main-wrapper">
      <TopBar @toggle-sidebar="toggleSidebar" />
      <main class="main-content">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Sidebar from './Sidebar.vue'
import TopBar from './TopBar.vue'

const mobileOpen = ref(false)

const toggleSidebar = () => {
  mobileOpen.value = !mobileOpen.value
}
</script>

<style scoped>
.dashboard-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: var(--color-bg-primary);
}

.main-wrapper {
  flex: 1;
  margin-left: 260px;
  display: flex;
  flex-direction: column;
  height: 100%;
  transition: margin-left 0.3s ease;
  overflow: hidden;
}

.main-content {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
  overflow-x: hidden;
}

@media (max-width: 768px) {
  .main-wrapper {
    margin-left: 0;
  }
  
  .main-content {
    padding: 1rem;
    padding-bottom: 2rem; /* Reduced from 5rem to avoid extra scroll */
  }
}
</style>
