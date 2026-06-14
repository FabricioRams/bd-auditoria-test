"""
Estilos globales compartidos para todas las páginas de la app de auditoría.
"""

GLOBAL_CSS = """
<style>
/* ===== FUENTES ===== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

/* ===== VARIABLES ===== */
:root {
    --bg-base:       #0a0e1a;
    --bg-surface:    #0f1628;
    --bg-card:       #141d35;
    --bg-card-hover: #192040;
    --border:        #1e2d4d;
    --border-bright: #2a3f6f;
    --accent:        #3b82f6;
    --accent-glow:   #3b82f640;
    --accent-2:      #06b6d4;
    --success:       #10b981;
    --warning:       #f59e0b;
    --danger:        #ef4444;
    --text-primary:  #e2e8f0;
    --text-secondary:#94a3b8;
    --text-muted:    #475569;
    --font-mono:     'JetBrains Mono', monospace;
    --font-sans:     'Inter', sans-serif;
    --radius:        8px;
    --radius-lg:     12px;
}

/* ===== BASE ===== */
html, body, [class*="css"] {
    font-family: var(--font-sans) !important;
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
}

/* Fondo principal */
.stApp {
    background-color: var(--bg-base) !important;
    background-image: radial-gradient(ellipse at 20% 0%, #1e2d4d22 0%, transparent 60%),
                      radial-gradient(ellipse at 80% 10%, #0e2a4422 0%, transparent 50%);
}

/* ===== SIDEBAR ===== */
[data-testid="stSidebar"] {
    background-color: var(--bg-surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * {
    color: var(--text-primary) !important;
}
[data-testid="stSidebarNav"] a {
    border-radius: var(--radius) !important;
    margin: 2px 0 !important;
    padding: 8px 12px !important;
    transition: background 0.15s ease !important;
}
[data-testid="stSidebarNav"] a:hover {
    background: var(--bg-card-hover) !important;
}
[data-testid="stSidebarNav"] a[aria-selected="true"] {
    background: var(--accent-glow) !important;
    border-left: 2px solid var(--accent) !important;
}

/* ===== HEADERS (ocultar anclas) ===== */
h1 a, h2 a, h3 a, h4 a, h5 a, h6 a { display: none !important; }

h1 { 
    font-size: 1.75rem !important; 
    font-weight: 700 !important; 
    color: var(--text-primary) !important;
    letter-spacing: -0.02em !important;
}
h2 { font-size: 1.35rem !important; font-weight: 600 !important; color: var(--text-primary) !important; }
h3 { font-size: 1.1rem !important; font-weight: 600 !important; color: var(--text-secondary) !important; }

/* ===== BOTONES ===== */
.stButton > button {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius) !important;
    font-family: var(--font-sans) !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.5rem 1.25rem !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 0 0 0 var(--accent-glow) !important;
}
.stButton > button:hover {
    filter: brightness(1.15) !important;
    box-shadow: 0 0 20px var(--accent-glow) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-bright) !important;
    color: var(--text-secondary) !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    box-shadow: none !important;
}

/* ===== INPUTS ===== */
.stTextInput input,
.stTextArea textarea,
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-sans) !important;
    transition: border-color 0.15s !important;
}
.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
    outline: none !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label, .stMultiSelect label {
    color: var(--text-secondary) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
}

/* ===== FORMS ===== */
[data-testid="stForm"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1.5rem !important;
}

/* ===== EXPANDER ===== */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] summary {
    background: var(--bg-card) !important;
    padding: 0.875rem 1rem !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    letter-spacing: 0.02em !important;
}
[data-testid="stExpander"] summary:hover {
    background: var(--bg-card-hover) !important;
}

/* ===== TABS ===== */
[data-testid="stTabs"] [role="tablist"] {
    background: var(--bg-card) !important;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0 !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
    padding: 0.25rem !important;
}
[data-testid="stTabs"] [role="tab"] {
    background: transparent !important;
    border-radius: var(--radius) !important;
    color: var(--text-muted) !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    padding: 0.5rem 1rem !important;
    border: none !important;
    transition: all 0.15s ease !important;
}
[data-testid="stTabs"] [role="tab"]:hover {
    color: var(--text-secondary) !important;
    background: var(--bg-card-hover) !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: var(--accent) !important;
    color: #fff !important;
    font-weight: 600 !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] + * {
    border-left: none !important;
}

/* ===== MÉTRICAS (KPIs) ===== */
[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1rem 1.25rem !important;
    transition: border-color 0.15s ease !important;
}
[data-testid="stMetric"]:hover {
    border-color: var(--accent) !important;
}
[data-testid="stMetricLabel"] {
    color: var(--text-muted) !important;
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-size: 1.75rem !important;
    font-weight: 700 !important;
    font-family: var(--font-mono) !important;
}

/* ===== DATAFRAME ===== */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    overflow: hidden !important;
}

/* ===== ALERTAS ===== */
[data-testid="stAlert"] {
    border-radius: var(--radius) !important;
    border-left-width: 3px !important;
    font-size: 0.875rem !important;
}

/* ===== CODE BLOCKS ===== */
.stCode, code, pre {
    font-family: var(--font-mono) !important;
    font-size: 0.8rem !important;
    background: #050810 !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
}

/* ===== DIVIDER ===== */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 1.5rem 0 !important;
}

/* ===== CHECKBOX ===== */
.stCheckbox label {
    color: var(--text-secondary) !important;
    font-size: 0.875rem !important;
}

/* ===== SPINNER ===== */
.stSpinner > div {
    border-top-color: var(--accent) !important;
}

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-surface); }
::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

/* ===== DOWNLOAD BUTTON ===== */
[data-testid="stDownloadButton"] > button {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-bright) !important;
    color: var(--text-secondary) !important;
    font-size: 0.825rem !important;
}
[data-testid="stDownloadButton"] > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    box-shadow: none !important;
    transform: none !important;
}
</style>
"""


