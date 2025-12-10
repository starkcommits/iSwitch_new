// Portal Renderers - Functions to render API responses

function renderDashboard(data) {
    const { wallet, merchant, stats } = data;

    const html = `
        <div class="page-header">
            <h1>Welcome back, ${merchant.name}</h1>
            <p>Here's what's happening with your account today</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-card-header">
                    <span class="stat-card-title">Wallet Balance</span>
                    <div class="stat-card-icon primary">
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="20" height="20">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"/>
                        </svg>
                    </div>
                </div>
                <div class="stat-card-value">${formatCurrency(wallet.balance)}</div>
                <div class="stat-card-label">
                    <span class="badge ${wallet.status === 'Active' ? 'badge-success' : 'badge-danger'}">${wallet.status}</span>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-card-header">
                    <span class="stat-card-title">Total Orders</span>
                    <div class="stat-card-icon primary">
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="20" height="20">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                        </svg>
                    </div>
                </div>
                <div class="stat-card-value">${formatNumber(stats.total_orders)}</div>
                <div class="stat-card-label">All time transactions</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-card-header">
                    <span class="stat-card-title">Processed</span>
                    <div class="stat-card-icon success">
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="20" height="20">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                    </div>
                </div>
                <div class="stat-card-value">${formatNumber(stats.processed_orders)}</div>
                <div class="stat-card-label">${formatCurrency(stats.total_processed_amount)}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-card-header">
                    <span class="stat-card-title">Pending</span>
                    <div class="stat-card-icon warning">
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="20" height="20">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                    </div>
                </div>
                <div class="stat-card-value">${formatNumber(stats.pending_orders)}</div>
                <div class="stat-card-label">${formatCurrency(stats.total_pending_amount)}</div>
            </div>
        </div>
        
        <div class="table-container">
            <div class="table-header">
                <h3>Recent Transactions</h3>
                <button class="btn btn-secondary btn-sm" onclick="loadTransactions()">View All</button>
            </div>
            
            <div id="recent-transactions"
                 hx-get="/api/method/iswitch.portal_api.get_merchant_orders?page=1&limit=5"
                 hx-trigger="load"
                 hx-swap="innerHTML">
                <div style="text-align: center; padding: 2rem;">
                    <div class="loading-spinner" style="margin: 0 auto;"></div>
                </div>
            </div>
        </div>
    `;

    document.getElementById('main-content').innerHTML = html;
    document.getElementById('merchant-name').textContent = merchant.name;
}

function renderOrdersTable(data) {
    const { orders, pagination } = data;

    if (!orders || orders.length === 0) {
        document.getElementById('transactions-content').innerHTML = `
            <div class="empty-state">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
                <h3>No transactions found</h3>
                <p>You don't have any transactions yet</p>
            </div>
        `;
        return;
    }

    let tableHTML = `
        <table id="transactions-table">
            <thead>
                <tr>
                    <th>Order ID</th>
                    <th>Customer</th>
                    <th>Amount</th>
                    <th>Fee</th>
                    <th>Product</th>
                    <th>Status</th>
                    <th>UTR</th>
                    <th>Date</th>
                </tr>
            </thead>
            <tbody>
    `;

    orders.forEach(order => {
        tableHTML += `
            <tr>
                <td><code>${order.name}</code></td>
                <td>${order.customer_name || '-'}</td>
                <td>${formatCurrency(order.order_amount)}</td>
                <td>${formatCurrency(order.fee)}</td>
                <td><span class="badge badge-info">${order.product}</span></td>
                <td><span class="badge ${getStatusBadgeClass(order.status)}">${order.status}</span></td>
                <td>${order.utr || '-'}</td>
                <td>${formatDate(order.creation)}</td>
            </tr>
        `;
    });

    tableHTML += `
            </tbody>
        </table>
        
        <div class="pagination">
            <div class="pagination-info">
                Showing ${((pagination.page - 1) * pagination.limit) + 1} to ${Math.min(pagination.page * pagination.limit, pagination.total)} of ${pagination.total} results
            </div>
            <div class="pagination-controls">
                ${pagination.page > 1 ? `<button class="btn btn-secondary btn-sm" onclick="loadPage(${pagination.page - 1})">Previous</button>` : ''}
                <span style="padding: 0 1rem;">Page ${pagination.page} of ${pagination.pages}</span>
                ${pagination.page < pagination.pages ? `<button class="btn btn-secondary btn-sm" onclick="loadPage(${pagination.page + 1})">Next</button>` : ''}
            </div>
        </div>
    `;

    document.getElementById('transactions-content').innerHTML = tableHTML;
}

