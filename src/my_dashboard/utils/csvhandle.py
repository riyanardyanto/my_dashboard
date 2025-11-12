from pathlib import Path

import pandas as pd

from .helpers import get_script_folder

columns = ["Shift 1", "Shift 2", "Shift 3"]
data = [
    ("3", "3", "3"),
    ("65.0%", "69.2%", "77.5%"),
    ("111", "117", "131"),
    ("4.9%", "4.9%", "4.9%"),
    ("26.0%", "21.8%", "13.5%"),
    ("4.1%", "4.1%", "4.1%"),
]


def get_targets_file_path(lu, func_location: str = None):
    script_folder = Path(get_script_folder())
    target_folder = script_folder / "Target"
    target_folder.mkdir(parents=True, exist_ok=True)

    filename = target_folder / f"target_{func_location.lower()}_{lu}.csv"
    if not filename.exists():
        df = pd.DataFrame(data, columns=columns)
        df.to_csv(filename, index=False)

    return str(filename)


def load_targets_df(filename=None):
    """Memuat pengaturan dari file CSV"""

    return pd.read_csv(filename)


def get_cards_file_path() -> str:
    script_folder = Path(get_script_folder())
    data_folder = script_folder / "data"
    data_folder.mkdir(parents=True, exist_ok=True)

    filename = data_folder / "issue_cards.csv"
    if not filename.exists():
        pd.DataFrame(
            columns=[
                "card_id",
                "issue",
                "detail",
                "action",
                "saved_at",
                "user",
                "lu",
                "tanggal",
                "shift",
            ]
        ).to_csv(filename, index=False)

    return str(filename)


def get_users_file_path() -> str:
    """Get or create the users CSV file path."""
    script_folder = Path(get_script_folder())
    data_folder = script_folder / "data"
    data_folder.mkdir(parents=True, exist_ok=True)

    filename = data_folder / "users.csv"
    if not filename.exists():
        pd.DataFrame(columns=["username"]).to_csv(filename, index=False)

    return str(filename)


def load_users() -> list[str]:
    """Load unique usernames from the users CSV file."""
    try:
        df = pd.read_csv(get_users_file_path())
        return sorted(df["username"].dropna().unique().tolist())
    except Exception:
        return []


def save_user(username: str) -> None:
    """Append a new username to the users CSV if it doesn't exist."""
    if not username or not username.strip():
        return

    username = username.strip()
    filepath = get_users_file_path()

    try:
        df = pd.read_csv(filepath)
        if username not in df["username"].values:
            new_row = pd.DataFrame([{"username": username}])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(filepath, index=False)
    except Exception:
        pass
