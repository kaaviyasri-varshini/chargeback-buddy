# 🚀 Quick Start Guide

## Run the Application

```bash
# 1. Activate your conda environment
conda activate chargeback

# 2. Install dependencies (if not already done)
pip install -r requirements.txt

# 3. Seed the database with demo data
python -m app.db.seed

# 4. Run the application
python app.py
```

## Open in Browser

Visit: **http://localhost:8080**

## What You'll See

- **Dashboard** - KPIs, charts, and activity feed
- **Inbox** - List of all disputes with AI recommendations
- **Settings** - Configuration and status

## Next Steps

1. **Get your Gemini API key** (for AI features in Phase 3):
   - Visit: https://aistudio.google.com/app/apikey
   - Click "Create API Key"
   - Add to `.env`: `GEMINI_API_KEY=your_key_here`

2. **Explore the demo data**:
   - 20 realistic disputes
   - Various statuses and amounts
   - AI analyses with win probabilities
   - Audit trail

3. **Reset data** (if needed):
   ```bash
   python -m app.db.seed --reset
   ```

## Troubleshooting

**MongoDB connection error:**
- Make sure MongoDB is running: `brew services start mongodb-community`
- Or use MongoDB Atlas (free): https://cloud.mongodb.com

**Port 8080 already in use:**
- Edit `.env` and change `PORT=8080` to another port

**Module not found:**
- Make sure you're in the conda environment: `conda activate chargeback`
- Reinstall: `pip install -r requirements.txt`
