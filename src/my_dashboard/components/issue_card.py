import tkinter as tk
import uuid
from ast import List
from tkinter import Menu

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame


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

        # Header
        header = ttk.Frame(self)
        header.pack(expand=True, fill="x", padx=(0, 0), pady=(0, 10))

        self.textbox = ttk.Entry(header, bootstyle="warning", width=51)
        self.textbox.pack(side="left", fill="x", expand=True, padx=(0, 4), pady=(0, 2))

        # Placeholder
        self.placeholder = "Masukkan detail..."
        self.textbox.insert(0, self.placeholder)
        self.textbox.config(foreground="gray")
        self.textbox._placeholder_active = True
        self.textbox._placeholder_text = self.placeholder
        self.textbox.bind("<FocusIn>", self.on_focus_in)
        self.textbox.bind("<FocusOut>", self.on_focus_out)

        # + Action Button
        add_btn = ttk.Button(
            header,
            text="+ Action",
            width=8,
            bootstyle="warning",
            command=self.add_action,
        )
        add_btn.pack(side="right", padx=(4, 0), pady=(0, 2))

        self.configure(
            bootstyle="warning",
            labelwidget=header,
        )

        # Klik kanan pada textbox
        self.textbox.bind("<Button-3>", self.show_context_menu)

        # Action container (dengan indentasi)
        self.action_container = ttk.Frame(self)
        self.action_container.pack(fill="x", padx=(15, 15), pady=(0, 8))

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
        issue_frame.pack(fill="x", padx=0, pady=(0, 0))

        # ttk.Label(issue_frame, text="Issue:", width=8, anchor="w").pack(
        #     side="left", padx=(5, 5)
        # )
        self.issue_entry = ttk.Entry(issue_frame, bootstyle="success", width=55)
        setup_entry_placeholder(self.issue_entry, "Masukkan issue...")
        self.issue_entry.pack(
            side="left", fill="x", expand=True, padx=(0, 4), pady=(0, 0)
        )

        # + Detail Button
        add_detail_btn = ttk.Button(
            issue_frame,
            text="+ Detail",
            width=8,
            bootstyle="success",
            command=self.add_detail_item,
        )
        add_detail_btn.pack(side="right", padx=(4, 0), pady=(0, 0))

        # Style untuk card
        self.configure(
            bootstyle="success",
            labelwidget=issue_frame,
        )

        # Detail Container
        self.detail_container = ttk.Frame(
            self,
        )
        self.detail_container.pack(fill="x", padx=(25, 10), pady=(0, 0))

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
class App(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("Issue Tracker – Clean Layout")
        self.geometry("820x880")
        self.minsize(720, 600)

        # Header
        header = ttk.Frame(self)
        header.pack(fill="x", padx=20, pady=(20, 10))
        ttk.Label(
            header,
            text="Issue Tracker",
            font=("", 16, "bold"),
            bootstyle="inverse-dark",
        ).pack(side="left")

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=20, pady=10)

        ttk.Button(
            btn_frame,
            text="+ Tambah Card",
            command=self.add_new_card,
            width=15,
            bootstyle="success",
        ).pack(side="left")

        ttk.Button(
            btn_frame,
            text="Tampilkan Data",
            command=self.show_all_data,
            width=15,
            bootstyle="primary",
        ).pack(side="right")

        # Scrollable
        self.scrollable = ScrolledFrame(self, autohide=True)
        self.scrollable.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.scrollable_frame = self.scrollable

        self.cards = {}
        self.add_new_card()

    def add_new_card(self):
        card = IssueCard(self.scrollable_frame, on_delete=self.remove_card)
        card.pack(fill="x", pady=10, padx=5, ipadx=5, ipady=5)
        self.cards[card.card_id] = card

    def remove_card(self, card_id):
        if card_id in self.cards:
            del self.cards[card_id]

    def show_all_data(self):
        print("\n" + "=" * 70)
        print("DATA SEMUA CARD")
        print("=" * 70)
        for idx, card in enumerate(self.cards.values(), 1):
            data = card.get_data()
            if not data:
                continue
            print(f"CARD {idx}")
            print(f"ID    : {data['id']}")
            print(f"Issue : {data['issue']}")
            for d_idx, detail in enumerate(data["details"], 1):
                print(f"Detail {d_idx}: {detail['detail']}")
                print("   Actions:")
                for a_idx, action in enumerate(detail["actions"], 1):
                    print(f"      {a_idx}. {action}")
            print("-" * 70)
        print(f"Total Card: {len([c for c in self.cards.values() if c.get_data()])}\n")


if __name__ == "__main__":
    app = App()
    app.mainloop()
