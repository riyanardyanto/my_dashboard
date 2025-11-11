import asyncio
from io import StringIO

import httpx
import numpy as np
import pandas as pd
from tabulate import tabulate

from ..utils.constants import HEADERS, NTLM_AUTH


class SPADataFetcher:
    """Handles fetching data from URLs."""

    def __init__(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        auth=None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.url = url
        self.raw_html: str | None = None
        self._headers = headers or HEADERS
        self._auth = auth or NTLM_AUTH
        self._client = client

    async def fetch(self, client: httpx.AsyncClient | None = None) -> str:
        """Fetch HTML content from the URL asynchronously."""

        if self.raw_html is not None:
            return self.raw_html

        active_client = client or self._client
        should_close = False
        if active_client is None:
            active_client = httpx.AsyncClient(timeout=30)
            should_close = True

        try:
            response = await active_client.get(
                self.url,
                headers=self._headers,
                auth=self._auth,
                follow_redirects=True,
            )
            response.raise_for_status()
        finally:
            if should_close:
                await active_client.aclose()

        self.raw_html = response.text
        return self.raw_html


class HTMLTableExtractor:
    """Extracts and processes tables from HTML content."""

    def __init__(self, html_content: str):
        self.html_content = html_content
        self.tables: list[pd.DataFrame] = []

    def extract(self) -> list[pd.DataFrame]:
        """Extract tables from HTML and replace empty strings with NaN."""
        tables = pd.read_html(StringIO(self.html_content))
        if not tables:
            raise ValueError("No tables found in the HTML content.")

        # Replace empty strings with np.nan in all tables
        self.tables = [table.replace("", np.nan) for table in tables]
        return self.tables


class DataFrameCleaner:
    """Handles DataFrame cleaning operations."""

    @staticmethod
    def remove_duplicate_rows(df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove rows where column '1' has the same value as the previous row
        AND column '2' is NaN.
        """
        # Remove row that all columns are NaN
        df = df.dropna(how="all").reset_index(drop=True)

        # Create a mask for rows to keep
        rows_to_keep = []

        for idx in range(len(df)):
            if idx == 0:
                # Always keep the first row
                rows_to_keep.append(True)
            else:
                # Check if column 1 value equals previous row's column 1 value
                # AND column 2 is NaN
                col1_same = df.iloc[idx][1] == df.iloc[idx - 1][1]
                col2_is_nan = pd.isna(df.iloc[idx][2])

                # Remove row only if BOTH conditions are true
                if col1_same and col2_is_nan:
                    rows_to_keep.append(False)
                else:
                    rows_to_keep.append(True)

        # Return filtered dataframe
        return df[rows_to_keep].reset_index(drop=True)


class DataFrameSplitter:
    """Splits DataFrames based on specific column values."""

    def __init__(self, tables: list[pd.DataFrame]):
        self.tables = tables
        self.sections: list[pd.DataFrame] = []

    def split_by_column_14(self) -> list[pd.DataFrame]:
        """Split the fourth table by rows where column 14 has value 'i'."""
        # Select the fourth table as main datatable
        datatable = self.tables[3]

        # Remove duplicate rows
        datatable = DataFrameCleaner.remove_duplicate_rows(datatable)

        # Find indices where column 14 has value "i"
        split_indices = datatable[datatable[14] == "i"].index.tolist()

        # Split the dataframe into sections
        self.sections = []
        for i, start_idx in enumerate(split_indices):
            # Determine end index for current section
            if i < len(split_indices) - 1:
                end_idx = split_indices[i + 1]
            else:
                end_idx = len(datatable)

            # Extract section (including the header row with "i")
            section = datatable.iloc[start_idx:end_idx].copy()
            self.sections.append(section)

        return self.sections


class StopReasonTableProcessor:
    """Processes stop reason table from splitted tables."""

    def __init__(self, splitted_tables: list[pd.DataFrame]):
        self.splitted_tables = splitted_tables

    def process(self) -> pd.DataFrame:
        """Get and process the stops reason table from splitted tables."""
        stops_reason = (
            self.splitted_tables[3]
            .dropna(how="all")  # Remove rows where all values are NaN
            .loc[lambda df: df[4].notna()][  # Keep only rows where column 4 is not NaN
                [1, 9, 2, 4]
            ]  # Select specific columns
            .iloc[1:]  # Skip first row (header)
            .reset_index(drop=True)
        )

        # Rename columns
        stops_reason.columns = ["Line", "Reason", "Stops", "Downtime"]

        # Fill NaN in 'Line' column with previous value and extract first part
        stops_reason["Line"] = (
            stops_reason["Line"].ffill().str.split(" - ", n=1, expand=True)[0]
        )

        return stops_reason


class DataLossesTableProcessor:
    """Processes data losses table from splitted tables."""

    def __init__(self, splitted_tables: list[pd.DataFrame]):
        self.splitted_tables = splitted_tables

    def process(self) -> pd.DataFrame:
        """Extract and combine data losses metrics from splitted tables."""
        data = {
            "RANGE": self.splitted_tables[0][9].iloc[1],
            "STOP": self.splitted_tables[7][2].iloc[1],
            "PR": self.splitted_tables[0][5].iloc[5],
            "MTBF": self.splitted_tables[0][7].iloc[5],
            "UPDT": self.splitted_tables[7][5].iloc[1],
            "PDT": self.splitted_tables[6][5].iloc[1],
            "NATR": self.splitted_tables[4][5].iloc[3],
        }

        return pd.DataFrame([data])


class SPADataProcessor:
    """Main processor that orchestrates all data processing operations."""

    def __init__(
        self,
        source: str,
        *,
        is_html: bool = False,
        headers: dict[str, str] | None = None,
        auth=None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._source = source
        self._is_html = is_html
        self._headers = headers or HEADERS
        self._auth = auth or NTLM_AUTH
        self._client = client
        self.fetcher: SPADataFetcher | None = (
            None
            if is_html
            else SPADataFetcher(
                source,
                headers=self._headers,
                auth=self._auth,
                client=client,
            )
        )
        self.raw_html: str | None = source if is_html else None
        self.tables: list[pd.DataFrame] = []
        self.splitted_tables: list[pd.DataFrame] = []
        self.processed_data: dict[str, pd.DataFrame] = {}

    async def process(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        force: bool = False,
    ) -> dict[str, pd.DataFrame]:
        """Execute the full data processing pipeline asynchronously."""

        if self.processed_data and not force:
            return self.processed_data

        if self.raw_html is None:
            if self.fetcher is None:
                self.fetcher = SPADataFetcher(
                    self._source,
                    headers=self._headers,
                    auth=self._auth,
                    client=self._client,
                )
            self.raw_html = await self.fetcher.fetch(client=client)

        extractor = HTMLTableExtractor(self.raw_html)
        self.tables = extractor.extract()

        splitter = DataFrameSplitter(self.tables)
        self.splitted_tables = splitter.split_by_column_14()

        self.processed_data = {
            "data_losses": DataLossesTableProcessor(self.splitted_tables).process(),
            "stops_reason": StopReasonTableProcessor(self.splitted_tables).process(),
        }

        return self.processed_data

    async def save_results(self, output_format: str = "psql") -> None:
        """Save processed data to files after ensuring processing."""

        await self.process()

        for key, df in self.processed_data.items():
            filename = f"{key}.txt"
            with open(filename, "w", encoding="utf-8") as file_handle:
                file_handle.write(
                    tabulate(
                        df,
                        headers="keys",
                        tablefmt=output_format,
                        showindex=False,
                    )
                )

    def display_results(self) -> None:
        """Display processed data to console."""

        if not self.processed_data:
            raise RuntimeError(
                "Data belum diproses. Panggil 'await process()' sebelum tampilkan hasil."
            )

        for key, df in self.processed_data.items():
            print(f"\n=== {key.upper()} ===")
            print(tabulate(df, headers="keys", tablefmt="psql", showindex=False))


async def main() -> None:
    processor = SPADataProcessor("http://127.0.0.1:5501/assets/spa1.html")
    await processor.process()
    processor.display_results()
    await processor.save_results()


if __name__ == "__main__":
    asyncio.run(main())
