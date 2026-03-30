"""
╔══════════════════════════════════════════════════════════╗
║       DONIA PULSE AI — Dashboard v2.0 (Supabase)        ║
║       DONIA LABS TECH                                    ║
╚══════════════════════════════════════════════════════════╝
تثبيت:
    pip install -r requirements.txt

تشغيل:
    streamlit run dashboard.py
"""

import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════
# إعداد الصفحة
# ═══════════════════════════════════════════════════════
st.set_page_config(
    page_title="Donia Pulse AI",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
    :root {
        --primary: #6C63FF; --accent: #00D9A3;
        --danger: #FF4757; --warning: #FFA502;
        --bg: #0D0F1A; --card: #161826; --border: #252840;
    }
    .stApp { background-color: var(--bg); font-family: 'IBM Plex Sans Arabic', sans-serif; }
    .metric-card {
        background: var(--card); border: 1px solid var(--border);
        border-radius: 12px; padding: 20px; text-align: center;
        border-top: 3px solid var(--primary);
    }
    .metric-value { font-size: 2.2rem; font-weight: 700; color: var(--accent); font-family: 'JetBrains Mono', monospace; }
    .metric-label { font-size: 0.85rem; color: #888; margin-top: 4px; }
    .status-active  { background:rgba(0,217,163,.15); color:var(--accent);   border:1px solid var(--accent);   padding:3px 10px; border-radius:20px; font-size:.75rem; }
    .status-killed  { background:rgba(255,71,87,.15);  color:var(--danger);   border:1px solid var(--danger);   padding:3px 10px; border-radius:20px; font-size:.75rem; }
    .status-warning { background:rgba(255,165,2,.15);  color:var(--warning);  border:1px solid var(--warning);  padding:3px 10px; border-radius:20px; font-size:.75rem; }
    .kill-banner { background:linear-gradient(135deg,#FF4757,#c0392b); color:white; padding:15px; border-radius:10px; font-weight:700; text-align:center; margin-bottom:20px; }
    div[data-testid="stSidebar"] { background: var(--card) !important; border-right: 1px solid var(--border) !important; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# اتصال Supabase
# ═══════════════════════════════════════════════════════
@st.cache_resource
def get_supabase() -> Client:
    try:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        if not url or not key:
            st.error("❌ تحقق من ملف .env")
            return None
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ خطأ: {e}")
        return None
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال بـ Supabase: {e}")
        return None


# ═══════════════════════════════════════════════════════
# دوال قاعدة البيانات
# ═══════════════════════════════════════════════════════
@st.cache_data(ttl=30)
def get_all_clients():
    sb = get_supabase()
    if not sb: return []
    try:
        res = sb.table("clients").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except Exception as e:
        st.error(f"خطأ: {e}"); return []


@st.cache_data(ttl=10)
def get_system_config():
    sb = get_supabase()
    if not sb: return {}
    try:
        res = sb.table("system_config").select("*").limit(1).execute()
        return res.data[0] if res.data else {}
    except:
        return {}


def update_client(client_id: str, updates: dict):
    sb = get_supabase()
    if not sb: return False
    try:
        updates["updated_at"] = datetime.utcnow().isoformat()
        sb.table("clients").update(updates).eq("client_id", client_id).execute()
        log_audit(f"update", client_id, str(updates))
        get_all_clients.clear()
        return True
    except Exception as e:
        st.error(f"خطأ في التحديث: {e}"); return False


def create_client_db(data: dict):
    sb = get_supabase()
    if not sb: return False
    try:
        sb.table("clients").insert(data).execute()
        log_audit("client_created", data["client_id"], "عميل جديد")
        get_all_clients.clear()
        return True
    except Exception as e:
        st.error(f"خطأ في الإنشاء: {e}"); return False


def toggle_global_kill_switch(activate: bool):
    sb = get_supabase()
    if not sb: return False
    try:
        sb.table("system_config").update({
            "global_kill_switch": activate,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", get_system_config().get("id")).execute()
        log_audit("GLOBAL_KILL_SWITCH", "ALL", "ACTIVATED" if activate else "DEACTIVATED")
        get_system_config.clear()
        return True
    except Exception as e:
        st.error(f"خطأ: {e}"); return False


def log_audit(action: str, target: str, details: str):
    sb = get_supabase()
    if sb:
        try:
            sb.table("audit_logs").insert({
                "action": action, "target": target,
                "details": details,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
        except: pass


# ═══════════════════════════════════════════════════════
# مساعدات
# ═══════════════════════════════════════════════════════
def is_expiring_soon(client):
    exp = client.get("expiry_date")
    if not exp: return False
    try:
        exp_dt = datetime.fromisoformat(exp.replace("Z","").replace("+00:00",""))
        now = datetime.utcnow()
        return now < exp_dt < now + timedelta(hours=48)
    except: return False


def is_expired(client):
    exp = client.get("expiry_date")
    if not exp: return False
    try:
        return datetime.fromisoformat(exp.replace("Z","").replace("+00:00","")) < datetime.utcnow()
    except: return False


def status_badge(client):
    if client.get("kill_switch"):
        return '<span class="status-killed">🔴 Kill Switch</span>'
    if is_expired(client):
        return '<span class="status-killed">⛔ منتهي</span>'
    if is_expiring_soon(client):
        return '<span class="status-warning">⚠️ ينتهي قريباً</span>'
    if client.get("is_active"):
        return '<span class="status-active">✅ نشط</span>'
    return '<span class="status-killed">⚫ غير نشط</span>'


def metric_card(label, value, color="#00D9A3"):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color:{color};">{value}</div>
        <div class="metric-label">{label}</div>
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# المصادقة
# ═══════════════════════════════════════════════════════
def check_auth():
    if st.session_state.get("auth"): return True
    st.markdown("""
    <div style='text-align:center;padding:60px 20px;'>
        <div style='font-size:3rem;'>🌐</div>
        <h1 style='color:#6C63FF;'>Donia Pulse AI</h1>
        <p style='color:#888;'>Management Dashboard — DONIA LABS TECH</p>
    </div>""", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        pwd = st.text_input("🔑 كلمة المرور", type="password", placeholder="أدخل كلمة المرور")
        if st.button("🚀 دخول", use_container_width=True):
            stored = os.getenv("ADMIN_PASSWORD") or st.secrets.get("ADMIN_PASSWORD", "DoniaLabs2024!")
            if hashlib.sha256(pwd.encode()).hexdigest() == hashlib.sha256(stored.encode()).hexdigest():
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("❌ كلمة مرور خاطئة")
    return False


# ═══════════════════════════════════════════════════════
# صفحة: Overview
# ═══════════════════════════════════════════════════════
def page_overview():
    clients = get_all_clients()
    config  = get_system_config()

    if config.get("global_kill_switch"):
        st.markdown('<div class="kill-banner">🚨 GLOBAL KILL SWITCH نشط — جميع الوكلاء متوقفون</div>', unsafe_allow_html=True)

    st.markdown("### 📊 نظرة عامة على المنصة")

    now = datetime.utcnow()
    active   = sum(1 for c in clients if c.get("is_active") and not c.get("kill_switch") and not is_expired(c))
    killed   = sum(1 for c in clients if c.get("kill_switch"))
    expiring = sum(1 for c in clients if is_expiring_soon(c))
    total_msgs = sum(c.get("total_messages", 0) for c in clients)

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: metric_card("إجمالي العملاء", len(clients), "#6C63FF")
    with c2: metric_card("نشط", active, "#00D9A3")
    with c3: metric_card("Kill Switch", killed, "#FF4757")
    with c4: metric_card("ينتهي ≤48h", expiring, "#FFA502")
    with c5: metric_card("إجمالي الرسائل", f"{total_msgs:,}", "#6C63FF")

    st.markdown("---")

    if clients:
        cl, cr = st.columns([3,2])
        with cl:
            st.markdown("#### 📈 الرسائل لكل عميل")
            df = pd.DataFrame([{"العميل": c.get("business_name","?"), "الرسائل": c.get("total_messages",0)} for c in clients])
            df = df.sort_values("الرسائل", ascending=False).head(10)
            fig = px.bar(df, x="العميل", y="الرسائل", color="الرسائل",
                         color_continuous_scale=["#252840","#6C63FF","#00D9A3"], template="plotly_dark")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=280, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig, use_container_width=True)

        with cr:
            st.markdown("#### 🥧 توزيع الحالات")
            labels = ["نشط","Kill Switch","ينتهي قريباً","غير نشط"]
            values = [active, killed, expiring, max(0, len(clients)-active-killed-expiring)]
            fig2 = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.6,
                                          marker_colors=["#00D9A3","#FF4757","#FFA502","#555"])])
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=280, margin=dict(l=0,r=0,t=0,b=0),
                               legend=dict(font=dict(color="white")))
            st.plotly_chart(fig2, use_container_width=True)


# ═══════════════════════════════════════════════════════
# صفحة: إدارة العملاء
# ═══════════════════════════════════════════════════════
def page_clients():
    st.markdown("### 👥 إدارة العملاء")
    clients = get_all_clients()

    col_s, col_f = st.columns([3,1])
    with col_s: search = st.text_input("🔍 بحث", placeholder="اسم العميل، ID، قطاع...")
    with col_f: filt = st.selectbox("تصفية", ["الكل","نشط","Kill Switch","ينتهي قريباً","منتهي"])

    filtered = clients
    if search:
        q = search.lower()
        filtered = [c for c in filtered if q in c.get("business_name","").lower() or q in c.get("client_id","").lower()]
    if filt == "نشط":        filtered = [c for c in filtered if c.get("is_active") and not c.get("kill_switch")]
    elif filt == "Kill Switch": filtered = [c for c in filtered if c.get("kill_switch")]
    elif filt == "ينتهي قريباً": filtered = [c for c in filtered if is_expiring_soon(c)]
    elif filt == "منتهي":    filtered = [c for c in filtered if is_expired(c)]

    st.markdown(f"**{len(filtered)}** عميل")
    st.markdown("---")

    for i, c in enumerate(filtered):
        with st.expander(f"🏢 {c.get('business_name','N/A')}  |  `{c.get('client_id','N/A')}`  |  {status_badge(c)}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**📋 معلومات عامة**")
                st.write(f"القطاع: {c.get('business_sector','N/A')}")
                st.write(f"البريد: {c.get('contact_email','N/A')}")
            with col2:
                st.markdown("**🤖 إعدادات الذكاء**")
                st.write(f"النموذج: `{c.get('arcee_model','arcee-blaze')}`")
                st.write(f"اللغة: `{c.get('language_mode','auto')}`")
                st.write(f"الحرارة: `{c.get('temperature',0.7)}`")
            with col3:
                st.markdown("**📅 الاشتراك**")
                st.write(f"الخطة: `{c.get('plan','N/A')}`")
                exp = c.get('expiry_date','N/A')
                st.write(f"الانتهاء: `{str(exp)[:10]}`")
                st.metric("الرسائل", f"{c.get('total_messages',0):,}")

            st.markdown("---")
            b1, b2, b3 = st.columns(3)

            with b1:
                if c.get("kill_switch"):
                    if st.button("✅ إعادة التفعيل", key=f"r_{i}"):
                        if update_client(c["client_id"], {"kill_switch": False, "kill_switch_reason": None}):
                            st.success("✅ تم إعادة التفعيل"); st.rerun()
                else:
                    if st.button("🔴 تفعيل Kill Switch", key=f"k_{i}"):
                        if update_client(c["client_id"], {"kill_switch": True}):
                            st.warning("🔴 Kill Switch مفعّل"); st.rerun()

            with b2:
                if st.button("📅 تمديد الاشتراك", key=f"e_{i}"):
                    st.session_state[f"ext_{i}"] = True

            with b3:
                if st.button("🌍 تغيير اللغة", key=f"l_{i}"):
                    st.session_state[f"lng_{i}"] = True

            if st.session_state.get(f"ext_{i}"):
                with st.form(f"ef_{i}"):
                    new_exp = st.date_input("تاريخ الانتهاء الجديد", value=datetime.utcnow() + timedelta(days=30))
                    if st.form_submit_button("✅ تأكيد التمديد"):
                        if update_client(c["client_id"], {
                            "expiry_date": new_exp.isoformat() + "T23:59:59Z",
                            "sub_status": "active", "alert_sent": False
                        }):
                            st.success(f"✅ تم التمديد حتى {new_exp}")
                            del st.session_state[f"ext_{i}"]; st.rerun()

            if st.session_state.get(f"lng_{i}"):
                with st.form(f"lf_{i}"):
                    mode = st.radio("وضع اللغة", ["auto","manual"], horizontal=True)
                    lang = st.selectbox("اللغة المجبرة", ["ar","fr","en"]) if mode == "manual" else None
                    if st.form_submit_button("✅ حفظ"):
                        if update_client(c["client_id"], {"language_mode": mode, "forced_language": lang}):
                            st.success("✅ تم الحفظ")
                            del st.session_state[f"lng_{i}"]; st.rerun()


# ═══════════════════════════════════════════════════════
# صفحة: إضافة عميل جديد
# ═══════════════════════════════════════════════════════
def page_add_client():
    st.markdown("### ➕ إضافة عميل جديد")

    with st.form("new_client"):
        st.markdown("#### 📋 معلومات العمل")
        c1, c2 = st.columns(2)
        with c1:
            client_id     = st.text_input("Client ID *", placeholder="boutique_oran_01")
            business_name = st.text_input("اسم العمل *", placeholder="بوتيك وهران")
        with c2:
            sector = st.selectbox("القطاع", ["e-commerce","restaurant","hotel","healthcare","education","real_estate","other"])
            email  = st.text_input("البريد الإلكتروني", placeholder="owner@business.dz")

        st.markdown("#### 📱 WhatsApp")
        c3, c4 = st.columns(2)
        with c3:
            phone_id = st.text_input("Phone Number ID *", placeholder="من Meta Business")
            waba_id  = st.text_input("WABA ID *", placeholder="WhatsApp Business Account ID")
        with c4:
            token    = st.text_input("Access Token *", type="password", placeholder="EAAxxxx...")
            v_token  = st.text_input("Verify Token *", placeholder="كلمة سرية تختارها")

        st.markdown("#### 🤖 إعدادات Arcee")
        c5, c6 = st.columns(2)
        with c5:
            model    = st.selectbox("النموذج", ["arcee-blaze","arcee-lite","arcee-nova","arcee-agent"])
            lang_mode = st.radio("اللغة", ["auto","manual"], horizontal=True)
            forced   = st.selectbox("اللغة المجبرة", ["ar","fr","en"]) if lang_mode == "manual" else None
        with c6:
            temp     = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1)
            tokens   = st.slider("Max Tokens", 256, 4096, 1024, 128)

        brand  = st.text_input("اسم العلامة التجارية", placeholder="نفس اسم العمل أو مختلف")
        prompt = st.text_area("System Prompt *", height=120,
                              placeholder="أنت مساعد ذكي لـ [اسم المتجر]. أجب بأسلوب احترافي...")

        st.markdown("#### 📅 الاشتراك")
        c7, c8 = st.columns(2)
        with c7: plan = st.selectbox("الخطة", ["basic","standard","premium"])
        with c8: exp  = st.date_input("تاريخ الانتهاء", value=datetime.utcnow() + timedelta(days=30))

        submitted = st.form_submit_button("🚀 إنشاء العميل والبدء مباشرة", type="primary", use_container_width=True)

        if submitted:
            if not all([client_id, business_name, phone_id, waba_id, token, prompt]):
                st.error("❌ يرجى ملء جميع الحقول المطلوبة (*)")
            else:
                data = {
                    "client_id": client_id.strip().lower().replace(" ","_"),
                    "business_name": business_name,
                    "business_sector": sector,
                    "contact_email": email,
                    "phone_number_id": phone_id,
                    "waba_id": waba_id,
                    "access_token": token,
                    "verify_token": v_token,
                    "plan": plan,
                    "sub_status": "active",
                    "expiry_date": exp.isoformat() + "T23:59:59Z",
                    "arcee_model": model,
                    "language_mode": lang_mode,
                    "forced_language": forced,
                    "temperature": temp,
                    "max_tokens": tokens,
                    "system_prompt": prompt,
                    "brand_name": brand or business_name,
                    "is_active": True,
                    "kill_switch": False,
                    "total_messages": 0
                }
                if create_client_db(data):
                    st.success(f"✅ تم إنشاء **{business_name}** بنجاح!")
                    st.balloons()


# ═══════════════════════════════════════════════════════
# صفحة: الأمان
# ═══════════════════════════════════════════════════════
def page_security():
    st.markdown("### 🔐 الأمان والتحكم العام")
    config = get_system_config()
    gks = config.get("global_kill_switch", False)

    st.markdown("#### 🚨 Global Kill Switch")
    if gks:
        st.markdown('<div class="kill-banner">🚨 GLOBAL KILL SWITCH نشط — جميع الوكلاء متوقفون</div>', unsafe_allow_html=True)
        if st.button("✅ إلغاء تفعيل Global Kill Switch", type="primary", use_container_width=True):
            if toggle_global_kill_switch(False):
                st.success("✅ جميع الوكلاء عادوا للعمل"); st.rerun()
    else:
        st.success("✅ النظام يعمل بشكل طبيعي")
        with st.expander("⚠️ تفعيل Global Kill Switch"):
            st.warning("⚠️ سيوقف هذا جميع الوكلاء فوراً لجميع العملاء!")
            reason = st.text_input("سبب الإيقاف *")
            if st.button("🔴 تفعيل Global Kill Switch"):
                if reason:
                    if toggle_global_kill_switch(True):
                        st.error("🚨 تم إيقاف جميع الوكلاء"); st.rerun()
                else: st.error("أدخل سبباً أولاً")

    st.markdown("---")
    st.markdown("#### 📋 سجل الإجراءات")
    sb = get_supabase()
    if sb:
        try:
            logs = sb.table("audit_logs").select("*").order("created_at", desc=True).limit(50).execute()
            if logs.data:
                st.dataframe(pd.DataFrame(logs.data)[["created_at","action","target","details"]], use_container_width=True, height=400)
            else:
                st.info("لا يوجد سجلات بعد.")
        except Exception as e:
            st.error(f"خطأ: {e}")


# ═══════════════════════════════════════════════════════
# الشريط الجانبي
# ═══════════════════════════════════════════════════════
def sidebar():
    with st.sidebar:
        st.markdown('<div style="font-size:1.3rem;font-weight:700;color:#6C63FF;">🌐 Donia Pulse AI</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:#888;font-size:.75rem;margin-bottom:20px;">DONIA LABS TECH — v2.0</div>', unsafe_allow_html=True)
        st.markdown("---")
        page = st.radio("", ["📊 Overview","👥 العملاء","➕ عميل جديد","🔐 الأمان"], label_visibility="hidden")
        st.markdown("---")
        if st.button("🚪 خروج", use_container_width=True):
            del st.session_state["auth"]; st.rerun()
        st.markdown('<div style="color:#555;font-size:.7rem;text-align:center;">© 2025 DONIA LABS TECH</div>', unsafe_allow_html=True)
    return page


# ═══════════════════════════════════════════════════════
# نقطة الدخول الرئيسية
# ═══════════════════════════════════════════════════════
def main():
    if not check_auth(): return
    page = sidebar()
    if   page == "📊 Overview":    page_overview()
    elif page == "👥 العملاء":     page_clients()
    elif page == "➕ عميل جديد":   page_add_client()
    elif page == "🔐 الأمان":      page_security()

if __name__ == "__main__":
    main()
