import tkinter as tk
from tkinter import ttk, messagebox
import uuid
import os
from PIL import Image, ImageTk

class EquipmentManager:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.selected_item = None
        self.drag_data = {"item": None, "x": 0, "y": 0}
        self.connected_items = set()  # Track connected equipment
        
        # Create UI elements
        self.setup_ui()
        
        # Load icons
        self.load_icons()
        
        # Create context menus
        self.create_context_menus()
        
        # Load saved equipment
        self.load_equipment()

    def setup_ui(self):
        # Equipment panel frame
        self.frame = ttk.LabelFrame(self.parent, text="Equipment Manager")
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Equipment list with scrollbar
        list_frame = ttk.Frame(self.frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create custom styles
        style = ttk.Style()
        style.configure('Header.Treeview.Heading',
            font=('Segoe UI', 10, 'bold'),
            foreground='#2c3e50')
        
        # Create treeview with single column but hide headers
        self.tree = ttk.Treeview(list_frame, columns=("name"), show="tree", selectmode="browse", style='Header.Treeview')
        self.tree.column("#0", width=40)  # Icon column
        self.tree.column("name", width=250, anchor=tk.W)
        
        # Add scrollbar that only appears when needed
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self._on_scroll)
        self.scrollbar = scrollbar  # Store reference to scrollbar
        
        # Pack tree and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure tree styles
        self.tree.tag_configure('folder',
            font=('Segoe UI', 9, 'bold'),
            foreground='#34495e')
        
        self.tree.tag_configure('equipment',
            font=('Segoe UI', 9),
            foreground='#2980b9')

        self.tree.tag_configure('connected',
            font=('Segoe UI', 9, 'bold'),
            foreground='#27ae60')  # Green color for connected equipment

        self.tree.tag_configure('disconnected',
            font=('Segoe UI', 9),
            foreground='#2980b9')  # Default blue color
            
        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self.on_equipment_select)
        self.tree.bind('<Double-1>', self.on_equipment_double_click)
        self.tree.bind('<Button-3>', self.show_context_menu)

    def _on_scroll(self, *args):
        # Show scrollbar only when content exceeds visible area
        if float(args[0]) == 0.0 and float(args[1]) == 1.0:
            self.scrollbar.pack_forget()
        else:
            self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrollbar.set(*args)

    def connect_to_selected(self):
        if not self.selected_item:
            messagebox.showinfo("Info", "Please select an equipment first")
            return
            
        # Check if it's a folder
        item_type = self.get_item_type(self.selected_item)
        if item_type == "folder":
            return
            
        # Find the profile for the selected equipment
        for profile in self.app.equipment_profiles:
            if profile["id"] == self.selected_item and profile.get("type") != "folder":
                # Add to connected set before connecting
                self.connected_items.add(self.selected_item)
                
                # Update only equipment items, preserve folder tags
                if item_type == "equipment":
                    self.tree.item(self.selected_item, tags=("equipment", "connected"))
                
                self.app.connect_to_equipment(profile)
                return
                
        self.app.logger.error(f"Profile not found for ID: {self.selected_item}")

    def load_equipment(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # First pass: Add all folders
        folders = [p for p in self.app.equipment_profiles if p.get("type") == "folder"]
        for folder in folders:
            parent_id = folder.get("parent", "")
            if parent_id and parent_id not in self.tree.get_children():
                parent_id = ""
                
            self.tree.insert(
                parent_id,
                tk.END,
                iid=folder["id"],
                text=self.folder_icon,
                values=(folder["name"]),
                tags=("folder",)
            )
            
        # Second pass: Add all equipment
        equipment = [p for p in self.app.equipment_profiles if p.get("type") != "folder"]
        for profile in equipment:
            parent_id = profile.get("parent", "")
            if parent_id and parent_id not in self.tree.get_children():
                parent_id = ""
                
            # Check if equipment is connected
            tags = ("equipment", "connected" if profile["id"] in self.connected_items else "disconnected")
            
            self.tree.insert(
                parent_id,
                tk.END,
                iid=profile["id"],
                text=self.equipment_icon,
                values=(profile["name"]),
                tags=tags
            )
            
        # Open all folders
        for item in self.tree.get_children():
            self.tree.item(item, open=True)

    def on_equipment_select(self, event):
        selected_items = self.tree.selection()
        if selected_items:
            self.selected_item = selected_items[0]
        else:
            self.selected_item = None

    def on_equipment_double_click(self, event):
        if self.selected_item:
            # Check if it's equipment (not a folder)
            if self.get_item_type(self.selected_item) != "folder":
                self.connect_to_selected()

    def add_equipment(self):
        # Get parent folder if any is selected
        parent = ""
        if self.selected_item and self.get_item_type(self.selected_item) == "folder":
            parent = self.selected_item
        
        # Create dialog window
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Add Equipment")
        dialog.geometry("400x300")
        dialog.transient(self.app.root)
        dialog.grab_set()
        
        # Equipment properties
        ttk.Label(dialog, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(dialog, text="Hostname:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        hostname_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=hostname_var).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(dialog, text="Port:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        port_var = tk.StringVar(value="22")
        ttk.Entry(dialog, textvariable=port_var).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(dialog, text="Username:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        username_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=username_var).grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(dialog, text="Password:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        password_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=password_var, show="*").grid(row=4, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        def save_equipment():
            # Validate inputs
            name = name_var.get().strip()
            hostname = hostname_var.get().strip()
            port = port_var.get().strip()
            username = username_var.get().strip()
            password = password_var.get()
            
            if not name or not hostname or not port or not username:
                messagebox.showerror("Error", "Please fill all required fields")
                return
                
            try:
                port_num = int(port)
                if port_num <= 0 or port_num > 65535:
                    raise ValueError("Invalid port number")
            except ValueError:
                messagebox.showerror("Error", "Port must be a valid number (1-65535)")
                return
                
            # Create new profile
            new_profile = {
                "id": str(uuid.uuid4()),
                "name": name,
                "hostname": hostname,
                "port": port,
                "username": username,
                "password": password,
                "parent": parent
            }
            
            # Add to profiles and save
            self.app.equipment_profiles.append(new_profile)
            self.app.save_equipment_profiles()
            
            # Refresh equipment list
            self.load_equipment()
            
            # Close dialog
            dialog.destroy()
        
        ttk.Button(btn_frame, text="Save", command=save_equipment).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Configure grid
        dialog.columnconfigure(1, weight=1)
        
        # Center dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def add_folder(self):
        # Get parent folder if any is selected
        parent = ""
        if self.selected_item and self.get_item_type(self.selected_item) == "folder":
            parent = self.selected_item
        
        # Create dialog window
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Add Folder")
        dialog.geometry("300x120")
        dialog.transient(self.app.root)
        dialog.grab_set()
        
        # Folder properties
        ttk.Label(dialog, text="Folder Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        def save_folder():
            # Validate inputs
            name = name_var.get().strip()
            
            if not name:
                messagebox.showerror("Error", "Please enter a folder name")
                return
                
            # Create new folder profile
            new_folder = {
                "id": str(uuid.uuid4()),
                "name": name,
                "type": "folder",
                "parent": parent
            }
            
            # Add to profiles and save
            self.app.equipment_profiles.append(new_folder)
            self.app.save_equipment_profiles()
            
            # Refresh equipment list
            self.load_equipment()
            
            # Close dialog
            dialog.destroy()
        
        ttk.Button(btn_frame, text="Save", command=save_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Configure grid
        dialog.columnconfigure(1, weight=1)
        
        # Center dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def rename_folder(self):
        if not self.selected_item:
            return
            
        # Find the folder profile
        selected_folder = None
        for profile in self.app.equipment_profiles:
            if profile["id"] == self.selected_item and profile.get("type") == "folder":
                selected_folder = profile
                break
                
        if not selected_folder:
            return
            
        # Create dialog window
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Rename Folder")
        dialog.geometry("300x120")
        dialog.transient(self.app.root)
        dialog.grab_set()
        
        # Folder properties
        ttk.Label(dialog, text="New Folder Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        name_var = tk.StringVar(value=selected_folder["name"])
        ttk.Entry(dialog, textvariable=name_var).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        def update_folder():
            # Validate inputs
            name = name_var.get().strip()
            
            if not name:
                messagebox.showerror("Error", "Please enter a folder name")
                return
                
            # Update folder name
            selected_folder["name"] = name
            
            # Save profiles
            self.app.save_equipment_profiles()
            
            # Refresh equipment list
            self.load_equipment()
            
            # Close dialog
            dialog.destroy()
        
        ttk.Button(btn_frame, text="Update", command=update_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Configure grid
        dialog.columnconfigure(1, weight=1)
        
        # Center dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def delete_folder(self):
        if not self.selected_item:
            return
            
        # Check if it's a folder
        is_folder = False
        for profile in self.app.equipment_profiles:
            if profile["id"] == self.selected_item and profile.get("type") == "folder":
                is_folder = True
                break
                
        if not is_folder:
            return
            
        # Check if folder has children
        has_children = len(self.tree.get_children(self.selected_item)) > 0
        
        # Confirm deletion
        if has_children:
            if not messagebox.askyesno("Confirm", "This folder contains items. Delete everything?"):
                return
        else:
            if not messagebox.askyesno("Confirm", "Are you sure you want to delete this folder?"):
                return
            
        # Delete folder and all its contents
        self.delete_item_recursive(self.selected_item)
        
        # Save profiles
        self.app.save_equipment_profiles()
        
        # Refresh equipment list
        self.load_equipment()

    def delete_item_recursive(self, item_id):
        """Delete an item and all its children recursively"""
        # Delete all children first
        for child in self.tree.get_children(item_id):
            self.delete_item_recursive(child)
            
        # Delete the item from profiles
        for i, profile in enumerate(self.app.equipment_profiles):
            if profile["id"] == item_id:
                del self.app.equipment_profiles[i]
                break

    def edit_equipment(self):
        if not self.selected_item:
            messagebox.showinfo("Info", "Please select an equipment to edit")
            return
            
        # Check if it's a folder
        if self.get_item_type(self.selected_item) == "folder":
            return
            
        # Find the profile for the selected equipment
        selected_profile = None
        for profile in self.app.equipment_profiles:
            if profile["id"] == self.selected_item and profile.get("type") != "folder":
                selected_profile = profile
                break
                
        if not selected_profile:
            self.app.logger.error(f"Profile not found for ID: {self.selected_item}")
            return
            
        # Create dialog window
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Edit Equipment")
        dialog.geometry("400x300")
        dialog.transient(self.app.root)
        dialog.grab_set()
        
        # Equipment properties
        ttk.Label(dialog, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        name_var = tk.StringVar(value=selected_profile["name"])
        ttk.Entry(dialog, textvariable=name_var).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(dialog, text="Hostname:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        hostname_var = tk.StringVar(value=selected_profile["hostname"])
        ttk.Entry(dialog, textvariable=hostname_var).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(dialog, text="Port:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        port_var = tk.StringVar(value=selected_profile["port"])
        ttk.Entry(dialog, textvariable=port_var).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(dialog, text="Username:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        username_var = tk.StringVar(value=selected_profile["username"])
        ttk.Entry(dialog, textvariable=username_var).grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(dialog, text="Password:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        password_var = tk.StringVar(value=selected_profile["password"])
        ttk.Entry(dialog, textvariable=password_var, show="*").grid(row=4, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        def update_equipment():
            # Validate inputs
            name = name_var.get().strip()
            hostname = hostname_var.get().strip()
            port = port_var.get().strip()
            username = username_var.get().strip()
            password = password_var.get()
            
            if not name or not hostname or not port or not username:
                messagebox.showerror("Error", "Please fill all required fields")
                return
                
            try:
                port_num = int(port)
                if port_num <= 0 or port_num > 65535:
                    raise ValueError("Invalid port number")
            except ValueError:
                messagebox.showerror("Error", "Port must be a valid number (1-65535)")
                return
                
            # Update profile
            selected_profile["name"] = name
            selected_profile["hostname"] = hostname
            selected_profile["port"] = port
            selected_profile["username"] = username
            selected_profile["password"] = password
            
            # Save profiles
            self.app.save_equipment_profiles()
            
            # Refresh equipment list
            self.load_equipment()
            
            # Close dialog
            dialog.destroy()
        
        ttk.Button(btn_frame, text="Update", command=update_equipment).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Configure grid
        dialog.columnconfigure(1, weight=1)
        
        # Center dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def delete_equipment(self):
        if not self.selected_item:
            messagebox.showinfo("Info", "Please select an equipment to delete")
            return
            
        # Check if it's a folder
        if self.get_item_type(self.selected_item) == "folder":
            return
            
        # Confirm deletion
        if not messagebox.askyesno("Confirm", "Are you sure you want to delete this equipment?"):
            return
            
        # Find and remove the profile
        for i, profile in enumerate(self.app.equipment_profiles):
            if profile["id"] == self.selected_item and profile.get("type") != "folder":
                del self.app.equipment_profiles[i]
                break
                
        # Save profiles
        self.app.save_equipment_profiles()
        
        # Refresh equipment list
        self.load_equipment()

    # Drag and drop functionality
    def on_drag_start(self, event):
        """Start drag operation"""
        item = self.tree.identify_row(event.y)
        if item:
            self.drag_data["item"] = item
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

    def on_drag_motion(self, event):
        """Handle drag motion"""
        # This could be used to show visual feedback during drag
        pass

    def on_drag_release(self, event):
        """End drag operation and handle drop"""
        if not self.drag_data["item"]:
            return
            
        # Get the target item (where we're dropping)
        target = self.tree.identify_row(event.y)
        
        # Don't drop on self
        if target == self.drag_data["item"]:
            self.drag_data["item"] = None
            return
            
        # Get the dragged item
        dragged_item = self.drag_data["item"]
        
        # Find the profiles
        dragged_profile = None
        for profile in self.app.equipment_profiles:
            if profile["id"] == dragged_item:
                dragged_profile = profile
                break
                
        if not dragged_profile:
            self.drag_data["item"] = None
            return
            
        # If target is empty, move to root
        if not target:
            # Update parent to empty string (root)
            dragged_profile["parent"] = ""
        else:
            # Check if target is a folder
            is_folder = False
            for profile in self.app.equipment_profiles:
                if profile["id"] == target and profile.get("type") == "folder":
                    is_folder = True
                    break
                    
            if is_folder:
                # Move into folder
                dragged_profile["parent"] = target
            else:
                # Get the parent of the target
                target_parent = self.tree.parent(target)
                dragged_profile["parent"] = target_parent
                
        # Save profiles
        self.app.save_equipment_profiles()
        
        # Refresh equipment list
        self.load_equipment()
        
        # Reset drag data
        self.drag_data["item"] = None

    def show_context_menu(self, event):
        """Show the appropriate context menu based on what was clicked"""
        # Get the item under cursor
        item = self.tree.identify_row(event.y)
        
        if item:
            # Select the item
            self.tree.selection_set(item)
            self.selected_item = item
            
            # Check if it's a folder or equipment
            item_type = self.get_item_type(item)
            
            if item_type == "folder":
                self.folder_menu.tk_popup(event.x_root, event.y_root)
            else:
                self.equipment_menu.tk_popup(event.x_root, event.y_root)
        else:
            # Clicked on empty area
            self.background_menu.tk_popup(event.x_root, event.y_root)

    def create_context_menus(self):
        """Create context menus for equipment, folders and background"""
        # Equipment context menu (right-click on equipment)
        self.equipment_menu = tk.Menu(self.app.root, tearoff=0)
        self.equipment_menu.add_command(label="Connect", command=self.connect_to_selected)
        self.equipment_menu.add_separator()
        self.equipment_menu.add_command(label="Edit", command=self.edit_equipment)
        self.equipment_menu.add_command(label="Delete", command=self.delete_equipment)
        
        # Folder context menu (right-click on folder)
        self.folder_menu = tk.Menu(self.app.root, tearoff=0)
        self.folder_menu.add_command(label="Add Equipment", command=self.add_equipment)
        self.folder_menu.add_command(label="Add Folder", command=self.add_folder)
        self.folder_menu.add_separator()
        self.folder_menu.add_command(label="Rename", command=self.rename_folder)
        self.folder_menu.add_command(label="Delete", command=self.delete_folder)
        
        # Background context menu (right-click on empty area)
        self.background_menu = tk.Menu(self.app.root, tearoff=0)
        self.background_menu.add_command(label="Add Equipment", command=self.add_equipment)
        self.background_menu.add_command(label="Add Folder", command=self.add_folder)

    def get_item_type(self, item_id):
        """Determine if an item is a folder or equipment"""
        # Check if the item has children
        if self.tree.get_children(item_id):
            return "folder"
            
        # Check if it's in our equipment profiles
        for profile in self.app.equipment_profiles:
            if profile.get("id") == item_id:
                return "equipment"
                
        # Must be a folder without children
        return "folder"

    def load_icons(self):
        # Use Unicode symbols for icons
        self.folder_icon = "📁"  # Folder icon
        self.equipment_icon = "🖥️"  # Computer icon
        self.connected_icon = "🟢"  # Connected status
        self.disconnected_icon = "⚪"  # Disconnected status