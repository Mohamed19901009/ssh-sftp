import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import os
from pathlib import Path
import webbrowser

# Import menu modules
from src.ui.menu.file_menu import FileMenu
from src.ui.menu.edit_menu import EditMenu
from src.ui.menu.view_menu import ViewMenu
from src.ui.menu.tools_menu import ToolsMenu  # If this exists
from src.ui.menu.macros_menu import MacrosMenu
from src.ui.menu.settings_menu import SettingsMenu
from src.ui.menu.help_menu import HelpMenu
from src.ui.menu.network_menu import NetworkMenu  # Add this import

def create_menubar(app):
    menubar = tk.Menu(app.root)
    
    # Initialize menu modules in the correct order
    file_menu = FileMenu(menubar, app)
    edit_menu = EditMenu(menubar, app)
    view_menu = ViewMenu(menubar, app)  # Make sure this is initialized
    
    # Add the other menus after View
    try:
        tools_menu = ToolsMenu(menubar, app)  # If this exists
    except Exception as e:
        print(f"Error loading Tools menu: {e}")
    
    macros_menu = MacrosMenu(menubar, app)
    network_menu = NetworkMenu(menubar, app)  # Add this line
    settings_menu = SettingsMenu(menubar, app)
    help_menu = HelpMenu(menubar, app)
    
    app.root.config(menu=menubar)
    return menubar

# Remove the view menu functions as they're now in the ViewMenu class
# Remove these functions:
# - toggle_equipment_panel
# - toggle_ssh_terminal
# - toggle_sftp_browser

# Keep other functions that might still be needed
def toggle_equipment_panel(app):
    """Toggle visibility of equipment panel"""
    if app.show_equipment_var.get():
        app.equipment_frame.pack(fill=tk.BOTH, expand=True)
        app.main_paned.add(app.equipment_frame, weight=1)
    else:
        app.main_paned.forget(app.equipment_frame)

def toggle_ssh_terminal(app):
    """Toggle visibility of SSH terminal in current tab"""
    current_tab = app.tab_manager.notebook.select()
    if not current_tab:
        return
        
    # Find tab info
    for tab_id, tab_info in app.tab_manager.tabs.items():
        if tab_info["frame"] == current_tab:
            client = tab_info.get("client")
            if client and hasattr(client, "toggle_ssh_terminal"):
                client.toggle_ssh_terminal(app.show_ssh_var.get())
            break

def toggle_sftp_browser(app):
    """Toggle visibility of SFTP browser in current tab"""
    current_tab = app.tab_manager.notebook.select()
    if not current_tab:
        return
        
    # Find tab info
    for tab_id, tab_info in app.tab_manager.tabs.items():
        if tab_info["frame"] == current_tab:
            client = tab_info.get("client")
            if client and hasattr(client, "toggle_sftp_browser"):
                client.toggle_sftp_browser(app.show_sftp_var.get())
            break

