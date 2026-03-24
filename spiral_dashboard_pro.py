import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import io
from datetime import date

SLURRY_DENSITY = 1.2  # kg/L for heavy mineral placer slurry
EFFECTIVE_HOURS = 11
VALID_PRODUCTS = {'Concentrate', 'Middling', 'Tailings'}
APP_ICON = '🏭'

# ── Dark professional color palette ──────────────────────────────────────────
COLORS = {
    'primary':    '#38BDF8',   # sky blue accent
    'accent':     '#0EA5E9',   # deeper blue
    'success':    '#4ADE80',   # green
    'warning':    '#FBBF24',   # amber
    'danger':     '#F87171',   # red
    'info':       '#818CF8',   # indigo
    'bg':         '#0F172A',   # main background
    'surface':    '#1E293B',   # card / panel
    'surface2':   '#273549',   # elevated card
    'border':     '#334155',   # border
    'text':       '#F1F5F9',   # primary text
    'text_muted': '#94A3B8',   # secondary text
    'gradient_1': '#0F172A',
    'gradient_2': '#1E3A5F',
}

CHART_COLORS = [
    '#38BDF8', '#4ADE80', '#FBBF24', '#F87171',
    '#C084FC', '#34D399', '#FB923C', '#94A3B8',
]

# ── Global custom CSS ─────────────────────────────────────────────────────────
GLOBAL_CSS = """
<style>
/* ---------- Reset & base ---------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* ---------- Dark main background ---------- */
.stApp {
    background-color: #0F172A !important;
}

.main .block-container {
    padding: 1.5rem 2rem 3rem 2rem;
    max-width: 1400px;
    background-color: #0F172A;
}

/* ---------- Page header ---------- */
.pro-header {
    background: linear-gradient(135deg, #0F172A 0%, #1E3A5F 100%);
    padding: 1.2rem 1.8rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    border: 1px solid #334155;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
}

.pro-header h1 {
    color: #F1F5F9 !important;
    font-size: 1.6rem;
    font-weight: 700;
    margin: 0;
    line-height: 1.2;
}

.pro-header p {
    color: #94A3B8 !important;
    font-size: 0.85rem;
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
    background: #1E293B;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    border: 1px solid #334155;
    border-left: 4px solid #38BDF8;
    box-shadow: 0 2px 12px rgba(0,0,0,0.3);
    transition: transform 0.2s, box-shadow 0.2s;
}

.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(0,0,0,0.5);
    background: #273549;
}

.kpi-card .kpi-icon {
    font-size: 1.4rem;
    margin-bottom: 0.4rem;
    display: block;
}

.kpi-card .kpi-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #64748B;
    margin-bottom: 0.3rem;
}

.kpi-card .kpi-value {
    font-size: 1.8rem;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 0.2rem;
}

.kpi-card .kpi-unit {
    font-size: 0.78rem;
    color: #64748B;
    font-weight: 500;
}

.kpi-blue   { border-left-color: #38BDF8; }
.kpi-blue   .kpi-value { color: #38BDF8; }
.kpi-green  { border-left-color: #4ADE80; }
.kpi-green  .kpi-value { color: #4ADE80; }
.kpi-red    { border-left-color: #F87171; }
.kpi-red    .kpi-value { color: #F87171; }
.kpi-amber  { border-left-color: #FBBF24; }
.kpi-amber  .kpi-value { color: #FBBF24; }
.kpi-purple { border-left-color: #C084FC; }
.kpi-purple .kpi-value { color: #C084FC; }

/* ---------- Section heading ---------- */
.section-heading {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 1.05rem;
    font-weight: 700;
    color: #E2E8F0;
    border-bottom: 1px solid #334155;
    padding-bottom: 0.5rem;
    margin: 1.5rem 0 1rem 0;
}

/* ---------- Status badge ---------- */
.badge {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.badge-success { background: rgba(74,222,128,0.15); color: #4ADE80; border: 1px solid #4ADE80; }
.badge-warning { background: rgba(251,191,36,0.15);  color: #FBBF24; border: 1px solid #FBBF24; }
.badge-danger  { background: rgba(248,113,113,0.15); color: #F87171; border: 1px solid #F87171; }
.badge-info    { background: rgba(129,140,248,0.15); color: #818CF8; border: 1px solid #818CF8; }

/* ---------- Alert boxes ---------- */
.pro-alert {
    border-radius: 8px;
    padding: 0.9rem 1.2rem;
    margin: 0.6rem 0;
    border-left: 4px solid;
    font-size: 0.88rem;
}
.pro-alert-danger  { background: rgba(248,113,113,0.1); border-color: #F87171; color: #FCA5A5; }
.pro-alert-warning { background: rgba(251,191,36,0.1);  border-color: #FBBF24; color: #FDE68A; }
.pro-alert-success { background: rgba(74,222,128,0.1);  border-color: #4ADE80; color: #86EFAC; }
.pro-alert-info    { background: rgba(129,140,248,0.1); border-color: #818CF8; color: #A5B4FC; }
.pro-alert strong  { font-weight: 700; }

/* ---------- Info panel ---------- */
.info-panel {
    background: rgba(56,189,248,0.08);
    border: 1px solid rgba(56,189,248,0.25);
    border-radius: 8px;
    padding: 0.8rem 1.1rem;
    font-size: 0.85rem;
    color: #7DD3FC;
    margin: 0.8rem 0;
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0B1120 0%, #0F172A 100%) !important;
    border-right: 1px solid #1E293B !important;
}

[data-testid="stSidebar"] * {
    color: #CBD5E1 !important;
}

[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stSlider label {
    color: #64748B !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #F1F5F9 !important;
}

.sidebar-brand {
    text-align: center;
    padding: 1.2rem 0.5rem 0.8rem;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 1rem;
}

.sidebar-brand h2 {
    color: #F1F5F9 !important;
    font-size: 1rem;
    font-weight: 700;
    margin: 0.4rem 0 0.1rem;
}

.sidebar-brand p {
    color: #64748B !important;
    font-size: 0.72rem;
    margin: 0;
}

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] {
    background: #1E293B;
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
    border: 1px solid #334155;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    padding: 0.45rem 1rem !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    color: #64748B !important;
    background: transparent !important;
    border: none !important;
}

.stTabs [aria-selected="true"] {
    background: #273549 !important;
    color: #38BDF8 !important;
    box-shadow: none !important;
    border: 1px solid #334155 !important;
}

/* ---------- Metrics ---------- */
[data-testid="stMetric"] {
    background: #1E293B;
    border-radius: 10px;
    padding: 0.8rem 1rem;
    border: 1px solid #334155;
}

[data-testid="stMetricLabel"] {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #64748B !important;
}

[data-testid="stMetricValue"] {
    font-size: 1.4rem !important;
    font-weight: 700 !important;
    color: #F1F5F9 !important;
}

[data-testid="stMetricDelta"] svg { display: none; }

/* ---------- Buttons ---------- */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.5rem 1.2rem !important;
    border: 1px solid #334155 !important;
    background: #1E293B !important;
    color: #38BDF8 !important;
    box-shadow: none !important;
    transition: all 0.2s !important;
}

.stButton > button:hover {
    background: #273549 !important;
    border-color: #38BDF8 !important;
}

/* ---------- File uploader ---------- */
[data-testid="stFileUploader"] {
    border: 1px dashed #334155 !important;
    border-radius: 10px !important;
    background: #1E293B !important;
    padding: 0.5rem !important;
}

/* ---------- Download button ---------- */
.stDownloadButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    background: #1E293B !important;
    color: #4ADE80 !important;
    border: 1px solid #4ADE80 !important;
}

/* ---------- Expander ---------- */
.streamlit-expanderHeader {
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    color: #CBD5E1 !important;
    background: #1E293B !important;
    border-radius: 8px !important;
    border: 1px solid #334155 !important;
}

/* ---------- Caption / text ---------- */
.stCaption, .stCaption p {
    font-size: 0.78rem !important;
    color: #64748B !important;
}

p, label, .stMarkdown p {
    color: #CBD5E1 !important;
}

h1, h2, h3, h4, h5, h6 {
    color: #F1F5F9 !important;
}

/* ---------- Divider ---------- */
hr {
    border: none !important;
    border-top: 1px solid #1E293B !important;
    margin: 1.5rem 0 !important;
}

/* ---------- Alert containers ---------- */
.stSuccess, .stWarning, .stError, .stInfo { border-radius: 8px !important; }

/* ---------- Dataframe / table ---------- */
.stDataFrame { background: #1E293B !important; border-radius: 10px; overflow: hidden; }

/* ---------- Selectbox / input ---------- */
[data-testid="stSelectbox"] > div > div {
    background: #1E293B !important;
    border: 1px solid #334155 !important;
    color: #F1F5F9 !important;
    border-radius: 8px !important;
}

/* ---------- Slider ---------- */
[data-testid="stSlider"] .st-bk { background: #334155 !important; }
[data-testid="stSlider"] .st-cn { background: #38BDF8 !important; }

/* ---------- Scrollbar ---------- */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0F172A; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #475569; }
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
                line=dict(width=0),
                opacity=0.85,
            ),
            text=data[y].round(2),
            textposition='outside',
            textfont=dict(size=11, color='#94A3B8'),
        )
    )
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color='#E2E8F0', family='Inter'), x=0),
        xaxis=dict(
            title=dict(text=x, font=dict(size=12, color='#64748B')),
            showgrid=False,
            tickfont=dict(size=11, color='#94A3B8'),
            linecolor='#334155',
        ),
        yaxis=dict(
            title=dict(text=ylabel, font=dict(size=12, color='#64748B')),
            showgrid=True,
            gridcolor='#1E293B',
            zeroline=False,
            tickfont=dict(size=11, color='#94A3B8'),
        ),
        plot_bgcolor='#0F172A',
        paper_bgcolor='#1E293B',
        margin=dict(l=40, r=20, t=50, b=60),
        height=360,
        font=dict(family='Inter', color='#94A3B8'),
        showlegend=False,
    )
    return fig


def make_gauge(value, title, max_val=100, suffix="%", color=None):
    if color is None:
        color = '#4ADE80' if value >= 55 else ('#FBBF24' if value >= 45 else '#F87171')
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=value,
            title=dict(text=title, font=dict(size=14, color='#94A3B8')),
            number=dict(suffix=suffix, font=dict(size=28, color=color)),
            gauge=dict(
                axis=dict(range=[0, max_val], tickfont=dict(size=10, color='#64748B'),
                          tickcolor='#334155', linecolor='#334155'),
                bar=dict(color=color, thickness=0.7),
                bgcolor='#1E293B',
                borderwidth=0,
                steps=[
                    dict(range=[0, max_val * 0.45], color='rgba(248,113,113,0.15)'),
                    dict(range=[max_val * 0.45, max_val * 0.55], color='rgba(251,191,36,0.15)'),
                    dict(range=[max_val * 0.55, max_val], color='rgba(74,222,128,0.15)'),
                ],
            ),
        )
    )
    fig.update_layout(
        height=240,
        margin=dict(l=20, r=20, t=40, b=10),
        paper_bgcolor='#1E293B',
        font=dict(family='Inter', color='#94A3B8'),
    )
    return fig


def make_line_chart(df_chart, x_col, y_cols, title):
    fig = go.Figure()
    palette = ['#38BDF8', '#4ADE80', '#F87171', '#FBBF24']
    for i, col in enumerate(y_cols):
        fig.add_trace(
            go.Scatter(
                x=df_chart[x_col],
                y=df_chart[col],
                name=col,
                mode='lines+markers',
                line=dict(color=palette[i % len(palette)], width=2.5),
                marker=dict(size=6),
            )
        )
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color='#E2E8F0'), x=0),
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color='#94A3B8'), linecolor='#334155'),
        yaxis=dict(showgrid=True, gridcolor='#1E293B', zeroline=False, tickfont=dict(size=10, color='#94A3B8')),
        plot_bgcolor='#0F172A',
        paper_bgcolor='#1E293B',
        margin=dict(l=40, r=20, t=50, b=40),
        height=320,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                    font=dict(color='#94A3B8'), bgcolor='rgba(0,0,0,0)'),
        font=dict(family='Inter', color='#94A3B8'),
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
                <h1 style="margin:0;font-size:1.7rem;font-weight:800;color:#F1F5F9;">
                    Spiral Concentrator Analysis
                </h1>
                <p style="margin:0.2rem 0 0;color:#94A3B8;font-size:0.9rem;">
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
    sens_df = pd.read_excel(path, sheet_name='Sensitivity Analysis Spiral 1', header=1)
    sens_df.columns = sens_df.columns.str.strip()
    sens_df = sens_df.rename(columns={'% Solid': 'Percent Solid'})
    sens_df['Condition'] = sens_df['Condition'].ffill()
    for col in ['Flowrate (L/hr)', 'Slurry Weight (g)', 'Dry Solid Weight (g)', 'Percent Solid']:
        if col in sens_df.columns:
            sens_df[col] = pd.to_numeric(sens_df[col], errors='coerce')
    if 'Percent Solid' in sens_df.columns and sens_df['Percent Solid'].max() <= 1.0:
        sens_df['Percent Solid'] = sens_df['Percent Solid'] * 100
    sens_df['Solids Flow'] = sens_df['Flowrate (L/hr)'] * (sens_df['Percent Solid'] / 100) * SLURRY_DENSITY
    sens_df = normalize_products(sens_df, 'Product Type')

    sens_summary = []
    for condition in sens_df['Condition'].dropna().unique():
        cond_data = sens_df[sens_df['Condition'] == condition]
        total_flow       = cond_data['Flowrate (L/hr)'].sum()
        calculated_feed  = cond_data['Solids Flow'].sum()
        feed_solids_pct  = (calculated_feed / total_flow * 100) if total_flow > 0 else 0
        conc_solids      = cond_data[cond_data['Product Type'] == 'Concentrate']['Solids Flow'].sum()
        middling_solids  = cond_data[cond_data['Product Type'] == 'Middling']['Solids Flow'].sum()
        tailing_solids   = cond_data[cond_data['Product Type'] == 'Tailings']['Solids Flow'].sum()
        solid_yield_conc = (conc_solids    / calculated_feed * 100) if calculated_feed > 0 else 0
        middling_fraction= (middling_solids / calculated_feed * 100) if calculated_feed > 0 else 0
        tailing_fraction = (tailing_solids  / calculated_feed * 100) if calculated_feed > 0 else 0
        score_primary    = solid_yield_conc - 0.3 * middling_fraction

        condition_str = str(condition)
        splitter = 'Mid' if 'Medium Splitter' in condition_str or 'Mid Splitter' in condition_str else \
                   'Narrow' if 'Narrow Splitter' in condition_str else \
                   'Open' if 'Open Splitter' in condition_str else 'Unknown'
        solids_level = 'Low' if 'Lowest Solid' in condition_str else \
                       'Medium' if ('Medium Solid' in condition_str or 'Mid Solid' in condition_str) else \
                       'High' if 'Highest Solid' in condition_str else 'Unknown'

        sens_summary.append({
            'Condition': condition,
            'Calculated Feed Solids %': feed_solids_pct,
            'Splitter Position': splitter,
            'Solids Level': solids_level,
            'Concentrate Solid Yield %': solid_yield_conc,
            'Concentrate Solids (tons/hr)': conc_solids / 1000,
            'Middling Fraction %': middling_fraction,
            'Tailing Fraction %': tailing_fraction,
            'score_primary': score_primary,
        })

    sens_df_summary = pd.DataFrame(sens_summary).sort_values('score_primary', ascending=False).reset_index(drop=True)
    df_s1 = sens_df_summary.rename(columns={
        'Calculated Feed Solids %': 'feed_solids',
        'Splitter Position': 'splitter',
        'Concentrate Solid Yield %': 'yield_conc',
        'Middling Fraction %': 'middling',
    }).copy()

    # Sensitivity Analysis – Spiral 5
    sens_df_spiral5 = pd.read_excel(path, sheet_name='Sensitivity Analysis Spiral 5', header=1)
    sens_df_spiral5.columns = sens_df_spiral5.columns.str.strip()
    sens_df_spiral5 = sens_df_spiral5.rename(columns={'% Solid': 'Percent Solid'})
    sens_df_spiral5['Condition'] = sens_df_spiral5['Condition'].ffill()
    for col in ['Flowrate (L/hr)', 'Slurry Weight (g)', 'Dry Solid Weight (g)', 'Percent Solid']:
        if col in sens_df_spiral5.columns:
            sens_df_spiral5[col] = pd.to_numeric(sens_df_spiral5[col], errors='coerce')
    if 'Percent Solid' in sens_df_spiral5.columns and sens_df_spiral5['Percent Solid'].max() <= 1.0:
        sens_df_spiral5['Percent Solid'] = sens_df_spiral5['Percent Solid'] * 100
    sens_df_spiral5['Solids Flow'] = (
        sens_df_spiral5['Flowrate (L/hr)'] * (sens_df_spiral5['Percent Solid'] / 100) * SLURRY_DENSITY
    )
    sens_df_spiral5 = normalize_products(sens_df_spiral5, 'Product Type')

    sens_summary_spiral5 = []
    for condition in sens_df_spiral5['Condition'].dropna().unique():
        cond_data = sens_df_spiral5[sens_df_spiral5['Condition'] == condition]
        total_flow      = cond_data['Flowrate (L/hr)'].sum()
        calculated_feed = cond_data['Solids Flow'].sum()
        feed_solids_pct = (calculated_feed / total_flow * 100) if total_flow > 0 else 0
        conc_solids     = cond_data[cond_data['Product Type'] == 'Concentrate']['Solids Flow'].sum()
        middling_solids = cond_data[cond_data['Product Type'] == 'Middling']['Solids Flow'].sum()
        tailing_solids  = cond_data[cond_data['Product Type'] == 'Tailings']['Solids Flow'].sum()
        solid_yield     = (conc_solids    / calculated_feed * 100) if calculated_feed > 0 else 0
        middling_fraction=(middling_solids / calculated_feed * 100) if calculated_feed > 0 else 0
        tailing_fraction= (tailing_solids  / calculated_feed * 100) if calculated_feed > 0 else 0
        score_secondary = solid_yield - 0.6 * middling_fraction

        condition_str = str(condition)
        splitter = 'Mid' if 'Medium Splitter' in condition_str or 'Mid Splitter' in condition_str else \
                   'Narrow' if 'Narrow Splitter' in condition_str else \
                   'Open' if 'Open Splitter' in condition_str else 'Unknown'
        solids_level = 'Low' if 'Lowest Solid' in condition_str else \
                       'Medium' if ('Medium Solid' in condition_str or 'Mid Solid' in condition_str) else \
                       'High' if 'Highest Solid' in condition_str else 'Unknown'

        sens_summary_spiral5.append({
            'Condition': condition,
            'Calculated Feed Solids %': feed_solids_pct,
            'Splitter Position': splitter,
            'Solids Level': solids_level,
            'Solid Yield %': solid_yield,
            'Middling Fraction %': middling_fraction,
            'Tailing Fraction %': tailing_fraction,
            'score_secondary': score_secondary,
        })

    sens_df_summary_spiral5 = (
        pd.DataFrame(sens_summary_spiral5)
        .sort_values('score_secondary', ascending=False)
        .reset_index(drop=True)
    )
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

    # ── MAIN PAGE ─────────────────────────────────────────────────────────────

    # Always-visible: slim KPI strip
    st.markdown("<br>", unsafe_allow_html=True)
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

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Main navigation tabs ──────────────────────────────────────────────────
    main_tabs = st.tabs([
        "📊 Overview",
        "🔮 Production",
        "🔩 Spiral Performance",
        "💧 Feed & Hydraulics",
        "♻️ Recycle Analysis",
        "🔬 Sensitivity Analysis",
    ])

    # Tab 1 — Overview
    with main_tabs[0]:
        col_gauge, col_mb = st.columns([1, 2])
        with col_gauge:
            st.plotly_chart(make_gauge(recovery, "Recovery Rate"), use_container_width=True)
        with col_mb:
            section_heading("⚖️", "Mass Balance")
            info_panel("Feed is calculated from final outputs (Concentrate + Tailing). Middling is internal recycle.")
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

        loss_pct = (tailing_solids_total / plant_feed * 100) if plant_feed > 0 else 0
        section_heading("📉", "Loss Summary")
        loss_cols = st.columns(2)
        with loss_cols[0]:
            st.metric("Tailing Loss %", f"{loss_pct:.1f}%")
        with loss_cols[1]:
            st.caption(f"Tailing = {tailing_daily:.2f} TPD  ({loss_pct:.1f}% of plant feed)")

        section_heading("🚨", "Alerts & Recommendations")

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
            spiral_num = int(row['Spiral'])
            if row['Middling %'] > 40:
                alerts.append(("danger", f"🔴 Spiral {spiral_num}", "High middling → recycle overload"))
            elif row['Middling %'] > 30:
                alerts.append(("warning", f"🟡 Spiral {spiral_num}", "Moderate middling"))
            if row['Tailing %'] > 35:
                alerts.append(("danger", f"🔴 Spiral {spiral_num}", "High loss to tailing"))

        alerts = alerts[:4]
        if alerts:
            for variant, alert_title, msg in alerts:
                pro_alert(alert_title, msg, variant)
        else:
            st.markdown('<div class="pro-alert pro-alert-success">✅ <strong>All systems nominal</strong> — No critical alerts detected.</div>', unsafe_allow_html=True)

        if recovery < 45:
            st.markdown(
                f"""<div class="pro-alert pro-alert-danger">
                <strong>🔴 LOW RECOVERY — Recommended Action:</strong><br>
                Adjust Spiral 1: Feed Solids {best_s1['feed_solids']:.1f}% · Splitter: {best_s1['splitter']}<br>
                <em>This condition gave highest concentrate recovery in sensitivity analysis.</em>
                </div>""",
                unsafe_allow_html=True,
            )

        if (all_perf_df['Middling %'] > 40).any():
            st.markdown(
                f"""<div class="pro-alert pro-alert-warning">
                <strong>🟡 HIGH RECYCLE LOAD — Optimize Spiral 5:</strong><br>
                Feed Solids {best_s5['feed_solids']:.1f}% · Splitter: {best_s5['splitter']}<br>
                <em>This condition minimizes middling and improves cleaning efficiency.</em>
                </div>""",
                unsafe_allow_html=True,
            )

        if tail_day > 90:
            st.markdown(
                f"""<div class="pro-alert pro-alert-danger">
                <strong>🔴 HIGH LOSS TO TAILING — Recommended Action:</strong><br>
                Improve primary recovery (Spiral 1): Feed Solids {best_s1['feed_solids']:.1f}% · Splitter: {best_s1['splitter']}
                </div>""",
                unsafe_allow_html=True,
            )

    # Tab 2 — Production
    with main_tabs[1]:
        section_heading("🔮", "What-If Production Simulation")

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

        best_yield_s5     = best_s5['yield_conc']
        combined_yield    = (best_yield_s1 + best_yield_s5) / 2
        new_conc_combined = current_feed * (combined_yield / 100)
        gain_combined     = new_conc_combined - current_conc

        with st.expander("🔎 Full optimisation comparison"):
            sim_data = pd.DataFrame({
                'Scenario': ['Current', 'Spiral 1 Optimised', 'Full Optimisation'],
                'Concentrate TPD': [current_conc, new_conc, new_conc_combined],
            })
            fig = make_bar_chart(sim_data, 'Scenario', 'Concentrate TPD', 'Production Scenarios', 'Concentrate (TPD)')
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        section_heading("📅", "Daily Production Tracking")

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

        if not df_history.empty:
            df_history['Date'] = pd.to_datetime(df_history['Date'])

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

            avg_recovery = df_history['Recovery'].mean()
            st.metric("📊 Average Recovery (All Time)", f"{avg_recovery:.1f}%")

            selected_range = st.date_input(
                "📅 Filter by Date Range",
                [df_history['Date'].min().date(), df_history['Date'].max().date()],
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
            info_panel("No historical data yet. Click 'Save Today's Data' to start tracking.")

    # Tab 3 — Spiral Performance
    with main_tabs[2]:
        section_heading("🔩", f"Spiral Performance — Spiral {selected_spiral}")

        spiral_df   = df[df['Spiral unit'] == selected_spiral].copy()
        spiral_conc = spiral_df[spiral_df['Product'] == 'Concentrate']['Solids Flow'].sum()
        sel_production = spiral_conc * EFFECTIVE_HOURS / 1000
        selected_row   = all_perf_df[all_perf_df['Spiral'] == int(selected_spiral)]
        sel_yield      = selected_row.iloc[0]['Solid Yield %'] if not selected_row.empty else 0

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

    # Tab 4 — Feed & Hydraulics
    with main_tabs[3]:
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
        group_a_yield    = all_perf_df[all_perf_df['Spiral'].isin(group_A)]['Solid Yield %'].mean()
        group_b_yield    = all_perf_df[all_perf_df['Spiral'].isin(group_B)]['Solid Yield %'].mean()

        feed_overview = pd.DataFrame({
            'Group': ['A (1-4)', 'B (7-8)'],
            'Internal Feed (tons/hr)': [group_a_internal, group_b_internal],
            'Average Yield (%)': [group_a_yield, group_b_yield],
        })
        st.dataframe(feed_overview, hide_index=True, use_container_width=True)
        st.caption("Internal Feed = Concentrate + Middling + Tailing per group (for yield calculations only).")

        section_heading("📊", "Group Performance Analysis")
        for group_name, group_spirals in [("A (1-4)", group_A), ("B (7-8)", group_B)]:
            with st.expander(f"Group {group_name}", expanded=True):
                group_perf = all_perf_df[all_perf_df['Spiral'].isin(group_spirals)].copy()
                if not group_perf.empty:
                    group_perf_display = group_perf[['Spiral', 'Solid Yield %', 'Middling %', 'Tailing %']].rename(
                        columns={'Solid Yield %': 'Yield (%)'}
                    ).sort_values('Spiral')
                    st.dataframe(group_perf_display.style.background_gradient(subset=['Yield (%)'], cmap='Greens')
                                                         .format({'Yield (%)': '{:.1f}', 'Middling %': '{:.1f}', 'Tailing %': '{:.1f}'}),
                                 hide_index=True, use_container_width=True)

                    group_perf = group_perf.copy()
                    group_perf['score'] = group_perf['Solid Yield %'] - group_perf['Middling %'] * 0.5
                    best_spiral_row = group_perf.loc[group_perf['score'].idxmax()]
                    best_sp  = int(best_spiral_row['Spiral'])
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

    # Tab 5 — Recycle Analysis
    with main_tabs[4]:
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
        recycle_tph   = recycle_kgph / 1000
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
                colors=['#FBBF24', '#F87171'],
            )
            st.plotly_chart(fig_mid, use_container_width=True)
            st.dataframe(
                group_c_data[['Spiral', 'Solid Yield %', 'Middling %', 'Tailing %']].style
                .background_gradient(subset=['Middling %'], cmap='Oranges')
                .format({'Solid Yield %': '{:.1f}', 'Middling %': '{:.1f}', 'Tailing %': '{:.1f}'}),
                hide_index=True,
                use_container_width=True,
            )

    # Tab 6 — Sensitivity Analysis
    with main_tabs[5]:
        section_heading("🔬", "Sensitivity Analysis")

        st.markdown("#### 🔵 Spiral 1 — Primary Concentrator")
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
            colors=['#FBBF24', '#F87171', '#FB923C', '#FDE68A'],
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
