"""Dashboard orchestration helpers."""

from __future__ import annotations

from typing import Callable, Iterable, Optional, Sequence

import httpx
import pandas as pd

from ..services.achievement_service import (
    compute_row_updates,
    fetch_actual_metrics,
    load_target_shift,
)
from ..services.card_service import append_cards_to_csv, build_card_rows
from ..services.spa_service import SPADataProcessor
from ..utils.constants import HEADERS, NTLM_AUTH


class ControllerError(RuntimeError):
    """Raised when the controller cannot complete a request."""


class DashboardController:
    """Coordinates service calls on behalf of the UI layer."""

    def __init__(
        self,
        *,
        spa_source: str = "spa.html",
        http_client_factory: Optional[Callable[[], httpx.AsyncClient]] = None,
        spa_scraper_cls: type[SPADataProcessor] = SPADataProcessor,
        target_loader: Callable[[str, str, int], pd.Series] = load_target_shift,
        actual_fetcher: Callable[
            [pd.DataFrame | dict[str, object], Sequence[str]],
            tuple[list[str], dict[str, object]],
        ] = fetch_actual_metrics,
        row_updater: Callable[
            [Iterable, Sequence[str], Sequence[str]], list[tuple[object, tuple]]
        ] = compute_row_updates,
        card_row_builder: Callable[
            [Iterable[dict], str, str, str, str], list[dict[str, str]]
        ] = build_card_rows,
        card_persister: Callable[[list[dict[str, str]]], object] = append_cards_to_csv,
        request_headers: Optional[dict[str, str]] = None,
        request_auth=NTLM_AUTH,
    ) -> None:
        self._spa_source = spa_source
        self._spa_scraper_cls = spa_scraper_cls
        self._load_target_shift = target_loader
        self._fetch_actual_metrics = actual_fetcher
        self._compute_row_updates = row_updater
        self._build_card_rows = card_row_builder
        self._append_cards_to_csv = card_persister

        self._headers = request_headers or HEADERS
        self._auth = request_auth
        self._client_factory = http_client_factory or (
            lambda: httpx.AsyncClient(timeout=30)
        )

        self._current_scraper = self._make_scraper(spa_source)
        self._processed_cache: dict[str, pd.DataFrame] | None = None
        self._cached_url: str | None = None

    # ------------------------------------------------------------------
    # Internal helpers -------------------------------------------------
    # ------------------------------------------------------------------
    def _make_scraper(self, source: str, *, is_html: bool = False) -> SPADataProcessor:
        return self._spa_scraper_cls(
            source,
            is_html=is_html,
            headers=self._headers,
            auth=self._auth,
        )

    async def _ensure_processed(
        self, *, client: httpx.AsyncClient | None = None, force: bool = False
    ) -> dict[str, pd.DataFrame]:
        if self._processed_cache is not None and not force:
            return self._processed_cache

        processed = await self._current_scraper.process(client=client, force=force)
        self._processed_cache = processed
        self._cached_url = None
        return processed

    def _cache_remote_data(
        self, processed: dict[str, pd.DataFrame], url: str
    ) -> dict[str, pd.DataFrame]:
        self._processed_cache = processed
        self._cached_url = url
        return processed

    # ------------------------------------------------------------------
    # SPA data ---------------------------------------------------------
    # ------------------------------------------------------------------

    async def load_local_issue_dataframe(self) -> pd.DataFrame:
        processed = await self._ensure_processed()
        return processed.get("stops_reason", pd.DataFrame())

    async def load_local_data_losses(self) -> pd.DataFrame:
        processed = await self._ensure_processed()
        return processed.get("data_losses", pd.DataFrame())

    async def load_stop_reason_dataframe(
        self, url: str, *, use_cache: bool = False
    ) -> pd.DataFrame:
        processed = await self.fetch_remote_issue_data(url, use_cache=use_cache)
        return processed.get("stops_reason", pd.DataFrame())

    async def load_data_losses_dataframe(
        self, url: str, *, use_cache: bool = False
    ) -> pd.DataFrame:
        processed = await self.fetch_remote_issue_data(url, use_cache=use_cache)
        return processed.get("data_losses", pd.DataFrame())

    async def fetch_remote_issue_data(
        self, url: str, *, use_cache: bool = False
    ) -> dict[str, pd.DataFrame]:
        """Fetch SPA data from a remote endpoint and cache the scraper."""

        if use_cache and self._processed_cache is not None and self._cached_url == url:
            return self._processed_cache

        async with self._client_factory() as client:
            response = await client.get(
                url,
                follow_redirects=True,
                headers=self._headers,
                auth=self._auth,
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ControllerError(
                f"Error Code {response.status_code}: {response.text}"
            ) from exc

        self._current_scraper = self._make_scraper(response.text, is_html=True)
        processed = await self._current_scraper.process()
        return self._cache_remote_data(processed, url)

    def get_cached_processed_data(self) -> dict[str, pd.DataFrame] | None:
        return self._processed_cache

    def clear_cache(self) -> None:
        self._processed_cache = None
        self._cached_url = None

    # ------------------------------------------------------------------
    # Achievement ------------------------------------------------------
    # ------------------------------------------------------------------
    async def compute_achievement_updates(
        self,
        tablerows: Iterable,
        metric_names: Sequence[str],
        *,
        lu_value: str,
        func_location: str,
        shift_number: int,
        data_url: str,
    ) -> tuple[list[tuple[object, tuple]], dict[str, object]]:
        """Determine table updates and actual metrics for the given shift."""

        target_shift = self._load_target_shift(lu_value, func_location, shift_number)
        data_losses = await self.load_data_losses_dataframe(data_url, use_cache=True)
        actual_values, actual_data = self._fetch_actual_metrics(
            data_losses, metric_names
        )

        updates = self._compute_row_updates(
            tablerows,
            target_shift.tolist(),
            actual_values,
        )

        return updates, actual_data

    # ------------------------------------------------------------------
    # Cards ------------------------------------------------------------
    # ------------------------------------------------------------------
    def save_cards(
        self,
        cards: Iterable[dict],
        username: str = "",
        lu: str = "",
        tanggal: str = "",
        shift: str = "",
    ) -> Optional[object]:
        """Persist card data and return the created file path."""

        rows = self._build_card_rows(cards, username, lu, tanggal, shift)
        if not rows:
            return None
        return self._append_cards_to_csv(rows)

    # ------------------------------------------------------------------
    # Utilities --------------------------------------------------------
    # ------------------------------------------------------------------
    @property
    def current_scraper(self) -> SPADataProcessor:
        return self._current_scraper
