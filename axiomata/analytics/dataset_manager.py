"""Dataset import and management for the data-analysis module.

Supports CSV, JSON, Excel, Parquet, and HDF5. Imported data is loaded into a
pandas DataFrame and registered with DuckDB for analytical queries. Original
imported datasets are never silently altered; a working copy is provided for
transformations so raw data stays intact.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd


class ImportError_(Exception):
    """Raised when a dataset cannot be imported."""


def import_dataset(path: str) -> pd.DataFrame:
    """Import a dataset from disk based on its extension.

    Returns a DataFrame. Raises ImportError_ on unsupported or unreadable files.
    The returned DataFrame is the raw imported data (a copy is made for any
    subsequent transformation so the original stays intact).
    """
    p = Path(path)
    if not p.exists():
        raise ImportError_(f"File not found: {path}")
    suffix = p.suffix.lower()

    try:
        if suffix == ".csv":
            return pd.read_csv(p)
        if suffix in (".json",):
            return pd.read_json(p)
        if suffix in (".xlsx", ".xls"):
            return pd.read_excel(p)
        if suffix == ".parquet":
            return pd.read_parquet(p)
        if suffix in (".h5", ".hdf5", ".hdf"):
            return pd.read_hdf(p)
        if suffix == ".txt":
            return pd.read_csv(p, sep=None, engine="python")
    except Exception as exc:  # noqa: BLE001
        raise ImportError_(f"Failed to import {p.name}: {exc}") from exc

    raise ImportError_(f"Unsupported file format: {suffix or '(none)'}")


def dataset_summary(df: pd.DataFrame) -> dict:
    """Return a summary of a DataFrame: shape, dtypes, missing values."""
    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": list(df.columns),
        "dtypes": {c: str(df[c].dtype) for c in df.columns},
        "missing": {c: int(df[c].isna().sum()) for c in df.columns},
    }


def numeric_columns(df: pd.DataFrame) -> list[str]:
    return list(df.select_dtypes(include="number").columns)


def categorical_columns(df: pd.DataFrame) -> list[str]:
    return list(df.select_dtypes(include=["object", "category", "bool"]).columns)