# PayPal Sandbox Demo Guide

This guide walks you through testing the PayPal integration using PayPal's sandbox environment.

## Prerequisites

1. **PayPal Developer Account**: Sign up at https://developer.paypal.com
2. **Sandbox App Credentials**: Create a REST API app in the sandbox dashboard
3. **MongoDB**: Running locally or accessible
4. **Gemini API Key**: For AI analysis (optional but recommended)

## Setup Steps

### 1. Get PayPal Sandbox Credentials

1. Go to https://developer.paypal.com/dashboard/
2. Click "Apps & Credentials"
3. Switch to "Sandbox" mode
4. Create a new app or use an existing one
5. Copy the **Client ID** and **Secret**

### 2. Configure Environment Variables

Update your `.env` file with the sandbox credentials:

```bash
PAYPAL_CLIENT_ID=your_sandbox_client_id_here
PAYPAL_CLIENT_SECRET=your_sandbox_client_secret_here
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com
PAYPAL_WEBHOOK_ID=your_webhook_id_here  # Optional for demo script
```

### 3. Start MongoDB

```bash
# If using Docker
docker-compose up -d mongodb

# Or start your local MongoDB
mongod --dbpath /path/to/data
```

### 4. Initialize Database

```bash
python -m app.db.seed --reset
```

## Running the Demo

### Option 1: With Real Sandbox Dispute (Recommended)

If you have access to PayPal sandbox and have created a test dispute:

```bash
python scripts/sandbox_demo.py --dispute-id PP-D-XXXXX
```

**Steps to create a sandbox dispute:**
1. Go to PayPal Sandbox: https://www.sandbox.paypal.com
2. Log in with your sandbox buyer account
3. Find a completed transaction
4. Open a dispute for that transaction
5. Copy the dispute ID from the URL or email

### Option 2: Replay Saved Webhook (Fallback)

If you don't have sandbox access, use the fallback mode with mock data:

```bash
python scripts/sandbox_demo.py --replay-webhook
```

This simulates receiving a webhook event and processes it end-to-end.

## What the Demo Does

The demo script demonstrates the complete flow:

1. **📥 Fetch Dispute**: Retrieves dispute details from PayPal API
2. **💾 Store in Database**: Saves dispute to MongoDB
3. **🤖 AI Analysis**: Runs both heuristic and LLM-based analysis
4. **⚔️ Submit Evidence**: If FIGHT is recommended, submits evidence to PayPal

## Expected Output

```
================================================================================
 PayPal Sandbox Dispute Flow Demo
================================================================================

📊 Initializing database connection...
✅ Database connected

📥 Step 1: Fetching dispute PP-D-XXXXX from PayPal sandbox...
✅ Successfully fetched dispute
   - Buyer: Test Buyer
   - Amount: 150.00 USD
   - Reason: MERCHANDISE_OR_SERVICE_NOT_RECEIVED
   - Status: WAITING_FOR_SELLER_RESPONSE

💾 Step 2: Storing dispute in database...
✅ Dispute stored with ID: 507f1f77bcf86cd799439011

🤖 Step 3: Running AI agent analysis...
   This combines heuristic scoring with LLM reasoning...

📊 Analysis Results:
------------------------------------------------------------
   Decision: FIGHT
   Confidence: 90%
   
   Heuristic Win Probability: 75%
   LLM Win Probability: 85%
   Blended Win Probability: 79%
   
   Expected Loss (Fight): $46.50
   Expected Loss (Refund): $150.00

📝 Reasoning:
   • Heuristic scorer: 75% win probability
   • LLM analysis: 85% win probability (high confidence)
   • Blended probability (60% heuristic, 40% LLM): 79%
   • LLM analyzed 3 evidence items
   • Found 2 supporting factors
   • Identified 1 concerning factors
   • Recommended gathering 1 additional pieces of evidence
   • Expected loss if we fight: $46.50
   • Expected loss if we refund: $150.00
   • Strong delivery proof with tracking and signature makes this a winnable case...

⚔️  Step 4: Submitting evidence to PayPal (FIGHT recommended)...
✅ Evidence submitted successfully
   Response: {...}

================================================================================
 Demo Complete!
================================================================================

Summary:
  - Dispute: PP-D-XXXXX
  - Amount: $150.00
  - Recommendation: FIGHT
  - Win Probability: 79%
  - Expected Savings: $103.50
```

## Setting Up Webhooks (Optional)

To test real-time webhook events:

### 1. Expose Local Server

Use ngrok or similar to expose your local server:

```bash
ngrok http 8080
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

### 2. Configure Webhook in PayPal

1. Go to PayPal Developer Dashboard
2. Navigate to your app
3. Click "Add Webhook"
4. Set URL to: `https://abc123.ngrok.io/api/webhooks/paypal/`
5. Subscribe to events:
   - `CUSTOMER.DISPUTE.CREATED`
   - `CUSTOMER.DISPUTE.UPDATED`
6. Copy the Webhook ID and add to `.env`:

```bash
PAYPAL_WEBHOOK_ID=your_webhook_id_here
```

### 3. Test Webhook

1. Start the application: `python app.py`
2. Create a dispute in sandbox
3. Check your app logs for the webhook event
4. Verify the dispute appears in your dashboard

## Troubleshooting

### "Failed to fetch dispute from PayPal"
- Verify your Client ID and Secret are correct
- Check that you're using sandbox credentials with sandbox base URL
- Ensure the dispute ID exists in your sandbox account

### "Invalid signature"
- Make sure PAYPAL_WEBHOOK_ID matches your webhook in the developer dashboard
- Verify the webhook URL is correct
- Check that your ngrok tunnel is still active

### "GEMINI_API_KEY must be set"
- Add your Gemini API key to `.env`
- Or the agent will use heuristic-only analysis (fallback mode)

### Database connection errors
- Ensure MongoDB is running
- Check MONGODB_URI in `.env`
- Verify network connectivity to MongoDB

## Next Steps

After running the demo:

1. View the dispute in the web UI: http://localhost:8080
2. Check the audit logs for the complete decision trail
3. Review the savings calculation on the dashboard
4. Test the "Submit evidence" button in the UI

## Notes

- **Sandbox vs Production**: Never use production credentials for testing
- **Simulated Data**: The demo uses mock evidence if real data isn't available
- **Idempotency**: Webhook events are processed only once by event ID
- **Signature Verification**: Always enabled in production for security
