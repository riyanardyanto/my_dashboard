"""SPA data extraction utilities."""
from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


class SpaScraper:
    """Extract structured data from the SPA HTML export."""

    def __init__(self, source: str, *, is_html: Optional[bool] = None):
        if is_html is None:
            self._is_html = not Path(source).is_file()
        else:
            self._is_html = is_html

        self._source = source
        self._df = self._read_source()
        self._splitted_dfs: Optional[list[pd.DataFrame]] = None

    @property
    def dataframe(self) -> pd.DataFrame:
        return self._df

    def _read_source(self) -> pd.DataFrame:
        data_source = StringIO(self._source) if self._is_html else self._source
        list_df = pd.read_html(data_source, flavor="lxml")
        return list_df[3]

    def get_split_indexes(self) -> list[int]:
        return [i for i in range(len(self._df)) if self._df[14][i] == "i"]

    def get_splitted_dataframes(self, refresh: bool = False) -> list[pd.DataFrame]:
        if self._splitted_dfs is not None and not refresh:
            return self._splitted_dfs

        split_indexes = self.get_split_indexes()
        self._splitted_dfs = split_dataframe(self._df, split_indexes)
        return self._splitted_dfs

    def get_actual_data_metric(self) -> dict[str, object]:
        splitted_dfs = self.get_splitted_dataframes()
        metric_map = {
            "STOP": (7, "Stops", 0),
            "MTBF": (7, "MTBF", 0),
            "PR": (0, "Uptime Loss", 4),
            "NATR": (4, "Uptime Loss", 2),
            "PDT": (6, "Uptime Loss", 0),
            "UPDT": (7, "Uptime Loss", 0),
            "RANGE": (0, "nan_9", 0),
        }

        actual_data: dict[str, object] = {}
        for metric, (df_index, column, row_index) in metric_map.items():
            try:
                actual_data[metric] = splitted_dfs[df_index][column].iat[row_index]
            except (IndexError, KeyError):
                actual_data[metric] = None
        return actual_data

    def get_issue_dataframe(self) -> pd.DataFrame:
        try:
            issue_df = self.get_splitted_dataframes()[3].copy()
            issue_df = issue_df.loc[
                :, ["Line performance Details", "nan_9", "Stops", "Downtime"]
            ].copy()
            issue_df.columns = ["Line", "Issue", "Stops", "Downtime"]
            issue_df.loc[:, "Line"] = issue_df["Line"].apply(_clean_line).ffill()
            return issue_df
        except IndexError:
            return pd.DataFrame()


def scrape_spa(source: str) -> pd.DataFrame:
    return SpaScraper(source).dataframe


def split_dataframe(df: pd.DataFrame, split_indexes: list[int]) -> list[pd.DataFrame]:
    new_tables: list[pd.DataFrame] = []

    for idx in range(len(split_indexes)):
        header: list[str] = df.iloc[split_indexes[idx]].tolist()
        new_header: list[str] = []

        try:
            for index, col in enumerate(header):
                if "nan" in str(col).lower() or col == header[index - 1]:
                    new_header.append(f"{col}_{index}")
                else:
                    new_header.append(str(col))
            header = new_header
        except Exception:  # pragma: no cover - defensive
            continue

        start_idx = split_indexes[idx] + 1
        end_idx = split_indexes[idx + 1] if idx + 1 < len(split_indexes) else len(df)
        sub_df = df.iloc[start_idx:end_idx].reset_index(drop=True)
        sub_df.columns = header

        new_tables.append(sub_df)

    return new_tables


def _clean_line(value):
    if isinstance(value, str):
        new_value = value.strip("&nbsp;")
        if new_value == "":
            new_value = np.nan
        return new_value
    return value
