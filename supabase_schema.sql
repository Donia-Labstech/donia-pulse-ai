-- ============================================================
-- DONIA PULSE AI — Supabase Database Schema
-- انسخ هذا الكود كاملاً في Supabase → SQL Editor → Run
-- ============================================================

-- ① جدول العملاء (clients)
CREATE TABLE IF NOT EXISTS clients (
    id                  UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id           TEXT UNIQUE NOT NULL,
    business_name       TEXT NOT NULL,
    business_sector     TEXT DEFAULT 'general',
    contact_email       TEXT,
    contact_phone       TEXT,

    -- WhatsApp Config
    phone_number_id     TEXT,
    waba_id             TEXT,
    access_token        TEXT,
    verify_token        TEXT,

    -- Subscription
    plan                TEXT DEFAULT 'basic',
    sub_status          TEXT DEFAULT 'active',
    start_date          TIMESTAMPTZ DEFAULT NOW(),
    expiry_date         TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '30 days'),
    auto_alert_48h      BOOLEAN DEFAULT TRUE,
    alert_sent          BOOLEAN DEFAULT FALSE,

    -- AI Config
    arcee_model         TEXT DEFAULT 'arcee-blaze',
    language_mode       TEXT DEFAULT 'auto',
    forced_language     TEXT,
    temperature         FLOAT DEFAULT 0.7,
    max_tokens          INT DEFAULT 1024,
    system_prompt       TEXT DEFAULT 'أنت مساعد ذكي احترافي.',
    brand_name          TEXT,
    brand_tone          TEXT DEFAULT 'friendly_professional',

    -- Safety
    guardrails_enabled  BOOLEAN DEFAULT TRUE,
    blocked_topics      TEXT[] DEFAULT ARRAY['politics','religion','adult_content','violence'],
    custom_blocked_words TEXT[] DEFAULT ARRAY[]::TEXT[],
    fallback_ar         TEXT DEFAULT 'عذراً، لا يمكنني الإجابة على هذا السؤال.',
    fallback_fr         TEXT DEFAULT 'Désolé, je ne peux pas répondre à cette question.',
    fallback_en         TEXT DEFAULT 'Sorry, I cannot answer this question.',

    -- Status
    is_active           BOOLEAN DEFAULT TRUE,
    kill_switch         BOOLEAN DEFAULT FALSE,
    kill_switch_reason  TEXT,
    maintenance_mode    BOOLEAN DEFAULT FALSE,

    -- Analytics
    total_messages      INT DEFAULT 0,
    messages_today      INT DEFAULT 0,
    last_activity       TIMESTAMPTZ,

    -- Meta
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    notes               TEXT
);

-- ② جدول المحادثات (conversations)
CREATE TABLE IF NOT EXISTS conversations (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id       TEXT REFERENCES clients(client_id) ON DELETE CASCADE,
    user_phone      TEXT NOT NULL,
    user_name       TEXT DEFAULT 'Unknown',
    language        TEXT DEFAULT 'ar',
    user_message    TEXT,
    ai_response     TEXT,
    is_blocked      BOOLEAN DEFAULT FALSE,
    block_reason    TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ③ جدول سجل الإجراءات (audit_logs)
CREATE TABLE IF NOT EXISTS audit_logs (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    admin_email TEXT DEFAULT 'admin@donialabs.tech',
    action      TEXT NOT NULL,
    target      TEXT,
    details     TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ④ إعدادات النظام العامة (system_config)
CREATE TABLE IF NOT EXISTS system_config (
    id                   UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    global_kill_switch   BOOLEAN DEFAULT FALSE,
    kill_switch_message  TEXT DEFAULT 'الخدمة متوقفة مؤقتاً للصيانة.',
    platform_name        TEXT DEFAULT 'Donia Pulse AI',
    version              TEXT DEFAULT '2.0',
    updated_at           TIMESTAMPTZ DEFAULT NOW()
);

-- أضف صف إعدادات افتراضي
INSERT INTO system_config (global_kill_switch, platform_name, version)
VALUES (FALSE, 'Donia Pulse AI', '2.0')
ON CONFLICT DO NOTHING;

-- ⑤ عميل تجريبي للاختبار
INSERT INTO clients (
    client_id, business_name, business_sector,
    contact_email, phone_number_id, waba_id, access_token,
    arcee_model, system_prompt, brand_name,
    plan, expiry_date
) VALUES (
    'test_client_01',
    'متجر الاختبار',
    'e-commerce',
    'test@example.com',
    'PHONE_NUMBER_ID_من_Meta',
    'WABA_ID_من_Meta',
    'ACCESS_TOKEN_من_Meta',
    'arcee-blaze',
    'أنت مساعد ذكي لمتجر الاختبار. أجب بأسلوب احترافي وودود على أسئلة العملاء.',
    'متجر الاختبار',
    'premium',
    NOW() + INTERVAL '365 days'
) ON CONFLICT (client_id) DO NOTHING;

-- ⑥ Indexes للأداء
CREATE INDEX IF NOT EXISTS idx_clients_waba_id    ON clients(waba_id);
CREATE INDEX IF NOT EXISTS idx_clients_is_active  ON clients(is_active);
CREATE INDEX IF NOT EXISTS idx_conversations_client ON conversations(client_id);
CREATE INDEX IF NOT EXISTS idx_conversations_phone  ON conversations(user_phone);

-- ⑦ Row Level Security (حماية البيانات)
ALTER TABLE clients       ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs    ENABLE ROW LEVEL SECURITY;

-- السماح للـ service_role بقراءة وكتابة كل شيء
CREATE POLICY "service_role_all" ON clients
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_all" ON conversations
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_all" ON audit_logs
    FOR ALL USING (auth.role() = 'service_role');

-- ✅ انتهى! قاعدة البيانات جاهزة
SELECT 'تم إنشاء قاعدة البيانات بنجاح ✅' AS status;
