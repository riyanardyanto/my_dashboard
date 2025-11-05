import customtkinter as ctk
import pandas as pd
from ttkbootstrap.tableview import Tableview

# --- Buat DataFrame contoh ---
data = {
    "Nama": ["Budi", "Siti", "Andi", "Rina", "Dika"],
    "Umur": [25, 30, 22, 28, 35],
    "Kota": ["Jakarta", "Bandung", "Surabaya", "Yogyakarta", "Medan"],
    "Gaji": [5000000, 7500000, 4500000, 6000000, 8000000],
}
df = pd.DataFrame(data)

# --- Setup CustomTkinter ---
ctk.set_appearance_mode("System")  # "System", "Dark", "Light"
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Tabel DataFrame dengan CustomTkinter")
app.geometry("700x400")


# --- Judul ---
label = ctk.CTkLabel(
    app, text="Data Karyawan", font=ctk.CTkFont(size=16, weight="bold")
)
label.pack(pady=10)
# --- Buat Tabel menggunakan CTkTable ---
# Pastikan customtkinter versi >= 5.2.0

# Konversi DataFrame ke list of lists (termasuk header)
# Konversi DataFrame ke list of lists (termasuk header)
table_data = [df.columns.tolist()] + df.values.tolist()


def on_double_click1(event):
    pass
    selected = tableview.view.selection()
    if selected:
        item = selected[0]
        row_index = tableview.view.index(item)
        row_data = tableview.get_row(row_index)
        print(row_data)


def on_double_click(event):
    selected = tableview.view.selection()
    if selected:
        item = selected[0]
        row_index = tableview.view.index(item)
        row_data = df.iloc[row_index]

        # Print to console
        print(f"\nRow {row_index} clicked:")
        for col, val in row_data.items():
            print(f"  {col}: {val}")

        # Show in textbox
        output_text = f"Baris {row_index}: "
        output_text += " | ".join([f"{k}: {v}" for k, v in row_data.items()])
        # self.output.delete("1.0", "end")
        # self.output.insert("1.0", output_text)


# Buat tabel

tableview = Tableview(app, height=300, coldata=table_data[0], rowdata=table_data[1:])
tableview.pack(pady=10, padx=10, fill="both", expand=True)
tableview.bind("<Double-1>", on_double_click)


# --- Jalankan aplikasi ---
app.mainloop()
