from typing import Optional

import pandas as pd
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tableview import Tableview

from components.grok_card import IssueCard
from scrape_spa import SpaScraper

SPA = SpaScraper("spa.html")
df = SPA.get_splitted_dataframes()[3][
    ["Line performance Details", "nan_9", "Stops", "Downtime"]
]
df.columns = ["Line", "Issue", "Stops", "Downtime"]


def _clean_line(value):
    if isinstance(value, str):
        return value.strip("&nbsp;")
    return value


df["Line"] = df["Line"].apply(_clean_line).ffill()
# df["Line"] = df["Line"].fillna(method="ffill", inplace=True)

# print(df.head())


class App(ttk.Window):
    def __init__(self):
        super().__init__(themename="superhero")
        self.title("Issue Tracker – Clean Layout")
        self.geometry("1200x650")
        self.minsize(1000, 600)

        # ============== Table on the left side =================
        left_frame = ttk.Frame(self, width=200)
        left_frame.pack(side="left", fill="y")

        table = Tableview(
            left_frame,
            coldata=[{"text": col} for col in df.columns],
            rowdata=df.values.tolist(),
            autofit=True,
            searchable=True,
        )
        table.pack(fill="both", expand=True, padx=10, pady=10)
        self.table = table
        self.table.view.bind("<Double-1>", self.on_table_double_click)

        # ============== Right side for cards =================
        right_frame = ttk.Frame(self)
        right_frame.pack(side="right", fill="both", expand=True)

        # Header
        # header = ttk.Frame(right_frame)
        # header.pack(fill="x", padx=20, pady=(20, 10))
        # ttk.Label(
        #     header,
        #     text="Issue Tracker",
        #     font=("", 16, "bold"),
        #     bootstyle="inverse-dark",
        # ).pack(side="left")

        # Buttons
        btn_frame = ttk.Frame(right_frame)
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

        # Scrollable
        self.scrollable = ScrolledFrame(right_frame, autohide=True)
        self.scrollable.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.scrollable_frame = self.scrollable

        self.cards = {}
        self.add_new_card()

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

    def on_table_double_click(self, event):
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
