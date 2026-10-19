"""UI theme configuration - premium fintech SaaS dark mode."""

from nicegui import ui


# Premium fintech color palette
COLORS = {
    # Sidebar & backgrounds
    "sidebar": "#0B1220",
    "main-bg": "#F5F7FB",
    "page-bg": "#0F172A",
    "card-bg": "#FFFFFF",
    
    # Primary colors
    "primary-blue": "#2563EB",
    "ai-violet": "#8B5CF6",
    "success": "#16A34A",
    "warning": "#D97706",
    "error": "#DC2626",
    
    # Text
    "text-primary": "#0F172A",
    "text-secondary": "#64748B",
    "text-white": "#FFFFFF",
    
    # Borders & neutrals
    "border": "#E2E8F0",
    "border-dark": "#334155",
    "slate-800": "#1E293B",
    "slate-700": "#334155",
}


def apply_theme():
    """Apply premium fintech SaaS theme with custom styling."""
    
    # Global CSS
    ui.add_head_html("""
    <style>
        /* Root variables */
        :root {
            --sidebar-bg: #0B1220;
            --page-bg: #0F172A;
            --card-bg: #1E293B;
            --primary-blue: #2563EB;
            --ai-violet: #8B5CF6;
            --success: #16A34A;
            --warning: #D97706;
            --error: #DC2626;
            --text-primary: #F1F5F9;
            --text-secondary: #94A3B8;
            --border: #E2E8F0;
            --border-dark: #334155;
        }
        
        /* Body and typography */
        body {
            background-color: var(--page-bg) !important;
            color: var(--text-primary) !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Helvetica Neue', Arial, sans-serif;
            font-size: 14px;
            line-height: 1.6;
        }
        
        /* Premium card styling */
        .premium-card {
            background: var(--card-bg) !important;
            border: 1px solid var(--border-dark);
            border-radius: 12px;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.3);
            transition: all 0.2s ease;
        }
        
        .premium-card:hover {
            box-shadow: 0 4px 12px 0 rgba(0, 0, 0, 0.4);
        }
        
        /* Glass card for overlays */
        .glass-card {
            background: rgba(30, 41, 59, 0.85) !important;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(148, 163, 184, 0.1);
            border-radius: 12px;
            box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.25);
        }
        
        /* KPI cards */
        .kpi-card {
            background: var(--card-bg) !important;
            border: 1px solid var(--border-dark);
            border-radius: 14px;
            padding: 20px;
            transition: all 0.25s ease;
            position: relative;
            overflow: hidden;
        }
        
        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--primary-blue), var(--ai-violet));
            opacity: 0;
            transition: opacity 0.25s ease;
        }
        
        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px 0 rgba(37, 99, 235, 0.15);
            border-color: var(--primary-blue);
        }
        
        .kpi-card:hover::before {
            opacity: 1;
        }
        
        /* Status badges - refined */
        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .status-open {
            background: rgba(37, 99, 235, 0.15);
            color: #60A5FA;
            border: 1px solid rgba(37, 99, 235, 0.3);
        }
        
        .status-waiting {
            background: rgba(139, 92, 246, 0.15);
            color: #A78BFA;
            border: 1px solid rgba(139, 92, 246, 0.3);
        }
        
        .status-review {
            background: rgba(217, 119, 6, 0.15);
            color: #FBBF24;
            border: 1px solid rgba(217, 119, 6, 0.3);
        }
        
        .status-resolved {
            background: rgba(22, 163, 74, 0.15);
            color: #4ADE80;
            border: 1px solid rgba(22, 163, 74, 0.3);
        }
        
        /* Decision badges */
        .decision-badge {
            display: inline-flex;
            align-items: center;
            padding: 6px 14px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        
        .decision-fight {
            background: linear-gradient(135deg, #16A34A 0%, #15803D 100%);
            color: white;
            box-shadow: 0 2px 8px rgba(22, 163, 74, 0.3);
        }
        
        .decision-refund {
            background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%);
            color: white;
            box-shadow: 0 2px 8px rgba(220, 38, 38, 0.3);
        }
        
        /* Sidebar navigation */
        .sidebar {
            background: var(--sidebar-bg) !important;
            border-right: 1px solid var(--border-dark);
        }
        
        .nav-item {
            display: flex;
            align-items: center;
            padding: 10px 16px;
            margin: 2px 8px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.15s ease;
            color: var(--text-secondary);
            font-size: 14px;
            font-weight: 500;
        }
        
        .nav-item:hover {
            background: rgba(37, 99, 235, 0.1);
            color: var(--text-primary);
        }
        
        .nav-item.active {
            background: rgba(37, 99, 235, 0.15);
            color: #60A5FA;
            border-left: 3px solid var(--primary-blue);
        }
        
        /* Tables */
        .data-table-header {
            background: rgba(30, 41, 59, 0.5);
            border-bottom: 1px solid var(--border-dark);
            padding: 12px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary);
        }
        
        .data-table-row {
            background: rgba(30, 41, 59, 0.3);
            border-bottom: 1px solid rgba(51, 65, 85, 0.3);
            padding: 14px 12px;
            transition: all 0.15s ease;
            cursor: pointer;
        }
        
        .data-table-row:hover {
            background: rgba(37, 99, 235, 0.1);
            border-left: 2px solid var(--primary-blue);
        }
        
        /* Animations */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .animate-fade-in-up {
            animation: fadeInUp 0.4s ease-out;
        }
        
        @keyframes pulse {
            0%, 100% {
                opacity: 1;
            }
            50% {
                opacity: 0.7;
            }
        }
        
        .animate-pulse {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        
        /* Progress bars */
        .progress-container {
            height: 6px;
            background: rgba(51, 65, 85, 0.5);
            border-radius: 3px;
            overflow: hidden;
        }
        
        .progress-bar {
            height: 100%;
            border-radius: 3px;
            transition: width 0.6s ease;
        }
        
        .progress-success {
            background: linear-gradient(90deg, var(--success), #15803D);
        }
        
        .progress-warning {
            background: linear-gradient(90deg, var(--warning), #B45309);
        }
        
        .progress-error {
            background: linear-gradient(90deg, var(--error), #B91C1C);
        }
        
        /* Empty states */
        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 64px 32px;
            text-align: center;
            color: var(--text-secondary);
        }
        
        .empty-state-icon {
            font-size: 48px;
            opacity: 0.4;
            margin-bottom: 16px;
        }
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--page-bg);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--border-dark);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--primary-blue);
        }
        
        /* Input and form styling */
        .q-field--outlined .q-field__control {
            border-radius: 8px;
        }
        
        /* Button refinements */
        .q-btn {
            border-radius: 8px;
            font-weight: 500;
            text-transform: none;
            letter-spacing: 0.3px;
        }
        
        /* Tooltip styling */
        .q-tooltip {
            background: rgba(15, 23, 42, 0.95);
            border: 1px solid var(--border-dark);
            border-radius: 6px;
            font-size: 12px;
            padding: 6px 10px;
        }
        
        /* Demo mode indicator */
        .demo-indicator {
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(139, 92, 246, 0.05));
            border: 1px solid rgba(139, 92, 246, 0.3);
            border-radius: 12px;
            padding: 16px;
        }
        
        /* Win probability indicator */
        .win-prob-high {
            color: var(--success);
            font-weight: 600;
        }
        
        .win-prob-medium {
            color: var(--warning);
            font-weight: 600;
        }
        
        .win-prob-low {
            color: var(--error);
            font-weight: 600;
        }
        
        /* Priority indicators */
        .priority-urgent {
            border-left: 4px solid var(--error);
        }
        
        .priority-high {
            border-left: 4px solid var(--warning);
        }
        
        .priority-normal {
            border-left: 4px solid var(--primary-blue);
        }
    </style>
    """)
    
    # Enable dark mode
    ui.dark_mode().enable()


# Utility classes
PREMIUM_CARD = "premium-card"
GLASS_CARD = "glass-card"
KPI_CARD = "kpi-card"
