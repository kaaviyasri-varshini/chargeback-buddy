# ChargeBack Buddy

An AI-powered PayPal dispute management system that helps small online sellers make data-driven decisions on whether to fight or refund disputes.

## 🏗️ Architecture

ChargeBack Buddy uses:
- **MongoDB + Beanie ODM** for data persistence with change streams for live updates
- **NiceGUI** (FastAPI/Starlette) for a rich, modern Python-based UI
- **Google Gemini** for AI-powered dispute analysis
- **PayPal Disputes API** for webhook handling and evidence submission

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- MongoDB (local via Homebrew or Docker, or MongoDB Atlas free tier)
- Google AI Studio API key (free at [aistudio.google.com](https://aistudio.google.com/app/apikey))
- PayPal Sandbox credentials (optional for demo mode)

### Installation

1. **Clone and setup environment:**

**Using Miniconda/Conda:**
```bash
cd chargeback-buddy
conda create -n chargeback python=3.11 -y
conda activate chargeback
pip install -r requirements.txt
```

**Or using venv:**
```bash
cd chargeback-buddy
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment variables:**

```bash
cp .env.example .env
# Edit .env with your credentials
```

**Get your free Gemini API key:**
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy and paste into `.env` as `GEMINI_API_KEY=your_key_here`

**Recommended models:**
- `gemini-2.0-flash-exp` - Fastest, best for real-time analysis (default)
- `gemini-1.5-pro` - More reasoning power, slightly slower
- `gemini-1.5-flash` - Good balance of speed and quality

3. **Start MongoDB (local development):**

```bash
docker compose up -d
```

This starts MongoDB as a single-node replica set, enabling change streams for live updates.

**MongoDB Atlas Setup (Alternative):**

1. Create a free M0 cluster at [cloud.mongodb.com](https://cloud.mongodb.com)
2. Get your connection string
3. Set `MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/` in `.env`

4. **Seed the database:**

```bash
python -m app.db.seed
```

Or to reset existing data:

```bash
python -m app.db.seed --reset
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_expected_value.py -v

# Run with coverage
pytest --cov=app tests/
```

## 📊 Database Schema

### Collections

**disputes:**
- Core dispute information
- Indexed on: `paypal_dispute_id` (unique), `status`, `due_by`, `created_at`
- Embedded evidence items with strength scores

**dispute_events:**
- Webhook events and timeline entries
- Indexed on: `event_id` (unique), `dispute_id`, `received_at`
- Used for idempotent event processing

**agent_analyses:**
- AI agent recommendations and reasoning
- Indexed on: `dispute_id`, `created_at`
- Contains expected value calculations and drafted responses

**audit_logs:**
- Complete audit trail of all actions
- Indexed on: `dispute_id`, `timestamp`
- Tracks both agent and human decisions

### Dashboard Aggregation Pipelines

The dashboard uses MongoDB aggregation pipelines for real-time KPIs:

**Total Money at Risk:**
```javascript
db.disputes.aggregate([
  { $match: { status: { $in: ["OPEN", "WAITING_FOR_SELLER_RESPONSE", "UNDER_REVIEW"] } } },
  { $group: { _id: null, total: { $sum: "$amount" } } }
])
```

**Win Rate:**
```javascript
db.disputes.aggregate([
  { $match: { status: "RESOLVED", seller_response_submitted: true } },
  { $lookup: { from: "agent_analyses", localField: "latest_analysis_id", foreignField: "_id", as: "analysis" } },
  { $unwind: "$analysis" },
  { $group: {
      _id: "$analysis.decision",
      count: { $sum: 1 }
  }}
])
```

**Disputes Over Time:**
```javascript
db.disputes.aggregate([
  { $group: {
      _id: { $dateTrunc: { date: "$created_at", unit: "day" } },
      count: { $sum: 1 }
  }},
  { $sort: { _id: 1 } }
])
```

## 🧪 Phase 1 Complete: Models & Database

### What's Implemented

✅ MongoDB connection with Beanie ODM  
✅ Document models: Dispute, DisputeEvent, AgentAnalysis, AuditLog  
✅ Database indexes for efficient queries  
✅ Seed script with 20 realistic mock disputes  
✅ Expected value calculation logic  
✅ Unit tests for EV edge cases  
✅ Integration tests for document models  

### Verification Steps

1. **Check MongoDB is running:**
```bash
docker compose ps
# Should show mongodb container running
```

2. **Test database connection:**
```bash
python -c "import asyncio; from app.db.connection import init_db, close_db; asyncio.run(init_db()); print('✅ Connected'); asyncio.run(close_db())"
```

3. **Seed the database:**
```bash
python -m app.db.seed
# Should output: ✅ Successfully seeded 20 disputes
```

4. **Verify data in MongoDB:**
```bash
# Using mongosh
docker exec -it chargeback-buddy-mongo mongosh

use chargeback_buddy
db.disputes.countDocuments()  // Should return 20
db.agent_analyses.countDocuments()  // Should return 20
db.audit_logs.countDocuments()  // Should return 40 (2 per dispute)

# Sample a dispute
db.disputes.findOne()
```

5. **Run tests:**
```bash
pytest tests/test_expected_value.py -v
pytest tests/test_documents.py -v
```

Expected output:
```
tests/test_expected_value.py::TestExpectedValueLogic::test_high_win_probability_fight_recommended PASSED
tests/test_expected_value.py::TestExpectedValueLogic::test_low_win_probability_refund_recommended PASSED
tests/test_expected_value.py::TestExpectedValueLogic::test_low_amount_refund_preferred PASSED
tests/test_expected_value.py::TestExpectedValueLogic::test_amount_equal_to_fighting_cost PASSED
tests/test_expected_value.py::TestExpectedValueLogic::test_win_probability_near_zero PASSED
tests/test_expected_value.py::TestExpectedValueLogic::test_win_probability_near_one PASSED
tests/test_expected_value.py::TestExpectedValueLogic::test_breakeven_point PASSED
tests/test_documents.py::test_create_dispute PASSED
tests/test_documents.py::test_dispute_unique_paypal_id PASSED
tests/test_documents.py::test_create_agent_analysis PASSED
tests/test_documents.py::test_create_dispute_event PASSED
tests/test_documents.py::test_create_audit_log PASSED
tests/test_documents.py::test_dispute_indexes PASSED
```

## 🔄 Expected Value Logic

The agent uses the following decision logic:

```python
refund_loss = amount
fight_expected_loss = (1 - win_probability) * amount + fighting_cost

# Recommend FIGHT only if the expected win value exceeds costs plus buffer
recommend_fight = (win_probability * amount) > (fighting_cost + risk_buffer)
```

**Default Settings:**
- `fighting_cost`: $25 (time, resources, risk to seller metrics)
- `risk_buffer`: $10 (safety margin for uncertainty)

**Examples:**

| Amount | Win Prob | Fight EL | Refund Loss | Decision | Reason |
|--------|----------|----------|-------------|----------|--------|
| $100 | 90% | $35 | $100 | FIGHT | $90 win value > $35 cost |
| $100 | 20% | $105 | $100 | REFUND | $20 win value < $35 cost |
| $15 | 70% | $29.50 | $15 | REFUND | $10.50 win value < $35 cost |
| $200 | 5% | $215 | $200 | REFUND | $10 win value < $35 cost |

## 📝 Next Steps

- [ ] Phase 2: Mock PayPal client for demo mode
- [ ] Phase 3: AI agent with Anthropic
- [ ] Phase 4: Services layer (dispute, scoring, audit)
- [ ] Phase 5: UI theme and layout
- [ ] Phase 6: Rich UI pages (dashboard, inbox, detail)
- [ ] Phase 7: Real PayPal API integration
- [ ] Phase 8: Additional tests
- [ ] Phase 9: Demo script and final polish

## 📄 License

MIT License - Built for PayPal AI Hackathon
