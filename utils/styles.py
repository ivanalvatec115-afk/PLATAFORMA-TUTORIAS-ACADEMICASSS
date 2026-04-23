"""
utils/styles.py — Plataforma de Tutorías Académicas - ITMH
"""

MAIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800&display=swap');

:root {
    --navy:      #0d2137;
    --navy-mid:  #163352;
    --blue:      #1a6fa8;
    --blue-lt:   #d0e8f7;
    --card:      #ffffff;
    --border:    #cdd8e3;
    --text:      #0d1f2d;
    --text-soft: #3d5166;
    --muted:     #5a7080;
    --green:     #155f2e;
    --green-bg:  #d4edda;
    --red:       #8b1a1a;
    --red-bg:    #fde8e8;
    --orange:    #7a3a00;
    --orange-bg: #fdecd3;
    --gray-bg:   #e9ecef;
    --gray-txt:  #3a3f45;
}

html, body, [class*="css"] {
    font-family: 'Nunito', sans-serif !important;
}

.stApp {
    background: linear-gradient(150deg, #dce8f5 0%, #eef2f7 60%, #e0eaf4 100%) !important;
}

/* ══════════════════════════════════════════════════════
   REGLA MAESTRA: TODO dentro de fondo oscuro = BLANCO
   Se aplica a sidebar, dash-header, metric-box y login-brand
   ══════════════════════════════════════════════════════ */
[data-testid="stSidebar"] *,
.dash-header *,
.metric-box *,
.login-brand * {
    color: #ffffff !important;
}

/* ── Excepciones dentro de fondos oscuros ── */
.dash-header .role-tag {
    background: rgba(255,255,255,0.18) !important;
    color: #d0e8f7 !important;
    padding: 3px 12px;
    border-radius: 30px;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    margin-left: 8px;
    border: 1px solid rgba(255,255,255,0.28);
}
.dash-header .user-info-txt * {
    color: #a8c8e8 !important;
}
.metric-box .lbl * {
    color: #a8c8e8 !important;
}
.login-brand p * {
    color: #ffffff !important;
}
.login-brand .feature * {
    color: #d0e8f7 !important;
}

/* ══════════════════════════════════
   SIDEBAR
   ══════════════════════════════════ */
[data-testid="stSidebar"] {
    background: var(--navy) !important;
    border-right: 3px solid var(--blue) !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.15) !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.1) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    font-weight: 700 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.22) !important;
}
[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    background: #ffffff !important;
    color: #0d2137 !important;
    border: none !important;
    font-weight: 700 !important;
}
[data-testid="stSidebar"] .stButton > button[kind="secondary"] * {
    color: #0d2137 !important;
}
[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
    background: #e8f0f7 !important;
}

/* ══════════════════════════════════
   DASH HEADER
   ══════════════════════════════════ */
.dash-header {
    background: var(--navy);
    border-radius: 14px;
    padding: 1rem 1.8rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 16px rgba(13,33,55,0.20);
}

/* ══════════════════════════════════
   METRIC BOXES
   ══════════════════════════════════ */
.metric-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.metric-box {
    background: var(--navy);
    border-radius: 14px;
    padding: 1.1rem 1rem;
    text-align: center;
    box-shadow: 0 3px 12px rgba(13,33,55,0.18);
}
.metric-box .num {
    font-size: 2.2rem;
    font-weight: 800;
    line-height: 1;
    display: block;
}
.metric-box .lbl {
    font-size: 0.73rem;
    margin-top: 5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    display: block;
    color: #a8c8e8 !important;
}

/* ══════════════════════════════════
   LOGIN BRAND
   ══════════════════════════════════ */
.login-brand {
    background: linear-gradient(145deg, var(--navy) 0%, var(--navy-mid) 100%);
    border-radius: 20px;
    padding: 2.8rem;
    box-shadow: 0 8px 32px rgba(13,33,55,0.25);
    min-height: 420px;
}
.login-brand h1 {
    font-size: 2.4rem;
    font-weight: 800;
    margin-bottom: 1rem;
    letter-spacing: -0.02em;
}
.login-brand p {
    line-height: 1.7;
    font-size: 0.95rem;
    font-weight: 500;
}
.login-brand .feature {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 0.8rem;
    font-size: 0.88rem;
    font-weight: 600;
}

