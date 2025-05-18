import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
import sys
import json
import logging
from pathlib import Path
from src.app import SSHClientApp
from src.ui.equipment_manager import EquipmentManager
from src.ui.tab_manager import TabManager
from src.ui.menu.menubar import create_menubar
from src.utils.logger import setup_logger

class EnhancedSSHSFTPClient:
    def __init__(self, root):
        # Store the root window
        self.root = root
        self.root.title("Enhanced SSH-SFTP Client")
        
        # Set window to full screen
        self.root.state('zoomed')  # For Windows
        # self.root.attributes('-zoomed', True)  # For Linux
        
        # Set minimum size
        self.root.minsize(800, 600)
        
        # Initialize logger
        self.logger = setup_logger()
        
        # Load saved equipment profiles
        self.config_dir = Path.home() / ".ssh-sftp-client"
        self.config_file = self.config_dir / "equipment.json"
        self.equipment_profiles = self.load_equipment_profiles()
        
        # Create main layout
        self.setup_layout()
        
        # Create menubar
        create_menubar(self)
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.logger.info("Application initialized")

    def setup_layout(self):
        # Main paned window to divide equipment panel and tabs
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Tab manager for connections (left side)
        self.tabs_frame = ttk.Frame(self.main_paned)
        self.tab_manager = TabManager(self.tabs_frame, self)
        self.main_paned.add(self.tabs_frame, weight=4)
        
        # Equipment manager panel (right side)
        self.equipment_frame = ttk.Frame(self.main_paned)
        self.equipment_manager = EquipmentManager(self.equipment_frame, self)
        self.main_paned.add(self.equipment_frame, weight=1)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Set initial pane positions (80% for tabs panel, 20% for equipment panel)
        self.root.update()
        width = self.main_paned.winfo_width()
        self.main_paned.sashpos(0, int(width * 0.8))

    def load_equipment_profiles(self):
        try:
            # Create config directory if it doesn't exist
            if not self.config_dir.exists():
                self.config_dir.mkdir(parents=True)
                
            # Create default config file if it doesn't exist
            if not self.config_file.exists():
                default_profiles = []
                with open(self.config_file, 'w') as f:
                    json.dump(default_profiles, f, indent=4)
                return default_profiles
                
            # Load existing profiles
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load equipment profiles: {str(e)}")
            return []

    def save_equipment_profiles(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.equipment_profiles, f, indent=4)
            self.logger.info("Equipment profiles saved")
        except Exception as e:
            self.logger.error(f"Failed to save equipment profiles: {str(e)}")

    def connect_to_equipment(self, profile):
        self.logger.info(f"Connecting to {profile['name']} ({profile['hostname']})")
        self.tab_manager.open_connection_tab(profile)

    def on_close(self):
        self.logger.info("Application closing")
        self.save_equipment_profiles()
        self.root.destroy()
if __name__ == "__main__":
    root = ttk.Window(themename="cosmo")
    app = EnhancedSSHSFTPClient(root)
    root.mainloop()