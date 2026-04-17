"""
utils/styles.py
Estilos CSS globales inyectados en Streamlit via st.markdown.
Reproduce la paleta y el look del mockup HTML (TutorIA.html).
"""

MAIN_CSS = """
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,400;14..32,500;14..32,600;14..32,700&display=swap');

/* ── Variables de color ── */
:root {
    --navy:    #1e3a5f;
    --blue:    #2c7da0;
    --blue-lt: #a8d5e2;
    --bg:      #f0f4ff;
    --bg2:     #f8fafc;
    --card:    #ffffff;
    --border:  #e2e8f0;
    --text:    #0f2b3d;
    --muted:   #5b6e8c;
    --green:   #2b7e3a;
    --green-lt:#e0f2e9;
    --red-lt:  #ffe6e6;
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* ── Fondo principal ── */
.stApp {
    background: linear-gradient(135deg, #f0f4ff 0%, #e6edf7 100%) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--navy) !important;
}
[data-testid="stSidebar"] * {
    color: #ffffff !important;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label {
    color: rgba(255,255,255,0.7) !important;
    font-size: 0.8rem;
}

/* ── Cards ── */
.tutoria-card {
    background: var(--card);
    border-radius: 20px;
    padding: 1.4rem 1.6rem;
    box-shadow: 0 4px 18px rgba(0,0,0,0.06);
    border: 1px solid var(--border);
    margin-bottom: 1rem;
}
.tutoria-card h3 {
    color: var(--navy);
    font-size: 1rem;
    font-weight: 600;
    border-left: 4px solid var(--blue);
    padding-left: 10px;
    margin-bottom: 0.8rem;
}

/* ── Badges ── */
.badge-green {
    background: var(--green-lt);
    color: var(--green);
    padding: 3px 10px;
    border-radius: 50px;
    font-size: 0.72rem;
    font-weight: 600;
}
.badge-blue {
    background: #eef2ff;
    color: var(--navy);
    padding: 3px 10px;
    border-radius: 50px;
    font-size: 0.72rem;
    font-weight: 600;
}
.badge-red {
    background: var(--red-lt);
    color: #c0392b;
    padding: 3px 10px;
    border-radius: 50px;
    font-size: 0.72rem;
    font-weight: 600;
}
.badge-gray {
    background: #f1f5f9;
    color: #475569;
    padding: 3px 10px;
    border-radius: 50px;
    font-size: 0.72rem;
    font-weight: 600;
}

/* ── Header del dashboard ── */
.dash-header {
    background: white;
    border-radius: 16px;
    padding: 1rem 1.6rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    border: 1px solid var(--border);
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.dash-header h2 {
    color: var(--navy);
    font-size: 1.3rem;
    margin: 0;
}
.dash-header .role-tag {
    background: #eef2ff;
    color: var(--navy);
    padding: 4px 12px;
    border-radius: 30px;
    font-size: 0.8rem;
    font-weight: 500;
    margin-left: 10px;
}

/* ── Metric cards ── */
.metric-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.metric-box {
    background: white;
    border-radius: 16px;
    padding: 1rem 1.2rem;
    text-align: center;
    border: 1px solid var(--border);
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.metric-box .num {
    font-size: 2rem;
    font-weight: 700;
    color: var(--navy);
}
.metric-box .lbl {
    font-size: 0.75rem;
    color: var(--muted);
    margin-top: 2px;
}

/* ── Tabla de historial ── */
.hist-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}
.hist-table th {
    text-align: left;
    padding: 8px 6px;
    border-bottom: 2px solid var(--border);
    color: var(--muted);
    font-weight: 500;
}
.hist-table td {
    padding: 10px 6px;
    border-bottom: 1px solid var(--border);
    color: var(--text);
    vertical-align: middle;
}

/* ── Availability items ── */
.avail-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid #edf2f7;
}
.avail-item:last-child { border-bottom: none; }
.avail-item strong { color: var(--navy); }
.avail-item small  { color: var(--muted); font-size: 0.78rem; }

/* ── Mensaje info/success/error ── */
.msg-success {
    background: var(--green-lt);
    color: var(--green);
    border-radius: 12px;
    padding: 10px 14px;
    font-size: 0.85rem;
    margin-top: 0.6rem;
}
.msg-error {
    background: var(--red-lt);
    color: #c0392b;
    border-radius: 12px;
    padding: 10px 14px;
    font-size: 0.85rem;
    margin-top: 0.6rem;
}

/* ── Botones Streamlit ── */
.stButton > button {
    border-radius: 40px !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="primary"] {
    background: var(--blue) !important;
    border: none !important;
}
.stButton > button[kind="primary"]:hover {
    background: #1f5e7a !important;
    transform: translateY(-1px);
}

/* ── Inputs ── */
.stTextInput input, .stSelectbox div[data-baseweb],
.stDateInput input, .stTimeInput input {
    border-radius: 12px !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 30px !important;
    font-weight: 500;
    color: var(--muted) !important;
}
.stTabs [aria-selected="true"] {
    background: var(--navy) !important;
    color: white !important;
}

/* ── Login brand panel ── */
.login-brand {
    background: var(--navy);
    border-radius: 20px;
    padding: 2.5rem;
    color: white;
}
.login-brand h1 {
    font-size: 1.8rem;
    font-weight: 700;
    margin-bottom: 0.8rem;
}
.login-brand p {
    opacity: 0.85;
    line-height: 1.6;
    font-size: 0.92rem;
}
.login-brand .feature {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 0.6rem;
    font-size: 0.85rem;
    opacity: 0.9;
}
</style>
"""


def inject_css():
    """Inyecta los estilos globales en la app."""
    import streamlit as st
    st.markdown(MAIN_CSS, unsafe_allow_html=True)


def badge(text: str, color: str = "blue") -> str:
    """Retorna HTML de un badge coloreado."""
    return f'<span class="badge-{color}">{text}</span>'


ESTADO_COLOR = {
    "Programada": "blue",
    "Completada": "green",
    "Cancelada": "red",
    "No asistió": "gray",
}


def estado_badge(estado: str) -> str:
    return badge(estado, ESTADO_COLOR.get(estado, "gray"))
