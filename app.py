"""Main Streamlit entry point for the Cleaner Shaking Table dashboard."""

from pathlib import Path

import streamlit as st

from alerts import evaluate_performance_alerts
from calculations import (
    CalculationError,
    analyze_band_image,
    apply_band_evaluation,
    calculate_best_operating_condition,
    calculate_best_band_table,
    calculate_cleaner_ranking,
    calculate_monthly_summary,
    calculate_table_comparison,
    calculate_top_metrics,
    prepare_process_metrics,
)
from data_loader import DataLoadError, load_excel_data
from dashboard import (
    collect_band_inputs,
    render_dashboard,
    render_header,
    render_sensitivity_analysis,
    render_sidebar,
)
from recommendations import generate_operating_recommendations


DEFAULT_DATA_FILE = "cleaner_current (2).xlsx"


def main() -> None:
    """Run the Streamlit application."""
    st.set_page_config(
        page_title="Cleaner Shaking Table Performance Dashboard",
        layout="wide",
    )

    render_header()
    cleaner_tab, sensitivity_tab = st.tabs(["Cleaner Performance", "Sensitivity Analysis"])

    with cleaner_tab:
        st.header("Cleaner Performance")
        uploaded_file = render_sidebar(DEFAULT_DATA_FILE)

        try:
            raw_data = load_data_source(uploaded_file)
            prepared_data = prepare_process_metrics(raw_data)
        except (DataLoadError, CalculationError) as error:
            st.error(f"Unable to load data: {error}")
            return

        uploaded_images = {}
        band_analyses = {}

        for row_index, row in prepared_data.iterrows():
            uploaded_images[row_index] = None
            band_analyses[row_index] = {"has_image": False, "has_detection": False}

        band_scores, uploaded_images = collect_band_inputs(prepared_data, band_analyses)

        for row_index, uploaded_image in uploaded_images.items():
            if uploaded_image is None:
                continue
            try:
                band_analyses[row_index] = analyze_band_image(uploaded_image)
            except CalculationError as error:
                st.warning(f"{prepared_data.loc[row_index, 'Table']}: {error}")
                band_analyses[row_index] = {"has_image": False, "has_detection": False}

        detected_band_scores = []
        for row_index, manual_score in zip(prepared_data.index, band_scores):
            analysis = band_analyses.get(row_index, {})
            detected_band_scores.append(float(analysis.get("band_score", manual_score)))

        try:
            prepared_data = apply_band_evaluation(prepared_data, detected_band_scores)
        except CalculationError as error:
            st.error(f"Unable to calculate band evaluation: {error}")
            return

        metrics = calculate_top_metrics(prepared_data)
        comparison = calculate_table_comparison(prepared_data)
        monthly_summary = calculate_monthly_summary(prepared_data)
        ranking = calculate_cleaner_ranking(prepared_data)
        best_condition = calculate_best_operating_condition(prepared_data)
        best_band_table = calculate_best_band_table(prepared_data)
        alerts = evaluate_performance_alerts(prepared_data)
        recommendations = generate_operating_recommendations(prepared_data)

        render_dashboard(
            prepared_data,
            metrics,
            comparison,
            monthly_summary,
            ranking,
            best_condition,
            best_band_table,
            uploaded_images,
            band_analyses,
            alerts,
            recommendations,
        )

    with sensitivity_tab:
        render_sensitivity_analysis()


def load_data_source(uploaded_file):
    """Load data from an uploaded workbook or the default sample file."""
    if uploaded_file is not None:
        return load_excel_data(uploaded_file)

    default_path = Path(DEFAULT_DATA_FILE)
    if default_path.exists():
        st.info(f"Showing sample data from `{DEFAULT_DATA_FILE}`.")
        return load_excel_data(default_path)

    st.warning("Upload an Excel workbook to begin.")
    st.stop()


if __name__ == "__main__":
    main()
