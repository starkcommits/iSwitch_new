import { ref, watchEffect } from 'vue'

const isDark = ref(false)

export function useTheme() {
    // Initialize theme from localStorage or system preference
    const initTheme = () => {
        if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            isDark.value = true
            document.documentElement.classList.add('dark')
        } else {
            isDark.value = false
            document.documentElement.classList.remove('dark')
        }
    }

    // Toggle theme function
    const toggleTheme = () => {
        if (isDark.value) {
            isDark.value = false
            document.documentElement.classList.remove('dark')
            localStorage.theme = 'light'
        } else {
            isDark.value = true
            document.documentElement.classList.add('dark')
            localStorage.theme = 'dark'
        }
    }

    // Watch for system theme changes if no preference is saved
    watchEffect(() => {
        if (!localStorage.theme) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
            const handler = (e) => {
                if (e.matches) {
                    isDark.value = true
                    document.documentElement.classList.add('dark')
                } else {
                    isDark.value = false
                    document.documentElement.classList.remove('dark')
                }
            }
            mediaQuery.addEventListener('change', handler)
            return () => mediaQuery.removeEventListener('change', handler)
        }
    })

    // Initialize on mount
    initTheme()

    return {
        isDark,
        toggleTheme
    }
}
