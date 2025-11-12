"""Dashboard layout container for the issue tracker application."""

from __future__ import annotations

from tkinter import TOP
from typing import Callable, Iterable

import ttkbootstrap as ttk
from PIL import Image, ImageTk, UnidentifiedImageError
from ttkbootstrap.tableview import Tableview
from ttkbootstrap.tooltip import ToolTip
from ttkwidgets.autocomplete import AutocompleteCombobox

from ..components.editble_tableview import EditableTableView
from ..components.issue_card import IssueCardFrame
from ..components.sidebar import Sidebar
from ..utils.csvhandle import load_users, save_user
from ..utils.helpers import resource_path


class DashboardView(ttk.Frame):
    """Compose and expose the widgets used by the dashboard window."""

    def __init__(self, master: ttk.Window):
        super().__init__(master)
        self.pack(fill="both", expand=True)

        self.sidebar = Sidebar(self)
        self.sidebar.pack(anchor="nw", side="left", fill="none", expand=False)

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
            ("STOP", 0, 0),
            ("PR", 0, 0),
            ("MTBF", 0, 0),
            ("UPDT", 0, 0),
            ("PDT", 0, 0),
            ("NATR", 0, 0),
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

        self.target_btn = ttk.Button(
            btn_frame,
            text="Set Target",
            width=12,
            bootstyle="warning",
        )
        self.target_btn.pack(fill="x", pady=(0, 10))

        ToolTip(self.target_btn, "Atur Target", delay=0, position="left")

        try:
            target_image = Image.open(resource_path("assets/target.png")).resize(
                (16, 16), Image.LANCZOS
            )
            target_icon = ImageTk.PhotoImage(target_image)
            self.target_btn.configure(image=target_icon, compound="left")
            self.target_btn.image = target_icon
        except (FileNotFoundError, UnidentifiedImageError):
            pass

        self.show_cards_button = ttk.Button(
            btn_frame,
            text="Show Report",
            width=12,
            bootstyle="primary",
        )

        ToolTip(
            self.show_cards_button,
            "Tampilkan Laporan Issue Cards",
            delay=0,
            position="left",
        )

        try:
            qr_image = Image.open(resource_path("assets/qrcode.png")).resize(
                (16, 16), Image.LANCZOS
            )
            qr_icon = ImageTk.PhotoImage(qr_image)
            self.show_cards_button.configure(image=qr_icon, compound="left")
            self.show_cards_button.image = qr_icon
        except (FileNotFoundError, UnidentifiedImageError):
            pass
        self.show_cards_button.pack(fill="x", pady=(0, 10))

        self.check_table = ttk.Checkbutton(
            btn_frame,
            text="Show Table",
            width=12,
            bootstyle="round-toggle",
        )
        self.check_table.pack(fill="x", pady=(0, 35))

        self.entry_user = AutocompleteCombobox(
            btn_frame,
            width=15,
            completevalues=load_users(),
            cursor="hand2",
        )
        self.entry_user.pack(side=TOP, pady=(0, 10))
        self.entry_user.bind("<<ComboboxSelected>>", self._on_user_selected)
        self.entry_user.bind("<Return>", self._on_user_entry)
        self.entry_user.bind("<FocusOut>", self._on_user_entry)
        ToolTip(self.entry_user, "Select Username", delay=0, position="left")

        self.save_btn = ttk.Button(
            btn_frame,
            text="Save Data",
            width=12,
            bootstyle="success",
        )
        try:
            excel_image = Image.open(resource_path("assets/excel.png")).resize(
                (16, 16), Image.LANCZOS
            )
            excel_icon = ImageTk.PhotoImage(excel_image)
            self.save_btn.configure(image=excel_icon, compound="left")
            self.save_btn.image = excel_icon
        except (FileNotFoundError, UnidentifiedImageError):
            pass
        self.save_btn.pack(fill="x", pady=(0, 10))

        ToolTip(self.save_btn, "Simpan Data ke Excel", delay=0, position="left")

        self.card_frame = IssueCardFrame(self.right_frame)
        self.card_frame.pack(fill="both", expand=True, pady=(8, 12))

    # ------------------------------------------------------------------
    # User entry event handlers ----------------------------------------
    # ------------------------------------------------------------------
    def _on_user_selected(self, event) -> None:
        """Handle when user selects from dropdown."""
        username = self.entry_user.get().strip()
        if username:
            save_user(username)

    def _on_user_entry(self, event) -> None:
        """Handle when user types and commits (Enter or loses focus)."""
        username = self.entry_user.get().strip()
        if username:
            save_user(username)
            # Refresh autocomplete values
            current_users = load_users()
            self.entry_user.configure(completevalues=current_users)

    # ------------------------------------------------------------------
    # Public helpers ---------------------------------------------------
    # ------------------------------------------------------------------
    def configure_card_actions(self, *, on_show_cards: Callable[[], None]) -> None:
        """Attach callbacks to the card control buttons."""

        self.show_cards_button.configure(command=on_show_cards)

    def iter_card_data(self) -> Iterable[dict]:
        """Yield the structured data for each populated card."""

        for card in self.card_frame.cards.values():
            data = card.get_data()
            if data:
                yield data

    def get_card_entries(self) -> list[dict]:
        """Return a list with serialized card entries."""

        return list(self.iter_card_data())
