import tkinter as tk
from tkinter import simpledialog, messagebox, Toplevel, Text, Button, Label, Frame, Scrollbar, ttk
import json
import os
import time

class MacrosMenu:
    def __init__(self, menubar, app):
        self.app = app
        self.batches = []  # Store batch commands
        self.config_dir = os.path.join(os.path.expanduser("~"), ".ssh_sftp_client")
        self.batch_file = os.path.join(self.config_dir, "batches.json")
        
        # Load saved batches
        self.load_batches()
        
        # Create Macros menu
        self.menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Macros", menu=self.menu)
        
        # Add menu items
        self.menu.add_command(label="Create Batch", command=self.create_batch)
        self.menu.add_separator()
        self.menu.add_command(label="Manage Batches", command=self.manage_batches)
        self.menu.add_separator()
        
        # This section would be dynamically populated with saved batch commands
        self.update_batch_list()
    
    def load_batches(self):
        """Load batches from the configuration file"""
        try:
            # Create config directory if it doesn't exist
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
                
            # Load batches if file exists
            if os.path.exists(self.batch_file):
                with open(self.batch_file, 'r') as f:
                    self.batches = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load batches: {str(e)}")
            self.batches = []
    
    def save_batches(self):
        """Save batches to the configuration file"""
        try:
            # Create config directory if it doesn't exist
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
                
            # Save batches to file
            with open(self.batch_file, 'w') as f:
                json.dump(self.batches, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save batches: {str(e)}")
    
    def update_batch_list(self):
        # Clear existing batches from menu
        last_index = self.menu.index(tk.END)
        if last_index > 3:  # Keep the first 4 items (Create, separator, Manage, separator)
            for i in range(4, last_index + 1):
                self.menu.delete(4)
        
        # Add saved batches to menu
        if not self.batches:
            self.menu.add_command(label="No batches created", state=tk.DISABLED)
        else:
            for batch in self.batches:
                self.menu.add_command(
                    label=batch['name'],
                    command=lambda b=batch: self.execute_batch(b)
                )
    
    def create_batch(self):
        # Create a new batch of commands
        batch_name = simpledialog.askstring("Create Batch", "Enter a name for the batch:")
        if batch_name:
            self.show_batch_editor(batch_name)
    
    def show_batch_editor(self, batch_name, commands=None, edit_mode=False, batch_index=None):
        # Create a dialog to add/edit commands in the batch
        editor = Toplevel(self.app.root)
        editor.title(f"{'Edit' if edit_mode else 'Create'} Batch: {batch_name}")
        editor.geometry("600x400")
        editor.transient(self.app.root)
        editor.grab_set()
        
        # Batch name frame
        name_frame = Frame(editor)
        name_frame.pack(fill=tk.X, padx=10, pady=5)
        Label(name_frame, text="Batch Name:").pack(side=tk.LEFT)
        name_var = tk.StringVar(value=batch_name)
        name_entry = ttk.Entry(name_frame, textvariable=name_var, width=40)
        name_entry.pack(side=tk.LEFT, padx=5)
        
        # Commands frame
        cmd_frame = Frame(editor)
        cmd_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        Label(cmd_frame, text="Batch Commands (one command per line):").pack(anchor=tk.W)
        
        # Text widget with scrollbar for commands
        text_frame = Frame(cmd_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        cmd_text = Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        cmd_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=cmd_text.yview)
        
        # Insert existing commands if in edit mode
        if commands:
            cmd_text.insert(tk.END, "\n".join(commands))
        
        # Buttons frame
        btn_frame = Frame(editor)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_batch():
            new_name = name_var.get().strip()
            if not new_name:
                messagebox.showerror("Error", "Batch name cannot be empty")
                return
                
            commands_text = cmd_text.get(1.0, tk.END).strip()
            if not commands_text:
                messagebox.showerror("Error", "Batch must contain at least one command")
                return
                
            command_list = [cmd.strip() for cmd in commands_text.split("\n") if cmd.strip()]
            
            batch = {
                'name': new_name,
                'commands': command_list
            }
            
            if edit_mode and batch_index is not None:
                self.batches[batch_index] = batch
                messagebox.showinfo("Batch", f"Batch '{new_name}' updated")
            else:
                self.batches.append(batch)
                messagebox.showinfo("Batch", f"Batch '{new_name}' created")
            
            self.update_batch_list()
            # Save batches to file after creating or updating
            self.save_batches()
            editor.destroy()
        
        Button(btn_frame, text="Cancel", command=editor.destroy).pack(side=tk.RIGHT, padx=5)
        Button(btn_frame, text="Save", command=save_batch).pack(side=tk.RIGHT)
    
    def manage_batches(self):
        if not self.batches:
            messagebox.showinfo("Manage Batches", "No batches created yet")
            return
            
        # Create batch management dialog
        manager = Toplevel(self.app.root)
        manager.title("Manage Batches")
        manager.geometry("500x300")
        manager.transient(self.app.root)
        manager.grab_set()
        
        # Create treeview to display batches
        frame = Frame(manager)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("name", "commands")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        tree.heading("name", text="Batch Name")
        tree.heading("commands", text="Number of Commands")
        tree.column("name", width=200)
        tree.column("commands", width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Populate treeview
        for i, batch in enumerate(self.batches):
            tree.insert("", tk.END, values=(batch['name'], len(batch['commands'])))
        
        # Button frame
        btn_frame = Frame(manager)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def edit_selected():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a batch to edit")
                return
                
            item = tree.item(selection[0])
            batch_name = item['values'][0]
            
            # Find the batch index
            batch_index = next((i for i, b in enumerate(self.batches) if b['name'] == batch_name), None)
            if batch_index is not None:
                batch = self.batches[batch_index]
                manager.destroy()
                self.show_batch_editor(batch['name'], batch['commands'], True, batch_index)
        
        def delete_selected():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a batch to delete")
                return
                
            item = tree.item(selection[0])
            batch_name = item['values'][0]
            
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete batch '{batch_name}'?"):
                # Find and remove the batch
                batch_index = next((i for i, b in enumerate(self.batches) if b['name'] == batch_name), None)
                if batch_index is not None:
                    del self.batches[batch_index]
                    self.update_batch_list()
                    # Save batches to file after deleting
                    self.save_batches()
                    messagebox.showinfo("Delete", f"Batch '{batch_name}' deleted")
                    manager.destroy()
                    # Reopen the manager if there are still batches
                    if self.batches:
                        self.manage_batches()
        
        Button(btn_frame, text="Close", command=manager.destroy).pack(side=tk.RIGHT, padx=5)
        Button(btn_frame, text="Delete", command=delete_selected).pack(side=tk.RIGHT, padx=5)
        Button(btn_frame, text="Edit", command=edit_selected).pack(side=tk.RIGHT)
    
    def execute_batch(self, batch):
        # Confirm execution
        if messagebox.askyesno("Execute Batch", 
                      f"Execute batch '{batch['name']}' on current SSH connection?\n\n"
                      f"This will run {len(batch['commands'])} commands."):
            
            # Get current tab index
            current_tab_id = self.app.tab_manager.notebook.select()
            if not current_tab_id:
                messagebox.showerror("Error", "No active tab")
                return
                
            # Find an active SSH connection
            active_client = None
            
            # Check all tabs for an active SSH connection
            for tab_id, tab_info in self.app.tab_manager.tabs.items():
                if "client" in tab_info and tab_info["client"]:
                    client = tab_info["client"]
                    # Check if this client has an active SSH connection
                    if hasattr(client, "connected") and client.connected:
                        active_client = client
                        break
            
            if not active_client:
                messagebox.showerror("Error", "No active SSH connection in current tab")
                return
                
            # Now we have a client with an active connection, send commands
            if hasattr(active_client, "ssh_client") and hasattr(active_client.ssh_client, "channel"):
                channel = active_client.ssh_client.channel
                if channel:
                    # Execute commands on the SSH channel
                    for cmd in batch['commands']:
                        # Send the command followed by a newline
                        channel.send(cmd + "\r\n")
                        # Small delay to ensure commands don't run too quickly
                        time.sleep(0.1)
                        
                    messagebox.showinfo("Batch Execution", 
                                  f"Executed {len(batch['commands'])} commands from batch '{batch['name']}'")
                else:
                    messagebox.showerror("Error", "SSH channel not available")
            else:
                messagebox.showerror("Error", "SSH client not properly initialized")
