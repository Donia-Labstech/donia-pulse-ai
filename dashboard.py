"""
╔══════════════════════════════════════════════════════════════════╗
║          DONIA PULSE AI — Management Dashboard v1.0             ║
║          Built by DONIA LABS TECH                               ║
╚══════════════════════════════════════════════════════════════════╝

Installation:
    pip install streamlit firebase-admin pandas plotly requests python-dotenv

Run:
    streamlit run dashboard.py

Environment Variables (.env):
    FIREBASE_CREDENTIALS_PATH=./firebase-service-account.json
    FIREBASE_PROJECT_ID=your-project-id
    ADMIN_PASSWORD=your_secure_password
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import hashlib
import time
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════
# CONFIG & PAGE SETUP
# ═══════════════════════════════════════════════════════
st.set_page_config(
    page_title="Donia Pulse AI — Dashboard",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS — Dark theme with DONIA LABS brand colors
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
    
    :root {
        --donia-primary: #6C63FF;
        --donia-accent: #00D9A3;
        --donia-danger: #FF4757;
        --donia-warning: #FFA502;
        --donia-bg: #0D0F1A;
        --donia-card: #161826;
        --donia-border: #252840;
    }
    
    .stApp { background-color: var(--donia-bg); font-family: 'IBM Plex Sans Arabic', sans-serif; }
    
    .metric-card {
        background: var(--donia-card);
        border: 1px solid var(--donia-border);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        border-top: 3px solid var(--donia-primary);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--donia-accent);
        font-family: 'JetBrains Mono', monospace;
    }
    
    .metric-label { font-size: 0.85rem; color: #888; margin-top: 4px; }
    
    .status-active {
        background: rgba(0, 217, 163, 0.15);
        color: var(--donia-accent);
        border: 1px solid var(--donia-accent);
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .status-killed {
        background: rgba(255, 71, 87, 0.15);
        color: var(--donia-danger);
        border: 1px solid var(--donia-danger);
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
    }
    
    .status-expiring {
        background: rgba(255, 165, 2, 0.15);
        color: var(--donia-warning);
        border: 1px solid var(--donia-warning);
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
    }
    
    .kill-switch-banner {
        background: linear-gradient(135deg, #FF4757, #c0392b);
        color: white;
        padding: 15px 20px;
        border-radius: 10px;
        font-weight: 700;
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 20px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    .header-logo {
        font-size: 1.4rem;
        font-weight: 700;
        color: var(--donia-primary);
        letter-spacing: 1px;
    }
    
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: white;
        border-left: 3px solid var(--donia-primary);
        padding-left: 12px;
        margin: 20px 0 15px 0;
    }
    
    div[data-testid="stSidebar"] {
        background: var(--donia-card) !important;
        border-right: 1px solid var(--donia-border) !important;
    }
    
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }
    
    code { font-family: 'JetBrains Mono', monospace !important; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# FIREBASE INITIALIZATION
# ═══════════════════════════════════════════════════════
@st.cache_resource
def init_firebase():
    """Initialize Firebase Admin SDK. Called once and cached."""
    try:
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-service-account.json")
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"❌ Firebase connection failed: {e}")
        return None


def get_db():
    return init_firebase()


# ═══════════════════════════════════════════════════════
# AUTHENTICATION
# ═══════════════════════════════════════════════════════
def check_password():
    """Simple password gate for the dashboard."""
    if "authenticated" in st.session_state and st.session_state.authenticated:
        return True

    st.markdown("""
    <div style='text-align:center; padding: 60px 20px;'>
        <div style='font-size:3rem;'>🌐</div>
        <h1 style='color:#6C63FF; font-size:1.8rem;'>Donia Pulse AI</h1>
        <p style='color:#888;'>Management Dashboard — DONIA LABS TECH</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("🔑 Admin Password", type="password", placeholder="Enter your password")
        if st.button("🚀 Login", use_container_width=True):
            stored_hash = hashlib.sha256(
                os.getenv("ADMIN_PASSWORD", "donia2024!").encode()
            ).hexdigest()
            entered_hash = hashlib.sha256(password.encode()).hexdigest()
            if entered_hash == stored_hash:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Incorrect password")
    return False


