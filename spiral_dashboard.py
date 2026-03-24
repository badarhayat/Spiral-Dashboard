import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import io
from datetime import date

SLURRY_DENSITY = 1.2  # kg/L for heavy mineral placer slurry
EFFECTIVE_HOURS = 11
VALID_PRODUCTS = {'Concentrate', 'Middling', 'Tailings'}


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
    df = df.rename(columns={
        '% Solid': 'Percent Solid',
    })

    # Fill spiral unit names (forward fill) and keep only product rows used in the model.
    df['Spiral unit'] = df['Spiral unit'].ffill()
    df = df[df['Product'].notna()]
    df = normalize_products(df, 'Product')

    # Convert numeric columns
    for col in ['Flowrate (L/hr)', 'Slurry Weight (g)', 'Dry Solid Weight (g)', 'Percent Solid']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # If percent fields are in 0-1 range, convert to 0-100 for user display.
    if 'Percent Solid' in df.columns and df['Percent Solid'].max() <= 1.0:
        df['Percent Solid'] = df['Percent Solid'] * 100

    # Standard aliases for solids calculations.
    df['Flowrate'] = df['Flowrate (L/hr)']
    df['Dry Weight'] = df['Dry Solid Weight (g)']
    df['Slurry Weight'] = df['Slurry Weight (g)']

    # User formula: solids percent and solids flow based on dry/slurry ratio and density.
    df['Solids %'] = (df['Dry Weight'] / df['Slurry Weight']) * 100
    df['Solids Flow (kg/hr)'] = (
        df['Flowrate'] *
        (df['Dry Weight'] / df['Slurry Weight']) *
        SLURRY_DENSITY
    )

    # Keep compatibility with existing downstream code.
    df['Solids Flow'] = df['Solids Flow (kg/hr)']

    # Total solids per spiral
    total_solids = df.groupby('Spiral unit')['Solids Flow'].transform('sum')

    # Solid yield to each row's product
    df['Solid Yield %'] = (df['Solids Flow'] / total_solids) * 100

    # Create a group summary
    group = (
        df.groupby(['Spiral unit', 'Product'])
        .agg({
            'Flowrate (L/hr)': 'sum',
            'Slurry Weight (g)': 'sum',
            'Dry Solid Weight (g)': 'sum',
            'Solids Flow': 'sum',
            'Percent Solid': 'mean',
            'Solid Yield %': 'mean'
        })
        .reset_index()
    )

    return df, group


def load_uploaded_daily_data(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    required_cols = ['Spiral unit', 'Product', 'Flowrate', 'Slurry Weight', 'Dry Weight']
    if not all(col in df.columns for col in required_cols):
        st.error("Excel format incorrect. Please use template.")
        st.stop()

    for col in ['Flowrate', 'Slurry Weight', 'Dry Weight']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = normalize_products(df, 'Product')
    if df.empty:
        st.error("No valid product rows found. Use only Concentrate, Middling, or Tailing.")
        st.stop()

    density = 1.2
    df['Solids Flow'] = (
        df['Flowrate'] *
        (df['Dry Weight'] / df['Slurry Weight']) *
        density
    )

    # Keep compatibility aliases used elsewhere in the app.
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
            'Solid Yield %': 'mean'
        })
        .reset_index()
    )

    return df, group

def plot_bar(data, x, y, title, ylabel):
    # Use larger figure size for better visibility
    fig, ax = plt.subplots(figsize=(12, 8))

    # Consistent professional color scheme
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']

    # Create bars with consistent colors
    bars = ax.bar(data[x], data[y], color=colors[:len(data)], edgecolor='black', linewidth=0.5, alpha=0.8)

    # Enhanced title and labels
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20, color='#2c3e50')
    ax.set_xlabel(x, fontsize=14, fontweight='medium', color='#34495e')
    ax.set_ylabel(ylabel, fontsize=14, fontweight='medium', color='#34495e')

    # Improve x-axis labels
    plt.xticks(rotation=45, ha='right', fontsize=12)
    plt.yticks(fontsize=12)

    # Clean grid and spines
    ax.grid(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(0.5)
    ax.spines['bottom'].set_linewidth(0.5)

    # Keep white chart background for consistency
    ax.set_facecolor('#FFFFFF')

    # Add value labels on bars for clarity
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + max(data[y])*0.01,
                f'{height:.1f}', ha='center', va='bottom', fontsize=10, fontweight='medium')

    plt.tight_layout()
    return fig


