import csv
from tkinter import filedialog, messagebox
from typing import Callable, List

import customtkinter as ctk

# Pengaturan tema
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class Card(ctk.CTkFrame):
    def __init__(self, master, on_delete: Callable[[], None], **kwargs):
        super().__init__(
            master,
            corner_radius=12,
            fg_color=("gray92", "gray17"),
            border_width=2,
            border_color=("gray70", "gray30"),
            **kwargs,
        )

        self.on_delete = on_delete

        # --- Input Fields ---
        labels = ["Nama", "Email", "Catatan (bullet list)"]
        self.entries = []

        # Baris 1 & 2: CTkEntry
        for i in range(2):
            lbl = ctk.CTkLabel(
                self, text=labels[i] + ":", font=ctk.CTkFont(weight="bold")
            )
            ent = ctk.CTkEntry(
                self, placeholder_text=f"Masukkan {labels[i].lower()}..."
            )
            lbl.grid(row=i, column=0, padx=(15, 5), pady=(12, 6), sticky="w")
            ent.grid(row=i, column=1, padx=(0, 15), pady=(12, 6), sticky="ew")
            self.entries.append(ent)

        # Baris 3: CTkTextbox dengan AUTO BULLET saat Enter
        lbl3 = ctk.CTkLabel(self, text=labels[2] + ":", font=ctk.CTkFont(weight="bold"))
        self.textbox = ctk.CTkTextbox(
            self, height=100, wrap="word", font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        lbl3.grid(row=2, column=0, padx=(15, 5), pady=(12, 6), sticky="nw")
        self.textbox.grid(row=2, column=1, padx=(0, 15), pady=(12, 6), sticky="ew")

        # === FITUR AUTO BULLET ===
        self.textbox.bind("<Return>", self._insert_bullet)
        self.textbox.bind("<KeyRelease>", self._prevent_default_enter, add="+")

        # Inisialisasi dengan bullet pertama
        self.textbox.insert("0.0", "- ")
        self.textbox.focus_set()

        # --- Tombol Hapus ---
        delete_btn = ctk.CTkButton(
            self,
            text="Hapus Card",
            width=120,
            fg_color="#c0392b",
            hover_color="#a93226",
            command=self._delete,
        )
        delete_btn.grid(
            row=3, column=0, columnspan=2, pady=(15, 15), sticky="e", padx=15
        )

        # Layout responsif
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

    # ------------------------------------------------------------------
    def _insert_bullet(self, event=None):
        """Sisipkan bullet baru saat Enter ditekan"""
        self.textbox.insert("insert", "\n- ")
        return "break"  # Cegah Enter default (double newline)

    # ------------------------------------------------------------------
    def _prevent_default_enter(self, event=None):
        """Cegah baris kosong ganda atau Enter biasa"""
        if event.keysym == "Return":
            return "break"

    # ------------------------------------------------------------------
    def _delete(self):
        if self.on_delete:
            self.on_delete()

    # ------------------------------------------------------------------
    def get_values(self):
        values: List[str] = [
            entry.get() for entry in self.entries if isinstance(entry, ctk.CTkEntry)
        ]
        values.append(self.textbox.get("0.0", "end").strip())
        return values


# ======================================================================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CustomTkinter + Auto Bullet + Export CSV")
        self.geometry("700x800")
        self.minsize(600, 500)

        # Scrollable container
        self.scrollable = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable.pack(fill="both", expand=True, padx=20, pady=20)

        self.cards: List[Card] = []

        # Tombol tambah card
        add_btn = ctk.CTkButton(
            self,
            text="+ Tambah Card Baru",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#27ae60",
            hover_color="#1e8449",
            command=self.add_card,
        )
        add_btn.pack(pady=(0, 10), padx=20, fill="x")

        # === FITUR EXPORT CSV BARU ===
        export_btn = ctk.CTkButton(
            self,
            text="📊 Export ke CSV",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#3498db",
            hover_color="#2980b9",
            command=self.export_csv,
        )
        export_btn.pack(pady=(0, 15), padx=20, fill="x")

        # Mulai dengan 1 card
        self.add_card()

    # ------------------------------------------------------------------
    def add_card(self):
        card = Card(
            master=self.scrollable, on_delete=lambda c=Card: self.remove_card(c)
        )
        card.pack(fill="x", pady=10, padx=5)
        self.cards.append(card)

    # ------------------------------------------------------------------
    def remove_card(self, card: Card):
        if card in self.cards:
            self.cards.remove(card)
            card.destroy()

    # ------------------------------------------------------------------
    def export_csv(self):
        """Export semua card ke CSV"""
        if not self.cards:
            messagebox.showwarning("Peringatan", "Tidak ada data untuk diexport!")
            return

        # Kumpulkan data dari semua card
        data = []
        for card in self.cards:
            values = card.get_values()
            if values[0].strip():  # Hanya export jika Nama tidak kosong
                data.append(values)

        if not data:
            messagebox.showwarning("Peringatan", "Tidak ada data valid untuk diexport!")
            return

        # Dialog save file
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Simpan CSV",
        )

        if filename:
            try:
                with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                    writer = csv.writer(csvfile)
                    # Header
                    writer.writerow(["Nama", "Email", "Catatan"])
                    # Data
                    writer.writerows(data)

                messagebox.showinfo("Sukses", f"Data diexport ke:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Gagal export: {str(e)}")


# ======================================================================
if __name__ == "__main__":
    app = App()
    app.mainloop()
