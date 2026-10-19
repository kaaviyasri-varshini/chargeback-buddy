"""Main layout with navigation and header."""

from contextlib import contextmanager

from nicegui import ui

from app.config import settings


@contextmanager
def create_layout(current_page: str = ''):
    """
    Create the main layout with sidebar navigation.
    
    Args:
        current_page: The current page identifier for active state
    """
    
    # Compact header with brand
    with ui.header().classes('bg-gradient-to-r from-slate-900 to-slate-800 shadow-lg border-b border-slate-700'):
        with ui.row().classes('w-full items-center justify-between px-6 py-3'):
            # Brand
            with ui.row().classes('items-center gap-3'):
                ui.icon('account_balance_wallet', size='md').classes('text-blue-400')
                ui.label('ChargeBack Buddy').classes('text-xl font-semibold')
            
            # Status indicators
            with ui.row().classes('items-center gap-3'):
                if settings.demo_mode:
                    ui.badge('DEMO', color='purple').props('outline').classes('text-xs')
                ui.icon('smart_toy', size='sm').classes('text-violet-400').tooltip('AI Powered')
                ui.icon('storage', size='sm').classes('text-green-400').tooltip('Database Connected')
    
    # Sidebar navigation
    with ui.left_drawer(value=True, fixed=False, bordered=True).classes('sidebar').props('width=240'):
        with ui.column().classes('gap-1 p-3 h-full'):
            # Navigation section
            ui.label('NAVIGATION').classes('text-[10px] text-slate-500 uppercase font-bold px-3 py-2 tracking-wider')
            
            # Dashboard
            nav_class = 'nav-item items-center gap-3'
            if current_page == 'dashboard':
                nav_class += ' active'
            with ui.row().classes(nav_class).on('click', lambda: ui.navigate.to('/')):
                ui.icon('dashboard', size='sm')
                ui.label('Dashboard')
            
            # Inbox
            nav_class = 'nav-item items-center gap-3'
            if current_page == 'inbox':
                nav_class += ' active'
            with ui.row().classes(nav_class).on('click', lambda: ui.navigate.to('/inbox')):
                ui.icon('inbox', size='sm')
                ui.label('Disputes Inbox')
            
            # Detail (coming soon)
            with ui.row().classes('nav-item items-center gap-3 opacity-40 cursor-not-allowed'):
                ui.icon('article', size='sm')
                ui.label('Dispute Details')
            
            # Audit Log
            nav_class = 'nav-item items-center gap-3'
            if current_page == 'audit':
                nav_class += ' active'
            with ui.row().classes(nav_class).on('click', lambda: ui.navigate.to('/audit')):
                ui.icon('history', size='sm')
                ui.label('Audit Log')
            
            ui.separator().classes('my-3')
            
            # Settings
            nav_class = 'nav-item items-center gap-3'
            if current_page == 'settings':
                nav_class += ' active'
            with ui.row().classes(nav_class).on('click', lambda: ui.navigate.to('/settings')):
                ui.icon('settings', size='sm')
                ui.label('Settings')
            
            ui.space()
            
            # Footer
            with ui.column().classes('mt-auto p-3 pt-6'):
                ui.separator().classes('mb-3')
                with ui.column().classes('gap-1'):
                    with ui.row().classes('items-center gap-2 text-[11px] text-slate-600'):
                        ui.icon('emoji_events', size='xs')
                        ui.label('PayPal AI Hackathon')
                    ui.label('Version 1.0.0').classes('text-[10px] text-slate-700')
    
    # Main content area with better spacing
    with ui.column().classes('w-full p-8 gap-6'):
        yield
