import tkinter as tk

import matplotlib.pyplot as plt
import pandas as pd
import qrcode
import tabulate
import ttkbootstrap as ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
from ttkbootstrap.constants import BOTH, LEFT, RIGHT, X, Y
from ttkbootstrap.tableview import Tableview


def show_table_view(parent):
    # Create a new window for the table
    table_window = ttk.Toplevel(parent)
    table_window.title("Data Table")
    table_window.geometry("1000x700")

    # Load data from dh.csv
    try:
        df = pd.read_csv("dh.csv")[
            [
                "NUMBER",
                "DESCRIPTION",
                "WORK CENTER TYPE",
                "STATUS",
                "PRIORITY",
                "FOUND DURING",
                "DEFECT COUNTERMEASURES",
                "DEFECT TYPES",
                "REPORTED AT",
                "CLOSED AT",
            ]
        ]
        data = df.values.tolist()
        coldata = df.columns.tolist()
    except Exception as e:
        # Fallback to sample data if CSV fails to load
        data = [
            ["Alice", 25, "New York"],
            ["Bob", 30, "London"],
            ["Charlie", 35, "Paris"],
            ["Diana", 28, "Tokyo"],
        ]
        coldata = ["Name", "Age", "City"]
        ttk.Label(
            table_window,
            text=f"Error loading CSV: {str(e)}. Showing sample data.",
            bootstyle="warning",
        ).pack(pady=5)

    # Create frame for table and controls
    table_frame = ttk.Frame(table_window)
    table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # Create Treeview with custom style for text wrapping
    style = ttk.Style()
    style.configure(
        "Custom.Treeview", rowheight=20
    )  # Base row height, will be adjusted dynamically
    style.configure("Custom.Treeview.Heading", font=("Helvetica", 10, "bold"))

    # Create Treeview widget
    tree = ttk.Treeview(
        table_frame,
        columns=coldata,
        show="headings",
        style="Custom.Treeview",
        height=15,
    )

    # Configure columns with appropriate widths
    column_widths = {
        "NUMBER": 80,
        "DESCRIPTION": 200,
        "WORK CENTER TYPE": 150,
        "STATUS": 80,
        "PRIORITY": 80,
        "FOUND DURING": 100,
        "DEFECT COUNTERMEASURES": 300,
        "DEFECT TYPES": 250,
        "REPORTED AT": 120,
        "CLOSED AT": 120,
    }

    for col in coldata:
        width = column_widths.get(col, 120)
        tree.heading(col, text=col, anchor=tk.W)
        tree.column(col, width=width, minwidth=80, stretch=True, anchor=tk.W)

    # Function to wrap text
    def wrap_text(text, max_chars=50):
        if len(str(text)) <= max_chars:
            return str(text)
        # Split text into chunks of max_chars
        words = str(text).split()
        lines = []
        current_line = ""

        for word in words:
            if len(current_line + " " + word) <= max_chars:
                current_line += " " + word if current_line else word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return "\n".join(lines)

    # Insert data with text wrapping
    max_row_height = 20  # Base height
    for row in data:
        wrapped_row = []
        row_lines = 1  # Track max lines in this row

        for i, cell in enumerate(row):
            col_name = coldata[i]
            if col_name in ["DESCRIPTION", "DEFECT COUNTERMEASURES", "DEFECT TYPES"]:
                # Wrap long text
                wrapped_text = wrap_text(cell, 50)
                wrapped_row.append(wrapped_text)
                # Count lines in wrapped text
                lines_in_cell = len(wrapped_text.split("\n"))
                row_lines = max(row_lines, lines_in_cell)
            else:
                wrapped_row.append(cell)

        # Calculate row height based on number of lines (20px per line)
        row_height = row_lines * 20
        max_row_height = max(max_row_height, row_height)

        # Insert the row
        tree.insert("", tk.END, values=wrapped_row)

        # Set individual row height (this is a limitation - Treeview doesn't easily support per-row heights)
        # We'll use the maximum height found

    # Update style with calculated row height
    style.configure("Custom.Treeview", rowheight=max_row_height)

    # Add scrollbars
    v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
    h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=tree.xview)
    tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

    # Pack the treeview and scrollbars
    tree.grid(row=0, column=0, sticky="nsew")
    v_scrollbar.grid(row=0, column=1, sticky="ns")
    h_scrollbar.grid(row=1, column=0, sticky="ew")

    # Configure grid weights
    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    # Add search functionality
    search_frame = ttk.Frame(table_window)
    search_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

    ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 10))
    search_var = tk.StringVar()
    search_entry = ttk.Entry(search_frame, textvariable=search_var)
    search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def filter_table(*args):
        search_term = search_var.get().lower()
        # Clear current items
        for item in tree.get_children():
            tree.delete(item)

        # Filter and insert matching rows
        for row in data:
            if any(search_term in str(cell).lower() for cell in row):
                wrapped_row = []
                for i, cell in enumerate(row):
                    col_name = coldata[i]
                    if col_name in [
                        "DESCRIPTION",
                        "DEFECT COUNTERMEASURES",
                        "DEFECT TYPES",
                    ]:
                        # Wrap long text
                        wrapped_text = wrap_text(cell, 50)
                        wrapped_row.append(wrapped_text)
                    else:
                        wrapped_row.append(cell)
                tree.insert("", tk.END, values=wrapped_row)

    search_var.trace("w", filter_table)


