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
		path: '/transactions',
		name: 'Transactions',
		component: () => import('@/pages/Transactions.vue'),
	},
	{
		path: '/merchants',
		name: 'Merchants',
		component: () => import('@/pages/Merchants.vue'),
	},
	{
		path: '/processors',
		name: 'Processors',
		component: () => import('@/pages/Processors.vue'),
	},
	{
		path: '/services',
		name: 'Services',
		component: () => import('@/pages/Services.vue'),
		meta: { requiresAuth: true }
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
	history: createWebHistory("/admin"),
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
	} else if (to.name !== "Login" && !isLoggedIn) {
		next({ name: "Login" })
	} else {
		next()
	}
})

export default router
