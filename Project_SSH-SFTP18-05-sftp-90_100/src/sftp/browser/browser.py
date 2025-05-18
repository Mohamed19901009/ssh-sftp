import tkinter as tk
from tkinter import ttk, Menu
import os
import stat
import time
from pathlib import Path
import tempfile

from .file_types import FileTypeManager
from .tree_manager import TreeManager
from .context_menu import ContextMenuManager

class SFTPBrowser:
    def __init__(self, master, app):
        self.app = app
        self.master = master
        self.remote_tree = None
        self.remote_path_var = None
        self.remote_path_entry = None
        self.remote_context_menu = None
        self.uid_to_username_cache = {}
        
        # Initialize managers
        self.file_types = FileTypeManager()
        self.tree_manager = TreeManager(self)
        self.context_menu = ContextMenuManager(self)

    def create_browser_frame(self, parent):
        # SFTP browser frame
        sftp_frame = ttk.LabelFrame(parent, text="SFTP Browser")
        sftp_frame.pack(fill=tk.BOTH, expand=True)

        # Remote browser
        remote_frame = ttk.LabelFrame(sftp_frame, text="Remote Files")
        remote_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self._create_remote_path_frame(remote_frame)
        self._create_remote_tree_frame(remote_frame)

    def _create_remote_path_frame(self, parent):
        remote_path_frame = ttk.Frame(parent)
        remote_path_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(remote_path_frame, text="Path:").pack(side=tk.LEFT)
        self.remote_path_var = tk.StringVar(value=self.app.remote_path)
        self.remote_path_entry = ttk.Entry(remote_path_frame, textvariable=self.remote_path_var)
        self.remote_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.remote_path_entry.bind("<Return>", lambda event: self.goto_remote_path())

        ttk.Button(remote_path_frame, text="Go", style="outline.TButton", 
                  command=self.goto_remote_path).pack(side=tk.LEFT, padx=2)
        ttk.Button(remote_path_frame, text="Back", style="outline.TButton", 
                  command=self.go_remote_back).pack(side=tk.LEFT, padx=2)

    def _create_remote_tree_frame(self, parent):
        remote_tree_frame = ttk.Frame(parent, style="TreeviewBorder.TFrame")
        remote_tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.remote_tree = self.tree_manager.create_remote_tree(remote_tree_frame)
        self.remote_tree.pack(fill=tk.BOTH, expand=True)
        self.remote_tree.bind("<Double-1>", self.on_remote_double_click)
        self.remote_tree.bind("<Button-3>", self.context_menu.show_remote_context_menu)

        self.remote_context_menu = self.context_menu.create_remote_context_menu()

    def goto_remote_path(self):
        try:
            path = self.remote_path_var.get().strip()
            if not path:
                return
                
            # Normalize path separators for the remote system
            if self.app.remote_is_linux:
                path = path.replace('\\', '/')
                if not path.startswith('/'):
                    path = '/' + path
            else:
                path = path.replace('/', '\\')
                
            # Verify the path exists before setting it
            sftp = self.app.ssh_client.sftp_client
            try:
                sftp.stat(path)
                self.app.remote_path = path
                self.refresh_browsers()
            except IOError:
                self.app.show_error(f"Directory not found: {path}")
                # Reset path to current valid path
                self.remote_path_var.set(self.app.remote_path)
        except Exception as e:
            self.app.show_error(f"Error navigating to path: {str(e)}")

    def go_remote_back(self):
        try:
            current_path = self.app.remote_path
            if self.app.remote_is_linux:
                # For Linux systems
                if current_path == '/':
                    return  # Already at root
                parent_path = '/'.join(current_path.rstrip('/').split('/')[:-1])
                parent_path = '/' if not parent_path else parent_path
            else:
                # For Windows systems
                current_path = current_path.rstrip('\\')
                if current_path.endswith(':'):
                    return  # Already at drive root
                parent_path = '\\'.join(current_path.split('\\')[:-1])
                if not parent_path.endswith(':'):
                    parent_path += '\\'

            # Verify the parent path exists
            self.app.ssh_client.sftp_client.stat(parent_path)
            self.app.remote_path = parent_path
            self.remote_path_var.set(parent_path)
            self.refresh_browsers()
        except Exception as e:
            self.app.show_error(f"Cannot access parent directory: {str(e)}")

    def get_username_from_uid(self, uid):
        if uid in self.uid_to_username_cache:
            return self.uid_to_username_cache[uid]
        try:
            # Try to get username from /etc/passwd on Linux systems
            if self.app.remote_is_linux:
                stdin, stdout, stderr = self.app.ssh_client.ssh_client.exec_command(f"getent passwd {uid} | cut -d: -f1")
                username = stdout.read().decode().strip()
                if username:
                    self.uid_to_username_cache[uid] = username
                    return username
            return str(uid)  # Fallback to UID if username cannot be determined
        except Exception:
            return str(uid)

    def refresh_browsers(self):
        try:
            # Try to get existing SFTP client or create a new one
            if not self.app.ssh_client.sftp_client or self.app.ssh_client.sftp_client.sock.closed:
                self.app.ssh_client.sftp_client = self.app.ssh_client.ssh_client.open_sftp()
            
            sftp = self.app.ssh_client.sftp_client
            items = []
            for entry in sftp.listdir_attr(self.app.remote_path):
                name = entry.filename
                size = entry.st_size if not stat.S_ISDIR(entry.st_mode) else ""
                mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(entry.st_mtime))
                owner = self.get_username_from_uid(entry.st_uid)  # Convert UID to username
                permissions = stat.filemode(entry.st_mode)
                is_dir = stat.S_ISDIR(entry.st_mode)
                
                file_type = "directory" if is_dir else self.file_types.get_file_type(name)
                icon, color = self.file_types.get_file_icon_and_color(name, is_dir)
                
                items.append((icon, name, size, owner, permissions, mtime, color))
            
            self.tree_manager._sort_and_insert_items(self.remote_tree, items)
        except Exception as e:
            self.app.show_error(f"Error refreshing SFTP browser: {str(e)}")

    def on_remote_double_click(self, event):
        item = self.remote_tree.selection()[0]
        values = self.remote_tree.item(item)['values']
        if not values:
            return
            
        name = values[1]  # Name is the second column
        if values[2] == "":  # Empty size indicates a directory
            # Use proper path joining based on remote system type
            if self.app.remote_is_linux:
                # For Linux, use forward slashes
                new_path = self.app.remote_path.rstrip('/') + '/' + name
            else:
                # For Windows, use backslashes
                new_path = self.app.remote_path.rstrip('\\') + '\\' + name
            
            try:
                # Verify the path exists before setting it
                self.app.ssh_client.sftp_client.stat(new_path)
                self.app.remote_path = new_path
                self.remote_path_var.set(new_path)
                self.refresh_browsers()
            except Exception as e:
                self.app.show_error(f"Cannot access directory: {str(e)}")