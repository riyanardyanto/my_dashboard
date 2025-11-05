import json
import tkinter as tk
import uuid
from datetime import datetime
from tkinter import Menu

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame


def setup_entry_placeholder(entry, placeholder_text, string_var=None):
    """Attach placeholder text behavior to a ttk Entry."""

    def handle_focus_in(_):
        if getattr(entry, "_placeholder_active", False):
            entry.delete(0, "end")
            entry.configure(foreground="black")
            entry._placeholder_active = False
            if string_var is not None:
                string_var.set("")

    def handle_focus_out(_):
        if not entry.get():
            entry.delete(0, "end")
            entry.insert(0, placeholder_text)
            entry.configure(foreground="gray")
            entry._placeholder_active = True
            if string_var is not None:
                string_var.set(placeholder_text)

    entry.delete(0, "end")
    entry.insert(0, placeholder_text)
    entry.configure(foreground="gray")
    entry._placeholder_active = True
    entry._placeholder_text = placeholder_text
    entry._placeholder_focus_out = handle_focus_out
    entry.bind("<FocusIn>", handle_focus_in, add="+")
    entry.bind("<FocusOut>", handle_focus_out, add="+")


# ----------------------------------------------------------------------
# Action Item (klik kanan -> delete)
# ----------------------------------------------------------------------
class ActionItem(ttk.Frame):
    def __init__(self, master, on_remove=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_remove = on_remove

        self.entry = ttk.Entry(self, bootstyle="secondary")
        setup_entry_placeholder(self.entry, "Tindakan...")
        self.entry.pack(side="left", fill="x", expand=True, padx=(20, 0))

        # Klik kanan pada entry
        self.entry.bind("<Button-3>", self.show_context_menu)
        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(label="Delete", command=self.delete_self)

    def show_context_menu(self, event: tk.Event):
        # Ensure menu stays within screen bounds
        x = min(event.x_root, self.winfo_screenwidth() - 100)
        y = min(event.y_root, self.winfo_screenheight() - 100)
        try:
            self.context_menu.tk_popup(x, y)
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
class DetailItem(ttk.Frame):
    def __init__(self, master, on_remove=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_remove = on_remove
        self.action_items = []
        self._placeholder_active = True  # Flag for textbox placeholder

        # Header
        header = ttk.Frame(self)
        header.pack(fill="x", padx=15, pady=(8, 5))

        self.textbox = ttk.Text(header, height=4, width=50)
        self.textbox.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Placeholder
        self.placeholder = "Masukkan detail..."
        self.textbox.insert("1.0", self.placeholder)
        self.textbox.config(foreground="gray")
        self.textbox.bind("<FocusIn>", self.on_focus_in)
        self.textbox.bind("<FocusOut>", self.on_focus_out)

        # + Action Button
        add_btn = ttk.Button(
            header,
            text="+ Action",
            width=10,
            bootstyle="warning",
            command=self.add_action,
        )
        add_btn.pack(side="right")

        # Klik kanan pada textbox
        self.textbox.bind("<Button-3>", self.show_context_menu)

        # Action container (dengan indentasi)
        self.action_container = ttk.Frame(self)
        self.action_container.pack(fill="x", padx=(35, 15), pady=(0, 8))

        # Context menu
        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(label="Delete Detail", command=self.delete_self)

    def on_focus_in(self, event: tk.Event):
        if self._placeholder_active:
            self.textbox.delete("1.0", "end")
            self.textbox.config(foreground="black")
            self._placeholder_active = False

    def on_focus_out(self, event: tk.Event):
        if not self.textbox.get(
            "1.0", "end-1c"
        ).strip():  # Use end-1c to remove trailing newline
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", self.placeholder)
            self.textbox.config(foreground="gray")
            self._placeholder_active = True

    def show_context_menu(self, event: tk.Event):
        # Ensure menu stays within screen bounds
        x = min(event.x_root, self.winfo_screenwidth() - 100)
        y = min(event.y_root, self.winfo_screenheight() - 100)
        try:
            self.context_menu.tk_popup(x, y)
        finally:
            self.context_menu.grab_release()

    def add_action(self):
        item = ActionItem(self.action_container, on_remove=self.remove_action)
        item.pack(fill="x", pady=2)
        self.action_items.append(item)
        return item  # Return the created item for external reference

    def remove_action(self, item):
        if item in self.action_items:
            self.action_items.remove(item)

    def delete_self(self):
        if self.on_remove:
            self.on_remove(self)
        self.destroy()

    def get_data(self):
        if self._placeholder_active:
            detail_text = ""
        else:
            detail_text = self.textbox.get("1.0", "end-1c").strip()
        actions = [a.get_text() for a in self.action_items if a.get_text()]
        return (
            {"detail": detail_text, "actions": actions}
            if detail_text or actions
            else None
        )


# ----------------------------------------------------------------------
# Issue Card
# ----------------------------------------------------------------------
class IssueCard(ttk.Frame):
    def __init__(self, master, on_delete=None, **kwargs):
        super().__init__(master, **kwargs)
        self.card_id = str(uuid.uuid4())
        self.on_delete = on_delete
        self.detail_items = []

        # Style untuk card
        self.configure(bootstyle="dark")

        # Issue Row
        issue_frame = ttk.Frame(self)
        issue_frame.pack(fill="x", padx=15, pady=(15, 5))

        ttk.Label(issue_frame, text="Issue:", width=8, anchor="w").pack(
            side="left", padx=(5, 5)
        )
        self.issue_entry = ttk.Entry(issue_frame, bootstyle="secondary")
        setup_entry_placeholder(self.issue_entry, "Masukkan issue...")
        self.issue_entry.pack(side="left", fill="x", expand=True, padx=(5, 8))

        # Status Indicator
        self.setup_status_indicator(issue_frame)

        # + Detail Button
        add_detail_btn = ttk.Button(
            issue_frame,
            text="+ Detail",
            width=10,
            bootstyle="success",
            command=self.add_detail_item,
        )
        add_detail_btn.pack(side="right", padx=(5, 0))

        # Detail Container
        self.detail_container = ttk.Frame(self)
        self.detail_container.pack(fill="x", padx=15, pady=(0, 10))

        # Hapus Card Button
        del_btn = ttk.Button(
            self,
            text="Hapus Card",
            width=12,
            bootstyle="danger-outline",
            command=self.delete_card,
        )
        del_btn.pack(anchor="e", padx=15, pady=(0, 5))

        # Klik kanan pada card → hapus card
        self.bind("<Button-3>", self.show_card_menu)
        self.card_menu = Menu(self, tearoff=0)
        self.card_menu.add_command(label="Delete Card", command=self.delete_card)

    def setup_status_indicator(self, parent_frame):
        status_frame = ttk.Frame(parent_frame)
        status_frame.pack(side="right", padx=(5, 0))

        self.status_var = tk.StringVar(value="open")
        status_combo = ttk.Combobox(
            status_frame,
            textvariable=self.status_var,
            values=["open", "in progress", "resolved"],
            state="readonly",
            width=12,
            bootstyle="secondary",
        )
        status_combo.pack(side="right")

        # Update card style based on status
        def update_status(*args):
            status = self.status_var.get()
            style_map = {"open": "dark", "in progress": "info", "resolved": "success"}
            self.configure(bootstyle=style_map.get(status, "dark"))

        self.status_var.trace_add("write", update_status)

    def show_card_menu(self, event: tk.Event):
        # Cek apakah klik di area kosong (bukan widget lain)
        widget = event.widget
        if widget in (self, self.detail_container):
            # Ensure menu stays within screen bounds
            x = min(event.x_root, self.winfo_screenwidth() - 100)
            y = min(event.y_root, self.winfo_screenheight() - 100)
            try:
                self.card_menu.tk_popup(x, y)
            finally:
                self.card_menu.grab_release()

    def add_detail_item(self):
        item = DetailItem(self.detail_container, on_remove=self.remove_detail_item)
        item.pack(fill="x", pady=(3, 0))
        self.detail_items.append(item)
        return item  # Return the created item for external reference

    def remove_detail_item(self, item):
        if item in self.detail_items:
            self.detail_items.remove(item)

    def delete_card(self):
        if self.on_delete:
            self.on_delete(self.card_id)
        self.destroy()

    def get_data(self):
        if getattr(self.issue_entry, "_placeholder_active", False):
            issue = ""
        else:
            issue = self.issue_entry.get().strip()
        details = [item.get_data() for item in self.detail_items if item.get_data()]
        return (
            {
                "id": self.card_id,
                "issue": issue,
                "details": details,
                "status": self.status_var.get(),
            }
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

        # Search Frame
        self.setup_search(btn_frame)

        # Scrollable
        self.scrollable = ScrolledFrame(self, autohide=True)
        self.scrollable.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.scrollable_frame = self.scrollable

        self.cards = {}

        # Setup menu bar
        self.setup_menubar()

        # Load existing data
        self.load_data()

    def setup_menubar(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Data", command=self.save_data)
        file_menu.add_command(label="Load Data", command=self.load_data)
        file_menu.add_separator()
        file_menu.add_command(label="Export to JSON", command=self.export_json)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def setup_search(self, parent_frame):
        search_frame = ttk.Frame(parent_frame)
        search_frame.pack(side="left", padx=(20, 0), fill="x", expand=True)

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            search_frame,
            bootstyle="secondary",
            textvariable=self.search_var,
        )
        setup_entry_placeholder(
            self.search_entry, "Cari issue atau detail...", self.search_var
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", self.filter_cards)

        # Clear search button
        ttk.Button(
            search_frame,
            text="✕",
            width=3,
            bootstyle="light",
            command=self.clear_search,
        ).pack(side="right", padx=(5, 0))

    def filter_cards(self, event=None):
        search_value = self.search_var.get()
        if getattr(getattr(self, "search_entry", None), "_placeholder_active", False):
            search_value = ""
        search_term = search_value.strip().lower()
        for card in self.cards.values():
            card_data = card.get_data()
            if not card_data:
                card.pack_forget()
                continue

            # Search in issue and details
            issue_match = search_term in card_data.get("issue", "").lower()
            detail_match = any(
                search_term in detail.get("detail", "").lower()
                for detail in card_data.get("details", [])
            )
            action_match = any(
                search_term in action.lower()
                for detail in card_data.get("details", [])
                for action in detail.get("actions", [])
            )

            if search_term and (issue_match or detail_match or action_match):
                card.pack(fill="x", pady=10, padx=5, ipadx=5, ipady=5)
            elif not search_term:
                card.pack(fill="x", pady=10, padx=5, ipadx=5, ipady=5)
            else:
                card.pack_forget()

    def clear_search(self):
        self.search_var.set("")
        if hasattr(self, "search_entry"):
            self.search_entry.delete(0, "end")
            if hasattr(self.search_entry, "_placeholder_focus_out"):
                self.search_entry._placeholder_focus_out(None)
        self.filter_cards()

    def add_new_card(self):
        card = IssueCard(self.scrollable_frame, on_delete=self.remove_card)
        card.pack(fill="x", pady=10, padx=5, ipadx=5, ipady=5)
        self.cards[card.card_id] = card
        return card

    def remove_card(self, card_id):
        if card_id in self.cards:
            del self.cards[card_id]

    def show_all_data(self):
        print("\n" + "=" * 70)
        print("DATA SEMUA CARD")
        print("=" * 70)
        valid_cards = [c for c in self.cards.values() if c.get_data()]

        if not valid_cards:
            print("Tidak ada data card yang valid.")
            print("=" * 70)
            return

        for idx, card in enumerate(valid_cards, 1):
            data = card.get_data()
            print(f"CARD {idx}")
            print(f"ID     : {data['id']}")
            print(f"Issue  : {data['issue']}")
            print(f"Status : {data.get('status', 'open')}")
            for d_idx, detail in enumerate(data["details"], 1):
                print(f"Detail {d_idx}: {detail['detail']}")
                if detail["actions"]:
                    print("   Actions:")
                    for a_idx, action in enumerate(detail["actions"], 1):
                        print(f"      {a_idx}. {action}")
                else:
                    print("   Actions: (tidak ada)")
            print("-" * 70)
        print(f"Total Card: {len(valid_cards)}\n")

    def save_data(self):
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "cards": [
                    card.get_data() for card in self.cards.values() if card.get_data()
                ],
            }
            with open("issue_tracker_backup.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("Data saved successfully!")
        except Exception as e:
            print(f"Error saving data: {e}")

    def load_data(self):
        try:
            with open("issue_tracker_backup.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                # Clear existing cards
                for card_id in list(self.cards.keys()):
                    self.cards[card_id].destroy()
                    del self.cards[card_id]

                # Load new cards
                for card_data in data.get("cards", []):
                    card = self.add_new_card()

                    # Set issue
                    if card_data.get("issue"):
                        card.issue_entry.delete(0, "end")
                        card.issue_entry.insert(0, card_data["issue"])
                        card.issue_entry.configure(foreground="black")
                        card.issue_entry._placeholder_active = False

                    # Set status
                    if card_data.get("status"):
                        card.status_var.set(card_data["status"])

                    # Clear default detail items if any and load details
                    for detail_item in card.detail_items[:]:
                        detail_item.destroy()
                        card.detail_items.remove(detail_item)

                    # Load details
                    for detail_data in card_data.get("details", []):
                        detail_item = card.add_detail_item()
                        detail_item.textbox.delete("1.0", "end")
                        detail_item.textbox.insert("1.0", detail_data["detail"])
                        detail_item.textbox.config(foreground="black")
                        detail_item._placeholder_active = False

                        # Clear default action and load actions
                        for action_item in detail_item.action_items[:]:
                            action_item.destroy()
                            detail_item.action_items.remove(action_item)

                        for action_text in detail_data.get("actions", []):
                            action_item = detail_item.add_action()
                            action_item.entry.delete(0, "end")
                            action_item.entry.insert(0, action_text)
                            action_item.entry.configure(foreground="black")
                            action_item.entry._placeholder_active = False

                print("Data loaded successfully!")
                print(f"Loaded {len(data.get('cards', []))} cards")
        except FileNotFoundError:
            print("No saved data found. Starting with empty tracker.")
            # Add one empty card if no data exists
            if not self.cards:
                self.add_new_card()
        except Exception as e:
            print(f"Error loading data: {e}")
            # Add one empty card if loading fails
            if not self.cards:
                self.add_new_card()

    def export_json(self):
        try:
            filename = f"issue_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            data = {
                "timestamp": datetime.now().isoformat(),
                "cards": [
                    card.get_data() for card in self.cards.values() if card.get_data()
                ],
            }
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Data exported to {filename}")
        except Exception as e:
            print(f"Error exporting data: {e}")

    def show_about(self):
        about_window = ttk.Toplevel(self)
        about_window.title("About")
        about_window.geometry("300x200")
        about_window.resizable(False, False)

        about_text = """
Issue Tracker App

Version: 1.0
Built with ttkbootstrap

Features:
• Hierarchical issue tracking
• Data persistence
• Search and filter
• Status tracking
• JSON export
        """

        ttk.Label(about_window, text=about_text.strip(), justify="left").pack(
            padx=20, pady=20
        )
        ttk.Button(about_window, text="Close", command=about_window.destroy).pack(
            pady=10
        )


if __name__ == "__main__":
    app = App()
    app.mainloop()