# ═══════════════════════════════════════════════════════
# FIREBASE DATA FUNCTIONS
# ═══════════════════════════════════════════════════════
@st.cache_data(ttl=30)  # Cache for 30 seconds for performance
def get_all_clients():
    """Fetch all clients from Firebase."""
    db = get_db()
    if not db:
        return []
    try:
        docs = db.collection("clients").stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        st.error(f"Error fetching clients: {e}")
        return []


@st.cache_data(ttl=10)
def get_system_config():
    """Fetch global system config."""
    db = get_db()
    if not db:
        return {}
    try:
        doc = db.collection("system_config").document("global_settings").get()
        return doc.to_dict() if doc.exists else {}
    except:
        return {}


def update_client(client_id: str, updates: dict):
    """Update a specific client document in Firebase."""
    db = get_db()
    if not db:
        return False
    try:
        updates["meta.updated_at"] = datetime.utcnow().isoformat()
        db.collection("clients").document(client_id).update(updates)
        # Log the action
        log_audit(f"update_{list(updates.keys())[0]}", client_id, str(updates))
        get_all_clients.clear()  # Clear cache
        return True
    except Exception as e:
        st.error(f"Update failed: {e}")
        return False


def create_client(client_data: dict):
    """Add a new client to Firebase."""
    db = get_db()
    if not db:
        return False
    try:
        client_id = client_data["client_id"]
        db.collection("clients").document(client_id).set(client_data)
        log_audit("client_created", client_id, "New client onboarded")
        get_all_clients.clear()
        return True
    except Exception as e:
        st.error(f"Failed to create client: {e}")
        return False


def toggle_kill_switch(client_id: str, activate: bool, reason: str = ""):
    """Toggle the kill switch for a specific client."""
    updates = {
        "status.kill_switch": activate,
        "status.kill_switch_reason": reason if activate else None
    }
    return update_client(client_id, updates)


def toggle_global_kill_switch(activate: bool):
    """Toggle the GLOBAL kill switch — affects ALL clients."""
    db = get_db()
    if not db:
        return False
    try:
        db.collection("system_config").document("global_settings").update({
            "global_kill_switch": activate,
            "updated_at": datetime.utcnow().isoformat()
        })
        log_audit("GLOBAL_KILL_SWITCH", "ALL_CLIENTS",
                  f"Global kill switch {'ACTIVATED' if activate else 'DEACTIVATED'}")
        get_system_config.clear()
        return True
    except Exception as e:
        st.error(f"Failed to toggle global kill switch: {e}")
        return False


def log_audit(action: str, target: str, details: str):
    """Write an immutable audit log entry."""
    db = get_db()
    if db:
        try:
            db.collection("audit_logs").add({
                "timestamp":   datetime.utcnow().isoformat(),
                "admin_email": st.session_state.get("admin_email", "dashboard@donialabs.tech"),
                "action":      action,
                "target":      target,
                "details":     details
            })
        except:
            pass  # Non-critical


# ═══════════════════════════════════════════════════════
# UI COMPONENTS
# ═══════════════════════════════════════════════════════
def render_metric_card(label: str, value, delta=None, color="#6C63FF"):
    delta_html = f"<div style='color:{'#00D9A3' if str(delta or '').startswith('+') else '#FF4757'}; font-size:0.8rem;'>{delta}</div>" if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color:{color};">{value}</div>
        <div class="metric-label">{label}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_status_badge(client: dict) -> str:
    if client.get("status", {}).get("kill_switch"):
        return '<span class="status-killed">🔴 Kill Switch</span>'
    
    expiry = client.get("subscription", {}).get("expiry_date")
    if expiry:
        exp_dt = datetime.fromisoformat(expiry.replace("Z", "+00:00").replace("+00:00", ""))
        now = datetime.utcnow()
        if exp_dt < now:
            return '<span class="status-killed">⛔ Expired</span>'
        elif exp_dt < now + timedelta(hours=48):
            return '<span class="status-expiring">⚠️ Expiring Soon</span>'
    
    if client.get("status", {}).get("is_active"):
        return '<span class="status-active">✅ Active</span>'
    return '<span class="status-killed">⚫ Inactive</span>'


