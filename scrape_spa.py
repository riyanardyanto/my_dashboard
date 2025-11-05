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
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = self.scrape_spa()

    def scrape_spa(self) -> pd.DataFrame:
        list_df = pd.read_html(self.file_path, flavor="lxml")
        df = list_df[3]
        return df

    def get_split_indexes(self) -> list:
        return [i for i in range(len(self.df)) if self.df[14][i] == "i"]

    def get_splitted_dataframes(self) -> list[pd.DataFrame]:
        split_indexes = self.get_split_indexes()
        return split_dataframe(self.df, split_indexes)
