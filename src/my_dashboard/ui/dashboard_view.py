"""Dashboard layout container for the issue tracker application."""

from __future__ import annotations

from typing import Callable, Dict, Iterable, Optional

import ttkbootstrap as ttk
from ttkbootstrap.constants import RIGHT, S
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
        self.sidebar.pack(side="left", fill="y")

        self.main_view = ttk.Frame(self)
        self.main_view.pack(side="left", fill="both", expand=True)

        # Header with progressbar and time range label
        self.header_top = ttk.Frame(self.main_view)
        self.header_top.pack(fill="x", expand=False, padx=10, pady=(5, 0))

        self.progressbar = ttk.Progressbar(
            self.header_top,
            mode="determinate",
            style="success.Striped.Horizontal.TProgressbar",
        )
        self.progressbar.pack(
            side="left", expand=True, fill="x", padx=(10, 0), pady=(0, 0)
        )

        self.time_period = ttk.Label(
            self.header_top,
            text="",
            font=("", 10),
            bootstyle="inverse-dark",
            justify="right",
        )
        self.time_period.pack(padx=(5, 0), pady=(0, 0), fill="none", side=RIGHT)

        # Main content split into issue table and cards area
        self.main_content = ttk.Frame(self.main_view)
        self.main_content.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.left_frame = ttk.Frame(self.main_content, width=200)
        self.left_frame.pack(side="left", fill="y")

        self.issue_table = Tableview(
            self.left_frame,
            coldata=["Line", "Issue", "Stops", "Downtime"],
            rowdata=[],
            autofit=True,
            searchable=True,
        )
        self.issue_table.pack(fill="both", expand=True, padx=10, pady=10)

        self.right_frame = ttk.Frame(self.main_content)
        self.right_frame.pack(side="right", fill="both", expand=True)

        # Achievement table and card controls
        self.header_frame = ttk.Frame(self.right_frame)
        self.header_frame.pack(fill="x", padx=(10, 0), pady=(15, 0))

        self.achievement_frame = ttk.Labelframe(self.header_frame)
        self.achievement_frame.pack(
            side="left", fill="x", expand=False, padx=(0, 10), pady=0
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
        self.achieve_table.pack(
            side="left", fill="both", expand=True, padx=10, pady=(5, 10)
        )

        btn_frame = ttk.Frame(self.header_frame)
        btn_frame.pack(side="right", fill="both", padx=(0, 10), pady=0)

        self.add_card_button = ttk.Button(
            btn_frame,
            text="+ Tambah Card",
            width=15,
            bootstyle="success",
        )
        self.add_card_button.pack(side="bottom", anchor=S, padx=(0, 0), pady=(0, 5))

        self.check_table = ttk.Checkbutton(
            btn_frame,
            text="Table Data",
            width=15,
            bootstyle="primary",
        )
        self.check_table.pack(side="bottom", anchor=S, padx=(0, 0), pady=(0, 25))

        self.clear_cards_button = ttk.Button(
            btn_frame,
            text="Clear Cards",
            width=15,
            bootstyle="primary",
        )
        self.clear_cards_button.pack(side="bottom", anchor=S, padx=(0, 0), pady=(0, 5))

        self.show_cards_button = ttk.Button(
            btn_frame,
            text="Tampilkan Data",
            width=15,
            bootstyle="primary",
        )
        self.show_cards_button.pack(side="bottom", anchor=S, padx=(0, 0), pady=(0, 5))

        self.scrollable = ScrolledFrame(self.right_frame, autohide=True)
        self.scrollable.pack(fill="both", expand=True, padx=5, pady=(0, 20))
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
        return card

    def remove_card(self, card_id: str) -> None:
        """Remove a card reference once it is destroyed."""

        if card_id in self.cards:
            del self.cards[card_id]

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
