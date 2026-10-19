"""Settings page with grouped configuration sections."""

from nicegui import ui
from app.config import settings


async def settings_page():
    """Render the premium settings page."""
    
    # Page header
    with ui.row().classes('w-full items-center justify-between mb-8'):
        with ui.column().classes('gap-1'):
            ui.label('Settings').classes('text-3xl font-bold')
            ui.label('Configure database, AI, and application settings').classes('text-sm text-slate-400')
        
        ui.button('Reload Config', icon='refresh', on_click=lambda: ui.notify('Config reloaded', type='positive')).props('outline size=sm')
    
    # Layout: Two columns
    with ui.row().classes('w-full gap-6'):
        # Left column
        with ui.column().classes('flex-1 gap-6'):
            # Database Configuration
            with ui.card().classes('premium-card p-6'):
                with ui.row().classes('items-center gap-3 mb-4'):
                    ui.icon('storage', size='md').classes('text-green-400')
                    ui.label('Database Configuration').classes('text-xl font-semibold')
                
                with ui.column().classes('gap-4'):
                    # Connection status
                    with ui.row().classes('items-center justify-between p-3 rounded-lg bg-slate-800/50'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('check_circle', size='sm').classes('text-green-400')
                            ui.label('MongoDB').classes('font-semibold')
                        ui.badge('CONNECTED', color='green').props('outline')
                    
                    ui.separator()
                    
                    # Configuration details
                    with ui.column().classes('gap-3'):
                        with ui.row().classes('items-start gap-2'):
                            ui.label('URI:').classes('text-xs text-slate-500 uppercase tracking-wide font-semibold w-20')
                            ui.label(settings.mongodb_uri).classes('text-sm font-mono text-slate-300 flex-1 break-all')
                        
                        with ui.row().classes('items-start gap-2'):
                            ui.label('Database:').classes('text-xs text-slate-500 uppercase tracking-wide font-semibold w-20')
                            ui.label(settings.mongodb_db_name).classes('text-sm font-mono text-slate-300')
            
            # AI Configuration
            with ui.card().classes('premium-card p-6'):
                with ui.row().classes('items-center gap-3 mb-4'):
                    ui.icon('smart_toy', size='md').classes('text-violet-400')
                    ui.label('AI Configuration').classes('text-xl font-semibold')
                
                with ui.column().classes('gap-4'):
                    # Provider
                    with ui.row().classes('items-center justify-between p-3 rounded-lg bg-slate-800/50'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('psychology', size='sm').classes('text-violet-400')
                            ui.label('Google Gemini').classes('font-semibold')
                        
                        if settings.gemini_api_key and settings.gemini_api_key != "your_gemini_api_key":
                            ui.badge('API KEY SET', color='green').props('outline')
                        else:
                            ui.badge('NOT CONFIGURED', color='orange').props('outline')
                    
                    ui.separator()
                    
                    # Model details
                    with ui.column().classes('gap-3'):
                        with ui.row().classes('items-start gap-2'):
                            ui.label('Model:').classes('text-xs text-slate-500 uppercase tracking-wide font-semibold w-20')
                            ui.label(settings.ai_model).classes('text-sm font-mono text-slate-300')
                        
                        with ui.row().classes('items-start gap-2'):
                            ui.label('API Key:').classes('text-xs text-slate-500 uppercase tracking-wide font-semibold w-20')
                            if settings.gemini_api_key and settings.gemini_api_key != "your_gemini_api_key":
                                masked_key = settings.gemini_api_key[:10] + '•' * 20 + settings.gemini_api_key[-4:]
                                ui.label(masked_key).classes('text-sm font-mono text-slate-300')
                            else:
                                ui.label('Not configured').classes('text-sm text-slate-500 italic')
                    
                    # Help link
                    if not settings.gemini_api_key or settings.gemini_api_key == "your_gemini_api_key":
                        with ui.row().classes('items-center gap-2 p-3 rounded-lg bg-amber-900/20 border border-amber-700/30'):
                            ui.icon('info', size='sm').classes('text-amber-400')
                            with ui.column().classes('gap-1 flex-1'):
                                ui.label('API key required for AI features').classes('text-sm font-semibold text-amber-300')
                                ui.link('Get your free key at Google AI Studio', 'https://aistudio.google.com/app/apikey', new_tab=True).classes('text-xs text-blue-400')
            
            # PayPal Integration
            with ui.card().classes('premium-card p-6'):
                with ui.row().classes('items-center gap-3 mb-4'):
                    ui.icon('payment', size='md').classes('text-blue-400')
                    ui.label('PayPal Integration').classes('text-xl font-semibold')
                
                with ui.column().classes('gap-4'):
                    # Environment
                    with ui.row().classes('items-center justify-between p-3 rounded-lg bg-slate-800/50'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('science', size='sm').classes('text-blue-400')
                            ui.label('Sandbox API').classes('font-semibold')
                        
                        if settings.paypal_client_id and settings.paypal_client_id != "your_sandbox_client_id":
                            ui.badge('CONFIGURED', color='green').props('outline')
                        else:
                            ui.badge('NOT CONFIGURED', color='orange').props('outline')
                    
                    ui.separator()
                    
                    # Configuration details
                    with ui.column().classes('gap-3'):
                        with ui.row().classes('items-start gap-2'):
                            ui.label('Base URL:').classes('text-xs text-slate-500 uppercase tracking-wide font-semibold w-24')
                            ui.label(settings.paypal_base_url).classes('text-sm font-mono text-slate-300 flex-1 break-all')
                        
                        with ui.row().classes('items-start gap-2'):
                            ui.label('Client ID:').classes('text-xs text-slate-500 uppercase tracking-wide font-semibold w-24')
                            if settings.paypal_client_id and settings.paypal_client_id != "your_sandbox_client_id":
                                masked_id = settings.paypal_client_id[:12] + '•' * 10
                                ui.label(masked_id).classes('text-sm font-mono text-slate-300')
                            else:
                                ui.label('Not configured').classes('text-sm text-slate-500 italic')
                    
                    # Help link
                    if not settings.paypal_client_id or settings.paypal_client_id == "your_sandbox_client_id":
                        with ui.row().classes('items-center gap-2 p-3 rounded-lg bg-amber-900/20 border border-amber-700/30'):
                            ui.icon('info', size='sm').classes('text-amber-400')
                            with ui.column().classes('gap-1 flex-1'):
                                ui.label('Credentials required for PayPal API access').classes('text-sm font-semibold text-amber-300')
                                ui.link('Get sandbox credentials', 'https://developer.paypal.com', new_tab=True).classes('text-xs text-blue-400')
        
        # Right column
        with ui.column().classes('flex-1 gap-6'):
            # Application Settings
            with ui.card().classes('premium-card p-6'):
                with ui.row().classes('items-center gap-3 mb-4'):
                    ui.icon('tune', size='md').classes('text-slate-400')
                    ui.label('Application Settings').classes('text-xl font-semibold')
                
                with ui.column().classes('gap-4'):
                    # Demo mode
                    with ui.column().classes('gap-2 p-3 rounded-lg bg-slate-800/50'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('science', size='sm').classes('text-violet-400')
                            ui.label('Demo Mode').classes('font-semibold')
                        ui.label(str(settings.demo_mode)).classes('text-sm text-slate-300 font-mono')
                        ui.label('Uses mock PayPal data for testing without real API calls').classes('text-xs text-slate-500')
                    
                    ui.separator()
                    
                    # Fighting cost
                    with ui.column().classes('gap-2 p-3 rounded-lg bg-slate-800/50'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('attach_money', size='sm').classes('text-green-400')
                            ui.label('Fighting Cost').classes('font-semibold')
                        ui.label(f'${settings.fighting_cost}').classes('text-sm text-slate-300 font-mono')
                        ui.label('Cost to fight a dispute (time, resources, seller metrics risk)').classes('text-xs text-slate-500')
                    
                    ui.separator()
                    
                    # Risk buffer
                    with ui.column().classes('gap-2 p-3 rounded-lg bg-slate-800/50'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('shield', size='sm').classes('text-amber-400')
                            ui.label('Risk Buffer').classes('font-semibold')
                        ui.label(f'${settings.risk_buffer}').classes('text-sm text-slate-300 font-mono')
                        ui.label('Safety margin for uncertain cases in expected value calculation').classes('text-xs text-slate-500')
            
            # Auto-Approval Settings
            with ui.card().classes('premium-card p-6'):
                with ui.row().classes('items-center gap-3 mb-4'):
                    ui.icon('autopilot', size='md').classes('text-blue-400')
                    ui.label('Auto-Approval').classes('text-xl font-semibold')
                
                with ui.column().classes('gap-4'):
                    # Status
                    with ui.row().classes('items-center justify-between p-3 rounded-lg bg-slate-800/50'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('smart_toy', size='sm').classes('text-blue-400')
                            ui.label('Automatic Decisions').classes('font-semibold')
                        
                        if settings.auto_approve_enabled:
                            ui.badge('ENABLED', color='green').props('outline')
                        else:
                            ui.badge('DISABLED', color='red').props('outline')
                    
                    if settings.auto_approve_enabled:
                        ui.separator()
                        
                        with ui.column().classes('gap-3'):
                            with ui.row().classes('items-start gap-2'):
                                ui.label('Max Amount:').classes('text-xs text-slate-500 uppercase tracking-wide font-semibold w-32')
                                ui.label(f'${settings.auto_approve_max_amount}').classes('text-sm font-mono text-slate-300')
                            
                            with ui.row().classes('items-start gap-2'):
                                ui.label('Min Win Prob:').classes('text-xs text-slate-500 uppercase tracking-wide font-semibold w-32')
                                ui.label(f'{settings.auto_approve_min_win_prob:.0%}').classes('text-sm font-mono text-slate-300')
                            
                            ui.label('Disputes meeting these criteria will be auto-approved by the AI agent').classes('text-xs text-slate-500 mt-2')
                    else:
                        ui.separator()
                        ui.label('All AI decisions require human approval').classes('text-sm text-slate-400 italic')
            
            # System Info
            with ui.card().classes('premium-card p-6'):
                with ui.row().classes('items-center gap-3 mb-4'):
                    ui.icon('info', size='md').classes('text-slate-400')
                    ui.label('System Information').classes('text-xl font-semibold')
                
                with ui.column().classes('gap-3'):
                    with ui.row().classes('items-start gap-2'):
                        ui.label('Host:').classes('text-xs text-slate-500 uppercase tracking-wide font-semibold w-20')
                        ui.label(f'{settings.host}:{settings.port}').classes('text-sm font-mono text-slate-300')
                    
                    with ui.row().classes('items-start gap-2'):
                        ui.label('Version:').classes('text-xs text-slate-500 uppercase tracking-wide font-semibold w-20')
                        ui.label('1.0.0').classes('text-sm font-mono text-slate-300')
    
    # Configuration note
    with ui.card().classes('demo-indicator w-full mt-6'):
        with ui.row().classes('items-center gap-4'):
            ui.icon('settings_suggest', size='lg').classes('text-blue-400')
            with ui.column().classes('gap-1 flex-1'):
                ui.label('Configuration Management').classes('text-lg font-semibold')
                ui.label('Settings are loaded from the .env file at startup. To modify configuration:').classes('text-sm text-slate-300')
                with ui.column().classes('gap-1 mt-2 font-mono text-xs text-slate-400'):
                    ui.label('1. Edit the .env file in the project root')
                    ui.label('2. Restart the application')
                    ui.label('3. Changes will be reflected here')
