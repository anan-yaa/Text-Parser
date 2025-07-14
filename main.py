import tkinter as tk
from tkinter import filedialog, ttk, messagebox, simpledialog
import os
import nltk
import re

from parsers.pdf_parser import parse_pdf
from parsers.latex_parser import parse_latex
from parsers.resume_parser import parse_resume
from parsers.invoice_parser import parse_invoice

FILE_TYPES = [
    ("PDF files", "*.pdf"),
    ("LaTeX files", "*.tex"),
    ("All files", "*.*"),
]

SUPPORTED_TYPES = ["resume", "invoice", "latex"]

def detect_file_type(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        # Heuristic: if 'resume' in filename, treat as resume, else invoice
        if "resume" in os.path.basename(filepath).lower():
            return "resume"
        elif "invoice" in os.path.basename(filepath).lower():
            return "invoice"
        else:
            return None  # ambiguous
    elif ext == ".tex":
        return "latex"
    else:
        return None

def fix_spacing(text):
    import re
    # Remove unwanted symbols like (cid:132), (cid:240), §, #, +, etc.
    text = re.sub(r'\(cid:[0-9]+\)', '', text)  # Remove (cid:xxx)
    text = re.sub(r'[§#\+]', '', text)  # Remove §, #, +
    # Add space between lowercase/number and uppercase (e.g., "firstAid" -> "first Aid")
    text = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', text)
    # Add space between two uppercase letters followed by lowercase (e.g., "AIModel" -> "AI Model")
    text = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', text)
    # Add space before numbers if not already present
    text = re.sub(r'([a-zA-Z])([0-9])', r'\1 \2', text)
    # Add space after punctuation if not already present
    text = re.sub(r'([.,;:!?])([^\s])', r'\1 \2', text)
    # Replace multiple spaces with a single space
    text = re.sub(r' +', ' ', text)
    return text

class TextParserApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Text Parser App")
        self.geometry("800x600")
        self.configure(bg="#f7f7f7")
        self.create_widgets()

    def create_widgets(self):
        self.upload_btn = ttk.Button(self, text="Upload File", command=self.upload_file)
        self.upload_btn.pack(pady=20)

        self.result_frame = ttk.Frame(self)
        self.result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.tree = None
        self.line_items_tree = None

    def upload_file(self):
        file_path = filedialog.askopenfilename(filetypes=FILE_TYPES)
        if not file_path:
            return

        file_type = detect_file_type(file_path)
        if file_type is None:
            # Ask user to select type
            file_type = self.ask_file_type()
            if file_type is None:
                return

        try:
            if file_type == "resume":
                try:
                    data = parse_resume(file_path)
                except Exception as e:
                    # fallback to plain PDF parsing
                    data = {"Raw Text": parse_pdf(file_path)}
            elif file_type == "invoice":
                data = parse_invoice(file_path)
            elif file_type == "latex":
                data = parse_latex(file_path)
            else:
                messagebox.showerror("Unsupported", "File type not supported.")
                return
            self.display_data(data, file_type)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def ask_file_type(self):
        # Simple dialog to ask user for file type
        win = tk.Toplevel(self)
        win.title("Select File Type")
        win.geometry("300x150")
        tk.Label(win, text="Select the type of document:").pack(pady=10)
        var = tk.StringVar(value=SUPPORTED_TYPES[0])
        combo = ttk.Combobox(win, textvariable=var, values=SUPPORTED_TYPES, state="readonly")
        combo.pack(pady=10)
        result = {"type": None}
        def submit():
            result["type"] = var.get()
            win.destroy()
        ttk.Button(win, text="OK", command=submit).pack(pady=10)
        win.grab_set()
        self.wait_window(win)
        return result["type"]

    def display_data(self, data, file_type):
        # Clear previous widgets
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        # For invoices, show line items in a separate table if present
        if file_type == "invoice" and isinstance(data, dict):
            # Show main fields
            main_fields = {k: v for k, v in data.items() if k != "Line Items"}
            if main_fields:
                self.tree = ttk.Treeview(self.result_frame, columns=("Field", "Value"), show="headings")
                self.tree.heading("Field", text="Field")
                self.tree.heading("Value", text="Value")
                for k, v in main_fields.items():
                    if isinstance(v, str) and (len(v) > 100 or "\n" in v):
                        v_fixed = fix_spacing(v)
                        self.tree.insert("", tk.END, values=(k, "[See below]"))
                        self.tree.pack(fill=tk.X, expand=False, pady=(0, 10))
                        tk.Label(self.result_frame, text=f"{k}:").pack(anchor="w")
                        text_widget = tk.Text(self.result_frame, height=10, wrap="word")
                        text_widget.insert("1.0", v_fixed)
                        text_widget.config(state="disabled")
                        text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
                    else:
                        self.tree.insert("", tk.END, values=(k, v))
                self.tree.pack(fill=tk.X, expand=False, pady=(0, 10))
            # Show line items if present
            line_items = data.get("Line Items")
            if isinstance(line_items, list) and line_items:
                self.line_items_tree = ttk.Treeview(self.result_frame)
                columns = tuple(line_items[0].keys())
                self.line_items_tree["columns"] = columns
                self.line_items_tree["show"] = "headings"
                for col in columns:
                    self.line_items_tree.heading(col, text=col)
                for row in line_items:
                    self.line_items_tree.insert("", tk.END, values=list(row.values()))
                tk.Label(self.result_frame, text="Line Items:").pack(anchor="w")
                self.line_items_tree.pack(fill=tk.BOTH, expand=True)
            elif line_items:
                tk.Label(self.result_frame, text=f"Line Items: {line_items}").pack(anchor="w")
        elif isinstance(data, dict):
            self.tree = ttk.Treeview(self.result_frame, columns=("Field", "Value"), show="headings")
            self.tree.heading("Field", text="Field")
            self.tree.heading("Value", text="Value")
            for k, v in data.items():
                if isinstance(v, str) and (len(v) > 100 or "\n" in v):
                    v_fixed = fix_spacing(v)
                    self.tree.insert("", tk.END, values=(k, "[See below]"))
                    self.tree.pack(fill=tk.X, expand=False, pady=(0, 10))
                    tk.Label(self.result_frame, text=f"{k}:").pack(anchor="w")
                    text_widget = tk.Text(self.result_frame, height=10, wrap="word")
                    text_widget.insert("1.0", v_fixed)
                    text_widget.config(state="disabled")
                    text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
                else:
                    self.tree.insert("", tk.END, values=(k, v))
            self.tree.pack(fill=tk.BOTH, expand=True)
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            self.tree = ttk.Treeview(self.result_frame)
            columns = tuple(data[0].keys())
            self.tree["columns"] = columns
            self.tree["show"] = "headings"
            for col in columns:
                self.tree.heading(col, text=col)
            for row in data:
                self.tree.insert("", tk.END, values=list(row.values()))
            self.tree.pack(fill=tk.BOTH, expand=True)
        else:
            if isinstance(data, str):
                data = fix_spacing(data)
            tk.Label(self.result_frame, text=str(data)).pack()

if __name__ == "__main__":
    app = TextParserApp()
    app.mainloop()