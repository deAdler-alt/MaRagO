"""Shared CSS + HTML utilities for the BI dashboard.

All pages import GLOBAL_CSS and use the helper functions for
consistent colored KPI cards, section headers, and badges.
"""

from __future__ import annotations

# ── Color palette ────────────────────────────────────────────────────────────

PRIORITY_COLORS = {
    "TERAZ (zaległe)": {"bg": "#7f1d1d", "accent": "#ef4444", "text": "#fef2f2"},
    "TERAZ":           {"bg": "#b91c1c", "accent": "#f87171", "text": "#fff1f2"},
    "6 mies.":         {"bg": "#92400e", "accent": "#fbbf24", "text": "#fef3c7"},
    "12 mies.":        {"bg": "#1e3a8a", "accent": "#60a5fa", "text": "#eff6ff"},
    "Daleko":          {"bg": "#1e293b", "accent": "#94a3b8", "text": "#e2e8f0"},
    "Nieaktywny":      {"bg": "#374151", "accent": "#6b7280", "text": "#f3f4f6"},
}

CONFIDENCE_COLORS = {
    "HIGH":   {"bg": "#14532d", "accent": "#4ade80", "text": "#f0fdf4"},
    "MEDIUM": {"bg": "#78350f", "accent": "#fcd34d", "text": "#fefce8"},
    "LOW":    {"bg": "#4c0519", "accent": "#fb7185", "text": "#fff1f2"},
}

# ── Base CSS injected on every page ─────────────────────────────────────────

GLOBAL_CSS = """
<style>
/* ---------- Layout ---------- */
.stApp { background-color: #0f172a !important; }
.block-container { padding-top: 1.5rem !important; max-width: 1400px; }
#MainMenu, footer, header { visibility: hidden; }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] .stCaption { color: #94a3b8 !important; }
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stCheckbox label { color: #cbd5e1 !important; }

/* ---------- Streamlit metric (fallback) ---------- */
[data-testid="stMetric"] { background: #1e293b !important; border-radius: 8px;
    border: 1px solid #334155 !important; padding: 12px 16px !important; }
[data-testid="stMetricValue"] { color: #f1f5f9 !important; font-size: 1.8rem !important; font-weight: 800 !important; }
[data-testid="stMetricLabel"] { color: #94a3b8 !important; font-size: 0.8rem !important; }
[data-testid="stMetricDelta"] { color: #64748b !important; font-size: 0.75rem !important; }

/* ---------- DataFrames ---------- */
[data-testid="stDataFrame"] { border-radius: 8px !important; border: 1px solid #334155 !important; }
.stDataFrame > div { background-color: #1e293b !important; }

/* ---------- Expander ---------- */
[data-testid="stExpander"] { background: #1e293b !important; border: 1px solid #334155 !important;
    border-radius: 8px !important; }
[data-testid="stExpander"] summary { color: #94a3b8 !important; }

/* ---------- Tabs ---------- */
[data-testid="stTabs"] [data-testid="stTab"] { color: #94a3b8 !important; }
[data-testid="stTabs"] [aria-selected="true"] { color: #f1f5f9 !important;
    border-bottom-color: #3b82f6 !important; }

/* ---------- Select/multi/text input ---------- */
[data-testid="stSelectbox"] div, [data-testid="stMultiSelect"] div,
[data-testid="stTextInput"] input { background-color: #1e293b !important;
    color: #f1f5f9 !important; border-color: #334155 !important; }

/* ---------- Divider ---------- */
hr { border-color: #334155 !important; }

/* ---------- Caption / text ---------- */
.stMarkdown p { color: #cbd5e1; }
h1, h2, h3, h4 { color: #f1f5f9 !important; }

/* ---------- Download button ---------- */
[data-testid="stDownloadButton"] button { background-color: #1e3a8a !important;
    color: #eff6ff !important; border: 1px solid #3b82f6 !important; }
[data-testid="stDownloadButton"] button:hover { background-color: #1d4ed8 !important; }

/* ---------- Info / warning / error ---------- */
[data-testid="stAlertContainer"] { border-radius: 8px !important; }

/* ---------- Code block ---------- */
[data-testid="stCode"] { background: #1e293b !important; border: 1px solid #334155 !important; }
</style>
"""

# ── Page header ──────────────────────────────────────────────────────────────

def page_header(title: str, subtitle: str, icon: str = "✈️") -> str:
    return f"""
<div style="
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border-bottom: 1px solid #334155;
    padding: 20px 24px 16px;
    margin: -24px -24px 20px -24px;
    display: flex; align-items: center; gap: 16px;
">
    <div style="font-size: 2rem;">{icon}</div>
    <div>
        <h2 style="margin:0; color:#f1f5f9; font-size:1.4rem; font-weight:800;">{title}</h2>
        <p style="margin:0; color:#64748b; font-size:0.85rem;">{subtitle}</p>
    </div>
</div>
"""

# ── KPI cards ────────────────────────────────────────────────────────────────

def kpi_card(
    value: str,
    label: str,
    sublabel: str = "",
    bg: str = "#1e293b",
    accent: str = "#3b82f6",
    text_color: str = "#f1f5f9",
) -> str:
    sub_html = f'<div style="color:#94a3b8;font-size:0.75rem;margin-top:2px;">{sublabel}</div>' if sublabel else ""
    return f"""
<div style="
    background: {bg};
    border-radius: 10px;
    padding: 16px 18px;
    border: 1px solid {accent}40;
    border-left: 4px solid {accent};
    height: 100%;
">
    <div style="color:#94a3b8;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;">{label}</div>
    <div style="color:{text_color};font-size:2.2rem;font-weight:800;line-height:1.1;margin-top:4px;">{value}</div>
    {sub_html}
</div>
"""

# ── Section header ───────────────────────────────────────────────────────────

def section_header(title: str, desc: str = "", accent: str = "#3b82f6") -> str:
    desc_html = f'<p style="margin:2px 0 0;color:#64748b;font-size:0.78rem;">{desc}</p>' if desc else ""
    return f"""
<div style="
    background:#1e293b;
    border-left: 4px solid {accent};
    border-radius: 0 8px 8px 0;
    padding: 10px 16px;
    margin: 20px 0 12px;
">
    <h4 style="margin:0;color:#f1f5f9;font-size:0.95rem;font-weight:700;">{title}</h4>
    {desc_html}
</div>
"""

# ── Priority badge (inline HTML) ─────────────────────────────────────────────

def priority_badge(priority: str) -> str:
    colors = PRIORITY_COLORS.get(priority, {"bg": "#374151", "text": "#e2e8f0"})
    icons = {
        "TERAZ (zaległe)": "🚨",
        "TERAZ": "🔴",
        "6 mies.": "🟡",
        "12 mies.": "🔵",
        "Daleko": "⚪",
        "Nieaktywny": "⬛",
    }
    icon = icons.get(priority, "")
    return (
        f'<span style="background:{colors["bg"]};color:{colors["text"]};'
        f'padding:3px 8px;border-radius:5px;font-size:0.7rem;font-weight:700;">'
        f'{icon} {priority}</span>'
    )

# ── Info card (action box) ───────────────────────────────────────────────────

def action_box(title: str, body: str, accent: str = "#3b82f6") -> str:
    return f"""
<div style="
    background:#1e293b; border-radius:10px; padding:16px 18px;
    border: 1px solid {accent}50; border-top: 3px solid {accent};
    margin-bottom: 8px;
">
    <div style="color:{accent};font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;">{title}</div>
    <div style="color:#cbd5e1;font-size:0.88rem;margin-top:6px;line-height:1.5;">{body}</div>
</div>
"""
