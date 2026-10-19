#!/bin/bash
# Quick run script for ChargeBack Buddy

echo "🚀 ChargeBack Buddy Launcher"
echo ""

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "❌ Conda not found. Please install Miniconda."
    exit 1
fi

# Detect conda environment
ENV_NAME="py12"  # Change this if your env has a different name

echo "📦 Activating conda environment: $ENV_NAME"
eval "$(conda shell.bash hook)"
conda activate $ENV_NAME

# Check if dependencies are installed
if ! python -c "import beanie" 2>/dev/null; then
    echo "⚠️  Dependencies not found. Installing..."
    pip install -r requirements.txt
fi

# Check if database is seeded
echo ""
echo "🌱 Checking database..."
python -c "import asyncio; from app.db import Dispute; from app.db.connection import init_db, close_db; async def check(): await init_db(); count = await Dispute.count(); await close_db(); return count; count = asyncio.run(check()); print(f'Found {count} disputes'); exit(0 if count > 0 else 1)" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "⚠️  Database is empty. Seeding..."
    python -m app.db.seed
    echo ""
fi

echo "🎉 Starting ChargeBack Buddy..."
echo "🌐 Open: http://localhost:8080"
echo ""
python app.py
