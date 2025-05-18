import paramiko
import threading
import time
from tkinter import messagebox

class SSHClient:
    def __init__(self, app):
        self.app = app
        self.ssh_client = None
        self.channel = None
        self.sftp_client = None

    def connect(self):
        if self.app.connected:
            messagebox.showwarning("Warning", "Already connected!")
            self.app.status_var.set("Already connected")
            return

        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(
                hostname=self.app.hostname.get(),
                port=int(self.app.port.get()),
                username=self.app.username.get(),
                password=self.app.password.get(),
                timeout=10
            )

            self.channel = self.ssh_client.invoke_shell(term="xterm-256color", width=80, height=24)
            self.channel.settimeout(0.1)

            self.app.terminal_emulator.terminal.config(state="normal")
            self.app.terminal_emulator.terminal.delete(1.0, "end")
            self.app.terminal_emulator.screen.reset()

            self.app.connected = True
            threading.Thread(target=self.read_ssh, daemon=True).start()

            # Wait briefly to ensure MOTD is captured
            time.sleep(2)

            # Now perform additional operations
            self.detect_remote_filesystem()
            self.fetch_remote_users()
            
            # After successful SSH connection:
            try:
                self.sftp_client = self.ssh_client.open_sftp()
                self.app.sftp_browser.refresh_browsers()  # Make sure to refresh browsers after connection
            except Exception as e:
                messagebox.showwarning("SFTP Warning", f"SSH connected but SFTP failed: {str(e)}")

            self.app.terminal_emulator.on_resize(None)
            self.app.sftp_browser.refresh_browsers()

            messagebox.showinfo("Success", "Connected to SSH and SFTP server!")
            self.app.status_var.set("Connected to SSH and SFTP server")
        except Exception as e:
            messagebox.showerror("Error", f"Connection failed: {str(e)}")
            self.app.status_var.set(f"Connection failed: {str(e)}")
            self.disconnect()

    def disconnect(self):
        if self.app.connected:
            if self.channel:
                self.channel.close()
            if self.sftp_client:
                self.sftp_client.close()
            if self.ssh_client:
                self.ssh_client.close()
            self.app.connected = False
            self.app.terminal_emulator.terminal.config(state="disabled")
            self.app.remote_users.clear()
            self.app.sftp_browser.refresh_browsers()
            messagebox.showinfo("Info", "Disconnected from SSH and SFTP server.")
            self.app.status_var.set("Disconnected from SSH and SFTP server")

    def read_ssh(self):
        while self.app.connected:
            try:
                if self.channel.recv_ready():
                    data = self.channel.recv(1024).decode("utf-8", errors="ignore")
                    self.app.queue.put(data)
                    # Use after instead of after_idle for more consistent updates
                    self.app.root.after(1, self.app.terminal_emulator.update_terminal)
                time.sleep(0.005)  # Reduce from 0.01 to 0.005 for more responsive updates
            except Exception:
                self.app.queue.put("Connection lost.\n")
                self.app.root.after(0, self.app.terminal_emulator.update_terminal)
                self.disconnect()
                break

    def detect_remote_filesystem(self):
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command("uname")
            system = stdout.read().decode().strip().lower()
            self.app.remote_is_linux = "linux" in system
            self.app.status_var.set(f"Detected remote filesystem: {'Linux' if self.app.remote_is_linux else 'Unknown'}")
            if not self.app.remote_is_linux:
                self.app.status_var.set("Warning: Non-Linux remote filesystem detected; assuming Linux paths")
        except Exception as e:
            self.app.status_var.set(f"Failed to detect remote filesystem: {str(e)}")
            self.app.remote_is_linux = True

    def fetch_remote_users(self):
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command("getent passwd")
            for line in stdout:
                parts = line.strip().decode().split(":")
                if len(parts) >= 3:
                    self.app.remote_users[int(parts[2])] = parts[0]
        except Exception as e:
            self.app.status_var.set(f"Failed to fetch remote users: {str(e)}")

    def open_sftp(self):
        """Open and return an SFTP session"""
        if not self.ssh_client:
            raise Exception("Not connected to SSH server")
            
        if not self.sftp_client:
            try:
                self.sftp_client = self.ssh_client.open_sftp()
            except Exception as e:
                raise Exception(f"Failed to open SFTP session: {str(e)}")
                
        return self.sftp_client