def kpi_card(title, value, unit="", color="#1f77b4"):
    st.markdown(
        f"""
        <div style="
            background-color: white;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            text-align: center;
        ">
            <h4 style="margin:0; color:gray;">{title}</h4>
            <h2 style="margin:5px; color:{color};">{value}</h2>
            <p style="margin:0; color:gray;">{unit}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def generate_pdf_report(reference_spiral, highest_yield, lowest_middling, lowest_tailing, recommendations_text):
    report_path = 'spiral_report.pdf'
    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.axis('off')

    lines = [
        'Spiral Concentrator Analysis Report',
        f'Reference Spiral: Spiral {reference_spiral}',
        '',
        'KPI Summary:',
        f'  - Highest Solid Yield: {highest_yield:.1f}%',
        f'  - Lowest Middling: {lowest_middling:.1f}%',
        f'  - Lowest Tailing: {lowest_tailing:.1f}%',
        '',
        'Key Recommendations:',
    ]

    y = 0.95
    for line in lines:
        ax.text(0.1, y, line, fontsize=14, fontweight='bold' if line.endswith(':') or line.startswith('Spiral') else 'normal', va='top')
        y -= 0.05

    for paragraph in recommendations_text.strip().split('\n'):
        ax.text(0.1, y, f'- {paragraph.strip()}', fontsize=12, va='top')
        y -= 0.04

    fig.savefig(report_path, bbox_inches='tight')
    plt.close(fig)
    return report_path

def main():
    st.set_page_config(page_title='Spiral Concentrator Analysis', layout='wide')

    # Top branding with logo and title
    col_logo, col_title = st.columns([1, 8])
    with col_logo:
        st.image('logo.png', width=150)
    with col_title:
        st.markdown('## 🏭 Spiral Concentrator Analysis Dashboard')
        st.markdown('#### Commercial-grade solids-based spiral performance analysis')

    template = pd.DataFrame({
        'Spiral unit': [],
        'Product': [],
        'Flowrate': [],
        'Slurry Weight': [],
        'Dry Weight': []
    })
    template_buffer = io.BytesIO()
    with pd.ExcelWriter(template_buffer) as writer:
        template.to_excel(writer, index=False, sheet_name='Daily Data')
    template_bytes = template_buffer.getvalue()

    uploaded_file = st.file_uploader("Upload Daily Plant Data (Excel)", type=["xlsx"])
    st.download_button(
        "Download Excel Template",
        data=template_bytes,
        file_name="plant_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    path = 'Spiral Plant Sheet.xlsx'
    if uploaded_file is not None:
        df, group = load_uploaded_daily_data(uploaded_file)
        st.success("✅ Data uploaded successfully. Dashboard updated.")
    else:
        df, group = load_data(path)

    st.sidebar.header('Controls')
    spirals = sorted(df['Spiral unit'].dropna().unique())
    selected_spiral = st.sidebar.selectbox('Select Spiral Unit', spirals)

    # Pre-compute all dataframes needed across tabs
    # Define circuit
    primary_spirals = [1, 2, 3, 4, 7, 8]
    secondary_spirals = [5, 6]
    
    # Define feed groups with equal feed assumptions
    group_A = [1, 2, 3, 4]   # same feed tank
    group_B = [7, 8]         # same feed tank
    group_C = [5, 6]         # recycle circuit
    
    # All spirals solid-based analysis
    all_spirals = sorted(df['Spiral unit'].dropna().unique())
    all_perf_list = []

    for spiral in all_spirals:
        spiral_data = df[df['Spiral unit'] == spiral]
        if spiral_data.empty:
            continue

        calculated_feed = spiral_data['Solids Flow'].sum()
        conc_solids = spiral_data[spiral_data['Product'] == 'Concentrate']['Solids Flow'].sum()
        middling_solids = spiral_data[spiral_data['Product'] == 'Middling']['Solids Flow'].sum()
        tailing_solids = spiral_data[spiral_data['Product'] == 'Tailings']['Solids Flow'].sum()

        solid_yield = (conc_solids / calculated_feed * 100) if calculated_feed > 0 else 0
        middling_frac = (middling_solids / calculated_feed * 100) if calculated_feed > 0 else 0
        tailing_frac = (tailing_solids / calculated_feed * 100) if calculated_feed > 0 else 0

        # Different scoring for primary vs secondary spirals
        if spiral in secondary_spirals:
            score = (solid_yield * 0.4) - (middling_frac * 0.6) - (tailing_frac * 0.2)
        else:
            score = solid_yield - 0.4 * middling_frac - 0.2 * tailing_frac

        all_perf_list.append({
            'Spiral': int(spiral),
            'Solid Yield %': solid_yield,
            'Middling %': middling_frac,
            'Tailing %': tailing_frac,
            'Score': score
        })

    all_perf_df = pd.DataFrame(all_perf_list)
    all_perf_df = all_perf_df.sort_values('Spiral').reset_index(drop=True)

    st.markdown("---")

    # Define concentrate dataframe early for use in sensitivity and main page
    conc_df = df[df['Product'] == 'Concentrate'].copy()

    # Sensitivity analysis
    sens_df = pd.read_excel(path, sheet_name='Sensitivity Analysis Spiral 1', header=1)
    sens_df.columns = sens_df.columns.str.strip()
    sens_df = sens_df.rename(columns={
        '% Solid': 'Percent Solid',
    })

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
        total_flow = cond_data['Flowrate (L/hr)'].sum()
        calculated_feed = cond_data['Solids Flow'].sum()
        feed_solids_pct = (calculated_feed / total_flow * 100) if total_flow > 0 else 0

        conc_solids = cond_data[cond_data['Product Type'] == 'Concentrate']['Solids Flow'].sum()
        middling_solids = cond_data[cond_data['Product Type'] == 'Middling']['Solids Flow'].sum()
        tailing_solids = cond_data[cond_data['Product Type'] == 'Tailings']['Solids Flow'].sum()

        solid_yield_conc = (conc_solids / calculated_feed * 100) if calculated_feed > 0 else 0
        middling_fraction = (middling_solids / calculated_feed * 100) if calculated_feed > 0 else 0
        tailing_fraction = (tailing_solids / calculated_feed * 100) if calculated_feed > 0 else 0

        score_primary = solid_yield_conc - 0.3 * middling_fraction

        condition_str = str(condition)
        if 'Medium Splitter' in condition_str or 'Mid Splitter' in condition_str:
            splitter = 'Mid'
        elif 'Narrow Splitter' in condition_str:
            splitter = 'Narrow'
        elif 'Open Splitter' in condition_str:
            splitter = 'Open'
        else:
            splitter = 'Unknown'

        if 'Lowest Solid' in condition_str:
            solids_level = 'Low'
        elif 'Medium Solid' in condition_str or 'Mid Solid' in condition_str:
            solids_level = 'Medium'
        elif 'Highest Solid' in condition_str:
            solids_level = 'High'
        else:
            solids_level = 'Unknown'

        sens_summary.append({
            'Condition': condition,
            'Calculated Feed Solids %': feed_solids_pct,
            'Splitter Position': splitter,
            'Solids Level': solids_level,
            'Concentrate Solid Yield %': solid_yield_conc,
            'Concentrate Solids (tons/hr)': conc_solids / 1000,
            'Middling Fraction %': middling_fraction,
            'Tailing Fraction %': tailing_fraction,
            'score_primary': score_primary
        })

    sens_df_summary = pd.DataFrame(sens_summary)
    sens_df_summary = sens_df_summary.sort_values('score_primary', ascending=False).reset_index(drop=True)

    df_s1 = sens_df_summary.rename(columns={
        'Calculated Feed Solids %': 'feed_solids',
        'Splitter Position': 'splitter',
        'Concentrate Solid Yield %': 'yield_conc',
        'Middling Fraction %': 'middling'
    }).copy()

    # Sensitivity analysis for Spiral 5 (secondary spiral treating middlings)
    sens_df_spiral5 = pd.read_excel(path, sheet_name='Sensitivity Analysis Spiral 5', header=1)
    sens_df_spiral5.columns = sens_df_spiral5.columns.str.strip()
    sens_df_spiral5 = sens_df_spiral5.rename(columns={
        '% Solid': 'Percent Solid',
    })

    sens_df_spiral5['Condition'] = sens_df_spiral5['Condition'].ffill()

    for col in ['Flowrate (L/hr)', 'Slurry Weight (g)', 'Dry Solid Weight (g)', 'Percent Solid']:
        if col in sens_df_spiral5.columns:
            sens_df_spiral5[col] = pd.to_numeric(sens_df_spiral5[col], errors='coerce')

    if 'Percent Solid' in sens_df_spiral5.columns and sens_df_spiral5['Percent Solid'].max() <= 1.0:
        sens_df_spiral5['Percent Solid'] = sens_df_spiral5['Percent Solid'] * 100

    sens_df_spiral5['Solids Flow'] = sens_df_spiral5['Flowrate (L/hr)'] * (sens_df_spiral5['Percent Solid'] / 100) * SLURRY_DENSITY
    sens_df_spiral5 = normalize_products(sens_df_spiral5, 'Product Type')

    sens_summary_spiral5 = []
    for condition in sens_df_spiral5['Condition'].dropna().unique():
        cond_data = sens_df_spiral5[sens_df_spiral5['Condition'] == condition]
        total_flow = cond_data['Flowrate (L/hr)'].sum()
        calculated_feed = cond_data['Solids Flow'].sum()
        feed_solids_pct = (calculated_feed / total_flow * 100) if total_flow > 0 else 0

        conc_solids = cond_data[cond_data['Product Type'] == 'Concentrate']['Solids Flow'].sum()
        middling_solids = cond_data[cond_data['Product Type'] == 'Middling']['Solids Flow'].sum()
        tailing_solids = cond_data[cond_data['Product Type'] == 'Tailings']['Solids Flow'].sum()

        # Solid-based calculations for Spiral 5
        solid_yield = (conc_solids / calculated_feed * 100) if calculated_feed > 0 else 0
        middling_fraction = (middling_solids / calculated_feed * 100) if calculated_feed > 0 else 0
        tailing_fraction = (tailing_solids / calculated_feed * 100) if calculated_feed > 0 else 0

        # Secondary score emphasizes middling penalty for recycle control.
        score_secondary = solid_yield - 0.6 * middling_fraction

        condition_str = str(condition)
        if 'Medium Splitter' in condition_str or 'Mid Splitter' in condition_str:
            splitter = 'Mid'
        elif 'Narrow Splitter' in condition_str:
            splitter = 'Narrow'
        elif 'Open Splitter' in condition_str:
            splitter = 'Open'
        else:
            splitter = 'Unknown'

        if 'Lowest Solid' in condition_str:
            solids_level = 'Low'
        elif 'Medium Solid' in condition_str or 'Mid Solid' in condition_str:
            solids_level = 'Medium'
        elif 'Highest Solid' in condition_str:
            solids_level = 'High'
        else:
            solids_level = 'Unknown'

        sens_summary_spiral5.append({
            'Condition': condition,
            'Calculated Feed Solids %': feed_solids_pct,
            'Splitter Position': splitter,
            'Solids Level': solids_level,
            'Solid Yield %': solid_yield,
            'Middling Fraction %': middling_fraction,
            'Tailing Fraction %': tailing_fraction,
            'score_secondary': score_secondary
        })

    sens_df_summary_spiral5 = pd.DataFrame(sens_summary_spiral5)
    sens_df_summary_spiral5 = sens_df_summary_spiral5.sort_values('score_secondary', ascending=False).reset_index(drop=True)

    df_s5 = sens_df_summary_spiral5.rename(columns={
        'Calculated Feed Solids %': 'feed_solids',
        'Splitter Position': 'splitter',
        'Solid Yield %': 'yield_conc',
        'Middling Fraction %': 'middling'
    }).copy()

    best_s1 = df_s1.loc[df_s1['yield_conc'].idxmax()]
    best_s5 = df_s5.loc[(df_s5['yield_conc'] - 0.6 * df_s5['middling']).idxmax()]

    # Main page summaries (minimal UI)
    # Final outputs in base units (kg/hr)
    conc_solids_total = conc_df['Solids Flow'].sum()
    tailing_solids_total = df[df['Product'] == 'Tailings']['Solids Flow'].sum()
    
    # Main page mass balance: Feed = Concentrate + Tailing (no middling)
    plant_feed = conc_solids_total + tailing_solids_total
    
    # Convert display units: TPH = kg/hr / 1000, TPD = TPH * hours
    plant_feed_tph = plant_feed / 1000
    plant_feed_daily = plant_feed_tph * EFFECTIVE_HOURS
    
    concentrate_tph = conc_solids_total / 1000
    concentrate_daily = concentrate_tph * EFFECTIVE_HOURS
    
    tailing_tph = tailing_solids_total / 1000
    tailing_daily = tailing_tph * EFFECTIVE_HOURS

    conc_hr = concentrate_tph
    feed_hr = plant_feed_tph
    tail_hr = tailing_tph
    feed_day = plant_feed_daily
    conc_day = concentrate_daily
    tail_day = tailing_daily
    recovery = (conc_hr / feed_hr) * 100 if feed_hr > 0 else 0

    group_conc = (
        group[group['Product'] == 'Concentrate'][['Spiral unit', 'Solid Yield %']]
        .rename(columns={'Solid Yield %': 'Concentrate Yield (%)'})
        .reset_index(drop=True)
    )
    best_spiral = int(group_conc.loc[group_conc['Concentrate Yield (%)'].idxmax(), 'Spiral unit']) if not group_conc.empty else 0
    worst_spiral = int(group_conc.loc[group_conc['Concentrate Yield (%)'].idxmin(), 'Spiral unit']) if not group_conc.empty else 0

    if recovery > 55 and tail_day < 80:
        status = "GOOD"
        status_color = "green"
    elif recovery > 45:
        status = "MODERATE"
        status_color = "orange"
    else:
        status = "POOR"
        status_color = "red"

    group_scores = {
        'Group A': all_perf_df[all_perf_df['Spiral'].isin(group_A)]['Solid Yield %'].mean(),
        'Group B': all_perf_df[all_perf_df['Spiral'].isin(group_B)]['Solid Yield %'].mean(),
        'Group C': all_perf_df[all_perf_df['Spiral'].isin(group_C)]['Solid Yield %'].mean(),
    }
    best_group = max(group_scores, key=lambda k: group_scores[k] if pd.notna(group_scores[k]) else float('-inf'))

    st.markdown("## Main Page")
    st.caption(f"Assumed slurry density factor: {SLURRY_DENSITY:.1f} | Effective hours: {EFFECTIVE_HOURS} h/day")

    st.markdown("### 1. Plant KPIs")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("📦 Production", f"{conc_day:.1f}", "TPD", "#1f77b4")
    with col2:
        kpi_card("📈 Recovery", f"{recovery:.1f}%", "", "green")
    with col3:
        kpi_card("⚠️ Loss", f"{tail_day:.1f}", "TPD", "red")
    with col4:
        kpi_card("🟢 Status", status, "", status_color)

    col1, col2, col3 = st.columns(3)
    with col1:
        kpi_card("Best Spiral", f"S{best_spiral}", "", "green")
    with col2:
        kpi_card("Worst Spiral", f"S{worst_spiral}", "", "red")
    with col3:
        kpi_card("Best Group", best_group, "", "blue")

    st.info("""
Recovery = % of feed converted to concentrate.
Loss = material going to tailing.
Best spiral = highest recovery with low losses.
""")

    alerts = []

    # Recovery alert
    if recovery < 45:
        alerts.append(("🔴 LOW RECOVERY", "Recovery below 45%. Check feed conditions."))
    elif recovery < 55:
        alerts.append(("🟡 MODERATE RECOVERY", "Recovery can be improved."))

    # Tailing loss alert
    if tail_day > 90:
        alerts.append(("🔴 HIGH LOSS", "Too much material going to tailing."))
    elif tail_day > 70:
        alerts.append(("🟡 ELEVATED LOSS", "Monitor tailing losses."))

    # Mass balance alert
    mb_error = (abs(feed_hr - (conc_hr + tail_hr)) / feed_hr * 100) if feed_hr > 0 else 0
    if mb_error > 5:
        alerts.append(("🔴 MASS BALANCE ERROR", "Check calculations/data."))
    elif mb_error > 2:
        alerts.append(("🟡 MASS BALANCE WARNING", "Minor mismatch detected."))

    # Spiral-wise alerts using per-spiral summary
    for _, row in all_perf_df.iterrows():
        spiral = int(row['Spiral'])
        if row['Middling %'] > 40:
            alerts.append((f"🔴 Spiral {spiral}", "High middling -> recycle overload"))
        elif row['Middling %'] > 30:
            alerts.append((f"🟡 Spiral {spiral}", "Moderate middling"))

        if row['Tailing %'] > 35:
            alerts.append((f"🔴 Spiral {spiral}", "High loss to tailing"))

    # Show top-priority alerts only
    alerts = alerts[:3]

    st.subheader("⚠️ Alerts & Recommendations")
    for title, msg in alerts:
        if "🔴" in title:
            st.error(f"{title}: {msg}")
        elif "🟡" in title:
            st.warning(f"{title}: {msg}")
        else:
            st.success(f"{title}: {msg}")

    if recovery < 45:
        st.error(f"""
🔴 LOW RECOVERY

Recommended Action:
- Adjust Spiral 1 to optimal condition:

  - Feed Solids: {best_s1['feed_solids']:.1f}%
  - Splitter: {best_s1['splitter']}

Reason:
This condition gave highest concentrate recovery in sensitivity analysis.
""")

    if (all_perf_df['Middling %'] > 40).any():
        st.warning(f"""
🟡 HIGH RECYCLE LOAD

Recommended Action:
- Optimize Spiral 5:

  - Feed Solids: {best_s5['feed_solids']:.1f}%
  - Splitter: {best_s5['splitter']}

Reason:
This condition minimizes middling and improves cleaning efficiency.
""")

    if tail_day > 90:
        st.error(f"""
🔴 HIGH LOSS TO TAILING

Recommended Action:
- Improve primary recovery (Spiral 1 settings)

  - Feed Solids: {best_s1['feed_solids']:.1f}%
  - Splitter: {best_s1['splitter']}

Reason:
Higher recovery condition reduces valuable material loss.
""")

    if worst_spiral > 0:
        st.error(f"""
🔴 Spiral {worst_spiral} Underperforming

Recommended Action:
Match its settings with best-performing spiral or sensitivity optimum.
""")

    st.info("""
Recommendation Logic:

Spiral 1:
- Selected condition with highest concentrate yield

Spiral 5:
- Selected condition with high yield and low middling

These conditions are derived from plant sensitivity experiments.
""")

    current_feed = feed_day
    current_conc = conc_day
    current_yield = (current_conc / current_feed) * 100 if current_feed > 0 else 0

    best_yield_s1 = best_s1['yield_conc']
    new_conc = current_feed * (best_yield_s1 / 100)
    new_tail = current_feed - new_conc
    gain = new_conc - current_conc

    st.subheader("🔮 What-If Simulation")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Production", f"{current_conc:.2f} TPD")
    with col2:
        st.metric("Projected Production", f"{new_conc:.2f} TPD")
    with col3:
        st.metric("Gain", f"{gain:.2f} TPD")

    if gain > 0:
        st.success(f"📈 Production can increase by {gain:.2f} tons/day")
    else:
        st.warning("No improvement expected")

    st.info(f"""
Simulation based on:

- Feed remains constant: {current_feed:.2f} TPD
- New yield from sensitivity: {best_yield_s1:.2f}%
- Only Spiral 1 settings adjusted

Note:
Actual improvement depends on plant stability.
""")

    best_yield_s5 = best_s5['yield_conc']
    combined_yield = (best_yield_s1 + best_yield_s5) / 2
    new_conc_combined = current_feed * (combined_yield / 100)
    gain_combined = new_conc_combined - current_conc

    st.write({
        "Current": current_conc,
        "Spiral 1 Optimized": new_conc,
        "Full Optimization": new_conc_combined
    })

    today = date.today()
    new_date = pd.to_datetime(today).normalize()
    new_data = pd.DataFrame([{
        "Date": new_date,
        "Feed_TPD": feed_day,
        "Concentrate_TPD": conc_day,
        "Tailing_TPD": tail_day,
        "Recovery": recovery
    }])

    history_path = "plant_history.csv"
    history_columns = ["Date", "Feed_TPD", "Concentrate_TPD", "Tailing_TPD", "Recovery"]

    # Load existing history if available.
    try:
        df_history = pd.read_csv(history_path)
    except Exception:
        df_history = pd.DataFrame(columns=history_columns)

    if not df_history.empty:
        df_history['Date'] = pd.to_datetime(df_history['Date']).dt.normalize()

    # Validation warning before save.
    if (not df_history.empty) and (df_history['Date'] == new_date).any():
        st.warning("Data for this date already exists. It will be overwritten.")

    if st.button("Save Daily Data"):
        existing = df_history.copy()
        if not existing.empty:
            existing['Date'] = pd.to_datetime(existing['Date']).dt.normalize()
            existing = existing[existing['Date'] != new_date]

        df_history = pd.concat([existing, new_data], ignore_index=True)
        df_history = df_history.drop_duplicates(subset=['Date'], keep='last')
        df_history = df_history.sort_values(by='Date').reset_index(drop=True)

        # Save with clean date formatting.
        save_df = df_history.copy()
        save_df['Date'] = pd.to_datetime(save_df['Date']).dt.strftime('%Y-%m-%d')
        save_df.to_csv(history_path, index=False)
        st.success("Daily data saved successfully.")

    if not df_history.empty:
        st.subheader("📈 Daily Production Trend")
        st.line_chart(df_history.set_index('Date')[['Concentrate_TPD']])
        st.line_chart(df_history.set_index('Date')[['Feed_TPD', 'Concentrate_TPD', 'Tailing_TPD']])

        df_history['Month'] = df_history['Date'].dt.to_period('M')
        monthly_total = df_history.groupby('Month')['Concentrate_TPD'].sum()
        monthly_avg = df_history.groupby('Month')['Concentrate_TPD'].mean()
        monthly_total.index = monthly_total.index.astype(str)
        monthly_avg.index = monthly_avg.index.astype(str)

        st.subheader("📅 Monthly Production (tons)")
        st.bar_chart(monthly_total)
        st.subheader("📅 Monthly Avg Production (TPD)")
        st.bar_chart(monthly_avg)

        df_history['Year'] = df_history['Date'].dt.year
        yearly_total = df_history.groupby('Year')['Concentrate_TPD'].sum()
        yearly_avg = df_history.groupby('Year')['Concentrate_TPD'].mean()

        st.subheader("📆 Yearly Production (tons)")
        st.bar_chart(yearly_total)
        st.subheader("📆 Yearly Avg Production (TPD)")
        st.bar_chart(yearly_avg)

        avg_recovery = df_history['Recovery'].mean()
        st.metric("Average Recovery (All Time)", f"{avg_recovery:.1f}%")

        selected_range = st.date_input(
            "Select Date Range",
            [df_history['Date'].min().date(), df_history['Date'].max().date()]
        )

        if isinstance(selected_range, (list, tuple)) and len(selected_range) == 2:
            start_date, end_date = selected_range
            filtered = df_history[
                (df_history['Date'] >= pd.to_datetime(start_date)) &
                (df_history['Date'] <= pd.to_datetime(end_date))
            ]
            if not filtered.empty:
                st.line_chart(filtered.set_index('Date')['Concentrate_TPD'])
            else:
                st.warning("No data in selected date range.")

        with st.expander("Debug: History Data"):
            st.write(df_history)

        st.download_button(
            "Download Report",
            df_history.to_csv(index=False),
            file_name="plant_report.csv",
            mime="text/csv"
        )
    else:
        st.info("No historical data saved yet. Click Save Daily Data to create history.")

    st.markdown("### 2. Mass Balance Summary (Feed = Concentrate + Tailing)")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Plant Feed (TPH)", f"{plant_feed_tph:.1f}")
    with col2:
        st.metric("Plant Feed (TPD)", f"{plant_feed_daily:.2f}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Concentrate (TPH)", f"{concentrate_tph:.1f}")
    with col2:
        st.metric("Concentrate (TPD)", f"{concentrate_daily:.2f}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Tailing (TPH)", f"{tailing_tph:.1f}")
    with col2:
        st.metric("Tailing (TPD)", f"{tailing_daily:.2f}")
    
    st.info("**Mass Balance:** Feed is calculated from final outputs (Concentrate + Tailing) to enforce plant mass balance. Middling is treated as internal recycle and excluded from main page.")

    st.markdown("### 3. Loss Summary")
    loss_pct = (tailing_solids_total / plant_feed * 100) if plant_feed > 0 else 0
    st.metric("Tailing Loss %", f"{loss_pct:.1f}%")
    st.caption(f"Tailing = {tailing_daily:.2f} TPD or {loss_pct:.1f}% of plant feed")

    # Create simplified tabs
    tabs = st.tabs([
        "Spiral Performance",
        "Feed & Hydraulics",
        "Recycle Analysis",
        "Sensitivity Analysis"
    ])

    # Tab 1: Spiral Performance
    with tabs[0]:
        st.markdown(f"## Spiral Performance - Spiral {selected_spiral}")
        spiral_df = df[df['Spiral unit'] == selected_spiral].copy()
        spiral_conc = spiral_df[spiral_df['Product'] == 'Concentrate']['Solids Flow'].sum()
        selected_production = spiral_conc * EFFECTIVE_HOURS / 1000
        selected_row = all_perf_df[all_perf_df['Spiral'] == int(selected_spiral)]
        selected_yield = selected_row.iloc[0]['Solid Yield %'] if not selected_row.empty else 0

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Solid Flow (Production)", f"{selected_production:.2f} tons/day")
        with col2:
            st.metric("Solid Yield", f"{selected_yield:.2f}%")

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
            on='Spiral',
            how='left'
        )
        combined_table['Production (tons/day)'] = combined_table['Production (tons/day)'].fillna(0)
        combined_table = combined_table[[
            'Spiral',
            'Production (tons/day)',
            'Solid Yield %',
            'Middling %',
            'Tailing %'
        ]]
        combined_table = combined_table.rename(columns={'Solid Yield %': 'Yield (%)'})

        st.markdown("Production shows quantity, yield shows separation efficiency.")

        chart_prod = combined_table[['Spiral', 'Production (tons/day)']].copy()
        chart_prod['Spiral'] = chart_prod['Spiral'].astype(str)
        fig = plot_bar(chart_prod, 'Spiral', 'Production (tons/day)', 'Solid Flow by Spiral', 'Production (tons/day)')
        st.pyplot(fig, width='stretch')

        chart_yield = combined_table[['Spiral', 'Yield (%)']].copy()
        chart_yield['Spiral'] = chart_yield['Spiral'].astype(str)
        fig = plot_bar(chart_yield, 'Spiral', 'Yield (%)', 'Solid Yield by Spiral', 'Yield (%)')
        st.pyplot(fig, width='stretch')

        st.markdown("### Combined Performance Table")
        st.dataframe(combined_table, hide_index=True)

    # Tab 2: Feed & Hydraulics
    with tabs[1]:
        st.markdown("## Feed & Hydraulics (Calculated Feed: C + M + T)")

        st.caption("All metrics in this tab use calculated feed only (Concentrate + Middling + Tailing).")

        # Analysis tabs use calculated feed only (C + M + T)
        # Internal feed per spiral (C + M + T)
        internal_feed_by_spiral = (
            df.groupby('Spiral unit', as_index=False)['Solids Flow']
            .sum()
            .rename(columns={'Spiral unit': 'Spiral', 'Solids Flow': 'Internal Feed (tons/hr)'})
        )
        internal_feed_by_spiral['Internal Feed (tons/hr)'] = internal_feed_by_spiral['Internal Feed (tons/hr)'] / 1000
        internal_feed_by_spiral['Spiral'] = internal_feed_by_spiral['Spiral'].astype(str)
        fig = plot_bar(
            internal_feed_by_spiral,
            'Spiral',
            'Internal Feed (tons/hr)',
            'Internal Feed Distribution by Spiral (C + M + T)',
            'Internal Feed (tons/hr)'
        )
        st.pyplot(fig, width='stretch')
        st.caption("Internal Feed = Concentrate + Middling + Tailing. Used for yield calculations, not plant mass balance.")

        # Internal feed = C + M + T for group analysis
        group_a_internal_feed = df[df['Spiral unit'].isin(group_A)]['Solids Flow'].sum() / 1000
        group_b_internal_feed = df[df['Spiral unit'].isin(group_B)]['Solids Flow'].sum() / 1000
        group_a_yield = all_perf_df[all_perf_df['Spiral'].isin(group_A)]['Solid Yield %'].mean()
        group_b_yield = all_perf_df[all_perf_df['Spiral'].isin(group_B)]['Solid Yield %'].mean()

        feed_overview = pd.DataFrame({
            'Group': ['A (1-4)', 'B (7-8)'],
            'Internal Feed (tons/hr)': [group_a_internal_feed, group_b_internal_feed],
            'Average Yield (%)': [group_a_yield, group_b_yield]
        })
        st.dataframe(feed_overview, hide_index=True)
        st.caption("Internal Feed = Concentrate + Middling + Tailing per group (used for yield calculations only)")

        # Group Performance Analysis
        st.markdown("### Group Performance Analysis")
        
        for group_name, group_spirals in [("A (1-4)", group_A), ("B (7-8)", group_B)]:
            st.markdown(f"#### Group {group_name}")
            
            # Get performance data for this group
            group_perf = all_perf_df[all_perf_df['Spiral'].isin(group_spirals)].copy()
            
            if not group_perf.empty:
                group_perf_display = group_perf[['Spiral', 'Solid Yield %', 'Middling %', 'Tailing %']].rename(
                    columns={'Solid Yield %': 'Yield (%)'}
                ).sort_values('Spiral')
                
                st.dataframe(group_perf_display, hide_index=True)
                
                # Identify best spiral: highest yield AND lowest middling
                group_perf['score'] = (group_perf['Solid Yield %'] * 1.0) - (group_perf['Middling %'] * 0.5)
                best_spiral_row = group_perf.loc[group_perf['score'].idxmax()]
                best_spiral = int(best_spiral_row['Spiral'])
                best_yield = best_spiral_row['Solid Yield %']
                best_middling = best_spiral_row['Middling %']
                best_tailing = best_spiral_row['Tailing %']
                
                # Generate performance explanation and recommendation
                st.info(f"""
**Spiral {best_spiral} is performing best in this group.**

Recommendation:
- Increase feed to this spiral
- Adjust other spirals to match its operating conditions
""")
                
                # Show performance status
                explanation = ""
                if best_yield > 70 and best_middling < 20:
                    explanation = "✅ **Best performance:** High recovery with efficient separation"
                elif best_middling >= 20:
                    explanation = "⚠️ **Poor separation:** Excessive recycle load from high middling"
                elif best_tailing > 15:
                    explanation = "⚠️ **High loss:** Significant valuable material lost to tailing"
                else:
                    explanation = "📊 **Moderate performance:** Balanced yield and losses"
                
                st.caption(explanation)

        st.markdown("### Production Projection (Based on Plant Feed)")
        increase = st.slider('Increase Plant Feed (%)', 0, 30, 10)
        factor = 1 + increase / 100
        new_production = plant_feed_daily * factor
        st.metric('Projected Production', f'{new_production:.2f} tons/day')
        if increase > 15:
            st.warning('Higher feed may reduce separation efficiency and increase middling recycle')

    # Tab 3: Recycle Analysis
    with tabs[2]:
        st.markdown("## Recycle Analysis")
        st.info("Middling flow and recycle behavior. Internal feed = C + M + T per spiral.")

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
        circulating_load = (recycle_kgph / primary_middlings_kgph) * 100 if primary_middlings_kgph > 0 else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric('Primary Middlings', f'{primary_middlings_tph:.2f} tons/hr')
        with col2:
            st.metric('Recycled Middlings', f'{recycle_tph:.2f} tons/hr')
        with col3:
            st.metric('Circulating Load %', f'{circulating_load:.1f}%')

        group_c_data = all_perf_df[all_perf_df['Spiral'].isin(group_C)].sort_values('Middling %', ascending=True)
        if not group_c_data.empty:
            middling_chart_c = group_c_data[['Spiral', 'Middling %']].copy()
            middling_chart_c['Spiral'] = middling_chart_c['Spiral'].astype(str)
            fig = plot_bar(middling_chart_c, 'Spiral', 'Middling %', 'Group C Middling % (Lower is Better)', 'Middling %')
            st.pyplot(fig, width='stretch')
            st.dataframe(group_c_data[['Spiral', 'Solid Yield %', 'Middling %', 'Tailing %']], hide_index=True)

    # Tab 4: Sensitivity Analysis
    with tabs[3]:
        st.markdown("## Sensitivity Analysis")

        st.markdown("### Spiral 1")
        st.dataframe(sens_df_summary, hide_index=True)
        yield_data = sens_df_summary[['Condition', 'Concentrate Solid Yield %']].copy()
        fig = plot_bar(yield_data, 'Condition', 'Concentrate Solid Yield %', 'Spiral 1 Concentrate Yield by Condition', 'Yield %')
        st.pyplot(fig, width='stretch')
        
        # Best condition using primary ranking score.
        st.success(f"""
    Spiral 1 Best Condition:

    - Feed Solids: {best_s1['feed_solids']:.1f}%
    - Splitter: {best_s1['splitter']}
    - Yield: {best_s1['yield_conc']:.2f}%

    Reason:
    High recovery with acceptable middling.
    """)

        st.markdown("### Spiral 5")
        st.dataframe(sens_df_summary_spiral5, hide_index=True)
        middling_data_spiral5 = sens_df_summary_spiral5[['Condition', 'Middling Fraction %']].copy()
        fig = plot_bar(middling_data_spiral5, 'Condition', 'Middling Fraction %', 'Spiral 5 Middling Fraction by Condition', 'Middling %')
        st.pyplot(fig, width='stretch')
        
        # Best condition using secondary ranking score.
        st.success(f"""
    Spiral 5 Best Condition:

    - Feed Solids: {best_s5['feed_solids']:.1f}%
    - Splitter: {best_s5['splitter']}
    - Yield: {best_s5['yield_conc']:.2f}%

    Reason:
    Efficient cleaning with low recycle load.
    """)

if __name__ == '__main__':
    main()
