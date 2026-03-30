# 🌐 DONIA PULSE AI — Master Blueprint & Scalability Guide
**DONIA LABS TECH | Version 1.0**

---

## Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [Component Breakdown](#2-component-breakdown)
3. [Deployment Guide](#3-deployment-guide)
4. [Scalability Playbook](#4-scalability-playbook)
5. [Adding New Clients (SOP)](#5-adding-new-clients-sop)
6. [Security Checklist](#6-security-checklist)
7. [Monitoring & Alerting](#7-monitoring--alerting)
8. [Troubleshooting Guide](#8-troubleshooting-guide)
9. [Cost Estimation](#9-cost-estimation)
10. [Roadmap](#10-roadmap)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLIENT END USERS                           │
│              (WhatsApp Business Conversations)                  │
└─────────────────────┬───────────────────────────────────────────┘
                      │ WhatsApp Messages
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│               META CLOUD API (v20.0)                            │
│         (Webhook → Single n8n Endpoint)                         │
└─────────────────────┬───────────────────────────────────────────┘
                      │ POST /webhook/whatsapp-webhook
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    n8n WORKFLOW ENGINE                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Validate │→ │ Firebase │→ │ Safety   │→ │ Lang Detect  │   │
│  │ & Route  │  │ Lookup   │  │ Filter   │  │ AR/FR/EN     │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────┬───────┘   │
│                                                     │           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────┴───────┐   │
│  │  Send    │← │  Format  │← │ GPT-4o   │← │ Build Prompt │   │
│  │ WhatsApp │  │  Reply   │  │   API    │  │ + History    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Read/Write (Real-time)
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│               FIREBASE FIRESTORE (Source of Truth)              │
│   clients/ | conversations/ | system_config/ | audit_logs/      │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Read/Write
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│           STREAMLIT MANAGEMENT DASHBOARD                        │
│   Overview | Client CRUD | Kill Switch | Audit Logs             │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Principles
- **Single Webhook**: One n8n endpoint handles ALL clients. Routing via WABA ID.
- **Zero-Restart Config**: Every request fetches fresh config from Firebase.
- **Stateless n8n**: All state lives in Firebase, not in the workflow.
- **Fail-Safe Design**: Kill switch and subscription checks happen BEFORE AI invocation.

---

## 2. Component Breakdown

### Component 1: Firebase Firestore (The Brain)
| Collection | Purpose | Access |
|------------|---------|--------|
| `clients` | All client configs, tokens, AI settings | Admin SDK (server) |
| `conversations` | Per-user chat history for context | Admin SDK |
| `system_config` | Global settings, master kill switch | Admin SDK |
| `audit_logs` | Immutable admin action log | Admin SDK (write-only) |
| `alerts` | Subscription expiry notification queue | Admin SDK |

**Why Firebase?**
- Real-time updates (no cache invalidation needed)
- Scales to millions of documents with no schema changes
- Free tier handles 100+ clients comfortably
- Built-in security rules

### Component 2: n8n Workflow (The Engine)
The master workflow processes every WhatsApp message through these stages:

1. **Webhook Entry** → Receives raw Meta payload
2. **Validate & Extract** → Normalizes payload, extracts WABA ID
3. **Firebase Lookup** → Fetches client config by WABA ID (real-time)
4. **Guard Layer** → Kill switch, subscription expiry, maintenance mode
5. **Safety Filter** → Blocks politics, religion, adult content, custom words
6. **Language Detection** → Auto-detects AR/FR/EN or uses manual override
7. **History Fetch** → Retrieves last 10 messages for context
8. **Prompt Builder** → Constructs system prompt with brand voice + language rule
9. **OpenAI GPT-4o** → Generates response
10. **WhatsApp Send** → Delivers reply via Meta Cloud API
11. **Firebase Save** → Persists conversation history + updates analytics

**Parallel CRON Workflow** (runs every 6 hours):
- Fetches all active clients
- Filters those expiring within 48 hours with `alert_sent = false`
- Sends email alerts
- Marks `alert_sent = true` to prevent duplicate alerts

### Component 3: Streamlit Dashboard (The Control Room)
| Page | Features |
|------|---------|
| Overview | KPI cards, charts, expiry timeline |
| Clients | Search, filter, per-client actions |
| Add Client | Full onboarding form → Firebase |
| Security | Global kill switch, audit logs |

---

## 3. Deployment Guide

### Prerequisites
```bash
# Infrastructure Required
- n8n instance (self-hosted on VPS or n8n.cloud)
- Firebase project (Blaze plan recommended for production)
- OpenAI API key
- Meta Business Account (WhatsApp Business API)
- Python 3.10+ for Dashboard
- Domain + SSL for n8n webhook (required by Meta)
```

### Step 1: Firebase Setup
```bash
# 1. Create Firebase project at console.firebase.google.com
# 2. Enable Firestore Database (Native mode)
# 3. Create Service Account:
#    Project Settings → Service Accounts → Generate New Private Key
# 4. Save JSON as: firebase-service-account.json
# 5. Deploy security rules from firebase_schema.json
```

### Step 2: n8n Setup
```bash
# Environment variables to set in n8n:
FIREBASE_PROJECT_ID=your-project-id
OPENAI_API_KEY=sk-...
N8N_WEBHOOK_BASE_URL=https://your-n8n-domain.com

# Import workflow:
# n8n UI → Workflows → Import → paste n8n_master_workflow.json

# Configure credentials:
# - Google Firebase (Service Account JSON)
# - SMTP for email alerts
```

### Step 3: Dashboard Setup
```bash
# Install dependencies
pip install streamlit firebase-admin pandas plotly requests python-dotenv

# Create .env file
cat > .env << EOF
FIREBASE_CREDENTIALS_PATH=./firebase-service-account.json
FIREBASE_PROJECT_ID=your-project-id
ADMIN_PASSWORD=your_very_secure_password_here
EOF

# Run dashboard
streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0

# For production (with authentication proxy):
# Use nginx reverse proxy with basic auth in front of streamlit
```

### Step 4: Meta Webhook Configuration
```
Meta Business Manager → WhatsApp → Configuration → Webhook:
  Callback URL: https://your-n8n-domain.com/webhook/whatsapp-webhook
  Verify Token:  (set same value as in Firebase client config)
  Subscribe to: messages, message_status
```

### Step 5: DNS & SSL
```nginx
# nginx config (example)
server {
    listen 443 ssl;
    server_name n8n.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:5678;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 443 ssl;
    server_name dashboard.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 4. Scalability Playbook

### Current Capacity (Single n8n Instance)
| Metric | Value |
|--------|-------|
| Concurrent clients | 100–500 |
| Messages/minute | ~200 (limited by OpenAI rate limits) |
| Firebase reads/day | 50,000 (free tier) |
| Conversations stored | Unlimited (Firestore scales automatically) |

### Scaling to 500+ Clients

**Phase 1: Optimize (0–200 clients)**
- Enable n8n execution queues
- Add Redis for n8n to handle concurrent workflows
- Set OpenAI rate limit headers in HTTP request node
```javascript
// Add retry logic in OpenAI node
"options": {
  "timeout": 30000,
  "retry": { "maxRetries": 3, "retryDelay": 1000 }
}
```

**Phase 2: Distribute (200–1000 clients)**
- Deploy multiple n8n instances behind a load balancer
- Each instance handles a subset of WABA IDs
- Use Firebase as the shared state (already stateless)

```bash
# docker-compose.yml for multi-instance
services:
  n8n-1:
    image: n8nio/n8n
    environment:
      - QUEUE_BULL_REDIS_HOST=redis
  n8n-2:
    image: n8nio/n8n
    environment:
      - QUEUE_BULL_REDIS_HOST=redis
  redis:
    image: redis:alpine
  nginx:
    image: nginx
    # round-robin load balancing
```

**Phase 3: Enterprise (1000+ clients)**
- Migrate n8n logic to dedicated microservices (Python FastAPI)
- Use Pub/Sub for message queuing (Google Cloud Pub/Sub)
- Cache frequent Firebase reads in Redis (TTL: 30 seconds)
- Dedicated OpenAI organization with higher rate limits

### Firebase Cost Optimization
```
Free Tier Limits:
- 50,000 reads/day
- 20,000 writes/day  
- 1 GB storage

Optimization for 100 clients at 100 messages/day each = 10,000 messages:
- Each message = 3 reads (client config + history + save) + 1 write
- Total: 30,000 reads + 10,000 writes/day → WITHIN FREE TIER ✅

For 500 clients at 100 msg/day: 150,000 reads → Blaze plan (~$0.06/100k reads)
Monthly cost for 500 clients: ~$10-20 USD
```

---

## 5. Adding New Clients (SOP)

### Standard Operating Procedure — New Client Onboarding

**Time Required:** 5–10 minutes  
**Tools Needed:** Dashboard, Meta Business Manager  

**Step 1: Dashboard → Add Client**
1. Navigate to `➕ Add Client`
2. Fill in Business Information (name, sector, contact)
3. Paste WhatsApp credentials from Meta Business Manager:
   - Phone Number ID (found in WhatsApp API settings)
   - WABA ID (WhatsApp Business Account ID)
   - Access Token (generate permanent token)
4. Paste the System Prompt (crafted for the client's brand)
5. Set subscription plan and expiry date
6. Click "🚀 Create Client & Go Live"

**Step 2: Configure Meta Webhook**
- The webhook URL is shared across ALL clients (single endpoint)
- Only the Verify Token needs to be set per-client phone number
- In Meta Business Manager → WhatsApp → Configuration:
  ```
  Callback URL: https://n8n.donialabs.tech/webhook/whatsapp-webhook
  Verify Token: [client's verify_token from Firebase]
  ```

**Step 3: Test**
Send a test message to the client's WhatsApp number and verify:
- Response arrives within 5 seconds
- Language detection works correctly
- Brand voice matches system prompt

**Step 4: Handover**
- Share access credentials with client (WhatsApp number only, no dashboard access)
- Schedule 48h subscription alert is configured automatically

### Quick-Add via CSV (Bulk Import)
For onboarding 10+ clients simultaneously:
```python
# bulk_import.py
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import json

cred = credentials.Certificate("firebase-service-account.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

df = pd.read_csv("clients_to_import.csv")
for _, row in df.iterrows():
    client_data = {
        "client_id": row["client_id"],
        "business_name": row["business_name"],
        # ... map all columns
    }
    db.collection("clients").document(row["client_id"]).set(client_data)
    print(f"✅ Imported: {row['business_name']}")
```

CSV Template columns:
```
client_id, business_name, business_sector, contact_email,
phone_number_id, waba_id, access_token, verify_token,
system_prompt, plan, expiry_date, language_mode
```

---

## 6. Security Checklist

### Pre-Launch Security Audit
- [ ] All Firebase access tokens stored in Firebase, NEVER in n8n plaintext
- [ ] Firebase Security Rules deployed (no open read/write)
- [ ] n8n instance behind HTTPS with valid SSL certificate
- [ ] Dashboard protected by strong password (use environment variable)
- [ ] Meta webhook verify token is unique per client
- [ ] OpenAI API key has spending limits set
- [ ] Audit logs are enabled and immutable
- [ ] Global kill switch tested and confirmed working
- [ ] All blocked topics tested with sample messages

### Token Rotation Policy
```
Access Tokens: Rotate every 90 days (set calendar reminder)
Dashboard Password: Rotate every 60 days
Firebase Service Account: Rotate every 180 days
OpenAI API Key: Rotate every 90 days or if compromised
```

### Incident Response
```
If suspicious activity detected:
1. Activate Global Kill Switch immediately (Dashboard → Security)
2. Check Audit Logs for unauthorized actions
3. Rotate ALL tokens (WhatsApp, OpenAI, Firebase)
4. Identify affected client(s) and notify them
5. Deactivate Global Kill Switch after remediation
6. Document incident in audit log
```

---

## 7. Monitoring & Alerting

### n8n Built-in Monitoring
- Enable "Error Workflow" in n8n settings → creates error notifications
- Set up execution history retention (recommended: 30 days)
- Monitor execution time — alert if average > 10 seconds

### Firebase Monitoring
```javascript
// In Firebase Console → Monitor tab:
// Set alerts for:
// - Read operations > 40,000/day (approaching free limit)
// - Write operations > 15,000/day
// - Storage > 800 MB
```

### Dashboard Health Check Endpoint
Add this to n8n as a separate workflow:
```
GET https://your-n8n.com/webhook/health
Response: { "status": "ok", "clients_active": 42, "timestamp": "..." }
```

### Uptime Monitoring (Free Tools)
- **UptimeRobot**: Monitor n8n webhook endpoint every 5 minutes
- **Freshping**: Alert if dashboard is down
- Set alert email: alerts@donialabs.tech

---

## 8. Troubleshooting Guide

### Issue: Client not receiving AI responses
```
Diagnosis Steps:
1. Check n8n execution logs for the specific WABA ID
2. Verify client is_active = true in Firebase
3. Verify kill_switch = false
4. Check subscription expiry_date > today
5. Verify access_token is valid (test via Meta Graph API Explorer)
6. Check OpenAI API key has sufficient credits
```

### Issue: Wrong language in responses
```
Check in Firebase client document:
- ai_config.language_mode = "auto" or "manual"
- If manual: ai_config.forced_language = "ar" | "fr" | "en"
- Check language detection scores in n8n execution log
```

### Issue: Safety filter too aggressive / not aggressive enough
```
In Firebase → clients → {client_id} → safety_config:
- Add/remove from blocked_topics array
- Add specific words to custom_blocked_words
Changes take effect IMMEDIATELY (no restart required)
```

### Issue: Dashboard not updating
```
Streamlit cache TTL is set to 30 seconds.
Force refresh: press R in browser or wait 30 seconds.
If Firebase data still wrong, check Firebase credentials path.
```

### Issue: Subscription alert emails not sending
```
Check in Firebase:
- subscription.auto_alert_48h = true
- subscription.alert_sent = false (if true, alert already sent)
Check n8n CRON workflow is active and running every 6 hours
Verify SMTP credentials in n8n environment variables
```

---

## 9. Cost Estimation

### For 50 Clients (300 messages/day total)

| Service | Usage | Monthly Cost |
|---------|-------|-------------|
| Firebase Firestore | Within free tier | **$0** |
| n8n Cloud (Starter) | 5,000 executions/month | **$20** |
| OpenAI GPT-4o | 300 msgs × 1000 tokens avg | **~$18** |
| VPS for Dashboard | 1GB RAM Hetzner | **€4** |
| Total | | **~$42/month** |

### For 200 Clients (2,000 messages/day total)

| Service | Usage | Monthly Cost |
|---------|-------|-------------|
| Firebase Firestore | Blaze plan, ~60k reads/day | **~$5** |
| n8n Cloud (Pro) or Self-hosted | Unlimited | **$50 or $20** |
| OpenAI GPT-4o | 2,000 msgs × 1000 tokens | **~$120** |
| VPS (4GB RAM) | DigitalOcean | **$24** |
| Total | | **~$199/month** |

### Revenue Model Guidance
```
If charging clients: 3,000–10,000 DZD/month per client
50 clients × 5,000 DZD = 250,000 DZD/month gross
Platform cost at 50 clients: ~42 USD ≈ 5,670 DZD
Gross margin: 97.7% 🚀
```

---

## 10. Roadmap

### v1.1 — Next Sprint (2–4 weeks)
- [ ] Voice message transcription (WhatsApp audio → text → AI)
- [ ] Image recognition (product photos via GPT-4o vision)
- [ ] Client-facing analytics portal (read-only)
- [ ] Telegram support (second channel)

### v1.2 — Growth Phase (1–3 months)
- [ ] Multi-agent support (Sales bot + Support bot per client)
- [ ] A/B testing for system prompts
- [ ] Automated client reports (weekly PDF via email)
- [ ] WhatsApp flow builder integration

### v2.0 — Enterprise Features (3–6 months)
- [ ] Multi-tenant architecture with isolated data
- [ ] Fine-tuned models per client sector
- [ ] CRM integrations (Salesforce, HubSpot, Zoho)
- [ ] Real-time analytics with Google Looker Studio
- [ ] White-label dashboard for clients

---

## Appendix: Environment Variables Reference

```env
# Firebase
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_CREDENTIALS_PATH=./firebase-service-account.json

# OpenAI
OPENAI_API_KEY=sk-proj-...

# n8n
N8N_WEBHOOK_BASE_URL=https://n8n.yourdomain.com
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=secure_password

# Dashboard
ADMIN_PASSWORD=very_secure_password_here

# Email Alerts (SendGrid recommended)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASS=SG.your-sendgrid-api-key
ALERT_EMAIL=alerts@donialabs.tech
```

---

*Document maintained by DONIA LABS TECH — Last updated: 2025*  
*For support: tech@donialabs.tech*