function renderLedgerTable(data) {
    const { ledger, pagination } = data;

    if (!ledger || ledger.length === 0) {
        document.getElementById('ledger-content').innerHTML = `
            <div class="empty-state">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                </svg>
                <h3>No ledger entries found</h3>
                <p>Your ledger is empty</p>
            </div>
        `;
        return;
    }

    let tableHTML = `
        <table>
            <thead>
                <tr>
                    <th>Transaction ID</th>
                    <th>Order ID</th>
                    <th>Type</th>
                    <th>Opening Balance</th>
                    <th>Closing Balance</th>
                    <th>Status</th>
                    <th>Date</th>
                </tr>
            </thead>
            <tbody>
    `;

    ledger.forEach(entry => {
        tableHTML += `
            <tr>
                <td><code>${entry.transaction_id || '-'}</code></td>
                <td><code>${entry.order || '-'}</code></td>
                <td><span class="badge ${entry.transaction_type === 'Credit' ? 'badge-success' : 'badge-warning'}">${entry.transaction_type}</span></td>
                <td>${formatCurrency(entry.opening_balance)}</td>
                <td>${formatCurrency(entry.closing_balance)}</td>
                <td><span class="badge ${getStatusBadgeClass(entry.status)}">${entry.status}</span></td>
                <td>${formatDate(entry.creation)}</td>
            </tr>
        `;
    });

    tableHTML += `
            </tbody>
        </table>
        
        <div class="pagination">
            <div class="pagination-info">
                Showing ${((pagination.page - 1) * pagination.limit) + 1} to ${Math.min(pagination.page * pagination.limit, pagination.total)} of ${pagination.total} results
            </div>
            <div class="pagination-controls">
                ${pagination.page > 1 ? `<button class="btn btn-secondary btn-sm" onclick="loadLedgerPage(${pagination.page - 1})">Previous</button>` : ''}
                <span style="padding: 0 1rem;">Page ${pagination.page} of ${pagination.pages}</span>
                ${pagination.page < pagination.pages ? `<button class="btn btn-secondary btn-sm" onclick="loadLedgerPage(${pagination.page + 1})">Next</button>` : ''}
            </div>
        </div>
    `;

    document.getElementById('ledger-content').innerHTML = tableHTML;
}

function renderVANLogsTable(data) {
    const { logs, pagination } = data;

    if (!logs || logs.length === 0) {
        document.getElementById('van-content').innerHTML = `
            <div class="empty-state">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"/>
                </svg>
                <h3>No VAN logs found</h3>
                <p>No virtual account transactions yet</p>
            </div>
        `;
        return;
    }

    let tableHTML = `
        <table>
            <thead>
                <tr>
                    <th>Account Number</th>
                    <th>Amount</th>
                    <th>UTR</th>
                    <th>Merchant</th>
                    <th>Date</th>
                </tr>
            </thead>
            <tbody>
    `;

    logs.forEach(log => {
        tableHTML += `
            <tr>
                <td><code>${log.account_number || '-'}</code></td>
                <td>${formatCurrency(log.amount)}</td>
                <td>${log.utr || '-'}</td>
                <td>${log.merchant || '-'}</td>
                <td>${formatDate(log.creation)}</td>
            </tr>
        `;
    });

    tableHTML += `
            </tbody>
        </table>
        
        <div class="pagination">
            <div class="pagination-info">
                Showing ${((pagination.page - 1) * pagination.limit) + 1} to ${Math.min(pagination.page * pagination.limit, pagination.total)} of ${pagination.total} results
            </div>
            <div class="pagination-controls">
                ${pagination.page > 1 ? `<button class="btn btn-secondary btn-sm" onclick="loadVANPage(${pagination.page - 1})">Previous</button>` : ''}
                <span style="padding: 0 1rem;">Page ${pagination.page} of ${pagination.pages}</span>
                ${pagination.page < pagination.pages ? `<button class="btn btn-secondary btn-sm" onclick="loadVANPage(${pagination.page + 1})">Next</button>` : ''}
            </div>
        </div>
    `;

    document.getElementById('van-content').innerHTML = tableHTML;
}

function renderAPIKeys(data) {
    const html = `
        <div style="margin-bottom: 1.5rem;">
            <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">API Key (Public)</label>
            <div class="api-key-display">
                <span class="api-key-value">${data.public_key || 'Not generated yet'}</span>
                ${data.public_key ? `<button class="btn btn-secondary btn-sm" onclick="copyToClipboard('${data.public_key}')">Copy</button>` : ''}
            </div>
        </div>
        
        <div>
            <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">API Secret (Private)</label>
            <div class="api-key-display">
                <span class="api-key-value">${data.secret_key || 'Not generated yet'}</span>
                ${data.secret_key ? `<button class="btn btn-secondary btn-sm" onclick="copyToClipboard('${data.secret_key}')">Copy</button>` : ''}
            </div>
        </div>
        
        ${data.secret_key ? `
        <div style="margin-top: 1rem; padding: 1rem; background: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 8px;">
            <p style="margin: 0; font-size: 0.875rem; color: #92400e;">
                <strong>Important:</strong> Keep your API secret secure. Do not share it publicly or commit it to version control.
            </p>
        </div>
        ` : ''}
    `;

    document.getElementById('api-keys-display').innerHTML = html;
}

