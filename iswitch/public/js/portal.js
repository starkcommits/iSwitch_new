// Portal Dashboard JavaScript Utilities

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2
    }).format(amount || 0);
}

// Format date
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

// Format date only
function formatDateOnly(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(date);
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(err => {
        showToast('Failed to copy', 'error');
    });
}

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                ${type === 'success'
            ? '<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>'
            : '<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>'
        }
            </svg>
            <span>${message}</span>
        </div>
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// HTMX event listeners
document.addEventListener('DOMContentLoaded', function () {
    // Handle HTMX errors
    document.body.addEventListener('htmx:responseError', function (event) {
        showToast('An error occurred. Please try again.', 'error');
    });

    // Handle HTMX success for forms
    document.body.addEventListener('htmx:afterSwap', function (event) {
        if (event.detail.target.hasAttribute('data-success-message')) {
            const message = event.detail.target.getAttribute('data-success-message');
            showToast(message, 'success');
        }

        // Refresh wallet balance when main content is updated
        if (event.detail.target.id === 'main-content') {
            htmx.trigger('body', 'walletBalanceUpdate');
        }
    });

    // Navigation active state
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function () {
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Mobile sidebar toggle
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('open');
        });
    }
});

// Get status badge class
function getStatusBadgeClass(status) {
    const statusMap = {
        'Processed': 'badge-success',
        'Processing': 'badge-warning',
        'Pending': 'badge-warning',
        'Cancelled': 'badge-danger',
        'Failed': 'badge-danger',
        'Reversed': 'badge-danger',
        'Success': 'badge-success',
        'Active': 'badge-success',
        'Inactive': 'badge-danger'
    };
    return statusMap[status] || 'badge-info';
}

// Refresh dashboard stats
function refreshDashboard() {
    htmx.trigger('#dashboard-stats', 'refresh');
    showToast('Dashboard refreshed', 'success');
}

// Export table data
function exportTableData(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;

    let csv = [];
    const rows = table.querySelectorAll('tr');

    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = Array.from(cols).map(col => {
            return '"' + col.textContent.trim().replace(/"/g, '""') + '"';
        });
        csv.push(rowData.join(','));
    });

    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'export.csv';
    a.click();
    window.URL.revokeObjectURL(url);
}

// Format number with commas
function formatNumber(num) {
    return new Intl.NumberFormat('en-IN').format(num || 0);
}

function exportVANLogs() {
    const fromDate = document.querySelector('input[name="from_date"]')?.value || '';
    const toDate = document.querySelector('input[name="to_date"]')?.value || '';

    const queryParams = new URLSearchParams({
        from_date: fromDate,
        to_date: toDate
    });

    window.location.href = `/api/method/iswitch.portal_api.export_merchant_van_logs?${queryParams.toString()}`;
}

function exportOrders() {
    const status = document.querySelector('select[name="status"]')?.value || '';
    const fromDate = document.querySelector('input[name="from_date"]')?.value || '';
    const toDate = document.querySelector('input[name="to_date"]')?.value || '';

    const queryParams = new URLSearchParams({
        status: status,
        from_date: fromDate,
        to_date: toDate
    });

    window.location.href = `/api/method/iswitch.portal_api.export_merchant_orders?${queryParams.toString()}`;
}

function exportLedger() {
    const type = document.querySelector('select[name="transaction_type"]')?.value || '';
    const fromDate = document.querySelector('input[name="from_date"]')?.value || '';
    const toDate = document.querySelector('input[name="to_date"]')?.value || '';

    const queryParams = new URLSearchParams({
        transaction_type: type,
        from_date: fromDate,
        to_date: toDate
    });

    window.location.href = `/api/method/iswitch.portal_api.export_merchant_ledger?${queryParams.toString()}`;
}

// Validate IP address
function isValidIP(ip) {
    const ipPattern = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!ipPattern.test(ip)) return false;

    const parts = ip.split('.');
    return parts.every(part => {
        const num = parseInt(part);
        return num >= 0 && num <= 255;
    });
}

