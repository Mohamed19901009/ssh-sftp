import tkinter as tk
from tkinter import ttk, Menu
import os
import stat
import time
from pathlib import Path
import logging
import paramiko
from paramiko import SSHClient, SFTPClient
from paramiko.ssh_exception import NoValidConnectionsError, AuthenticationException, SSHException
from paramiko.rsakey import RSAKey
from paramiko.ed25519key import Ed25519Key
from paramiko.dsskey import DSSKey
from paramiko.pkey import PKey
from tkinter import ttk, messagebox
import tempfile

class SFTPBrowser:
    def __init__(self, master, app):
        self.app = app
        self.master = master
        self.remote_tree = None
        self.remote_path_var = None
        self.remote_path_entry = None
        self.remote_context_menu = None
        self.uid_to_username_cache = {}
        
        # File type icons and colors - using consistent-width Unicode icons
        self.file_icons = {
            'default': ' 📄 ',  # Added spaces for consistent width
            'directory': ' 📁 ',
            'image': ' 🖼️ ',
            'video': ' 🎥 ',
            'audio': ' 🎵 ',
            'document': ' 📝 ',
            'archive': ' 📦 ',
            'code': ' 💻 ',
            'executable': ' ⚙️ ',
            'link': ' 🔗 '
        }
        
        self.extension_types = {
            # Images
            'jpg': 'image', 'jpeg': 'image', 'png': 'image', 'gif': 'image', 'bmp': 'image', 'svg': 'image',
            # Videos
            'mp4': 'video', 'avi': 'video', 'mkv': 'video', 'mov': 'video', 'wmv': 'video',
            # Audio
            'mp3': 'audio', 'wav': 'audio', 'flac': 'audio', 'm4a': 'audio', 'ogg': 'audio',
            # Documents
            'pdf': 'document', 'doc': 'document', 'docx': 'document', 'txt': 'document',
            'odt': 'document', 'rtf': 'document', 'md': 'document',
            # Archives
            'zip': 'archive', 'rar': 'archive', '7z': 'archive', 'tar': 'archive', 'gz': 'archive',
            # Code
            'py': 'code', 'java': 'code', 'cpp': 'code', 'h': 'code', 'js': 'code', 'html': 'code',
            'css': 'code', 'php': 'code', 'rb': 'code', 'go': 'code', 'rs': 'code',
            # Executables
            'exe': 'executable', 'msi': 'executable', 'app': 'executable', 'sh': 'executable',
            'bat': 'executable', 'cmd': 'executable'
        }
        
        self.type_colors = {
            'directory': '#4A90E2',  # Blue
            'image': '#27AE60',      # Green
            'video': '#E74C3C',      # Red
            'audio': '#F39C12',      # Orange
            'document': '#8E44AD',   # Purple
            'archive': '#D35400',    # Dark Orange
            'code': '#2ECC71',       # Light Green
            'executable': '#E67E22',  # Orange
            'link': '#95A5A6',       # Gray
            'default': '#000000'     # Black
        }

    def get_file_type(self, filename):
        if os.path.islink(filename):
            return 'link'
        if os.path.isdir(filename):
            return 'directory'
        
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        return self.extension_types.get(ext, 'default')

    def get_file_icon_and_color(self, filename, is_dir=False):
        if is_dir:
            return self.file_icons['directory'], self.type_colors['directory']
        
        file_type = self.get_file_type(filename)
        return self.file_icons.get(file_type, self.file_icons['default']), self.type_colors.get(file_type, self.type_colors['default'])

    def create_browser_frame(self, parent):
        # SFTP browser frame
        sftp_frame = ttk.LabelFrame(parent, text="SFTP Browser")
        sftp_frame.pack(fill=tk.BOTH, expand=True)

        # Remote browser
        remote_frame = ttk.LabelFrame(sftp_frame, text="Remote Files")
        remote_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Remote path frame
        remote_path_frame = ttk.Frame(remote_frame)
        remote_path_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(remote_path_frame, text="Path:").pack(side=tk.LEFT)
        self.remote_path_var = tk.StringVar(value=self.app.remote_path)
        ttk.Entry(remote_path_frame, textvariable=self.remote_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(remote_path_frame, text="Go", style="outline.TButton", 
                  command=self.goto_remote_path).pack(side=tk.LEFT, padx=2)
        ttk.Button(remote_path_frame, text="Back", style="outline.TButton", 
                  command=self.go_remote_back).pack(side=tk.LEFT, padx=2)

        # Remote tree frame
        remote_tree_frame = ttk.Frame(remote_frame, style="TreeviewBorder.TFrame")
        remote_tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Remote tree
        self.remote_tree = ttk.Treeview(
            remote_tree_frame,
            columns=("Icon", "Name", "Size", "Owner", "Permissions", "Modified"),
            show="headings",
            selectmode="extended"
        )
        self.remote_tree.heading("Icon", text="")
        self.remote_tree.heading("Name", text="Name", command=lambda: self.sort_column(self.remote_tree, "Name"))
        self.remote_tree.heading("Size", text="Size", command=lambda: self.sort_column(self.remote_tree, "Size"))
        self.remote_tree.heading("Owner", text="Owner", command=lambda: self.sort_column(self.remote_tree, "Owner"))
        self.remote_tree.heading("Permissions", text="Permissions", command=lambda: self.sort_column(self.remote_tree, "Permissions"))
        self.remote_tree.heading("Modified", text="Modified Date", command=lambda: self.sort_column(self.remote_tree, "Modified"))
        self.remote_tree.column("Icon", width=30, anchor="center")
        self.remote_tree.column("Name", width=150)
        self.remote_tree.column("Size", width=80)
        self.remote_tree.column("Owner", width=80)
        self.remote_tree.column("Permissions", width=80)
        self.remote_tree.column("Modified", width=120)
        self.remote_tree.pack(fill=tk.BOTH, expand=True)
        self.remote_tree.bind("<Double-1>", self.on_remote_double_click)
        self.remote_tree.bind("<Button-3>", self.show_remote_context_menu)

        # Setup path entries and context menus
        self.remote_path_entry = remote_path_frame.winfo_children()[1]
        self.remote_path_entry.bind("<Return>", lambda event: self.goto_remote_path())

        # Create context menus
        self.create_remote_context_menu()

    def create_remote_context_menu(self):
        self.remote_context_menu = Menu(self.app.root, tearoff=0)
        self.remote_context_menu.add_command(label="Upload", command=self.app.file_operations.upload_file)
        self.remote_context_menu.add_command(label="Download", command=self.app.file_operations.download_file)
        self.remote_context_menu.add_separator()
        self.remote_context_menu.add_command(label="Create File", command=self.app.file_operations.create_remote_file)
        self.remote_context_menu.add_command(label="Create Folder", command=self.app.file_operations.create_remote_folder)
        self.remote_context_menu.add_command(label="Delete", command=self.app.file_operations.delete_remote)
        self.remote_context_menu.add_separator()
        self.remote_context_menu.add_command(label="Refresh", command=self.refresh_browsers)

    def show_remote_context_menu(self, event):
        try:
            self.remote_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.remote_context_menu.grab_release()

    def refresh_browsers(self):
        # Check connection status and potentially clear cache
        if not self.app.connected:
            self._clear_uid_cache()

        # Clear tree
        for item in self.remote_tree.get_children():
            self.remote_tree.delete(item)
    
        # Update path entry
        self.remote_path_var.set(self.app.remote_path)
    
        # Populate remote browser
        if self.app.connected and self.app.ssh_client.sftp_client:
            try:
                remote_items = []
                seen_names = set()  # Track unique names to prevent duplicates
                
                # Prime the cache if it's empty and we are about to list files
                if not self.uid_to_username_cache:
                    self._get_remote_owner_name("") # Dummy call to potentially populate cache

                for file_attr in self.app.ssh_client.sftp_client.listdir_attr(self.app.remote_path):
                    # Skip if we've already seen this name
                    if file_attr.filename in seen_names:
                        continue
                    seen_names.add(file_attr.filename)
                    
                    is_dir = stat.S_ISDIR(file_attr.st_mode)
                    size_bytes = file_attr.st_size if not is_dir else ""
                    size_formatted = self._format_size(size_bytes) if not is_dir else ""
                    icon, color = self.get_file_icon_and_color(file_attr.filename, is_dir)
                    owner = self._get_remote_owner_name(file_attr.st_uid) 
                    permissions = stat.filemode(file_attr.st_mode) if file_attr.st_mode else "Unknown"
                    modified = self.format_mtime(file_attr.st_mtime)
                    remote_items.append((icon, file_attr.filename, size_formatted, owner, permissions, modified, color))
                
                # Sort and insert items
                self._sort_and_insert_items(self.remote_tree, remote_items)
                
            except Exception as e:
                self.remote_tree.insert("", tk.END, values=("", f"Error: {str(e)}", "", "", "", "Unknown", ""))

    def on_remote_double_click(self, event):
        if not self.app.connected:
            self.app.status_var.set("Not connected to server")
            return

        try:
            item = self.remote_tree.selection()[0]
            values = self.remote_tree.item(item, "values")
            name = values[1]  # Name is in the second column
            size = values[2]  # Size is in the third column
            is_dir = size == ""  # Directory if size is empty

            if is_dir:
                # Construct the new path properly
                new_path = os.path.join(self.app.remote_path, name).replace("\\", "/")
                if new_path.startswith("//"):
                    new_path = new_path[1:]
                
                # Verify the path exists
                try:
                    self.app.ssh_client.sftp_client.stat(new_path)
                    self.app.remote_path = new_path
                    self.refresh_browsers()
                    self.app.status_var.set(f"Changed remote directory to {new_path}")
                except IOError as e:
                    self.app.status_var.set(f"Cannot access directory: {str(e)}")
        except IndexError:
            pass  # No item selected
        except Exception as e:
            self.app.status_var.set(f"Error changing directory: {str(e)}")

    def goto_remote_path(self, event=None):
        if not self.app.connected:
            self.app.status_var.set("Not connected to server")
            return

        try:
            path = self.remote_path_var.get()
            # Normalize path to handle '..' and '.' correctly
            path = os.path.normpath(path)
            # Convert Windows-style paths to Unix-style for SFTP
            path = path.replace('\\', '/')
            # Ensure path starts with /
            if not path.startswith('/'):
                path = '/' + path
            
            # Split path into components and verify each level exists
            components = path.split('/')
            current_path = ''
            for component in components:
                if not component:  # Skip empty components
                    continue
                current_path = current_path + '/' + component if current_path else '/' + component
                try:
                    self.app.ssh_client.sftp_client.stat(current_path)
                except IOError:
                    raise Exception(f"Path component {current_path} does not exist or is not accessible")
                
            self.app.remote_path = path
            self.refresh_browsers()
            self.app.status_var.set(f"Changed remote directory to {path}")
        except Exception as e:
            self.app.status_var.set(f"Error changing directory: {str(e)}")

    def go_remote_back(self, event=None):
        if not self.app.connected:
            self.app.status_var.set("Not connected to server")
            return

        try:
            if self.app.remote_path != "/":
                parent = os.path.dirname(self.app.remote_path)
                if not parent:  # Empty string means we're at root
                    parent = "/"
                self.app.remote_path = parent
                self.refresh_browsers()
                self.app.status_var.set(f"Changed remote directory to {parent}")
        except Exception as e:
            self.app.status_var.set(f"Error going back: {str(e)}")

    def format_mtime(self, timestamp):
        """Format modification time for display"""
        try:
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        except Exception:
            return "Unknown"

    def _format_size(self, size_bytes):
        """Convert size in bytes to human-readable format (KB, MB, GB)."""
        if size_bytes == "":  # For directories
            return ""
        try:
            size_bytes = int(size_bytes)
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024**2:
                return f"{size_bytes/1024:.1f} KB"
            elif size_bytes < 1024**3:
                return f"{size_bytes/1024**2:.1f} MB"
            else:
                return f"{size_bytes/1024**3:.1f} GB"
        except ValueError:
            return "N/A"

    def _sort_and_insert_items(self, tree, items):
        # Clear existing items
        tree.delete(*tree.get_children())
        
        # Separate directories and files
        directories = []
        files = []
        seen_names = set()  # Track unique names
        
        for item_data in items:
            name = item_data[1]  # Name is at index 1
            if name in seen_names:
                continue
            seen_names.add(name)
            
            if item_data[2] == "":  # Directories have empty size
                directories.append(item_data)
            else:
                files.append(item_data)
        
        # Sort directories and files separately by name (case-insensitive)
        directories.sort(key=lambda x: x[1].lower())
        files.sort(key=lambda x: x[1].lower())
        
        # Insert directories first
        for item_data in directories:
            iid = tree.insert("", "end", values=item_data[:-1]) 
            tree.item(iid, tags=(iid,)) 
            tree.tag_configure(iid, foreground=item_data[-1])
        
        # Then insert files
        for item_data in files:
            iid = tree.insert("", "end", values=item_data[:-1])
            tree.item(iid, tags=(iid,))
            tree.tag_configure(iid, foreground=item_data[-1])

    def sort_column(self, tree, column):
        """Sort tree contents when a column header is clicked"""
        # Get all items in the tree
        items = [(tree.set(item, column), item) for item in tree.get_children('')]
        
        # If items exist and they're already sorted ascending, reverse the sort
        reverse = False
        if items and tree.set(items[0][1], column) == sorted(items)[0][0]:
            reverse = True
        
        # Sort items
        items.sort(reverse=reverse)
        
        # Rearrange items in sorted positions
        for index, (_, item) in enumerate(items):
            tree.move(item, '', index)

    def _clear_uid_cache(self):
        """Clears the UID to username cache."""
        self.uid_to_username_cache = {}

    def _get_remote_owner_name(self, uid):
        """Fetch username for a given UID from remote /etc/passwd."""
        uid_str = str(uid)
        if uid_str in self.uid_to_username_cache:
            return self.uid_to_username_cache[uid_str]

        if not self.app.connected or not self.app.ssh_client.sftp_client:
            return uid_str # Not connected, return UID

        if not self.uid_to_username_cache: 
            try:
                passwd_path = '/etc/passwd'
                # Create a unique temporary file name
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file_obj:
                    temp_passwd_file = tmp_file_obj.name
                
                self.app.ssh_client.sftp_client.get(passwd_path, temp_passwd_file)
                
                with open(temp_passwd_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        parts = line.strip().split(':')
                        if len(parts) > 2:
                            username = parts[0]
                            file_uid = parts[2]
                            self.uid_to_username_cache[file_uid] = username
                os.remove(temp_passwd_file) 
            except Exception as e:
                # Log this error appropriately in your application
                # print(f"Could not fetch or parse /etc/passwd: {e}") 
                # To prevent retrying on every item if /etc/passwd is inaccessible,
                # you might cache the failure for this UID for a short period or add a flag.
                # For now, it will return the UID if the fetch/parse fails.
                pass 

        return self.uid_to_username_cache.get(uid_str, uid_str) 

    def start_auto_refresh(self):
        """Start auto-refresh timer"""
        self.refresh_browsers()
        # Schedule next refresh in 5 seconds
        self.auto_refresh_id = self.master.after(5000, self.start_auto_refresh)

    def stop_auto_refresh(self):
        """Stop auto-refresh timer"""
        if self.auto_refresh_id:
            self.master.after_cancel(self.auto_refresh_id)
            self.auto_refresh_id = None