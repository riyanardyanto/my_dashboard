"""Dashboard layout container for the issue tracker application."""

from __future__ import annotations

from typing import Callable, Dict, Iterable, Optional

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tableview import Tableview

from ..components.editble_tableview import EditableTableView
from ..components.issue_card import IssueCard
from ..components.sidebar import Sidebar


class DashboardView(ttk.Frame):
    """Compose and expose the widgets used by the dashboard window."""

    def __init__(self, master: ttk.Window):
        super().__init__(master)
        self.pack(fill="both", expand=True)

        self.sidebar = Sidebar(self)
        self.sidebar.pack(anchor="nw", side="left", fill="y")

        self.main_view = ttk.Frame(self)
        self.main_view.pack(anchor="nw", side="left", fill="both", expand=True)

        # Header with title, status, and progress indicator
        self.header_top = ttk.Frame(self.main_view, padding=(10, 5, 10, 0))
        self.header_top.pack(side="top", fill="x", expand=True)
        self.header_top.columnconfigure(0, weight=1)
        self.header_top.columnconfigure(1, weight=0)

        title_container = ttk.Frame(self.header_top)
        title_container.grid(row=0, column=0, sticky="ew")

        ttk.Label(
            title_container,
            text="Issue Tracker Dashboard",
            font=("Segoe UI", 16, "bold"),
            bootstyle="primary",
        ).pack(anchor="w")
        ttk.Label(
            title_container,
            text="Pantau downtime dan rencana perbaikan secara real-time",
            # bootstyle="success",
        ).pack(anchor="w", pady=(0, 0))

        status_container = ttk.Frame(self.header_top)
        status_container.grid(row=0, column=1, sticky="e", padx=(15, 0))

        self.time_period = ttk.Label(
            status_container,
            text="",
            # bootstyle="secondary",
            justify="right",
            anchor="e",
        )
        self.time_period.pack(fill="x")

        self.progressbar = ttk.Progressbar(
            status_container,
            mode="indeterminate",
            style="success.Striped.Horizontal.TProgressbar",
            length=450,
        )
        self.progressbar.pack(fill="x", pady=(6, 0))

        # Main content split into issue table and cards area
        self.main_content = ttk.Frame(self.main_view, padding=(0, 0, 0, 15))
        self.main_content.pack(anchor="nw", side="left", fill="both", expand=True)

        self.left_frame = ttk.Labelframe(
            self.main_content,
            text="Daftar Stop Reason",
            padding=(5, 0, 5, 5),
            bootstyle="info",
        )

        self.left_frame.pack(side="left", fill="y", padx=(0, 5), pady=(15, 0))

        self.issue_table = Tableview(
            self.left_frame,
            bootstyle=ttk.INFO,
            coldata=["Line", "Issue", "Stops", "Downtime"],
            rowdata=[],
            autofit=True,
            searchable=True,
            height=50,
        )
        self.issue_table.pack(fill="both", expand=False)

        self.right_frame = ttk.Frame(self.main_content, padding=(0, 0, 15, 0))
        self.right_frame.pack(
            side="right", fill="both", expand=True, padx=(5, 0), pady=(15, 0)
        )

        # Achievement table and card controls
        self.header_frame = ttk.Frame(self.right_frame)
        self.header_frame.pack(
            side="top", expand=False, fill="x", padx=(5, 0), pady=(0, 8)
        )

        self.achievement_frame = ttk.Labelframe(
            self.header_frame,
            text="Ringkasan Achievement",
            padding=(5, 0, 5, 5),
            bootstyle="warning",
        )
        self.achievement_frame.pack(
            side="left", anchor="n", fill="both", expand=False, padx=(0, 12), pady=0
        )

        coldata = [
            ("Metrik", "w"),
            ("Target", "c"),
            ("Aktual", "c"),
        ]
        rowdata = [
            ("STOP", 3, 0),
            ("PR", 85, 0),
            ("MTBF", 150, 0),
            ("UPDT", 4, 0),
            ("PDT", 8, 0),
            ("NATR", 4, 0),
        ]

        self.achieve_table = EditableTableView(
            master=self.achievement_frame,
            coldata=coldata,
            rowdata=rowdata,
            editable_columns=[1, 2],
            row_height=30,
            paginated=False,
            bootstyle=ttk.SUCCESS,
            autoalign=True,
            autofit=True,
            height=6,
        )
        self.achieve_table.pack(fill="both", expand=False)

        btn_frame = ttk.Frame(self.header_frame, padding=(4, 4, 0, 0))
        btn_frame.pack(side="right", fill="y")

        self.show_cards_button = ttk.Button(
            btn_frame,
            text="Tampilkan Data",
            width=16,
            bootstyle="primary",
        )
        self.show_cards_button.pack(fill="x", pady=(0, 10))

        self.check_table = ttk.Checkbutton(
            btn_frame,
            text="Tampilkan Tabel",
            width=16,
            bootstyle="round-toggle",
        )
        self.check_table.pack(fill="x", pady=(0, 35))

        self.clear_cards_button = ttk.Button(
            btn_frame,
            text="Clear Cards",
            width=16,
            bootstyle="danger",
        )
        self.clear_cards_button.pack(fill="x", pady=(0, 10))

        self.add_card_button = ttk.Button(
            btn_frame,
            text="+ Tambah Card",
            width=16,
            bootstyle="success",
        )
        self.add_card_button.pack(fill="x", pady=(0, 10))

        self.cards_header = ttk.Frame(self.right_frame, padding=(4, 10, 4, 6))
        self.cards_header.pack(fill="x")

        ttk.Label(
            self.cards_header,
            text="Issue Cards",
            font=("Segoe UI", 12, "bold"),
            bootstyle="inverse-primary",
        ).pack(side="left")

        self.cards_badge = ttk.Label(
            self.cards_header,
            text="0 Kartu",
            # bootstyle="secondary",
            padding=(8, 2),
        )
        self.cards_badge.pack(side="right")

        ttk.Separator(self.right_frame, orient="horizontal").pack(fill="x", padx=4)

        self.scrollable = ScrolledFrame(self.right_frame, autohide=True, padding=(4, 0))
        self.scrollable.pack(fill="both", expand=True, pady=(8, 12))
        self.cards_container = self.scrollable
        self.cards: Dict[str, IssueCard] = {}

        # Ensure at least one empty card is visible
        self.add_card()

    # ------------------------------------------------------------------
    # Public helpers ---------------------------------------------------
    # ------------------------------------------------------------------
    def configure_card_actions(
        self,
        *,
        on_add_card: Callable[[], None],
        on_show_cards: Callable[[], None],
        on_clear_cards: Callable[[], None],
    ) -> None:
        """Attach callbacks to the card control buttons."""

        self.add_card_button.configure(command=on_add_card)
        self.show_cards_button.configure(command=on_show_cards)
        self.clear_cards_button.configure(command=on_clear_cards)

    def add_card(self, issue_text: Optional[str] = None) -> IssueCard:
        """Create a new issue card and register it in the view."""

        card = IssueCard(self.cards_container, on_delete=self.remove_card)
        card.pack(fill="x", pady=10, padx=5, ipadx=5, ipady=5)
        self.cards[card.card_id] = card
        if issue_text:
            card.set_issue(issue_text)
        card.issue_entry.focus_set()
        self._update_card_badge()
        return card

    def remove_card(self, card_id: str) -> None:
        """Remove a card reference once it is destroyed."""

        if card_id in self.cards:
            del self.cards[card_id]
            self._update_card_badge()

    def clear_cards(self) -> None:
        """Delete all cards and leave a single empty card for the user."""

        for card in list(self.cards.values()):
            card.destroy()
        self.cards.clear()
        self.add_card()

    def iter_card_data(self) -> Iterable[dict]:
        """Yield the structured data for each populated card."""

        for card in self.cards.values():
            data = card.get_data()
            if data:
                yield data

    def get_card_entries(self) -> list[dict]:
        """Return a list with serialized card entries."""

        return list(self.iter_card_data())

    def _update_card_badge(self) -> None:
        count = len(self.cards)
        label = "Kartu" if count == 1 else "Kartu"
        self.cards_badge.configure(text=f"{count} {label}")
