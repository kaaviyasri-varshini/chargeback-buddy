"""Settings page for configuration."""

from nicegui import ui
from app.config import settings


async def settings_page():
    """Render the settings page."""
    
    # Page header
    ui.label('Settings').classes('text-3xl font-bold text-white mb-6')
    
    # Configuration sections
    with ui.row().classes('w-full gap-4'):
        # Database settings
        with ui.card().classes('glass-card flex-1'):
            ui.label('Database').classes('text-xl font-bold mb-4')
            
            with ui.column().classes('gap-3'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('database', size='sm').classes('text-green-400')
                    ui.label('MongoDB').classes('font-semibold')
                
                ui.label(f'URI: {settings.mongodb_uri}').classes('text-sm text-gray-400 font-mono')
                ui.label(f'Database: {settings.mongodb_db_name}').classes('text-sm text-gray-400 font-mono')
                
                ui.separator()
                
                with ui.row().classes('items-center gap-2 text-green-400'):
                    ui.icon('check_circle', size='sm')
                    ui.label('Connected').classes('text-sm font-semibold')
        
        # AI settings
        with ui.card().classes('glass-card flex-1'):
            ui.label('AI Configuration').classes('text-xl font-bold mb-4')
            
            with ui.column().classes('gap-3'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('psychology', size='sm').classes('text-blue-400')
                    ui.label('Google Gemini').classes('font-semibold')
                
                ui.label(f'Model: {settings.ai_model}').classes('text-sm text-gray-400 font-mono')
                
                if settings.gemini_api_key and settings.gemini_api_key != "your_gemini_api_key":
                    ui.label(f'API Key: {settings.gemini_api_key[:10]}...').classes('text-sm text-gray-400 font-mono')
                    with ui.row().classes('items-center gap-2 text-green-400 mt-2'):
                        ui.icon('check_circle', size='sm')
                        ui.label('API Key Set').classes('text-sm font-semibold')
                else:
                    with ui.row().classes('items-center gap-2 text-yellow-400 mt-2'):
                        ui.icon('warning', size='sm')
                        ui.label('API Key Not Set').classes('text-sm font-semibold')
                    
                    ui.label('Get your free key at: https://aistudio.google.com/app/apikey').classes('text-xs text-blue-400 mt-2')
    
    # Application settings
    with ui.card().classes('glass-card w-full mt-4'):
        ui.label('Application Settings').classes('text-xl font-bold mb-4')
        
        with ui.grid(columns=2).classes('gap-6 w-full'):
            # Demo mode
            with ui.column().classes('gap-2'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('science', size='sm').classes('text-purple-400')
                    ui.label('Demo Mode').classes('font-semibold')
                ui.label(f'{settings.demo_mode}').classes('text-sm text-gray-400')
                ui.label('Uses mock PayPal data for testing').classes('text-xs text-gray-500')
            
            # Fighting cost
            with ui.column().classes('gap-2'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('attach_money', size='sm').classes('text-green-400')
                    ui.label('Fighting Cost').classes('font-semibold')
                ui.label(f'${settings.fighting_cost}').classes('text-sm text-gray-400')
                ui.label('Cost to fight a dispute (time, resources)').classes('text-xs text-gray-500')
            
            # Risk buffer
            with ui.column().classes('gap-2'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('shield', size='sm').classes('text-orange-400')
                    ui.label('Risk Buffer').classes('font-semibold')
                ui.label(f'${settings.risk_buffer}').classes('text-sm text-gray-400')
                ui.label('Safety margin for uncertain cases').classes('text-xs text-gray-500')
            
            # Auto-approve
            with ui.column().classes('gap-2'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('smart_toy', size='sm').classes('text-blue-400')
                    ui.label('Auto-Approve').classes('font-semibold')
                ui.label(f'{settings.auto_approve_enabled}').classes('text-sm text-gray-400')
                if settings.auto_approve_enabled:
                    ui.label(f'Max: ${settings.auto_approve_max_amount}, Min win: {settings.auto_approve_min_win_prob:.0%}').classes('text-xs text-gray-500')
                else:
                    ui.label('All decisions require human approval').classes('text-xs text-gray-500')
    
    # PayPal settings
    with ui.card().classes('glass-card w-full mt-4'):
        ui.label('PayPal Integration').classes('text-xl font-bold mb-4')
        
        with ui.column().classes('gap-3'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('payment', size='sm').classes('text-blue-600')
                ui.label('Sandbox API').classes('font-semibold')
            
            ui.label(f'Base URL: {settings.paypal_base_url}').classes('text-sm text-gray-400 font-mono')
            
            if settings.paypal_client_id and settings.paypal_client_id != "your_sandbox_client_id":
                ui.label(f'Client ID: {settings.paypal_client_id[:15]}...').classes('text-sm text-gray-400 font-mono')
                with ui.row().classes('items-center gap-2 text-green-400 mt-2'):
                    ui.icon('check_circle', size='sm')
                    ui.label('Credentials Set').classes('text-sm font-semibold')
            else:
                with ui.row().classes('items-center gap-2 text-yellow-400 mt-2'):
                    ui.icon('warning', size='sm')
                    ui.label('Credentials Not Set').classes('text-sm font-semibold')
                
                ui.label('Get sandbox credentials at: https://developer.paypal.com').classes('text-xs text-blue-400 mt-2')
    
    # Info section
    with ui.card().classes('glass-card w-full mt-4 bg-blue-900/20 border-blue-500/30'):
        with ui.row().classes('items-start gap-4'):
            ui.icon('info', size='lg').classes('text-blue-400')
            with ui.column().classes('gap-2 flex-1'):
                ui.label('Configuration').classes('text-lg font-bold')
                ui.label('Settings are loaded from the .env file. To change them:').classes('text-sm text-gray-400')
                with ui.column().classes('gap-1 mt-2 font-mono text-xs text-gray-500'):
                    ui.label('1. Edit /Users/kaaviya/hackathon/chargeback-buddy/.env')
                    ui.label('2. Restart the application')
                    ui.label('3. Changes will be reflected here')
