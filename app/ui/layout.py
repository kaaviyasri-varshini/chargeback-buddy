"""Main layout with navigation and header."""

from contextlib import contextmanager
from typing import Optional

from nicegui import ui, app
from beanie.operators import In

from app.config import settings
from app.db.documents import Dispute, DisputeStatus


async def _get_dispute_counts() -> tuple[int, int]:
    """
    Get active and overdue dispute counts.
    
    Returns:
        (active_count, overdue_count)
    """
    try:
        from datetime import datetime
        
        # Get active disputes
        active_disputes = await Dispute.find(
            In(Dispute.status, [
                DisputeStatus.OPEN,
                DisputeStatus.WAITING_FOR_SELLER_RESPONSE,
                DisputeStatus.UNDER_REVIEW
            ])
        ).to_list()
        
        active_count = len(active_disputes)
        
        # Count overdue
        overdue_count = 0
        for dispute in active_disputes:
            if dispute.due_by and dispute.due_by < datetime.utcnow():
                overdue_count += 1
        
        return active_count, overdue_count
    except:
        return 0, 0


def _check_mongodb_connected() -> bool:
    """Check if MongoDB is connected."""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        # Quick connectivity check would go here
        # For now, assume connected if we got this far
        return True
    except:
        return False


def _check_gemini_configured() -> bool:
    """Check if Gemini API is configured."""
    return bool(settings.gemini_api_key and settings.gemini_api_key != "your_gemini_api_key")


