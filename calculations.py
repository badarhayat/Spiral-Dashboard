"""Process calculation functions for the cleaner shaking table dashboard."""

from __future__ import annotations

import numpy as np
import pandas as pd


SLURRY_DENSITY = 1.2
MASS_BALANCE_TOLERANCE = 2.0
SECONDS_PER_HOUR = 3600

REQUIRED_COLUMNS = [
    "Date",
    "Table",
    "Conc_Flow_Lps",
    "Midd_Flow_Lps",
    "Tail_Flow_Lps",
    "Conc_Slurry_Weight",
    "Midd_Slurry_Weight",
    "Tail_Slurry_Weight",
    "Conc_Dry_Weight",
    "Midd_Dry_Weight",
    "Tail_Dry_Weight",
    "Slope",
    "Wash_Water_Lps",
]

SENSITIVITY_REQUIRED_COLUMNS = [
    "Slope",
    "Wash_Water_Lps",
    "Conc_Flow_Lps",
    "Midd_Flow_Lps",
    "Tail_Flow_Lps",
    "Conc_Slurry_Weight",
    "Midd_Slurry_Weight",
    "Tail_Slurry_Weight",
    "Conc_Dry_Weight",
    "Midd_Dry_Weight",
    "Tail_Dry_Weight",
]


class CalculationError(Exception):
    """Raised when required plant-model calculations cannot be completed."""


