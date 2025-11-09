import ttkbootstrap as ttk
from ttkbootstrap.constants import BOTH, SUCCESS
from ttkbootstrap.tooltip import ToolTip

from .editble_tableview import EditableTableView
from ..utils.csvhandle import load_targets_df


class TargetEditor(ttk.Toplevel):
    def __init__(self, file_path: str):
        super().__init__()
        self.title("Target Editor")
        self.resizable(False, False)

        target_df = load_targets_df(file_path)

        columns = target_df.columns.to_list()
        data = target_df.values.tolist()

        table = EditableTableView(
            self,
            coldata=columns,
            rowdata=data,
            height=6,
            editable_columns=list(range(0, len(columns))),
        )
        table.pack(fill=BOTH, expand=False, padx=10, pady=10)

        table.load_from_csv(file_path)

        save_btn = ttk.Button(
            self,
            text="Save",
            command=lambda: table.save_to_csv(file_path),
            bootstyle=SUCCESS,
        )
        save_btn.pack(pady=5)

        ToolTip(save_btn, "Save")
