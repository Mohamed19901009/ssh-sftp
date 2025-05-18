import tkinter as tk
from tkinter import ttk
import uuid
from src.app import SSHClientApp

class TabManager:
    def __init__(self, container, app):
        self.container = container
        self.app = app
        
        # Create a style object
        style = ttk.Style()
        
        # Configure the tab style with padding
        style.configure('TNotebook.Tab', padding=[10, 5], width=15)

        self.notebook = ttk.Notebook(container, style='TNotebook')
        
        # Set tab position using pack configuration
        self.set_tab_position('top')
        
        # Create tabs dictionary to track open connections
        self.tabs = {}
        self.tab_counter = 0
        
        # Tab context menu
        self.tab_menu = tk.Menu(self.notebook, tearoff=0)
        self.connect_index = 0
        self.disconnect_index = 1
        self.tab_menu.add_command(label="Connect", command=self.connect_tab)
        self.tab_menu.add_command(label="Disconnect", command=self.disconnect_tab)
        self.tab_menu.add_separator()
        self.tab_menu.add_command(label="Close", command=self.close_current_tab)
        self.tab_menu.add_command(label="Close All", command=self.close_all_tabs)
        
        # Bind right-click to show context menu
        self.notebook.bind("<Button-3>", self.show_tab_context_menu)
        
        # Create welcome tab
        self.create_welcome_tab()

    def create_welcome_tab(self):
        welcome_frame = ttk.Frame(self.notebook)
        self.notebook.add(welcome_frame, text="Welcome")
        
        welcome_text = tk.Text(welcome_frame, wrap=tk.WORD, padx=10, pady=10)
        welcome_text.pack(fill=tk.BOTH, expand=True)
        
        welcome_message = """
        Welcome to Enhanced SSH-SFTP Client!
        
        To get started:
        
        1. Add equipment connections using the panel on the left
        2. Double-click on a connection or select it and click "Connect"
        3. Each connection will open in a new tab
        
        You can manage your connections and perform various operations using the menu bar above.
        """
        
        welcome_text.insert(tk.END, welcome_message)
        welcome_text.config(state=tk.DISABLED)

    def open_connection_tab(self, profile):
        connection_frame = ttk.Frame(self.notebook)
        tab_id = str(uuid.uuid4())
        
        max_tab_text_length = 10
        tab_text = profile["name"]
        if len(tab_text) > max_tab_text_length:
            tab_text = tab_text[:max_tab_text_length-3] + "..."

        self.notebook.add(connection_frame, text=tab_text)
        
        ssh_client_app = SSHClientApp(connection_frame, self.app, profile)
        
        self.tabs[tab_id] = {
            "frame": connection_frame,
            "client": ssh_client_app,
            "name": profile["name"],
            "profile": profile
        }
        
        self.notebook.select(connection_frame)
        return ssh_client_app

    def show_tab_context_menu(self, event):
        try:
            # Get the tab under cursor
            tab_index = self.notebook.index(f"@{event.x},{event.y}")
            
            # Check if a valid tab was clicked
            if tab_index is None or tab_index < 0:
                return
                
            # Don't show menu for welcome tab
            if tab_index == 0:
                return
                
            self.notebook.select(tab_index)

            # Always disable Connect and Disconnect for now
            self.tab_menu.entryconfigure(self.connect_index, state=tk.DISABLED)
            self.tab_menu.entryconfigure(self.disconnect_index, state=tk.DISABLED)

            current_tab = self.notebook.select()
            for tab_id, tab_info in self.tabs.items():
                if tab_info["frame"] == current_tab:
                    client = tab_info.get("client")
                    if client and hasattr(client, "connected"):
                        if client.connected:
                            self.tab_menu.entryconfigure(self.connect_index, state=tk.DISABLED)
                            self.tab_menu.entryconfigure(self.disconnect_index, state=tk.NORMAL)
                        else:
                            self.tab_menu.entryconfigure(self.connect_index, state=tk.NORMAL)
                            self.tab_menu.entryconfigure(self.disconnect_index, state=tk.DISABLED)
                        break
                        
            # Show the menu
            self.tab_menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            # Log the error but don't crash
            self.app.status_var.set(f"Menu error: {str(e)}")
        finally:
            self.tab_menu.grab_release()

    def connect_tab(self):
        current_tab = self.notebook.select()
        if not current_tab:
            return
        for tab_id, tab_info in self.tabs.items():
            if tab_info["frame"] == current_tab:
                client = tab_info.get("client")
                if not client or not hasattr(client, "ssh_client"):
                    print("No SSH client found for this tab.")
                    return
                try:
                    if hasattr(client.ssh_client, "connect") and callable(client.ssh_client.connect):
                        client.ssh_client.connect()
                    else:
                        print("SSH client does not have a connect method.")
                except Exception as e:
                    print(f"Error connecting tab: {e}")
                break
                
    def disconnect_tab(self):
        current_tab = self.notebook.select()
        if not current_tab:
            return
        for tab_id, tab_info in self.tabs.items():
            if tab_info["frame"] == current_tab:
                client = tab_info.get("client")
                if not client or not hasattr(client, "ssh_client"):
                    print("No SSH client found for this tab.")
                    return
                try:
                    if hasattr(client.ssh_client, "disconnect") and callable(client.ssh_client.disconnect):
                        client.ssh_client.disconnect()
                    else:
                        print("SSH client does not have a disconnect method.")
                except Exception as e:
                    print(f"Error disconnecting tab: {e}")
                break
                
    def close_current_tab(self):
        current_tab = self.notebook.select()
        if not current_tab:
            return
            
        if self.notebook.index(current_tab) == 0 and self.notebook.tab(0, "text") == "Welcome":
            return
            
        tab_id_to_remove = None
        for tab_id, tab_info in list(self.tabs.items()):
            if tab_info["frame"] == current_tab:
                tab_id_to_remove = tab_id
                client = tab_info.get("client")
                if client and hasattr(client, "connected") and client.connected:
                    try:
                        if hasattr(client, "disconnect"):
                            client.disconnect()
                        elif hasattr(client, "ssh_client") and hasattr(client.ssh_client, "disconnect"):
                            client.ssh_client.disconnect()
                    except Exception as e:
                        print(f"Error disconnecting before closing tab: {e}")
                # In close_current_tab method:
                if tab_id_to_remove:
                    # Ensure all resources are cleaned up
                    tab_info = self.tabs.get(tab_id_to_remove)
                    if tab_info:
                        client = tab_info.get('client')
                        if client:
                            try:
                                if hasattr(client, 'disconnect'):
                                    client.disconnect()
                                elif hasattr(client, 'ssh_client') and hasattr(client.ssh_client, 'disconnect'):
                                    client.ssh_client.disconnect()
                            except Exception as e:
                                print(f"Error cleaning up client resources: {e}")
                    # Remove from dictionary
                    self.tabs.pop(tab_id_to_remove, None)
                
                # In close_all_tabs method:
                if tab_id:
                    tab_info = self.tabs.get(tab_id)
                    if tab_info:
                        client = tab_info.get('client')
                        if client and hasattr(client, 'connected') and client.connected:
                            try:
                                if hasattr(client, 'disconnect'):
                                    client.disconnect()
                                elif hasattr(client, 'ssh_client') and hasattr(client.ssh_client, 'disconnect'):
                                    client.ssh_client.disconnect()
                            except Exception as e:
                                print(f"Error disconnecting client: {e}")
                    # Remove from dictionary
                    self.tabs.pop(tab_id, None)
            
        try:
            self.notebook.forget(current_tab)
        except Exception as e:
            print(f"Error closing tab: {e}")

    def close_all_tabs(self):
        tabs_to_close = [tab for tab in self.notebook.tabs()][1:]  # Skip the welcome tab (index 0)
        for tab in reversed(tabs_to_close):
            tab_id = None
            for tid, tab_info in list(self.tabs.items()):
                if tab_info["frame"] == tab:
                    tab_id = tid
                    break
            if tab_id:
                tab_info = self.tabs.get(tab_id)
                if tab_info:
                    client = tab_info.get("client")
                    if client and hasattr(client, "connected") and client.connected:
                        try:
                            if hasattr(client, "disconnect"):
                                client.disconnect()
                            elif hasattr(client, "ssh_client") and hasattr(client.ssh_client, "disconnect"):
                                client.ssh_client.disconnect()
                        except Exception as e:
                            print(f"Error disconnecting client: {e}")
                self.tabs.pop(tab_id, None)
            try:
                self.notebook.forget(tab)
            except Exception as e:
                print(f"Error closing tab: {e}")

    def set_tab_position(self, position):
        """Set tab position using pack configuration"""
        self.notebook.pack_forget()
        if position == 'bottom':
            self.notebook.pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM)
        elif position == 'left':
            self.notebook.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        elif position == 'right':
            self.notebook.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT)
        else:  # default to top
            self.notebook.pack(fill=tk.BOTH, expand=True, side=tk.TOP)