// Handle API key generation
function handleGenerateKeys() {
    if (confirm('Are you sure you want to generate new API keys? This will invalidate your current keys.')) {
        return true;
    }
    return false;
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize tooltips (if needed)
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', function () {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = this.getAttribute('data-tooltip');
            document.body.appendChild(tooltip);

            const rect = this.getBoundingClientRect();
            tooltip.style.position = 'absolute';
            tooltip.style.top = (rect.top - tooltip.offsetHeight - 5) + 'px';
            tooltip.style.left = (rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2)) + 'px';

            this._tooltip = tooltip;
        });

        element.addEventListener('mouseleave', function () {
            if (this._tooltip) {
                this._tooltip.remove();
                this._tooltip = null;
            }
        });
    });
}

// Toggle sidebar for mobile
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('mobile-overlay');
    const menuBtn = document.getElementById('mobile-menu-btn');

    if (sidebar && overlay) {
        const isOpen = sidebar.classList.contains('open');
        
        if (isOpen) {
            // Close sidebar
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
            document.body.classList.remove('sidebar-open');
            document.body.style.overflow = '';
            if (menuBtn) {
                const svg = menuBtn.querySelector('svg');
                if (svg) {
                    svg.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />';
                }
            }
        } else {
            // Open sidebar
            sidebar.classList.add('open');
            overlay.classList.add('active');
            document.body.classList.add('sidebar-open');
            document.body.style.overflow = 'hidden';
            if (menuBtn) {
                const svg = menuBtn.querySelector('svg');
                if (svg) {
                    svg.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />';
                }
            }
        }
    }
}

// Handle responsive adjustments on resize
(function() {
    if (window.resizeHandlerInitialized) return;
    window.resizeHandlerInitialized = true;
    
    var resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            // Close sidebar on resize to desktop if open
            if (window.innerWidth > 768) {
                const sidebar = document.querySelector('.sidebar');
                const overlay = document.getElementById('mobile-overlay');
                if (sidebar && sidebar.classList.contains('open')) {
                    sidebar.classList.remove('open');
                    if (overlay) {
                        overlay.classList.remove('active');
                    }
                    document.body.classList.remove('sidebar-open');
                    document.body.style.overflow = '';
                    
                    // Reset menu button icon
                    const menuBtn = document.getElementById('mobile-menu-btn');
                    if (menuBtn) {
                        const svg = menuBtn.querySelector('svg');
                        if (svg) {
                            svg.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />';
                        }
                    }
                }
            }
        }, 250);
    });
})();

// Close sidebar when clicking nav item on mobile
document.addEventListener('DOMContentLoaded', function () {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function () {
            if (window.innerWidth <= 768) {
                const sidebar = document.querySelector('.sidebar');
                if (sidebar && sidebar.classList.contains('open')) {
                    toggleSidebar();
                }
            }
        });
    });

    // Wrap table in scrollable container, keep pagination fixed
    function setupTableScrolling() {
        if (window.innerWidth <= 768) {
            document.querySelectorAll('.table-container').forEach(container => {
                // Check if already wrapped
                if (container.querySelector('.table-scroll-wrapper')) return;
                
                const table = container.querySelector('table');
                const pagination = container.querySelector('.pagination');
                
                if (table && pagination) {
                    // Create scrollable wrapper
                    const wrapper = document.createElement('div');
                    wrapper.className = 'table-scroll-wrapper';
                    wrapper.style.cssText = 'flex: 1; min-height: 0; overflow-x: auto; overflow-y: auto; -webkit-overflow-scrolling: touch;';
                    
                    // Get all elements between table-header and pagination
                    const tableHeader = container.querySelector('.table-header');
                    const tableFilters = container.querySelector('.table-filters');
                    
                    // Insert wrapper before pagination
                    pagination.parentNode.insertBefore(wrapper, pagination);
                    
                    // Move table and filters into wrapper
                    if (tableFilters) wrapper.appendChild(tableFilters);
                    if (table) wrapper.appendChild(table);
                }
            });
        }
    }

    // Setup on load
    document.addEventListener('DOMContentLoaded', setupTableScrolling);

    // Setup after HTMX swaps
    document.body.addEventListener('htmx:afterSwap', function(event) {
        setTimeout(setupTableScrolling, 100);
    });
});
