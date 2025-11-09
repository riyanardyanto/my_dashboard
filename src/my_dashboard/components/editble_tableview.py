import csv
import tkinter as tk

import ttkbootstrap as ttk
from ttkbootstrap.constants import CENTER, INFO, PRIMARY, SUCCESS, E, W
from ttkbootstrap.tableview import Tableview
from ttkbootstrap.toast import ToastNotification


class EditableTableView(Tableview):
    """
    Tableview dengan fitur:
    - Editable cells (double-click)
    - Custom row height
    - Validasi input
    - Sinkronisasi data otomatis
    """

    def __init__(
        self,
        master=None,
        coldata=None,
        rowdata=None,
        editable_columns=None,
        row_height=30,
        paginated=False,
        searchable=False,
        bootstyle=PRIMARY,
        **kw,
    ):
        """
        Inisialisasi langsung sebagai Tableview (bukan membuat instance baru).
        """
        # Normalisasi coldata agar kompatibel
        coldata = self._normalize_coldata(coldata or [])
        self._col_headers = [col.get("text", "") for col in coldata]

        # Siapkan penampung data sebelum inisialisasi parent
        self.rowdata = []

        # Inisialisasi Tableview (parent: master)
        super().__init__(
            master=master,
            coldata=coldata,
            rowdata=rowdata or [],
            paginated=paginated,
            searchable=searchable,
            bootstyle=bootstyle,
            **kw,
        )

        # Simpan referensi
        if not self.rowdata:
            self.rowdata = [tuple(row) for row in (rowdata or [])]
        else:
            self.rowdata = [tuple(row.values) for row in self.tablerows]
        self.editable_columns = editable_columns or list(range(1, len(coldata)))
        self.entry = None
        self.current_iid = None
        self.current_col = None
        self.paste_start_iid = None
        self.paste_start_col = None

        # Set row height
        self._set_row_height(row_height)

        # Bind events
        self.view.bind("<Double-1>", self._on_double_click)
        self.view.bind("<Button-1>", self._remember_cell_position, add="+")
        for sequence in ("<Control-v>", "<Control-V>", "<<Paste>>"):
            self.view.bind(sequence, self._paste_from_clipboard, add="+")

    def _set_row_height(self, height):
        """Set row height via custom style."""
        style = ttk.Style()
        base_style = self.view.cget("style") or "Treeview"

        # Salin konfigurasi style dasar agar tampilan konsisten
        style_name = f"EditableTable{id(self)}.{base_style}"
        base_config = style.configure(base_style)
        if base_config:
            style.configure(style_name, **base_config)
        base_map = style.map(base_style)
        if base_map:
            style.map(style_name, **base_map)
        base_layout = style.layout(base_style)
        if base_layout:
            style.layout(style_name, base_layout)

        style.configure(style_name, rowheight=height)
        self.view.configure(style=style_name)

        # Terapkan auto align agar sesuai kebiasaan Tableview
        if getattr(self, "_autoalign", False):
            self.autoalign_columns()

    def _normalize_coldata(self, coldata):
        """Konversi format shorthand ke dict (jika perlu)."""
        normalized = []
        for col in coldata:
            if isinstance(col, str):
                normalized.append({"text": col})
            elif isinstance(col, tuple):
                text, anchor = col[0], col[1] if len(col) > 1 else "w"
                anchor_map = {"w": W, "e": E, "c": CENTER}
                normalized.append(
                    {"text": text, "anchor": anchor_map.get(anchor.lower(), W)}
                )
            elif isinstance(col, dict):
                normalized.append(col)
            else:
                normalized.append({"text": str(col)})
        return normalized

    def _on_double_click(self, event):
        """Handle double-click to edit cell."""
        tree = self.view
        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        item = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        if not item or not column:
            return

        col_idx = int(column[1:]) - 1
        if col_idx not in self.editable_columns:
            return

        # Cleanup previous entry
        if self.entry:
            self.entry.destroy()

        # Get cell bbox
        bbox = tree.bbox(item, column)
        if not bbox:
            return

        x, y, w, h = bbox
        self.current_iid = item
        self.current_col = col_idx
        self.paste_start_iid = item
        self.paste_start_col = col_idx

        # Create Entry
        style = ttk.Style()
        base_style = tree.cget("style") or "Treeview"
        entry_font = style.lookup(base_style, "font") or style.lookup(
            "Treeview", "font"
        )

        old_value = tree.item(item, "values")[col_idx]
        entry_kwargs = {
            "justify": "center" if col_idx == 1 else "left",
            "bootstyle": INFO,
        }
        if entry_font:
            entry_kwargs["font"] = entry_font

        self.entry = ttk.Entry(tree, **entry_kwargs)
        self.entry.place(x=x, y=y, width=w, height=h)
        self.entry.insert(0, str(old_value))
        self.entry.select_range(0, "end")
        self.entry.focus()

        # Bind save/cancel
        self.entry.bind("<Return>", self._save_edit)
        self.entry.bind("<FocusOut>", self._save_edit)
        self.entry.bind("<Escape>", self._cancel_edit)
        self.entry.bind("<Control-v>", self._on_entry_paste)
        self.entry.bind("<Control-V>", self._on_entry_paste)
        self.entry.bind("<<Paste>>", self._on_entry_paste)

    def _save_edit(self, event=None):
        """Save edited value."""
        if not self.entry or not self.current_iid:
            return

        new_val = self.entry.get().strip()
        if not new_val:
            self._cancel_edit()
            return

        # Validasi (contoh: kolom 1 = integer)
        # if self.current_col == 1:
        #     try:
        #         new_val = int(new_val)
        #     except ValueError:
        #         messagebox.showerror("Invalid Input", "Nilai harus berupa angka!")
        #         return

        # Update Treeview
        values = list(self.view.item(self.current_iid, "values"))
        values[self.current_col] = new_val
        self.view.item(self.current_iid, values=values)

        # Update internal rowdata
        tablerow = self.get_row(iid=self.current_iid)
        if tablerow is not None:
            tablerow.values = tuple(values)
            self.rowdata = [tuple(row.values) for row in self.tablerows]

        self._cleanup_entry()

    def _cancel_edit(self, event=None):
        """Cancel editing."""
        self._cleanup_entry()

    def _cleanup_entry(self):
        """Destroy entry and reset state."""
        if self.entry:
            self.entry.destroy()
            self.entry = None
        self.current_iid = None
        self.current_col = None

    # Optional: Tambah baris baru
    def insert_row(self, values, index="end"):
        row = super().insert_row(index=index, values=list(values))
        self.rowdata = [tuple(r.values) for r in self.tablerows]
        return row

    def save_to_csv(self, filepath, include_headers=True, encoding="utf-8"):
        """Simpan isi tabel ke CSV."""
        snapshot = [tuple(row.values) for row in self.tablerows]
        self.rowdata = snapshot

        try:
            with open(filepath, "w", encoding=encoding, newline="") as csvfile:
                writer = csv.writer(csvfile)
                if include_headers and self._col_headers:
                    writer.writerow(self._col_headers)
                writer.writerows(snapshot)
                ToastNotification(
                    title="Information",
                    message=f"Data berhasil disimpan ke {filepath!r}",
                    bootstyle="success",
                    duration=3000,
                    alert=True,
                ).show_toast()
        except OSError as exc:
            ToastNotification(
                title="Error",
                message=f"Gagal menulis CSV ke {filepath!r}: {exc}",
                bootstyle="danger",
                duration=3000,
                alert=True,
            ).show_toast()
            raise IOError(f"Gagal menulis CSV ke {filepath!r}: {exc}") from exc

    def load_from_csv(self, filepath, has_headers=True, encoding="utf-8"):
        """Muat data tabel dari CSV."""
        try:
            with open(filepath, "r", encoding=encoding, newline="") as csvfile:
                reader = csv.reader(csvfile)
                rows = [row for row in reader]
        except OSError as exc:
            raise IOError(f"Gagal membaca CSV dari {filepath!r}: {exc}") from exc

        headers = None
        if has_headers and rows:
            headers = rows.pop(0)
            if headers:
                columns = self.view["columns"]
                for idx, header in enumerate(headers):
                    if idx < len(columns):
                        self.view.heading(columns[idx], text=header)
                    else:
                        self.view.heading(f"#{idx + 1}", text=header)
                self._col_headers = headers

        target_cols = len(self._col_headers)
        if target_cols == 0 and rows:
            target_cols = len(rows[0])
            self._col_headers = ["" for _ in range(target_cols)]

        normalized_rows = []
        for row in rows:
            if target_cols:
                if len(row) < target_cols:
                    row = row + ["" for _ in range(target_cols - len(row))]
                elif len(row) > target_cols:
                    row = row[:target_cols]
            normalized_rows.append(tuple(row))

        self._cleanup_entry()
        for iid in self.view.get_children():
            self.view.delete(iid)
        if hasattr(self, "tablerows"):
            try:
                self.tablerows.clear()
            except AttributeError:
                self.tablerows[:] = []

        for values in normalized_rows:
            self.insert_row(values)

        self.rowdata = [tuple(row.values) for row in self.tablerows]
        if self.rowdata:
            children = self.view.get_children()
            if children:
                self.paste_start_iid = children[0]
            self.paste_start_col = (
                min(self.editable_columns) if self.editable_columns else 0
            )
        else:
            self.paste_start_iid = None
            self.paste_start_col = None

        return len(self.rowdata)

    def _remember_cell_position(self, event):
        """Simpan sel terakhir yang diklik untuk anchor paste."""
        tree = self.view
        item = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        if not item or not column:
            return

        col_idx = int(column[1:]) - 1
        self.paste_start_iid = item
        self.paste_start_col = col_idx

    def _paste_from_clipboard(self, event=None):
        """Tempelkan data clipboard mulai dari sel anchor."""
        try:
            raw_data = self.view.clipboard_get()
        except tk.TclError:
            return "break"

        if not raw_data:
            return "break"

        rows = [line.split("\t") for line in raw_data.splitlines()]
        if not rows:
            return "break"

        anchor_iid = self.current_iid or self.paste_start_iid or self.view.focus()
        if not anchor_iid:
            selection = self.view.selection()
            if selection:
                anchor_iid = selection[0]

        if not anchor_iid:
            return "break"

        anchor_col = self.current_col
        if anchor_col is None:
            anchor_col = self.paste_start_col
        if anchor_col is None:
            anchor_col = min(self.editable_columns) if self.editable_columns else 0

        tree_rows = list(self.view.get_children(""))
        try:
            start_index = tree_rows.index(anchor_iid)
        except ValueError:
            return "break"

        updated_any = False
        for row_offset, row_values in enumerate(rows):
            target_index = start_index + row_offset
            if target_index >= len(tree_rows):
                break

            target_iid = tree_rows[target_index]
            current_values = list(self.view.item(target_iid, "values"))
            row_updated = False
            for col_offset, cell in enumerate(row_values):
                target_col = anchor_col + col_offset
                if target_col >= len(current_values):
                    break
                if self.editable_columns and target_col not in self.editable_columns:
                    continue
                current_values[target_col] = cell.strip()
                row_updated = True

            if row_updated:
                self.view.item(target_iid, values=current_values)
                tablerow = self.get_row(iid=target_iid)
                if tablerow is not None:
                    tablerow.values = tuple(current_values)
                updated_any = True

        if updated_any:
            self.rowdata = [tuple(row.values) for row in self.tablerows]
            if self.entry:
                self._cleanup_entry()

        return "break"

    def _on_entry_paste(self, event: tk.Event):
        try:
            data = event.widget.clipboard_get()
        except tk.TclError:
            return "break"

        if "\n" in data or "\r" in data or "\t" in data:
            self._paste_from_clipboard()
            return "break"

        return None


# === CONTOH PENGGUNAAN ===
if __name__ == "__main__":
    root = ttk.Window(themename="superhero")
    root.title("Editable TableView - Fixed & Optimized")
    # root.geometry("700x500")

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

    # Gunakan langsung sebagai widget
    table = EditableTableView(
        master=root,
        coldata=coldata,
        rowdata=rowdata,
        editable_columns=[1, 2],
        row_height=30,
        paginated=False,
        # searchable=True,
        bootstyle=SUCCESS,
        autoalign=True,
        # autofit=True,
        height=6,
    )
    table.pack(fill="both", expand=True, padx=10, pady=10)

    # Tombol tambah row
    def add_new_row():
        table.insert_row(("NEW", 0, 0))

    ttk.Button(root, text="Tambah Baris", command=add_new_row, bootstyle=INFO).pack(
        pady=5
    )

    root.mainloop()
