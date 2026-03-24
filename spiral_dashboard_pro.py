import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import io
from datetime import date

SLURRY_DENSITY = 1.2  # kg/L for heavy mineral placer slurry
EFFECTIVE_HOURS = 11
VALID_PRODUCTS = {'Concentrate', 'Middling', 'Tailings'}
APP_ICON = '🏭'

# ── Professional color palette ───────────────────────────────────────────────
COLORS = {
    'primary':    '#0F172A',
    'accent':     '#38BDF8',
    'success':    '#22C55E',
    'warning':    '#F59E0B',
    'danger':     '#F97316',
    'info':       '#60A5FA',
    'light':      '#020617',
    'card_bg':    '#111827',
    'text':       '#E5EEF9',
    'text_light': '#94A3B8',
    'border':     '#243041',
    'gradient_1': '#020617',
    'gradient_2': '#0F172A',
}

CHART_COLORS = [
    '#38BDF8', '#22C55E', '#F59E0B', '#F97316',
    '#A78BFA', '#2DD4BF', '#F43F5E', '#94A3B8',
]

# ── Global custom CSS ─────────────────────────────────────────────────────────
GLOBAL_CSS = """
<style>
/* ---------- Reset & base ---------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

html, body, [data-testid="stAppViewContainer"], .stApp {
    background:
        radial-gradient(circle at top right, rgba(56, 189, 248, 0.08), transparent 28%),
        radial-gradient(circle at top left, rgba(167, 139, 250, 0.08), transparent 24%),
        linear-gradient(180deg, #020617 0%, #0B1120 100%);
    color: #E5EEF9;
}

/* ---------- Main container ---------- */
.main .block-container {
    padding: 1.5rem 2rem 3rem 2rem;
    max-width: 1380px;
}

/* ---------- Page header ---------- */
.pro-header {
    background: linear-gradient(135deg, #111827 0%, #0F172A 100%);
    padding: 1.5rem 2rem;
    border: 1px solid #243041;
    border-radius: 18px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1.5rem;
    box-shadow: 0 12px 40px rgba(2, 6, 23, 0.42);
}

.pro-header h1 {
    color: #F8FAFC !important;
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0;
    line-height: 1.2;
}

.pro-header p {
    color: #94A3B8 !important;
    font-size: 0.9rem;
    margin: 0.2rem 0 0 0;
}

/* ---------- KPI cards ---------- */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.kpi-card {
    background: rgba(15, 23, 42, 0.88);
    border-radius: 18px;
    padding: 1.2rem 1.4rem;
    border: 1px solid #243041;
    border-left: 4px solid #38BDF8;
    box-shadow: 0 12px 28px rgba(2, 6, 23, 0.30);
    transition: transform 0.2s, box-shadow 0.2s;
    position: relative;
    overflow: hidden;
}

.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 16px 32px rgba(2, 6, 23, 0.42);
}

.kpi-card::after {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 60px; height: 60px;
    border-radius: 0 12px 0 60px;
    opacity: 0.06;
    background: currentColor;
}

.kpi-card .kpi-icon {
    font-size: 1.6rem;
    margin-bottom: 0.4rem;
    display: block;
}

.kpi-card .kpi-label {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #94A3B8;
    margin-bottom: 0.3rem;
}

.kpi-card .kpi-value {
    font-size: 1.9rem;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 0.2rem;
}

.kpi-card .kpi-unit {
    font-size: 0.8rem;
    color: #94A3B8;
    font-weight: 500;
}

.kpi-blue  { border-left-color: #38BDF8; }
.kpi-blue  .kpi-value { color: #38BDF8; }
.kpi-green { border-left-color: #22C55E; }
.kpi-green .kpi-value { color: #22C55E; }
.kpi-red   { border-left-color: #F97316; }
.kpi-red   .kpi-value { color: #F97316; }
.kpi-amber { border-left-color: #F59E0B; }
.kpi-amber .kpi-value { color: #F59E0B; }
.kpi-purple{ border-left-color: #A78BFA; }
.kpi-purple .kpi-value{ color: #A78BFA; }

/* ---------- Section heading ---------- */
.section-heading {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 1.15rem;
    font-weight: 700;
    color: #E5EEF9;
    border-bottom: 1px solid #243041;
    padding-bottom: 0.5rem;
    margin: 1.5rem 0 1rem 0;
}

/* ---------- Status badge ---------- */
.badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.badge-success { background: rgba(34, 197, 94, 0.16); color: #86EFAC; }
.badge-warning { background: rgba(245, 158, 11, 0.16); color: #FCD34D; }
.badge-danger  { background: rgba(249, 115, 22, 0.18); color: #FDBA74; }
.badge-info    { background: rgba(56, 189, 248, 0.16); color: #7DD3FC; }

/* ---------- Alert boxes ---------- */
.pro-alert {
    border-radius: 8px;
    padding: 0.9rem 1.2rem;
    margin: 0.6rem 0;
    border-left: 4px solid;
    font-size: 0.9rem;
}
.pro-alert-danger  { background: rgba(249, 115, 22, 0.14); border-color: #F97316; color: #FED7AA; }
.pro-alert-warning { background: rgba(245, 158, 11, 0.12); border-color: #F59E0B; color: #FDE68A; }
.pro-alert-success { background: rgba(34, 197, 94, 0.12); border-color: #22C55E; color: #BBF7D0; }
.pro-alert-info    { background: rgba(56, 189, 248, 0.12); border-color: #38BDF8; color: #BAE6FD; }
.pro-alert strong  { font-weight: 700; }

/* ---------- Info panel ---------- */
.info-panel {
    background: rgba(15, 23, 42, 0.72);
    border: 1px solid #243041;
    border-radius: 14px;
    padding: 0.9rem 1.2rem;
    font-size: 0.88rem;
    color: #CBD5E1;
    margin: 0.8rem 0;
}

/* ---------- Data table wrapper ---------- */
.pro-table-wrap {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #243041;
    box-shadow: 0 12px 28px rgba(2, 6, 23, 0.24);
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617 0%, #0F172A 100%) !important;
    border-right: 1px solid #243041;
}

[data-testid="stSidebar"] * {
    color: #E2E8F0 !important;
}

[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stSlider label {
    color: #94A3B8 !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #F8FAFC !important;
}

.sidebar-brand {
    text-align: center;
    padding: 1.2rem 0.5rem 0.8rem;
    border-bottom: 1px solid rgba(255,255,255,0.15);
    margin-bottom: 1rem;
}

.sidebar-brand h2 {
    color: #FFFFFF !important;
    font-size: 1rem;
    font-weight: 700;
    margin: 0.5rem 0 0.1rem;
}

.sidebar-brand p {
    color: #94A3B8 !important;
    font-size: 0.72rem;
    margin: 0;
}

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid #243041;
    border-radius: 14px;
    padding: 4px;
    gap: 4px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    padding: 0.5rem 1.2rem !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    color: #94A3B8 !important;
    background: transparent !important;
    border: none !important;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(56, 189, 248, 0.22), rgba(167, 139, 250, 0.18)) !important;
    color: #F8FAFC !important;
    border: 1px solid #334155 !important;
    box-shadow: 0 10px 24px rgba(2, 6, 23, 0.35) !important;
}

/* ---------- Metrics ---------- */
[data-testid="stMetric"] {
    background: rgba(15, 23, 42, 0.82);
    border-radius: 16px;
    padding: 0.8rem 1rem;
    border: 1px solid #243041;
    box-shadow: 0 10px 24px rgba(2, 6, 23, 0.26);
}

[data-testid="stMetricLabel"] {
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #94A3B8 !important;
}

[data-testid="stMetricValue"] {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    color: #F8FAFC !important;
}

/* ---------- Buttons ---------- */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.5rem 1.2rem !important;
    border: none !important;
    background: linear-gradient(135deg, #0F172A, #1D4ED8) !important;
    color: #FFFFFF !important;
    box-shadow: 0 10px 20px rgba(2, 6, 23, 0.35) !important;
    transition: all 0.2s !important;
}

.stButton > button:hover {
    box-shadow: 0 14px 28px rgba(2, 6, 23, 0.45) !important;
    transform: translateY(-1px) !important;
}

/* ---------- File uploader ---------- */
[data-testid="stFileUploader"] {
    border: 2px dashed #334155 !important;
    border-radius: 14px !important;
    background: rgba(15, 23, 42, 0.72) !important;
    padding: 0.5rem !important;
}

/* ---------- Download button ---------- */
.stDownloadButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    background: linear-gradient(135deg, #14532D, #15803D) !important;
    color: #FFFFFF !important;
    border: none !important;
    box-shadow: 0 10px 20px rgba(2, 6, 23, 0.28) !important;
}

/* ---------- Expander ---------- */
.streamlit-expanderHeader {
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    color: #E2E8F0 !important;
    background: rgba(15, 23, 42, 0.82) !important;
    border: 1px solid #243041 !important;
    border-radius: 12px !important;
}

/* ---------- Caption ---------- */
.stCaption {
    font-size: 0.78rem !important;
    color: #94A3B8 !important;
}

/* ---------- Divider ---------- */
hr {
    border: none !important;
    border-top: 1px solid #243041 !important;
    margin: 1.5rem 0 !important;
}

/* ---------- Success / Warning / Error containers ---------- */
.stSuccess { border-radius: 8px !important; }
.stWarning { border-radius: 8px !important; }
.stError   { border-radius: 8px !important; }
.stInfo    { border-radius: 8px !important; }

div[data-testid="stDataFrame"] {
    border: 1px solid #243041;
    border-radius: 14px;
    overflow: hidden;
}
</style>
"""


