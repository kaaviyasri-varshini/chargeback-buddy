"""UI theme configuration - dark mode with electric blue accents."""

from nicegui import ui


# Color palette
COLORS = {
    # Primary colors
    "navy": "#0a1929",
    "navy-light": "#132f4c",
    "navy-lighter": "#1e4976",
    
    # Accent colors
    "electric-blue": "#0ea5e9",
    "teal": "#06b6d4",
    "blue-light": "#38bdf8",
    
    # Status colors
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "info": "#3b82f6",
    
    # Neutrals
    "bg-dark": "#0f172a",
    "bg-card": "#1e293b",
    "bg-hover": "#334155",
    "text-primary": "#f1f5f9",
    "text-secondary": "#94a3b8",
    "border": "#334155",
}


def apply_theme():
    """Apply the dark theme with custom styling."""
    
    # Global CSS
    ui.add_head_html("""
    <style>
        /* Root variables */
        :root {
            --color-navy: #0a1929;
            --color-electric-blue: #0ea5e9;
            --color-teal: #06b6d4;
            --color-bg-dark: #0f172a;
            --color-bg-card: #1e293b;
            --color-text: #f1f5f9;
        }
        
        /* Body */
        body {
            background-color: var(--color-bg-dark) !important;
            color: var(--color-text) !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        /* Glassmorphism card */
        .glass-card {
            background: rgba(30, 41, 59, 0.7) !important;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(51, 65, 85, 0.5);
            border-radius: 16px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }
        
        /* Card hover effect */
        .glass-card:hover {
            border-color: var(--color-electric-blue);
            transform: translateY(-2px);
            transition: all 0.3s ease;
        }
        
        /* KPI card */
        .kpi-card {
            background: linear-gradient(135deg, rgba(14, 165, 233, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
            border: 1px solid rgba(14, 165, 233, 0.3);
            border-radius: 12px;
            padding: 24px;
            transition: all 0.3s ease;
        }
        
        .kpi-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 24px rgba(14, 165, 233, 0.2);
        }
        
        /* Status badges */
        .badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .badge-open { background: #3b82f6; color: white; }
        .badge-under-review { background: #f59e0b; color: white; }
        .badge-resolved { background: #10b981; color: white; }
        .badge-waiting { background: #8b5cf6; color: white; }
        
        /* Decision badges */
        .decision-fight { 
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: 700;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
        }
        
        .decision-refund { 
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: 700;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
        }
        
        /* Animated number */
        @keyframes countUp {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .animated-number {
            animation: countUp 0.6s ease-out;
        }
        
        /* Progress bar */
        .win-progress {
            height: 8px;
            border-radius: 4px;
            background: rgba(51, 65, 85, 0.5);
            overflow: hidden;
        }
        
        .win-progress-bar {
            height: 100%;
            border-radius: 4px;
            background: linear-gradient(90deg, #10b981 0%, #059669 100%);
            transition: width 1s ease-out;
        }
        
        /* Sidebar */
        .sidebar {
            background: rgba(15, 23, 42, 0.95);
            border-right: 1px solid rgba(51, 65, 85, 0.5);
        }
        
        /* Nav item */
        .nav-item {
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            margin: 4px 8px;
        }
        
        .nav-item:hover {
            background: rgba(14, 165, 233, 0.1);
            border-left: 3px solid var(--color-electric-blue);
        }
        
        .nav-item.active {
            background: rgba(14, 165, 233, 0.2);
            border-left: 3px solid var(--color-electric-blue);
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--color-bg-dark);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--color-electric-blue);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--color-teal);
        }
    </style>
    """)
    
    # Quasar dark mode
    ui.dark_mode().enable()


# Utility classes
GLASS_CARD = "glass-card p-6"
KPI_CARD = "kpi-card"