def page_header(icon: str, title: str, subtitle: str = ""):
    """Renderiza el header de página con estilo unificado."""
    import streamlit as st
    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        gap: 0.875rem;
        padding: 1.25rem 0 0.5rem 0;
        border-bottom: 1px solid #1e2d4d;
        margin-bottom: 1.5rem;
    ">
        <div style="
            background: linear-gradient(135deg, #3b82f620, #06b6d420);
            border: 1px solid #3b82f640;
            border-radius: 10px;
            width: 42px; height: 42px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.25rem; flex-shrink: 0;
        ">{icon}</div>
        <div>
            <h1 style="margin:0; padding:0; font-size:1.4rem; font-weight:700; color:#e2e8f0; letter-spacing:-0.02em;">{title}</h1>
            {"<p style='margin:0; padding:0; font-size:0.8rem; color:#475569; margin-top:2px;'>" + subtitle + "</p>" if subtitle else ""}
        </div>
    </div>
    """, unsafe_allow_html=True)


def stat_card(label: str, value, color: str = "#3b82f6", icon: str = ""):
    """Devuelve HTML para una tarjeta de estadística inline."""
    return f"""
    <div style="
        background: #141d35;
        border: 1px solid #1e2d4d;
        border-top: 2px solid {color};
        border-radius: 10px;
        padding: 1rem 1.25rem;
        text-align: center;
    ">
        <div style="font-size:1.5rem; margin-bottom:4px;">{icon}</div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:1.65rem; font-weight:700; color:{color};">{value}</div>
        <div style="font-size:0.7rem; font-weight:600; letter-spacing:0.07em; text-transform:uppercase; color:#475569; margin-top:4px;">{label}</div>
    </div>
    """


def section_title(text: str, accent: bool = False):
    color = "#3b82f6" if accent else "#94a3b8"
    import streamlit as st
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:0.5rem; margin: 1.25rem 0 0.75rem 0;">
        <div style="width:3px; height:16px; background:{color}; border-radius:2px;"></div>
        <span style="font-size:0.75rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:{color};">{text}</span>
    </div>
    """, unsafe_allow_html=True)