# ═══════════════════════════════════════════════════════
# PAGE: OVERVIEW DASHBOARD
# ═══════════════════════════════════════════════════════
def page_overview():
    clients = get_all_clients()
    sys_config = get_system_config()

    # Global Kill Switch Banner
    if sys_config.get("global_kill_switch"):
        st.markdown('<div class="kill-switch-banner">🚨 GLOBAL KILL SWITCH IS ACTIVE — All AI Agents are OFFLINE</div>',
                    unsafe_allow_html=True)

    st.markdown('<div class="section-title">📊 Platform Overview</div>', unsafe_allow_html=True)

    # KPI Metrics Row
    now = datetime.utcnow()
    active_clients = sum(1 for c in clients if c.get("status", {}).get("is_active") and not c.get("status", {}).get("kill_switch"))
    killed_clients = sum(1 for c in clients if c.get("status", {}).get("kill_switch"))
    expiring = sum(1 for c in clients if _is_expiring_soon(c))
    total_msgs = sum(c.get("analytics", {}).get("total_messages", 0) for c in clients)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: render_metric_card("Total Clients", len(clients), color="#6C63FF")
    with col2: render_metric_card("Active", active_clients, color="#00D9A3")
    with col3: render_metric_card("Kill Switch ON", killed_clients, color="#FF4757")
    with col4: render_metric_card("Expiring ≤48h", expiring, color="#FFA502")
    with col5: render_metric_card("Total Messages", f"{total_msgs:,}", color="#6C63FF")

    st.markdown("---")

    # Charts Row
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown('<div class="section-title">📈 Messages per Client</div>', unsafe_allow_html=True)
        if clients:
            chart_data = pd.DataFrame([{
                "Client": c.get("business_name", c.get("client_id", "?")),
                "Messages": c.get("analytics", {}).get("total_messages", 0)
            } for c in clients]).sort_values("Messages", ascending=False).head(10)

            fig = px.bar(chart_data, x="Client", y="Messages",
                         color="Messages",
                         color_continuous_scale=["#252840", "#6C63FF", "#00D9A3"],
                         template="plotly_dark")
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                margin=dict(l=0, r=0, t=0, b=0),
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown('<div class="section-title">🥧 Client Status Distribution</div>', unsafe_allow_html=True)
        if clients:
            status_counts = {"Active": active_clients, "Kill Switch": killed_clients,
                             "Expiring": expiring, "Inactive": len(clients) - active_clients - killed_clients}
            fig2 = go.Figure(data=[go.Pie(
                labels=list(status_counts.keys()),
                values=list(status_counts.values()),
                hole=0.6,
                marker_colors=["#00D9A3", "#FF4757", "#FFA502", "#555"]
            )])
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=True,
                margin=dict(l=0, r=0, t=0, b=0),
                height=300,
                legend=dict(font=dict(color="white"))
            )
            st.plotly_chart(fig2, use_container_width=True)

    # Subscription Expiry Timeline
    st.markdown('<div class="section-title">⏰ Subscription Expiry Timeline</div>', unsafe_allow_html=True)
    expiry_data = []
    for c in clients:
        exp = c.get("subscription", {}).get("expiry_date")
        if exp:
            try:
                exp_dt = datetime.fromisoformat(exp.replace("Z", ""))
                days_left = (exp_dt - now).days
                expiry_data.append({
                    "Client": c.get("business_name", c.get("client_id")),
                    "Days Left": days_left,
                    "Expiry Date": exp_dt.strftime("%Y-%m-%d")
                })
            except:
                pass

    if expiry_data:
        df = pd.DataFrame(expiry_data).sort_values("Days Left")
        fig3 = px.bar(df, x="Client", y="Days Left", color="Days Left",
                      color_continuous_scale=["#FF4757", "#FFA502", "#00D9A3"],
                      text="Expiry Date",
                      template="plotly_dark")
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           height=280, margin=dict(l=0, r=0, t=0, b=0))
        fig3.add_hline(y=0, line_dash="dash", line_color="#FF4757", annotation_text="Expired")
        fig3.add_hline(y=2, line_dash="dot", line_color="#FFA502", annotation_text="48h Alert")
        st.plotly_chart(fig3, use_container_width=True)