/* ══════════════════════════════════
   CARDS (fondo blanco — texto oscuro)
   ══════════════════════════════════ */
.tutoria-card {
    background: var(--card);
    border-radius: 16px;
    padding: 1.5rem 1.6rem;
    box-shadow: 0 2px 12px rgba(13,33,55,0.08);
    border: 1px solid var(--border);
    margin-bottom: 1.2rem;
}
.tutoria-card h3 {
    color: var(--navy) !important;
    font-size: 1rem;
    font-weight: 700;
    border-left: 4px solid var(--blue);
    padding-left: 10px;
    margin-bottom: 1rem;
}

/* ── Login form box ── */
.login-box {
    background: white;
    border-radius: 16px;
    padding: 2rem 2rem 1rem;
    box-shadow: 0 4px 20px rgba(13,33,55,0.10);
    border: 1px solid var(--border);
    margin-bottom: 1rem;
}
.login-box h2 { color: var(--navy) !important; font-size: 1.6rem; font-weight: 800; }
.login-box p  { color: var(--text-soft) !important; font-size: 0.9rem; font-weight: 500; }

.login-note {
    background: var(--blue-lt);
    color: var(--navy-mid) !important;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 0.83rem;
    font-weight: 700;
    margin-top: 1rem;
    border: 1px solid #8bbcd8;
}

/* ══════════════════════════════════
   BADGES
   ══════════════════════════════════ */
