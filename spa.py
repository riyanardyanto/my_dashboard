from io import StringIO
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import tabulate


def _normalize_cell(value: object) -> object:
    if isinstance(value, str):
        stripped = value.strip()
        lowered = stripped.lower()
        if not stripped or lowered == "nan":
            return np.nan
    return value


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
        sub_df: pd.DataFrame = df.iloc[start_idx:end_idx].reset_index(drop=True)
        sub_df.columns = header

        # Normalize placeholder values so downstream processing sees real NaNs
        sub_df = sub_df.applymap(_normalize_cell).infer_objects(copy=False)
        new_tables.append(sub_df.dropna(axis=1, how="all").reset_index(drop=True))

    return new_tables


if __name__ == "__main__":
    df = scrape_spa()
    split_indexes = [i for i in range(len(df)) if df[14][i] == "i"]
    df_tables = split_dataframe(df, split_indexes)

    with open("spa.txt", "w", encoding="utf-8") as f:
        for i, df in enumerate(df_tables):
            f.write(
                f'Index: {i}\n{tabulate.tabulate(df, headers="keys", tablefmt="psql")} \n'
            )