# ═══════════════════════════════════════════════════════
# PAGE: CLIENT MANAGEMENT
# ═══════════════════════════════════════════════════════
def page_clients():
    st.markdown('<div class="section-title">👥 Client Management</div>', unsafe_allow_html=True)
    clients = get_all_clients()

    # Search & Filter
    col_search, col_filter = st.columns([3, 1])
    with col_search:
        search = st.text_input("🔍 Search clients", placeholder="Business name, ID, sector...")
    with col_filter:
        status_filter = st.selectbox("Filter", ["All", "Active", "Kill Switch", "Expiring", "Expired"])

    # Filter logic
    filtered = clients
    if search:
        q = search.lower()
        filtered = [c for c in filtered if
                    q in c.get("business_name", "").lower() or
                    q in c.get("client_id", "").lower() or
                    q in c.get("business_sector", "").lower()]

    if status_filter == "Active":
        filtered = [c for c in filtered if c.get("status", {}).get("is_active") and not c.get("status", {}).get("kill_switch")]
    elif status_filter == "Kill Switch":
        filtered = [c for c in filtered if c.get("status", {}).get("kill_switch")]
    elif status_filter == "Expiring":
        filtered = [c for c in filtered if _is_expiring_soon(c)]
    elif status_filter == "Expired":
        filtered = [c for c in filtered if _is_expired(c)]

    st.markdown(f"**{len(filtered)}** clients found")
    st.markdown("---")

    # Client Cards
    for i, client in enumerate(filtered):
        with st.expander(f"🏢 {client.get('business_name', 'N/A')}  |  `{client.get('client_id', 'N/A')}`  |  {render_status_badge(client)}", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**📋 General Info**")
                st.write(f"**Sector:** {client.get('business_sector', 'N/A')}")
                st.write(f"**Email:** {client.get('contact_email', 'N/A')}")
                st.write(f"**Phone:** {client.get('contact_phone', 'N/A')}")

            with col2:
                st.markdown("**🤖 AI Config**")
                ai = client.get("ai_config", {})
                st.write(f"**Model:** `{ai.get('model', 'N/A')}`")
                st.write(f"**Language Mode:** `{ai.get('language_mode', 'auto')}`")
                lang = ai.get("forced_language") or "Auto-detect"
                st.write(f"**Language:** `{lang}`")
                st.write(f"**Temperature:** `{ai.get('temperature', 0.7)}`")

            with col3:
                st.markdown("**📅 Subscription**")
                sub = client.get("subscription", {})
                st.write(f"**Plan:** `{sub.get('plan', 'N/A')}`")
                st.write(f"**Status:** `{sub.get('status', 'N/A')}`")
                exp = sub.get("expiry_date", "N/A")
                st.write(f"**Expires:** `{exp[:10] if exp != 'N/A' else 'N/A'}`")

            st.markdown("---")

            # Action Buttons
            btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)

            with btn_col1:
                kill_active = client.get("status", {}).get("kill_switch", False)
                if kill_active:
                    if st.button("✅ Restore Service", key=f"restore_{i}", type="primary"):
                        if toggle_kill_switch(client["client_id"], False):
                            st.success("✅ Kill switch deactivated!")
                            st.rerun()
                else:
                    if st.button("🔴 Kill Switch ON", key=f"kill_{i}", type="secondary"):
                        reason = st.text_input("Reason:", key=f"reason_{i}", placeholder="e.g., Payment overdue")
                        if st.button("Confirm", key=f"confirm_kill_{i}"):
                            if toggle_kill_switch(client["client_id"], True, reason):
                                st.success("Kill switch activated")
                                st.rerun()

            with btn_col2:
                if st.button("📅 Extend Subscription", key=f"extend_{i}"):
                    st.session_state[f"extend_client"] = client["client_id"]

            with btn_col3:
                if st.button("🌍 Change Language", key=f"lang_{i}"):
                    st.session_state[f"lang_client"] = client["client_id"]

            with btn_col4:
                msgs = client.get("analytics", {}).get("total_messages", 0)
                st.metric("Messages", f"{msgs:,}")

            # Extend Subscription Panel
            if st.session_state.get("extend_client") == client["client_id"]:
                with st.form(f"extend_form_{i}"):
                    st.markdown("**📅 Extend Subscription**")
                    new_expiry = st.date_input("New Expiry Date",
                                               value=datetime.utcnow() + timedelta(days=30))
                    if st.form_submit_button("✅ Confirm Extension"):
                        if update_client(client["client_id"], {
                            "subscription.expiry_date": new_expiry.isoformat() + "T23:59:59Z",
                            "subscription.status": "active",
                            "subscription.alert_sent": False
                        }):
                            st.success(f"✅ Subscription extended to {new_expiry}")
                            del st.session_state["extend_client"]
                            st.rerun()

            # Language Override Panel
            if st.session_state.get("lang_client") == client["client_id"]:
                with st.form(f"lang_form_{i}"):
                    st.markdown("**🌍 Language Settings**")
                    lang_mode = st.radio("Mode", ["auto", "manual"], horizontal=True)
                    forced_lang = st.selectbox("Forced Language", ["ar", "fr", "en"]) if lang_mode == "manual" else None
                    if st.form_submit_button("✅ Save Language"):
                        if update_client(client["client_id"], {
                            "ai_config.language_mode": lang_mode,
                            "ai_config.forced_language": forced_lang
                        }):
                            st.success("✅ Language settings updated!")
                            del st.session_state["lang_client"]
                            st.rerun()


