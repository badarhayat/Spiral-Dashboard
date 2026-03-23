import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

@st.cache_data
def load_data(path):
    df = pd.read_excel(path, sheet_name='Spiral Data on Actual Run', header=1)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        '% Solid': 'Percent Solid',
    })

    # Fill spiral unit names (forward fill) and drop invalid rows
    df['Spiral unit'] = df['Spiral unit'].ffill()
    df = df[df['Product'].notna()]

    # Convert numeric columns
    for col in ['Flowrate (L/hr)', 'Slurry Weight (g)', 'Dry Solid Weight (g)', 'Percent Solid']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # If percent fields are in 0-1 range, convert to 0-100 for user display.
    if 'Percent Solid' in df.columns and df['Percent Solid'].max() <= 1.0:
        df['Percent Solid'] = df['Percent Solid'] * 100

    # Calculate solids flow using dry/wet mass ratio: solids_flow = flowrate * (dry_weight / slurry_weight)
    df['Solids Flow'] = df['Flowrate (L/hr)'] * (df['Dry Solid Weight (g)'] / df['Slurry Weight (g)'])

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

    # Feed flow distribution
    feed_df = pd.read_excel(path, sheet_name='Feed Flow Distribution Spiral', header=1)

    return df, group, feed_df

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


def generate_pdf_report(best_spiral, highest_yield, lowest_middling, lowest_tailing, recommendations_text):
    report_path = 'spiral_report.pdf'
    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.axis('off')

    lines = [
        'Spiral Concentrator Analysis Report',
        f'Best Spiral: Spiral {best_spiral}',
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

    path = 'Spiral Plant Sheet.xlsx'
    df, group, feed_df = load_data(path)

    st.sidebar.header('Controls')
    spirals = sorted(df['Spiral unit'].dropna().unique())
    selected_spiral = st.sidebar.selectbox('Select Spiral Unit', spirals)

    # Pre-compute all dataframes needed across tabs
    # Primary spirals performance
    primary_spirals = [1, 2, 3, 4, 7, 8]
    perf_df = df[df['Spiral unit'].isin(primary_spirals)].copy()

    summary_list = []
    for spiral in primary_spirals:
        spiral_data = perf_df[perf_df['Spiral unit'] == spiral]
        if spiral_data.empty:
            continue

        total_feed = spiral_data['Flowrate (L/hr)'].sum()
        total_solids = spiral_data['Solids Flow'].sum()
        conc_solids = spiral_data[spiral_data['Product'] == 'Concentrate']['Solids Flow'].sum()
        middling_solids = spiral_data[spiral_data['Product'] == 'Middling']['Solids Flow'].sum()
        tailing_solids = spiral_data[spiral_data['Product'] == 'Tailings']['Solids Flow'].sum()

        feed_solids_pct = (total_solids / total_feed * 100) if total_feed > 0 else 0
        conc_yield = (conc_solids / total_solids * 100) if total_solids > 0 else 0
        middling_yield = (middling_solids / total_solids * 100) if total_solids > 0 else 0
        tailing_yield = (tailing_solids / total_solids * 100) if total_solids > 0 else 0

        score = (conc_yield * 0.5) - (middling_yield * 0.3) - (tailing_yield * 0.2)

        if feed_solids_pct < 20:
            indicator = 'Underloaded'
        elif 20 <= feed_solids_pct <= 35 and 10 <= conc_yield <= 30 and middling_yield < 25:
            indicator = 'Optimal'
        else:
            indicator = 'Overloaded'

        summary_list.append({
            'Spiral': spiral,
            'Feed solids %': feed_solids_pct,
            'Conc yield %': conc_yield,
            'Middling %': middling_yield,
            'Tailing %': tailing_yield,
            'Score': score,
            'Indicator': indicator
        })

    summary_df = pd.DataFrame(summary_list)
    summary_df = summary_df.sort_values('Score', ascending=False).reset_index(drop=True)

    # All spirals solid-based analysis
    all_spirals = sorted(df['Spiral unit'].dropna().unique())
    all_perf_list = []

    for spiral in all_spirals:
        spiral_data = df[df['Spiral unit'] == spiral]
        if spiral_data.empty:
            continue

        total_solids_flow = spiral_data['Solids Flow'].sum()
        conc_solids = spiral_data[spiral_data['Product'] == 'Concentrate']['Solids Flow'].sum()
        middling_solids = spiral_data[spiral_data['Product'] == 'Middling']['Solids Flow'].sum()
        tailing_solids = spiral_data[spiral_data['Product'] == 'Tailings']['Solids Flow'].sum()

        solid_yield = (conc_solids / total_solids_flow * 100) if total_solids_flow > 0 else 0
        middling_frac = (middling_solids / total_solids_flow * 100) if total_solids_flow > 0 else 0
        tailing_frac = (tailing_solids / total_solids_flow * 100) if total_solids_flow > 0 else 0

        score = solid_yield - 0.4 * middling_frac - 0.2 * tailing_frac

        all_perf_list.append({
            'Spiral': int(spiral),
            'Solid Yield %': solid_yield,
            'Middling %': middling_frac,
            'Tailing %': tailing_frac,
            'Score': score
        })

    all_perf_df = pd.DataFrame(all_perf_list)
    all_perf_df = all_perf_df.sort_values('Score', ascending=False).reset_index(drop=True)

    # Calculate KPI values
    best_spiral = int(all_perf_df.iloc[0]['Spiral']) if not all_perf_df.empty else 'N/A'
    highest_yield = all_perf_df['Solid Yield %'].max() if not all_perf_df.empty else 0
    lowest_middling = all_perf_df['Middling %'].min() if not all_perf_df.empty else 0
    lowest_tailing = all_perf_df['Tailing %'].min() if not all_perf_df.empty else 0

    # KPI Cards Section
    st.markdown("## 📊 Key Performance Indicators")

    # Create KPI cards in columns (responsive)
    kpi_cols = st.columns(4)

    with kpi_cols[0]:
        st.metric(
            label="🏆 Best Spiral",
            value=f"Spiral {best_spiral}",
            delta=None
        )

    with kpi_cols[1]:
        delta_color = "normal" if highest_yield > 55 else "inverse"
        st.metric(
            label="📈 Highest Solid Yield",
            value=f"{highest_yield:.1f}%",
            delta="Good" if highest_yield > 55 else "Below Target",
            delta_color=delta_color
        )

    with kpi_cols[2]:
        delta_color = "inverse" if lowest_middling > 40 else "normal"
        st.metric(
            label="⚠️ Lowest Middling",
            value=f"{lowest_middling:.1f}%",
            delta="High" if lowest_middling > 40 else "Acceptable",
            delta_color=delta_color
        )

    with kpi_cols[3]:
        delta_color = "inverse" if lowest_tailing > 25 else "normal"
        st.metric(
            label="🚨 Lowest Tailing",
            value=f"{lowest_tailing:.1f}%",
            delta="High Loss" if lowest_tailing > 25 else "Acceptable",
            delta_color=delta_color
        )

    # Highlight box for best performing spiral
    if not all_perf_df.empty:
        best_row = all_perf_df.iloc[0]
        yield_status = "✅ Excellent" if best_row['Solid Yield %'] > 55 else "⚠️ Needs Improvement"
        st.success(f"**Best Performing Spiral: Spiral {int(best_row['Spiral'])}** - Solid Yield: {best_row['Solid Yield %']:.1f}% ({yield_status})")

    st.markdown("---")

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

    sens_df['Solids Flow'] = sens_df['Flowrate (L/hr)'] * (sens_df['Percent Solid'] / 100)

    sens_summary = []
    for condition in sens_df['Condition'].dropna().unique():
        cond_data = sens_df[sens_df['Condition'] == condition]
        total_flow = cond_data['Flowrate (L/hr)'].sum()
        total_solids_flow = cond_data['Solids Flow'].sum()
        feed_solids_pct = (total_solids_flow / total_flow * 100) if total_flow > 0 else 0

        conc_solids = cond_data[cond_data['Product Type'] == 'Concentrate']['Solids Flow'].sum()
        middling_solids = cond_data[cond_data['Product Type'] == 'Middling']['Solids Flow'].sum()
        tailing_solids = cond_data[cond_data['Product Type'] == 'Tailings']['Solids Flow'].sum()

        solid_yield_conc = (conc_solids / total_solids_flow * 100) if total_solids_flow > 0 else 0
        middling_fraction = (middling_solids / total_solids_flow * 100) if total_solids_flow > 0 else 0
        tailing_fraction = (tailing_solids / total_solids_flow * 100) if total_solids_flow > 0 else 0

        score = (
            solid_yield_conc * 0.5 +
            conc_solids * 0.3 -
            middling_fraction * 0.4 -
            tailing_fraction * 0.2
        )

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
            'Feed Solids %': feed_solids_pct,
            'Splitter Position': splitter,
            'Solids Level': solids_level,
            'Concentrate Solid Yield %': solid_yield_conc,
            'Concentrate Solids (mass)': conc_solids,
            'Middling Fraction %': middling_fraction,
            'Tailing Fraction %': tailing_fraction,
            'Score': score
        })

    sens_df_summary = pd.DataFrame(sens_summary)
    sens_df_summary = sens_df_summary.sort_values('Score', ascending=False).reset_index(drop=True)

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

    sens_df_spiral5['Solids Flow'] = sens_df_spiral5['Flowrate (L/hr)'] * (sens_df_spiral5['Percent Solid'] / 100)

    sens_summary_spiral5 = []
    for condition in sens_df_spiral5['Condition'].dropna().unique():
        cond_data = sens_df_spiral5[sens_df_spiral5['Condition'] == condition]
        total_flow = cond_data['Flowrate (L/hr)'].sum()
        total_solids_flow = cond_data['Solids Flow'].sum()
        feed_solids_pct = (total_solids_flow / total_flow * 100) if total_flow > 0 else 0

        conc_solids = cond_data[cond_data['Product Type'] == 'Concentrate']['Solids Flow'].sum()
        middling_solids = cond_data[cond_data['Product Type'] == 'Middling']['Solids Flow'].sum()
        tailing_solids = cond_data[cond_data['Product Type'] == 'Tailings']['Solids Flow'].sum()

        # Solid-based calculations for Spiral 5
        solid_yield = (conc_solids / total_solids_flow * 100) if total_solids_flow > 0 else 0
        middling_fraction = (middling_solids / total_solids_flow * 100) if total_solids_flow > 0 else 0
        tailing_fraction = (tailing_solids / total_solids_flow * 100) if total_solids_flow > 0 else 0

        # Performance score for Spiral 5 (secondary spiral treating middlings)
        # Middling heavily penalized due to recycle loop problem
        score = (solid_yield * 0.4) - (middling_fraction * 0.5) - (tailing_fraction * 0.2)

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
            'Feed Solids %': feed_solids_pct,
            'Splitter Position': splitter,
            'Solids Level': solids_level,
            'Solid Yield %': solid_yield,
            'Middling Fraction %': middling_fraction,
            'Tailing Fraction %': tailing_fraction,
            'Score': score
        })

    sens_df_summary_spiral5 = pd.DataFrame(sens_summary_spiral5)
    sens_df_summary_spiral5 = sens_df_summary_spiral5.sort_values('Score', ascending=False).reset_index(drop=True)

    # Create tabs
    tabs = st.tabs([
        "🏭 Plant Performance Overview",
        "🔍 Individual Spiral Analysis",
        "📊 Spiral Comparison",
        "🔬 Sensitivity Analysis",
        "� Spiral 5 Sensitivity",
        "�💡 Recommendations"
    ])

    # Overview Tab
    with tabs[0]:
        with st.container():
            st.markdown("## 📈 Plant Performance Overview")
            st.info(
                '**📊 Analysis Methodology:** All performance metrics are based on **solids only**, not slurry. '
                'This approach removes water-related distortion and provides true separation efficiency. '
                'Solids flow = flowrate × (dry_weight / slurry_weight).'
            )

            st.markdown("### Feed Flow Distribution")
            feed_flow = feed_df.groupby('Feed Line')['Flowrate (L/hr)'].sum().reset_index()
            fig = plot_bar(feed_flow, 'Feed Line', 'Flowrate (L/hr)', 'Feed Flow Distribution Across Lines', 'Flowrate (L/hr)')
            st.pyplot(fig, width='stretch')

            st.markdown("### Overall Mass Balance")
            total_feed_flow = df['Flowrate (L/hr)'].sum()
            total_solids_flow = df['Solids Flow'].sum()
            overall_solids_pct = (total_solids_flow / total_feed_flow * 100) if total_feed_flow > 0 else 0

            col1, col2 = st.columns(2)
            with col1:
                st.metric('Total Feed Flow', f'{total_feed_flow:.1f} L/hr')
            with col2:
                st.metric('Overall Solids %', f'{overall_solids_pct:.2f}%')

            st.markdown("### Circulating Load Analysis")
            primary_middlings = df[
                df['Spiral unit'].isin([1,2,3,4,7,8]) &
                (df['Product'] == 'Middling')
            ]['Solids Flow'].sum()

            recycle = df[
                df['Spiral unit'].isin([5,6]) &
                (df['Product'] == 'Middling')
            ]['Solids Flow'].sum()

            total_feed_56 = primary_middlings + recycle
            circulating_load = (recycle / primary_middlings) * 100 if primary_middlings > 0 else 0

            st.metric('Circulating Load', f'{circulating_load:.2f}%')
            st.write(f'Primary middlings: {primary_middlings:.1f} L/hr | Recycle: {recycle:.1f} L/hr')

    # Individual Spiral Tab
    with tabs[1]:
        with st.container():
            st.markdown(f"## 🔍 Individual Spiral Analysis: Spiral {selected_spiral}")
            spiral_df = df[df['Spiral unit'] == selected_spiral].copy()

            st.markdown("### Raw Data")
            st.dataframe(spiral_df)

            st.markdown("### Flow Distribution")
            flow_by_product = spiral_df.groupby('Product')['Flowrate (L/hr)'].sum().reset_index()
            fig = plot_bar(flow_by_product, 'Product', 'Flowrate (L/hr)', f'Flow Distribution by Product - Spiral {selected_spiral}', 'Flowrate (L/hr)')
            st.pyplot(fig, width='stretch')

            st.markdown("### Solids Flow Distribution")
            solid_by_product = spiral_df.groupby('Product')['Solids Flow'].sum().reset_index()
            fig = plot_bar(solid_by_product, 'Product', 'Solids Flow', f'Solids Flow by Product - Spiral {selected_spiral}', 'Solids Flow (L/hr)')
            st.pyplot(fig, width='stretch')

            st.markdown("### Mass Balance")
            flows = spiral_df.groupby('Product').agg(
                flow=('Flowrate (L/hr)', 'sum'),
                solids_flow=('Solids Flow', 'sum'),
                percent_solid=('Percent Solid', 'mean')
            ).reset_index()

            total_feed_flow = flows['flow'].sum()
            feed_solids_flow = flows['solids_flow'].sum()
            feed_percent_solid = (feed_solids_flow / total_feed_flow * 100) if total_feed_flow > 0 else 0

            col1, col2 = st.columns(2)
            with col1:
                st.metric('Total Feed Flow', f'{total_feed_flow:.1f} L/hr')
            with col2:
                st.metric('Feed Solids %', f'{feed_percent_solid:.2f}%')

            st.markdown("### Stream Details")
            st.dataframe(flows.rename(columns={
                'flow': 'Flowrate (L/hr)',
                'percent_solid': '% Solid',
                'solids_flow': 'Solids Flow (L/hr)'
            }))

            st.markdown("### Performance Insights")
            spiral_summary = spiral_df.groupby('Product').agg({'Flowrate (L/hr)': 'sum'}).reset_index()
            total_output = spiral_summary['Flowrate (L/hr)'].sum()
            spiral_summary['Fraction'] = spiral_summary['Flowrate (L/hr)'] / total_output

            tail_fraction = spiral_summary.loc[spiral_summary['Product'].str.contains('Tail', case=False, na=False), 'Fraction'].sum()
            mid_fraction = spiral_summary.loc[spiral_summary['Product'].str.contains('Mid', case=False, na=False), 'Fraction'].sum()

            st.write(f'**Tailings flow share:** {tail_fraction:.2%}')
            st.write(f'**Middling flow share:** {mid_fraction:.2%}')

            if tail_fraction > 0.40:
                st.error('🚨 High tailings flow detected (> 40% of output) - Significant material loss!')
            else:
                st.success('✅ Tailings flow within normal range.')

            if mid_fraction > 0.25:
                st.warning('⚠️ High middling flow detected (> 25% of output) - Poor separation efficiency.')
            else:
                st.success('✅ Middling flow within normal range.')

    # Spiral Comparison Tab
    with tabs[2]:
        with st.container():
            st.markdown("## 📊 Spiral Comparison")

            st.markdown("### Primary Spirals Performance")
            st.dataframe(summary_df.style.apply(lambda x: ['background-color: #d4edda' if x.name == 0 else '' for i in x], axis=1))

            st.markdown("### All Spirals Solid-Based Ranking")
            st.markdown(
                '#### Methodology\n'
                'All metrics use **solid mass calculations**:\n'
                '- **Solid Yield %**: Concentrate solids ÷ Total solids (target > 55%)\n'
                '- **Middling %**: Middling solids ÷ Total solids (target < 25%)\n'
                '- **Tailing %**: Tailing solids ÷ Total solids (target < 15%)'
            )

            st.dataframe(all_perf_df.style.apply(
                lambda x: ['background-color: #d4edda'] * len(x) if x.name == 0 else
                          (['background-color: #f8d7da'] * len(x) if x.name == len(all_perf_df) - 1 else ['']*len(x)),
                axis=1
            ))

            st.markdown("### Performance Insights")
            for idx, row in all_perf_df.iterrows():
                spiral_num = int(row['Spiral'])
                solid_y = row['Solid Yield %']
                middle_f = row['Middling %']
                tail_f = row['Tailing %']
                score = row['Score']

                insights = []
                if middle_f > 40:
                    insights.append('🔴 High middling - poor separation')
                if tail_f > 25:
                    insights.append('🚨 High tailing - material loss')
                if solid_y > 55:
                    insights.append('✅ High recovery')
                if middle_f < 25 and tail_f < 15:
                    insights.append('✅ Good separation')

                st.write(f'**Spiral {spiral_num}** (Score: {score:.2f})')
                st.write(f'Solid Yield: {solid_y:.2f}% | Middling: {middle_f:.2f}% | Tailing: {tail_f:.2f}%')
                if insights:
                    st.write(' | '.join(insights))
                st.write('---')

    # Sensitivity Analysis Tab
    with tabs[3]:
        with st.container():
            st.markdown("## 🔬 Sensitivity Analysis - Primary Spiral (Spiral 1)")

            st.info(
                '**🔬 Primary Spiral Analysis:** Spiral 1 processes fresh feed. '
                'Standard performance scoring balances yield, middling control, and tailings minimization. '
                'Score = (Yield × 0.5) + (Solids × 0.3) - (Middling × 0.4) - (Tailing × 0.2)'
            )

            st.markdown("### Sensitivity Results - Spiral 1")
            st.dataframe(sens_df_summary)

            best_condition_spiral1 = sens_df_summary.iloc[0]['Condition'] if not sens_df_summary.empty else None
            worst_condition_spiral1 = sens_df_summary.iloc[-1]['Condition'] if not sens_df_summary.empty else None

            st.success(f'**🏆 Best Condition (Spiral 1):** {best_condition_spiral1}')
            st.error(f'**❌ Worst Condition (Spiral 1):** {worst_condition_spiral1}')

            st.markdown("### Concentrate Yield by Condition - Spiral 1")
            yield_data = sens_df_summary[['Condition', 'Concentrate Solid Yield %']].copy()
            fig = plot_bar(yield_data, 'Condition', 'Concentrate Solid Yield %', 'Concentrate Solid Yield by Operating Condition - Spiral 1', 'Yield %')
            st.pyplot(fig, width='stretch')

    # Spiral 5 Sensitivity Tab
    with tabs[4]:
        with st.container():
            st.markdown("## 🔄 Spiral 5 Sensitivity Analysis")

            st.markdown("### Secondary Spiral Overview")
            st.info(
                '**🔄 Critical Role:** Spiral 5 treats middlings from primary spirals (1-4, 7-8). '
                'Poor performance creates recycle loops that reduce overall plant efficiency. '
                'Performance scoring heavily penalizes middling production to prevent recirculation issues.'
            )

            # Key performance formula
            st.markdown("### Performance Scoring Formula")
            st.latex(r'''\text{Score} = (\text{Yield} \times 0.4) - (\text{Middling} \times 0.5) - (\text{Tailing} \times 0.2)''')
            st.markdown("**Why this formula?** Middling production (×0.5 penalty) is critical to avoid recycle loops.")

            st.markdown("### Ranked Operating Conditions")
            st.dataframe(sens_df_summary_spiral5.style.apply(
                lambda x: ['background-color: #d4edda'] * len(x) if x.name == 0 else
                          (['background-color: #f8d7da'] * len(x) if x.name == len(sens_df_summary_spiral5) - 1 else ['']*len(x)),
                axis=1
            ))

            # Best operating point
            best_condition_spiral5 = sens_df_summary_spiral5.iloc[0]['Condition'] if not sens_df_summary_spiral5.empty else None
            best_row = sens_df_summary_spiral5.iloc[0] if not sens_df_summary_spiral5.empty else None

            st.markdown("### 🏆 Best Operating Point")
            if best_row is not None:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("**Best Condition**", best_condition_spiral5)
                with col2:
                    st.metric("**Solid Yield**", f"{best_row['Solid Yield %']:.1f}%")
                with col3:
                    st.metric("**Middling Fraction**", f"{best_row['Middling Fraction %']:.1f}%")

            # Worst condition for comparison
            worst_condition_spiral5 = sens_df_summary_spiral5.iloc[-1]['Condition'] if not sens_df_summary_spiral5.empty else None
            st.markdown("### ❌ Worst Operating Point")
            st.error(f"**Avoid:** {worst_condition_spiral5} - High middling production leads to recycle loops")

            st.markdown("### 📊 Performance Analysis")

            # Solid yield chart
            st.markdown("#### Solid Yield by Condition")
            yield_data_spiral5 = sens_df_summary_spiral5[['Condition', 'Solid Yield %']].copy()
            fig = plot_bar(yield_data_spiral5, 'Condition', 'Solid Yield %', 'Solid Yield Performance - Spiral 5', 'Yield %')
            st.pyplot(fig, width='stretch')

            # Middling fraction chart (emphasized as critical)
            st.markdown("#### ⚠️ Middling Fraction by Condition (Critical Parameter)")
            middling_data_spiral5 = sens_df_summary_spiral5[['Condition', 'Middling Fraction %']].copy()
            fig = plot_bar(middling_data_spiral5, 'Condition', 'Middling Fraction %', 'Middling Production - Spiral 5 (Lower is Better)', 'Middling %')
            st.pyplot(fig, width='stretch')

            # Trade-off analysis
            st.markdown("### 🔄 Yield vs Middling Trade-off")
            fig, ax = plt.subplots(figsize=(12, 8))
            scatter_data = sens_df_summary_spiral5.copy()

            scatter = ax.scatter(scatter_data['Solid Yield %'], scatter_data['Middling Fraction %'],
                               s=120, c=range(len(scatter_data)), cmap='RdYlGn_r', alpha=0.8, edgecolors='black')

            # Add condition labels
            for i, row in scatter_data.iterrows():
                ax.annotate(row['Condition'], (row['Solid Yield %'], row['Middling Fraction %']),
                           xytext=(8, 8), textcoords='offset points', fontsize=11, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

            ax.set_title('Yield vs Middling Trade-off - Spiral 5', fontsize=16, fontweight='bold', pad=20, color='#2c3e50')
            ax.set_xlabel('Solid Yield % (Higher is Better)', fontsize=14, fontweight='medium', color='#34495e')
            ax.set_ylabel('Middling Fraction % (Lower is Better)', fontsize=14, fontweight='medium', color='#34495e')

            plt.xticks(fontsize=12)
            plt.yticks(fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_linewidth(0.5)
            ax.spines['bottom'].set_linewidth(0.5)
            ax.set_facecolor('#FFFFFF')

            cbar = plt.colorbar(scatter, ax=ax)
            cbar.set_label('Performance Rank (Green = Best)', fontsize=12)

            plt.tight_layout()
            st.pyplot(fig, width='stretch')

            # Correlation insights
            correlation = scatter_data['Solid Yield %'].corr(scatter_data['Middling Fraction %'])
            st.markdown("### 📈 Trade-off Insights")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("**Yield-Middling Correlation**", f"{correlation:.3f}")
            with col2:
                trend = "Positive (Trade-off)" if correlation > 0.3 else "Negative (Win-win)" if correlation < -0.3 else "Neutral"
                st.metric("**Relationship**", trend)

            # Recommendations
            st.markdown("### 💡 Operating Recommendations")

            if best_row is not None:
                st.success(f"""
                **🎯 Primary Recommendation:** Operate Spiral 5 under **{best_condition_spiral5}** conditions
                
                **Expected Performance:**
                - Solid Yield: {best_row['Solid Yield %']:.1f}%
                - Middling Fraction: {best_row['Middling Fraction %']:.1f}%
                - Performance Score: {best_row['Score']:.2f}
                """)

            st.warning("""
            **⚠️ Critical Warning:** Avoid conditions that produce >30% middling fraction as this will:
            - Create recycle loops
            - Reduce overall plant efficiency  
            - Increase operating costs
            """)

            if correlation > 0.5:
                st.info("**ℹ️ Optimization Strategy:** Focus on conditions in the bottom-right quadrant (high yield, low middling) of the trade-off chart.")
            elif correlation < -0.3:
                st.success("**✅ Good News:** Some conditions achieve both high yield and low middling - prioritize these operating points!")

    # Recommendations Tab
    with tabs[5]:
        with st.container():
            st.markdown("## 💡 Recommendations")

            # Final recommendation
            best_perf = all_perf_df.iloc[0] if not all_perf_df.empty else None
            worst_perf = all_perf_df.iloc[-1] if not all_perf_df.empty else None

            if best_perf is not None and worst_perf is not None:
                best_spiral = int(best_perf['Spiral'])
                worst_spiral = int(worst_perf['Spiral'])
                best_score = best_perf['Score']
                worst_score = worst_perf['Score']

                st.info(f'**🎯 Action Required:** Increase feed to Spiral {best_spiral} (Score: {best_score:.2f}), reduce load on Spiral {worst_spiral} (Score: {worst_score:.2f}) to optimize overall plant performance.')

            st.subheader("📌 Recommendation")
            st.info(f"""
Increase feed to Spiral {best_spiral}.
Reduce load on low-performing spirals.
Adjust splitter for optimal separation.
""")

            st.markdown("### Performance Charts")
            all_perf_plot = all_perf_df[['Spiral', 'Solid Yield %']].copy()
            all_perf_plot['Spiral'] = all_perf_plot['Spiral'].astype(str)
            fig = plot_bar(all_perf_plot, 'Spiral', 'Solid Yield %', 'Solid Yield % by Spiral', 'Yield %')
            st.pyplot(fig, width='stretch')

            all_score = all_perf_df[['Spiral', 'Score']].copy()
            all_score['Spiral'] = all_score['Spiral'].astype(str)
            fig = plot_bar(all_score, 'Spiral', 'Score', 'Performance Score by Spiral', 'Score')
            st.pyplot(fig, width='stretch')

            # PDF report download support
            if best_perf is not None:
                pdf_recommendations = (
                    f'Increase feed to Spiral {best_spiral}.\n'
                    'Reduce load on low-performing spirals.\n'
                    'Adjust splitter for optimal separation.'
                )

                if st.button('📄 Generate PDF Report'):
                    report_path = generate_pdf_report(
                        best_spiral,
                        highest_yield,
                        lowest_middling,
                        lowest_tailing,
                        pdf_recommendations
                    )
                    st.success(f'Report generated: {report_path}')
                    st.markdown(f'[Download Report](./{report_path})')

            # Optimal settings from sensitivity
            if not sens_df_summary.empty:
                optimal_row = sens_df_summary.loc[sens_df_summary['Score'].idxmax()]
                optimal_solids = optimal_row['Solids Level']
                optimal_splitter = optimal_row['Splitter Position']
                st.info(f'**⚙️ Optimal Operating Settings:** Solids level: **{optimal_solids}** | Splitter position: **{optimal_splitter}** for maximum efficiency.')

if __name__ == '__main__':
    main()