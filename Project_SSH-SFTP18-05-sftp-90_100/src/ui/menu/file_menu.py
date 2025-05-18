import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import time

class FileMenu:
    def __init__(self, menubar, app):
        self.app = app
        
        # Create File menu
        self.menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=self.menu)
        
        # Add menu items
        self.menu.add_command(label="New Connection", command=self.new_connection)
        self.menu.add_command(label="Quick Connect...", command=self.quick_connect)
        self.menu.add_separator()
        self.menu.add_command(label="Create Folder", command=self.create_folder)
        self.menu.add_separator()
        self.menu.add_command(label="Import Connections...", command=self.import_connections)
        self.menu.add_command(label="Export Connections...", command=self.export_connections)
        self.menu.add_separator()
        self.menu.add_command(label="Exit", command=self.exit_app)
    
    def new_connection(self):
        # Open the equipment manager's add dialog
        if hasattr(self.app, 'equipment_manager'):
            self.app.equipment_manager.add_equipment()
    
    def quick_connect(self):
        # Implement quick connect dialog
        # This would be a simplified version of the add equipment dialog
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Quick Connect")
        dialog.geometry("400x250")
        dialog.transient(self.app.root)
        dialog.grab_set()
        
        # Connection properties
        ttk.Label(dialog, text="Hostname:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        hostname_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=hostname_var).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(dialog, text="Port:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        port_var = tk.StringVar(value="22")
        ttk.Entry(dialog, textvariable=port_var).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(dialog, text="Username:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        username_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=username_var).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(dialog, text="Password:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        password_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=password_var, show="*").grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        def connect():
            # Validate inputs
            hostname = hostname_var.get().strip()
            port = port_var.get().strip()
            username = username_var.get().strip()
            password = password_var.get()
            
            if not hostname or not port or not username:
                messagebox.showerror("Error", "Please fill all required fields")
                return
                
            try:
                port_num = int(port)
                if port_num <= 0 or port_num > 65535:
                    raise ValueError("Invalid port number")
            except ValueError:
                messagebox.showerror("Error", "Port must be a valid number (1-65535)")
                return
            
            # Create temporary profile for connection
            temp_profile = {
                "id": "temp_" + str(int(time.time())),
                "name": f"{username}@{hostname}",
                "hostname": hostname,
                "port": port,
                "username": username,
                "password": password,
                "temporary": True  # Mark as temporary
            }
            
            # Close dialog
            dialog.destroy()
            
            # Connect using the temporary profile
            self.app.connect_to_equipment(temp_profile)
        
        ttk.Button(btn_frame, text="Connect", command=connect).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Make dialog responsive
        dialog.columnconfigure(1, weight=1)
        
        # Center dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Set focus to hostname field
        hostname_var.get_children()[0].focus()
    
    def import_connections(self):
        # Open file dialog to select a file to import connections from
        filename = filedialog.askopenfilename(
            title="Import Connections",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            # Implement import logic
            messagebox.showinfo("Import", f"Importing connections from {filename}")
    
    def export_connections(self):
        # Open file dialog to select where to save connections
        filename = filedialog.asksaveasfilename(
            title="Export Connections",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            # Implement export logic
            messagebox.showinfo("Export", f"Exporting connections to {filename}")
    
    def exit_app(self):
        # Confirm before exiting
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.app.root.destroy()
    
    def create_folder(self):
        # Get the current tab to determine if we're in SFTP browser
        current_tab = self.app.tab_manager.notebook.select()
        if not current_tab:
            return
            
        # Find tab info
        for tab_id, tab_info in self.app.tab_manager.tabs.items():
            if tab_info["frame"] == current_tab:
                client = tab_info.get("client")
                if client and hasattr(client, "file_operations"):
                    # Determine if we should create local or remote folder
                    # based on which pane has focus
                    focused = self.app.root.focus_get()
                    
                    if hasattr(client.sftp_browser, "local_tree") and focused == client.sftp_browser.local_tree:
                        client.file_operations.create_local_folder()
                    elif hasattr(client.sftp_browser, "remote_tree") and focused == client.sftp_browser.remote_tree:
                        client.file_operations.create_remote_folder()
                    else:
                        # Default to local folder if can't determine focus
                        client.file_operations.create_local_folder()
                    return
        
        # If we get here, we're not in a tab with SFTP browser
        messagebox.showinfo("Create Folder", "Please open an SFTP connection first")