#!/usr/bin/env python3

# Append mobile fixes to portal.css
mobile_css = """

/* ========== MOBILE FIXES ========== */

.sidebar {
    overflow-y: hidden !important;
    z-index: 1000 !important;
}

#mobile-overlay {
    z-index: 998 !important;
}

@media (max-width: 1024px) {
    .table-container {
        overflow-x: auto !important;
    }
    
    table {
        min-width: 600px !important;
    }
}

@media (max-width: 1024px) and (min-width: 481px) {
    .stats-grid {
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 0.625rem !important;
    }
    
    .stat-card {
        padding: 0.75rem !important;
    }
    
    .stat-card-value {
        font-size: 1.375rem !important;
    }
    
    #wallet-balance-header {
        padding: 0.875rem 1.125rem !important;
    }
    
    #wallet-balance-amount {
        font-size: 1.375rem !important;
    }
}

@media (max-width: 768px) {
    #wallet-balance-header {
        padding: 0.75rem 0.875rem !important;
    }
    
    #wallet-balance-amount {
        font-size: 1.125rem !important;
    }
}

@media (max-width: 480px) {
    #wallet-balance-header {
        padding: 0.625rem 0.75rem !important;
    }
    
    #wallet-balance-amount {
        font-size: 1rem !important;
    }
    
    .stat-card-value {
        font-size: 1.25rem !important;
    }
}
"""

with open('/Users/tinkalkumar/Dev/dev-bench/apps/iswitch/iswitch/public/css/portal.css', 'a') as f:
    f.write(mobile_css)

print("Mobile CSS fixes appended successfully!")