def prepare_process_metrics(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Validate the input schema and apply the plant model exactly."""
    validate_required_columns(dataframe)

    calculated = dataframe.copy()
    for column in REQUIRED_COLUMNS:
        if column not in {"Date", "Table"}:
            calculated[column] = pd.to_numeric(calculated[column], errors="coerce")
    calculated["Date"] = pd.to_datetime(calculated["Date"], errors="coerce")

    calculated = apply_core_yield_calculations(calculated)
    calculated = apply_additional_dashboard_calculations(calculated)
    return calculated


def prepare_sensitivity_metrics(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Apply the same core cleaner calculations to sensitivity-study data."""
    validate_sensitivity_columns(dataframe)

    calculated = dataframe.copy()
    for column in SENSITIVITY_REQUIRED_COLUMNS:
        calculated[column] = pd.to_numeric(calculated[column], errors="coerce")

    return apply_core_yield_calculations(calculated)


def apply_core_yield_calculations(calculated: pd.DataFrame) -> pd.DataFrame:
    """Apply the shared cleaner yield calculation logic."""

    calculated["Conc_Solid_Percent"] = round_series(
        safe_divide(calculated["Conc_Dry_Weight"], calculated["Conc_Slurry_Weight"]) * 100
    )
    calculated["Midd_Solid_Percent"] = round_series(
        safe_divide(calculated["Midd_Dry_Weight"], calculated["Midd_Slurry_Weight"]) * 100
    )
    calculated["Tail_Solid_Percent"] = round_series(
        safe_divide(calculated["Tail_Dry_Weight"], calculated["Tail_Slurry_Weight"]) * 100
    )

    calculated["Conc_Flow_Lph"] = round_series(calculated["Conc_Flow_Lps"] * SECONDS_PER_HOUR)
    calculated["Midd_Flow_Lph"] = round_series(calculated["Midd_Flow_Lps"] * SECONDS_PER_HOUR)
    calculated["Tail_Flow_Lph"] = round_series(calculated["Tail_Flow_Lps"] * SECONDS_PER_HOUR)

    calculated["Conc_Mass_Flow"] = round_series(calculated["Conc_Flow_Lph"] * SLURRY_DENSITY)
    calculated["Midd_Mass_Flow"] = round_series(calculated["Midd_Flow_Lph"] * SLURRY_DENSITY)
    calculated["Tail_Mass_Flow"] = round_series(calculated["Tail_Flow_Lph"] * SLURRY_DENSITY)

    calculated["Conc_Solid_Flow"] = round_series(
        calculated["Conc_Mass_Flow"] * safe_divide(calculated["Conc_Solid_Percent"], 100)
    )
    calculated["Midd_Solid_Flow"] = round_series(
        calculated["Midd_Mass_Flow"] * safe_divide(calculated["Midd_Solid_Percent"], 100)
    )
    calculated["Tail_Solid_Flow"] = round_series(
        calculated["Tail_Mass_Flow"] * safe_divide(calculated["Tail_Solid_Percent"], 100)
    )

    calculated["Conc_kgph"] = round_series(calculated["Conc_Solid_Flow"])
    calculated["Midd_kgph"] = round_series(calculated["Midd_Solid_Flow"])
    calculated["Tail_kgph"] = round_series(calculated["Tail_Solid_Flow"])

    calculated["Conc_kgpd"] = round_series(calculated["Conc_kgph"] * 24)
    calculated["Midd_kgpd"] = round_series(calculated["Midd_kgph"] * 24)
    calculated["Tail_kgpd"] = round_series(calculated["Tail_kgph"] * 24)

    calculated["Feed_Solid_Flow"] = round_series(
        calculated["Conc_Solid_Flow"].fillna(0)
        + calculated["Midd_Solid_Flow"].fillna(0)
        + calculated["Tail_Solid_Flow"].fillna(0)
    )

    calculated["Yield_Conc"] = round_series(
        safe_divide(calculated["Conc_Solid_Flow"], calculated["Feed_Solid_Flow"]) * 100
    )
    calculated["Yield_Midd"] = round_series(
        safe_divide(calculated["Midd_Solid_Flow"], calculated["Feed_Solid_Flow"]) * 100
    )
    calculated["Yield_Tail"] = round_series(
        safe_divide(calculated["Tail_Solid_Flow"], calculated["Feed_Solid_Flow"]) * 100
    )

    return calculated


def apply_additional_dashboard_calculations(calculated: pd.DataFrame) -> pd.DataFrame:
    """Apply extra dashboard-only calculations after core yield logic."""

    calculated["Total_Yield"] = round_series(
        calculated["Yield_Conc"].fillna(0)
        + calculated["Yield_Midd"].fillna(0)
        + calculated["Yield_Tail"].fillna(0)
    )
    calculated["flag"] = np.where(
        (calculated["Total_Yield"] - 100).abs() > MASS_BALANCE_TOLERANCE,
        "Mass balance error",
        "OK",
    )

    max_conc_kgph = calculated["Conc_kgph"].max()
    calculated["Norm_Production"] = round_series(
        safe_divide(calculated["Conc_kgph"], max_conc_kgph)
    )
    calculated["Score"] = round_series(
        (0.6 * calculated["Yield_Conc"]) + (0.4 * calculated["Norm_Production"] * 100)
    )
    calculated["Rank"] = round_series(
        calculated["Score"].rank(ascending=False, method="min")
    )
    calculated["Performance_Score"] = round_series(
        (0.6 * calculated["Yield_Conc"])
        - (0.3 * calculated["Yield_Tail"])
        - (0.1 * calculated["Yield_Midd"])
    )

    return calculated


def apply_band_evaluation(dataframe: pd.DataFrame, band_scores: list[float]) -> pd.DataFrame:
    """Apply manual band scores and compute the image-assisted final score."""
    if len(band_scores) != len(dataframe):
        raise CalculationError("Band score input count does not match the number of table runs.")

    calculated = dataframe.copy()
    calculated["Band_Score"] = round_series(pd.Series(band_scores, index=calculated.index))
    calculated["Final_Score"] = round_series(
        (0.5 * calculated["Yield_Conc"])
        - (0.2 * calculated["Yield_Tail"])
        - (0.1 * calculated["Yield_Midd"])
        + (0.2 * (calculated["Band_Score"] * 20))
    )
    return calculated


def analyze_band_image(uploaded_file) -> dict:
    """Detect the main mineral band using the advanced ROI and contour-scoring method."""
    try:
        import cv2
    except ImportError as error:  # pragma: no cover - depends on environment
        raise CalculationError("OpenCV is required for automatic band detection.") from error

    if uploaded_file is None:
        return {"has_image": False, "has_detection": False}

    image_bytes = uploaded_file.getvalue()
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    color_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if color_image is None:
        raise CalculationError("Unable to read the uploaded image for band detection.")

    resized_image = cv2.resize(color_image, (600, 800))
    original = resized_image.copy()
    image_height, image_width = resized_image.shape[:2]

    y_start = int(image_height * 0.20)
    y_end = int(image_height * 0.90)
    x_start = int(image_width * 0.30)
    x_end = int(image_width * 0.90)
    roi_image = resized_image[y_start:y_end, x_start:x_end]
    roi_display = roi_image.copy()

    blurred_roi = cv2.GaussianBlur(roi_image, (5, 5), 0)
    hsv_roi = cv2.cvtColor(blurred_roi, cv2.COLOR_BGR2HSV)
    gray_roi = cv2.cvtColor(blurred_roi, cv2.COLOR_BGR2GRAY)

    mask_red = cv2.inRange(hsv_roi, np.array([0, 80, 50]), np.array([10, 255, 255])) + cv2.inRange(
        hsv_roi, np.array([170, 80, 50]), np.array([180, 255, 255])
    )
    _, thresh = cv2.threshold(gray_roi, 120, 255, cv2.THRESH_BINARY_INV)
    combined_mask = cv2.bitwise_or(mask_red, thresh)

    kernel = np.ones((5, 5), np.uint8)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)

    band_contour, contour_score = select_main_band_contour(combined_mask)
    detection_mode = "color+gray"

    overlay = original.copy()
    cv2.rectangle(overlay, (x_start, y_start), (x_end, y_end), (255, 255, 0), 2)

    if band_contour is None:
        return {
            "has_image": True,
            "has_detection": False,
            "original_image": bgr_to_rgb(original),
            "overlay_image": bgr_to_rgb(overlay),
            "roi_image": bgr_to_rgb(roi_image),
            "mask_image": combined_mask,
        }

    x, y, width, height = cv2.boundingRect(band_contour)
    full_x = x + x_start
    full_y = y + y_start
    cv2.drawContours(overlay[y_start:y_end, x_start:x_end], [band_contour], -1, (0, 255, 0), 2)
    cv2.rectangle(overlay, (full_x, full_y), (full_x + width, full_y + height), (255, 0, 0), 2)
    cv2.rectangle(roi_display, (x, y), (x + width, y + height), (0, 255, 0), 2)

    band_width = float(width)
    band_position = float((y + (height / 2)) / max(roi_image.shape[0], 1))
    band_area = float(cv2.contourArea(band_contour))
    band_region = gray_roi[y : y + max(height, 1), x : x + max(width, 1)]
    sharpness = float(np.std(band_region)) if band_region.size else 0.0

    width_score = 1 / (band_width + 1)
    position_score = 1 - abs(band_position - 0.5)
    sharpness_score = sharpness / 100
    raw_band_score = round(
        (
            (0.4 * sharpness_score)
            + (0.3 * width_score)
            + (0.3 * position_score)
        )
        * 100,
        2,
    )
    raw_band_score = float(np.clip(raw_band_score, 0, 100))
    band_score = round(np.clip(raw_band_score / 20, 1, 5), 2)

    return {
        "has_image": True,
        "has_detection": True,
        "original_image": bgr_to_rgb(original),
        "overlay_image": bgr_to_rgb(overlay),
        "roi_image": bgr_to_rgb(roi_display),
        "mask_image": combined_mask,
        "band_width": round(band_width, 2),
        "band_position": round(band_position, 3),
        "band_area": round(band_area, 2),
        "sharpness": round(sharpness, 2),
        "width_score": round(float(width_score), 3),
        "position_score": round(float(position_score), 3),
        "sharpness_score": round(float(sharpness_score), 3),
        "contour_score": round(float(contour_score), 2),
        "raw_band_score": raw_band_score,
        "band_score": band_score,
        "classification": classify_band_score(raw_band_score),
        "detection_mode": detection_mode,
    }


