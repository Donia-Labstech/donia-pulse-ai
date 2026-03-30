# 🚀 دليل النشر السحابي المجاني — Donia Pulse AI + Arcee
## DONIA LABS TECH — خطوة بخطوة

---

## 🗺️ خريطة النشر الكاملة

```
┌─────────────────────────────────────────────────────────┐
│  المستخدم (WhatsApp)                                     │
│       ↓                                                  │
│  Meta Cloud API (مجاني)                                  │
│       ↓                                                  │
│  n8n على Railway.app (مجاني 500 ساعة/شهر)               │
│       ↓              ↓                                   │
│  Arcee AI API    Firebase Firestore (مجاني)              │
│                       ↓                                  │
│  Dashboard على Streamlit Cloud (مجاني)                   │
└─────────────────────────────────────────────────────────┘
```

---

## المرحلة 1 — Firebase (قاعدة البيانات) ✅

### الخطوة 1.1 — إنشاء مشروع Firebase
```
1. اذهب إلى: https://console.firebase.google.com
2. اضغط "Add project" أو "إضافة مشروع"
3. الاسم: donia-pulse-ai
4. أوقف Google Analytics (غير ضروري الآن)
5. اضغط "Create project"
```

### الخطوة 1.2 — تفعيل Firestore
```
1. من القائمة اليسرى: Build → Firestore Database
2. اضغط "Create database"
3. اختر: Start in production mode
4. المنطقة: europe-west1 (الأقرب للجزائر)
5. اضغط "Enable"
```

### الخطوة 1.3 — إنشاء Service Account
```
1. Project Settings (أيقونة الترس) → Service accounts
2. اضغط "Generate new private key"
3. احفظ الملف باسم: firebase-service-account.json
4. ضعه في مجلد المشروع: donia-pulse-ai/
```

### الخطوة 1.4 — أضف أول عميل تجريبي
```
Firestore → Start collection → clients
Document ID: test_client_01
أضف الحقول من firebase_schema.json
```

---

## المرحلة 2 — GitHub (حفظ الكود) ✅

### الخطوة 2.1 — إنشاء Repository
```
1. اذهب إلى: https://github.com
2. اضغط "New repository"
3. الاسم: donia-pulse-ai
4. Private (خاص) ← مهم جداً لأمان المفاتيح
5. اضغط "Create repository"
```

### الخطوة 2.2 — رفع الملفات (PowerShell)
```powershell
cd donia-pulse-ai

git init
git add dashboard.py requirements.txt MASTER_BLUEPRINT.md n8n_arcee_workflow.json firebase_schema.json
git commit -m "feat: Donia Pulse AI initial commit"
git branch -M main
git remote add origin https://github.com/اسم_المستخدم/donia-pulse-ai.git
git push -u origin main
```

> ⚠️ لا ترفع هذه الملفات أبداً:
> - firebase-service-account.json
> - .env
> (تأكد أنهم في .gitignore)

---

## المرحلة 3 — Streamlit Cloud (Dashboard سحابي مجاني) ✅

### الخطوة 3.1 — نشر Dashboard
```
1. اذهب إلى: https://share.streamlit.io
2. سجّل دخول بحساب GitHub
3. اضغط "New app"
4. Repository: donia-pulse-ai
5. Branch: main
6. Main file path: dashboard.py
7. اضغط "Deploy!"
```

### الخطوة 3.2 — إضافة Secrets (بديل .env في السحابة)
```
في Streamlit Cloud → Settings → Secrets
أضف هذا النص:
```

```toml
FIREBASE_PROJECT_ID = "donia-pulse-ai"
ADMIN_PASSWORD = "كلمة_مرور_قوية_هنا"

[firebase_credentials]
type = "service_account"
project_id = "donia-pulse-ai"
private_key_id = "xxx"
private_key = "-----BEGIN PRIVATE KEY-----\nxxx\n-----END PRIVATE KEY-----\n"
client_email = "firebase-adminsdk-xxx@donia-pulse-ai.iam.gserviceaccount.com"
client_id = "xxx"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
```

> انسخ القيم من ملف firebase-service-account.json

### الخطوة 3.3 — تعديل dashboard.py لقراءة Secrets
```python
# أضف هذا في أعلى dashboard.py بعد الـ imports:
import streamlit as st
import json
import tempfile

def init_firebase():
    try:
        # في السحابة: اقرأ من Secrets
        if "firebase_credentials" in st.secrets:
            cred_dict = dict(st.secrets["firebase_credentials"])
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(cred_dict, f)
                cred_path = f.name
        else:
            # محلياً: اقرأ من الملف
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-service-account.json")
        
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Firebase error: {e}")
        return None
```

```powershell
# بعد التعديل: ارفع التحديث لـ GitHub
git add dashboard.py
git commit -m "fix: support Streamlit Cloud secrets"
git push
```

سيتحدث Streamlit تلقائياً بعد الـ push ✅

---

## المرحلة 4 — n8n على Railway (محرك الوكيل) ✅

### الخطوة 4.1 — إنشاء حساب Railway
```
1. اذهب إلى: https://railway.app
2. سجّل دخول بـ GitHub
3. اضغط "New Project"
4. اختر: "Deploy from Docker Image"
5. الصورة: n8nio/n8n
```

### الخطوة 4.2 — إعداد متغيرات البيئة في Railway
```
في Railway → Variables → Add these:
```