# ═══════════════════════════════════════════════════════
# PAGE: ADD NEW CLIENT
# ═══════════════════════════════════════════════════════
def page_add_client():
    st.markdown('<div class="section-title">➕ Onboard New Client</div>', unsafe_allow_html=True)
    st.info("ℹ️ Fill in the required fields. The client will be live immediately after submission.")

    with st.form("new_client_form"):
        st.markdown("#### 📋 Business Information")
        col1, col2 = st.columns(2)
        with col1:
            client_id = st.text_input("Client ID *", placeholder="e.g., boutique_oran_01")
            business_name = st.text_input("Business Name *", placeholder="e.g., بوتيك وهران")
        with col2:
            business_sector = st.selectbox("Sector", ["e-commerce", "restaurant", "hotel", "healthcare", "education", "real_estate", "other"])
            contact_email = st.text_input("Contact Email *", placeholder="owner@business.dz")

        st.markdown("#### 📱 WhatsApp Configuration")
        col3, col4 = st.columns(2)
        with col3:
            phone_number_id = st.text_input("Phone Number ID *", placeholder="From Meta Business Manager")
            waba_id = st.text_input("WABA ID *", placeholder="WhatsApp Business Account ID")
        with col4:
            access_token = st.text_input("Access Token *", type="password", placeholder="EAAxxxx...")
            verify_token = st.text_input("Webhook Verify Token *", placeholder="Your custom verify token")

        st.markdown("#### 🤖 AI Configuration")
        col5, col6 = st.columns(2)
        with col5:
            model = st.selectbox("AI Model", ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"])
            lang_mode = st.radio("Language Mode", ["auto", "manual"], horizontal=True)
            forced_lang = st.selectbox("Forced Language", ["ar", "fr", "en"]) if lang_mode == "manual" else None
        with col6:
            temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1)
            max_tokens = st.slider("Max Tokens", 256, 4096, 1024, 128)

        brand_name = st.text_input("Brand Name", placeholder="Same as business name or custom")
        system_prompt = st.text_area("System Prompt *",
                                      height=150,
                                      placeholder="أنت مساعد ذكي لـ [اسم المتجر]. أجب بأسلوب احترافي وودود...")

        st.markdown("#### 📅 Subscription")
        col7, col8 = st.columns(2)
        with col7:
            plan = st.selectbox("Plan", ["basic", "standard", "premium"])
            start_date = st.date_input("Start Date", value=datetime.utcnow())
        with col8:
            expiry_date = st.date_input("Expiry Date", value=datetime.utcnow() + timedelta(days=30))

        st.markdown("#### 🛡️ Safety")
        blocked_topics = st.multiselect("Blocked Topics",
                                         ["politics", "religion", "adult_content", "violence"],
                                         default=["politics", "religion", "adult_content", "violence"])

        submitted = st.form_submit_button("🚀 Create Client & Go Live", type="primary", use_container_width=True)

        if submitted:
            if not all([client_id, business_name, phone_number_id, waba_id, access_token, system_prompt]):
                st.error("❌ Please fill all required (*) fields")
            else:
                client_data = {
                    "client_id": client_id.strip().lower().replace(" ", "_"),
                    "business_name": business_name,
                    "business_sector": business_sector,
                    "contact_email": contact_email,
                    "contact_phone": "",
                    "whatsapp_config": {
                        "phone_number_id": phone_number_id,
                        "waba_id": waba_id,
                        "access_token": access_token,
                        "webhook_verify_token": verify_token
                    },
                    "subscription": {
                        "plan": plan,
                        "status": "active",
                        "start_date": start_date.isoformat() + "T00:00:00Z",
                        "expiry_date": expiry_date.isoformat() + "T23:59:59Z",
                        "auto_alert_48h": True,
                        "alert_sent": False
                    },
                    "ai_config": {
                        "language_mode": lang_mode,
                        "forced_language": forced_lang,
                        "model": model,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "system_prompt": system_prompt,
                        "brand_name": brand_name or business_name,
                        "brand_tone": "friendly_professional"
                    },
                    "safety_config": {
                        "guardrails_enabled": True,
                        "blocked_topics": blocked_topics,
                        "custom_blocked_words": [],
                        "fallback_message": {
                            "ar": "عذراً، لا يمكنني الإجابة على هذا السؤال.",
                            "fr": "Désolé, je ne peux pas répondre à cette question.",
                            "en": "Sorry, I cannot answer this question."
                        }
                    },
                    "analytics": {"total_messages": 0, "messages_today": 0, "avg_response_time_ms": 0, "last_activity": None},
                    "status": {"is_active": True, "kill_switch": False, "kill_switch_reason": None, "maintenance_mode": False},
                    "meta": {
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                        "created_by": "dashboard",
                        "notes": ""
                    }
                }
                if create_client(client_data):
                    st.success(f"✅ Client **{business_name}** created successfully! They are now LIVE.")
                    st.balloons()


