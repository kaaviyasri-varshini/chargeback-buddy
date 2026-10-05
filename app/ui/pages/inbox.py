"""Disputes inbox page with filterable table."""

from datetime import datetime

from nicegui import ui

from app.db.documents import Dispute, AgentAnalysis, DisputeStatus, AgentDecision


async def inbox_page():
    """Render the disputes inbox page."""
    
    # Page header
    with ui.row().classes('w-full items-center justify-between mb-6'):
        ui.label('Disputes Inbox').classes('text-3xl font-bold text-white')
        with ui.row().classes('gap-2'):
            ui.button('Refresh', icon='refresh', on_click=lambda: ui.notify('Refreshed!', type='positive'))
            ui.button('Simulate Dispute', icon='add_circle', on_click=lambda: ui.notify('Demo dispute simulation coming soon!', type='info')).props('outline')
    
    # Filters
    with ui.card().classes('glass-card w-full mb-4'):
        with ui.row().classes('items-center gap-4 w-full'):
            ui.label('Filters:').classes('font-semibold')
            
            status_filter = ui.select(
                ['All', 'Open', 'Waiting for Response', 'Under Review', 'Resolved'],
                value='All',
                label='Status'
            ).classes('w-48')
            
            ui.input(placeholder='Search...', ).props('outlined dense').classes('flex-1')
            
            ui.button('Clear', icon='clear', on_click=lambda: ui.notify('Filters cleared')).props('flat')
    
    # Load disputes
    try:
        disputes = await Dispute.find().sort(-Dispute.created_at).to_list()
        
        if not disputes:
            # Empty state
            with ui.card().classes('glass-card w-full'):
                with ui.column().classes('items-center justify-center p-16 gap-4'):
                    ui.icon('inbox', size='xl').classes('text-gray-600 text-6xl')
                    ui.label('No disputes found').classes('text-2xl text-gray-400')
                    ui.label('Seed the database to see disputes').classes('text-gray-500')
                    ui.button('Run: python -m app.db.seed', icon='play_arrow', on_click=lambda: ui.notify('Run this in terminal', type='info'))
        else:
            # Disputes table
            with ui.card().classes('glass-card w-full'):
                ui.label(f'Showing {len(disputes)} disputes').classes('text-sm text-gray-400 mb-4')
                
                # Table headers
                with ui.row().classes('w-full bg-slate-800 p-3 rounded-t-lg font-semibold text-sm'):
                    ui.label('ID').classes('w-32')
                    ui.label('Buyer').classes('w-48')
                    ui.label('Amount').classes('w-24')
                    ui.label('Reason').classes('flex-1')
                    ui.label('Status').classes('w-40')
                    ui.label('Recommendation').classes('w-32')
                    ui.label('Due By').classes('w-32')
                    ui.label('Actions').classes('w-24')
                
                # Table rows
                with ui.column().classes('w-full gap-1'):
                    for dispute in disputes[:20]:  # Limit to 20 for performance
                        with ui.card().classes('bg-slate-800/30 hover:bg-slate-800/50 p-3 cursor-pointer transition-all'):
                            with ui.row().classes('w-full items-center'):
                                # ID
                                ui.label(dispute.paypal_dispute_id[-8:]).classes('w-32 font-mono text-sm')
                                
                                # Buyer
                                with ui.column().classes('w-48 gap-0'):
                                    ui.label(dispute.buyer_name).classes('text-sm font-semibold')
                                    ui.label(dispute.buyer_email).classes('text-xs text-gray-500')
                                
                                # Amount
                                ui.label(f'${dispute.amount}').classes('w-24 font-bold')
                                
                                # Reason
                                reason_short = dispute.reason.value.replace('_', ' ').title()
                                if len(reason_short) > 30:
                                    reason_short = reason_short[:27] + '...'
                                ui.label(reason_short).classes('flex-1 text-sm')
                                
                                # Status badge
                                with ui.row().classes('w-40'):
                                    if dispute.status == DisputeStatus.OPEN:
                                        ui.badge('Open', color='blue')
                                    elif dispute.status == DisputeStatus.WAITING_FOR_SELLER_RESPONSE:
                                        ui.badge('Waiting', color='purple')
                                    elif dispute.status == DisputeStatus.UNDER_REVIEW:
                                        ui.badge('Review', color='orange')
                                    elif dispute.status == DisputeStatus.RESOLVED:
                                        ui.badge('Resolved', color='green')
                                    else:
                                        ui.badge(dispute.status.value, color='gray')
                                
                                # Recommendation
                                if dispute.latest_analysis_id:
                                    try:
                                        analysis = await AgentAnalysis.get(dispute.latest_analysis_id)
                                        if analysis:
                                            if analysis.decision == AgentDecision.FIGHT:
                                                ui.badge('FIGHT', color='green').classes('decision-fight')
                                            else:
                                                ui.badge('REFUND', color='red').classes('decision-refund')
                                            
                                            # Win probability
                                            ui.label(f'{analysis.win_probability:.0%}').classes('text-xs text-gray-400 ml-2')
                                        else:
                                            ui.label('-').classes('w-32 text-gray-500')
                                    except:
                                        ui.label('-').classes('w-32 text-gray-500')
                                else:
                                    ui.label('-').classes('w-32 text-gray-500')
                                
                                # Due date
                                if dispute.due_by:
                                    days_left = (dispute.due_by - datetime.utcnow()).days
                                    if days_left < 0:
                                        ui.label('OVERDUE').classes('w-32 text-red-400 font-bold text-xs')
                                    elif days_left == 0:
                                        ui.label('Today!').classes('w-32 text-yellow-400 font-bold text-xs')
                                    elif days_left <= 3:
                                        ui.label(f'{days_left}d left').classes('w-32 text-orange-400 text-xs')
                                    else:
                                        ui.label(f'{days_left}d left').classes('w-32 text-gray-400 text-xs')
                                else:
                                    ui.label('-').classes('w-32 text-gray-500 text-xs')
                                
                                # Actions
                                with ui.row().classes('w-24 gap-1'):
                                    ui.button(icon='visibility', on_click=lambda: ui.notify('Detail view coming soon!')).props('flat dense round size=sm')
                    
                    if len(disputes) > 20:
                        ui.label(f'... and {len(disputes) - 20} more').classes('text-center text-gray-500 py-4')
    
    except Exception as e:
        with ui.card().classes('glass-card w-full'):
            with ui.column().classes('items-center p-8 gap-4'):
                ui.icon('error', size='xl').classes('text-red-400')
                ui.label(f'Error loading disputes: {e}').classes('text-red-400')
                ui.label('Make sure MongoDB is running and seeded').classes('text-gray-500')
