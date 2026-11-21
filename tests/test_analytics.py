"""Analytics engine tests: import, statistics, regression."""
import numpy as np
import pandas as pd
import pytest

from axiomata.analytics import dataset_manager as dm
from axiomata.analytics import statistics as stats


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "x": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "y": [2.1, 3.9, 6.2, 7.8, 10.1, 12.0, 13.9, 16.2, 17.8, 20.1],
        "category": ["a", "b", "a", "b", "a", "b", "a", "b", "a", "b"],
        "value": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
    })


def test_import_csv(tmp_path, sample_df):
    p = tmp_path / "data.csv"
    sample_df.to_csv(p, index=False)
    df = dm.import_dataset(str(p))
    assert list(df.columns) == ["x", "y", "category", "value"]
    assert len(df) == 10


def test_import_json(tmp_path, sample_df):
    p = tmp_path / "data.json"
    sample_df.to_json(p, orient="records")
    df = dm.import_dataset(str(p))
    assert "x" in df.columns


def test_import_parquet(tmp_path, sample_df):
    p = tmp_path / "data.parquet"
    sample_df.to_parquet(p)
    df = dm.import_dataset(str(p))
    assert len(df) == 10


def test_import_unsupported(tmp_path):
    p = tmp_path / "data.xyz"
    p.write_text("hello")
    with pytest.raises(dm.ImportError_):
        dm.import_dataset(str(p))


def test_import_missing_file():
    with pytest.raises(dm.ImportError_):
        dm.import_dataset("/nonexistent/file.csv")


def test_dataset_summary(sample_df):
    s = dm.dataset_summary(sample_df)
    assert s["rows"] == 10
    assert s["columns"] == 4
    assert "x" in s["column_names"]


def test_numeric_columns(sample_df):
    assert dm.numeric_columns(sample_df) == ["x", "y", "value"]


def test_descriptive_stats(sample_df):
    s = stats.descriptive_stats(sample_df, "x")
    assert s["count"] == 10
    assert s["mean"] == pytest.approx(5.5)
    assert s["min"] == 1
    assert s["max"] == 10
    assert s["median"] == pytest.approx(5.5)


def test_correlation_perfect(sample_df):
    # x and y are almost perfectly correlated
    corr = stats.correlation_matrix(sample_df)
    assert corr.loc["x", "y"] == pytest.approx(1.0, abs=0.02)


def test_linear_regression(sample_df):
    # y ≈ 2x + 0
    res = stats.linear_regression(sample_df, "x", "y")
    assert res["slope"] == pytest.approx(2.0, abs=0.1)
    assert res["r_squared"] == pytest.approx(1.0, abs=0.01)
    assert res["n"] == 10


def test_linear_regression_insufficient():
    df = pd.DataFrame({"x": [1], "y": [2]})
    with pytest.raises(ValueError):
        stats.linear_regression(df, "x", "y")


def test_histogram(sample_df):
    counts, edges = stats.histogram_data(sample_df, "x", bins=5)
    assert len(counts) == 5
    assert sum(counts) == 10


def test_groupby_aggregate(sample_df):
    res = stats.groupby_aggregate(sample_df, "category", "value", "mean")
    assert set(res["category"]) == {"a", "b"}
    # a: 10,30,50,70,90 -> mean 50; b: 20,40,60,80,100 -> mean 60
    a_mean = res[res["category"] == "a"]["value"].values[0]
    assert a_mean == pytest.approx(50.0)


def test_filter(sample_df):
    res = stats.filter_dataframe(sample_df, "x", ">", 5)
    assert len(res) == 5


def test_drop_missing():
    df = pd.DataFrame({"a": [1, 2, np.nan], "b": [4, 5, 6]})
    res = stats.drop_missing(df)
    assert len(res) == 2


def test_fill_missing_mean():
    df = pd.DataFrame({"a": [1, 2, np.nan, 4]})
    res = stats.fill_missing(df, "mean")
    assert res["a"].isna().sum() == 0
    assert res["a"].iloc[2] == pytest.approx((1 + 2 + 4) / 3)