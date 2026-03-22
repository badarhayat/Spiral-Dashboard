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
    feed_df.columns = feed_df.columns.str.strip()
    feed_df = feed_df.rename(columns={'Feed Flow Distribution in the Spiral Circuit': 'Line'})
    if 'Flowrate (L/hr)' in feed_df.columns:
        feed_df['Flowrate (L/hr)'] = pd.to_numeric(feed_df['Flowrate (L/hr)'], errors='coerce')

    return df, group, feed_df


def plot_bar(data, x, y, title, ylabel):
    fig, ax = plt.subplots()
    data.plot(kind='bar', x=x, y=y, ax=ax, legend=False)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel(x)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    return fig


def main():
    st.set_page_config(page_title='Spiral Concentrator Analysis', layout='wide')
    st.title('Spiral Concentrator Analysis Dashboard')

    path = 'Spiral Plant Sheet.xlsx'
    df, group, feed_df = load_data(path)

    st.sidebar.header('Controls')
    spirals = sorted(df['Spiral unit'].dropna().unique())
    selected_spiral = st.sidebar.selectbox('Select Spiral Unit', spirals)

    # Create tabs
    tabs = st.tabs([
        "Overview",
        "Individual Spiral",
        "Spiral Comparison",
        "Sensitivity Analysis",
        "Recommendations"
    ])

    # Overview Tab
    with tabs[0]:
        st.markdown("## Overview")
        st.info(
            '**📊 Analysis Methodology:** All performance metrics are based on **solids only**, not slurry. '
            'This approach removes water-related distortion and provides true separation efficiency. '
            'Solids flow = flowrate × (dry_weight / slurry_weight).'
        )

        st.markdown("### Feed Flow Distribution")
        feed_flow = feed_df.groupby('Product')['Flowrate (L/hr)'].sum().reset_index()
        fig = plot_bar(feed_flow, 'Product', 'Flowrate (L/hr)', 'Feed Flow Distribution', 'Flowrate (L/hr)')
        st.pyplot(fig, use_container_width=True)

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
        st.markdown(f"## Individual Spiral: {selected_spiral}")
        spiral_df = df[df['Spiral unit'] == selected_spiral].copy()

        st.markdown("### Raw Data")
        st.dataframe(spiral_df)

        st.markdown("### Flow Distribution")
        flow_by_product = spiral_df.groupby('Product')['Flowrate (L/hr)'].sum().reset_index()
        fig = plot_bar(flow_by_product, 'Product', 'Flowrate (L/hr)', 'Flow Distribution by Product', 'Flowrate (L/hr)')
        st.pyplot(fig, use_container_width=True)

        st.markdown("### Solids Flow Distribution")
        solid_by_product = spiral_df.groupby('Product')['Solids Flow'].sum().reset_index()
        fig = plot_bar(solid_by_product, 'Product', 'Solids Flow', 'Solids Flow by Product', 'Solids Flow (L/hr)')
        st.pyplot(fig, use_container_width=True)

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

        st.markdown("### Basic Insights")
        spiral_summary = spiral_df.groupby('Product').agg({'Flowrate (L/hr)': 'sum'}).reset_index()
        total_output = spiral_summary['Flowrate (L/hr)'].sum()
        spiral_summary['Fraction'] = spiral_summary['Flowrate (L/hr)'] / total_output

        tail_fraction = spiral_summary.loc[spiral_summary['Product'].str.contains('Tail', case=False, na=False), 'Fraction'].sum()
        mid_fraction = spiral_summary.loc[spiral_summary['Product'].str.contains('Mid', case=False, na=False), 'Fraction'].sum()

        st.write(f'Tailings flow share: {tail_fraction:.2%}')
        st.write(f'Middling flow share: {mid_fraction:.2%}')

        if tail_fraction > 0.40:
            st.warning('High tailings flow detected (> 40% of output).')
        else:
            st.success('Tailings flow within normal range.')

        if mid_fraction > 0.25:
            st.warning('High middling flow detected (> 25% of output).')
        else:
            st.success('Middling flow within normal range.')

    # Spiral Comparison Tab
    with tabs[2]:
        st.markdown("## Spiral Comparison")

        # Primary spirals performance comparison
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

        st.markdown("### Primary Spirals Performance")
        st.dataframe(summary_df.style.apply(lambda x: ['background-color: lightgreen' if x.name == 0 else '' for i in x], axis=1))

        # All spirals solid-based analysis
        st.markdown("### All Spirals Solid-Based Ranking")
        st.markdown(
            '#### Methodology\n'
            'All metrics use **solid mass calculations**:\n'
            '- **Solid Yield %**: Concentrate solids ÷ Total solids (target > 55%)\n'
            '- **Middling %**: Middling solids ÷ Total solids (target < 25%)\n'
            '- **Tailing %**: Tailing solids ÷ Total solids (target < 15%)'
        )

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

        st.dataframe(all_perf_df.style.apply(
            lambda x: ['background-color: lightgreen'] * len(x) if x.name == 0 else 
                      (['background-color: lightcoral'] * len(x) if x.name == len(all_perf_df) - 1 else ['']*len(x)),
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
                insights.append('⚠️ High tailing - material loss')
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
        st.markdown("## Sensitivity Analysis for Spiral 1")
        st.info(
            '**🔬 Method:** Solids-only calculations reveal true separation efficiency across operating parameters.'
        )

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

        st.markdown("### Sensitivity Results")
        st.dataframe(sens_df_summary)

        best_condition = sens_df_summary.iloc[0]['Condition'] if not sens_df_summary.empty else None
        top3 = sens_df_summary.head(3)['Condition'].tolist() if len(sens_df_summary) >= 3 else sens_df_summary['Condition'].tolist()

        st.success(f'**Best Condition:** {best_condition}')
        st.write(f'**Top 3:** {", ".join(top3)}')

        st.markdown("### Concentrate Yield by Condition")
        yield_data = sens_df_summary[['Condition', 'Concentrate Solid Yield %']].copy()
        fig = plot_bar(yield_data, 'Condition', 'Concentrate Solid Yield %', 'Concentrate Solid Yield by Condition', 'Yield %')
        st.pyplot(fig, use_container_width=True)

    # Recommendations Tab
    with tabs[4]:
        st.markdown("## Recommendations")

        # Final recommendation
        best_perf = all_perf_df.iloc[0] if not all_perf_df.empty else None
        worst_perf = all_perf_df.iloc[-1] if not all_perf_df.empty else None

        if best_perf is not None:
            st.success(
                f'**Best Spiral:** {int(best_perf["Spiral"])} (Score: {best_perf["Score"]:.2f})\n\n'
                f'**Worst Spiral:** {int(worst_perf["Spiral"])} (Score: {worst_perf["Score"]:.2f})\n\n'
                '**Action:** Increase feed to best-performing spirals, reduce load on poor performers.'
            )

        st.markdown("### Performance Charts")
        all_perf_plot = all_perf_df[['Spiral', 'Solid Yield %']].copy()
        all_perf_plot['Spiral'] = all_perf_plot['Spiral'].astype(str)
        fig = plot_bar(all_perf_plot, 'Spiral', 'Solid Yield %', 'Solid Yield % by Spiral', 'Yield %')
        st.pyplot(fig, use_container_width=True)

        all_score = all_perf_df[['Spiral', 'Score']].copy()
        all_score['Spiral'] = all_score['Spiral'].astype(str)
        fig = plot_bar(all_score, 'Spiral', 'Score', 'Performance Score by Spiral', 'Score')
        st.pyplot(fig, use_container_width=True)

        # Optimal settings from sensitivity
        optimal_solids = sens_df_summary.loc[sens_df_summary['Score'].idxmax(), 'Solids Level']
        optimal_splitter = sens_df_summary.loc[sens_df_summary['Score'].idxmax(), 'Splitter Position']
        st.info(f'**Optimal Settings:** Solids level: {optimal_solids} | Splitter position: {optimal_splitter}')




if __name__ == '__main__':
    main()
