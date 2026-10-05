#!/bin/bash
# Fix dependency compatibility issues

echo "🔧 Fixing dependency versions..."

# Uninstall problematic packages
pip uninstall -y pymongo motor beanie

# Install with correct versions
pip install pymongo==4.8.0
pip install motor==3.5.1  
pip install beanie==1.26.0

echo "✅ Dependencies fixed!"
echo "Now run: python -m app.db.seed"
