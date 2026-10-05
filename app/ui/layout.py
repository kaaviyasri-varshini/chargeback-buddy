"""Main layout with navigation and header."""

from contextlib import contextmanager

from nicegui import ui


@contextmanager
def create_layout():
    """Create the main layout with sidebar navigation."""
    
    with ui.header().classes('bg-gradient-to-r from-blue-900 to-blue-700 shadow-lg'):
        with ui.row().classes('w-full items-center justify-between px-6 py-3'):
            # Logo and title
            with ui.row().classes('items-center gap-3'):
                ui.label('💼').classes('text-4xl')
                ui.label('ChargeBack Buddy').classes('text-2xl font-bold')
            
            # Status indicators
            with ui.row().classes('items-center gap-4'):
                ui.badge('DEMO', color='purple').props('floating')
                ui.icon('psychology', size='sm').classes('text-teal-400').tooltip('AI Agent Active')
                ui.icon('database', size='sm').classes('text-green-400').tooltip('MongoDB Connected')
    
    with ui.left_drawer(value=True).classes('sidebar'):
        with ui.column().classes('gap-2 p-4'):
            ui.label('Navigation').classes('text-xs text-gray-400 uppercase font-bold px-4 mb-2')
            
            # Dashboard
            with ui.row().classes('nav-item items-center gap-3').on('click', lambda: ui.navigate.to('/')):
                ui.icon('dashboard', size='sm').classes('text-blue-400')
                ui.label('Dashboard').classes('font-semibold')
            
            # Inbox
            with ui.row().classes('nav-item items-center gap-3').on('click', lambda: ui.navigate.to('/inbox')):
                ui.icon('inbox', size='sm').classes('text-teal-400')
                ui.label('Disputes Inbox').classes('font-semibold')
            
            # Detail (disabled for now)
            with ui.row().classes('nav-item items-center gap-3 opacity-50'):
                ui.icon('description', size='sm').classes('text-yellow-400')
                ui.label('Dispute Detail').classes('font-semibold')
            
            # Audit Log (disabled for now)
            with ui.row().classes('nav-item items-center gap-3 opacity-50'):
                ui.icon('history', size='sm').classes('text-purple-400')
                ui.label('Audit Log').classes('font-semibold')
            
            ui.separator().classes('my-4')
            
            # Settings
            with ui.row().classes('nav-item items-center gap-3').on('click', lambda: ui.navigate.to('/settings')):
                ui.icon('settings', size='sm').classes('text-gray-400')
                ui.label('Settings').classes('font-semibold')
            
            ui.space()
            
            # Footer
            with ui.column().classes('mt-auto p-4'):
                ui.separator().classes('mb-4')
                with ui.row().classes('items-center gap-2 text-xs text-gray-500'):
                    ui.icon('info', size='xs')
                    ui.label('PayPal AI Hackathon')
                ui.label('v1.0.0').classes('text-xs text-gray-600')
    
    # Main content area
    with ui.column().classes('w-full p-6 gap-6'):
        yield