# ═══════════════════════════════════════════════════════
# PAGE: SECURITY & GLOBAL SETTINGS
# ═══════════════════════════════════════════════════════
def page_security():
    st.markdown('<div class="section-title">🔐 Security & Global Controls</div>', unsafe_allow_html=True)
    sys_config = get_system_config()

    # GLOBAL KILL SWITCH
    st.markdown("### 🚨 Global Kill Switch")
    gks_active = sys_config.get("global_kill_switch", False)

    if gks_active:
        st.markdown('<div class="kill-switch-banner">🚨 GLOBAL KILL SWITCH IS CURRENTLY ACTIVE — ALL AGENTS OFFLINE</div>',
                    unsafe_allow_html=True)
        if st.button("✅ DEACTIVATE GLOBAL KILL SWITCH", type="primary", use_container_width=True):
            if toggle_global_kill_switch(False):
                st.success("✅ All AI agents are back ONLINE")
                st.rerun()
    else:
        st.success("✅ System is OPERATIONAL — All agents online")
        with st.expander("⚠️ Activate Global Kill Switch"):
            st.warning("**WARNING:** This will immediately stop ALL AI agents for ALL clients.")
            reason = st.text_input("Reason for activation *", placeholder="e.g., Emergency maintenance")
            if st.button("🔴 ACTIVATE GLOBAL KILL SWITCH", type="secondary"):
                if reason:
                    if toggle_global_kill_switch(True):
                        st.error("🚨 GLOBAL KILL SWITCH ACTIVATED — All agents are now OFFLINE")
                        st.rerun()
                else:
                    st.error("Please provide a reason")

    st.markdown("---")

    # AUDIT LOGS
    st.markdown("### 📋 Audit Logs")
    db = get_db()
    if db:
        try:
            logs = db.collection("audit_logs").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(50).stream()
            log_data = [l.to_dict() for l in logs]
            if log_data:
                df_logs = pd.DataFrame(log_data)[["timestamp", "admin_email", "action", "target", "details"]]
                st.dataframe(df_logs, use_container_width=True, height=400)
            else:
                st.info("No audit logs yet.")
        except Exception as e:
            st.error(f"Could not fetch logs: {e}")


