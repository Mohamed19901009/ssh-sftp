import tkinter as tk
from tkinter import messagebox, Toplevel, Text, Scrollbar
import webbrowser

class HelpMenu:
    def __init__(self, menubar, app):
        self.app = app
        
        # Create Help menu
        self.menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=self.menu)
        
        # Add menu items - only Documentation and About
        self.menu.add_command(label="Documentation", command=self.show_documentation, accelerator="F1")
        self.menu.add_separator()
        self.menu.add_command(label="About", command=self.show_about)
    
    def show_documentation(self):
        # Create documentation window
        doc_window = Toplevel(self.app.root)
        doc_window.title("SSH-SFTP Client Documentation")
        doc_window.geometry("800x600")
        doc_window.transient(self.app.root)
        
        # Add scrollable text widget
        frame = tk.Frame(doc_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text = Text(frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text.yview)
        
        # Add documentation content
        documentation = """
# Enhanced SSH-SFTP Client User Guide

## Table of Contents
1. Introduction
2. Getting Started
3. Equipment Management
4. SSH Terminal
5. SFTP File Browser
6. Macros and Batch Commands
7. Settings and Preferences
8. Keyboard Shortcuts
9. Troubleshooting

## 1. Introduction

Enhanced SSH-SFTP Client is a powerful application for managing SSH connections and SFTP file transfers. It provides a tabbed interface for multiple connections, equipment management, and advanced features for power users.

## 2. Getting Started

### Installation
The application is portable and requires no installation. Simply run the executable file to start.

### First Launch
On first launch, you'll see a welcome tab with basic instructions. The equipment panel on the right side allows you to manage your connections.

### Quick Connect
To quickly connect to a server:
1. Go to File > Quick Connect
2. Enter the hostname, port, username, and password/key file
3. Click Connect

## 3. Equipment Management

### Adding Equipment
1. In the equipment panel, click "Add"
2. Fill in the connection details:
   - Name: A friendly name for the connection
   - Hostname: The server address
   - Port: SSH port (default: 22)
   - Username: Your login username
   - Authentication: Password or Key File
3. Click Save

### Connecting to Equipment
- Double-click on an equipment entry to connect
- Right-click for additional options

### Organizing Equipment
- Use folders to organize your connections
- Drag and drop to rearrange

## 4. SSH Terminal

### Basic Usage
- Type commands in the terminal window
- Use the up/down arrows to navigate command history

### Terminal Settings
- Go to Settings > Terminal to customize:
  - Font and size
  - Color scheme
  - Buffer size
  - Key mappings

### Multiple Sessions
- Open multiple tabs for different connections
- Switch between tabs to manage multiple sessions

## 5. SFTP File Browser

### Navigating Files
- The SFTP browser shows local files on the left and remote files on the right
- Double-click folders to navigate
- Use the path bar to enter specific paths

### File Operations
- Drag and drop files to transfer
- Right-click for context menu with options:
  - Upload/Download
  - Create folder
  - Rename
  - Delete
  - Change permissions

### Bookmarks
- Add bookmarks for frequently accessed locations
- Access bookmarks from the View menu

## 6. Macros and Batch Commands

### Creating Batch Commands
1. Go to Macros > Create Batch
2. Enter a name for the batch
3. Add commands (one per line)
4. Click Save

### Managing Batches
- Go to Macros > Manage Batches
- Edit or delete existing batches

### Executing Batches
- Select a batch from the Macros menu
- Confirm execution on the current SSH connection

## 7. Settings and Preferences

### Application Settings
- Go to Settings > Preferences
- Customize general application behavior

### Connection Defaults
- Set default parameters for new connections

### Appearance
- Choose between light and dark themes
- Customize colors and fonts

## 8. Keyboard Shortcuts

### General
- F1: Documentation
- Ctrl+T: New Tab
- Ctrl+W: Close Tab
- Ctrl+Tab: Next Tab
- Ctrl+Shift+Tab: Previous Tab

### Terminal
- Ctrl+C: Copy selected text
- Ctrl+V: Paste
- Ctrl+F: Find
- Ctrl+A: Select All

### File Browser
- F5: Refresh
- F2: Rename
- Delete: Delete file/folder
- Ctrl+N: New folder

## 9. Troubleshooting

### Connection Issues
- Verify hostname, port, username, and password/key
- Check network connectivity
- Ensure the SSH service is running on the server

### File Transfer Problems
- Check file permissions
- Verify available disk space
- Try smaller files first

### Application Errors
- Check the log file in ~/.ssh-sftp-client/logs
- Restart the application
- Update to the latest version

### Getting Help
- Check online resources
- Contact support
"""
        
        text.insert(tk.END, documentation)
        text.config(state=tk.DISABLED)  # Make text read-only
        
        # Add close button
        close_button = tk.Button(doc_window, text="Close", command=doc_window.destroy)
        close_button.pack(pady=10)
    
    def show_about(self):
        # Show about dialog
        about_text = """Enhanced SSH-SFTP Client
Version 1.0.0

A powerful SSH and SFTP client with tabbed interface,
equipment management, and advanced features.

© 2023 Your Organization"""
        messagebox.showinfo("About", about_text)