def calculate_mass_balance(dataframe: pd.DataFrame) -> dict:
    """Summarize mass balance status across cleaner tables."""
    flagged = dataframe[dataframe["flag"] == "Mass balance error"]
    return {
        "warning_count": int(len(flagged)),
        "tables": flagged["Table"].astype(str).tolist(),
    }


def calculate_recovery_metrics(dataframe: pd.DataFrame) -> dict:
    """Summarize yield metrics for downstream use."""
    return {
        "average_yield_conc": float(dataframe["Yield_Conc"].dropna().mean())
        if dataframe["Yield_Conc"].notna().any()
        else np.nan,
        "average_yield_tail": float(dataframe["Yield_Tail"].dropna().mean())
        if dataframe["Yield_Tail"].notna().any()
        else np.nan,
    }


def calculate_top_metrics(dataframe: pd.DataFrame) -> dict:
    """Calculate high-level KPI values for the dashboard."""
    yield_conc = dataframe["Yield_Conc"].dropna()
    total_feed = dataframe["Feed_Solid_Flow"].dropna().sum()

    if yield_conc.empty:
        best_table = "N/A"
        best_yield = np.nan
        average_yield = np.nan
    else:
        best_index = dataframe["Yield_Conc"].idxmax()
        best_table = str(dataframe.loc[best_index, "Table"])
        best_yield = float(dataframe.loc[best_index, "Yield_Conc"])
        average_yield = float(yield_conc.mean())

    return {
        "average_yield_conc": average_yield,
        "best_performing_table": best_table,
        "best_yield_conc": best_yield,
        "total_feed_processed": float(total_feed) if pd.notna(total_feed) else np.nan,
    }