def load_csv_data(frame):
    try:
        # Read CSV file
        df = pd.read_csv("dh.csv")[
            [
                "NUMBER",
                "DESCRIPTION",
                "WORK CENTER TYPE",
                "STATUS",
                "PRIORITY",
                "FOUND DURING",
                "DEFECT COUNTERMEASURES",
                "DEFECT TYPES",
                "REPORTED AT",
                "CLOSED AT",
            ]
        ]

        ttk.Label(
            frame, text=f"Loaded {len(df)} records from dh.csv", bootstyle="success"
        ).pack(pady=5)
    except Exception as e:
        ttk.Label(frame, text=f"Error loading CSV: {str(e)}", bootstyle="danger").pack(
            pady=5
        )


def create_home_view(parent):
    frame = ttk.Frame(parent)
    ttk.Label(
        frame,
        text="Dashboard Overview",
        font=("Helvetica", 24),
        bootstyle="primary",
    ).pack(pady=20)

    # Load data from dh.csv
    try:
        df = pd.read_csv("dh.csv")

        # Create subplots for dashboard
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle("Maintenance Dashboard", fontsize=16)

        # Chart 1: Status distribution
        status_counts = df["STATUS"].value_counts()
        ax1.bar(status_counts.index, status_counts.values, color="skyblue")
        ax1.set_title("Defect Status Distribution")
        ax1.set_ylabel("Count")
        ax1.tick_params(axis="x", rotation=45)

        # Chart 2: Priority distribution
        priority_counts = df["PRIORITY"].value_counts()
        ax2.pie(
            priority_counts.values,
            labels=priority_counts.index,
            autopct="%1.1f%%",
            startangle=90,
        )
        ax2.set_title("Priority Distribution")

        # Chart 3: Defects by Work Center Type
        work_center_counts = df["WORK CENTER TYPE"].value_counts().head(10)
        ax3.barh(
            work_center_counts.index, work_center_counts.values, color="lightgreen"
        )
        ax3.set_title("Top 10 Work Center Types")
        ax3.set_xlabel("Count")

        # Chart 4: Defects over time (by month)
        df["REPORTED AT"] = pd.to_datetime(
            df["REPORTED AT"], errors="coerce", dayfirst=True
        )
        df["Month"] = df["REPORTED AT"].dt.to_period("M")
        monthly_counts = df.groupby("Month").size()
        ax4.plot(
            range(len(monthly_counts)),
            monthly_counts.values,
            marker="o",
            color="orange",
        )
        ax4.set_title("Monthly Defect Trend")
        ax4.set_xlabel("Months")
        ax4.set_ylabel("Defect Count")
        ax4.set_xticks(range(len(monthly_counts)))
        ax4.set_xticklabels([str(m) for m in monthly_counts.index], rotation=45)

        plt.tight_layout()

        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True, padx=20, pady=20)

    except Exception as e:
        ttk.Label(
            frame,
            text=f"Welcome to the Dashboard\n\nError loading data: {str(e)}\n\nSelect a menu item from the sidebar.",
            bootstyle="secondary",
            justify="center",
        ).pack(pady=50)

        # Button to show table
        ttk.Button(
            frame,
            text="Show Table",
            bootstyle="info",
            command=lambda: show_table_view(frame),
        ).pack(pady=10)

    return frame


