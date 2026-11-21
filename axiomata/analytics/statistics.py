"""Statistical analysis for scientific datasets.

Provides descriptive statistics, correlation, linear regression, and histogram
binning. Uses pandas/NumPy/SciPy. No fabricated data — every result is computed
from the provided DataFrame.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


def descriptive_stats(df: pd.DataFrame, column: str) -> dict:
    """Compute descriptive statistics for a numeric column."""
    s = pd.to_numeric(df[column], errors="coerce").dropna()
    if len(s) == 0:
        return {"count": 0}
    return {
        "count": int(s.count()),
        "mean": float(s.mean()),
        "std": float(s.std(ddof=1)) if s.count() > 1 else 0.0,
        "min": float(s.min()),
        "q1": float(s.quantile(0.25)),
        "median": float(s.median()),
        "q3": float(s.quantile(0.75)),
        "max": float(s.max()),
        "range": float(s.max() - s.min()),
        "variance": float(s.var(ddof=1)) if s.count() > 1 else 0.0,
        "skew": float(s.skew()) if s.count() > 2 else 0.0,
        "kurtosis": float(s.kurt()) if s.count() > 3 else 0.0,
        "missing": int(df[column].isna().sum()),
    }


def correlation_matrix(df: pd.DataFrame, columns: Optional[list[str]] = None) -> pd.DataFrame:
    """Pearson correlation matrix for numeric columns."""
    num = df.select_dtypes(include="number")
    if columns:
        num = num[[c for c in columns if c in num.columns]]
    return num.corr()


def linear_regression(df: pd.DataFrame, x_col: str, y_col: str) -> dict:
    """Ordinary least squares linear regression y = slope*x + intercept.

    Returns slope, intercept, r-squared, and standard errors computed from the
    data. Uses numpy least squares.
    """
    x = pd.to_numeric(df[x_col], errors="coerce")
    y = pd.to_numeric(df[y_col], errors="coerce")
    mask = x.notna() & y.notna()
    xv = x[mask].to_numpy(dtype=float)
    yv = y[mask].to_numpy(dtype=float)
    n = len(xv)
    if n < 2:
        raise ValueError("Need at least 2 valid points for regression")
    # Design matrix [x, 1]
    A = np.vstack([xv, np.ones(n)]).T
    coeffs, residuals, rank, sv = np.linalg.lstsq(A, yv, rcond=None)
    slope, intercept = coeffs
    y_pred = slope * xv + intercept
    ss_res = float(np.sum((yv - y_pred) ** 2))
    ss_tot = float(np.sum((yv - yv.mean()) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    # Standard errors of coefficients.
    if n > 2:
        mse = ss_res / (n - 2)
        sigma = np.sqrt(mse)
        # variance of slope and intercept
        sxx = np.sum((xv - xv.mean()) ** 2)
        slope_se = sigma / np.sqrt(sxx) if sxx > 0 else float("nan")
        intercept_se = sigma * np.sqrt(1.0 / n + xv.mean() ** 2 / sxx) if sxx > 0 else float("nan")
    else:
        slope_se = intercept_se = float("nan")
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(r_squared),
        "slope_se": float(slope_se),
        "intercept_se": float(intercept_se),
        "n": int(n),
        "predictions": y_pred,
        "x": xv,
        "y": yv,
    }


def histogram_data(df: pd.DataFrame, column: str, bins: int = 20) -> tuple[np.ndarray, np.ndarray]:
    """Return (counts, bin_edges) for a histogram of a numeric column."""
    s = pd.to_numeric(df[column], errors="coerce").dropna().to_numpy(dtype=float)
    counts, edges = np.histogram(s, bins=bins)
    return counts, edges


def groupby_aggregate(df: pd.DataFrame, by: str, value: str,
                      agg: str = "mean") -> pd.DataFrame:
    """Aggregate a numeric column grouped by a categorical column."""
    funcs = {"mean": "mean", "sum": "sum", "count": "count", "median": "median",
             "min": "min", "max": "max", "std": "std"}
    if agg not in funcs:
        raise ValueError(f"Unknown aggregation: {agg}")
    return df.groupby(by)[value].agg(funcs[agg]).reset_index()


def filter_dataframe(df: pd.DataFrame, column: str, op: str, value) -> pd.DataFrame:
    """Filter a DataFrame by a comparison on one column.

    op: '==', '!=', '>', '<', '>=', '<=', 'contains'
    """
    series = df[column]
    if op == "==":
        return df[series == value]
    if op == "!=":
        return df[series != value]
    if op == ">":
        return df[pd.to_numeric(series, errors="coerce") > float(value)]
    if op == "<":
        return df[pd.to_numeric(series, errors="coerce") < float(value)]
    if op == ">=":
        return df[pd.to_numeric(series, errors="coerce") >= float(value)]
    if op == "<=":
        return df[pd.to_numeric(series, errors="coerce") <= float(value)]
    if op == "contains":
        return df[series.astype(str).str.contains(str(value), case=False, na=False)]
    raise ValueError(f"Unknown operator: {op}")


def drop_missing(df: pd.DataFrame, how: str = "any") -> pd.DataFrame:
    """Return a copy with rows containing missing values removed."""
    return df.dropna(how=how).copy()


def fill_missing(df: pd.DataFrame, strategy: str = "mean") -> pd.DataFrame:
    """Return a copy with missing numeric values filled.

    strategy: 'mean' | 'median' | 'zero' | 'ffill'
    """
    out = df.copy()
    num = out.select_dtypes(include="number").columns
    if strategy == "mean":
        out[num] = out[num].fillna(out[num].mean())
    elif strategy == "median":
        out[num] = out[num].fillna(out[num].median())
    elif strategy == "zero":
        out[num] = out[num].fillna(0)
    elif strategy == "ffill":
        out = out.ffill()
    else:
        raise ValueError(f"Unknown fill strategy: {strategy}")
    return out