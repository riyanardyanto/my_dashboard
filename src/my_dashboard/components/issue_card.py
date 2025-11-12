import tkinter as tk
import uuid
from ast import List
from tkinter import Menu, messagebox
from typing import Optional, Dict

import ttkbootstrap as ttk
from PIL import Image, ImageTk, UnidentifiedImageError
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tooltip import ToolTip

from ..utils.helpers import resource_path


_ACTION_ICON: Optional[ImageTk.PhotoImage] = None
_DETAIL_ICON: Optional[ImageTk.PhotoImage] = None
_ADD_ICON: Optional[ImageTk.PhotoImage] = None
_BIN_ICON: Optional[ImageTk.PhotoImage] = None


def _get_action_icon() -> Optional[ImageTk.PhotoImage]:
    global _ACTION_ICON
    if _ACTION_ICON is None:
        try:
            image = Image.open(resource_path("assets/+_action.png")).resize(
                (16, 16), Image.LANCZOS
            )
        except (FileNotFoundError, UnidentifiedImageError):
            return None
        _ACTION_ICON = ImageTk.PhotoImage(image)
    return _ACTION_ICON


def _get_detail_icon() -> Optional[ImageTk.PhotoImage]:
    global _DETAIL_ICON
    if _DETAIL_ICON is None:
        try:
            image = Image.open(resource_path("assets/+_detail.png")).resize(
                (16, 16), Image.LANCZOS
            )
        except (FileNotFoundError, UnidentifiedImageError):
            return None
        _DETAIL_ICON = ImageTk.PhotoImage(image)
    return _DETAIL_ICON


def _get_add_icon() -> Optional[ImageTk.PhotoImage]:
    global _ADD_ICON
    if _ADD_ICON is None:
        try:
            image = Image.open(resource_path("assets/add.png")).resize(
                (16, 16), Image.LANCZOS
            )
        except (FileNotFoundError, UnidentifiedImageError):
            return None
        _ADD_ICON = ImageTk.PhotoImage(image)
    return _ADD_ICON


def _get_bin_icon() -> Optional[ImageTk.PhotoImage]:
    global _BIN_ICON
    if _BIN_ICON is None:
        try:
            image = Image.open(resource_path("assets/bin.png")).resize(
                (16, 16), Image.LANCZOS
            )
        except (FileNotFoundError, UnidentifiedImageError):
            return None
        _BIN_ICON = ImageTk.PhotoImage(image)
    return _BIN_ICON


def setup_entry_placeholder(entry, placeholder_text):
    """Attach placeholder text behavior to a ttk Entry."""

    def handle_focus_in(_):
        if getattr(entry, "_placeholder_active", False):
            entry.delete(0, "end")
            entry.configure(foreground="white")
            entry._placeholder_active = False

    def handle_focus_out(_):
        if not entry.get():
            entry.insert(0, placeholder_text)
            entry.configure(foreground="gray")
            entry._placeholder_active = True

    entry.insert(0, placeholder_text)
    entry.configure(foreground="gray")
    entry._placeholder_active = True
    entry._placeholder_text = placeholder_text
    entry.bind("<FocusIn>", handle_focus_in, add="+")
    entry.bind("<FocusOut>", handle_focus_out, add="+")


