"""Operating recommendations for the cleaner table dashboard."""

from __future__ import annotations

import pandas as pd


def generate_operating_recommendations(dataframe: pd.DataFrame) -> list[str]:
    """Generate simple operating recommendations from current performance."""
    recommendations: list[str] = []

    low_conc = dataframe[dataframe["Yield_Conc"] < 60]
    high_tail = dataframe[dataframe["Yield_Tail"] > 15]

    if not low_conc.empty:
        tables = ", ".join(low_conc["Table"].astype(str).tolist())
        if dataframe["Slope"].notna().any() or dataframe["Wash_Water_Lps"].notna().any():
            recommendations.append(
                f"Low concentrate yield on {tables}. Check slope and wash water settings against the better-performing tables."
            )
        else:
            recommendations.append(
                f"Low concentrate yield on {tables}. Review slope and wash water settings to improve concentrate recovery."
            )

    if not high_tail.empty:
        tables = ", ".join(high_tail["Table"].astype(str).tolist())
        recommendations.append(
            f"High tail losses detected on {tables}. Inspect cut-point control and operating stability to reduce mineral losses to tailings."
        )

    if not recommendations:
        recommendations.append(
            "Cleaner table performance is within current alert thresholds. Continue monitoring yield, slope, and wash water trends."
        )

    return recommendations


def summarize_recommendations(recommendations: list[str]) -> str:
    """Return a short placeholder summary of recommendations."""
    if not recommendations:
        return "No recommendations generated."
    return "\n".join(recommendations)