.badge-green { background: var(--green-bg); color: var(--green) !important; padding: 4px 12px; border-radius: 50px; font-size: 0.75rem; font-weight: 700; border: 1px solid #a3d4b0; }
.badge-blue  { background: var(--blue-lt);  color: var(--navy) !important;  padding: 4px 12px; border-radius: 50px; font-size: 0.75rem; font-weight: 700; border: 1px solid #8bbcd8; }
.badge-red   { background: var(--red-bg);   color: var(--red) !important;   padding: 4px 12px; border-radius: 50px; font-size: 0.75rem; font-weight: 700; border: 1px solid #f0b0b0; }
.badge-gray  { background: var(--orange-bg);color: var(--orange) !important;padding: 4px 12px; border-radius: 50px; font-size: 0.75rem; font-weight: 700; border: 1px solid #f0c898; }

/* ══════════════════════════════════
   TABLA HISTORIAL
   ══════════════════════════════════ */
.hist-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
.hist-table th {
    text-align: left; padding: 10px 8px;
    border-bottom: 2px solid var(--border);
    color: var(--navy) !important; font-weight: 800;
    font-size: 0.78rem; text-transform: uppercase;
    letter-spacing: 0.05em; background: #e8f0f8;
}
.hist-table td {
    padding: 11px 8px; border-bottom: 1px solid #dde6ef;
    color: var(--text) !important; font-weight: 600; vertical-align: middle;
}
.hist-table tr:hover td { background: #f0f6fb; }

/* ── Availability items ── */
.avail-item {
    display: flex; justify-content: space-between;
    align-items: center; padding: 12px 0;
    border-bottom: 1px solid #dde6ef;
}
.avail-item:last-child { border-bottom: none; }
.avail-item strong { color: var(--navy) !important; font-weight: 700; font-size: 0.92rem; }
.avail-item small  { color: var(--text-soft) !important; font-size: 0.8rem; font-weight: 600; }

/* ══════════════════════════════════
   INPUTS Y LABELS (área clara)
   ══════════════════════════════════ */
.stTextInput label, .stSelectbox label, .stDateInput label,
.stTimeInput label, .stTextArea label, .stRadio label,
.stToggle label, .stCheckbox label {
    color: var(--navy) !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
}
.stTextInput input, .stTextArea textarea {
    border-radius: 10px !important;
    border: 1.5px solid var(--border) !important;
    color: var(--text) !important;
    background: #f8fbff !important;
    font-weight: 600 !important;
}
.stRadio div[role="radiogroup"] label p { color: var(--text) !important; font-weight: 600 !important; }

/* ══════════════════════════════════
   BOTONES
   ══════════════════════════════════ */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-family: 'Nunito', sans-serif !important;
    font-size: 0.92rem !important;
    transition: all 0.18s ease !important;
}
.stButton > button[kind="primary"] {
    background: var(--blue) !important; color: #ffffff !important;
    border: none !important; box-shadow: 0 3px 10px rgba(26,111,168,0.30) !important;
}
.stButton > button[kind="primary"]:hover { background: var(--navy) !important; transform: translateY(-1px); }
.stButton > button[kind="secondary"] { background: var(--gray-bg) !important; color: var(--gray-txt) !important; border: 1.5px solid var(--border) !important; }

/* ══════════════════════════════════
   TABS
   ══════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] { gap: 0.4rem; background: #dce8f5; border-radius: 10px; padding: 4px; }
.stTabs [data-baseweb="tab"] { border-radius: 8px !important; font-weight: 700 !important; font-size: 0.85rem !important; color: var(--navy-mid) !important; padding: 6px 16px !important; }
.stTabs [aria-selected="true"] { background: var(--navy) !important; box-shadow: 0 2px 8px rgba(13,33,55,0.2) !important; }
.stTabs [aria-selected="true"] * { color: #ffffff !important; }

/* ══════════════════════════════════
   SELECTBOX
   ══════════════════════════════════ */
div[data-baseweb="select"] > div { border-radius: 10px !important; border: 1.5px solid var(--border) !important; background: #f8fbff !important; }
div[data-baseweb="select"] span, div[data-baseweb="select"] div { color: var(--text) !important; font-weight: 600 !important; }

/* ══════════════════════════════════
   EXPANDER
   ══════════════════════════════════ */
[data-testid="stExpander"] { border: 1px solid var(--border) !important; border-radius: 10px !important; background: white !important; }
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span { color: var(--navy) !important; font-weight: 700 !important; }

/* ══════════════════════════════════
   FORM, DIVIDER, CAPTION, MARKDOWN
   ══════════════════════════════════ */
[data-testid="stForm"] { border: 1.5px solid var(--border) !important; border-radius: 14px !important; padding: 1rem !important; background: #f4f8fc !important; }
hr { border-color: var(--border) !important; }
.stCaption, [data-testid="stCaptionContainer"] * { color: var(--muted) !important; font-weight: 600 !important; }
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 { color: var(--navy) !important; font-weight: 800 !important; }
.stMarkdown p { color: var(--text) !important; font-weight: 500; }

/* ── Fuerza blanco en el párrafo del login brand (override Streamlit) ── */
div.login-brand p,
div.login-brand > p,
.login-brand p,
[data-testid="stMarkdownContainer"] .login-brand p,
.stMarkdown .login-brand p {
    color: #ffffff !important;
}


/* ── Scroll en tabs con muchos expanders ── */
.stTabs [data-baseweb="tab-panel"] {
    max-height: 520px;
    overflow-y: auto;
    padding-right: 4px;
}
.stTabs [data-baseweb="tab-panel"]::-webkit-scrollbar {
    width: 6px;
}
.stTabs [data-baseweb="tab-panel"]::-webkit-scrollbar-track {
    background: #f0f4ff;
    border-radius: 10px;
}
.stTabs [data-baseweb="tab-panel"]::-webkit-scrollbar-thumb {
    background: #1a6fa8;
    border-radius: 10px;
}


/* ── Ocultar navegación automática de páginas de Streamlit ── */
[data-testid="stSidebarNav"] {
    display: none !important;
}

</style>
"""


def inject_css():
    import streamlit as st
    st.markdown(MAIN_CSS, unsafe_allow_html=True)


def badge(text: str, color: str = "blue") -> str:
    return f'<span class="badge-{color}">{text}</span>'


ESTADO_COLOR = {
    "Programada":  "blue",
    "Completada":  "green",
    "Cancelada":   "red",
    "No asistió":  "gray",
}


def estado_badge(estado: str) -> str:
    return badge(estado, ESTADO_COLOR.get(estado, "gray"))