# ----------------------------------------------------------------------
# Action Item (klik kanan -> delete)
# ----------------------------------------------------------------------
class ActionItem(ttk.Frame):
    def __init__(self, master, on_remove=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_remove = on_remove

        self.entry = ttk.Entry(self, bootstyle="info")
        setup_entry_placeholder(self.entry, "Tindakan...")
        self.entry.pack(side="left", fill="x", expand=True, padx=(20, 0))

        # Klik kanan pada entry
        self.entry.bind("<Button-3>", self.show_context_menu)
        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(label="Delete", command=self.delete_self)

    def show_context_menu(self, event: tk.Event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def delete_self(self):
        if self.on_remove:
            self.on_remove(self)
        self.destroy()

    def get_text(self):
        if getattr(self.entry, "_placeholder_active", False):
            return ""
        return self.entry.get().strip()


# ----------------------------------------------------------------------
# Detail Item (klik kanan -> delete)
# ----------------------------------------------------------------------
class DetailItem(ttk.Labelframe):
    def __init__(self, master, on_remove=None, number=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_remove = on_remove
        self.action_items: List[ActionItem] = []

        # Header with width = parent width  - padding
        header = ttk.Frame(self)
        header.pack(expand=True, fill="x", padx=(0, 0), pady=(0, 10))

        # + Action Button
        add_btn = ttk.Button(
            header,
            bootstyle="warning",
            command=self.add_action,
        )
        icon = _get_action_icon()
        if icon:
            add_btn.configure(image=icon, compound="image")
            add_btn.image = icon
        add_btn.pack(side="right", anchor=E, padx=(4, 0), pady=(0, 2))

        ToolTip(add_btn, "Tambah tindakan", delay=0, position="left")

        # Textbox untuk detail lengan lebar = parent of parent width
        self.textbox = ttk.Entry(header, bootstyle="warning", width=250)
        self.textbox.pack(
            side="left", anchor=W, fill="x", expand=True, padx=(0, 4), pady=(0, 2)
        )

        # Placeholder
        self.placeholder = "Masukkan detail..."
        self.textbox.insert(0, self.placeholder)
        self.textbox.config(foreground="gray")
        self.textbox._placeholder_active = True
        self.textbox._placeholder_text = self.placeholder
        self.textbox.bind("<FocusIn>", self.on_focus_in)
        self.textbox.bind("<FocusOut>", self.on_focus_out)

        self.configure(
            bootstyle="warning",
            labelwidget=header,
        )

        # Klik kanan pada textbox
        self.textbox.bind("<Button-3>", self.show_context_menu)

        # Action container (dengan indentasi)
        self.action_container = ttk.Frame(self)
        self.action_container.pack(fill="x", padx=(10, 10), pady=(0, 8))

        # Tambah action pertama
        self.add_action()

        # Context menu
        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(label="Delete Detail", command=self.delete_self)

    def on_focus_in(self, event: tk.Event):
        if self.textbox.get().strip() == self.placeholder and getattr(
            self.textbox, "_placeholder_active", False
        ):
            self.textbox.delete(0, "end")
            self.textbox.config(foreground="white")
            self.textbox._placeholder_active = False

    def on_focus_out(self, event: tk.Event):
        if not self.textbox.get().strip():
            self.textbox.insert(0, self.placeholder)
            self.textbox.config(foreground="gray")
            self.textbox._placeholder_active = True
        else:
            self.textbox._placeholder_active = False

    def show_context_menu(self, event: tk.Event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def add_action(self):
        item = ActionItem(self.action_container, on_remove=self.remove_action)
        item.pack(fill="x", pady=2)
        self.action_items.append(item)
        item.entry.focus_set()

    def remove_action(self, item):
        if item in self.action_items:
            self.action_items.remove(item)

    def delete_self(self):
        if self.on_remove:
            self.on_remove(self)
        self.destroy()

    def get_data(self):
        if getattr(self.textbox, "_placeholder_active", False):
            detail_text = ""
        else:
            detail_text = self.textbox.get().strip()
        actions = [a.get_text() for a in self.action_items if a.get_text()]
        return {"detail": detail_text, "actions": actions} if detail_text else None


# ----------------------------------------------------------------------
# Issue Card
# ----------------------------------------------------------------------
class IssueCard(ttk.LabelFrame):
    def __init__(self, master, on_delete=None, **kwargs):
        super().__init__(master, **kwargs)
        self.card_id = str(uuid.uuid4())
        self.on_delete = on_delete
        self.detail_items: List[DetailItem] = []

        # Issue Row
        issue_frame = ttk.Frame(self)
        issue_frame.pack(fill="x", expand=True, padx=0, pady=(0, 0))

        # + Detail Button
        add_detail_btn = ttk.Button(
            issue_frame,
            bootstyle="success",
            command=self.add_detail_item,
        )
        detail_icon = _get_detail_icon()
        if detail_icon:
            add_detail_btn.configure(image=detail_icon, compound="image")
            add_detail_btn.image = detail_icon
        add_detail_btn.pack(side="right", padx=(4, 0), pady=(0, 0))

        ToolTip(add_detail_btn, "Tambah detail", delay=0, position="left")

        # Entry
        self.issue_entry = ttk.Entry(issue_frame, bootstyle="success", width=200)
        setup_entry_placeholder(self.issue_entry, "Masukkan issue...")
        self.issue_entry.pack(
            side="left", fill="x", expand=True, padx=(0, 4), pady=(0, 0)
        )

        # Style untuk card
        self.configure(
            bootstyle="success",
            labelwidget=issue_frame,
        )

        # Detail Container
        self.detail_container = ttk.Frame(
            self,
        )
        self.detail_container.pack(fill="x", padx=(15, 10), pady=(0, 0))

        # Tambah detail pertama
        self.add_detail_item()

        # Klik kanan pada card → hapus card
        self.bind("<Button-3>", self.show_card_menu)
        self.card_menu = Menu(self, tearoff=0)
        self.card_menu.add_command(label="Delete Card", command=self.delete_card)

    def show_card_menu(self, event: tk.Event):
        # Cek apakah klik di area kosong (bukan widget lain)
        widget = event.widget
        if widget in (self, self.detail_container):
            try:
                self.card_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.card_menu.grab_release()

    def add_detail_item(self):
        item = DetailItem(
            self.detail_container,
            on_remove=self.remove_detail_item,
            number=len(self.detail_items) + 1,
        )
        item.pack(fill="x", pady=(3, 0))
        self.detail_items.append(item)
        item.textbox.focus_set()

    def remove_detail_item(self, item):
        if item in self.detail_items:
            self.detail_items.remove(item)

    def delete_card(self):
        if self.on_delete:
            self.on_delete(self.card_id)
        self.destroy()

    def set_issue(self, issue_text: str):
        """Populate the issue entry without triggering placeholder state."""
        self.issue_entry.delete(0, "end")
        self.issue_entry.insert(0, issue_text)
        self.issue_entry.configure(foreground="white")
        self.issue_entry._placeholder_active = False

    def get_data(self):
        if getattr(self.issue_entry, "_placeholder_active", False):
            issue = ""
        else:
            issue = self.issue_entry.get().strip()
        details = [item.get_data() for item in self.detail_items if item.get_data()]
        return (
            {"id": self.card_id, "issue": issue, "details": details}
            if issue or details
            else None
        )


# ----------------------------------------------------------------------
# MAIN APP
# ----------------------------------------------------------------------
class IssueCardFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.cards_header = ttk.Frame(self, padding=(4, 10, 4, 6))
        self.cards_header.pack(fill="x")

        ttk.Label(
            self.cards_header,
            text="Issue Cards",
            font=("Segoe UI", 12, "bold"),
            foreground="white",
        ).pack(side="left")

        self.clear_btn = ttk.Button(
            self.cards_header,
            bootstyle="danger",
            text="Clear",
            width=10,
            command=self.clear_cards,
        )
        bin_icon = _get_bin_icon()
        if bin_icon:
            self.clear_btn.configure(image=bin_icon, compound="left")
            self.clear_btn.image = bin_icon
        self.clear_btn.pack(side="right", padx=(4, 0))

        ToolTip(self.clear_btn, "Clear all cards", delay=0, position="left")

        self.add_card_btn = ttk.Button(
            self.cards_header,
            bootstyle="success",
            text="Add Card",
            width=10,
            command=self.add_card,
        )
        add_icon = _get_add_icon()
        if add_icon:
            self.add_card_btn.configure(image=add_icon, compound="left")
            self.add_card_btn.image = add_icon
        self.add_card_btn.pack(side="right", padx=(4, 0))

        ToolTip(self.add_card_btn, "Add new card", delay=0, position="left")

        self.cards_badge = ttk.Label(
            self.cards_header,
            text="0 Kartu",
            # bootstyle="secondary",
            padding=(8, 2),
        )
        self.cards_badge.pack(side="right")

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=4)

        self.scrollable = ScrolledFrame(self, autohide=True, padding=(4, 0))
        self.scrollable.pack(fill="both", expand=True, pady=(8, 12))
        self.cards_container = self.scrollable
        self.cards: Dict[str, IssueCard] = {}

        # Ensure at least one empty card is visible
        self.add_card()

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

    def _update_card_badge(self) -> None:
        count = len(self.cards)
        label = "Kartu" if count == 1 else "Kartu"
        self.cards_badge.configure(text=f"{count} {label}")

    def remove_card(self, card_id: str) -> None:
        """Remove a card reference once it is destroyed."""

        if card_id in self.cards:
            del self.cards[card_id]
            self._update_card_badge()

    def clear_cards(self) -> None:
        """Delete all cards and leave a single empty card for the user."""

        if len(self.cards) <= 1:
            # If only one card or none, just clear it silently
            for card in list(self.cards.values()):
                card.destroy()
            self.cards.clear()
            self.add_card()
            return

        # Show warning if multiple cards exist
        result = messagebox.askyesno(
            "Konfirmasi",
            f"Apakah Anda yakin ingin menghapus semua {len(self.cards)} kartu?",
            icon="warning",
        )

        if result:
            for card in list(self.cards.values()):
                card.destroy()
            self.cards.clear()
            self.add_card()
