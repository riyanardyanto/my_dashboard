"""Main application window implementation."""

from __future__ import annotations

import tkinter as tk
from tkinter import DISABLED, NORMAL, messagebox
from typing import Optional, Set

import httpx
import pandas as pd
import qrcode
import ttkbootstrap as ttk
from async_tkinter_loop import async_handler
from PIL import ImageTk
from ttkbootstrap.toast import ToastNotification

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
from .dashboard_view import DashboardView


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
        self._active_toasts: Set[ToastNotification] = set()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.spa_scraper = SpaScraper("spa.html")
        self.target_editor: Optional[TargetEditor] = None
        self.data_window: Optional[ttk.Toplevel] = None
        self.view = DashboardView(self)
        self.sidebar = self.view.sidebar
        self.progressbar = self.view.progressbar
        self.time_period = self.view.time_period
        self.issue_table = self.view.issue_table
        self.achieve_table = self.view.achieve_table
        self.achievement_frame = self.view.achievement_frame
        self.header_frame = self.view.header_frame
        self.check_table = self.view.check_table

        self.view.configure_card_actions(
            on_add_card=self.add_new_card,
            on_show_cards=self.show_all_data,
            on_clear_cards=self.clear_data_cards,
        )

        self.sidebar.btn_target.configure(command=self.show_target_editor)
        self.sidebar.btn_get_data.configure(command=self.get_data)
        self.sidebar.btn_result.configure(
            command=self.update_achievement_target_from_csv
        )
        self.sidebar.btn_save.configure(command=self.save_data_cards_to_csv)

        link_up_values = sorted(self.data_config.get("DEFAULT", "link_up").split(","))
        self.sidebar.lu.configure(values=link_up_values)
        if link_up_values:
            self.sidebar.lu.current(0)

        self.issue_table.view.bind("<Double-1>", self.on_table_double_click)

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
        return self.view.add_card(issue_text)

    def remove_card(self, card_id):
        self.view.remove_card(card_id)

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
        card_entries = self.view.get_card_entries()

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
        card_rows = build_card_rows(self.view.iter_card_data())

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
        if not self.view.cards:
            messagebox.showinfo("Informasi", "Tidak ada card untuk dihapus.")
            return

        if not messagebox.askyesno(
            "Konfirmasi", "Hapus semua card yang sedang ditampilkan?"
        ):
            return

        self.view.clear_cards()

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