# ═══════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════
def _is_expiring_soon(client: dict) -> bool:
    exp = client.get("subscription", {}).get("expiry_date")
    if not exp:
        return False
    try:
        exp_dt = datetime.fromisoformat(exp.replace("Z", ""))
        now = datetime.utcnow()
        return now < exp_dt < now + timedelta(hours=48)
    except:
        return False


def _is_expired(client: dict) -> bool:
    exp = client.get("subscription", {}).get("expiry_date")
    if not exp:
        return False
    try:
        return datetime.fromisoformat(exp.replace("Z", "")) < datetime.utcnow()
    except:
        return False


# ═══════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ═══════════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="header-logo">🌐 Donia Pulse AI</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:#888; font-size:0.75rem; margin-bottom:20px;">DONIA LABS TECH — v1.0</div>',
                    unsafe_allow_html=True)
        st.markdown("---")

        page = st.radio("Navigation", [
            "📊 Overview",
            "👥 Clients",
            "➕ Add Client",
            "🔐 Security"
        ], label_visibility="hidden")

        st.markdown("---")

        # Auto-refresh toggle
        auto_refresh = st.toggle("🔄 Auto Refresh (30s)", value=False)
        if auto_refresh:
            time.sleep(30)
            st.rerun()

        # Logout
        if st.button("🚪 Logout", use_container_width=True):
            del st.session_state["authenticated"]
            st.rerun()

        st.markdown("---")
        st.markdown('<div style="color:#555; font-size:0.7rem; text-align:center;">© 2025 DONIA LABS TECH</div>',
                    unsafe_allow_html=True)

    return page


# ═══════════════════════════════════════════════════════
# MAIN APP ENTRY POINT
# ═══════════════════════════════════════════════════════
def main():
    if not check_password():
        return

    page = render_sidebar()

    if page == "📊 Overview":
        page_overview()
    elif page == "👥 Clients":
        page_clients()
    elif page == "➕ Add Client":
        page_add_client()
    elif page == "🔐 Security":
        page_security()


if __name__ == "__main__":
    main()
