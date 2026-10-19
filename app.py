#!/usr/bin/env python
"""
ChargeBack Buddy - AI-powered PayPal dispute management system.
Run with: python app.py
"""

from nicegui import app, ui

from app.config import settings
from app.db.connection import init_db, close_db, change_streams_available
from app.ui.theme import apply_theme


# Startup event
@app.on_startup
async def startup():
    """Initialize database on startup."""
    print("🚀 Starting ChargeBack Buddy...")
    try:
        await init_db()
        print("✅ Database connected")
        
        if change_streams_available():
            print("✅ Change streams available (live updates enabled)")
        else:
            print("⚠️  Change streams not available (using polling)")
        
        if settings.demo_mode:
            print("🎮 Demo mode enabled")
    except Exception as e:
        print(f"❌ Startup error: {e}")


# Shutdown event
@app.on_shutdown
async def shutdown():
    """Close database connection on shutdown."""
    print("👋 Shutting down...")
    await close_db()


# Apply dark theme
apply_theme()


# Route: Dashboard (home)
@ui.page('/')
async def home():
    from app.ui.layout import create_layout
    from app.ui.pages.dashboard import dashboard_page
    
    with create_layout(current_page='dashboard'):
        await dashboard_page()


# Route: Disputes Inbox
@ui.page('/inbox')
async def inbox():
    from app.ui.layout import create_layout
    from app.ui.pages.inbox import inbox_page
    
    with create_layout(current_page='inbox'):
        await inbox_page()


# Route: Audit Log
@ui.page('/audit')
async def audit():
    from app.ui.layout import create_layout
    from app.ui.pages.audit import audit_page
    
    with create_layout(current_page='audit'):
        await audit_page()


# Route: Settings
@ui.page('/settings')
async def settings_route():
    from app.ui.layout import create_layout
    from app.ui.pages.settings import settings_page
    
    with create_layout(current_page='settings'):
        await settings_page()


if __name__ in {"__main__", "__mp_main__"}:
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║         💼 ChargeBack Buddy - AI Dispute Manager         ║
    ║                                                           ║
    ║  🌐 URL: http://localhost:{settings.port}                        ║
    ║  📊 Database: {settings.mongodb_db_name}                   ║
    ║  🎮 Demo Mode: {settings.demo_mode}                              ║
    ║  🤖 AI Model: {settings.ai_model[:30]}           ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    ui.run(
        title="ChargeBack Buddy",
        host=settings.host,
        port=settings.port,
        reload=False,
        show=True,
        favicon="💼",
    )
