"""Audit log page with searchable timeline."""

from datetime import datetime

from nicegui import ui

from app.db.documents import AuditLog, Dispute


async def audit_page():
    """Render the audit log page."""
    
    # Page header
    with ui.row().classes('w-full items-center justify-between mb-8'):
        with ui.column().classes('gap-1'):
            ui.label('Audit Log').classes('text-3xl font-bold')
            ui.label('Complete history of all agent actions and human decisions').classes('text-sm text-slate-400')
        
        ui.button('Refresh', icon='refresh', on_click=lambda: ui.notify('Refreshed', type='positive')).props('outline size=sm')
    
    # Filters
    with ui.card().classes('premium-card p-4 mb-6'):
        with ui.row().classes('items-center gap-4 w-full'):
            ui.label('Filters:').classes('font-semibold text-sm')
            
            actor_filter = ui.select(
                ['All', 'Agent', 'Human'],
                value='All',
                label='Actor'
            ).classes('w-40').props('outlined dense')
            
            action_filter = ui.select(
                ['All', 'Analysis', 'Fight', 'Refund', 'Other'],
                value='All',
                label='Action'
            ).classes('w-40').props('outlined dense')
            
            search_input = ui.input(placeholder='Search...').props('outlined dense').classes('flex-1')
            
            ui.button('Clear', icon='clear', on_click=lambda: ui.notify('Filters cleared')).props('flat size=sm')
    
    # Load audit logs
    try:
        logs = await AuditLog.find().sort(-AuditLog.timestamp).to_list()
        
        if not logs:
            # Empty state
            with ui.card().classes('premium-card'):
                with ui.column().classes('empty-state'):
                    ui.icon('history', size='xl').classes('empty-state-icon')
                    ui.label('No Audit Logs Found').classes('text-2xl font-semibold text-slate-300')
                    ui.label('Activity will be logged here as actions are taken').classes('text-sm')
        else:
            # Audit log timeline
            with ui.card().classes('premium-card p-6'):
                ui.label(f'Showing {len(logs)} events').classes('text-sm text-slate-400 mb-4')
                
                with ui.column().classes('gap-3 w-full'):
                    # Group by date
                    current_date = None
                    
                    for log in logs[:100]:  # Limit to 100 for performance
                        log_date = log.timestamp.strftime('%Y-%m-%d')
                        
                        # Date separator
                        if log_date != current_date:
                            current_date = log_date
                            ui.separator().classes('my-2')
                            ui.label(log.timestamp.strftime('%B %d, %Y')).classes('text-sm font-semibold text-slate-400 px-2')
                        
                        # Log entry
                        with ui.card().classes('data-table-row'):
                            with ui.row().classes('items-start gap-4 w-full'):
                                # Time badge
                                with ui.column().classes('items-center gap-0 w-16'):
                                    ui.label(log.timestamp.strftime('%I:%M')).classes('text-xs font-mono font-semibold')
                                    ui.label(log.timestamp.strftime('%p')).classes('text-[10px] text-slate-500')
                                
                                # Icon based on action
                                icon_class = 'text-slate-400'
                                icon_name = 'info'
                                
                                if 'fight' in log.action.lower() or 'approved_fight' in log.action.lower():
                                    icon_name = 'shield'
                                    icon_class = 'text-green-400'
                                elif 'refund' in log.action.lower() or 'approved_refund' in log.action.lower():
                                    icon_name = 'payments'
                                    icon_class = 'text-red-400'
                                elif 'agent' in log.action.lower() or 'analysis' in log.action.lower():
                                    icon_name = 'smart_toy'
                                    icon_class = 'text-violet-400'
                                elif 'created' in log.action.lower():
                                    icon_name = 'add_circle'
                                    icon_class = 'text-blue-400'
                                elif 'updated' in log.action.lower():
                                    icon_name = 'edit'
                                    icon_class = 'text-amber-400'
                                
                                ui.icon(icon_name, size='sm').classes(icon_class)
                                
                                # Content
                                with ui.column().classes('gap-2 flex-1'):
                                    # Action
                                    with ui.row().classes('items-center gap-2'):
                                        ui.label(log.action.replace('_', ' ').title()).classes('text-base font-semibold')
                                        
                                        # Actor badge
                                        if log.actor == 'agent':
                                            ui.badge('AI', color='purple').props('outline').classes('text-xs')
                                        else:
                                            ui.badge(log.actor.upper(), color='blue').props('outline').classes('text-xs')
                                    
                                    # Reasoning
                                    if log.reasoning:
                                        ui.label(log.reasoning).classes('text-sm text-slate-300')
                                    
                                    # Metadata row
                                    with ui.row().classes('items-center gap-3 mt-1'):
                                        # Dispute link
                                        if log.dispute_id:
                                            try:
                                                dispute = await Dispute.get(log.dispute_id)
                                                if dispute:
                                                    ui.label(f'Dispute: {dispute.paypal_dispute_id[-8:]}').classes('text-xs text-slate-500 font-mono')
                                            except:
                                                ui.label(f'Dispute ID: {log.dispute_id[:8]}...').classes('text-xs text-slate-500 font-mono')
                                        
                                        # Approver
                                        if log.approver:
                                            ui.label('•').classes('text-xs text-slate-600')
                                            ui.label(f'Approved by: {log.approver}').classes('text-xs text-slate-500')
                                        
                                        # Metadata
                                        if log.metadata:
                                            ui.label('•').classes('text-xs text-slate-600')
                                            metadata_str = ', '.join([f'{k}: {v}' for k, v in list(log.metadata.items())[:2]])
                                            if len(metadata_str) > 50:
                                                metadata_str = metadata_str[:47] + '...'
                                            ui.label(metadata_str).classes('text-xs text-slate-500')
                    
                    if len(logs) > 100:
                        ui.label(f'... and {len(logs) - 100} more events').classes('text-center text-slate-500 py-4')
    
    except Exception as e:
        with ui.card().classes('premium-card'):
            with ui.column().classes('items-center p-8 gap-4'):
                ui.icon('error', size='xl').classes('text-red-400')
                ui.label(f'Error loading audit logs').classes('text-xl text-red-400')
                ui.label(str(e)).classes('text-sm text-slate-400 font-mono')
