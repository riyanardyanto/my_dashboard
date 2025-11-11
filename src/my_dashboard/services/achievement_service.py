"""Business logic for achievement target updates."""

from __future__ import annotations

from typing import Iterable, Mapping, Sequence

import pandas as pd

from ..utils.csvhandle import get_targets_file_path


def load_target_shift(
    lu_value: str, func_location: str, shift_number: int
) -> pd.Series:
    target_path = get_targets_file_path(
        lu_value.strip("LU"), func_location=func_location
    )
    target_df = pd.read_csv(target_path)
    shift_column = f"Shift {shift_number}"
    if shift_column not in target_df.columns:
        raise KeyError(f"Kolom {shift_column!r} tidak ditemukan pada file target.")
    return target_df[shift_column].astype(str).str.replace("%", "")


def _normalize_metric_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value)


def fetch_actual_metrics(
    data_losses: pd.DataFrame | Mapping[str, object], metric_order: Sequence[str]
) -> tuple[list[str], dict[str, object]]:
    if isinstance(data_losses, pd.DataFrame):
        if data_losses.empty:
            data_actual: dict[str, object] = {}
        else:
            data_actual = data_losses.iloc[0].to_dict()
    else:
        data_actual = dict(data_losses)

    values = [
        _normalize_metric_value(data_actual.get(metric)) for metric in metric_order
    ]
    return values, data_actual


def compute_row_updates(
    tablerows: Iterable,
    target_shift: Sequence[str],
    actual_values: Sequence[str],
) -> list[tuple[object, tuple]]:
    updates: list[tuple[object, tuple]] = []
    for idx, row in enumerate(tablerows):
        current_values = list(row.values)
        changed = False

        if len(current_values) >= 2 and idx < len(target_shift):
            new_target = target_shift[idx]
            if current_values[1] != new_target:
                current_values[1] = new_target
                changed = True

        if len(current_values) >= 3 and idx < len(actual_values):
            new_actual = actual_values[idx]
            if new_actual is not None and current_values[2] != new_actual:
                current_values[2] = new_actual
                changed = True

        if changed:
            updates.append((row, tuple(current_values)))

    return updates