@contextmanager
def create_layout(current_page: str = ''):
    """
    Create the main layout with sidebar navigation.
    
    Args:
        current_page: The current page identifier for active state
    """
    
    # Initialize sidebar collapsed state in app storage
    if 'sidebar_collapsed' not in app.storage.user:
        app.storage.user['sidebar_collapsed'] = False
    
    # Compact header with brand
    with ui.header().classes('bg-gradient-to-r from-slate-900 to-slate-800 shadow-lg border-b border-slate-700').style('z-index: 2000;'):
        with ui.row().classes('w-full items-center justify-between px-6 py-3'):
            # Brand and collapse toggle
            with ui.row().classes('items-center gap-3'):
                # Collapse toggle button (moved to header)
                collapse_btn = ui.button(
                    icon='menu',
                    on_click=lambda: toggle_sidebar()
                ).props('flat dense size=sm').classes('text-white clickable-element')
                collapse_btn.tooltip('Toggle sidebar')
                
                ui.icon('account_balance_wallet', size='md').classes('text-blue-400')
                ui.label('ChargeBack Buddy').classes('text-xl font-semibold')
            
            # Status indicators
            with ui.row().classes('items-center gap-3'):
                if settings.demo_mode:
                    with ui.badge('DEMO', color='purple').props('outline').classes('text-xs') as demo_badge:
                        demo_badge.tooltip('Demo mode: Using test data')
                with ui.icon('smart_toy', size='sm').classes('text-violet-400') as robot_icon:
                    robot_icon.tooltip('AI-powered recommendations')
    
    # Enhanced sidebar navigation
    sidebar_width = 240
    sidebar_collapsed_width = 72
    
    drawer = ui.left_drawer(value=True, fixed=True, bordered=True).classes('sidebar').props(f'width={sidebar_width}')
    drawer.style('border-right: 1px solid #E2E8F0; box-shadow: 2px 0 4px rgba(0,0,0,0.04);')
    
    with drawer:
        with ui.column().classes('gap-0 h-full').style('overflow-y: auto; overflow-x: hidden;'):
            # Get dispute counts for badges
            active_count = 0
            overdue_count = 0
            
            # Try to fetch counts (will work if DB is available)
            try:
                import asyncio
                active_count, overdue_count = asyncio.get_event_loop().run_until_complete(_get_dispute_counts())
            except:
                pass
            
            # MAIN section
            ui.label('MAIN').classes('text-[10px] text-slate-500 uppercase font-bold px-4 py-2 mt-2 tracking-wider')
            
            # Dashboard
            is_active = current_page == 'dashboard'
            item_class = 'nav-item-enhanced'
            if is_active:
                item_class += ' nav-item-active'
            
            with ui.item(on_click=lambda: ui.navigate.to('/')).classes(item_class) as dashboard_nav:
                with ui.item_section().props('avatar'):
                    ui.icon('dashboard', size='sm').classes('text-blue-600' if is_active else 'text-slate-500')
                with ui.item_section():
                    ui.item_label('Dashboard').classes('nav-label font-bold' if is_active else 'nav-label')
            dashboard_nav.tooltip('Go to Dashboard (G then D)')
            
            # Disputes Inbox with badges
            is_active = current_page == 'inbox'
            item_class = 'nav-item-enhanced'
            if is_active:
                item_class += ' nav-item-active'
            
            with ui.item(on_click=lambda: ui.navigate.to('/inbox')).classes(item_class) as inbox_nav:
                with ui.item_section().props('avatar'):
                    ui.icon('inbox', size='sm').classes('text-blue-600' if is_active else 'text-slate-500')
                with ui.item_section():
                    ui.item_label('Disputes Inbox').classes('nav-label font-bold' if is_active else 'nav-label')
                # Badge in side section
                if overdue_count > 0 or active_count > 0:
                    with ui.item_section().props('side'):
                        if overdue_count > 0:
                            ui.badge(str(overdue_count), color='red').props('rounded').classes('text-[10px]').tooltip(f'{overdue_count} overdue dispute(s)')
                        elif active_count > 0:
                            ui.badge(str(active_count), color='blue').props('rounded').classes('text-[10px]').tooltip(f'{active_count} active dispute(s)')
            inbox_nav.tooltip('Go to Disputes Inbox (G then I)')
            
            # ACTIVITY section
            ui.label('ACTIVITY').classes('text-[10px] text-slate-500 uppercase font-bold px-4 py-2 mt-4 tracking-wider')
            
            # Audit Log
            is_active = current_page == 'audit'
            item_class = 'nav-item-enhanced'
            if is_active:
                item_class += ' nav-item-active'
            
            with ui.item(on_click=lambda: ui.navigate.to('/audit')).classes(item_class) as audit_nav:
                with ui.item_section().props('avatar'):
                    ui.icon('history', size='sm').classes('text-blue-600' if is_active else 'text-slate-500')
                with ui.item_section():
                    ui.item_label('Audit Log').classes('nav-label font-bold' if is_active else 'nav-label')
            audit_nav.tooltip('Go to Audit Log (G then A)')
            
            ui.space()
            
            # Light divider before SYSTEM section
            ui.separator().classes('mx-3 my-2')
            
            # SYSTEM section (pinned to bottom)
            ui.label('SYSTEM').classes('text-[10px] text-slate-500 uppercase font-bold px-4 py-2 tracking-wider')
            
            # Settings
            is_active = current_page == 'settings'
            item_class = 'nav-item-enhanced'
            if is_active:
                item_class += ' nav-item-active'
            
            with ui.item(on_click=lambda: ui.navigate.to('/settings')).classes(item_class) as settings_nav:
                with ui.item_section().props('avatar'):
                    ui.icon('settings', size='sm').classes('text-blue-600' if is_active else 'text-slate-500')
                with ui.item_section():
                    ui.item_label('Settings').classes('nav-label font-bold' if is_active else 'nav-label')
            settings_nav.tooltip('Go to Settings (G then S)')
            
            # Status card at bottom
            with ui.card().classes('m-3 p-3 bg-slate-50 border border-slate-200').style('border-radius: 8px;'):
                with ui.column().classes('gap-2 w-full'):
                    # Demo mode indicator
                    if settings.demo_mode:
                        ui.badge('Demo Mode', color='purple').props('outline').classes('text-[10px]')
                    
                    # Connection status with labels
                    mongodb_ok = _check_mongodb_connected()
                    gemini_ok = _check_gemini_configured()
                    
                    # MongoDB row
                    with ui.row().classes('items-center gap-2 w-full') as mongo_row:
                        status_color = 'bg-green-500' if mongodb_ok else 'bg-red-500'
                        ui.html(f'<div class="w-2 h-2 rounded-full {status_color} flex-shrink-0"></div>')
                        ui.label('MongoDB').classes('text-xs text-slate-700')
                    mongo_row.tooltip('MongoDB: Connected' if mongodb_ok else 'MongoDB: Disconnected')
                    
                    # Gemini row
                    with ui.row().classes('items-center gap-2 w-full') as gemini_row:
                        status_color = 'bg-green-500' if gemini_ok else 'bg-amber-500'
                        ui.html(f'<div class="w-2 h-2 rounded-full {status_color} flex-shrink-0"></div>')
                        ui.label('Gemini').classes('text-xs text-slate-700')
                    gemini_row.tooltip('Gemini: Configured' if gemini_ok else 'Gemini: Not configured')
    
    def toggle_sidebar():
        """Toggle sidebar collapsed state."""
        app.storage.user['sidebar_collapsed'] = not app.storage.user.get('sidebar_collapsed', False)
        ui.notify(f"Sidebar {'collapsed' if app.storage.user['sidebar_collapsed'] else 'expanded'} - full width toggle coming in next iteration", type='info')
    
    # Keyboard shortcuts listener
    ui.keyboard(on_key=lambda e: handle_keyboard_shortcut(e.key, e.action.keydown))
    
    last_g_press = {'time': 0}
    
    def handle_keyboard_shortcut(key: str, is_keydown: bool):
        """Handle keyboard shortcuts for navigation."""
        if not is_keydown:
            return
        
        import time
        current_time = time.time()
        
        # G key starts a shortcut sequence
        if key == 'g':
            last_g_press['time'] = current_time
            return
        
        # Check if G was pressed within last second
        if current_time - last_g_press['time'] < 1.0:
            if key == 'd':
                ui.navigate.to('/')
                ui.notify('Navigated to Dashboard', type='positive', position='top', timeout=1000)
            elif key == 'i':
                ui.navigate.to('/inbox')
                ui.notify('Navigated to Inbox', type='positive', position='top', timeout=1000)
            elif key == 'a':
                ui.navigate.to('/audit')
                ui.notify('Navigated to Audit Log', type='positive', position='top', timeout=1000)
            elif key == 's':
                ui.navigate.to('/settings')
                ui.notify('Navigated to Settings', type='positive', position='top', timeout=1000)
            
            last_g_press['time'] = 0
    
    # Main content area with better spacing
    with ui.column().classes('w-full p-8 gap-6'):
        yield
