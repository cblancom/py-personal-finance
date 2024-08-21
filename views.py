import tkinter as tk
from tkinter import ttk


class FinanceApp:
    def __init__(
        self,
    ):

        root = tk.Tk()
        root.geometry("800x300")
        root.configure(background="gray")
        tk.Wm.wm_title(root, "PyPersonalFinance")

        # Initialize the interface
        self.initialize_interface(root)

        # Start the Tkinter main loop
        root.mainloop()

    def initialize_interface(self, root):

        # Create entry and button for adding income
        self.create_entry_and_button(root, "Add Income", row=0, column=0)
        self.create_entry_and_button(root, "Add Expense", row=3, column=0)

        # Date entry fields
        self.income_date_entry = self.create_date_entry(root, row=0, column=1)
        self.income_date_entry = self.create_date_entry(root, row=3, column=1)

        # Dropdown menu
        self.expense_category = self.create_drop_down_menu(root, row=3, column=2)

    def create_entry_and_button(self, root, name, row, column):
        # Create an entry widget for the amount
        entry = tk.Entry(root, font=("Courier", 14))
        entry.grid(row=row, column=column, padx=20, pady=(20, 5))

        button = tk.Button(
            root,
            text=name,
            font=("Courier", 14),
            background="#00a8e8",
            fg="white",
            command=lambda e=entry: self.handle_button_click(e),
        )
        button.grid(row=row + 1, column=column, padx=20, pady=(5, 20))

    def create_date_entry(self, root, row, column):
        # Create an entry widget for the date
        date_entry = tk.Entry(root, font=("Courier", 14))
        date_entry.grid(row=row, column=column, padx=20, pady=(20, 5))
        date_entry.insert(0, "DD-MM-YYYY")

        return date_entry

    def create_drop_down_menu(self, root, row, column):
        # Create a dropdown menu (combobox) for expense categories
        options = ["Necessary", "Non-Necessary", "Inversion"]
        combobox = ttk.Combobox(root, values=options, font=("Courier", 14))
        combobox.grid(row=row, column=column, padx=20, pady=(20, 5))
        combobox.current(0)

    def handle_button_click(self, entry):
        print(f"Entry Value: {entry.get()}")
        entry.delete(0, tk.END)

    def saludar(
        self,
    ):
        print("Saludar")
