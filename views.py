import tkinter as tk
from tkinter import BOTH, ttk, messagebox


class FinanceApp:
    def __init__(
        self,
    ):

        root = tk.Tk()
        root.geometry("600x300")
        root.configure(background="black")
        tk.Wm.wm_title(root, "PyPersonalFinance")

        tk.Button(
            root,
            text="Add",
            font=("Courier", 14),
            background="#00a8e8",
            fg="white",
            command=self.saludar,
        ).pack(
            fill=tk.BOTH,
            expand=True,
        )

        root.mainloop()

    def saludar(
        self,
    ):
        print("Saludar")
