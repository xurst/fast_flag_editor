import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import re
from typing import Dict, Any, Optional, List, Tuple
import sys

AUTOSAVE_DELAY = 1000

class FastFlagEditor:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Roblox Fast Flag Editor")
        
        window_width = 800
        window_height = 600
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        try:
            if hasattr(sys, '_MEIPASS'):
                icon_path = os.path.join(sys._MEIPASS, "assets", "fast_flag_editor_icon.ico")
            else:
                icon_path = os.path.join("assets", "fast_flag_editor_icon.ico")
            self.root.iconbitmap(icon_path)
        except Exception:
            pass  
        
        self.settings_path = os.path.join(
            os.environ["LOCALAPPDATA"], 
            "Roblox", 
            "ClientSettings", 
            "ClientAppSettings.json"
        )
        
        self.flags: Dict[str, Any] = {}
        self.flag_types: Dict[str, str] = {}
        
        self.autosave_delay = AUTOSAVE_DELAY
        self.autosave_pending = False
        
        self.create_ui()
        self.load_flags()
    
    def create_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(controls_frame, text="Add Flag", command=self.add_flag).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="Remove Flag", command=self.remove_flag).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="Refresh", command=self.load_flags).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="Import", command=self.import_flags).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="Export", command=self.export_flags).pack(side=tk.LEFT, padx=(0, 5))
        
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_flags)
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        list_frame = ttk.LabelFrame(main_frame, text="Fast Flags")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(
            list_frame,
            columns=("Name", "Type", "Value"),
            show="headings",
            selectmode="extended"
        )

        self.tree.heading("Name", text="Name")
        self.tree.heading("Type", text="Type")
        self.tree.heading("Value", text="Value")
        
        self.tree.column("Name", width=200)
        self.tree.column("Type", width=100)
        self.tree.column("Value", width=400)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.bind("<Double-1>", self.edit_flag)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)
    
    def schedule_autosave(self):
        if self.autosave_pending:
            return
        self.autosave_pending = True
        self.root.after(self.autosave_delay, self.perform_autosave)
        self.status_var.set("Changes detected - Auto-saving...")
    
    def perform_autosave(self):
        self.autosave_pending = False
        self.save_flags()
    
    def load_flags(self):
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, "r") as f:
                    self.flags = json.load(f)
            else:
                self.flags = {}
                
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            self.flag_types = {}
            for key, value in self.flags.items():
                if isinstance(value, bool) or str(value).lower() in ("true", "false"):
                    self.flag_types[key] = "bool"
                elif isinstance(value, int) or (isinstance(value, str) and (value.isdigit() or (value.startswith("-") and value[1:].isdigit()))):
                    self.flag_types[key] = "int"
                else:
                    self.flag_types[key] = "string"
                    
            self.populate_tree()
            
            self.status_var.set(f"Loaded {len(self.flags)} flags from {self.settings_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load flags: {str(e)}")
            self.status_var.set("Error loading flags")
    
    def populate_tree(self, filter_text: str = ""):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for key, value in sorted(self.flags.items()):
            if filter_text and filter_text.lower() not in key.lower():
                continue
                
            flag_type = self.flag_types.get(key, "string")
            
            self.tree.insert("", "end", values=(key, flag_type, value), iid=key)
            
        self.status_var.set(f"Displaying {len(self.tree.get_children())} flags")
    
    def filter_flags(self, *args):
        filter_text = self.search_var.get()
        self.populate_tree(filter_text)
    
    def add_flag(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("Add Flag")
        window_width = 400
        window_height = 200

        screen_width = add_window.winfo_screenwidth()
        screen_height = add_window.winfo_screenheight()

        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        add_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        add_window.transient(self.root)
        add_window.grab_set()
        
        ttk.Label(add_window, text="Flag Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        name_var = tk.StringVar()
        ttk.Entry(add_window, textvariable=name_var, width=30).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(add_window, text="Flag Type:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        type_var = tk.StringVar(value="bool")
        ttk.Combobox(add_window, textvariable=type_var, values=["bool", "int", "string"], state="readonly").grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=5
        )
        
        ttk.Label(add_window, text="Flag Value:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        value_var = tk.StringVar()
        ttk.Entry(add_window, textvariable=value_var, width=30).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        def do_add():
            name = name_var.get().strip()
            flag_type = type_var.get()
            value = value_var.get().strip()
            
            if not name:
                messagebox.showerror("Error", "Flag name cannot be empty")
                return
                
            if not self.validate_flag_value(flag_type, value):
                messagebox.showerror("Error", f"Invalid value for {flag_type} type")
                return
                
            converted_value = self.convert_value(flag_type, value)
            
            self.flags[name] = converted_value
            self.flag_types[name] = flag_type
            
            self.populate_tree(self.search_var.get())
            
            add_window.destroy()
            
            self.status_var.set(f"Added flag: {name}")
            self.schedule_autosave()
            
        ttk.Button(add_window, text="Add", command=do_add).grid(row=3, column=0, columnspan=2, pady=10)
    
    def edit_flag(self, event):
        selected = self.tree.focus()
        if not selected:
            return

        flag_name = selected
        flag_type = self.flag_types.get(flag_name, "string")
        flag_value = self.flags.get(flag_name, "")

        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Edit Flag: {flag_name}")

        window_width = 400
        window_height = 200

        screen_width = edit_window.winfo_screenwidth()
        screen_height = edit_window.winfo_screenheight()

        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        edit_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        edit_window.transient(self.root)
        edit_window.grab_set()
        
        ttk.Label(edit_window, text="Flag Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(edit_window, text=flag_name).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(edit_window, text="Flag Type:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        type_var = tk.StringVar(value=flag_type)
        ttk.Combobox(edit_window, textvariable=type_var, values=["bool", "int", "string"], state="readonly").grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=5
        )
        
        ttk.Label(edit_window, text="Flag Value:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        value_var = tk.StringVar(value=str(flag_value))
        ttk.Entry(edit_window, textvariable=value_var, width=30).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        def do_update():
            new_type = type_var.get()
            new_value = value_var.get().strip()
            
            if not self.validate_flag_value(new_type, new_value):
                messagebox.showerror("Error", f"Invalid value for {new_type} type")
                return
                
            converted_value = self.convert_value(new_type, new_value)
            
            self.flags[flag_name] = converted_value
            self.flag_types[flag_name] = new_type
            
            self.tree.item(selected, values=(flag_name, new_type, converted_value)) 
            
            edit_window.destroy()
            
            self.status_var.set(f"Updated flag: {flag_name}")
            self.schedule_autosave()
            
        ttk.Button(edit_window, text="Update", command=do_update).grid(row=3, column=0, columnspan=2, pady=10)
    
    def remove_flag(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No flags selected")
            return
        if not messagebox.askyesno(
            "Confirm",
            f"Are you sure you want to remove {len(selected)} flag(s)?"
        ):
            return
        for flag_name in selected:
            self.flags.pop(flag_name, None)
            self.flag_types.pop(flag_name, None)
            self.tree.delete(flag_name)
        self.status_var.set(f"Removed {len(selected)} flags")
        self.schedule_autosave()

    
    def save_flags(self):
        try:
            os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
            
            with open(self.settings_path, "w") as f:
                json.dump(self.flags, f, indent=2)
                
            self.status_var.set(f"Auto-saved {len(self.flags)} flags to {self.settings_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save flags: {str(e)}")
            self.status_var.set("Error saving flags")
    
    def import_flags(self):
        import_window = tk.Toplevel(self.root)
        import_window.title("Import Flags")

        window_width = 600
        window_height = 400

        screen_width = import_window.winfo_screenwidth()
        screen_height = import_window.winfo_screenheight()

        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        import_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        import_window.transient(self.root)
        import_window.grab_set()
        
        ttk.Label(import_window, text="Paste JSON content below:").pack(anchor=tk.W, padx=10, pady=5)
        
        text_area = scrolledtext.ScrolledText(import_window, width=70, height=15)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        def do_import():
            content = text_area.get("1.0", tk.END).strip()
            if not content:
                messagebox.showwarning("Warning", "No content to import")
                return
                
            try:
                imported_flags = json.loads(content)
                
                if not isinstance(imported_flags, dict):
                    messagebox.showerror("Error", "Invalid JSON format. Expected a dictionary.")
                    return
                    
                if self.flags:
                    response = messagebox.askyesnocancel(
                        "Confirm", 
                        "Do you want to merge with existing flags? Click 'Yes' to merge, 'No' to overwrite, or 'Cancel' to abort."
                    )
                    
                    if response is None:  
                        return
                        
                    if response:  
                        for key, value in imported_flags.items():
                            self.flags[key] = value
                    else:  
                        self.flags = imported_flags
                else:
                    self.flags = imported_flags
                    
                for key, value in self.flags.items():
                    if isinstance(value, bool) or (isinstance(value, str) and str(value).lower() in ("true", "false")):
                        self.flag_types[key] = "bool"
                    elif isinstance(value, int) or (isinstance(value, str) and (value.isdigit() or (value.startswith("-") and value[1:].isdigit()))):
                        self.flag_types[key] = "int"
                    else:
                        self.flag_types[key] = "string"
                        
                self.populate_tree()
                
                import_window.destroy()
                
                self.status_var.set(f"Imported {len(imported_flags)} flags")
                self.schedule_autosave()
                
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Invalid JSON format")
            except Exception as e:
                messagebox.showerror("Error", f"Import failed: {str(e)}")
        
        ttk.Button(import_window, text="Import", command=do_import).pack(pady=10)
    
    def export_flags(self):
        export_window = tk.Toplevel(self.root)
        export_window.title("Export Flags")

        window_width = 600
        window_height = 400

        screen_width = export_window.winfo_screenwidth()
        screen_height = export_window.winfo_screenheight()

        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        export_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        export_window.transient(self.root)
        export_window.grab_set()
        
        ttk.Label(export_window, text="Copy the JSON content below:").pack(anchor=tk.W, padx=10, pady=5)
        
        text_area = scrolledtext.ScrolledText(export_window, width=70, height=15)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        text_area.insert("1.0", json.dumps(self.flags, indent=2))
        
        def copy_to_clipboard():
            export_window.clipboard_clear()
            export_window.clipboard_append(text_area.get("1.0", tk.END))
            self.status_var.set("Copied flags to clipboard")
            
        ttk.Button(export_window, text="Copy to Clipboard", command=copy_to_clipboard).pack(pady=10)
    
    def validate_flag_value(self, flag_type: str, value: str) -> bool:
        if flag_type == "bool":
            return value.lower() in ("true", "false")
        elif flag_type == "int":
            try:
                int(value)
                return True
            except ValueError:
                return False
        else:  
            return True
    
    def convert_value(self, flag_type: str, value: str) -> Any:
        if flag_type == "bool":
            return value.lower() == "true"
        elif flag_type == "int":
            return int(value)
        else:  
            return value


def main():
    myappid = 'roblox.fast.flag.editor.1.0.0'
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception as e:
        print(f"Error setting application ID: {e}")
    
    root = tk.Tk()
    
    try:
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, "assets", "fast_flag_editor_icon.ico")
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(script_dir, "assets", "fast_flag_editor_icon.ico")
        
        root.iconbitmap(icon_path)
    except Exception as e:
        print(f"Error setting taskbar icon: {e}")
    
    app = FastFlagEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()