# ── Helper: render a professional KPI card ────────────────────────────────────
def kpi_card(title, value, unit="", color_class="kpi-blue", icon="📊"):
    st.markdown(
        f"""
        <div class="kpi-card {color_class}">
            <span class="kpi-icon">{icon}</span>
            <div class="kpi-label">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-unit">{unit}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Helper: section heading ────────────────────────────────────────────────────
def section_heading(icon, title):
    st.markdown(
        f'<div class="section-heading">'
        f'<span style="font-size:1.3rem">{icon}</span> {title}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Helper: status badge ───────────────────────────────────────────────────────
def status_badge(label, variant="info"):
    st.markdown(
        f'<span class="badge badge-{variant}">{label}</span>',
        unsafe_allow_html=True,
    )


# ── Helper: professional alert ────────────────────────────────────────────────
def pro_alert(title, message, variant="info"):
    st.markdown(
        f'<div class="pro-alert pro-alert-{variant}">'
        f'<strong>{title}</strong> — {message}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Helper: info panel ────────────────────────────────────────────────────────
def info_panel(text):
    st.markdown(
        f'<div class="info-panel">ℹ️ {text}</div>',
        unsafe_allow_html=True,
    )


# ── Plotly helpers ─────────────────────────────────────────────────────────────
def make_bar_chart(data, x, y, title, ylabel, colors=None):
    if colors is None:
        colors = CHART_COLORS
    bar_colors = [colors[i % len(colors)] for i in range(len(data))]
    fig = go.Figure(
        go.Bar(
            x=data[x],
            y=data[y],
            marker=dict(
                color=bar_colors,
                line=dict(width=1, color='rgba(226,232,240,0.16)'),
                opacity=0.96,
            ),
            text=data[y].round(2),
            textposition='outside',
            textfont=dict(size=11, color='#E2E8F0'),
            hovertemplate=f"{x}: %{{x}}<br>{ylabel}: %{{y:.2f}}<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color='#F8FAFC', family='Inter'), x=0),
        xaxis=dict(
            title=dict(text=x, font=dict(size=13, color='#94A3B8')),
            showgrid=False,
            tickfont=dict(size=11, color='#CBD5E1'),
        ),
        yaxis=dict(
            title=dict(text=ylabel, font=dict(size=13, color='#94A3B8')),
            showgrid=True,
            gridcolor='rgba(148,163,184,0.16)',
            zeroline=False,
            tickfont=dict(size=11, color='#CBD5E1'),
        ),
        plot_bgcolor='rgba(15, 23, 42, 0.92)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=20, t=50, b=60),
        height=400,
        font=dict(family='Inter'),
        showlegend=False,
        hoverlabel=dict(bgcolor='#0F172A', bordercolor='#334155', font=dict(color='#E2E8F0')),
    )
    return fig


def make_gauge(value, title, max_val=100, suffix="%", color=None):
    if color is None:
        color = '#22C55E' if value >= 55 else ('#F59E0B' if value >= 45 else '#F97316')
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=value,
            title=dict(text=title, font=dict(size=14, color='#E2E8F0')),
            number=dict(suffix=suffix, font=dict(size=28, color=color)),
            gauge=dict(
                axis=dict(range=[0, max_val], tickfont=dict(size=10)),
                bar=dict(color=color, thickness=0.7),
                bgcolor='#0F172A',
                borderwidth=0,
                steps=[
                    dict(range=[0, max_val * 0.45], color='rgba(249,115,22,0.30)'),
                    dict(range=[max_val * 0.45, max_val * 0.55], color='rgba(245,158,11,0.30)'),
                    dict(range=[max_val * 0.55, max_val], color='rgba(34,197,94,0.30)'),
                ],
            ),
        )
    )
    fig.update_layout(
        height=220,
        margin=dict(l=20, r=20, t=40, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter'),
    )
    return fig


def make_line_chart(df_chart, x_col, y_cols, title):
    fig = go.Figure()
    palette = ['#38BDF8', '#22C55E', '#F97316', '#A78BFA']
    for i, col in enumerate(y_cols):
        fig.add_trace(
            go.Scatter(
                x=df_chart[x_col],
                y=df_chart[col],
                name=col,
                mode='lines+markers',
                line=dict(color=palette[i % len(palette)], width=3, shape='spline', smoothing=0.6),
                marker=dict(size=7, line=dict(width=1, color='#0F172A')),
                hovertemplate=f"{col}: %{{y:.2f}}<br>{x_col}: %{{x}}<extra></extra>",
            )
        )
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color='#F8FAFC'), x=0),
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color='#CBD5E1')),
        yaxis=dict(showgrid=True, gridcolor='rgba(148,163,184,0.16)', zeroline=False, tickfont=dict(size=10, color='#CBD5E1')),
        plot_bgcolor='rgba(15, 23, 42, 0.92)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=20, t=50, b=40),
        height=340,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        font=dict(family='Inter'),
        hoverlabel=dict(bgcolor='#0F172A', bordercolor='#334155', font=dict(color='#E2E8F0')),
    )
    return fig


# ── Data helpers (unchanged logic) ───────────────────────────────────────────
def normalize_products(df, column_name):
    product_aliases = {
        'Tailing': 'Tailings',
        'Tailings': 'Tailings',
        'Concentrate': 'Concentrate',
        'Middling': 'Middling',
    }
    cleaned = df.copy()
    cleaned[column_name] = cleaned[column_name].astype(str).str.strip().str.title()
    cleaned[column_name] = cleaned[column_name].replace(product_aliases)
    cleaned = cleaned[cleaned[column_name].isin(VALID_PRODUCTS)].copy()
    return cleaned


@st.cache_data
def load_data(path):
    df = pd.read_excel(path, sheet_name='Spiral Data on Actual Run', header=1)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={'% Solid': 'Percent Solid'})

    df['Spiral unit'] = df['Spiral unit'].ffill()
    df = df[df['Product'].notna()]
    df = normalize_products(df, 'Product')

    for col in ['Flowrate (L/hr)', 'Slurry Weight (g)', 'Dry Solid Weight (g)', 'Percent Solid']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    if 'Percent Solid' in df.columns and df['Percent Solid'].max() <= 1.0:
        df['Percent Solid'] = df['Percent Solid'] * 100

    df['Flowrate'] = df['Flowrate (L/hr)']
    df['Dry Weight'] = df['Dry Solid Weight (g)']
    df['Slurry Weight'] = df['Slurry Weight (g)']
    df['Solids %'] = (df['Dry Weight'] / df['Slurry Weight']) * 100
    df['Solids Flow (kg/hr)'] = (
        df['Flowrate'] * (df['Dry Weight'] / df['Slurry Weight']) * SLURRY_DENSITY
    )
    df['Solids Flow'] = df['Solids Flow (kg/hr)']

    total_solids = df.groupby('Spiral unit')['Solids Flow'].transform('sum')
    df['Solid Yield %'] = (df['Solids Flow'] / total_solids) * 100

    group = (
        df.groupby(['Spiral unit', 'Product'])
        .agg({
            'Flowrate (L/hr)': 'sum',
            'Slurry Weight (g)': 'sum',
            'Dry Solid Weight (g)': 'sum',
            'Solids Flow': 'sum',
            'Percent Solid': 'mean',
            'Solid Yield %': 'mean',
        })
        .reset_index()
    )
    return df, group


def load_uploaded_daily_data(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    required_cols = ['Spiral unit', 'Product', 'Flowrate', 'Slurry Weight', 'Dry Weight']
    if not all(col in df.columns for col in required_cols):
        st.error("Excel format incorrect. Please use the template.")
        st.stop()

    for col in ['Flowrate', 'Slurry Weight', 'Dry Weight']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = normalize_products(df, 'Product')
    if df.empty:
        st.error("No valid product rows found. Use only Concentrate, Middling, or Tailing.")
        st.stop()

    df['Solids Flow'] = df['Flowrate'] * (df['Dry Weight'] / df['Slurry Weight']) * 1.2
    df['Flowrate (L/hr)'] = df['Flowrate']
    df['Slurry Weight (g)'] = df['Slurry Weight']
    df['Dry Solid Weight (g)'] = df['Dry Weight']
    df['Solids %'] = (df['Dry Weight'] / df['Slurry Weight']) * 100
    df['Percent Solid'] = df['Solids %']
    df['Solids Flow (kg/hr)'] = df['Solids Flow']

    total_solids = df.groupby('Spiral unit')['Solids Flow'].transform('sum')
    df['Solid Yield %'] = (df['Solids Flow'] / total_solids) * 100

    group = (
        df.groupby(['Spiral unit', 'Product'])
        .agg({
            'Flowrate (L/hr)': 'sum',
            'Slurry Weight (g)': 'sum',
            'Dry Solid Weight (g)': 'sum',
            'Solids Flow': 'sum',
            'Percent Solid': 'mean',
            'Solid Yield %': 'mean',
        })
        .reset_index()
    )
    return df, group


def empty_sensitivity_summary(is_secondary=False):
    if is_secondary:
        return pd.DataFrame(columns=[
            'Condition',
            'Calculated Feed Solids %',
            'Splitter Position',
            'Solids Level',
            'Solid Yield %',
            'Middling Fraction %',
            'Tailing Fraction %',
            'score_secondary',
        ])

    return pd.DataFrame(columns=[
        'Condition',
        'Calculated Feed Solids %',
        'Splitter Position',
        'Solids Level',
        'Concentrate Solid Yield %',
        'Concentrate Solids (tons/hr)',
        'Middling Fraction %',
        'Tailing Fraction %',
        'score_primary',
    ])


def load_sensitivity_summary(path, sheet_name, score_kind="primary"):
    is_secondary = score_kind == "secondary"
    empty_summary = empty_sensitivity_summary(is_secondary=is_secondary)

    try:
        sens_df = pd.read_excel(path, sheet_name=sheet_name, header=1)
    except Exception as exc:
        st.warning(f"Could not load {sheet_name}: {exc}")
        return empty_summary

    sens_df.columns = sens_df.columns.str.strip()
    sens_df = sens_df.rename(columns={'% Solid': 'Percent Solid'})

    required_cols = ['Condition', 'Product Type', 'Flowrate (L/hr)', 'Percent Solid']
    missing_cols = [col for col in required_cols if col not in sens_df.columns]
    if missing_cols:
        st.warning(f"{sheet_name} is missing required columns: {', '.join(missing_cols)}")
        return empty_summary

    sens_df['Condition'] = sens_df['Condition'].ffill()
    for col in ['Flowrate (L/hr)', 'Slurry Weight (g)', 'Dry Solid Weight (g)', 'Percent Solid']:
        if col in sens_df.columns:
            sens_df[col] = pd.to_numeric(sens_df[col], errors='coerce')

    if 'Percent Solid' in sens_df.columns and sens_df['Percent Solid'].max() <= 1.0:
        sens_df['Percent Solid'] = sens_df['Percent Solid'] * 100

    sens_df['Solids Flow'] = sens_df['Flowrate (L/hr)'] * (sens_df['Percent Solid'] / 100) * SLURRY_DENSITY
    sens_df = normalize_products(sens_df, 'Product Type')

    score_column = 'score_secondary' if is_secondary else 'score_primary'
    rows = []
    for condition in sens_df['Condition'].dropna().unique():
        cond_data = sens_df[sens_df['Condition'] == condition]
        total_flow = cond_data['Flowrate (L/hr)'].sum()
        calculated_feed = cond_data['Solids Flow'].sum()
        feed_solids_pct = (calculated_feed / total_flow * 100) if total_flow > 0 else 0
        conc_solids = cond_data[cond_data['Product Type'] == 'Concentrate']['Solids Flow'].sum()
        middling_solids = cond_data[cond_data['Product Type'] == 'Middling']['Solids Flow'].sum()
        tailing_solids = cond_data[cond_data['Product Type'] == 'Tailings']['Solids Flow'].sum()
        solid_yield = (conc_solids / calculated_feed * 100) if calculated_feed > 0 else 0
        middling_fraction = (middling_solids / calculated_feed * 100) if calculated_feed > 0 else 0
        tailing_fraction = (tailing_solids / calculated_feed * 100) if calculated_feed > 0 else 0
        score_value = solid_yield - (0.6 * middling_fraction if is_secondary else 0.3 * middling_fraction)

        condition_str = str(condition)
        splitter = 'Mid' if 'Medium Splitter' in condition_str or 'Mid Splitter' in condition_str else \
                   'Narrow' if 'Narrow Splitter' in condition_str else \
                   'Open' if 'Open Splitter' in condition_str else 'Unknown'
        solids_level = 'Low' if 'Lowest Solid' in condition_str else \
                       'Medium' if ('Medium Solid' in condition_str or 'Mid Solid' in condition_str) else \
                       'High' if 'Highest Solid' in condition_str else 'Unknown'

        row = {
            'Condition': condition,
            'Calculated Feed Solids %': feed_solids_pct,
            'Splitter Position': splitter,
            'Solids Level': solids_level,
            'Middling Fraction %': middling_fraction,
            'Tailing Fraction %': tailing_fraction,
            score_column: score_value,
        }
        if is_secondary:
            row['Solid Yield %'] = solid_yield
        else:
            row['Concentrate Solid Yield %'] = solid_yield
            row['Concentrate Solids (tons/hr)'] = conc_solids / 1000
        rows.append(row)

    if not rows:
        return empty_summary

    return pd.DataFrame(rows).sort_values(score_column, ascending=False).reset_index(drop=True)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title='Spiral Concentrator Analysis Pro',
        page_icon='🏭',
        layout='wide',
        initial_sidebar_state='expanded',
    )

    # Inject global CSS
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-brand">
                <div style="font-size:2rem">{APP_ICON}</div>
                <h2>Spiral Pro</h2>
                <p>Concentrator Analysis</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### 📂 Data Source")
        uploaded_file = st.file_uploader(
            "Upload Daily Plant Data (.xlsx)",
            type=["xlsx"],
            help="Upload an Excel file using the provided template.",
        )

        path = 'Spiral Plant Sheet.xlsx'
        if uploaded_file is not None:
            df, group = load_uploaded_daily_data(uploaded_file)
            st.success("✅ Data loaded from upload")
        else:
            df, group = load_data(path)
            st.info("📊 Using default plant data")

        template = pd.DataFrame({
            'Spiral unit': [],
            'Product': [],
            'Flowrate': [],
            'Slurry Weight': [],
            'Dry Weight': [],
        })
        template_buffer = io.BytesIO()
        with pd.ExcelWriter(template_buffer) as writer:
            template.to_excel(writer, index=False, sheet_name='Daily Data')
        st.download_button(
            "⬇️  Download Template",
            data=template_buffer.getvalue(),
            file_name="plant_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        st.markdown("---")
        st.markdown("#### ⚙️ Analysis Controls")
        spirals = sorted(df['Spiral unit'].dropna().unique())
        selected_spiral = st.selectbox('Select Spiral Unit', spirals)

        st.markdown("---")
        st.caption(
            f"Slurry density: **{SLURRY_DENSITY} kg/L**  \n"
            f"Effective hours: **{EFFECTIVE_HOURS} h/day**"
        )

    # ── Professional header ───────────────────────────────────────────────────
    col_logo, col_title = st.columns([1, 9])
    with col_logo:
        try:
            st.image('logo.png', width=90)
        except (FileNotFoundError, OSError):
            st.markdown(f'<div style="font-size:3rem;text-align:center">{APP_ICON}</div>', unsafe_allow_html=True)
    with col_title:
        st.markdown(
            """
            <div style="padding:0.6rem 0">
                <h1 style="margin:0;font-size:1.7rem;font-weight:800;color:#1B4F72;">
                    Spiral Concentrator Analysis
                </h1>
                <p style="margin:0.2rem 0 0;color:#5D6D7E;font-size:0.9rem;">
                    Enterprise-grade solids-based spiral performance analytics
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<hr style="margin:0.5rem 0 1.2rem">', unsafe_allow_html=True)

    # ── Pre-compute shared data ───────────────────────────────────────────────
    primary_spirals  = [1, 2, 3, 4, 7, 8]
    secondary_spirals = [5, 6]
    group_A = [1, 2, 3, 4]
    group_B = [7, 8]
    group_C = [5, 6]

    all_spirals = sorted(df['Spiral unit'].dropna().unique())
    all_perf_list = []
    for spiral in all_spirals:
        spiral_data = df[df['Spiral unit'] == spiral]
        if spiral_data.empty:
            continue
        calculated_feed   = spiral_data['Solids Flow'].sum()
        conc_solids       = spiral_data[spiral_data['Product'] == 'Concentrate']['Solids Flow'].sum()
        middling_solids   = spiral_data[spiral_data['Product'] == 'Middling']['Solids Flow'].sum()
        tailing_solids    = spiral_data[spiral_data['Product'] == 'Tailings']['Solids Flow'].sum()

        solid_yield    = (conc_solids    / calculated_feed * 100) if calculated_feed > 0 else 0
        middling_frac  = (middling_solids / calculated_feed * 100) if calculated_feed > 0 else 0
        tailing_frac   = (tailing_solids  / calculated_feed * 100) if calculated_feed > 0 else 0

        if spiral in secondary_spirals:
            score = (solid_yield * 0.4) - (middling_frac * 0.6) - (tailing_frac * 0.2)
        else:
            score = solid_yield - 0.4 * middling_frac - 0.2 * tailing_frac

        all_perf_list.append({
            'Spiral': int(spiral),
            'Solid Yield %': solid_yield,
            'Middling %': middling_frac,
            'Tailing %': tailing_frac,
            'Score': score,
        })

    all_perf_df = pd.DataFrame(all_perf_list).sort_values('Spiral').reset_index(drop=True)

    conc_df = df[df['Product'] == 'Concentrate'].copy()

    # Sensitivity Analysis – Spiral 1
    sens_df_summary = load_sensitivity_summary(path, 'Sensitivity Analysis Spiral 1', score_kind='primary')
    df_s1 = sens_df_summary.rename(columns={
        'Calculated Feed Solids %': 'feed_solids',
        'Splitter Position': 'splitter',
        'Concentrate Solid Yield %': 'yield_conc',
        'Middling Fraction %': 'middling',
    }).copy()

    # Sensitivity Analysis – Spiral 5
    sens_df_summary_spiral5 = load_sensitivity_summary(path, 'Sensitivity Analysis Spiral 5', score_kind='secondary')
    df_s5 = sens_df_summary_spiral5.rename(columns={
        'Calculated Feed Solids %': 'feed_solids',
        'Splitter Position': 'splitter',
        'Solid Yield %': 'yield_conc',
        'Middling Fraction %': 'middling',
    }).copy()

    if not df_s1.empty:
        best_s1 = df_s1.loc[df_s1['yield_conc'].idxmax()]
    else:
        best_s1 = pd.Series({'feed_solids': 0, 'splitter': 'N/A', 'yield_conc': 0, 'middling': 0})

    if not df_s5.empty:
        best_s5 = df_s5.loc[(df_s5['yield_conc'] - 0.6 * df_s5['middling']).idxmax()]
    else:
        best_s5 = pd.Series({'feed_solids': 0, 'splitter': 'N/A', 'yield_conc': 0, 'middling': 0})

    # Plant-level KPIs
    conc_solids_total    = conc_df['Solids Flow'].sum()
    tailing_solids_total = df[df['Product'] == 'Tailings']['Solids Flow'].sum()
    plant_feed           = conc_solids_total + tailing_solids_total
    plant_feed_tph       = plant_feed / 1000
    plant_feed_daily     = plant_feed_tph * EFFECTIVE_HOURS
    concentrate_tph      = conc_solids_total / 1000
    concentrate_daily    = concentrate_tph * EFFECTIVE_HOURS
    tailing_tph          = tailing_solids_total / 1000
    tailing_daily        = tailing_tph * EFFECTIVE_HOURS
    conc_hr = concentrate_tph
    feed_hr = plant_feed_tph
    tail_hr = tailing_tph
    feed_day = plant_feed_daily
    conc_day = concentrate_daily
    tail_day = tailing_daily
    recovery = (conc_hr / feed_hr * 100) if feed_hr > 0 else 0

    group_conc = (
        group[group['Product'] == 'Concentrate'][['Spiral unit', 'Solid Yield %']]
        .rename(columns={'Solid Yield %': 'Concentrate Yield (%)'})
        .reset_index(drop=True)
    )
    best_spiral  = int(group_conc.loc[group_conc['Concentrate Yield (%)'].idxmax(), 'Spiral unit']) if not group_conc.empty else 0
    worst_spiral = int(group_conc.loc[group_conc['Concentrate Yield (%)'].idxmin(), 'Spiral unit']) if not group_conc.empty else 0

    if recovery > 55 and tail_day < 80:
        status, status_variant = "GOOD", "success"
    elif recovery > 45:
        status, status_variant = "MODERATE", "warning"
    else:
        status, status_variant = "POOR", "danger"

    group_scores = {
        'Group A': all_perf_df[all_perf_df['Spiral'].isin(group_A)]['Solid Yield %'].mean(),
        'Group B': all_perf_df[all_perf_df['Spiral'].isin(group_B)]['Solid Yield %'].mean(),
        'Group C': all_perf_df[all_perf_df['Spiral'].isin(group_C)]['Solid Yield %'].mean(),
    }
    best_group = max(group_scores, key=lambda k: group_scores[k] if pd.notna(group_scores[k]) else float('-inf'))

    loss_pct = (tailing_solids_total / plant_feed * 100) if plant_feed > 0 else 0
    alerts = []
    if recovery < 45:
        alerts.append(("danger", "🔴 LOW RECOVERY", "Recovery below 45%. Check feed conditions."))
    elif recovery < 55:
        alerts.append(("warning", "🟡 MODERATE RECOVERY", "Recovery can be improved."))

    if tail_day > 90:
        alerts.append(("danger", "🔴 HIGH LOSS", "Too much material going to tailing."))
    elif tail_day > 70:
        alerts.append(("warning", "🟡 ELEVATED LOSS", "Monitor tailing losses."))

    mb_error = (abs(feed_hr - (conc_hr + tail_hr)) / feed_hr * 100) if feed_hr > 0 else 0
    if mb_error > 5:
        alerts.append(("danger", "🔴 MASS BALANCE ERROR", "Check calculations / data."))
    elif mb_error > 2:
        alerts.append(("warning", "🟡 MASS BALANCE WARNING", "Minor mismatch detected."))

    for _, row in all_perf_df.iterrows():
        spiral = int(row['Spiral'])
        if row['Middling %'] > 40:
            alerts.append(("danger", f"🔴 Spiral {spiral}", "High middling → recycle overload"))
        elif row['Middling %'] > 30:
            alerts.append(("warning", f"🟡 Spiral {spiral}", "Moderate middling"))
        if row['Tailing %'] > 35:
            alerts.append(("danger", f"🔴 Spiral {spiral}", "High loss to tailing"))

    alerts = alerts[:4]

    if recovery < 45:
        alerts.append((
            "danger",
            "Recommended Action",
            f"Adjust Spiral 1 to Feed Solids {best_s1['feed_solids']:.1f}% with splitter {best_s1['splitter']}."
        ))

    if (all_perf_df['Middling %'] > 40).any():
        alerts.append((
            "warning",
            "Recycle Optimisation",
            f"Optimise Spiral 5 at Feed Solids {best_s5['feed_solids']:.1f}% with splitter {best_s5['splitter']}."
        ))

    if tail_day > 90:
        alerts.append((
            "danger",
            "Loss Reduction",
            f"Improve primary recovery around Spiral 1 settings: {best_s1['feed_solids']:.1f}% solids and {best_s1['splitter']} splitter."
        ))

    current_feed  = feed_day
    current_conc  = conc_day
    best_yield_s1 = best_s1['yield_conc']
    new_conc      = current_feed * (best_yield_s1 / 100)
    gain          = new_conc - current_conc

    sim_cols = st.columns(3)
    with sim_cols[0]:
        st.metric("Current Production", f"{current_conc:.2f} TPD")
    with sim_cols[1]:
        st.metric("Projected Production", f"{new_conc:.2f} TPD", delta=f"+{gain:.2f} TPD" if gain > 0 else f"{gain:.2f} TPD")
    with sim_cols[2]:
        st.metric("Potential Gain", f"{gain:.2f} TPD")

    if gain > 0:
        st.success(f"📈 Production could increase by **{gain:.2f} tons/day** by optimizing Spiral 1 settings.")
    else:
        st.info("Current settings already near optimal for Spiral 1.")

    info_panel(
        f"Simulation: Feed constant at {current_feed:.2f} TPD — "
        f"New yield from sensitivity: {best_yield_s1:.2f}% — Spiral 1 settings only."
    )

    best_yield_s5       = best_s5['yield_conc']
    combined_yield      = (best_yield_s1 + best_yield_s5) / 2
    new_conc_combined   = current_feed * (combined_yield / 100)
    gain_combined       = new_conc_combined - current_conc

    today    = date.today()
    new_date = pd.to_datetime(today).normalize()
    new_data = pd.DataFrame([{
        "Date": new_date,
        "Feed_TPD": feed_day,
        "Concentrate_TPD": conc_day,
        "Tailing_TPD": tail_day,
        "Recovery": recovery,
    }])

    history_path    = "plant_history.csv"
    history_columns = ["Date", "Feed_TPD", "Concentrate_TPD", "Tailing_TPD", "Recovery"]

    try:
        df_history = pd.read_csv(history_path)
    except (FileNotFoundError, OSError):
        df_history = pd.DataFrame(columns=history_columns)

    if not df_history.empty:
        df_history['Date'] = pd.to_datetime(df_history['Date']).dt.normalize()

    if (not df_history.empty) and (df_history['Date'] == new_date).any():
        st.warning("⚠️ Data for today already exists and will be overwritten on save.")

    if st.button("💾 Save Today's Data"):
        existing = df_history.copy()
        if not existing.empty:
            existing['Date'] = pd.to_datetime(existing['Date']).dt.normalize()
            existing = existing[existing['Date'] != new_date]
        df_history = pd.concat([existing, new_data], ignore_index=True)
        df_history = df_history.drop_duplicates(subset=['Date'], keep='last')
        df_history = df_history.sort_values(by='Date').reset_index(drop=True)
        save_df = df_history.copy()
        save_df['Date'] = pd.to_datetime(save_df['Date']).dt.strftime('%Y-%m-%d')
        save_df.to_csv(history_path, index=False)
        st.success("✅ Daily data saved successfully.")

    top_tabs = st.tabs([
        "Overview",
        "Alerts",
        "Simulation",
        "History",
        "Analysis",
    ])

    with top_tabs[0]:
        section_heading("📊", "Plant Overview")
        info_panel("Start here for a quick snapshot. Detailed engineering views live in the Analysis tab.")

        cols = st.columns(4)
        with cols[0]:
            kpi_card("Production", f"{conc_day:.1f}", "tons/day", "kpi-blue", "📦")
        with cols[1]:
            kpi_card("Recovery", f"{recovery:.1f}%", "concentrate", "kpi-green", "📈")
        with cols[2]:
            kpi_card("Tailing Loss", f"{tail_day:.1f}", "tons/day", "kpi-red", "⚠️")
        with cols[3]:
            kpi_card("Plant Status", status, "", f"kpi-{'green' if status == 'GOOD' else 'amber' if status == 'MODERATE' else 'red'}", "🟢" if status == "GOOD" else "🟡" if status == "MODERATE" else "🔴")

        cols2 = st.columns(3)
        with cols2[0]:
            kpi_card("Best Spiral", f"S{best_spiral}", "highest recovery", "kpi-green", "🏆")
        with cols2[1]:
            kpi_card("Worst Spiral", f"S{worst_spiral}", "needs attention", "kpi-red", "⚠️")
        with cols2[2]:
            kpi_card("Top Group", best_group, "best avg yield", "kpi-purple", "🥇")

        overview_left, overview_right = st.columns([1.1, 1.4])
        with overview_left:
            st.plotly_chart(make_gauge(recovery, "Recovery Rate"), use_container_width=True)
        with overview_right:
            section_heading("⚖️", "Mass Balance")
            mb_cols = st.columns(3)
            with mb_cols[0]:
                st.metric("Feed (TPH)", f"{plant_feed_tph:.1f}")
                st.metric("Feed (TPD)", f"{plant_feed_daily:.2f}")
            with mb_cols[1]:
                st.metric("Concentrate (TPH)", f"{concentrate_tph:.1f}")
                st.metric("Concentrate (TPD)", f"{concentrate_daily:.2f}")
            with mb_cols[2]:
                st.metric("Tailing (TPH)", f"{tailing_tph:.1f}")
                st.metric("Tailing (TPD)", f"{tailing_daily:.2f}")

        section_heading("📉", "Loss Snapshot")
        loss_cols = st.columns(2)
        with loss_cols[0]:
            st.metric("Tailing Loss %", f"{loss_pct:.1f}%")
        with loss_cols[1]:
            st.metric("Current Focus", f"S{worst_spiral}" if worst_spiral else "N/A")
            st.caption(f"Tailing = {tailing_daily:.2f} TPD ({loss_pct:.1f}% of plant feed)")

    with top_tabs[1]:
        section_heading("🚨", "Alerts & Recommendations")
        if alerts:
            for variant, title, msg in alerts:
                pro_alert(title, msg, variant)
        else:
            st.markdown('<div class="pro-alert pro-alert-success">✅ <strong>All systems nominal</strong> — No critical alerts detected.</div>', unsafe_allow_html=True)

    with top_tabs[2]:
        section_heading("🔮", "Production Simulation")
        sim_cols = st.columns(3)
        with sim_cols[0]:
            st.metric("Current Production", f"{current_conc:.2f} TPD")
        with sim_cols[1]:
            st.metric("Projected Production", f"{new_conc:.2f} TPD", delta=f"+{gain:.2f} TPD" if gain > 0 else f"{gain:.2f} TPD")
        with sim_cols[2]:
            st.metric("Full Optimisation", f"{new_conc_combined:.2f} TPD", delta=f"+{gain_combined:.2f} TPD" if gain_combined > 0 else f"{gain_combined:.2f} TPD")

        if gain > 0:
            pro_alert("Spiral 1 Opportunity", f"Production could increase by {gain:.2f} tons/day by optimizing Spiral 1 settings.", "success")
        else:
            info_panel("Current settings already appear close to optimal for Spiral 1.")

        info_panel(
            f"Simulation basis: Feed fixed at {current_feed:.2f} TPD. Spiral 1 yield target {best_yield_s1:.2f}%. Full optimisation blends Spiral 1 and Spiral 5 improvements."
        )

        sim_data = pd.DataFrame({
            'Scenario': ['Current', 'Spiral 1 Optimised', 'Full Optimisation'],
            'Concentrate TPD': [current_conc, new_conc, new_conc_combined],
        })
        fig = make_bar_chart(sim_data, 'Scenario', 'Concentrate TPD', 'Production Scenarios', 'Concentrate (TPD)')
        st.plotly_chart(fig, use_container_width=True)

    with top_tabs[3]:
        section_heading("📅", "Historical Tracking")
        if not df_history.empty:
            df_history['Date'] = pd.to_datetime(df_history['Date'])

            hist_top_cols = st.columns([1, 1, 1.4])
            with hist_top_cols[0]:
                st.metric("Average Recovery", f"{df_history['Recovery'].mean():.1f}%")
            with hist_top_cols[1]:
                st.metric("Saved Days", f"{len(df_history)}")
            with hist_top_cols[2]:
                info_panel("Use the save button above to store today's plant snapshot into history.")

            fig_trend = make_line_chart(
                df_history, 'Date',
                ['Feed_TPD', 'Concentrate_TPD', 'Tailing_TPD'],
                'Daily Production Trend',
            )
            st.plotly_chart(fig_trend, use_container_width=True)

            df_history['Month'] = df_history['Date'].dt.to_period('M')
            monthly_total = df_history.groupby('Month')['Concentrate_TPD'].sum().reset_index()
            monthly_total['Month'] = monthly_total['Month'].astype(str)
            monthly_avg = df_history.groupby('Month')['Concentrate_TPD'].mean().reset_index()
            monthly_avg['Month'] = monthly_avg['Month'].astype(str)

            hist_col1, hist_col2 = st.columns(2)
            with hist_col1:
                fig_mt = make_bar_chart(monthly_total, 'Month', 'Concentrate_TPD', 'Monthly Production (tons)', 'Concentrate (tons)')
                st.plotly_chart(fig_mt, use_container_width=True)
            with hist_col2:
                fig_ma = make_bar_chart(monthly_avg, 'Month', 'Concentrate_TPD', 'Monthly Avg Production (TPD)', 'Concentrate (TPD)')
                st.plotly_chart(fig_ma, use_container_width=True)

            df_history['Year'] = df_history['Date'].dt.year
            yearly_total = df_history.groupby('Year')['Concentrate_TPD'].sum().reset_index()
            yearly_avg   = df_history.groupby('Year')['Concentrate_TPD'].mean().reset_index()

            yr_col1, yr_col2 = st.columns(2)
            with yr_col1:
                fig_yt = make_bar_chart(yearly_total, 'Year', 'Concentrate_TPD', 'Yearly Production (tons)', 'Concentrate (tons)')
                st.plotly_chart(fig_yt, use_container_width=True)
            with yr_col2:
                fig_ya = make_bar_chart(yearly_avg, 'Year', 'Concentrate_TPD', 'Yearly Avg Production (TPD)', 'Concentrate (TPD)')
                st.plotly_chart(fig_ya, use_container_width=True)

            selected_range = st.date_input(
                "📅 Filter by Date Range",
                [df_history['Date'].min().date(), df_history['Date'].max().date()],
                key="history_range",
            )
            if isinstance(selected_range, (list, tuple)) and len(selected_range) == 2:
                start_date, end_date = selected_range
                filtered = df_history[
                    (df_history['Date'] >= pd.to_datetime(start_date)) &
                    (df_history['Date'] <= pd.to_datetime(end_date))
                ]
                if not filtered.empty:
                    fig_fil = make_line_chart(filtered, 'Date', ['Concentrate_TPD'], 'Filtered Production')
                    st.plotly_chart(fig_fil, use_container_width=True)
                else:
                    st.warning("No data in selected date range.")

            with st.expander("🔎 Raw History Data"):
                st.dataframe(df_history, hide_index=True, use_container_width=True)

            st.download_button(
                "⬇️  Download Historical Report",
                df_history.to_csv(index=False),
                file_name="plant_report.csv",
                mime="text/csv",
            )
        else:
            info_panel("No historical data yet. Save today's values to begin trend tracking.")

    with top_tabs[4]:
        section_heading("🧪", "Detailed Analysis")
        info_panel("Use these tabs for deeper operational views. Each section is separated to keep the dashboard lighter.")
        tabs = st.tabs([
            "🔩 Spiral Performance",
            "💧 Feed & Hydraulics",
            "♻️ Recycle Analysis",
            "🔬 Sensitivity Analysis",
        ])

        with tabs[0]:
            section_heading("🔩", f"Spiral Performance — Spiral {selected_spiral}")
            spiral_df = df[df['Spiral unit'] == selected_spiral].copy()
            spiral_conc = spiral_df[spiral_df['Product'] == 'Concentrate']['Solids Flow'].sum()
            sel_production = spiral_conc * EFFECTIVE_HOURS / 1000
            selected_row = all_perf_df[all_perf_df['Spiral'] == int(selected_spiral)]
            sel_yield = selected_row.iloc[0]['Solid Yield %'] if not selected_row.empty else 0

            sp_cols = st.columns(2)
            with sp_cols[0]:
                st.metric("Solid Flow (Production)", f"{sel_production:.2f} tons/day")
            with sp_cols[1]:
                st.metric("Solid Yield", f"{sel_yield:.2f}%")

            spiral_production = (
                conc_df.groupby('Spiral unit', as_index=False)['Solids Flow']
                .sum()
                .rename(columns={'Spiral unit': 'Spiral'})
            )
            spiral_production['Production (tons/day)'] = spiral_production['Solids Flow'] * EFFECTIVE_HOURS / 1000
            spiral_production['Spiral'] = spiral_production['Spiral'].astype(int)

            combined_table = all_perf_df[['Spiral', 'Solid Yield %', 'Middling %', 'Tailing %']].copy()
            combined_table = combined_table.merge(
                spiral_production[['Spiral', 'Production (tons/day)']],
                on='Spiral', how='left',
            )
            combined_table['Production (tons/day)'] = combined_table['Production (tons/day)'].fillna(0)
            combined_table = combined_table[['Spiral', 'Production (tons/day)', 'Solid Yield %', 'Middling %', 'Tailing %']]
            combined_table = combined_table.rename(columns={'Solid Yield %': 'Yield (%)'})

            info_panel("Production shows quantity; yield shows separation efficiency.")

            chart_prod = combined_table[['Spiral', 'Production (tons/day)']].copy()
            chart_prod['Spiral'] = chart_prod['Spiral'].astype(str)
            chart_yield = combined_table[['Spiral', 'Yield (%)']].copy()
            chart_yield['Spiral'] = chart_yield['Spiral'].astype(str)

            t1_col1, t1_col2 = st.columns(2)
            with t1_col1:
                fig_prod = make_bar_chart(chart_prod, 'Spiral', 'Production (tons/day)', 'Solid Flow by Spiral', 'Production (tons/day)')
                st.plotly_chart(fig_prod, use_container_width=True)
            with t1_col2:
                fig_yld = make_bar_chart(chart_yield, 'Spiral', 'Yield (%)', 'Solid Yield by Spiral', 'Yield (%)')
                st.plotly_chart(fig_yld, use_container_width=True)

            section_heading("📋", "Combined Performance Table")
            st.dataframe(
                combined_table.style.background_gradient(subset=['Yield (%)'], cmap='Blues')
                                     .format({'Yield (%)': '{:.1f}', 'Middling %': '{:.1f}', 'Tailing %': '{:.1f}', 'Production (tons/day)': '{:.2f}'}),
                use_container_width=True,
                hide_index=True,
            )

        with tabs[1]:
            section_heading("💧", "Feed & Hydraulics (Calculated Feed: C + M + T)")
            info_panel("All metrics in this tab use calculated feed only (Concentrate + Middling + Tailing).")

            internal_feed_by_spiral = (
                df.groupby('Spiral unit', as_index=False)['Solids Flow']
                .sum()
                .rename(columns={'Spiral unit': 'Spiral', 'Solids Flow': 'Internal Feed (tons/hr)'})
            )
            internal_feed_by_spiral['Internal Feed (tons/hr)'] = internal_feed_by_spiral['Internal Feed (tons/hr)'] / 1000
            internal_feed_by_spiral['Spiral'] = internal_feed_by_spiral['Spiral'].astype(str)

            fig_feed = make_bar_chart(
                internal_feed_by_spiral, 'Spiral', 'Internal Feed (tons/hr)',
                'Internal Feed Distribution by Spiral (C + M + T)', 'Internal Feed (tons/hr)',
            )
            st.plotly_chart(fig_feed, use_container_width=True)
            st.caption("Internal Feed = Concentrate + Middling + Tailing. Used for yield calculations, not plant mass balance.")

            group_a_internal = df[df['Spiral unit'].isin(group_A)]['Solids Flow'].sum() / 1000
            group_b_internal = df[df['Spiral unit'].isin(group_B)]['Solids Flow'].sum() / 1000
            group_a_yield = all_perf_df[all_perf_df['Spiral'].isin(group_A)]['Solid Yield %'].mean()
            group_b_yield = all_perf_df[all_perf_df['Spiral'].isin(group_B)]['Solid Yield %'].mean()

            feed_overview = pd.DataFrame({
                'Group': ['A (1-4)', 'B (7-8)'],
                'Internal Feed (tons/hr)': [group_a_internal, group_b_internal],
                'Average Yield (%)': [group_a_yield, group_b_yield],
            })
            st.dataframe(feed_overview, hide_index=True, use_container_width=True)
            st.caption("Internal Feed = Concentrate + Middling + Tailing per group (for yield calculations only).")

            section_heading("📊", "Group Performance Analysis")
            for group_name, group_spirals in [("A (1–4)", group_A), ("B (7–8)", group_B)]:
                with st.expander(f"Group {group_name}", expanded=True):
                    group_perf = all_perf_df[all_perf_df['Spiral'].isin(group_spirals)].copy()
                    if not group_perf.empty:
                        group_perf_display = group_perf[['Spiral', 'Solid Yield %', 'Middling %', 'Tailing %']].rename(
                            columns={'Solid Yield %': 'Yield (%)'}
                        ).sort_values('Spiral')
                        st.dataframe(group_perf_display.style.background_gradient(subset=['Yield (%)'], cmap='Greens')
                                                             .format({'Yield (%)': '{:.1f}', 'Middling %': '{:.1f}', 'Tailing %': '{:.1f}'}),
                                     hide_index=True, use_container_width=True)

                        group_perf['score'] = group_perf['Solid Yield %'] - group_perf['Middling %'] * 0.5
                        best_spiral_row = group_perf.loc[group_perf['score'].idxmax()]
                        best_sp = int(best_spiral_row['Spiral'])
                        best_yld = best_spiral_row['Solid Yield %']
                        best_mid = best_spiral_row['Middling %']
                        best_tal = best_spiral_row['Tailing %']

                        st.markdown(
                            f'<div class="pro-alert pro-alert-info"><strong>Spiral {best_sp}</strong> is performing best in this group. '
                            f'Yield: {best_yld:.1f}% · Middling: {best_mid:.1f}% · Tailing: {best_tal:.1f}%<br>'
                            f'<em>Recommendation: increase feed to this spiral and match other spirals to its operating conditions.</em></div>',
                            unsafe_allow_html=True,
                        )

                        if best_yld > 70 and best_mid < 20:
                            status_badge("✅ High Recovery", "success")
                        elif best_mid >= 20:
                            status_badge("⚠️ Excessive Recycle", "warning")
                        elif best_tal > 15:
                            status_badge("⚠️ High Loss", "warning")
                        else:
                            status_badge("📊 Moderate", "info")

            section_heading("📈", "Production Projection")
            increase = st.slider('Increase Plant Feed (%)', 0, 30, 10)
            proj_production = plant_feed_daily * (1 + increase / 100)
            st.metric('Projected Production', f'{proj_production:.2f} tons/day', delta=f"+{proj_production - plant_feed_daily:.2f}")
            if increase > 15:
                pro_alert("⚠️ Feed Increase Warning", "Higher feed may reduce separation efficiency and increase middling recycle.", "warning")

        with tabs[2]:
            section_heading("♻️", "Recycle Analysis")
            info_panel("Middling flow and recycle behaviour. Internal feed = C + M + T per spiral.")

            primary_middlings_kgph = df[
                df['Spiral unit'].isin([1, 2, 3, 4, 7, 8]) &
                (df['Product'] == 'Middling')
            ]['Solids Flow'].sum()
            recycle_kgph = df[
                df['Spiral unit'].isin([5, 6]) &
                (df['Product'] == 'Middling')
            ]['Solids Flow'].sum()
            primary_middlings_tph = primary_middlings_kgph / 1000
            recycle_tph = recycle_kgph / 1000
            circulating_load = (recycle_kgph / primary_middlings_kgph * 100) if primary_middlings_kgph > 0 else 0

            r_cols = st.columns(3)
            with r_cols[0]:
                st.metric('Primary Middlings', f'{primary_middlings_tph:.2f} tons/hr')
            with r_cols[1]:
                st.metric('Recycled Middlings', f'{recycle_tph:.2f} tons/hr')
            with r_cols[2]:
                st.metric('Circulating Load %', f'{circulating_load:.1f}%')

            group_c_data = all_perf_df[all_perf_df['Spiral'].isin(group_C)].sort_values('Middling %')
            if not group_c_data.empty:
                middling_chart_c = group_c_data[['Spiral', 'Middling %']].copy()
                middling_chart_c['Spiral'] = middling_chart_c['Spiral'].astype(str)
                fig_mid = make_bar_chart(
                    middling_chart_c, 'Spiral', 'Middling %',
                    'Group C Middling % (Lower is Better)', 'Middling %',
                    colors=['#F59E0B', '#F97316'],
                )
                st.plotly_chart(fig_mid, use_container_width=True)
                st.dataframe(
                    group_c_data[['Spiral', 'Solid Yield %', 'Middling %', 'Tailing %']].style
                    .background_gradient(subset=['Middling %'], cmap='Oranges')
                    .format({'Solid Yield %': '{:.1f}', 'Middling %': '{:.1f}', 'Tailing %': '{:.1f}'}),
                    hide_index=True,
                    use_container_width=True,
                )

        with tabs[3]:
            section_heading("🔬", "Sensitivity Analysis")
            st.markdown("#### 🔵 Spiral 1 — Primary Concentrator")
            if sens_df_summary.empty:
                info_panel("Spiral 1 sensitivity data is unavailable. Add the relevant sheet to the workbook to enable this analysis.")
            else:
                st.dataframe(
                    sens_df_summary.style.background_gradient(subset=['Concentrate Solid Yield %'], cmap='Blues')
                                          .format({'Concentrate Solid Yield %': '{:.1f}', 'Middling Fraction %': '{:.1f}', 'Tailing Fraction %': '{:.1f}'}),
                    hide_index=True,
                    use_container_width=True,
                )
                yield_data_s1 = sens_df_summary[['Condition', 'Concentrate Solid Yield %']].copy()
                fig_s1 = make_bar_chart(
                    yield_data_s1, 'Condition', 'Concentrate Solid Yield %',
                    'Spiral 1 — Concentrate Yield by Condition', 'Yield %',
                )
                st.plotly_chart(fig_s1, use_container_width=True)

                st.markdown(
                    f"""<div class="pro-alert pro-alert-success">
                    <strong>✅ Spiral 1 Best Condition:</strong><br>
                    Feed Solids: {best_s1['feed_solids']:.1f}% · Splitter: {best_s1['splitter']} · Yield: {best_s1['yield_conc']:.2f}%<br>
                    <em>High recovery with acceptable middling.</em>
                    </div>""",
                    unsafe_allow_html=True,
                )

            st.markdown("---")

            st.markdown("#### 🟠 Spiral 5 — Secondary / Cleaning Concentrator")
            if sens_df_summary_spiral5.empty:
                info_panel("Spiral 5 sensitivity data is unavailable. Add the relevant sheet to the workbook to enable this analysis.")
            else:
                st.dataframe(
                    sens_df_summary_spiral5.style.background_gradient(subset=['Solid Yield %'], cmap='Oranges')
                                                  .format({'Solid Yield %': '{:.1f}', 'Middling Fraction %': '{:.1f}', 'Tailing Fraction %': '{:.1f}'}),
                    hide_index=True,
                    use_container_width=True,
                )
                middling_data_s5 = sens_df_summary_spiral5[['Condition', 'Middling Fraction %']].copy()
                fig_s5 = make_bar_chart(
                    middling_data_s5, 'Condition', 'Middling Fraction %',
                    'Spiral 5 — Middling Fraction by Condition', 'Middling %',
                    colors=['#F59E0B', '#F97316', '#F43F5E', '#FCD34D'],
                )
                st.plotly_chart(fig_s5, use_container_width=True)

                st.markdown(
                    f"""<div class="pro-alert pro-alert-success">
                    <strong>✅ Spiral 5 Best Condition:</strong><br>
                    Feed Solids: {best_s5['feed_solids']:.1f}% · Splitter: {best_s5['splitter']} · Yield: {best_s5['yield_conc']:.2f}%<br>
                    <em>Efficient cleaning with low recycle load.</em>
                    </div>""",
                    unsafe_allow_html=True,
                )


if __name__ == '__main__':
    main()
