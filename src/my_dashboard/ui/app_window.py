"""Main application window implementation."""

from __future__ import annotations

import tkinter as tk
from tkinter import DISABLED, NORMAL, RIGHT, S, messagebox
from typing import Optional, Set

import httpx
import pandas as pd
import qrcode
import ttkbootstrap as ttk
from async_tkinter_loop import async_handler
from PIL import ImageTk
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tableview import Tableview
from ttkbootstrap.toast import ToastNotification

from ..components.editble_tableview import EditableTableView
from ..components.issue_card import IssueCard
from ..components.sidebar import Sidebar
from ..components.target_editor import TargetEditor
from ..services.achievement_service import (
    compute_row_updates,
    fetch_actual_metrics,
    load_target_shift,
)
from ..services.card_service import append_cards_to_csv, build_card_rows
from ..services.spa_service import SpaScraper
from ..utils.constants import HEADERS, NTLM_AUTH
from ..utils.csvhandle import get_targets_file_path
from ..utils.helpers import read_config, resource_path


class App(ttk.Window):
    def __init__(self):
        super().__init__(themename="superhero")
        self.title("Issue Tracker - Clean Layout")
        self.geometry("1220x660")
        self.minsize(1220, 620)
        self.place_window_center()
        self.iconbitmap(resource_path("assets/c5_spa.ico"))

        self.data_config = read_config()

        self.selected_shift = tk.StringVar()
        self.progressbar = None
        self.time_period = None

        self._active_toasts: Set[ToastNotification] = set()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.spa_scraper = SpaScraper("spa.html")
        self.target_editor: Optional[TargetEditor] = None
        self.data_window: Optional[ttk.Toplevel] = None

        self._build_layout()

    def _build_layout(self):
        self.sidebar = Sidebar(self)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.btn_target.configure(command=self.show_target_editor)
        self.sidebar.btn_get_data.configure(command=self.get_data)
        self.sidebar.btn_result.configure(
            command=self.update_achievement_target_from_csv
        )
        self.sidebar.btn_save.configure(command=self.save_data_cards_to_csv)

        self.sidebar.lu.configure(
            values=sorted(self.data_config.get("DEFAULT", "link_up").split(","))
        )
        self.sidebar.lu.current(0)

        self.main_view = ttk.Frame(self)
        self.main_view.pack(side="left", fill="both", expand=True)

        self.header_top = ttk.Frame(self.main_view)
        self.header_top.pack(fill="x", expand=False, padx=10, pady=(5, 0))

        self.progressbar = ttk.Progressbar(
            self.header_top,
            mode="indeterminate",
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
        self.issue_table.view.bind("<Double-1>", self.on_table_double_click)

        self.right_frame = ttk.Frame(self.main_content)
        self.right_frame.pack(side="right", fill="both", expand=True)

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

        ttk.Button(
            btn_frame,
            text="+ Tambah Card",
            command=self.add_new_card,
            width=15,
            bootstyle="success",
        ).pack(side="bottom", anchor=S, padx=(0, 0), pady=(0, 5))

        self.check_table = ttk.Checkbutton(
            btn_frame,
            text="Table Data",
            width=15,
            bootstyle="primary",
        )
        self.check_table.pack(side="bottom", anchor=S, padx=(0, 0), pady=(0, 25))

        ttk.Button(
            btn_frame,
            text="Clear Cards",
            command=self.clear_data_cards,
            width=15,
            bootstyle="primary",
        ).pack(side="bottom", anchor=S, padx=(0, 0), pady=(0, 5))

        ttk.Button(
            btn_frame,
            text="Tampilkan Data",
            command=self.show_all_data,
            width=15,
            bootstyle="primary",
        ).pack(side="bottom", anchor=S, padx=(0, 0), pady=(0, 5))

        self.scrollable = ScrolledFrame(self.right_frame, autohide=True)
        self.scrollable.pack(fill="both", expand=True, padx=5, pady=(0, 20))
        self.scrollable_frame = self.scrollable
        self.cards = {}
        self.data_window = None
        self.add_new_card()

        self._initialize_issue_table(self.spa_scraper)

    def _initialize_issue_table(self, scraper: SpaScraper):
        issue_df = scraper.get_issue_dataframe()
        if issue_df.empty:
            return

        self.issue_table.delete_rows()
        self.issue_table.build_table_data(
            issue_df.columns.to_list(), issue_df.values.tolist()
        )
        self.issue_table.reset_table()

    def add_new_card(self, issue_text: Optional[str] = None):
        card = IssueCard(self.scrollable_frame, on_delete=self.remove_card)
        card.pack(fill="x", pady=10, padx=5, ipadx=5, ipady=5)
        self.cards[card.card_id] = card
        if issue_text:
            card.set_issue(issue_text)
        card.issue_entry.focus_set()

    def remove_card(self, card_id):
        if card_id in self.cards:
            del self.cards[card_id]

    def on_table_double_click(self, event: tk.Event):
        row_id = event.widget.identify_row(event.y)
        if not row_id:
            return
        event.widget.selection_set(row_id)
        values = event.widget.item(row_id, "values")
        if len(values) < 2:
            return
        issue_text = str(values[1]).strip()
        if not issue_text:
            return
        self.add_new_card(issue_text=issue_text)

    def _on_data_window_close(self):
        if self.data_window and self.data_window.winfo_exists():
            self.data_window.destroy()
        self.data_window = None

    def show_all_data(self):
        card_entries = [card.get_data() for card in self.cards.values()]
        card_entries = [entry for entry in card_entries if entry]

        if not card_entries:
            messagebox.showinfo("Data Kosong", "Tidak ada data card untuk ditampilkan.")
            return

        if self.data_window and self.data_window.winfo_exists():
            self.data_window.destroy()

        self.data_window = ttk.Toplevel(self)
        self.data_window.title("Data Semua Card")
        self.data_window.geometry("900x530")
        self.data_window.minsize(520, 400)
        self.data_window.protocol("WM_DELETE_WINDOW", self._on_data_window_close)

        data_text = ttk.Text(
            self.data_window,
            font=("consolas", 10),
            width=50,
        )
        data_text.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)

        data_header = ["METRIK", "TARGET", "AKTUAL"]
        data_table = [tuple(row.values) for row in self.achieve_table.tablerows]
        if self.check_table.instate(["selected"]):
            from tabulate import tabulate

            data_text.insert(
                "end",
                tabulate(
                    data_table,
                    data_header,
                    tablefmt="pretty",
                    stralign="center",
                )
                + "\n",
            )

        for data in card_entries:
            data_text.insert("end", f"\n*{data['issue']}*\n")
            for detail in data["details"]:
                data_text.insert("end", f"> {detail['detail']}\n")
                for action in detail["actions"]:
                    data_text.insert("end", f"- {action or '-'}\n")

        qr = qrcode.QRCode(
            box_size=10,
            border=4,
        )
        qr.add_data(data_text.get("1.0", "end").encode("utf-8"))
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="orange")
        qr_img = qr_img.resize((500, 500))
        qr_img_tk = ImageTk.PhotoImage(qr_img)
        qr_label = ttk.Label(self.data_window, image=qr_img_tk)
        qr_label.image = qr_img_tk
        qr_label.pack(side="right", pady=10, padx=10, anchor="n")

        self.data_window.focus()

    @async_handler
    async def get_data(self):
        try:
            self.progressbar.start()
            self.sidebar.btn_get_data.configure(state=DISABLED)

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    "http://127.0.0.1:5500/spa.html",
                    follow_redirects=True,
                    headers=HEADERS,
                    auth=NTLM_AUTH,
                )
            if response.status_code == 200:
                spa = SpaScraper(response.text, is_html=True)
                df = spa.get_issue_dataframe()
                self.time_period.configure(
                    text=spa.get_actual_data_metric().get("RANGE", "")
                )

                head = df.columns.to_list()
                data = df.values.tolist()
                self.issue_table.columnconfigure(0, weight=1)
                self.issue_table.columnconfigure(1, weight=1)
                self.issue_table.build_table_data(head, data)
                self.issue_table.reset_table()

                self._show_toast(
                    title="Berhasil",
                    message="Data berhasil diambil.",
                    bootstyle="success",
                    duration=3000,
                )
            else:
                self._show_toast(
                    title="Kesalahan",
                    message=f"Error Code {response.status_code}: {response.text}",
                    bootstyle="danger",
                    duration=3000,
                )
        except httpx.HTTPError as e:
            self._show_toast(
                title="HTTP Error",
                message=str(e),
                bootstyle="danger",
                duration=3000,
            )
        finally:
            self.progressbar.stop()
            self.sidebar.btn_get_data.configure(state=NORMAL)

    def _show_toast(self, **kwargs):
        if not self.winfo_exists():
            return
        toast = ToastNotification(**kwargs)
        try:
            toast.show_toast()
        except tk.TclError:
            return

        toplevel = getattr(toast, "toplevel", None)
        if toplevel:
            toplevel.bind(
                "<Destroy>",
                lambda *_: self._active_toasts.discard(toast),
            )
        self._active_toasts.add(toast)

    def _cleanup_toasts(self):
        for toast in list(self._active_toasts):
            toplevel = getattr(toast, "toplevel", None)
            if not toplevel:
                continue
            try:
                toplevel.destroy()
            except tk.TclError:
                pass
        self._active_toasts.clear()

    def _on_close(self):
        self._cleanup_toasts()
        self.destroy()

    def update_achievement_table(self, show_message: bool = False) -> bool:
        shift_value = self.sidebar.select_shift.get()
        if not shift_value:
            if show_message:
                messagebox.showwarning(
                    "Peringatan", "Silakan pilih shift sebelum memperbarui target."
                )
            return False

        lu_value = self.sidebar.lu.get().strip()
        if not lu_value:
            if show_message:
                messagebox.showwarning(
                    "Peringatan",
                    "Silakan pilih Link Up sebelum memperbarui target.",
                )
            return False

        func_location = self.sidebar.func_location.get()

        try:
            shift_number = int(shift_value.split()[-1])
        except (ValueError, IndexError):
            if show_message:
                messagebox.showerror(
                    "Kesalahan",
                    "Format shift tidak valid. Gunakan format 'Shift X'.",
                )
            return False

        try:
            target_shift = load_target_shift(lu_value, func_location, shift_number)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            if show_message:
                messagebox.showerror(
                    "Kesalahan",
                    "Gagal membaca file target. Periksa konfigurasi Link Up/Function.",
                )
            return False
        except KeyError as exc:
            if show_message:
                messagebox.showerror("Kesalahan", str(exc))
            return False

        metric_names = [row.values[0] for row in self.achieve_table.tablerows]
        self.spa_scraper = SpaScraper("spa.html")
        actual_values, actual_data = fetch_actual_metrics(
            self.spa_scraper, metric_names
        )
        self.time_period.configure(text=actual_data.get("RANGE", ""))

        updates = compute_row_updates(
            self.achieve_table.tablerows,
            target_shift.tolist(),
            actual_values,
        )

        for row, values in updates:
            row.values = values
            self.achieve_table.view.item(row.iid, values=values)

        if not updates:
            if show_message:
                messagebox.showwarning(
                    "Informasi",
                    "Tidak ada baris target yang diperbarui. Pastikan CSV berisi data.",
                )
            return False

        self.achieve_table.rowdata = [
            tuple(row.values) for row in self.achieve_table.tablerows
        ]

        if show_message:
            messagebox.showinfo(
                "Berhasil",
                f"Target dan aktual shift {shift_number} berhasil diperbarui dari CSV dan SPA.",
            )

        return True

    @async_handler
    async def update_achievement_target_from_csv(self):
        self.progressbar.start()
        try:
            label_text = (
                f"{self.sidebar.lu.get()} {self.sidebar.func_location.get()}"
            ).strip()
            if label_text:
                self.achievement_frame.configure(
                    labelwidget=ttk.Label(
                        self.header_frame,
                        text=label_text,
                        font=("sans-serif", 10, "bold"),
                    ),
                    style="warning.TLabelframe",
                )

            self.update_achievement_table(show_message=True)
        finally:
            self.progressbar.stop()

    @async_handler
    async def save_data_cards_to_csv(self):
        card_rows = build_card_rows(card.get_data() for card in self.cards.values())

        if not card_rows:
            messagebox.showinfo(
                "Data Kosong", "Tidak ada data card yang dapat disimpan ke CSV."
            )
            return

        try:
            file_path = append_cards_to_csv(card_rows)
        except Exception as exc:
            messagebox.showerror(
                "Kesalahan", f"Gagal menyimpan data card ke CSV.\n{exc}"
            )
            return

        messagebox.showinfo(
            "Berhasil", f"Data card berhasil ditambahkan ke file:\n{file_path}"
        )

    def clear_data_cards(self):
        if not self.cards:
            messagebox.showinfo("Informasi", "Tidak ada card untuk dihapus.")
            return

        if not messagebox.askyesno(
            "Konfirmasi", "Hapus semua card yang sedang ditampilkan?"
        ):
            return

        for card in list(self.cards.values()):
            card.destroy()
        self.cards.clear()

        self.add_new_card()

    def show_target_editor(self):
        if self.target_editor and self.target_editor.winfo_exists():
            self.target_editor.destroy()

        lu_value = self.sidebar.lu.get()
        if not lu_value:
            messagebox.showwarning(
                "Peringatan", "Silakan pilih Link Up terlebih dahulu."
            )
            return

        func_location = self.sidebar.func_location.get()
        file_path = get_targets_file_path(lu_value.strip("LU"), func_location)

        self.target_editor = TargetEditor(file_path)
        self.target_editor.grab_set()
