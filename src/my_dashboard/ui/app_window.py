"""Main application window implementation."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Optional, Set

import httpx
import pandas as pd
import qrcode
import ttkbootstrap as ttk
from async_tkinter_loop import async_handler
from PIL import ImageTk
from ttkbootstrap.toast import ToastNotification

from my_dashboard.services.achievement_service import (
    compute_row_updates,
    fetch_actual_metrics,
    load_target_shift,
)

from ..components.target_editor import TargetEditor

from ..controllers import ControllerError, DashboardController
from ..utils.csvhandle import get_targets_file_path, save_user
from ..utils.helpers import get_url_period_loss_tree, read_config, resource_path
from .dashboard_view import DashboardView
from .decorators import with_button_state, with_progressbar


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

        self.controller = DashboardController()
        self.target_editor: Optional[TargetEditor] = None
        self.data_window: Optional[ttk.Toplevel] = None
        self.view = DashboardView(self)
        self.sidebar = self.view.sidebar
        self.date_entry = self.sidebar.dt
        self.progressbar = self.view.progressbar
        self.time_period = self.view.time_period
        self.issue_table = self.view.issue_table
        self.achieve_table = self.view.achieve_table
        self.achievement_frame = self.view.achievement_frame
        self.header_frame = self.view.header_frame
        self.check_table = self.view.check_table

        self.view.configure_card_actions(on_show_cards=self.show_all_data)
        self.view.target_btn.configure(command=self.show_target_editor)
        self.view.save_btn.configure(command=self.save_data_cards_to_csv)

        # self.sidebar.btn_target.configure(command=self.show_target_editor)
        self.sidebar.btn_get_data.configure(command=self.get_data_and_update_tables)
        # self.sidebar.btn_result.configure(command=self.refresh_achievement_table)
        # self.sidebar.btn_save.configure(command=self.save_data_cards_to_csv)

        link_up_values = sorted(self.data_config.get("DEFAULT", "link_up").split(","))
        self.sidebar.lu.configure(values=link_up_values)
        if link_up_values:
            self.sidebar.lu.current(0)

        self.issue_table.view.bind("<Double-1>", self.on_table_double_click)

        # self._initialize_issue_table()

    async def _initialize_stop_reason_table(self):
        issue_df = await self.controller.load_local_issue_dataframe()
        self._populate_issue_table(issue_df)

    def _populate_issue_table(self, issue_df: pd.DataFrame) -> None:
        if issue_df.empty:
            return

        self.issue_table.delete_rows()
        self.issue_table.columnconfigure(0, weight=1)
        self.issue_table.columnconfigure(1, weight=1)
        self.issue_table.build_table_data(
            issue_df.columns.to_list(), issue_df.values.tolist()
        )
        self.issue_table.reset_table()

    def _get_selected_date(self) -> str:
        if hasattr(self.date_entry, "entry"):
            return self.date_entry.entry.get()
        try:
            return self.date_entry.get_date().isoformat()  # type: ignore[call-arg]
        except AttributeError:
            return str(self.date_entry)

    @staticmethod
    def _extract_actual_record(
        data_losses: object,
    ) -> dict[str, object]:
        if isinstance(data_losses, pd.DataFrame):
            if data_losses.empty:
                return {}
            return data_losses.iloc[0].to_dict()
        if isinstance(data_losses, pd.Series):
            return data_losses.to_dict()
        if isinstance(data_losses, dict):
            return dict(data_losses)
        return {}

    @staticmethod
    def _format_http_error(exc: httpx.HTTPError, url: str) -> str:
        response = getattr(exc, "response", None)
        if response is not None:
            reason = getattr(response, "reason_phrase", "") or getattr(
                response, "reason", ""
            )
            status_line = f"{response.status_code} {reason}".strip()
            return f"{status_line}\n{exc}\nURL: {url}"

        return f"{exc.__class__.__name__}: {exc}\nURL: {url}"

    def add_new_card(self, issue_text: Optional[str] = None):
        return self.view.card_frame.add_card(issue_text)

    def remove_card(self, card_id):
        self.view.card_frame.remove_card(card_id)

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
            self._show_toast(
                title="Data Kosong",
                message="Tidak ada data card untuk ditampilkan.",
                bootstyle="info",
                duration=3000,
            )
            # messagebox.showinfo("Data Kosong", "Tidak ada data card untuk ditampilkan.")
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

        data_text.insert(
            "end",
            f"*{self.sidebar.func_location.get()} {self.sidebar.lu.get().strip('LU')}*"
            + " | "
            + f"{self._get_selected_date()}, {self.sidebar.select_shift.get()}\n",
        )

        data_header = ["METRIK", "TARGET", "AKTUAL"]
        data_table = [tuple(row.values) for row in self.achieve_table.tablerows]
        if self.check_table.instate(["selected"]):
            from tabulate import tabulate

            data_text.insert(
                "end",
                f"`{tabulate(
                    data_table,
                    data_header,
                    tablefmt="pretty",
                    stralign="left",
                    numalign="left",
                ).replace('\n','`\n`')}`"
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
    @with_button_state("btn_get_data")
    @with_progressbar
    async def get_data_and_update_tables(self):
        """Fetch data from SPA and update both issue table and achievement table."""
        # Get URL parameters
        link_up = self.sidebar.lu.get().strip("LU")
        date_entry = self._get_selected_date()
        shift_value = self.sidebar.select_shift.get().strip("Shift ")
        func_location = self.sidebar.func_location.get()[:4]

        url = self._get_url(link_up, date_entry, shift_value, func_location)
        if not url:
            return

        # Validate shift selection
        if not shift_value:
            self._show_toast(
                title="Peringatan",
                message="Silakan pilih shift terlebih dahulu.",
                bootstyle="warning",
                duration=3000,
            )
            return

        try:
            shift_number = int(shift_value)
        except ValueError:
            self._show_toast(
                title="Kesalahan",
                message="Format shift tidak valid.",
                bootstyle="danger",
                duration=3000,
            )
            return

        # Fetch remote data
        try:
            processed = await self.controller.fetch_remote_issue_data(url)
        except ControllerError as exc:
            self._show_toast(
                title="Kesalahan",
                message=str(exc),
                bootstyle="danger",
                duration=3000,
            )
            return
        except httpx.HTTPError as exc:
            self._show_toast(
                title="HTTP Error",
                message=self._format_http_error(exc, url),
                bootstyle="danger",
                duration=3000,
            )
            return
        except Exception as exc:
            self._show_toast(
                title="Kesalahan",
                message=str(exc),
                bootstyle="danger",
                duration=3000,
            )
            return

        stops_df = processed.get("stops_reason", pd.DataFrame())
        data_losses_df = processed.get("data_losses", pd.DataFrame())

        # Update issue table
        self._populate_issue_table(stops_df)

        # Extract actual data
        actual_record = self._extract_actual_record(data_losses_df)
        time_text = actual_record.get("RANGE") or actual_record.get("Time range", "")
        self.time_period.configure(text=str(time_text))

        # Update achievement frame label
        label_text = (
            f"{self.sidebar.lu.get()} {self.sidebar.func_location.get()}".strip()
        )
        if label_text:
            self.achievement_frame.configure(
                labelwidget=ttk.Label(
                    self.header_frame,
                    text=label_text,
                    font=("sans-serif", 10, "bold"),
                ),
                style="warning.TLabelframe",
            )

        # Load target data
        try:
            target_series = load_target_shift(
                self.sidebar.lu.get().strip("LU"),
                self.sidebar.func_location.get(),
                shift_number,
            )
        except (FileNotFoundError, pd.errors.EmptyDataError):
            self._show_toast(
                title="Kesalahan",
                message="Gagal membaca file target. Periksa konfigurasi Link Up/Function.",
                bootstyle="danger",
                duration=3000,
            )
            return
        except KeyError as exc:
            self._show_toast(
                title="Kesalahan",
                message=str(exc),
                bootstyle="danger",
                duration=3000,
            )
            return
        except Exception as exc:
            self._show_toast(
                title="Kesalahan",
                message=str(exc),
                bootstyle="danger",
                duration=3000,
            )
            return

        # Update achievement table
        self.update_achievement_table(
            show_message=False,
            target_data=target_series,
            actual_data=actual_record,
        )

        self._show_toast(
            title="Berhasil",
            message="Issue table dan achievement table berhasil diperbarui.",
            bootstyle="success",
            duration=3000,
        )

    @async_handler
    @with_button_state("btn_get_data")
    @with_progressbar
    async def get_data(self):
        url = self._get_url(
            self.sidebar.lu.get().strip("LU"),
            self._get_selected_date(),
            self.sidebar.select_shift.get().strip("Shift "),
            self.sidebar.func_location.get()[:4],
        )

        if not url:
            return

        try:
            processed = await self.controller.fetch_remote_issue_data(url)
        except ControllerError as exc:
            self._show_toast(
                title="Kesalahan",
                message=str(exc),
                bootstyle="danger",
                duration=3000,
            )
            return
        except httpx.HTTPError as exc:
            self._show_toast(
                title="HTTP Error",
                message=self._format_http_error(exc, url),
                bootstyle="danger",
                duration=3000,
            )
            return
        except Exception as exc:
            self._show_toast(
                title="Kesalahan",
                message=str(exc),
                bootstyle="danger",
                duration=3000,
            )
            return

        stops_df = processed.get("stops_reason", pd.DataFrame())
        data_losses_df = processed.get("data_losses", pd.DataFrame())

        self._populate_issue_table(stops_df)

        actual_record = self._extract_actual_record(data_losses_df)
        time_text = actual_record.get("RANGE") or actual_record.get("Time range", "")
        self.time_period.configure(text=str(time_text))

        self._show_toast(
            title="Berhasil",
            message=f"Data berhasil diambil dari {url}.",
            bootstyle="success",
            duration=3000,
        )

    def _get_url(self, link_up, date_entry, shift, functional_location="PACK") -> str:
        """Helper method to generate URLs based on environment."""
        if self.data_config.get("DEFAULT", "environment") == "production":
            return get_url_period_loss_tree(
                link_up, date_entry, shift, functional_location
            )

        elif self.data_config.get("DEFAULT", "environment") == "development":
            # For development or testing environment, use local HTML files
            return "http://127.0.0.1:5500/assets/spa1.html"
            # return "http://127.0.0.1:5500/assets/no_pdt.html"

        else:
            self._show_toast(
                title="Kesalahan",
                message=f"Environment {self.data_config.get('DEFAULT', 'environment')} tidak diketahui. Silakan periksa konfigurasi.",
                bootstyle="danger",
                duration=3000,
            )
            return ""

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

    def update_achievement_table(
        self,
        show_message: bool = False,
        *,
        target_data: Optional[pd.Series] = None,
        actual_data: Optional[dict[str, object]] = None,
    ) -> bool:
        shift_value = self.sidebar.select_shift.get()
        if not shift_value:
            if show_message:
                self._show_toast(
                    title="Peringatan",
                    message="Silakan pilih shift sebelum memperbarui target.",
                    bootstyle="warning",
                    duration=3000,
                )
                # messagebox.showwarning(
                #     "Peringatan", "Silakan pilih shift sebelum memperbarui target."
                # )
            return False

        lu_value = self.sidebar.lu.get().strip()
        if not lu_value:
            if show_message:
                self._show_toast(
                    title="Peringatan",
                    message="Silakan pilih Link Up sebelum memperbarui target.",
                    bootstyle="warning",
                    duration=3000,
                )
                # messagebox.showwarning(
                #     "Peringatan",
                #     "Silakan pilih Link Up sebelum memperbarui target.",
                # )
            return False

        func_location = self.sidebar.func_location.get()

        try:
            shift_number = int(shift_value.split()[-1])
        except (ValueError, IndexError):
            if show_message:
                self._show_toast(
                    title="Kesalahan",
                    message="Format shift tidak valid. Gunakan format 'Shift X'.",
                    bootstyle="danger",
                    duration=3000,
                )
                # messagebox.showerror(
                #     "Kesalahan",
                #     "Format shift tidak valid. Gunakan format 'Shift X'.",
                # )
            return False

        metric_names = [row.values[0] for row in self.achieve_table.tablerows]

        target_series = target_data
        if target_series is not None and not isinstance(target_series, pd.Series):
            target_series = pd.Series(target_series)
        if target_series is None:
            try:
                target_series = load_target_shift(lu_value, func_location, shift_number)
            except (FileNotFoundError, pd.errors.EmptyDataError):
                if show_message:
                    self._show_toast(
                        title="Kesalahan",
                        message="Gagal membaca file target. Periksa konfigurasi Link Up/Function.",
                        bootstyle="danger",
                        duration=3000,
                    )
                return False
            except KeyError as exc:
                if show_message:
                    self._show_toast(
                        title="Kesalahan",
                        message=str(exc),
                        bootstyle="danger",
                        duration=3000,
                    )
                return False

        target_values = [
            str(target_series.iloc[idx]) if idx < len(target_series) else ""
            for idx in range(len(metric_names))
        ]

        if actual_data is None:
            processed_cache = self.controller.get_cached_processed_data()
            cached_losses = (
                processed_cache.get("data_losses")
                if processed_cache
                else pd.DataFrame()
            )
            actual_source: pd.DataFrame | dict[str, object] = cached_losses
        else:
            actual_source = actual_data

        actual_values, actual_info = fetch_actual_metrics(actual_source, metric_names)

        updates = compute_row_updates(
            self.achieve_table.tablerows,
            target_values,
            actual_values,
        )

        for row, values in updates:
            row.values = values
            self.achieve_table.view.item(row.iid, values=values)

        if not updates:
            if show_message:
                self._show_toast(
                    title="Informasi",
                    message="Tidak ada baris target yang diperbarui. Pastikan CSV berisi data.",
                    bootstyle="warning",
                    duration=3000,
                )
            return False

        self.achieve_table.rowdata = [
            tuple(row.values) for row in self.achieve_table.tablerows
        ]

        range_value = ""
        if actual_info:
            range_value = actual_info.get("RANGE") or actual_info.get("Time range", "")
        range_text = str(range_value)
        self.time_period.configure(text=range_text)

        if show_message:
            self._show_toast(
                title="Berhasil",
                message=(
                    f"Target dan aktual shift {shift_number} berhasil diperbarui.\n"
                    f"Environment: {self.data_config.get('DEFAULT', 'environment')}"
                ),
                bootstyle="success",
                duration=3000,
            )
            # messagebox.showinfo(
            #     "Berhasil",
            #     f"Target dan aktual shift {shift_number} berhasil diperbarui dari CSV dan SPA.",
            # )

        return True

    @async_handler
    @with_button_state("btn_result")
    @with_progressbar
    async def refresh_achievement_table(self):
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

        shift_value = self.sidebar.select_shift.get().strip("Shift ")
        if not shift_value:
            self.update_achievement_table(show_message=True)
            return

        try:
            shift_number = int(shift_value)
        except ValueError:
            self._show_toast(
                title="Kesalahan",
                message="Format shift tidak valid. Gunakan format 'Shift X'.",
                bootstyle="danger",
                duration=3000,
            )
            return

        url = self._get_url(
            self.sidebar.lu.get().strip("LU"),
            self._get_selected_date(),
            str(shift_number),
            self.sidebar.func_location.get()[:4],
        )

        if not url:
            return

        try:
            target_series = load_target_shift(
                self.sidebar.lu.get().strip("LU"),
                self.sidebar.func_location.get(),
                shift_number,
            )
        except (FileNotFoundError, pd.errors.EmptyDataError):
            self._show_toast(
                title="Kesalahan",
                message="Gagal membaca file target. Periksa konfigurasi Link Up/Function.",
                bootstyle="danger",
                duration=3000,
            )
            return
        except KeyError as exc:
            self._show_toast(
                title="Kesalahan",
                message=str(exc),
                bootstyle="danger",
                duration=3000,
            )
            return
        except Exception as exc:
            self._show_toast(
                title="Kesalahan",
                message=str(exc),
                bootstyle="danger",
                duration=3000,
            )
            return

        try:
            processed = await self.controller.fetch_remote_issue_data(
                url, use_cache=True
            )
        except ControllerError as exc:
            self._show_toast(
                title="Kesalahan",
                message=str(exc),
                bootstyle="danger",
                duration=3000,
            )
            return
        except httpx.HTTPError as exc:
            self._show_toast(
                title="HTTP Error",
                message=self._format_http_error(exc, url),
                bootstyle="danger",
                duration=3000,
            )
            return

        actual_df = processed.get("data_losses", pd.DataFrame())
        actual_dict = self._extract_actual_record(actual_df)

        self.update_achievement_table(
            show_message=True,
            target_data=target_series,
            actual_data=actual_dict,
        )

    @async_handler
    @with_button_state("btn_save")
    @with_progressbar
    async def save_data_cards_to_csv(self):
        # Validate username entry
        username = self.view.entry_user.get().strip()
        if not username:
            self._show_toast(
                title="Peringatan",
                message="Silakan masukkan username terlebih dahulu.",
                bootstyle="warning",
                duration=3000,
            )
            return

        # Get sidebar data
        lu = self.sidebar.lu.get().strip()
        tanggal = self._get_selected_date()
        shift = self.sidebar.select_shift.get().strip()

        # Save username to CSV
        save_user(username)

        try:
            file_path = self.controller.save_cards(
                self.view.iter_card_data(), username, lu, tanggal, shift
            )

            self._show_toast(
                title="Berhasil",
                message=f"Data card berhasil ditambahkan ke file:\n{file_path}",
                bootstyle="success",
                duration=3000,
            )
        except Exception as exc:
            self._show_toast(
                title="Kesalahan",
                message=f"Gagal menyimpan data card ke CSV.\n{exc}",
                bootstyle="danger",
                duration=3000,
            )
            # messagebox.showerror(
            #     "Kesalahan", f"Gagal menyimpan data card ke CSV.\n{exc}"
            # )
            # return

        if not file_path:
            self._show_toast(
                title="Data Kosong",
                message="Tidak ada data card yang dapat disimpan ke CSV.",
                bootstyle="info",
                duration=3000,
            )
            # messagebox.showinfo(
            #     "Data Kosong", "Tidak ada data card yang dapat disimpan ke CSV."
            # )
            # return

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
            self._show_toast(
                title="Peringatan",
                message="Silakan pilih Link Up terlebih dahulu.",
                bootstyle="warning",
                duration=3000,
            )
            # messagebox.showwarning(
            #     "Peringatan", "Silakan pilih Link Up terlebih dahulu."
            # )
            return

        func_location = self.sidebar.func_location.get()
        file_path = get_targets_file_path(lu_value.strip("LU"), func_location)

        self.target_editor = TargetEditor(file_path)
        self.target_editor.grab_set()
