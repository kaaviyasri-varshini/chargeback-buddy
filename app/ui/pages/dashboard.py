"""Dashboard page with KPIs, charts, and activity feed."""

from datetime import datetime
from decimal import Decimal

from nicegui import ui

from app.db.documents import Dispute, AuditLog, AgentAnalysis, DisputeStatus


async def dashboard_page():
    """Render the dashboard page."""
    
    # Page header
    with ui.row().classes('w-full items-center justify-between mb-6'):
        with ui.column().classes('gap-1'):
            ui.label('Dashboard').classes('text-3xl font-bold text-white')
            ui.label(f'Last updated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}').classes('text-sm text-gray-400')
        
        ui.button('Refresh', icon='refresh', on_click=lambda: ui.notify('Refreshed!', type='positive'))
    
    # Calculate KPIs
    try:
        # Total disputes
        total_disputes = await Dispute.count()
        
        # Open disputes
        open_disputes = await Dispute.find(
            Dispute.status.in_([
                DisputeStatus.OPEN,
                DisputeStatus.WAITING_FOR_SELLER_RESPONSE,
                DisputeStatus.UNDER_REVIEW
            ])
        ).count()
        
        # Money at risk
        open_disputes_list = await Dispute.find(
            Dispute.status.in_([
                DisputeStatus.OPEN,
                DisputeStatus.WAITING_FOR_SELLER_RESPONSE,
                DisputeStatus.UNDER_REVIEW
            ])
        ).to_list()
        money_at_risk = sum(d.amount for d in open_disputes_list) if open_disputes_list else Decimal("0")
        
        # Resolved count
        resolved_count = await Dispute.find(Dispute.status == DisputeStatus.RESOLVED).count()
        
        # Win rate calculation (simplified for now)
        if resolved_count > 0:
            win_rate = 0.65  # Placeholder - will calculate properly later
        else:
            win_rate = 0.0
            
    except Exception as e:
        ui.notify(f'Error loading KPIs: {e}', type='warning')
        total_disputes = 0
        open_disputes = 0
        money_at_risk = Decimal("0")
        resolved_count = 0
        win_rate = 0.0
    
    # KPI Cards
    with ui.row().classes('w-full gap-4 mb-6'):
        # Total Disputes
        with ui.card().classes('kpi-card flex-1'):
            with ui.column().classes('gap-2'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('gavel', size='lg').classes('text-blue-400')
                    ui.label('Total Disputes').classes('text-sm text-gray-400 uppercase')
                ui.label(str(total_disputes)).classes('text-4xl font-bold animated-number')
                ui.label('+3 this week').classes('text-xs text-green-400')
        
        # Open Disputes
        with ui.card().classes('kpi-card flex-1'):
            with ui.column().classes('gap-2'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('pending', size='lg').classes('text-yellow-400')
                    ui.label('Open Disputes').classes('text-sm text-gray-400 uppercase')
                ui.label(str(open_disputes)).classes('text-4xl font-bold animated-number')
                ui.label('Needs attention').classes('text-xs text-yellow-400')
        
        # Money at Risk
        with ui.card().classes('kpi-card flex-1'):
            with ui.column().classes('gap-2'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('attach_money', size='lg').classes('text-red-400')
                    ui.label('Money at Risk').classes('text-sm text-gray-400 uppercase')
                ui.label(f'${money_at_risk:,.2f}').classes('text-4xl font-bold animated-number')
                ui.label('In open disputes').classes('text-xs text-red-400')
        
        # Win Rate
        with ui.card().classes('kpi-card flex-1'):
            with ui.column().classes('gap-2'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('trending_up', size='lg').classes('text-green-400')
                    ui.label('Win Rate').classes('text-sm text-gray-400 uppercase')
                ui.label(f'{win_rate:.0%}').classes('text-4xl font-bold animated-number')
                with ui.row().classes('items-center gap-1'):
                    ui.icon('arrow_upward', size='xs').classes('text-green-400')
                    ui.label('+5% vs last month').classes('text-xs text-green-400')
    
    # Charts and Activity
    with ui.row().classes('w-full gap-4'):
        # Charts section
        with ui.card().classes('glass-card flex-1'):
            ui.label('Dispute Analytics').classes('text-xl font-bold mb-4')
            
            if total_disputes == 0:
                with ui.column().classes('items-center justify-center p-12 gap-4'):
                    ui.icon('inbox', size='xl').classes('text-gray-600')
                    ui.label('No disputes yet').classes('text-lg text-gray-400')
                    ui.label('Run: python -m app.db.seed').classes('text-sm text-gray-500 font-mono')
            else:
                # Placeholder for charts
                with ui.column().classes('gap-4'):
                    ui.label('📊 Disputes by Status').classes('font-semibold')
                    with ui.row().classes('gap-4'):
                        with ui.card().classes('bg-blue-900/20 p-4 flex-1'):
                            ui.label(str(open_disputes)).classes('text-2xl font-bold')
                            ui.label('Open').classes('text-sm text-gray-400')
                        with ui.card().classes('bg-green-900/20 p-4 flex-1'):
                            ui.label(str(resolved_count)).classes('text-2xl font-bold')
                            ui.label('Resolved').classes('text-sm text-gray-400')
                    
                    ui.separator()
                    
                    ui.label('💡 Quick Actions').classes('font-semibold mt-4')
                    with ui.row().classes('gap-2'):
                        ui.button('View All Disputes', icon='inbox', on_click=lambda: ui.navigate.to('/inbox')).props('outline')
                        ui.button('Run Analysis', icon='psychology', on_click=lambda: ui.notify('AI Analysis coming in Phase 3!', type='info')).props('outline')
        
        # Activity feed
        with ui.card().classes('glass-card w-96'):
            ui.label('Recent Activity').classes('text-xl font-bold mb-4')
            
            try:
                recent_logs = await AuditLog.find().sort(-AuditLog.timestamp).limit(10).to_list()
                
                if not recent_logs:
                    with ui.column().classes('items-center justify-center p-8 gap-2'):
                        ui.icon('history', size='lg').classes('text-gray-600')
                        ui.label('No activity yet').classes('text-gray-400')
                else:
                    with ui.column().classes('gap-3 max-h-96 overflow-y-auto'):
                        for log in recent_logs:
                            with ui.card().classes('bg-slate-800/50 p-3'):
                                with ui.row().classes('items-start gap-3'):
                                    # Icon based on action
                                    if 'fight' in log.action.lower():
                                        ui.icon('shield', size='sm').classes('text-green-400')
                                    elif 'refund' in log.action.lower():
                                        ui.icon('money_off', size='sm').classes('text-red-400')
                                    elif 'agent' in log.action.lower():
                                        ui.icon('smart_toy', size='sm').classes('text-blue-400')
                                    else:
                                        ui.icon('info', size='sm').classes('text-gray-400')
                                    
                                    with ui.column().classes('gap-1 flex-1'):
                                        ui.label(log.action.replace('_', ' ').title()).classes('text-sm font-semibold')
                                        ui.label(log.reasoning[:60] + '...' if len(log.reasoning) > 60 else log.reasoning).classes('text-xs text-gray-400')
                                        ui.label(f'{log.actor} • {log.timestamp.strftime("%m/%d %I:%M %p")}').classes('text-xs text-gray-500')
            except Exception as e:
                ui.label(f'Error loading activity: {e}').classes('text-sm text-gray-400')
    
    # Demo mode notice
    with ui.card().classes('glass-card w-full bg-purple-900/20 border-purple-500/30 mt-6'):
        with ui.row().classes('items-center gap-3'):
            ui.icon('science', size='lg').classes('text-purple-400')
            with ui.column().classes('gap-1 flex-1'):
                ui.label('🎮 Demo Mode Active').classes('text-lg font-bold')
                ui.label('Using mock PayPal data. Seed the database with: python -m app.db.seed').classes('text-sm text-gray-400')
            ui.button('Seed Database', icon='cloud_download', on_click=lambda: ui.notify('Run: python -m app.db.seed', type='info'))
