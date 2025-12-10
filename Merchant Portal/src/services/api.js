import { createResource } from 'frappe-ui'

/**
 * API Service for Merchant Portal
 * Handles all backend API calls using Frappe UI resources
 */

// Dashboard Stats
export const dashboardStats = createResource({
    url: 'iswitch.portal_api.get_dashboard_stats',
    auto: false,
    transform(data) {
        return data
    }
})

// Wallet Balance
export const walletBalance = createResource({
    url: 'iswitch.portal_api.get_wallet_balance_header',
    auto: false,
    transform(data) {
        return data
    }
})

// Orders
export const orders = createResource({
    url: 'iswitch.portal_api.get_merchant_orders',
    auto: false,
    params: {
        page: 1,
        limit: 10,
        status: null,
        from_date: null,
        to_date: null
    },
    transform(data) {
        return data
    }
})

export function exportOrders(filters) {
    const params = new URLSearchParams()
    if (filters.status) params.append('status', filters.status)
    if (filters.from_date) params.append('from_date', filters.from_date)
    if (filters.to_date) params.append('to_date', filters.to_date)

    window.open(`/api/method/iswitch.portal_api.export_merchant_orders?${params.toString()}`, '_blank')
}

// Ledger
export const ledger = createResource({
    url: 'iswitch.portal_api.get_merchant_ledger',
    auto: false,
    params: {
        page: 1,
        limit: 10,
        transaction_type: null,
        from_date: null,
        to_date: null
    },
    transform(data) {
        return data
    }
})

export function exportLedger(filters) {
    const params = new URLSearchParams()
    if (filters.transaction_type) params.append('transaction_type', filters.transaction_type)
    if (filters.from_date) params.append('from_date', filters.from_date)
    if (filters.to_date) params.append('to_date', filters.to_date)

    window.open(`/api/method/iswitch.portal_api.export_merchant_ledger?${params.toString()}`, '_blank')
}

// VAN Logs
export const vanLogs = createResource({
    url: 'iswitch.portal_api.get_merchant_van_logs',
    auto: false,
    params: {
        page: 1,
        limit: 10,
        from_date: null,
        to_date: null
    },
    transform(data) {
        return data
    }
})

export function exportVANLogs(filters) {
    const params = new URLSearchParams()
    if (filters.from_date) params.append('from_date', filters.from_date)
    if (filters.to_date) params.append('to_date', filters.to_date)

    window.open(`/api/method/iswitch.portal_api.export_merchant_van_logs?${params.toString()}`, '_blank')
}

// Webhook Config
export const webhookConfig = createResource({
    url: 'iswitch.portal_api.get_webhook_config',
    auto: false
})

export const updateWebhook = createResource({
    url: 'iswitch.portal_api.update_webhook_config',
    auto: false,
    makeParams(values) {
        return {
            webhook_url: values.webhook_url
        }
    }
})

// IP Whitelist
export const ipWhitelist = createResource({
    url: 'iswitch.portal_api.get_ip_whitelist',
    auto: false
})

export const addWhitelistIP = createResource({
    url: 'iswitch.portal_api.add_whitelisted_ip',
    auto: false,
    makeParams(values) {
        return {
            whitelisted_ip: values.ip
        }
    }
})

export const deleteWhitelistIP = createResource({
    url: 'iswitch.portal_api.delete_whitelisted_ip',
    auto: false,
    makeParams(values) {
        return {
            ip_name: values.name
        }
    }
})

// Merchant Profile
export const merchantProfile = createResource({
    url: 'iswitch.portal_api.get_merchant_profile_page',
    auto: false
})