def create_table_view(parent):
    frame = ttk.Frame(parent)
    ttk.Label(frame, text="Data Table", font=("Helvetica", 20), bootstyle="info").pack(
        pady=20
    )

    # Load data from dh.csv
    try:
        df = pd.read_csv("dh.csv")[
            [
                "NUMBER",
                "DESCRIPTION",
                "WORK CENTER TYPE",
                "STATUS",
                "PRIORITY",
                "FOUND DURING",
                "DEFECT COUNTERMEASURES",
                "DEFECT TYPES",
                "REPORTED AT",
                "CLOSED AT",
            ]
        ]
        data = df.values.tolist()
        coldata = df.columns.tolist()
    except Exception as e:
        # Fallback to sample data if CSV fails to load
        data = [
            {"Name": "Alice", "Age": 25, "City": "New York", "Salary": 50000},
            {"Name": "Bob", "Age": 30, "City": "London", "Salary": 60000},
            {"Name": "Charlie", "Age": 35, "City": "Paris", "Salary": 70000},
            {"Name": "Diana", "Age": 28, "City": "Tokyo", "Salary": 55000},
        ]
        coldata = ["Name", "Age", "City", "Salary"]
        ttk.Label(
            frame,
            text=f"Error loading CSV: {str(e)}. Showing sample data.",
            bootstyle="warning",
        ).pack(pady=5)

    # Create Tableview
    table = Tableview(
        master=frame,
        coldata=coldata,
        rowdata=data,
        paginated=False,
        searchable=True,
        bootstyle="primary",
        autofit=True,
        yscrollbar=True,
    )
    table.pack(fill=BOTH, expand=True, padx=20, pady=20)

    return frame


def create_reports_view(parent):
    frame = ttk.Frame(parent)
    ttk.Label(frame, text="Reports", font=("Helvetica", 20), bootstyle="success").pack(
        pady=20
    )

    # Load data and generate report text
    try:
        df = pd.read_csv("dh.csv")
        report_text = create_reports_text(df)

        # Create main content frame
        content_frame = ttk.Frame(frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10, side=tk.LEFT)

        # Create text widget to display report
        text_widget = tk.Text(
            content_frame,
            wrap=tk.WORD,
            padx=20,
            pady=20,
            font=("Consolas", 10),
        )
        text_widget.insert(tk.END, report_text)
        text_widget.config(state=tk.DISABLED)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(content_frame, command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)

        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create QR code from report text
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(report_text)
        qr.make(fit=True)

        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="orange").resize(
            (500, 500)
        )

        # Convert PIL image to PhotoImage for tkinter
        qr_photo = ImageTk.PhotoImage(qr_image)

        # # Create QR code frame
        # qr_frame = ttk.Frame(frame)
        # qr_frame.pack(fill=tk.X, padx=20, pady=10, side=tk.LEFT, anchor=tk.N)

        # ttk.Label(qr_frame, text="QR Code:", font=("Helvetica", 12, "bold")).pack(
        #     anchor=tk.W
        # )

        # Display QR code
        qr_label = ttk.Label(content_frame, image=qr_photo)
        qr_label.image = qr_photo  # Keep a reference to prevent garbage collection
        qr_label.pack(padx=10, pady=10, side=tk.RIGHT, anchor=tk.NE)

    except Exception as e:
        ttk.Label(
            frame,
            text=f"Error generating report: {str(e)}",
            bootstyle="danger",
        ).pack(pady=50)

    return frame


