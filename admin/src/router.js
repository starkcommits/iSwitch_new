import { userResource } from "@/data/user"
import { createRouter, createWebHistory } from "vue-router"
import { session } from "./data/session"

const routes = [
	{
		path: '/',
		name: 'Dashboard',
		component: () => import('@/pages/Home.vue'),
		meta: { requiresAuth: true, role: 'Admin' }
	},
	{
		path: '/orders',
		name: 'Orders',
		component: () => import('@/pages/Orders.vue'),
		meta: { requiresAuth: true, role: 'Admin' }
	},
	{
		path: '/transactions',
		name: 'Transactions',
		component: () => import('@/pages/Transactions.vue'),
		meta: { requiresAuth: true, role: 'Admin' }
	},
	{
		path: '/merchants',
		name: 'Merchants',
		component: () => import('@/pages/Merchants.vue'),
		meta: { requiresAuth: true, role: 'Admin' }
	},
	{
		path: '/processors',
		name: 'Processors',
		component: () => import('@/pages/Processors.vue'),
		meta: { requiresAuth: true, role: 'Admin' }
	},
	{
		path: '/services',
		name: 'Services',
		component: () => import('@/pages/Services.vue'),
		meta: { requiresAuth: true, role: 'Admin' }
	},
	{
		path: '/van-logs',
		name: 'VANLogs',
		component: () => import('@/pages/VANLogs.vue'),
		meta: { requiresAuth: true, role: 'Admin' }
	},
	{
		path: '/virtual-accounts',
		name: 'VirtualAccounts',
		component: () => import('@/pages/VirtualAccounts.vue'),
		meta: { requiresAuth: true, role: 'Admin' }
	},
	{
		path: '/settings',
		name: 'Settings',
		component: () => import('@/pages/Settings.vue'),
		meta: { requiresAuth: true, role: 'Admin' }
	},
	{
		path: '/login',
		name: 'Login',
		component: () => import('@/pages/Login.vue'),
	},
	{
		path: '/403',
		name: 'Forbidden',
		component: () => import('@/pages/Forbidden.vue'),
	},
	{
		path: '/500',
		name: 'ServerError',
		component: () => import('@/pages/ServerError.vue'),
	},
	{
		path: '/:pathMatch(.*)*',
		name: 'NotFound',
		component: () => import('@/pages/NotFound.vue'),
	},
]

const router = createRouter({
	history: createWebHistory("/admin"),
	routes,
})

router.beforeEach(async (to, from, next) => {
	// Allow non-protected routes
	if (!to.meta.requiresAuth) {
		return next()
	}

	// Check if user is logged in
	let isLoggedIn = session.isLoggedIn
	try {
		await userResource.promise
	} catch (error) {
		isLoggedIn = false
	}

	if (!isLoggedIn) {
		window.location.href = '/login'
		return
	}

	// Load user context if not already loaded
	if (!session.userContext.data) {
		await session.userContext.fetch()
	}

	const roles = session.roles || []

	// Check role requirement
	if (to.meta.role && !roles.includes(to.meta.role)) {
		// Admin trying merchant portal - redirect to admin
		if (roles.includes('Admin')) {
			return next('/admin')
		}

		// Merchant trying admin portal - redirect to dashboard
		if (roles.includes('Merchant')) {
			window.location.href = '/dashboard'
			return
		}

		// Unknown user - redirect to login
		window.location.href = '/login'
		return
	}

	next()
})

export default router
