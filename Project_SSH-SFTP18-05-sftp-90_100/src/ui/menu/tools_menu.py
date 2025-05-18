import tkinter as tk
from tkinter import ttk, messagebox
import threading

class ToolsMenu:
    def __init__(self, menubar, app):
        self.app = app
        
        # Create Tools menu
        self.menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=self.menu)
        
        # Add menu items
        self.menu.add_command(label="Port Scanner", command=self.port_scanner)
        self.menu.add_command(label="Network Diagnostics", command=self.network_diagnostics)
        self.menu.add_separator()
        self.menu.add_command(label="Key Generator", command=self.key_generator)
        self.menu.add_command(label="Certificate Manager", command=self.certificate_manager)
    
    def port_scanner(self):
        from src.ui.tools.port_scanner import open_port_scanner
        open_port_scanner(self.app.root)
    
    def network_diagnostics(self):
        from src.ui.tools.network_diagnostics import open_network_diagnostics
        open_network_diagnostics(self.app.root)
    
    def key_generator(self):
        from src.ui.tools.key_generator import open_key_generator
        open_key_generator(self.app.root)
    
    def certificate_manager(self):
        from src.ui.tools.certificate_manager import open_certificate_manager
        open_certificate_manager(self.app.root)