def create_reports_text(df: pd.DataFrame):
    link_up = ""
    list_lu = list(df["WORK CENTER TYPE"].unique())
    for i in range(len(list_lu)):
        link_up = f"{link_up},  {list_lu[i]}"

    df_date = pd.to_datetime(df["REPORTED AT"], dayfirst=True).dt.strftime("%d-%m-%Y")
    period = f"*DH {df_date.min()} to {df_date.max()}*"

    total_found = len(df["WORK CENTER TYPE"])
    DH_found = df.groupby(["WORK CENTER TYPE"]).size().reset_index()
    DH_found.rename(
        columns={"WORK CENTER TYPE": "WORK CENTER", 0: "FOUND"}, inplace=True
    )

    def get_detail_DH(df: pd.DataFrame, value: str):
        DH_detail = df.groupby(["WORK CENTER TYPE"]).size().reset_index()
        DH_detail.rename(
            columns={"WORK CENTER TYPE": "WORK CENTER", 0: value}, inplace=True
        )
        return f"`{str(tabulate.tabulate(DH_detail, headers='keys', tablefmt='psql', showindex=False)).replace('\n', '`\n`')}`"
        # return f"`{str(DH_detail.to_markdown(tablefmt='pipe', index=False)).replace('\n', '`\n`')}`"

    # DH FOUND
    df_total = df
    total_found = len(df_total)
    detail_found = get_detail_DH(df_total, " FOUND")

    # DH FOUND DURING CIL
    df_cil = df.loc[df["FOUND DURING"].isin(["CIL"])]
    total_found_cil = len(df_cil)
    detail_found_cil = get_detail_DH(df_cil, "   CIL")

    # DH FIX (CLOSED)
    df_close = df.loc[df["STATUS"].isin(["CLOSED"])]
    total_close = len(df_close)
    detail_close = get_detail_DH(df_close, "CLOSED")

    # DH SOC
    # df_soc = df.loc[df["DEFECT TYPES"].str.contains("SOURCE_OF_CONTAMINATION")]
    df_soc_found = df_total.loc[
        df_total["DEFECT TYPES"].str.contains("SOURCE_OF_CONTAMINATION")
    ]
    df_soc_fix = df_close.loc[
        df_close["DEFECT TYPES"].str.contains("SOURCE_OF_CONTAMINATION")
    ]

    soc = {"FOUND": len(df_soc_found), "FIX": len(df_soc_fix)}
    # len_dh_soc_found = len(df_soc_found)
    # len_dh_soc_fix = len(df_soc_fix)

    df_soc = pd.DataFrame.from_dict(soc, orient="index")

    # total_soc = len(df_soc_found)
    # for item in df["DEFECT TYPES"].values.tolist():
    #     if "SOURCE_OF_CONTAMINATION" in item:
    #         total_soc += 1
    detail_soc = f"`{str(tabulate.tabulate(df_soc, headers=['STATUS     ', ' COUNT'], tablefmt='psql', showindex=True)).replace('\n', '`\n`')}`"

    # open
    try:
        df_open = df.loc[df["STATUS"].isin(["OPEN"])][
            ["NUMBER", "DESCRIPTION", "PRIORITY"]
        ]

        li_val = df_open.values.tolist()
        data_open = []
        for i in range(len(li_val)):
            a = f"""{1 + i}. {li_val[i][0]}: {li_val[i][1]}\n"""
            data_open.append(a)
        str_open = ""
        for i in range(len(data_open)):
            str_open = str_open + data_open[i]
    except Exception:
        str_open = ""

    # high
    try:
        df_high = df.loc[df["PRIORITY"].isin(["HIGH"])][
            ["NUMBER", "DESCRIPTION", "STATUS", "DEFECT COUNTERMEASURES"]
        ]

        li_val = df_high.values.tolist()
        data_high = []
        for i in range(len(li_val)):
            a = f"""{1 + i}. {li_val[i][0]}: {li_val[i][1]}\n- Status : {li_val[i][2]}\n- CM      : {li_val[i][3]}\n\n"""
            data_high.append(a)
        str_high = ""
        for i in range(len(data_high)):
            str_high = str_high + data_high[i]
    except Exception:
        str_high = ""

    return f"{period}\n\n*DH FOUND DURING CIL*: {total_found_cil}\n{detail_found_cil}\n\n*DH FOUND*: {total_found}\n{detail_found}\n\n*DH FIX (CLOSED)*: {total_close}\n{detail_close}\n\n*DH SOC*: \n{detail_soc}\n\n*DH OPEN*: {len(data_open)}\n{str_open}\n*DH HIGH*: {len(data_high)}\n{str_high}"


