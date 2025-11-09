import ttkbootstrap as ttk
from PIL import Image, ImageTk, UnidentifiedImageError
from ttkbootstrap.constants import SUCCESS, WARNING, PRIMARY, TOP, W, X, YES
from ttkbootstrap.tooltip import ToolTip
from ttkwidgets.autocomplete import AutocompleteCombobox

from ..utils.helpers import get_data_from_excel, resource_path


class Sidebar(ttk.Frame):
    def __init__(self, master: ttk.Frame):
        super().__init__(master, padding=(10, 10))
        self.home_frame = master
        self.select_shift = ttk.StringVar()

        # Load and display the logo
        self._create_logo()

        # Create widgets for user input
        self._create_input_widgets()

        # Create buttons for actions
        self._create_action_buttons()

        # Create username entry and save button
        self._create_user_entry()

        # Create a test button for debugging
        # self._create_test_button()

    def _create_logo(self):
        """Load and display the application logo."""
        try:
            self.photo = ImageTk.PhotoImage(
                image=Image.open(resource_path("assets/c5_spa.ico")).resize((80, 80))
            )
        except (FileNotFoundError, UnidentifiedImageError):
            self.photo = None

        if self.photo:
            self.logo = ttk.Label(master=self, image=self.photo)
            self.logo.pack(side=TOP, padx=10, pady=10)

        self._add_separator()

    def _create_input_widgets(self):
        """Create widgets for user input (Link Up, Date, Shift)."""
        # Link Up combobox
        self.lu = ttk.Combobox(
            self,
            bootstyle="success",
            width=12,
            cursor="hand2",
        )
        self.lu.pack(side=TOP, padx=10, pady=(5, 5))

        # Date entry
        self.dt = ttk.DateEntry(
            self,
            bootstyle=SUCCESS,
            width=10,
            dateformat=r"%Y-%m-%d",
            cursor="hand2",
        )
        self.dt.pack(side=TOP, padx=10, pady=5)

        # Shift radio buttons
        shifts = ["Shift 1", "Shift 2", "Shift 3"]
        for shift in shifts:
            ttk.Radiobutton(
                self,
                bootstyle=SUCCESS,
                variable=self.select_shift,
                text=shift,
                value=shift,
                cursor="hand2",
            ).pack(padx=10, pady=5, anchor=W)

        self._add_separator()

    def _create_action_buttons(self):
        """Create buttons for various actions."""
        # Get Data button
        self.btn_get_data = self._create_button(
            "Get Data", SUCCESS, "Get data stop reason from SPA"
        )
        self.btn_get_data.pack(side=TOP, padx=10, pady=(5, 10))

        # Link Up combobox
        self.func_location = ttk.Combobox(
            self,
            bootstyle="success",
            width=12,
            cursor="hand2",
            values=["PACKER", "MAKER"],
        )
        self.func_location.set("PACKER")
        self.func_location.pack(side=TOP, padx=10, pady=(10, 5))

        # Result button
        self.btn_result = self._create_button(
            "Result", SUCCESS, "Show Target and Actual Result"
        )
        self.btn_result.pack(side=TOP, padx=10, pady=(5, 5))

        self._add_separator()

        # QR Code button
        self.btn_qr = self._create_button("QR Code", WARNING, "Generate QR Code")
        self.btn_qr.pack(side=TOP, padx=10, pady=(5, 5))

        # Update Target button
        self.btn_target = self._create_button(
            "Update Target", WARNING, "Open Target Editor"
        )
        self.btn_target.pack(side=TOP, padx=10, pady=(5, 5))

        self._add_separator()

    def _create_user_entry(self):
        """Create username entry and save button."""
        # Username entry
        self.entry_user = AutocompleteCombobox(
            master=self,
            width=12,
            completevalues=get_data_from_excel(sheet_index=1),
            cursor="hand2",
        )
        self.entry_user.pack(side=TOP, padx=10, pady=(5, 5))
        ToolTip(self.entry_user, "Select Username", delay=0)

        # Save to Excel button
        self.btn_save = self._create_button("Save Excel", PRIMARY, "Save to Excel")
        self.btn_save.pack(side=TOP, padx=10, pady=(5, 5))

        self._add_separator()

    def _create_test_button(self):
        """Create a test button for debugging purposes."""
        self.btn_test = ttk.Button(
            master=self,
            text="Test",
            bootstyle="danger",
            width=13,
            cursor="hand2",
        )
        ToolTip(self.btn_test, "Test Button", delay=0)
        self.btn_test.pack(side=TOP, padx=10, pady=(5, 5))

    def _create_button(self, text, style, tooltip_text):
        """Helper method to create a button with a tooltip."""
        button = ttk.Button(
            master=self,
            text=text,
            bootstyle=style,
            width=13,
            cursor="hand2",
        )
        ToolTip(button, tooltip_text, delay=0)
        return button

    def _add_separator(self):
        """Add a horizontal separator."""
        ttk.Separator(
            master=self,
            orient="horizontal",
            style="danger.Horizontal.TSeparator",
        ).pack(side=TOP, expand=YES, fill=X, padx=0, pady=10)
