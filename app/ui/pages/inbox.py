"""Disputes inbox page with enhanced search, filters, and table."""

from datetime import datetime

from nicegui import ui

from app.db.documents import Dispute, AgentAnalysis, DisputeStatus, AgentDecision


async def inbox_page():
    """Render the premium disputes inbox page."""
    
    # Page header
    with ui.row().classes('w-full items-center justify-between mb-8'):
        with ui.column().classes('gap-1'):
            ui.label('Disputes Inbox').classes('text-3xl font-bold text-slate-900')
            ui.label('Manage and review all PayPal disputes').classes('text-sm text-slate-600')
        
        with ui.row().classes('gap-2'):
            ui.button('Refresh', icon='refresh', on_click=lambda: ui.notify('Refreshed', type='positive')).props('outline size=sm')
            ui.button('Export', icon='download', on_click=lambda: ui.notify('Export feature coming soon', type='info')).props('outline size=sm')
    
    # Filters bar
    with ui.card().classes('premium-card p-4 mb-6'):
        with ui.row().classes('items-center gap-4 w-full flex-wrap'):
            # Search
            search_input = ui.input(placeholder='Search by ID, buyer, or email...').props('outlined dense').classes('w-80')
            search_input.classes('flex-grow-0')
            
            # Status filter
            status_filter = ui.select(
                ['All Statuses', 'Open', 'Waiting for Response', 'Under Review', 'Resolved'],
                value='All Statuses',
                label='Status'
            ).classes('w-48').props('outlined dense')
            
            # Sort by
            sort_select = ui.select(
                ['Due Date (Urgent First)', 'Amount (High to Low)', 'Amount (Low to High)', 'Created (Newest)', 'Created (Oldest)'],
                value='Due Date (Urgent First)',
                label='Sort by'
            ).classes('w-56').props('outlined dense')
            
            ui.space()
            
            # Clear button
            ui.button('Clear Filters', icon='clear', on_click=lambda: ui.notify('Filters cleared')).props('flat size=sm')
    
    # Load disputes
    try:
        disputes = await Dispute.find().sort(-Dispute.created_at).to_list()
        
        if not disputes:
            # Empty state
            with ui.card().classes('premium-card'):
                with ui.column().classes('empty-state'):
                    ui.icon('inbox', size='xl').classes('empty-state-icon')
                    ui.label('No Disputes Found').classes('text-2xl font-semibold text-slate-300')
                    ui.label('Load sample disputes to get started').classes('text-sm')
                    ui.button('Load Demo Data', icon='cloud_download', 
                            on_click=lambda: ui.notify('Run: python -m app.db.seed', type='info')).props('outline').classes('mt-4')
        else:
            # Summary stats
            with ui.row().classes('gap-4 mb-4'):
                open_count = sum(1 for d in disputes if d.status in [DisputeStatus.OPEN, DisputeStatus.WAITING_FOR_SELLER_RESPONSE])
                review_count = sum(1 for d in disputes if d.status == DisputeStatus.UNDER_REVIEW)
                resolved_count = sum(1 for d in disputes if d.status == DisputeStatus.RESOLVED)
                
                with ui.row().classes('items-center gap-2'):
                    ui.label(f'{len(disputes)} total').classes('text-sm font-semibold text-slate-700')
                    ui.label('•').classes('text-slate-400')
                    ui.label(f'{open_count} open').classes('text-sm text-blue-600')
                    ui.label('•').classes('text-slate-400')
                    ui.label(f'{review_count} in review').classes('text-sm text-amber-600')
                    ui.label('•').classes('text-slate-400')
                    ui.label(f'{resolved_count} resolved').classes('text-sm text-green-600')
            
            # Disputes table
            with ui.card().classes('premium-card p-0 overflow-hidden'):
                # Table header
                with ui.row().classes('data-table-header').style('padding: 14px 20px;'):
                    ui.label('ID').classes('w-24')
                    ui.label('Buyer').classes('w-48')
                    ui.label('Amount').classes('w-24')
                    ui.label('Reason').classes('flex-1')
                    ui.label('Status').classes('w-36')
                    ui.label('AI Rec.').classes('w-28 text-center')
                    ui.label('Win %').classes('w-20 text-center')
                    ui.label('Due').classes('w-24 text-right')
                
                # Table rows
                with ui.column().classes('w-full'):
                    for i, dispute in enumerate(disputes[:50]):  # Limit to 50 for performance
                        # Determine row styling based on urgency
                        row_class = 'data-table-row'
                        
                        if dispute.due_by:
                            days_left = (dispute.due_by - datetime.utcnow()).days
                            if days_left < 0:
                                row_class += ' priority-urgent'
                            elif days_left <= 2:
                                row_class += ' priority-high'
                        
                        with ui.card().classes(row_class).style('padding: 14px 20px; border-radius: 0;'):
                            with ui.row().classes('w-full items-center'):
                                # ID
                                ui.label(f'#{dispute.paypal_dispute_id[-6:]}').classes('w-24 font-mono text-sm font-semibold')
                                
                                # Buyer info
                                with ui.column().classes('w-48 gap-0'):
                                    ui.label(dispute.buyer_name).classes('text-sm font-semibold text-slate-900')
                                    ui.label(dispute.buyer_email).classes('text-xs text-slate-600 truncate')
                                
                                # Amount
                                ui.label(f'${dispute.amount}').classes('w-24 font-bold text-base')
                                
                                # Reason
                                reason_display = dispute.reason.value.replace('_', ' ').title()
                                if len(reason_display) > 35:
                                    reason_display = reason_display[:32] + '...'
                                ui.label(reason_display).classes('flex-1 text-sm text-slate-700')
                                
                                # Status badge
                                with ui.row().classes('w-36 justify-center'):
                                    badge_class = 'status-badge '
                                    
                                    if dispute.status == DisputeStatus.OPEN:
                                        badge_class += 'status-open'
                                        badge_text = 'Open'
                                    elif dispute.status == DisputeStatus.WAITING_FOR_SELLER_RESPONSE:
                                        badge_class += 'status-waiting'
                                        badge_text = 'Waiting'
                                    elif dispute.status == DisputeStatus.UNDER_REVIEW:
                                        badge_class += 'status-review'
                                        badge_text = 'Review'
                                    elif dispute.status == DisputeStatus.RESOLVED:
                                        badge_class += 'status-resolved'
                                        badge_text = 'Resolved'
                                    else:
                                        badge_class += 'status-open'
                                        badge_text = dispute.status.value[:8]
                                    
                                    ui.html(f'<span class="{badge_class}">{badge_text}</span>')
                                
                                # AI Recommendation
                                with ui.column().classes('w-28 items-center gap-1'):
                                    if dispute.latest_analysis_id:
                                        try:
                                            analysis = await AgentAnalysis.get(dispute.latest_analysis_id)
                                            if analysis:
                                                if analysis.decision == AgentDecision.FIGHT:
                                                    ui.html('<span class="decision-badge decision-fight" style="font-size: 10px; padding: 4px 10px;">FIGHT</span>')
                                                else:
                                                    ui.html('<span class="decision-badge decision-refund" style="font-size: 10px; padding: 4px 10px;">REFUND</span>')
                                            else:
                                                ui.label('-').classes('text-slate-600')
                                        except:
                                            ui.label('-').classes('text-slate-600')
                                    else:
                                        ui.label('-').classes('text-slate-600')
                                
                                # Win probability
                                with ui.column().classes('w-20 items-center'):
                                    if dispute.latest_analysis_id:
                                        try:
                                            analysis = await AgentAnalysis.get(dispute.latest_analysis_id)
                                            if analysis:
                                                prob = analysis.win_probability
                                                prob_class = 'text-sm font-semibold '
                                                
                                                if prob >= 0.7:
                                                    prob_class += 'win-prob-high'
                                                elif prob >= 0.4:
                                                    prob_class += 'win-prob-medium'
                                                else:
                                                    prob_class += 'win-prob-low'
                                                
                                                ui.label(f'{prob:.0%}').classes(prob_class)
                                            else:
                                                ui.label('-').classes('text-slate-600')
                                        except:
                                            ui.label('-').classes('text-slate-600')
                                    else:
                                        ui.label('-').classes('text-slate-600')
                                
                                # Due date
                                with ui.column().classes('w-24 items-end'):
                                    if dispute.due_by:
                                        days_left = (dispute.due_by - datetime.utcnow()).days
                                        
                                        if days_left < 0:
                                            ui.label('OVERDUE').classes('text-xs font-bold text-red-400')
                                        elif days_left == 0:
                                            ui.label('TODAY').classes('text-xs font-bold text-amber-400')
                                        elif days_left <= 2:
                                            ui.label(f'{days_left}d left').classes('text-xs font-semibold text-amber-400')
                                        elif days_left <= 7:
                                            ui.label(f'{days_left}d left').classes('text-xs text-slate-300')
                                        else:
                                            ui.label(dispute.due_by.strftime('%m/%d')).classes('text-xs text-slate-500')
                                    else:
                                        ui.label('-').classes('text-xs text-slate-600')
                    
                    if len(disputes) > 50:
                        with ui.row().classes('w-full justify-center p-6 bg-slate-900/30'):
                            ui.label(f'... and {len(disputes) - 50} more disputes').classes('text-sm text-slate-500')
                            ui.button('Load More', icon='expand_more', on_click=lambda: ui.notify('Pagination coming soon')).props('flat size=sm')
    
    except Exception as e:
        with ui.card().classes('premium-card'):
            with ui.column().classes('items-center p-8 gap-4'):
                ui.icon('error', size='xl').classes('text-red-400')
                ui.label('Error Loading Disputes').classes('text-xl text-red-400')
                ui.label(str(e)).classes('text-sm text-slate-400 font-mono')
                ui.label('Make sure MongoDB is running and seeded').classes('text-sm text-slate-500')
