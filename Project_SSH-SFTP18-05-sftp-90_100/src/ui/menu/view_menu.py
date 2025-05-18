import tkinter as tk
from tkinter import ttk

class ViewMenu:
    def __init__(self, menubar, app):
        self.app = app
        
        # Create View menu
        self.menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=self.menu)
        
        # View toggles
        app.show_equipment_var = tk.BooleanVar(value=True)
        app.show_ssh_var = tk.BooleanVar(value=True)
        app.show_sftp_var = tk.BooleanVar(value=True)
        
        self.menu.add_checkbutton(label="Show Equipment Panel", 
                                 variable=app.show_equipment_var,
                                 command=lambda: self.toggle_equipment_panel())
        self.menu.add_checkbutton(label="Show SSH Terminal", 
                                 variable=app.show_ssh_var,
                                 command=lambda: self.toggle_ssh_terminal(app.show_ssh_var.get()))
        self.menu.add_checkbutton(label="Show SFTP Browser", 
                                 variable=app.show_sftp_var,
                                 command=lambda: self.toggle_sftp_browser(app.show_sftp_var.get()))
    
    def toggle_equipment_panel(self):
        """Toggle visibility of equipment panel"""
        if self.app.show_equipment_var.get():
            self.app.equipment_frame.pack(fill=tk.BOTH, expand=True)
            self.app.main_paned.add(self.app.equipment_frame, weight=1)
        else:
            self.app.main_paned.forget(self.app.equipment_frame)
            
        # Force update to refresh the UI
        self.app.root.update_idletasks()
        
        # Adjust tab content after equipment panel toggle
        self.refresh_tab_layouts()
        
        # Redraw terminal to handle the new panel area
        self.redraw_terminals_in_tabs()

    def toggle_ssh_terminal(self, show):
        """Toggle visibility of SSH terminal in all tabs"""
        # Apply to all tabs
        for tab_id, tab_info in self.app.tab_manager.tabs.items():
            client = tab_info.get("client")
            if client and hasattr(client, "terminal_emulator"):
                # Find the terminal frame
                ssh_frame = None
                
                for child in client.main_frame.winfo_children():
                    if hasattr(child, 'cget') and 'text' in child.keys():
                        if "SSH" in child.cget("text"):
                            ssh_frame = child
                            break
                
                if ssh_frame:
                    if show:
                        ssh_frame.pack(fill=tk.BOTH, expand=True)
                    else:
                        ssh_frame.pack_forget()
        
        # Refresh all tab layouts after toggling
        self.refresh_tab_layouts()
        
        # Redraw terminal to handle the new panel area
        self.redraw_terminals_in_tabs()

    def toggle_sftp_browser(self, show):
        """Toggle visibility of SFTP browser in all tabs"""
        # Apply to all tabs
        for tab_id, tab_info in self.app.tab_manager.tabs.items():
            client = tab_info.get("client")
            if client and hasattr(client, "sftp_browser"):
                # Find the SFTP browser frame
                sftp_frame = None
                
                for child in client.main_frame.winfo_children():
                    if hasattr(child, 'cget') and 'text' in child.keys():
                        if "SFTP" in child.cget("text"):
                            sftp_frame = child
                            break
                
                if sftp_frame:
                    if show:
                        sftp_frame.pack(fill=tk.BOTH, expand=True)
                    else:
                        sftp_frame.pack_forget()
        
        # Refresh all tab layouts after toggling
        self.refresh_tab_layouts()
        
        # Redraw terminal to handle the new panel area
        self.redraw_terminals_in_tabs()
    
    def refresh_tab_layouts(self):
        """Refresh the layout of all tabs to ensure proper sizing"""
        for tab_id, tab_info in self.app.tab_manager.tabs.items():
            client = tab_info.get("client")
            if client and hasattr(client, "main_frame"):
                # Find SSH and SFTP frames
                ssh_frame = None
                sftp_frame = None
                
                for child in client.main_frame.winfo_children():
                    if hasattr(child, 'cget') and 'text' in child.keys():
                        if "SSH" in child.cget("text"):
                            ssh_frame = child
                        elif "SFTP" in child.cget("text"):
                            sftp_frame = child
                
                # Unpack all frames first
                if ssh_frame and ssh_frame.winfo_manager() == 'pack':
                    ssh_frame.pack_forget()
                if sftp_frame and sftp_frame.winfo_manager() == 'pack':
                    sftp_frame.pack_forget()
                
                # Repack visible frames with appropriate weights
                if self.app.show_ssh_var.get() and ssh_frame:
                    ssh_frame.pack(fill=tk.BOTH, expand=True)
                
                if self.app.show_sftp_var.get() and sftp_frame:
                    sftp_frame.pack(fill=tk.BOTH, expand=True)
                
                # Force update to refresh the UI
                client.main_frame.update_idletasks()
                self.app.root.update_idletasks()
    
    def redraw_terminals_in_tabs(self):
        """Redraw all terminals in tabs to handle the new panel area"""
        for tab_id, tab_info in self.app.tab_manager.tabs.items():
            client = tab_info.get("client")
            if client and hasattr(client, "terminal_emulator") and client.connected:
                # Call handle_resize to redraw the terminal
                client.terminal_emulator.handle_resize()
