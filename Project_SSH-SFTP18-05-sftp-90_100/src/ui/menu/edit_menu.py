import tkinter as tk
from tkinter import messagebox, ttk  # Add ttk import

class EditMenu:
    def __init__(self, menubar, app):
        self.app = app
        
        # Create Edit menu
        self.menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=self.menu)
        
        # Add menu items
        self.menu.add_command(label="Copy", command=self.copy, accelerator="Ctrl+C")
        self.menu.add_command(label="Paste", command=self.paste, accelerator="Ctrl+V")
        self.menu.add_command(label="Save", command=self.save, accelerator="Ctrl+S")
        self.menu.add_separator()
        self.menu.add_command(label="Find...", command=self.find, accelerator="Ctrl+F")
        self.menu.add_command(label="Select All", command=self.select_all, accelerator="Ctrl+A")
        self.menu.add_separator()
        self.menu.add_command(label="Preferences", command=self.preferences)
    
    def copy(self):
        # Get the currently focused widget
        focused = self.app.root.focus_get()
        
        if focused:
            # Check if the widget has a copy method or is a Text/Entry widget
            if hasattr(focused, 'copy'):
                focused.copy()
            elif isinstance(focused, (tk.Text, tk.Entry)):
                if focused.tag_ranges(tk.SEL):
                    self.app.root.clipboard_clear()
                    self.app.root.clipboard_append(focused.get(tk.SEL_FIRST, tk.SEL_LAST))

    def paste(self):
        # Get the currently focused widget
        focused = self.app.root.focus_get()
        
        if focused:
            # Check if the widget has a paste method or is a Text/Entry widget
            if hasattr(focused, 'paste'):
                focused.paste()
            elif isinstance(focused, (tk.Text, tk.Entry)) and focused.cget('state') == 'normal':
                try:
                    text = self.app.root.clipboard_get()
                    if focused.tag_ranges(tk.SEL):
                        focused.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    focused.insert(tk.INSERT, text)
                except tk.TclError:
                    # No clipboard content
                    pass
    
    def find(self):
        # Implement find functionality for the current tab
        current_tab = self.app.tab_manager.notebook.select()
        if not current_tab:
            return
        
        # Find the text widget in the current tab
        text_widget = None
        
        # Check if it's a terminal tab
        for tab_id, tab_info in self.app.tab_manager.tabs.items():
            if tab_info["frame"] == current_tab and hasattr(tab_info["app"], "terminal_emulator"):
                text_widget = tab_info["app"].terminal_emulator.terminal
                break
        
        if not text_widget:
            # Check if it's the welcome tab
            if self.app.tab_manager.notebook.index(current_tab) == 0:
                # Find the text widget in the welcome tab
                for child in current_tab.winfo_children():
                    if isinstance(child, tk.Text):
                        text_widget = child
                        break
        
        if not text_widget:
            messagebox.showinfo("Find", "No searchable content in the current tab")
            return
        
        # Create find dialog
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Find")
        dialog.geometry("300x100")
        dialog.transient(self.app.root)
        dialog.grab_set()
        
        # Find options
        ttk.Label(dialog, text="Find what:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        find_var = tk.StringVar()
        find_entry = ttk.Entry(dialog, textvariable=find_var, width=30)
        find_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        find_entry.focus()
        
        case_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(dialog, text="Match case", variable=case_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5)
        
        # Last found position
        last_pos = tk.StringVar(value="1.0")
        
        def find_next():
            search_text = find_var.get()
            if not search_text:
                return
            
            # Start search from the last position or from the beginning if we've wrapped around
            start_pos = last_pos.get()
            if start_pos == "end":
                start_pos = "1.0"
            
            # Set search options
            kwargs = {}
            if not case_var.get():
                kwargs["nocase"] = True
            
            # Find the text
            pos = text_widget.search(search_text, start_pos, "end", **kwargs)
            
            if pos:
                # Text found, select it
                end_pos = f"{pos}+{len(search_text)}c"
                text_widget.tag_remove(tk.SEL, "1.0", tk.END)
                text_widget.tag_add(tk.SEL, pos, end_pos)
                text_widget.mark_set(tk.INSERT, end_pos)
                text_widget.see(pos)
                
                # Update last position for next search
                last_pos.set(end_pos)
            else:
                # Not found, wrap around to the beginning
                if start_pos != "1.0":
                    last_pos.set("1.0")
                    find_next()
                else:
                    messagebox.showinfo("Find", f"Cannot find '{search_text}'")
                    last_pos.set("1.0")
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Find Next", command=find_next).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Make dialog responsive
        dialog.columnconfigure(1, weight=1)
        
        # Handle Enter key
        dialog.bind("<Return>", lambda event: find_next())
        
        # Center dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def select_all(self):
        # Get the currently focused widget
        focused = self.app.root.focus_get()
        if hasattr(focused, 'select_all'):
            focused.event_generate("<<SelectAll>>")
    
    def preferences(self):
        # Open preferences dialog
        if hasattr(self.app, 'terminal_settings'):
            self.app.terminal_settings.open_settings()
    
    def save(self):
        # Get the current tab
        current_tab = self.app.tab_manager.notebook.select()
        if not current_tab:
            return
        
        # Find the text widget in the current tab
        text_widget = None
        tab_name = ""
        
        # Check if it's a terminal tab
        for tab_id, tab_info in self.app.tab_manager.tabs.items():
            if tab_info["frame"] == current_tab and hasattr(tab_info["app"], "terminal_emulator"):
                text_widget = tab_info["app"].terminal_emulator.terminal
                tab_name = tab_info.get("name", "terminal")
                break
        
        if not text_widget:
            messagebox.showinfo("Save", "No terminal content to save in the current tab")
            return
        
        # Determine if there's selected text
        has_selection = False
        try:
            selected_text = ""
            if text_widget.tag_ranges(tk.SEL):
                selected_text = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
                has_selection = True
        except tk.TclError:
            # No selection
            pass
        
        # If no selection, get all text
        if not has_selection:
            selected_text = text_widget.get("1.0", tk.END)
        
        # Open file dialog to save
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            title="Save Terminal Content",
            defaultextension=".txt",
            initialfile=f"{tab_name}_output.txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(selected_text)
                self.app.status_var.set(f"Terminal content saved to {filename}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save file: {str(e)}")