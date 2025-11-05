import uuid
from tkinter import Menu

import customtkinter as ctk

# ----------------------------------------------------------------------
# Appearance
# ----------------------------------------------------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ----------------------------------------------------------------------
# Action Item (klik kanan -> delete)
# ----------------------------------------------------------------------
class ActionItem(ctk.CTkFrame):
    def __init__(self, master, on_remove=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_remove = on_remove

        self.entry = ctk.CTkEntry(self, placeholder_text="Tindakan...")
        self.entry.pack(side="left", fill="x", expand=True, padx=(20, 0))

        # Klik kanan pada entry
        self.entry.bind("<Button-3>", self.show_context_menu)
        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(label="Delete", command=self.delete_self)

    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def delete_self(self):
        if self.on_remove:
            self.on_remove(self)
        self.destroy()

    def get_text(self):
        return self.entry.get().strip()


# ----------------------------------------------------------------------
# Detail Item (klik kanan -> delete)
# ----------------------------------------------------------------------
class DetailItem(ctk.CTkFrame):
    def __init__(self, master, on_remove=None, **kwargs):
        super().__init__(master, fg_color="#333333", corner_radius=8, **kwargs)
        self.on_remove = on_remove
        self.action_items = []

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(8, 5))

        self.textbox = ctk.CTkTextbox(header, height=50)
        self.textbox.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Placeholder
        self.placeholder = "Masukkan detail..."
        self.textbox.insert("0.0", self.placeholder)
        self.textbox.configure(text_color="#888888")
        self.textbox.bind("<FocusIn>", self.on_focus_in)
        self.textbox.bind("<FocusOut>", self.on_focus_out)

        # + Action Button
        add_btn = ctk.CTkButton(
            header,
            text="+ Action",
            width=80,
            fg_color="#ff9900",
            hover_color="#e68a00",
            command=self.add_action,
        )
        add_btn.pack(side="right")

        # Klik kanan pada textbox
        self.textbox.bind("<Button-3>", self.show_context_menu)

        # Action container (dengan indentasi)
        self.action_container = ctk.CTkFrame(self, fg_color="transparent")
        self.action_container.pack(fill="x", padx=(35, 15), pady=(0, 8))

        # Tambah action pertama
        self.add_action()

        # Context menu
        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(label="Delete Detail", command=self.delete_self)

    def on_focus_in(self, event):
        if self.textbox.get("0.0", "end").strip() == self.placeholder:
            self.textbox.delete("0.0", "end")
            self.textbox.configure(text_color="#ffffff")

    def on_focus_out(self, event):
        if not self.textbox.get("0.0", "end").strip():
            self.textbox.insert("0.0", self.placeholder)
            self.textbox.configure(text_color="#888888")

    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def add_action(self):
        item = ActionItem(self.action_container, on_remove=self.remove_action)
        item.pack(fill="x", pady=2)
        self.action_items.append(item)

    def remove_action(self, item):
        if item in self.action_items:
            self.action_items.remove(item)

    def delete_self(self):
        if self.on_remove:
            self.on_remove(self)
        self.destroy()

    def get_data(self):
        detail_text = self.textbox.get("0.0", "end").strip()
        if detail_text == self.placeholder:
            detail_text = ""
        actions = [a.get_text() for a in self.action_items if a.get_text()]
        return {"detail": detail_text, "actions": actions} if detail_text else None


# ----------------------------------------------------------------------
# Issue Card
# ----------------------------------------------------------------------
class IssueCard(ctk.CTkFrame):
    def __init__(self, master, on_delete=None, **kwargs):
        super().__init__(
            master,
            corner_radius=12,
            fg_color="#2b2b2b",
            border_width=2,
            border_color="#3a3a3a",
            **kwargs,
        )
        self.card_id = str(uuid.uuid4())
        self.on_delete = on_delete
        self.detail_items = []

        # Issue Row
        issue_frame = ctk.CTkFrame(self, fg_color="transparent")
        issue_frame.pack(fill="x", padx=15, pady=(15, 8))

        ctk.CTkLabel(issue_frame, text="Issue:", width=60, anchor="w").pack(side="left")
        self.issue_entry = ctk.CTkEntry(
            issue_frame, placeholder_text="Masukkan issue..."
        )
        self.issue_entry.pack(side="left", fill="x", expand=True, padx=(5, 8))

        # + Detail Button
        add_detail_btn = ctk.CTkButton(
            issue_frame,
            text="+ Detail",
            width=80,
            fg_color="#00b300",
            hover_color="#009900",
            command=self.add_detail_item,
        )
        add_detail_btn.pack(side="right")

        # Detail Container
        self.detail_container = ctk.CTkFrame(self, fg_color="transparent")
        self.detail_container.pack(fill="x", padx=15, pady=(0, 10))

        # Tambah detail pertama
        self.add_detail_item()

        # Hapus Card Button
        del_btn = ctk.CTkButton(
            self,
            text="Hapus Card",
            width=100,
            fg_color="transparent",
            border_width=2,
            border_color="#ff4444",
            text_color="#ff4444",
            hover_color="#ff4444",
            command=self.delete_card,
        )
        del_btn.pack(anchor="e", padx=15, pady=(0, 12))

        # Klik kanan pada card → hapus card
        self.bind("<Button-3>", self.show_card_menu)
        self.card_menu = Menu(self, tearoff=0)
        self.card_menu.add_command(label="Delete Card", command=self.delete_card)

    def show_card_menu(self, event):
        # Cek apakah klik di area kosong (bukan widget lain)
        widget = event.widget
        if widget in (self, self.detail_container):
            try:
                self.card_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.card_menu.grab_release()

    def add_detail_item(self):
        item = DetailItem(self.detail_container, on_remove=self.remove_detail_item)
        item.pack(fill="x", pady=(3, 0))
        self.detail_items.append(item)

    def remove_detail_item(self, item):
        if item in self.detail_items:
            self.detail_items.remove(item)

    def delete_card(self):
        if self.on_delete:
            self.on_delete(self.card_id)
        self.destroy()

    def get_data(self):
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
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Issue Tracker – Clean Layout")
        self.geometry("820x880")
        self.minsize(720, 600)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(
            header, text="Issue Tracker", font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(
            btn_frame,
            text="+ Tambah Card",
            command=self.add_new_card,
            width=150,
            fg_color="#00b300",
            hover_color="#009900",
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame, text="Tampilkan Data", command=self.show_all_data, width=150
        ).pack(side="right")

        # Scrollable
        self.scrollable = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.cards = {}
        self.add_new_card()

    def add_new_card(self):
        card = IssueCard(self.scrollable, on_delete=self.remove_card)
        card.pack(fill="x", pady=10, padx=5)
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
