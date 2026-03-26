"""Streamlit UI components for the cleaner table dashboard."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import streamlit as st

from calculations import CalculationError, prepare_sensitivity_metrics


def render_header() -> None:
    """Render the main page heading and description."""
    st.title("Cleaner Shaking Table Performance Dashboard")
    st.caption("Upload cleaner table operating data to review plant performance.")


def render_sidebar(default_file_name: str) -> Any | None:
    """Render sidebar controls and return the uploaded Excel file."""
    st.sidebar.header("Data Input")
    st.sidebar.write("Load an Excel workbook containing cleaner shaking table data.")
    st.sidebar.write(f"Default sample file: `{default_file_name}`")
    return st.sidebar.file_uploader(
        "Upload Excel file",
        type=["xlsx", "xls"],
        accept_multiple_files=False,
    )


def collect_band_inputs(
    dataframe: pd.DataFrame,
    band_analyses: dict[int, dict],
) -> tuple[list[float], dict[int, Any | None]]:
    """Collect per-run band scores and optional uploaded images."""
    st.subheader("Band Input")
    st.caption("Upload a band image and enter a band score for each table run.")

    band_scores: list[float] = []
    uploaded_images: dict[int, Any | None] = {}

    for row_index, row in dataframe.iterrows():
        with st.container(border=True):
            left_column, right_column = st.columns([1, 1.4], gap="large")

            with left_column:
                st.markdown(f"**{row['Table']}**")
                detected_score = band_analyses.get(row_index, {}).get("band_score", 3.0)
                band_score = st.number_input(
                    "Band Score",
                    min_value=1.0,
                    max_value=5.0,
                    value=float(detected_score),
                    step=1.0,
                    key=f"band_score_{row_index}",
                )
                band_scores.append(float(band_score))

            with right_column:
                uploaded_images[row_index] = st.file_uploader(
                    f"Upload image for {row['Table']}",
                    type=["png", "jpg", "jpeg"],
                    accept_multiple_files=False,
                    key=f"band_image_{row_index}",
                )

    return band_scores, uploaded_images


def render_data_preview(dataframe: pd.DataFrame) -> None:
    """Display the full dataframe with key calculated columns highlighted."""
    st.subheader("Calculated Results")
    st.write(f"Rows: {len(dataframe)} | Columns: {len(dataframe.columns)}")
    styled = dataframe.style.format(na_rep="-", precision=2)
    styled = styled.map(
        lambda _: "background-color: #dbeafe; font-weight: 600;",
        subset=["Yield_Conc"],
    )
    styled = styled.map(
        lambda _: "background-color: #fee2e2; font-weight: 600;",
        subset=["Yield_Tail"],
    )
    styled = styled.map(
        lambda value: (
            "background-color: #fecaca; color: #991b1b; font-weight: 700;"
            if value == "Mass balance error"
            else "background-color: #dcfce7; color: #166534; font-weight: 700;"
        ),
        subset=["flag"],
    )
    if "Band_Score" in dataframe.columns and "Final_Score" in dataframe.columns:
        styled = styled.map(
            lambda _: "background-color: #fff3bf; font-weight: 600;",
            subset=["Band_Score", "Final_Score"],
        )
    st.dataframe(styled, use_container_width=True, hide_index=True)


def render_dashboard(
    dataframe: pd.DataFrame,
    metrics: dict,
    comparison: pd.DataFrame,
    monthly_summary: pd.DataFrame,
    ranking: pd.DataFrame,
    best_condition: dict,
    best_band_table: dict,
    uploaded_images: dict[int, Any | None],
    band_analyses: dict[int, dict],
    alerts: list[dict],
    recommendations: list[str],
) -> None:
    """Render the full cleaner table dashboard."""
    render_top_metrics(metrics)

    left_column, right_column = st.columns([1.35, 1], gap="large")
    with left_column:
        render_table_comparison(comparison, best_condition)
        render_ranking_table(ranking)
        render_charts(dataframe, best_condition)
    with right_column:
        render_best_operating_condition(best_condition)
        render_best_band_table(best_band_table, uploaded_images)
        render_alerts(alerts)
        render_recommendations(recommendations)
    render_production_section(dataframe, monthly_summary)
    render_band_analysis(dataframe, uploaded_images, band_analyses, best_band_table)
    render_data_preview(dataframe)


def render_sensitivity_analysis() -> None:
    """Render a separate sensitivity-analysis workflow."""
    st.header("Sensitivity Analysis")
    uploaded_file = st.file_uploader(
        "Upload Sensitivity Excel",
        type=["xlsx"],
        key="sensitivity_upload",
    )

    if uploaded_file is None:
        st.info("Upload a sensitivity workbook to analyze slope and wash water effects.")
        return

    try:
        raw_df_sens = pd.read_excel(uploaded_file)
        df_sens = prepare_sensitivity_metrics(raw_df_sens)
    except (Exception, CalculationError) as error:  # pragma: no cover - defensive UI wrapper
        st.error(f"Unable to read sensitivity workbook: {error}")
        return

    st.dataframe(df_sens, use_container_width=True, hide_index=True)

    best_row = df_sens.loc[df_sens["Yield_Conc"].idxmax()]
    best_slope = best_row["Slope"]
    best_water = best_row["Wash_Water_Lps"]
    best_yield = best_row["Yield_Conc"]

    st.subheader("Best Operating Condition")
    st.write(f"Best Slope: {best_slope:.2f}")
    st.write(f"Best Wash_Water_Lps: {best_water:.2f}")
    st.write(f"Best Yield_Conc: {best_yield:.2f}")

    if len(df_sens) < 3:
        st.warning("Not enough data for optimization")
        return

    top = df_sens.nlargest(3, "Yield_Conc")
    best_slope_range = (top["Slope"].min(), top["Slope"].max())
    best_water_range = (top["Wash_Water_Lps"].min(), top["Wash_Water_Lps"].max())

    st.write(f"Best Slope Range: ({best_slope_range[0]:.2f}, {best_slope_range[1]:.2f})")
    st.write(f"Best Water Range: ({best_water_range[0]:.2f}, {best_water_range[1]:.2f})")

    chart_left, chart_right = st.columns(2, gap="large")
    with chart_left:
        fig1, ax1 = plt.subplots()
        ax1.scatter(df_sens["Slope"], df_sens["Yield_Conc"], color="#94a3b8", label="All Points")
        ax1.scatter(top["Slope"], top["Yield_Conc"], color="#16a34a", s=80, label="Top 3")
        ax1.scatter(best_slope, best_yield, color="#dc2626", s=140, label="Optimum")
        ax1.annotate(
            f"Optimum\nSlope = {best_slope:.2f}\nYield = {best_yield:.2f}",
            xy=(best_slope, best_yield),
            xytext=(12, 12),
            textcoords="offset points",
            arrowprops={"arrowstyle": "->", "color": "#dc2626"},
        )
        ax1.set_xlabel("Slope")
        ax1.set_ylabel("Yield_Conc")
        ax1.set_title("Yield_Conc vs Slope")
        ax1.legend()
        st.pyplot(fig1)
        plt.close(fig1)

    with chart_right:
        fig2, ax2 = plt.subplots()
        ax2.scatter(df_sens["Wash_Water_Lps"], df_sens["Yield_Conc"], color="#94a3b8", label="All Points")
        ax2.scatter(top["Wash_Water_Lps"], top["Yield_Conc"], color="#16a34a", s=80, label="Top 3")
        ax2.scatter(best_water, best_yield, color="#dc2626", s=140, label="Optimum")
        ax2.annotate(
            f"Optimum\nWater = {best_water:.2f}\nYield = {best_yield:.2f}",
            xy=(best_water, best_yield),
            xytext=(12, 12),
            textcoords="offset points",
            arrowprops={"arrowstyle": "->", "color": "#dc2626"},
        )
        ax2.set_xlabel("Wash Water")
        ax2.set_ylabel("Yield_Conc")
        ax2.set_title("Yield_Conc vs Wash_Water_Lps")
        ax2.legend()
        st.pyplot(fig2)
        plt.close(fig2)

    st.subheader("Yield Heatmap")
    pivot = df_sens.pivot_table(
        values="Yield_Conc",
        index="Wash_Water_Lps",
        columns="Slope",
    ).sort_index().sort_index(axis=1)

    if pivot.empty:
        st.info("Heatmap could not be created from the uploaded sensitivity data.")
        return

    fig3, ax3 = plt.subplots()
    image = ax3.imshow(
        pivot.values,
        aspect="auto",
        origin="lower",
        interpolation="bilinear",
        cmap="YlOrRd",
    )
    ax3.set_title("Yield_Conc Heatmap")
    ax3.set_xlabel("Slope")
    ax3.set_ylabel("Wash_Water_Lps")
    ax3.set_xticks(range(len(pivot.columns)))
    ax3.set_xticklabels([f"{value:.2f}" for value in pivot.columns], rotation=45, ha="right")
    ax3.set_yticks(range(len(pivot.index)))
    ax3.set_yticklabels([f"{value:.2f}" for value in pivot.index])

    if best_slope in pivot.columns and best_water in pivot.index:
        optimum_x = list(pivot.columns).index(best_slope)
        optimum_y = list(pivot.index).index(best_water)
        ax3.scatter(optimum_x, optimum_y, color="#1d4ed8", s=120, marker="x")
        ax3.annotate(
            "Optimum",
            xy=(optimum_x, optimum_y),
            xytext=(8, -14),
            textcoords="offset points",
            color="#1d4ed8",
            fontweight="bold",
        )

    colorbar = fig3.colorbar(image, ax=ax3)
    colorbar.set_label("Yield_Conc")
    st.pyplot(fig3)
    plt.close(fig3)


def render_top_metrics(metrics: dict) -> None:
    """Render headline KPI metrics."""
    st.subheader("Top Metrics")
    metric_columns = st.columns(3, gap="large")

    with metric_columns[0]:
        with st.container(border=True):
            st.metric(
                "Average Yield_Conc",
                format_percent(metrics.get("average_yield_conc")),
            )

    with metric_columns[1]:
        with st.container(border=True):
            st.metric(
                "Best Performing Table",
                metrics.get("best_performing_table", "N/A"),
                delta=format_percent(metrics.get("best_yield_conc")),
            )

    with metric_columns[2]:
        with st.container(border=True):
            st.metric(
                "Total Feed Processed (kg/h)",
                format_number(metrics.get("total_feed_processed")),
            )


def render_table_comparison(comparison: pd.DataFrame, best_condition: dict) -> None:
    """Show side-by-side cleaner table comparison with visual highlights."""
    st.subheader("Table Comparison")
    styled = comparison.style.format(
        {
            "Yield_Conc": "{:.1f}",
            "Yield_Midd": "{:.1f}",
            "Yield_Tail": "{:.1f}",
            "Feed_Solid_Flow": "{:.2f}",
            "Slope": "{:.2f}",
            "Wash_Water_Lps": "{:.2f}",
            "flag": "{}",
        },
        na_rep="-",
    )

    if comparison["Yield_Conc"].notna().any():
        best_index = comparison["Yield_Conc"].idxmax()
        worst_index = comparison["Yield_Conc"].idxmin()
        top_indices = set(best_condition.get("top_indices", []))
        styled = styled.apply(
            lambda row: [
                "background-color: #c7f9cc; font-weight: 700;" if row.name in top_indices else
                "background-color: #dff3e4" if row.name == best_index else
                "background-color: #f8d7da" if row.name == worst_index else ""
                for _ in row
            ],
            axis=1,
        )

    with st.container(border=True):
        st.dataframe(styled, use_container_width=True, hide_index=True)


def render_charts(dataframe: pd.DataFrame, best_condition: dict) -> None:
    """Render performance charts for the cleaner tables."""
    st.subheader("Performance Charts")

    first_row, second_row = st.columns(2, gap="large")
    with first_row:
        render_yield_vs_slope_chart(dataframe, best_condition)
    with second_row:
        render_yield_vs_water_chart(dataframe, best_condition)

    with st.container(border=True):
        render_yield_vs_table_chart(dataframe)


def render_production_section(dataframe: pd.DataFrame, monthly_summary: pd.DataFrame) -> None:
    """Render daily and monthly production reporting."""
    st.subheader("Production Reporting")
    daily_column, monthly_column = st.columns(2, gap="large")

    with daily_column:
        with st.container(border=True):
            st.markdown("**Daily Production Table**")
            daily_columns = [
                "Date",
                "Table",
                "Conc_kgph",
                "Midd_kgph",
                "Tail_kgph",
                "Conc_kgpd",
                "Midd_kgpd",
                "Tail_kgpd",
            ]
            st.dataframe(
                dataframe[daily_columns].style.format(na_rep="-", precision=2),
                use_container_width=True,
                hide_index=True,
            )

    with monthly_column:
        with st.container(border=True):
            st.markdown("**Monthly Summary Table**")
            st.dataframe(
                monthly_summary.style.format(na_rep="-", precision=2),
                use_container_width=True,
                hide_index=True,
            )

    with st.container(border=True):
        st.markdown("**Monthly Concentrate Production**")
        if monthly_summary.empty:
            st.info("Monthly production summary is not available.")
            return

        figure = px.bar(
            monthly_summary,
            x="Date",
            y="Conc_ton",
            title="Monthly Concentrate Production",
            labels={"Date": "Month", "Conc_ton": "Concentrate Production (tons/month)"},
        )
        st.plotly_chart(figure, use_container_width=True)


def render_ranking_table(ranking: pd.DataFrame) -> None:
    """Render cleaner ranking based on yield and concentrate production."""
    st.subheader("Cleaner Ranking")
    styled = ranking.style.format(
        {
            "Yield_Conc": "{:.2f}",
            "Conc_kgph": "{:.2f}",
            "Norm_Production": "{:.2f}",
            "Score": "{:.2f}",
            "Rank": "{:.0f}",
        },
        na_rep="-",
    )

    if ranking["Rank"].notna().any():
        best_index = ranking["Rank"].idxmin()
        styled = styled.apply(
            lambda row: [
                "background-color: #dff3e4; font-weight: 700;" if row.name == best_index else ""
                for _ in row
            ],
            axis=1,
        )

    with st.container(border=True):
        st.dataframe(styled, use_container_width=True, hide_index=True)


def render_best_operating_condition(best_condition: dict) -> None:
    """Render the best operating condition summary."""
    st.subheader("Best Operating Condition")
    with st.container(border=True):
        if not best_condition.get("has_enough_data"):
            st.info(best_condition.get("message", "Not enough data for optimization"))
            return

        st.write(f"Table: {best_condition['table']}")
        st.write(f"Best Slope: {best_condition['best_slope']:.2f}")
        st.write(f"Best Wash Water: {best_condition['best_wash_water']:.2f} L/s")
        st.write(f"Average Slope (Top 3): {best_condition['average_slope']:.2f}")
        st.write(f"Average Wash Water (Top 3): {best_condition['average_wash_water']:.2f} L/s")
        st.write(f"Yield_Conc: {best_condition['yield_conc']:.2f}%")
        st.write(f"Yield_Tail: {best_condition['yield_tail']:.2f}%")


def render_best_band_table(best_band_table: dict, uploaded_images: dict[int, Any | None]) -> None:
    """Render the best table based on final score and show its uploaded image."""
    st.subheader("Best Table")
    with st.container(border=True):
        if not best_band_table.get("has_data"):
            st.info(best_band_table.get("message", "Band analysis is not available."))
            return

        image = uploaded_images.get(best_band_table["best_index"])
        if image is not None:
            st.image(image, use_container_width=True)

        st.write(f"Table: {best_band_table['table']}")
        st.write(f"Yield_Conc: {best_band_table['yield_conc']:.2f}%")
        st.write(f"Yield_Tail: {best_band_table['yield_tail']:.2f}%")
        st.write(f"Band Score: {best_band_table['band_score']:.2f}")
        st.write(f"Final Score: {best_band_table['final_score']:.2f}")


def render_band_analysis(
    dataframe: pd.DataFrame,
    uploaded_images: dict[int, Any | None],
    band_analyses: dict[int, dict],
    best_band_table: dict,
) -> None:
    """Render a clean image-based band analysis section."""
    st.subheader("Band Analysis")

    for row_index, row in dataframe.iterrows():
        with st.container(border=True):
            left_column, right_column = st.columns([1, 1.3], gap="large")

            with left_column:
                analysis = band_analyses.get(row_index, {})
                if analysis.get("has_detection"):
                    image_column_left, image_column_center, image_column_right = st.columns(3, gap="small")
                    with image_column_left:
                        st.caption("ROI")
                        st.image(analysis["roi_image"], use_container_width=True)
                    with image_column_center:
                        st.caption("Mask")
                        st.image(analysis["mask_image"], use_container_width=True, clamp=True)
                    with image_column_right:
                        st.caption("Detected Band")
                        st.image(analysis["overlay_image"], use_container_width=True)
                elif analysis.get("has_image"):
                    st.image(analysis["original_image"], use_container_width=True)
                else:
                    st.info("No image uploaded for this run.")

            with right_column:
                title = str(row["Table"])
                if best_band_table.get("best_index") == row_index:
                    title = f"{title} (Best Table)"
                st.markdown(f"**{title}**")
                st.write(f"Yield_Conc: {row['Yield_Conc']:.2f}%")
                st.write(f"Band Score: {row['Band_Score']:.2f}")
                st.write(f"Final Score: {row['Final_Score']:.2f}")
                if analysis.get("has_detection"):
                    st.write(f"Band Width: {analysis['band_width']:.2f} px")
                    st.write(f"Band Position: {analysis['band_position']:.3f}")
                    st.write(f"Band Area: {analysis['band_area']:.2f}")
                    st.write(f"Sharpness: {analysis['sharpness']:.2f}")
                    st.write(f"Detection Mode: {analysis['detection_mode']}")
                    st.write(f"Contour Score: {analysis['contour_score']:.2f}")
                    st.write(f"Detected Band Score: {analysis['raw_band_score']:.2f}")
                    st.write(f"Classification: {analysis['classification']}")
                st.write(f"Interpretation: {interpret_band_score(row['Band_Score'])}")


def interpret_band_score(band_score: float) -> str:
    """Return a simple band interpretation for the operator."""
    if pd.isna(band_score):
        return "Band score not available"
    if band_score <= 2:
        return "Poor separation"
    if band_score >= 4:
        return "Good separation"
    return "Moderate separation"


def render_yield_vs_table_chart(dataframe: pd.DataFrame) -> None:
    """Render concentrate yield by cleaner table."""
    with st.container(border=True):
        chart_data = dataframe.dropna(subset=["Yield_Conc"]).sort_values("Yield_Conc", ascending=False)
        if chart_data.empty:
            st.info("Yield_Conc data is not available for table comparison.")
            return

        figure = px.bar(
            chart_data,
            x="Table",
            y="Yield_Conc",
            color="Yield_Conc",
            color_continuous_scale="Blues",
            title="Yield_Conc vs Table",
            labels={"Yield_Conc": "Yield_Conc (%)"},
        )
        figure.update_layout(coloraxis_showscale=False, xaxis_title="Cleaner Table")
        st.plotly_chart(figure, use_container_width=True)


def render_yield_vs_slope_chart(dataframe: pd.DataFrame, best_condition: dict) -> None:
    """Render concentrate yield against slope when slope is available."""
    with st.container(border=True):
        chart_data = dataframe.dropna(subset=["Yield_Conc", "Slope"])
        if chart_data.empty:
            st.info("Slope data is not available in this workbook.")
            return

        figure = px.scatter(
            chart_data,
            x="Slope",
            y="Yield_Conc",
            text="Table",
            title="Yield_Conc vs Slope",
            labels={"Yield_Conc": "Yield_Conc (%)", "Slope": "Slope"},
        )
        figure.update_traces(textposition="top center", marker=dict(size=11, color="#1f77b4"))
        add_best_point_highlight(
            figure=figure,
            dataframe=chart_data,
            x_column="Slope",
            y_column="Yield_Conc",
            best_condition=best_condition,
        )
        st.plotly_chart(figure, use_container_width=True)


def render_yield_vs_water_chart(dataframe: pd.DataFrame, best_condition: dict) -> None:
    """Render concentrate yield against wash water setting."""
    with st.container(border=True):
        chart_data = dataframe.dropna(subset=["Yield_Conc", "Wash_Water_Lps"])
        if chart_data.empty:
            st.info("Wash water data is not available in this workbook.")
            return

        figure = px.scatter(
            chart_data,
            x="Wash_Water_Lps",
            y="Yield_Conc",
            color="Table",
            title="Yield_Conc vs Wash_Water_Lps",
            labels={"Yield_Conc": "Yield_Conc (%)", "Wash_Water_Lps": "Wash Water (L/s)"},
        )
        add_best_point_highlight(
            figure=figure,
            dataframe=chart_data,
            x_column="Wash_Water_Lps",
            y_column="Yield_Conc",
            best_condition=best_condition,
        )
        st.plotly_chart(figure, use_container_width=True)


def add_best_point_highlight(
    figure,
    dataframe: pd.DataFrame,
    x_column: str,
    y_column: str,
    best_condition: dict,
) -> None:
    """Overlay the best operating point on a scatter chart."""
    best_index = best_condition.get("best_index")
    if best_index is None or best_index not in dataframe.index:
        return

    best_row = dataframe.loc[best_index]
    figure.add_scatter(
        x=[best_row[x_column]],
        y=[best_row[y_column]],
        mode="markers+text",
        name="Best Point",
        text=["Best"],
        textposition="top center",
        marker={
            "size": 18,
            "color": "#d62828",
            "symbol": "star",
            "line": {"width": 2, "color": "#ffffff"},
        },
        showlegend=True,
    )


def render_alerts(alerts: list[dict]) -> None:
    """Render current process warnings."""
    st.subheader("Alerts")
    with st.container(border=True):
        if not alerts:
            st.success("No active performance warnings.")
            return

        for alert in alerts:
            st.warning(alert["message"])


def render_recommendations(recommendations: list[str]) -> None:
    """Render operating recommendations for plant operators."""
    st.subheader("Recommendations")
    with st.container(border=True):
        for recommendation in recommendations:
            st.write(f"- {recommendation}")


def format_percent(value: Any) -> str:
    """Format a numeric percentage for display."""
    if pd.isna(value):
        return "N/A"
    return f"{float(value):.1f}%"


def format_number(value: Any) -> str:
    """Format a numeric value for display."""
    if pd.isna(value):
        return "N/A"
    return f"{float(value):,.1f}"
