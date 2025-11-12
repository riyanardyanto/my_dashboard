import pandas as pd
import ttkbootstrap as ttk
from .editble_tableview import EditableTableView


class HistoryWindow(ttk.Toplevel):
    def __init__(self, master: ttk.Window):
        super().__init__(master)
        self.title("History Window")
        self.geometry("400x300")
        ttk.Label(self, text="This is the history window").pack(pady=20)
        self.history_data = pd.read_csv("history_data.csv")  # Example data source
        self.history_table = EditableTableView(
            self,
            coldata=["Column 1", "Column 2", "Column 3"],
            rowdata=[
                ["Row1-Col1", "Row1-Col2", "Row1-Col3"],
                ["Row2-Col1", "Row2-Col2", "Row2-Col3"],
                ["Row3-Col1", "Row3-Col2", "Row3-Col3"],
                ["Row4-Col1", "Row4-Col2", "Row4-Col3"],
            ],
        )
        self.history_table.pack(fill="both", expand=True)
