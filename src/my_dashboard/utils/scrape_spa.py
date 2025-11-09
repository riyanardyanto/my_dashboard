from io import StringIO
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


def scrape_spa() -> pd.DataFrame:
    list_df = pd.read_html("spa.html", flavor="lxml")
    df = list_df[3]
    return df


def split_dataframe(df: pd.DataFrame, split_indexes: list[int]) -> list[pd.DataFrame]:
    """
    Split a pandas DataFrame into multiple smaller DataFrames based on the given split indexes.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to split.
    split_indexes : list[int]
        The list of indexes where the DataFrame should be split.

    Returns
    -------
    list[pd.DataFrame]
        A list of DataFrames, each containing a subset of the original DataFrame.
    """
    new_tables: list[pd.DataFrame] = []

    for idx in range(len(split_indexes)):
        header: list[str] = df.iloc[split_indexes[idx]].tolist()
        new_header: list[str] = []

        try:
            for index, col in enumerate(header):
                if "nan" in str(col).lower() or col == header[index - 1]:
                    new_header.append(str(col) + "_" + str(index))
                else:
                    new_header.append(str(col))
            header = new_header
        except Exception:
            continue

        start_idx = split_indexes[idx] + 1
        end_idx = split_indexes[idx + 1] if idx + 1 < len(split_indexes) else len(df)
        sub_df = df.iloc[start_idx:end_idx].reset_index(drop=True)
        sub_df.columns = header

        new_tables.append(sub_df)

    return new_tables


class SpaScraper:
    def __init__(self, source: str, *, is_html: Optional[bool] = None):
        self.source = source
        if is_html is None:
            self._is_html = not Path(source).is_file()
        else:
            self._is_html = is_html

        self.df = self.scrape_spa()
        self._splitted_dfs: Optional[list[pd.DataFrame]] = None

    def scrape_spa(self) -> pd.DataFrame:
        data_source = StringIO(self.source) if self._is_html else self.source
        list_df = pd.read_html(data_source, flavor="lxml")
        df = list_df[3]
        return df

    def get_split_indexes(self) -> list:
        return [i for i in range(len(self.df)) if self.df[14][i] == "i"]

    def get_splitted_dataframes(self, refresh: bool = False) -> list[pd.DataFrame]:
        if self._splitted_dfs is not None and not refresh:
            return self._splitted_dfs

        split_indexes = self.get_split_indexes()
        self._splitted_dfs = split_dataframe(self.df, split_indexes)
        return self._splitted_dfs

    def get_actual_data_metric(self):
        splitted_dfs = self.get_splitted_dataframes()

        # Map every metric to its (dataframe index, column name, row index)
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
            _issue_df = self.get_splitted_dataframes()[3].copy()
            _issue_df = _issue_df.loc[
                :, ["Line performance Details", "nan_9", "Stops", "Downtime"]
            ].copy()
            _issue_df.columns = ["Line", "Issue", "Stops", "Downtime"]

            def _clean_line(value):
                if isinstance(value, str):
                    new_value = value.strip("&nbsp;")
                    if new_value == "":
                        new_value = np.nan
                    return new_value
                return value

            _issue_df.loc[:, "Line"] = _issue_df["Line"].apply(_clean_line).ffill()

            issue_df = _issue_df
            return issue_df
        except IndexError:
            return pd.DataFrame()  # Return empty DataFrame if not found


if __name__ == "__main__":
    spa_scraper = SpaScraper("spa.html")
    actual = spa_scraper.get_actual_data_metric()

    print(actual)
