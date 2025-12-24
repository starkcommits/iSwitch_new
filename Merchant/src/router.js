import { userResource } from "@/data/user"
import { createRouter, createWebHistory } from "vue-router"
import { session } from "./data/session"

const routes = [
	{
		path: '/',
		name: 'Dashboard',
		component: () => import('@/pages/Home.vue'),
	},
	{
		path: '/orders',
		name: 'Orders',
		component: () => import('@/pages/Orders.vue'),
	},
	{
		path: '/ledger',
		name: 'Ledger',
		component: () => import('@/pages/Ledger.vue'),
	},
	{
		path: '/van-logs',
		name: 'VANLogs',
		component: () => import('@/pages/VANLogs.vue'),
		meta: { requiresAuth: true }
	},
	{
		path: '/virtual-accounts',
		name: 'VirtualAccounts',
		component: () => import('@/pages/VirtualAccounts.vue'),
		meta: { requiresAuth: true }
	},
	{
		path: '/support',
		name: 'Support',
		component: () => import('@/pages/Support.vue'),
		meta: { requiresAuth: true }
	},
	{
		path: '/settings',
		name: 'Settings',
		component: () => import('@/pages/Settings.vue'),
		meta: { requiresAuth: true }
	},
	{
		path: '/login',
		name: 'Login',
		component: () => import('@/pages/Login.vue'),
	},
]

const router = createRouter({
	history: createWebHistory("/dashboard"),
	routes,
})

router.beforeEach(async (to, from, next) => {
	let isLoggedIn = session.isLoggedIn
	try {
		await userResource.promise
	} catch (error) {
		isLoggedIn = false
	}

	if (to.name === "Login" && isLoggedIn) {
		next({ name: "Dashboard" })
	} else if (!isLoggedIn) {
		window.location.href = '/login'
	} else {
		next()
	}
})

export default router
