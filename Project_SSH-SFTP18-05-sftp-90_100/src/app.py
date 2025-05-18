import tkinter as tk
from tkinter import ttk, messagebox, font
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
from queue import Queue
import os
from pathlib import Path

from src.terminal.emulator import TerminalEmulator
from src.terminal.settings import TerminalSettings
from src.ssh.client import SSHClient
from src.sftp.browser import SFTPBrowser
from src.sftp.operations import FileOperations
from src.ui.styles import setup_styles
from src.ui.menu.network_menu import NetworkMenu

class SSHClientApp:
    # Keep only this __init__ method, which is designed for the tabbed interface
    def __init__(self, container, main_app, profile=None):
        self.container = container
        self.main_app = main_app
        self.profile = profile

        # Use main_app.root for the main window
        self.root = main_app.root

        # Initialize connection parameters
        self.hostname = tk.StringVar(value=profile.get("hostname", "") if profile else "localhost")
        self.username = tk.StringVar(value=profile.get("username", "") if profile else "")
        self.password = tk.StringVar(value=profile.get("password", "") if profile else "")
        self.port = tk.StringVar(value=str(profile.get("port", 22)) if profile else "22")
        self.connected = False
        # Use main_app's status_var
        self.status_var = main_app.status_var

        # SSH connection
        # Remove duplicate initialization: self.connected = False
        self.queue = Queue()

        # Initialize remote_users and filesystem attributes
        self.remote_users = {}
        self.remote_is_linux = True

        # Initialize file paths for SFTP browser
        self.local_path = Path(str(Path.home()))
        self.remote_path = "/home" if self.remote_is_linux else "C:\\"

        # Add sorting attributes for SFTP browser
        self.local_sort_column = "Name"
        self.local_sort_reverse = False
        self.remote_sort_column = "Name"
        self.remote_sort_reverse = False

        # Initialize terminal settings first
        # Pass main_app.root
        self.terminal_settings = TerminalSettings(self.root)

        # Initialize components in the correct order
        self.terminal_emulator = TerminalEmulator(self)
        # Make sure to import SSHClient at the top of the file
        self.ssh_client = SSHClient(self)

        # Initialize file operations before SFTP browser
        self.file_operations = FileOperations(self)
        self.sftp_browser = SFTPBrowser(self.container, self) # Pass self.container as master and self as app

        # Create UI AFTER all components are initialized
        self.create_ui()

        # Connect to SSH with a delay to ensure everything is initialized
        if self.profile:
            self.root.after(500, self.delayed_connect)

    def delayed_connect(self):
        """Connect with proper error handling"""
        try:
            if self.profile and hasattr(self, 'ssh_client') and self.ssh_client:
                self.ssh_client.connect()
        except Exception as e:
            # Changed from self.parent_window
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}", parent=self.container)

    def create_ui(self):
        # Create main frame
        self.main_frame = ttk.Frame(self.container)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create terminal emulator
        self.terminal_emulator.create_terminal_frame(self.main_frame)

        # Create SFTP browser frame
        self.sftp_browser.create_browser_frame(self.main_frame)

        # Start terminal update loop
        self.root.after(100, self.terminal_emulator.update_terminal)

    # Remove the duplicate create_widgets method
    # def create_widgets(self):
    #     # Create your UI widgets here
    #     # Remove the connection form completely
    #     
    #     # Main content frame
    #     content_frame = ttk.Frame(self.root)
    #     content_frame.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
    
    # Create terminal frame
    # self.terminal_emulator.create_terminal_frame(content_frame)
    
    # Create SFTP browser frame
    # self.sftp_browser.create_browser_frame(content_frame)
    
    # Create menubar with terminal settings
    # self.create_menubar()
    
    # def create_menubar(self):
    #     # Initialize menubar variable to avoid UnboundLocalError
    #     menubar = None
    
    # For tabbed interface, we shouldn't try to set a menubar on a Frame
    # if self.parent_window:
    #     # Don't try to set a menu on a Frame widget
    #     pass
    # else:
    #     # For standalone window, create and set the menubar
    #     menubar = tk.Menu(self.root)
    
    # File menu
    # file_menu = tk.Menu(menubar, tearoff=0)
    # menubar.add_cascade(label="File", menu=file_menu)
    # file_menu.add_separator()
    # file_menu.add_command(label="Exit", command=lambda: self.root.destroy())
    
    # Terminal menu
    # terminal_menu = tk.Menu(menubar, tearoff=0)
    # menubar.add_cascade(label="Terminal", menu=terminal_menu)
    
    # Set the menubar for the window
    # self.root.config(menu=menubar)
    
    # Remove the second part that tries to access menubar when it might not be defined
    # The following code should be removed:
    # if self.parent_window:
    #     self.root.config(menu=menubar)
    # else:
    #     self.root.config(menu=menubar)
    
    # For tabbed interface, add menu buttons to the tab
    # if self.parent_window:
    #     # Remove the entire menu_frame since we're moving settings to the main menubar
    #     # menu_frame = ttk.Frame(self.container)
    #     # menu_frame.pack(fill=tk.X, side=tk.TOP)
    
    # Remove settings button
    # settings_btn = ttk.Menubutton(menu_frame, text="Settings")
    # settings_btn.menu = terminal_menu
    # settings_btn["menu"] = settings_btn.menu
    # settings_btn.pack(side=tk.LEFT)
    
    # Remove the disconnect button
    # ttk.Button(menu_frame, text="Disconnect", style="secondary.TButton", 
    #           command=self.ssh_client.disconnect).pack(side=tk.RIGHT, padx=5)
    
    # Set the menubar for the window
    # self.root.config(menu=menubar)
    # else:
    #     # For standalone window, set the menubar
    #     self.root.config(menu=menubar)
    # network_menu = NetworkMenu(menubar, self)
    
    # def auto_connect(self):
    #     """Automatically connect using the profile information"""
    #     if not self.profile:
    #         return
    
    # Extract connection details from profile
    # self.hostname.set(self.profile.get("hostname", ""))
    # self.username.set(self.profile.get("username", ""))
    # self.password.set(self.profile.get("password", ""))
    # self.port.set(str(self.profile.get("port", 22)))
    
    # Connect using the SSH client with a small delay to ensure UI is ready
    # if self.ssh_client and hasattr(self.ssh_client, "connect"):
    #     self.root.after(500, self.ssh_client.connect)  # Increased delay for reliability
    
    # def connect(self):
    #     """Connect to SSH server using the profile information"""
    #     if self.ssh_client and hasattr(self.ssh_client, "connect"):
    #         self.ssh_client.connect()
    #     else:
    #         self.auto_connect()
    
    # def connect(self, hostname, port, username, password=None, private_key=None):
    #     """Establish SSH connection"""
    #     try:
    #         # Your connection code here
    
    #         # On successful connection:
    #         self.connected = True
    
    #         # Update UI
    #         self.disconnect_btn.config(state=tk.NORMAL)
    
    #         # Hide the connection form and show the terminal/file browser
    #         self.connection_form.pack_forget()
    #         self.terminal_frame.pack(fill=tk.BOTH, expand=True)
    
    #         # Add terminal/file browser content
    #         terminal_label = ttk.Label(self.terminal_frame, text=f"Terminal for {username}@{hostname}")
    #         terminal_label.pack(pady=20)
    
    #         # You would add your actual terminal/file browser implementation here
    
    #     except Exception as e:
    #         from tkinter import messagebox
    #         messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}", parent=self.parent_window)
    
    # def disconnect(self):
    #     """Disconnect from the server"""
    #     # Your disconnect code here
    #     self.connected = False
    
    # Update UI
    # self.disconnect_btn.config(state=tk.DISABLED)
    
    # Hide terminal and show connection form
    # self.terminal_frame.pack_forget()
    # self.connection_form.pack(fill=tk.BOTH, expand=True)
    
    # def show_settings(self):
    #     """Show connection settings dialog"""
    #     from tkinter import messagebox
    #     messagebox.showinfo("Settings", "Settings dialog not implemented yet", parent=self.parent_window)

    def show_error(self, message):
        """Display error message in a dialog box"""
        messagebox.showerror("SFTP Warning", message, parent=self.container)

        