def create_settings_view(parent):
    frame = ttk.Frame(parent)
    ttk.Label(frame, text="Settings", font=("Helvetica", 20), bootstyle="warning").pack(
        pady=20
    )

    # Settings form
    ttk.Label(frame, text="Username:").pack(pady=5)
    username_entry = ttk.Entry(frame)
    username_entry.pack(pady=5)

    ttk.Label(frame, text="Email:").pack(pady=5)
    email_entry = ttk.Entry(frame)
    email_entry.pack(pady=5)

    ttk.Button(frame, text="Save Settings", bootstyle="primary").pack(pady=20)

    return frame


def create_help_view(parent):
    frame = ttk.Frame(parent)
    ttk.Label(
        frame, text="Help & Support", font=("Helvetica", 20), bootstyle="danger"
    ).pack(pady=20)

    help_text = """
    Welcome to the Dashboard Help.

    - Home: Overview of the dashboard.
    - Analytics: View charts and data visualizations.
    - Reports: Browse tabular reports.
    - Settings: Configure your preferences.
    - Help: This help page.

    For more assistance, contact support.
    """
    text_widget = tk.Text(frame, wrap=tk.WORD, height=10)
    text_widget.insert(tk.END, help_text)
    text_widget.config(state=tk.DISABLED)
    text_widget.pack(fill=BOTH, expand=True, padx=20, pady=20)

    return frame


def main():
    # Create the main window
    root = ttk.Window(themename="superhero")  # Modern theme
    root.title("Modern Dashboard")
    root.geometry("1200x600")
    root.minsize(1000, 500)

    # Create sidebar frame
    sidebar = ttk.Frame(root, width=250, bootstyle="secondary")
    sidebar.pack(side=LEFT, fill=Y)

    # Sidebar title
    sidebar_title = ttk.Label(
        sidebar,
        text="Dashboard Menu",
        font=("Helvetica", 16, "bold"),
        bootstyle="inverse-secondary",
    )
    sidebar_title.pack(pady=20, padx=10)

    # Sidebar buttons
    menu_items = [
        ("Home", "🏠"),
        ("Table", "📊"),
        ("Reports", "📋"),
        ("Settings", "⚙️"),
        ("Help", "❓"),
    ]

    for text, icon in menu_items:
        btn = ttk.Button(
            sidebar,
            text=f"{icon} {text}",
            bootstyle="outline-secondary",
            command=lambda t=text: switch_view(t),
        )
        btn.pack(fill=X, padx=10, pady=5)

    # Main content area
    main_frame = ttk.Frame(root, bootstyle="light")
    main_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=5, pady=5)

    # Create view frames
    home_frame = create_home_view(main_frame)
    table_frame = create_table_view(main_frame)
    reports_frame = create_reports_view(main_frame)
    settings_frame = create_settings_view(main_frame)
    help_frame = create_help_view(main_frame)

    # Dictionary of views
    views = {
        "Home": home_frame,
        "Table": table_frame,
        "Reports": reports_frame,
        "Settings": settings_frame,
        "Help": help_frame,
    }

    # Function to switch views
    def switch_view(view_name):
        for frame in views.values():
            frame.pack_forget()
        views[view_name].pack(fill=BOTH, expand=True)

    # Show home by default
    switch_view("Home")

    # Handle window close event
    def on_closing():
        plt.close("all")  # Close all matplotlib figures
        root.quit()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Run the application
    root.mainloop()


if __name__ == "__main__":
    main()