# Macros menu functions
def create_macro(app):
    """Create a new macro"""
    macro_window = tk.Toplevel(app.root)
    macro_window.title("Create Macro")
    macro_window.geometry("500x400")
    macro_window.transient(app.root)
    macro_window.grab_set()
    
    # Center the window
    macro_window.update_idletasks()
    width = macro_window.winfo_width()
    height = macro_window.winfo_height()
    x = (macro_window.winfo_screenwidth() // 2) - (width // 2)
    y = (macro_window.winfo_screenheight() // 2) - (height // 2)
    macro_window.geometry(f"{width}x{height}+{x}+{y}")
    
    # Macro name
    ttk.Label(macro_window, text="Macro Name:").pack(anchor=tk.W, padx=10, pady=5)
    name_var = tk.StringVar()
    ttk.Entry(macro_window, textvariable=name_var, width=40).pack(fill=tk.X, padx=10, pady=5)
    
    # Macro commands
    ttk.Label(macro_window, text="Commands (one per line):").pack(anchor=tk.W, padx=10, pady=5)
    commands_text = tk.Text(macro_window, height=15)
    commands_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    # Scrollbar for commands
    scrollbar = ttk.Scrollbar(commands_text, command=commands_text.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    commands_text.config(yscrollcommand=scrollbar.set)
    
    # Buttons
    btn_frame = ttk.Frame(macro_window)
    btn_frame.pack(fill=tk.X, padx=10, pady=10)
    
    def save_macro():
        name = name_var.get().strip()
        commands = commands_text.get("1.0", tk.END).strip().split("\n")
        
        if not name:
            messagebox.showerror("Error", "Please enter a macro name")
            return
            
        if not commands or not any(cmd.strip() for cmd in commands):
            messagebox.showerror("Error", "Please enter at least one command")
            return
            
        # Save macro (would be implemented with a proper macro system)
        # For now, just show a message
        app.logger.info(f"Macro '{name}' created with {len(commands)} commands")
        messagebox.showinfo("Macro Created", f"Macro '{name}' created successfully")
        macro_window.destroy()
    
    ttk.Button(btn_frame, text="Save", command=save_macro).pack(side=tk.RIGHT, padx=5)
    ttk.Button(btn_frame, text="Cancel", command=macro_window.destroy).pack(side=tk.RIGHT, padx=5)

def play_macro(app):
    """Play a saved macro"""
    # This would be implemented with a proper macro system
    # For now, just show a message
    messagebox.showinfo("Play Macro", "Macro playback functionality will be implemented here")

def manage_macros(app):
    """Manage saved macros"""
    # This would be implemented with a proper macro system
    # For now, just show a message
    messagebox.showinfo("Manage Macros", "Macro management functionality will be implemented here")

# Help menu functions
def show_documentation(app):
    """Show application documentation"""
    doc_window = tk.Toplevel(app.root)
    doc_window.title("Documentation")
    doc_window.geometry("700x500")
    doc_window.transient(app.root)
    
    # Center the window
    doc_window.update_idletasks()
    width = doc_window.winfo_width()
    height = doc_window.winfo_height()
    x = (doc_window.winfo_screenwidth() // 2) - (width // 2)
    y = (doc_window.winfo_screenheight() // 2) - (height // 2)
    doc_window.geometry(f"{width}x{height}+{x}+{y}")
    
    # Create notebook for documentation sections
    notebook = ttk.Notebook(doc_window)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Getting Started
    getting_started = ttk.Frame(notebook)
    notebook.add(getting_started, text="Getting Started")
    
    gs_text = tk.Text(getting_started, wrap=tk.WORD, padx=10, pady=10)
    gs_text.pack(fill=tk.BOTH, expand=True)
    
    gs_content = """
# Getting Started with Enhanced SSH-SFTP Client

## Introduction
Enhanced SSH-SFTP Client is a powerful tool for managing SSH connections and SFTP file transfers. This guide will help you get started with the basic features.

## Adding Equipment
1. Right-click in the Equipment panel and select "Add Equipment"
2. Enter the connection details (name, hostname, port, username, password)
3. Click "Save" to add the equipment to your list

## Connecting to Equipment
1. Double-click on an equipment item in the list, or
2. Right-click on an equipment item and select "Connect"
3. A new tab will open with the SSH connection

## Using SSH Terminal
Once connected, you can use the SSH terminal to run commands on the remote server.

## Using SFTP Browser
The SFTP browser allows you to browse and transfer files between your local machine and the remote server.
"""
    gs_text.insert(tk.END, gs_content)
    gs_text.config(state=tk.DISABLED)
    
    # Equipment Management
    equipment_mgmt = ttk.Frame(notebook)
    notebook.add(equipment_mgmt, text="Equipment Management")
    
    em_text = tk.Text(equipment_mgmt, wrap=tk.WORD, padx=10, pady=10)
    em_text.pack(fill=tk.BOTH, expand=True)
    
    em_content = """
# Equipment Management

## Organizing Equipment
- Create folders to organize your equipment
- Drag and drop equipment items to move them between folders
- Right-click on a folder to add new equipment or subfolders

## Equipment Properties
- Name: A friendly name for the equipment
- Hostname: The IP address or hostname of the equipment
- Port: The SSH port (default: 22)
- Username: The SSH username
- Password: The SSH password

## Importing and Exporting
- Use File > Import Topology to import equipment from a JSON file
- Use File > Export Topology to export your equipment to a JSON file
"""
    em_text.insert(tk.END, em_content)
    em_text.config(state=tk.DISABLED)
    
    # Macros
    macros_doc = ttk.Frame(notebook)
    notebook.add(macros_doc, text="Macros")
    
    macros_text = tk.Text(macros_doc, wrap=tk.WORD, padx=10, pady=10)
    macros_text.pack(fill=tk.BOTH, expand=True)
    
    macros_content = """
# Using Macros

## Creating Macros
1. Go to Macros > Create Macro
2. Enter a name for the macro
3. Enter the commands to be executed (one per line)
4. Click "Save" to save the macro

## Playing Macros
1. Connect to an equipment
2. Go to Macros > Play Macro
3. Select the macro to play
4. The macro commands will be executed in sequence

## Managing Macros
- Go to Macros > Manage Macros to view, edit, or delete your macros
"""
    macros_text.insert(tk.END, macros_content)
    macros_text.config(state=tk.DISABLED)
    
    # Close button
    ttk.Button(doc_window, text="Close", command=doc_window.destroy).pack(pady=10)

def show_about(app):
    """Show about dialog"""
    about_window = tk.Toplevel(app.root)
    about_window.title("About")
    about_window.geometry("400x300")
    about_window.transient(app.root)
    about_window.grab_set()
    
    # Center the window
    about_window.update_idletasks()
    width = about_window.winfo_width()
    height = about_window.winfo_height()
    x = (about_window.winfo_screenwidth() // 2) - (width // 2)
    y = (about_window.winfo_screenheight() // 2) - (height // 2)
    about_window.geometry(f"{width}x{height}+{x}+{y}")
    
    # App logo (placeholder)
    logo_frame = ttk.Frame(about_window)
    logo_frame.pack(pady=20)
    
    # App name and version
    ttk.Label(about_window, text="Enhanced SSH-SFTP Client", font=("Helvetica", 16, "bold")).pack()
    ttk.Label(about_window, text="Version 1.0.0").pack()
    
    # Copyright info
    ttk.Label(about_window, text="© 2023 Your Name/Company").pack(pady=10)
    
    # Description
    description = ttk.Label(about_window, text="A powerful SSH and SFTP client for managing remote connections", wraplength=350)
    description.pack(pady=10)
    
    # Close button
    ttk.Button(about_window, text="Close", command=about_window.destroy).pack(pady=20)