function renderWhitelistIPs(data) {
    const { ips } = data;

    if (!ips || ips.length === 0) {
        document.getElementById('whitelist-ips').innerHTML = `
            <div class="empty-state">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                </svg>
                <h3>No whitelisted IPs</h3>
                <p>Add IP addresses to allow API access</p>
            </div>
        `;
        return;
    }

    let tableHTML = `
        <table>
            <thead>
                <tr>
                    <th>IP Address</th>
                    <th>Added On</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;

    ips.forEach(ip => {
        tableHTML += `
            <tr>
                <td><code>${ip.whitelisted_ip}</code></td>
                <td>${formatDate(ip.creation)}</td>
                <td>
                    <button class="btn btn-secondary btn-sm" 
                            onclick="deleteWhitelistIP('${ip.name}')">
                        Delete
                    </button>
                </td>
            </tr>
        `;
    });

    tableHTML += `
            </tbody>
        </table>
    `;

    document.getElementById('whitelist-ips').innerHTML = tableHTML;
}

function renderWebhookConfig(data) {
    const html = `
        <form style="padding: 1.5rem;" onsubmit="return saveWebhook(event)">
            <div style="margin-bottom: 1.5rem;">
                <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">Webhook URL</label>
                <input type="text" 
                       id="webhook-url" 
                       value="${data.webhook_url || ''}" 
                       placeholder="https://your-domain.com/webhook"
                       style="width: 100%;">
                <p style="margin-top: 0.5rem; font-size: 0.875rem; color: #6b7280;">
                    Enter the URL where you want to receive transaction notifications
                </p>
            </div>
            
            <button type="submit" class="btn btn-primary">Save Webhook URL</button>
        </form>
    `;

    document.getElementById('webhook-config').innerHTML = html;
}

// Pagination handlers
function loadPage(page) {
    const status = document.getElementById('status-filter')?.value || '';
    const product = document.getElementById('product-filter')?.value || '';
    const fromDate = document.getElementById('from-date-filter')?.value || '';
    const toDate = document.getElementById('to-date-filter')?.value || '';

    let url = `/api/method/iswitch.portal_api.get_merchant_orders?page=${page}&limit=10`;
    if (status) url += '&status=' + status;
    if (product) url += '&product=' + product;
    if (fromDate) url += '&from_date=' + fromDate;
    if (toDate) url += '&to_date=' + toDate;

    htmx.ajax('GET', url, { target: '#transactions-content', swap: 'innerHTML' });
}

function loadLedgerPage(page) {
    htmx.ajax('GET', `/api/method/iswitch.portal_api.get_merchant_ledger?page=${page}&limit=10`, {
        target: '#ledger-content',
        swap: 'innerHTML'
    });
}

function loadVANPage(page) {
    htmx.ajax('GET', `/api/method/iswitch.portal_api.get_merchant_van_logs?page=${page}&limit=10`, {
        target: '#van-content',
        swap: 'innerHTML'
    });
}

// Action handlers
function showAddIPForm() {
    const ip = prompt('Enter IP address to whitelist:');
    if (ip && isValidIP(ip)) {
        frappe.call({
            method: 'iswitch.portal_api.add_whitelist_ip',
            args: { ip_address: ip },
            callback: function (r) {
                if (r.message && r.message.success) {
                    showToast(r.message.message, 'success');
                    htmx.ajax('GET', '/api/method/iswitch.portal_api.get_whitelist_ips', {
                        target: '#whitelist-ips',
                        swap: 'innerHTML'
                    });
                } else {
                    showToast(r.message.error || 'Failed to add IP', 'error');
                }
            }
        });
    } else if (ip) {
        showToast('Invalid IP address format', 'error');
    }
}

function deleteWhitelistIP(ipName) {
    if (confirm('Are you sure you want to remove this IP address?')) {
        frappe.call({
            method: 'iswitch.portal_api.delete_whitelist_ip',
            args: { ip_name: ipName },
            callback: function (r) {
                if (r.message && r.message.success) {
                    showToast(r.message.message, 'success');
                    htmx.ajax('GET', '/api/method/iswitch.portal_api.get_whitelist_ips', {
                        target: '#whitelist-ips',
                        swap: 'innerHTML'
                    });
                } else {
                    showToast(r.message.error || 'Failed to delete IP', 'error');
                }
            }
        });
    }
}

function saveWebhook(event) {
    event.preventDefault();
    const webhookUrl = document.getElementById('webhook-url').value;

    frappe.call({
        method: 'iswitch.portal_api.update_webhook_config',
        args: { webhook_url: webhookUrl },
        callback: function (r) {
            if (r.message && r.message.success) {
                showToast(r.message.message, 'success');
            } else {
                showToast(r.message.error || 'Failed to update webhook', 'error');
            }
        }
    });

    return false;
}