def calculate_table_comparison(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return cleaner-by-cleaner comparison data sorted by concentrate yield."""
    comparison = dataframe[
        [
            "Table",
            "Yield_Conc",
            "Yield_Midd",
            "Yield_Tail",
            "Feed_Solid_Flow",
            "Slope",
            "Wash_Water_Lps",
            "flag",
        ]
    ].copy()
    return comparison.sort_values(by="Yield_Conc", ascending=False, na_position="last")


def calculate_monthly_summary(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Summarize daily production by calendar month."""
    if dataframe["Date"].isna().all():
        raise CalculationError("Date column could not be converted to datetime.")

    monthly = (
        dataframe.dropna(subset=["Date"])
        .groupby(lambda index: dataframe.loc[index, "Date"].to_period("M"))
        .agg(
            {
                "Conc_kgpd": "sum",
                "Midd_kgpd": "sum",
                "Tail_kgpd": "sum",
            }
        )
        .reset_index(names="Date")
    )
    monthly["Conc_ton"] = round_series(monthly["Conc_kgpd"] / 1000)
    monthly["Midd_ton"] = round_series(monthly["Midd_kgpd"] / 1000)
    monthly["Tail_ton"] = round_series(monthly["Tail_kgpd"] / 1000)
    monthly[["Conc_kgpd", "Midd_kgpd", "Tail_kgpd"]] = monthly[
        ["Conc_kgpd", "Midd_kgpd", "Tail_kgpd"]
    ].round(2)
    monthly["Date"] = monthly["Date"].astype(str)
    return monthly


def calculate_cleaner_ranking(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return cleaner ranking based on yield and normalized production."""
    ranking = dataframe[
        ["Table", "Yield_Conc", "Conc_kgph", "Norm_Production", "Score", "Rank"]
    ].copy()
    return ranking.sort_values(by=["Rank", "Score"], ascending=[True, False], na_position="last")


def calculate_best_operating_condition(dataframe: pd.DataFrame) -> dict:
    """Return recommended operating conditions from the top 3 performance scores."""
    if len(dataframe) < 3:
        return {
            "has_enough_data": False,
            "message": "Not enough data for optimization",
            "best_index": None,
            "top_indices": [],
        }

    valid_rows = dataframe.dropna(
        subset=["Performance_Score", "Slope", "Wash_Water_Lps", "Yield_Conc", "Yield_Tail"]
    )
    if valid_rows.empty:
        return {
            "has_enough_data": False,
            "message": "Not enough data for optimization",
            "best_index": None,
            "top_indices": [],
        }

    top_rows = valid_rows.nlargest(3, "Performance_Score")
    best_index = top_rows["Performance_Score"].idxmax()
    best_row = dataframe.loc[best_index]
    return {
        "has_enough_data": True,
        "message": "",
        "best_index": best_index,
        "top_indices": top_rows.index.tolist(),
        "table": best_row["Table"],
        "best_slope": round_value(best_row["Slope"]),
        "best_wash_water": round_value(best_row["Wash_Water_Lps"]),
        "yield_conc": round_value(best_row["Yield_Conc"]),
        "yield_tail": round_value(best_row["Yield_Tail"]),
        "performance_score": round_value(best_row["Performance_Score"]),
        "average_slope": round_value(top_rows["Slope"].mean()),
        "average_wash_water": round_value(top_rows["Wash_Water_Lps"].mean()),
    }


def calculate_best_band_table(dataframe: pd.DataFrame) -> dict:
    """Return the best table based on final score after band evaluation."""
    valid_rows = dataframe.dropna(subset=["Final_Score", "Band_Score", "Yield_Conc", "Yield_Tail"])
    if valid_rows.empty:
        return {
            "has_data": False,
            "message": "Band analysis will appear after band scores are entered.",
            "best_index": None,
        }

    best_index = valid_rows["Final_Score"].idxmax()
    best_row = dataframe.loc[best_index]
    return {
        "has_data": True,
        "message": "",
        "best_index": best_index,
        "table": best_row["Table"],
        "yield_conc": round_value(best_row["Yield_Conc"]),
        "yield_tail": round_value(best_row["Yield_Tail"]),
        "band_score": round_value(best_row["Band_Score"]),
        "final_score": round_value(best_row["Final_Score"]),
    }


def validate_required_columns(dataframe: pd.DataFrame) -> None:
    """Raise an error if any required plant-model column is missing."""
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in dataframe.columns]
    if missing_columns:
        raise CalculationError(f"Missing required column(s): {', '.join(missing_columns)}")


def validate_sensitivity_columns(dataframe: pd.DataFrame) -> None:
    """Raise an error if any required sensitivity-study column is missing."""
    missing_columns = [column for column in SENSITIVITY_REQUIRED_COLUMNS if column not in dataframe.columns]
    if missing_columns:
        raise CalculationError(f"Missing required column(s): {', '.join(missing_columns)}")


def safe_divide(numerator: pd.Series, denominator: pd.Series | float | int) -> pd.Series:
    """Safely divide two values and return NaN where division is not possible."""
    denominator_series = denominator
    if not isinstance(denominator, pd.Series):
        denominator_series = pd.Series(denominator, index=numerator.index)

    result = numerator.divide(denominator_series)
    invalid = denominator_series.isna() | denominator_series.eq(0)
    return result.mask(invalid, np.nan)


def round_series(series: pd.Series) -> pd.Series:
    """Round numeric series to plant reporting precision."""
    return pd.to_numeric(series, errors="coerce").round(2)


def round_value(value: float) -> float:
    """Round a single numeric value to plant reporting precision."""
    return round(float(value), 2)


def bgr_to_rgb(image: np.ndarray) -> np.ndarray:
    """Convert an OpenCV BGR image to RGB for Streamlit display."""
    return image[:, :, ::-1]


def classify_band_score(raw_band_score: float) -> str:
    """Classify a 0-100 band score into operator-friendly labels."""
    if raw_band_score > 75:
        return "Excellent"
    if raw_band_score > 55:
        return "Good"
    if raw_band_score > 35:
        return "Average"
    return "Poor"


def select_main_band_contour(mask: np.ndarray):
    """Select the main horizontal band contour while filtering noise."""
    try:
        import cv2
    except ImportError as error:  # pragma: no cover - depends on environment
        raise CalculationError("OpenCV is required for automatic band detection.") from error

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best_contour = None
    best_score = 0.0

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 1500:
            continue
        x, y, width, height = cv2.boundingRect(contour)
        if width <= 0 or height <= 0:
            continue
        aspect_ratio = width / max(height, 1)
        score = area * aspect_ratio
        if score > best_score:
            best_score = score
            best_contour = contour

    return best_contour, best_score
