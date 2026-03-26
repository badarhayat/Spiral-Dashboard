"""Performance alert rules for the cleaner table dashboard."""

from __future__ import annotations

import pandas as pd


def evaluate_performance_alerts(dataframe: pd.DataFrame) -> list[dict]:
    """Generate process alerts based on yield thresholds."""
    alerts: list[dict] = []

    for _, row in dataframe.iterrows():
        table_name = row.get("Table", "Unknown")
        yield_conc = row.get("Yield_Conc")
        yield_tail = row.get("Yield_Tail")

        if pd.notna(yield_conc) and float(yield_conc) < 60:
            alerts.append(
                {
                    "level": "warning",
                    "table": table_name,
                    "metric": "Yield_Conc",
                    "message": f"{table_name}: Yield_Conc is below target at {yield_conc:.1f}%.",
                }
            )

        if pd.notna(yield_tail) and float(yield_tail) > 15:
            alerts.append(
                {
                    "level": "warning",
                    "table": table_name,
                    "metric": "Yield_Tail",
                    "message": f"{table_name}: Yield_Tail is elevated at {yield_tail:.1f}%, indicating losses.",
                }
            )

        if row.get("flag") == "Mass balance error":
            alerts.append(
                {
                    "level": "warning",
                    "table": table_name,
                    "metric": "Mass_Balance",
                    "message": f"{table_name}: Mass balance error. Total_Yield deviates from 100% by more than 2%.",
                }
            )

    return alerts


def format_alert_messages(alerts: list[dict]) -> list[str]:
    """Convert alert dictionaries into display-ready text."""
    return [alert["message"] for alert in alerts]
