"""Data Analysis page.

Import datasets (CSV/JSON/Excel/Parquet/HDF5), preview and filter data, compute
descriptive statistics, run correlation and regression, and generate charts.
Datasets are registered with DuckDB for analytical queries. Raw imported data is
never modified — transformations operate on a working copy.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox,
    QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit, QVBoxLayout,
    QWidget,
)

from ..core.application import AppContext
from ..ui.panels.base_page import BasePage
from ..ui.widgets.chart_widget import ChartWidget
from ..ui.themes.theme import ACCENT, ACCENT_BLUE
from ..analytics import dataset_manager as dm
from ..analytics import statistics as stats


class DataAnalysisPage(BasePage):
    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None):
        super().__init__("Data Analysis",
                         "Import datasets, run statistics, and generate scientific charts.",
                         parent)
        self.ctx = ctx
        self._df: Optional[pd.DataFrame] = None        # raw imported data
        self._work: Optional[pd.DataFrame] = None      # working copy for transforms
        self._current_file: Optional[str] = None

        self._build()
        self._refresh_controls()

    # -- build ------------------------------------------------------------
    def _build(self) -> None:
        import_btn = QPushButton("Import Dataset…")
        import_btn.setObjectName("Primary")
        import_btn.clicked.connect(self._import)
        self.add_toolbar_widget(import_btn)

        self.dataset_label = QLabel("No dataset loaded")
        self.dataset_label.setObjectName("MutedLabel")
        self.add_toolbar_widget(self.dataset_label)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_preview(), "Preview")
        self.tabs.addTab(self._build_filter(), "Filter / Transform")
        self.tabs.addTab(self._build_stats(), "Statistics")
        self.tabs.addTab(self._build_visual(), "Visualize")
        self.add_body_widget(self.tabs, 1)

    def _build_preview(self) -> QWidget:
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        self.preview_table = QTableWidget(0, 0)
        self.preview_table.verticalHeader().setVisible(False)
        self.preview_table.setEditTriggers(QTableWidget.NoEditTriggers)
        lay.addWidget(self.preview_table, 1)
        self.summary_label = QLabel("")
        self.summary_label.setObjectName("MutedLabel")
        self.summary_label.setWordWrap(True)
        lay.addWidget(self.summary_label)
        return container

    def _build_filter(self) -> QWidget:
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        # Filter row
        fbox = QGroupBox("Filter rows")
        ff = QFormLayout(fbox)
        self.filter_col = QComboBox()
        self.filter_op = QComboBox()
        self.filter_op.addItems(["==", "!=", ">", "<", ">=", "<=", "contains"])
        self.filter_val = QLineEdit()
        self.filter_val.setPlaceholderText("value")
        ff.addRow("Column", self.filter_col)
        ff.addRow("Operator", self.filter_op)
        ff.addRow("Value", self.filter_val)
        apply_btn = QPushButton("Apply filter")
        apply_btn.clicked.connect(self._apply_filter)
        reset_btn = QPushButton("Reset to raw")
        reset_btn.clicked.connect(self._reset_filter)
        btnrow = QHBoxLayout()
        btnrow.addWidget(apply_btn)
        btnrow.addWidget(reset_btn)
        btnrow.addStretch(1)
        ff.addRow(btnrow)
        lay.addWidget(fbox)

        # Missing values
        mbox = QGroupBox("Missing values")
        mf = QFormLayout(mbox)
        self.missing_strategy = QComboBox()
        self.missing_strategy.addItems(["drop", "mean", "median", "zero"])
        mf.addRow("Strategy", self.missing_strategy)
        mf_btn = QPushButton("Apply")
        mf_btn.clicked.connect(self._apply_missing)
        mf.addRow(mf_btn)
        lay.addWidget(mbox)

        self.status_label = QLabel("Rows: —")
        self.status_label.setObjectName("MutedLabel")
        lay.addWidget(self.status_label)
        lay.addStretch(1)
        return container

    def _build_stats(self) -> QWidget:
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        form = QFormLayout()
        self.stats_col = QComboBox()
        form.addRow("Column", self.stats_col)
        desc_btn = QPushButton("Descriptive statistics")
        desc_btn.clicked.connect(self._descriptive)
        form.addRow(desc_btn)
        lay.addLayout(form)

        self.stats_output = QTextEdit()
        self.stats_output.setReadOnly(True)
        self.stats_output.setStyleSheet("font-family: Consolas, monospace;")
        lay.addWidget(self.stats_output, 1)

        # Regression controls
        rbox = QGroupBox("Linear regression")
        rf = QFormLayout(rbox)
        self.reg_x = QComboBox()
        self.reg_y = QComboBox()
        rf.addRow("X column", self.reg_x)
        rf.addRow("Y column", self.reg_y)
        reg_btn = QPushButton("Regress")
        reg_btn.clicked.connect(self._regress)
        rf.addRow(reg_btn)
        lay.addWidget(rbox)
        return container

    def _build_visual(self) -> QWidget:
        container = QWidget()
        lay = QHBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        controls = QVBoxLayout()
        box = QGroupBox("Chart")
        bf = QFormLayout(box)
        self.chart_type = QComboBox()
        self.chart_type.addItems(["Line", "Scatter", "Bar", "Histogram"])
        self.chart_x = QComboBox()
        self.chart_y = QComboBox()
        self.chart_bins = QSpinBox()
        self.chart_bins.setRange(5, 100)
        self.chart_bins.setValue(20)
        bf.addRow("Type", self.chart_type)
        bf.addRow("X / category", self.chart_x)
        bf.addRow("Y / value", self.chart_y)
        bf.addRow("Bins (hist)", self.chart_bins)
        plot_btn = QPushButton("Plot")
        plot_btn.setObjectName("Primary")
        plot_btn.clicked.connect(self._plot)
        bf.addRow(plot_btn)
        controls.addWidget(box)

        export_btn = QPushButton("Export processed data (.csv)")
        export_btn.clicked.connect(self._export_csv)
        controls.addWidget(export_btn)
        controls.addStretch(1)
        lay.addLayout(controls, 0)

        self.chart = ChartWidget()
        lay.addWidget(self.chart, 1)
        return container

    # -- data loading -----------------------------------------------------
    def _import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import dataset", "",
            "Data files (*.csv *.json *.xlsx *.xls *.parquet *.h5 *.hdf5 *.txt);;All files (*)")
        if not path:
            return
        try:
            df = dm.import_dataset(path)
        except dm.ImportError_ as exc:
            QMessageBox.warning(self, "Import failed", str(exc))
            return
        self._df = df
        self._work = df.copy()
        self._current_file = path
        self.dataset_label.setText(f"Loaded: {path.split(chr(92))[-1].split('/')[-1]}")
        # Register with DuckDB (lazy; ignore failure).
        self._register_duckdb(df)
        self._refresh_controls()
        self._render_preview()
        self._update_status()

    def _register_duckdb(self, df: pd.DataFrame) -> None:
        try:
            self.ctx.duckdb.open()
            self.ctx.duckdb.register_dataframe("dataset", df)
        except Exception:  # noqa: BLE001
            pass

    def _refresh_controls(self) -> None:
        # Populate column combos.
        for combo in (self.filter_col, self.stats_col, self.reg_x, self.reg_y,
                      self.chart_x, self.chart_y):
            combo.blockSignals(True)
            combo.clear()
        if self._work is not None:
            cols = list(self._work.columns)
            num_cols = dm.numeric_columns(self._work)
            for combo in (self.filter_col, self.stats_col, self.chart_x, self.chart_y):
                combo.addItems(cols)
            for combo in (self.reg_x, self.reg_y):
                combo.addItems(num_cols)
        for combo in (self.filter_col, self.stats_col, self.reg_x, self.reg_y,
                      self.chart_x, self.chart_y):
            combo.blockSignals(False)

    # -- preview ----------------------------------------------------------
    def _render_preview(self) -> None:
        if self._work is None:
            return
        df = self._work
        preview = df.head(50)
        self.preview_table.setRowCount(0)
        self.preview_table.setColumnCount(len(preview.columns))
        self.preview_table.setHorizontalHeaderLabels([str(c) for c in preview.columns])
        for r in range(len(preview)):
            self.preview_table.insertRow(r)
            for c in range(len(preview.columns)):
                val = preview.iloc[r, c]
                self.preview_table.setItem(r, c, QTableWidgetItem(str(val)))
        summary = dm.dataset_summary(df)
        self.summary_label.setText(
            f"{summary['rows']} rows × {summary['columns']} columns  ·  "
            f"{len(dm.numeric_columns(df))} numeric, "
            f"{len(dm.categorical_columns(df))} categorical"
        )

    def _update_status(self) -> None:
        if self._work is not None:
            self.status_label.setText(
                f"Rows: {len(self._work)}  ·  Columns: {len(self._work.columns)}"
            )
        else:
            self.status_label.setText("Rows: —")

    # -- filter / transform ----------------------------------------------
    def _apply_filter(self) -> None:
        if self._work is None:
            return
        col = self.filter_col.currentText()
        op = self.filter_op.currentText()
        val = self.filter_val.text().strip()
        if not col or not val:
            return
        try:
            # Try numeric compare if value looks numeric and op is numeric.
            if op in (">", "<", ">=", "<="):
                val_parsed = float(val)
            elif op in ("==", "!="):
                # keep as string but try numeric
                try:
                    val_parsed = float(val)
                except ValueError:
                    val_parsed = val
            else:
                val_parsed = val
            self._work = stats.filter_dataframe(self._work, col, op, val_parsed)
            self._render_preview()
            self._update_status()
            self._refresh_controls()
        except (ValueError, KeyError) as exc:
            QMessageBox.warning(self, "Filter error", str(exc))

    def _reset_filter(self) -> None:
        if self._df is not None:
            self._work = self._df.copy()
            self._render_preview()
            self._update_status()
            self._refresh_controls()

    def _apply_missing(self) -> None:
        if self._work is None:
            return
        strat = self.missing_strategy.currentText()
        try:
            if strat == "drop":
                self._work = stats.drop_missing(self._work)
            else:
                self._work = stats.fill_missing(self._work, strat)
            self._render_preview()
            self._update_status()
            self._refresh_controls()
        except ValueError as exc:
            QMessageBox.warning(self, "Error", str(exc))

    # -- statistics -------------------------------------------------------
    def _descriptive(self) -> None:
        if self._work is None:
            return
        col = self.stats_col.currentText()
        if not col:
            return
        try:
            s = stats.descriptive_stats(self._work, col)
        except (ValueError, KeyError) as exc:
            self.stats_output.setPlainText(f"Error: {exc}")
            return
        if s.get("count", 0) == 0:
            self.stats_output.setPlainText(f"Column '{col}' has no numeric data.")
            return
        lines = [f"Descriptive statistics — {col}", ""]
        for k, v in s.items():
            if isinstance(v, float):
                lines.append(f"  {k:12s}: {v:.6g}")
            else:
                lines.append(f"  {k:12s}: {v}")
        # Also show correlation matrix if >1 numeric column.
        num_cols = dm.numeric_columns(self._work)
        if len(num_cols) >= 2:
            lines.append("\nCorrelation matrix:")
            corr = stats.correlation_matrix(self._work)
            lines.append(corr.round(3).to_string())
        self.stats_output.setPlainText("\n".join(lines))

    def _regress(self) -> None:
        if self._work is None:
            return
        x = self.reg_x.currentText()
        y = self.reg_y.currentText()
        if not x or not y:
            return
        try:
            res = stats.linear_regression(self._work, x, y)
        except (ValueError, KeyError) as exc:
            self.stats_output.setPlainText(f"Regression error: {exc}")
            return
        lines = [
            f"Linear regression: y = {res['slope']:.6g}·x + {res['intercept']:.6g}",
            f"  R² = {res['r_squared']:.6f}",
            f"  slope SE = {res['slope_se']:.6g}",
            f"  intercept SE = {res['intercept_se']:.6g}",
            f"  n = {res['n']}",
            "",
            "Plotting regression on Visualize tab…",
        ]
        self.stats_output.setPlainText("\n".join(lines))
        # Draw regression chart on the visual tab.
        order = np.argsort(res["x"])
        self.chart.plot_series(
            [
                (res["x"][order], res["y"][order], "data", ACCENT),
                (res["x"][order], res["slope"] * res["x"][order] + res["intercept"],
                 "fit", ACCENT_BLUE),
            ],
            x, y, f"Regression (R²={res['r_squared']:.3f})")
        self.tabs.setCurrentWidget(self.chart.parentWidget())

    # -- visualization ----------------------------------------------------
    def _plot(self) -> None:
        if self._work is None:
            return
        ctype = self.chart_type.currentText()
        xcol = self.chart_x.currentText()
        ycol = self.chart_y.currentText()
        try:
            if ctype == "Histogram":
                counts, edges = stats.histogram_data(self._work, xcol, self.chart_bins.value())
                centers = (edges[:-1] + edges[1]) / 2
                self.chart.plot_xy(centers, counts, xcol, "count",
                                   f"Histogram of {xcol}", ACCENT)
                return
            if ctype in ("Line", "Scatter", "Bar"):
                if not xcol or not ycol:
                    return
                xv = self._work[xcol]
                yv = self._work[ycol]
                # numeric sort for line/scatter
                if ctype == "Bar":
                    # categorical bar
                    agg = self._work.groupby(xcol)[ycol].mean().reset_index()
                    self.chart.plot_xy(agg[xcol].astype(str), agg[ycol],
                                       xcol, ycol, f"Bar of {ycol} by {xcol}", ACCENT)
                else:
                    mask = xv.notna() & yv.notna()
                    xs = pd.to_numeric(xv[mask], errors="coerce")
                    ys = pd.to_numeric(yv[mask], errors="coerce")
                    m2 = xs.notna() & ys.notna()
                    xs, ys = xs[m2], ys[m2]
                    if ctype == "Line":
                        order = xs.argsort()
                        self.chart.plot_xy(xs[order], ys[order], xcol, ycol,
                                           f"{ycol} vs {xcol}", ACCENT)
                    else:  # Scatter
                        self.chart.scatter(xs, ys, xcol, ycol,
                                           f"Scatter: {ycol} vs {xcol}", ACCENT)
        except (ValueError, KeyError, TypeError) as exc:
            QMessageBox.warning(self, "Plot error", str(exc))

    def _export_csv(self) -> None:
        if self._work is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export processed data", "processed.csv", "CSV (*.csv)")
        if path:
            try:
                self._work.to_csv(path, index=False)
            except OSError as exc:
                QMessageBox.warning(self, "Export failed", str(exc))

    def refresh(self) -> None:
        self._refresh_controls()