| المتغير | القيمة |
|---------|--------|
| `N8N_BASIC_AUTH_ACTIVE` | `true` |
| `N8N_BASIC_AUTH_USER` | `admin` |
| `N8N_BASIC_AUTH_PASSWORD` | `كلمة_مرور_قوية` |
| `ARCEE_API_KEY` | `مفتاح_Arcee_الخاص_بك` |
| `FIREBASE_PROJECT_ID` | `donia-pulse-ai` |
| `N8N_HOST` | `0.0.0.0` |
| `N8N_PORT` | `5678` |
| `WEBHOOK_URL` | `https://اسمك.up.railway.app` |

### الخطوة 4.3 — الحصول على رابط n8n
```
Railway → Settings → Domains → Generate Domain
ستحصل على رابط مثل:
https://donia-pulse-ai.up.railway.app
```

### الخطوة 4.4 — استيراد Workflow
```
1. افتح رابط n8n في المتصفح
2. سجل دخول بكلمة المرور
3. Workflows → Import from file
4. اختر: n8n_arcee_workflow.json
5. فعّل الـ Workflow: toggle "Active" ← مهم!
```

### الخطوة 4.5 — Firebase Access Token في n8n
```javascript
// أضف node جديد من نوع "Code" في بداية الـ Workflow
// اسمه: "🔑 Get Firebase Token"
// هذا الكود يولّد Token تلقائياً

const { GoogleAuth } = require('google-auth-library');

const serviceAccount = {
  type: "service_account",
  project_id: $env.FIREBASE_PROJECT_ID,
  private_key: $env.FIREBASE_PRIVATE_KEY.replace(/\\n/g, '\n'),
  client_email: $env.FIREBASE_CLIENT_EMAIL
};

const auth = new GoogleAuth({
  credentials: serviceAccount,
  scopes: ['https://www.googleapis.com/auth/cloud-platform']
});

const client = await auth.getClient();
const token = await client.getAccessToken();

return [{ json: { firebase_token: token.token } }];
```

أضف هذه المتغيرات أيضاً في Railway:
| المتغير | القيمة |
|---------|--------|
| `FIREBASE_CLIENT_EMAIL` | من ملف service-account.json |
| `FIREBASE_PRIVATE_KEY` | من ملف service-account.json |

---

## المرحلة 5 — ربط Meta WhatsApp ✅

### الخطوة 5.1 — إعداد Webhook في Meta
```
1. اذهب إلى: https://developers.facebook.com
2. اختر تطبيقك
3. WhatsApp → Configuration → Webhook
4. Callback URL:
   https://donia-pulse.up.railway.app/webhook/whatsapp-webhook
5. Verify Token: اخترع كلمة سرية مثل: donia_verify_2024
6. اضغط "Verify and Save"
7. فعّل Subscribe على: messages
```

### الخطوة 5.2 — أضف بيانات العميل في Firebase
```
في Firestore → clients → new document
أضف هذه الحقول الأساسية:
```

```json
{
  "client_id": "test_client_01",
  "business_name": "متجر الاختبار",
  "whatsapp_config": {
    "phone_number_id": "رقم_الـ_Phone_Number_ID_من_Meta",
    "waba_id": "رقم_الـ_WABA_ID_من_Meta",
    "access_token": "الـ_Token_من_Meta"
  },
  "subscription": {
    "status": "active",
    "expiry_date": "2026-12-31T23:59:59Z",
    "plan": "premium"
  },
  "ai_config": {
    "arcee_model": "arcee-blaze",
    "language_mode": "auto",
    "temperature": 0.7,
    "max_tokens": 1024,
    "system_prompt": "أنت مساعد ذكي لمتجر الاختبار. أجب بأسلوب احترافي وودود.",
    "brand_name": "متجر الاختبار"
  },
  "safety_config": {
    "guardrails_enabled": true,
    "blocked_topics": ["politics", "religion", "adult_content", "violence"]
  },
  "status": {
    "is_active": true,
    "kill_switch": false
  }
}
```

---

## المرحلة 6 — الاختبار النهائي ✅

### اختبر هذه السيناريوهات:

```
1. أرسل رسالة عادية بالعربية على WhatsApp
   ← يجب أن تصلك إجابة من Arcee خلال 5 ثوانٍ

2. أرسل رسالة بالفرنسية
   ← يجب أن يرد بالفرنسية تلقائياً

3. أرسل "سياسة" أو "دين"
   ← يجب أن يرسل رسالة الرفض

4. من Dashboard: فعّل Kill Switch للعميل
   ← يجب أن تصله رسالة "الخدمة متوقفة"

5. من Dashboard: عطّل Kill Switch
   ← يعود للعمل تلقائياً
```

---

## 📊 ملخص التكاليف

| الخدمة | الخطة المجانية | الحد |
|--------|---------------|------|
| Firebase Firestore | Spark (مجاني) | 50,000 قراءة/يوم |
| Streamlit Cloud | مجاني | تطبيق واحد |
| Railway n8n | مجاني | 500 ساعة/شهر |
| Arcee AI | حسب مفتاحك | - |
| Meta WhatsApp | مجاني | 1000 محادثة/شهر |
| **الإجمالي** | **مجاني تقريباً** | **كافٍ للاختبار** |

---

## 🆘 حل المشاكل الشائعة

| المشكلة | السبب | الحل |
|---------|-------|------|
| Webhook لا يعمل | رابط n8n غير صحيح | تحقق من WEBHOOK_URL في Railway |
| Arcee لا يرد | مفتاح API منتهي | جدّد المفتاح في arcee.ai |
| Firebase خطأ | Token منتهي | أعد تشغيل n8n service |
| Dashboard لا يتحدث | Cache | انتظر 30 ثانية أو اضغط R |

---

*DONIA LABS TECH — donia-pulse-ai v2.0 مع Arcee*
