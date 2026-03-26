"""Utilities for loading and validating cleaner table Excel data."""

from pathlib import Path
from typing import BinaryIO, Union

import pandas as pd


ExcelSource = Union[str, Path, BinaryIO]


class DataLoadError(Exception):
    """Raised when Excel data cannot be loaded or validated."""


def load_excel_data(source: ExcelSource, sheet_name: int | str = 0) -> pd.DataFrame:
    """Load cleaner table data from an Excel workbook."""
    try:
        dataframe = pd.read_excel(source, sheet_name=sheet_name)
    except Exception as error:  # pragma: no cover - defensive wrapper
        raise DataLoadError(str(error)) from error

    return validate_dataframe(dataframe)


def validate_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Apply lightweight validation to the loaded data."""
    if dataframe.empty:
        raise DataLoadError("The selected worksheet is empty.")

    return dataframe.copy()


def get_available_sheets(source: ExcelSource) -> list[str]:
    """Return workbook sheet names for future multi-sheet support."""
    try:
        workbook = pd.ExcelFile(source)
    except Exception as error:  # pragma: no cover - defensive wrapper
        raise DataLoadError(str(error)) from error

    return workbook.sheet_names
