import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
import os
from pathlib import Path
import stat
import time
import posixpath

class FileOperations:
    def __init__(self, app):
        self.app = app

    def upload_file(self):
        if not self.app.connected:
            self.app.status_var.set("Not connected to server")
            return

        # Open file dialog to select files for upload
        filetypes = [("All files", "*.*")]
        filenames = filedialog.askopenfilenames(
            title="Select Files to Upload",
            filetypes=filetypes
        )

        if not filenames:
            return

        try:
            # Use current remote path as destination
            remote_dir = self.app.remote_path
            
            for local_path in filenames:
                name = os.path.basename(local_path)
                # Ensure proper path separator for remote system
                if self.app.remote_is_linux:
                    remote_path = posixpath.join(remote_dir, name).replace("\\", "/")
                else:
                    remote_path = os.path.join(remote_dir, name).replace("/", "\\")

                if os.path.isdir(local_path):
                    self._upload_directory(Path(local_path), remote_path)
                else:
                    self._upload_file(Path(local_path), remote_path)

            self.app.sftp_browser.refresh_browsers()
            self.app.status_var.set("Upload completed successfully")
        except Exception as e:
            self.app.status_var.set(f"Upload error: {str(e)}")
            messagebox.showerror("Upload Error", str(e))

    def download_file(self):
        if not self.app.connected:
            self.app.status_var.set("Not connected to server")
            return

        selected_items = self.app.sftp_browser.remote_tree.selection()
        if not selected_items:
            self.app.status_var.set("No remote files selected for download")
            return

        # Ask for local destination directory
        local_dir = filedialog.askdirectory(
            title="Select Download Location",
            initialdir=os.path.expanduser("~")
        )

        if not local_dir:
            return

        try:
            for item in selected_items:
                values = self.app.sftp_browser.remote_tree.item(item, "values")
                name = values[1]
                type_ = values[3]
                local_path = Path(local_dir) / name
                remote_path = posixpath.join(self.app.remote_path, name)

                if type_ == "Directory":
                    self._download_directory(remote_path, local_path)
                else:
                    self._download_file(remote_path, local_path)

            self.app.status_var.set("Download completed successfully")
        except Exception as e:
            self.app.status_var.set(f"Download error: {str(e)}")
            messagebox.showerror("Download Error", str(e))

    def _upload_file(self, local_path, remote_path):
        try:
            # Create progress bar frame
            progress_frame = ttk.Frame(self.app.container)  # Use container instead of root
            progress_frame.pack(fill=tk.X, padx=5, pady=5, side=tk.BOTTOM)  # Pack at bottom
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100)
            progress_bar.pack(fill=tk.X, side=tk.LEFT, expand=True)
            speed_label = ttk.Label(progress_frame, text="0 KB/s")
            speed_label.pack(side=tk.RIGHT, padx=5)

            # Get file size
            file_size = os.path.getsize(local_path)
            bytes_transferred = 0
            start_time = time.time()

            def callback(bytes_sent, _):
                nonlocal bytes_transferred
                bytes_transferred += bytes_sent
                progress = (bytes_transferred / file_size) * 100
                progress_var.set(progress)
                
                # Calculate speed
                elapsed_time = time.time() - start_time
                if elapsed_time > 0:
                    speed = bytes_transferred / elapsed_time
                    speed_text = self._format_speed(speed)
                    speed_label.config(text=speed_text)
                
                self.app.root.update()

            # Use paramiko's putfo with callback
            with open(str(local_path), 'rb') as local_file:
                self.app.ssh_client.sftp_client.putfo(local_file, remote_path, callback=callback)

            progress_frame.destroy()
            self.app.status_var.set(f"Uploaded {local_path} successfully")
        except Exception as e:
            if 'progress_frame' in locals():
                progress_frame.destroy()
            raise e

    def _download_file(self, remote_path, local_path):
        try:
            # Create progress bar frame
            progress_frame = ttk.Frame(self.app.container)  # Use container instead of root
            progress_frame.pack(fill=tk.X, padx=5, pady=5, side=tk.BOTTOM)  # Pack at bottom
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100)
            progress_bar.pack(fill=tk.X, side=tk.LEFT, expand=True)
            speed_label = ttk.Label(progress_frame, text="0 KB/s")
            speed_label.pack(side=tk.RIGHT, padx=5)

            # Get file size
            file_size = self.app.ssh_client.sftp_client.stat(remote_path).st_size
            bytes_transferred = 0
            start_time = time.time()

            def callback(bytes_received, _):
                nonlocal bytes_transferred
                bytes_transferred += bytes_received
                progress = (bytes_transferred / file_size) * 100
                progress_var.set(progress)
                
                # Calculate speed
                elapsed_time = time.time() - start_time
                if elapsed_time > 0:
                    speed = bytes_transferred / elapsed_time
                    speed_text = self._format_speed(speed)
                    speed_label.config(text=speed_text)
                
                self.app.root.update()

            # Use paramiko's getfo with callback
            with open(str(local_path), 'wb') as local_file:
                self.app.ssh_client.sftp_client.getfo(remote_path, local_file, callback=callback)

            progress_frame.destroy()
            self.app.status_var.set(f"Downloaded {remote_path} successfully")
        except Exception as e:
            if 'progress_frame' in locals():
                progress_frame.destroy()
            raise e

    def _format_speed(self, bytes_per_second):
        if bytes_per_second < 1024:
            return f"{bytes_per_second:.1f} B/s"
        elif bytes_per_second < 1024 ** 2:
            return f"{bytes_per_second / 1024:.1f} KB/s"
        elif bytes_per_second < 1024 ** 3:
            return f"{bytes_per_second / (1024 ** 2):.1f} MB/s"
        else:
            return f"{bytes_per_second / (1024 ** 3):.1f} GB/s"

    def _upload_directory(self, local_path, remote_path):
        # Create remote directory if it doesn't exist
        try:
            self.app.ssh_client.sftp_client.stat(remote_path)
        except FileNotFoundError:
            self.app.ssh_client.sftp_client.mkdir(remote_path)

        # Upload all files in the directory
        for item in local_path.iterdir():
            local_item_path = local_path / item.name
            remote_item_path = posixpath.join(remote_path, item.name)

            if item.is_dir():
                self._upload_directory(local_item_path, remote_item_path)
            else:
                self._upload_file(local_item_path, remote_item_path)

    def download_file(self):
        if not self.app.connected:
            self.app.status_var.set("Not connected to server")
            return

        selected_items = self.app.sftp_browser.remote_tree.selection()
        if not selected_items:
            self.app.status_var.set("No remote files selected for download")
            return

        # Ask for local destination directory
        local_dir = filedialog.askdirectory(
            title="Select Local Destination Directory",
            initialdir=str(self.app.local_path)
        )

        if not local_dir:
            return

        try:
            for item in selected_items:
                values = self.app.sftp_browser.remote_tree.item(item, "values")
                name = values[1]
                type_ = values[3]
                # Use the current local directory path
                local_path = self.app.local_path / name
                # Use posixpath for remote paths
                remote_path = posixpath.join(self.app.remote_path, name)

                if type_ == "Directory":
                    self._download_directory(remote_path, local_path)
                else:
                    self._download_file(remote_path, local_path)

            self.app.sftp_browser.refresh_browsers()
            self.app.status_var.set("Download completed successfully")
        except Exception as e:
            self.app.status_var.set(f"Download error: {str(e)}")
            messagebox.showerror("Download Error", str(e))

    def _download_directory(self, remote_path, local_path):
        # Create local directory if it doesn't exist
        if not local_path.exists():
            local_path.mkdir(parents=True)

        # Download all files in the directory
        for fileattr in self.app.ssh_client.sftp_client.listdir_attr(remote_path):
            remote_item_path = posixpath.join(remote_path, fileattr.filename)
            local_item_path = local_path / fileattr.filename

            if stat.S_ISDIR(fileattr.st_mode):
                self._download_directory(remote_item_path, local_item_path)
            else:
                self._download_file(remote_item_path, local_item_path)

    def create_remote_file(self):
        if not self.app.connected:
            self.app.status_var.set("Not connected to server")
            return

        filename = simpledialog.askstring("Create Remote File", "Enter file name:")
        if not filename:
            return

        try:
            # Use posixpath for remote paths
            path = posixpath.join(self.app.remote_path, filename)
            
            # Check if a directory with the same name exists
            try:
                stat_result = self.app.ssh_client.sftp_client.stat(path)
                if stat.S_ISDIR(stat_result.st_mode):
                    messagebox.showerror("Error", f"A folder named '{filename}' already exists")
                    return
                # If it's a file, ask for overwrite
                if not messagebox.askyesno("File Exists", f"File {filename} already exists. Overwrite?"):
                    return
            except FileNotFoundError:
                pass  # File doesn't exist, we can create it
                
            # Create empty file on remote server
            with self.app.ssh_client.sftp_client.open(path, 'w') as f:
                pass
            self.app.sftp_browser.refresh_browsers()
            self.app.status_var.set(f"Created remote file: {filename}")
        except Exception as e:
            self.app.status_var.set(f"Error creating remote file: {str(e)}")
            messagebox.showerror("Error", str(e))
    
    def create_remote_folder(self):
        if not self.app.connected:
            self.app.status_var.set("Not connected to server")
            return

        foldername = simpledialog.askstring("Create Remote Folder", "Enter folder name:")
        if not foldername:
            return

        try:
            # Use posixpath for remote paths
            path = posixpath.join(self.app.remote_path, foldername)
            
            # Check if a file with the same name exists
            try:
                stat_result = self.app.ssh_client.sftp_client.stat(path)
                if not stat.S_ISDIR(stat_result.st_mode):
                    messagebox.showerror("Error", f"A file named '{foldername}' already exists")
                    return
                # If it's a directory, ask for continue
                if not messagebox.askyesno("Folder Exists", f"Folder {foldername} already exists. Continue?"):
                    return
            except FileNotFoundError:
                pass  # Folder doesn't exist, we can create it
                
            self.app.ssh_client.sftp_client.mkdir(path)
            self.app.sftp_browser.refresh_browsers()
            self.app.status_var.set(f"Created remote folder: {foldername}")
        except Exception as e:
            self.app.status_var.set(f"Error creating remote folder: {str(e)}")
            messagebox.showerror("Error", str(e))

    def delete_remote(self):
        if not self.app.connected:
            self.app.status_var.set("Not connected to server")
            return

        selected_items = self.app.sftp_browser.remote_tree.selection()
        if not selected_items:
            self.app.status_var.set("No remote files selected for deletion")
            return

        file_names = [self.app.sftp_browser.remote_tree.item(item, "values")[1] for item in selected_items]
        if not messagebox.askyesno("Confirm Deletion", f"Delete {len(file_names)} remote items?\n{', '.join(file_names[:5])}{'...' if len(file_names) > 5 else ''}"):
            return

        try:
            for item in selected_items:
                values = self.app.sftp_browser.remote_tree.item(item, "values")
                name = values[1]
                type_ = values[2]  # Changed from index 3 to 2 to match tree view structure
                # Normalize path for remote system
                path = posixpath.join(self.app.remote_path, name).replace('\\', '/')

                try:
                    if not type_:  # Empty size indicates a directory
                        self._rmdir_recursive(path)
                    else:
                        self.app.ssh_client.sftp_client.remove(path)
                except FileNotFoundError:
                    # Skip if file/directory no longer exists
                    continue
                except PermissionError:
                    messagebox.showerror("Permission Error", f"Cannot delete {name}: Permission denied")
                    continue

            self.app.sftp_browser.refresh_browsers()
            self.app.status_var.set(f"Deleted {len(selected_items)} remote items")
        except Exception as e:
            self.app.status_var.set(f"Deletion error: {str(e)}")
            messagebox.showerror("Deletion Error", str(e))

    def _rmdir_recursive(self, path):
        try:
            # List directory contents
            for fileattr in self.app.ssh_client.sftp_client.listdir_attr(path):
                filepath = posixpath.join(path, fileattr.filename).replace('\\', '/')
                try:
                    if stat.S_ISDIR(fileattr.st_mode):
                        self._rmdir_recursive(filepath)
                    else:
                        self.app.ssh_client.sftp_client.remove(filepath)
                except (FileNotFoundError, PermissionError) as e:
                    # Log error but continue with deletion
                    self.app.status_var.set(f"Error deleting {fileattr.filename}: {str(e)}")
                    continue

            # Remove the empty directory
            self.app.ssh_client.sftp_client.rmdir(path)
        except Exception as e:
            raise Exception(f"Failed to delete directory {path}: {str(e)}")

    def open_remote_file(self):
        if not self.app.connected:
            self.app.status_var.set("Not connected to server")
            return

        selected_items = self.app.sftp_browser.remote_tree.selection()
        if not selected_items:
            self.app.status_var.set("No file selected")
            return

        try:
            # Get the selected file info
            item = selected_items[0]  # Open only the first selected file
            values = self.app.sftp_browser.remote_tree.item(item, "values")
            name = values[1]
            
            # Skip if it's a directory
            if values[2] == "":
                self.app.status_var.set("Cannot open directories")
                return

            # Create a temporary directory if it doesn't exist
            temp_dir = Path(os.path.expanduser("~")) / ".ssh-sftp-client" / "temp"
            temp_dir.mkdir(parents=True, exist_ok=True)

            # Create temporary file path
            temp_path = temp_dir / name
            remote_path = posixpath.join(self.app.remote_path, name)

            # Download the file to temp directory
            self.app.ssh_client.sftp_client.get(remote_path, str(temp_path))

            # Get file's last modification time
            remote_mtime = self.app.ssh_client.sftp_client.stat(remote_path).st_mtime

            # Open the file with default application
            os.startfile(temp_path) if os.name == 'nt' else os.system(f'xdg-open "{temp_path}"')

            # Start a monitoring thread to check for changes
            def monitor_changes():
                try:
                    last_mtime = os.path.getmtime(temp_path)
                    while True:
                        time.sleep(1)  # Check every second
                        current_mtime = os.path.getmtime(temp_path)
                        
                        if current_mtime != last_mtime:
                            # File has been modified, upload it back
                            self.app.ssh_client.sftp_client.put(str(temp_path), remote_path)
                            last_mtime = current_mtime
                            self.app.status_var.set(f"Saved changes to {name}")
                except Exception as e:
                    self.app.status_var.set(f"Error monitoring file: {str(e)}")

            import threading
            monitor_thread = threading.Thread(target=monitor_changes, daemon=True)
            monitor_thread.start()

            self.app.status_var.set(f"Opened {name} for editing")
        except Exception as e:
            self.app.status_var.set(f"Error opening file: {str(e)}")
            messagebox.showerror("Open Error", str(e))