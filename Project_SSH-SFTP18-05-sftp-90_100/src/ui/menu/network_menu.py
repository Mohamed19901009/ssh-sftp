import tkinter as tk
from tkinter import ttk, Toplevel, Canvas, Frame, Label, Button, Scrollbar
import threading
import time
import uuid

class NetworkMenu:
    def __init__(self, menubar, app):
        self.app = app
        
        # Check if menubar exists before adding cascade
        if menubar is None:
            print("Error: Menubar is None in NetworkMenu initialization")
            return
            
        # Create Network menu
        self.menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Network", menu=self.menu)
        
        # Add menu items
        self.menu.add_command(label="Topography", command=self.open_topography)
        self.menu.add_command(label="Monitor", command=self.open_monitor)
        self.menu.add_command(label="Alarms", command=self.open_alarms)
    
    def open_topography(self):
        """Open the topography tab"""
        # Check if menu was properly initialized
        if not hasattr(self, 'menu'):
            print("Error: Network menu was not properly initialized")
            return
            
        # Check if tab already exists
        for tab_id, tab_info in self.app.tab_manager.tabs.items():
            if tab_info.get("type") == "topography":
                try:
                    # Select existing tab using tab index instead of frame
                    tab_index = self.app.tab_manager.notebook.index(tab_info["frame"])
                    self.app.tab_manager.notebook.select(tab_index)
                    return
                except Exception as e:
                    # If tab selection fails, remove the invalid reference and create a new tab
                    print(f"Error selecting tab: {e}")
                    del self.app.tab_manager.tabs[tab_id]
                    break
        
        # Create a new tab frame
        topo_frame = ttk.Frame(self.app.tab_manager.notebook)
        
        # Create a unique ID for this tab
        tab_id = str(uuid.uuid4())
        
        # Add to notebook
        self.app.tab_manager.notebook.add(topo_frame, text="Network Topography")
        
        # Create topography canvas
        self.create_topography_view(topo_frame)
        
        # Store tab information
        self.app.tab_manager.tabs[tab_id] = {
            "frame": topo_frame,
            "name": "Network Topography",
            "type": "topography"
        }
        
        # Select the new tab
        try:
            tab_index = self.app.tab_manager.notebook.index(topo_frame)
            self.app.tab_manager.notebook.select(tab_index)
        except Exception as e:
            print(f"Error selecting new tab: {e}")
    
    def create_topography_view(self, parent):
        """Create the topography view with canvas for network diagram"""
        # Main frame
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Toolbar frame
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, side=tk.TOP, padx=5, pady=5)
        
        # Add toolbar buttons
        ttk.Button(toolbar, text="Add Device", command=lambda: self.add_device_to_topo()).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Add Connection", command=lambda: self.add_connection_to_topo()).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Delete", command=lambda: self.delete_from_topo()).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Clear All", command=lambda: self.clear_topo()).pack(side=tk.LEFT, padx=2)
        
        # Canvas for network diagram
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create canvas with scrollbars
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(fill=tk.X, side=tk.BOTTOM)
        
        v_scrollbar = ttk.Scrollbar(canvas_frame)
        v_scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        
        self.topo_canvas = Canvas(canvas_frame, bg="white", 
                                  xscrollcommand=h_scrollbar.set,
                                  yscrollcommand=v_scrollbar.set)
        self.topo_canvas.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        h_scrollbar.config(command=self.topo_canvas.xview)
        v_scrollbar.config(command=self.topo_canvas.yview)
        
        # Configure canvas for scrolling
        self.topo_canvas.config(scrollregion=(0, 0, 1000, 1000))
        
        # Bind events for canvas interaction
        self.topo_canvas.bind("<Button-1>", self.canvas_click)
        self.topo_canvas.bind("<B1-Motion>", self.canvas_drag)
        self.topo_canvas.bind("<ButtonRelease-1>", self.canvas_release)
        
        # Initialize variables for tracking objects
        self.topo_devices = {}
        self.topo_connections = {}
        self.selected_object = None
        self.connection_start = None
        self.drag_data = {"x": 0, "y": 0, "item": None}
    
    def add_device_to_topo(self):
        """Add a device to the topography"""
        # Get equipment list from equipment manager
        equipment_list = []
        if hasattr(self.app, "equipment_manager"):
            for item_id in self.app.equipment_manager.tree.get_children():
                item = self.app.equipment_manager.tree.item(item_id)
                equipment_list.append({
                    "id": item_id,
                    "name": item["values"][0],
                    "host": item["values"][1]
                })
        
        # Create device selection dialog
        dialog = Toplevel(self.app.root)
        dialog.title("Add Device to Topography")
        dialog.geometry("300x400")
        dialog.transient(self.app.root)
        dialog.grab_set()
        
        # Create listbox for equipment
        Label(dialog, text="Select equipment to add:").pack(pady=(10, 5))
        
        list_frame = Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=listbox.yview)
        
        # Populate listbox
        for equip in equipment_list:
            listbox.insert(tk.END, f"{equip['name']} ({equip['host']})")
        
        # Add buttons
        btn_frame = Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def on_add():
            selection = listbox.curselection()
            if selection:
                idx = selection[0]
                equip = equipment_list[idx]
                
                # Add to canvas at a random position
                import random
                x = random.randint(50, 800)
                y = random.randint(50, 800)
                
                # Create device on canvas
                device_id = self.topo_canvas.create_oval(x-20, y-20, x+20, y+20, fill="lightblue", tags=("device", equip["id"]))
                text_id = self.topo_canvas.create_text(x, y+30, text=equip["name"], tags=("label", equip["id"]))
                
                # Store device info
                self.topo_devices[equip["id"]] = {
                    "id": equip["id"],
                    "name": equip["name"],
                    "host": equip["host"],
                    "canvas_ids": [device_id, text_id],
                    "position": (x, y)
                }
                
                dialog.destroy()
        
        Button(btn_frame, text="Add", command=on_add).pack(side=tk.RIGHT, padx=5)
        Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def add_connection_to_topo(self):
        """Enter connection mode to connect two devices"""
        self.connection_mode = True
        self.connection_start = None
        
        # Show instructions
        self.app.status_var.set("Click on first device, then second device to create connection")
    
    def delete_from_topo(self):
        """Delete selected object from topography"""
        if self.selected_object:
            tags = self.topo_canvas.gettags(self.selected_object)
            
            if "device" in tags:
                # Get device ID
                device_id = tags[1]
                
                # Remove from canvas
                for canvas_id in self.topo_devices[device_id]["canvas_ids"]:
                    self.topo_canvas.delete(canvas_id)
                
                # Remove connections to this device
                connections_to_remove = []
                for conn_id, conn in self.topo_connections.items():
                    if device_id in [conn["from_id"], conn["to_id"]]:
                        # Remove from canvas
                        self.topo_canvas.delete(conn["line_id"])
                        connections_to_remove.append(conn_id)
                
                # Remove connections from dictionary
                for conn_id in connections_to_remove:
                    del self.topo_connections[conn_id]
                
                # Remove device from dictionary
                del self.topo_devices[device_id]
            
            elif "connection" in tags:
                # Get connection ID
                conn_id = tags[1]
                
                # Remove from canvas
                self.topo_canvas.delete(self.selected_object)
                
                # Remove from dictionary
                del self.topo_connections[conn_id]
            
            self.selected_object = None
    
    def clear_topo(self):
        """Clear all objects from topography"""
        self.topo_canvas.delete("all")
        self.topo_devices = {}
        self.topo_connections = {}
        self.selected_object = None
    
    def canvas_click(self, event):
        """Handle canvas click event"""
        # Get canvas coordinates
        x = self.topo_canvas.canvasx(event.x)
        y = self.topo_canvas.canvasy(event.y)
        
        # Find closest item
        item = self.topo_canvas.find_closest(x, y)
        if item:
            tags = self.topo_canvas.gettags(item[0])
            
            # Handle connection mode
            if hasattr(self, "connection_mode") and self.connection_mode:
                if "device" in tags:
                    device_id = tags[1]
                    
                    if not self.connection_start:
                        # First device selected
                        self.connection_start = device_id
                        self.app.status_var.set(f"Selected {self.topo_devices[device_id]['name']} as start. Click on destination device.")
                    else:
                        # Second device selected
                        if device_id != self.connection_start:
                            # Create connection
                            from_pos = self.topo_devices[self.connection_start]["position"]
                            to_pos = self.topo_devices[device_id]["position"]
                            
                            # Create line
                            conn_id = str(uuid.uuid4())
                            line_id = self.topo_canvas.create_line(
                                from_pos[0], from_pos[1], to_pos[0], to_pos[1],
                                width=2, fill="black", tags=("connection", conn_id)
                            )
                            
                            # Store connection
                            self.topo_connections[conn_id] = {
                                "id": conn_id,
                                "from_id": self.connection_start,
                                "to_id": device_id,
                                "line_id": line_id
                            }
                            
                            # Exit connection mode
                            self.connection_mode = False
                            self.connection_start = None
                            self.app.status_var.set("Connection created")
                        else:
                            self.app.status_var.set("Cannot connect device to itself")
            else:
                # Normal selection mode
                self.selected_object = item[0]
                
                # Save drag start position
                self.drag_data["item"] = item[0]
                self.drag_data["x"] = x
                self.drag_data["y"] = y
    
    def canvas_drag(self, event):
        """Handle canvas drag event"""
        if self.drag_data["item"]:
            # Get canvas coordinates
            x = self.topo_canvas.canvasx(event.x)
            y = self.topo_canvas.canvasy(event.y)
            
            # Calculate movement
            dx = x - self.drag_data["x"]
            dy = y - self.drag_data["y"]
            
            # Move item
            tags = self.topo_canvas.gettags(self.drag_data["item"])
            
            if "device" in tags:
                device_id = tags[1]
                
                # Move all canvas objects for this device
                for canvas_id in self.topo_devices[device_id]["canvas_ids"]:
                    self.topo_canvas.move(canvas_id, dx, dy)
                
                # Update position
                pos = self.topo_devices[device_id]["position"]
                self.topo_devices[device_id]["position"] = (pos[0] + dx, pos[1] + dy)
                
                # Update connections
                for conn in self.topo_connections.values():
                    if conn["from_id"] == device_id or conn["to_id"] == device_id:
                        # Get positions
                        from_pos = self.topo_devices[conn["from_id"]]["position"]
                        to_pos = self.topo_devices[conn["to_id"]]["position"]
                        
                        # Update line
                        self.topo_canvas.coords(conn["line_id"], from_pos[0], from_pos[1], to_pos[0], to_pos[1])
            
            # Update drag position
            self.drag_data["x"] = x
            self.drag_data["y"] = y
    
    def canvas_release(self, event):
        """Handle canvas release event"""
        self.drag_data["item"] = None
    
    def open_monitor(self):
        """Open the monitoring tab"""
        # Check if tab already exists
        for tab_id, tab_info in self.app.tab_manager.tabs.items():
            if tab_info.get("type") == "monitor":
                try:
                    # Select existing tab using tab index instead of frame
                    tab_index = self.app.tab_manager.notebook.index(tab_info["frame"])
                    self.app.tab_manager.notebook.select(tab_index)
                    return
                except Exception as e:
                    # If tab selection fails, remove the invalid reference and create a new tab
                    print(f"Error selecting tab: {e}")
                    del self.app.tab_manager.tabs[tab_id]
                    break
        
        # Create a new tab frame
        monitor_frame = ttk.Frame(self.app.tab_manager.notebook)
        
        # Create a unique ID for this tab
        tab_id = str(uuid.uuid4())
        
        # Add to notebook
        self.app.tab_manager.notebook.add(monitor_frame, text="System Monitor")
        
        # Create monitoring view
        self.create_monitor_view(monitor_frame)
        
        # Store tab information
        self.app.tab_manager.tabs[tab_id] = {
            "frame": monitor_frame,
            "name": "System Monitor",
            "type": "monitor",
            "monitor_thread": None,
            "monitoring": False
        }
        
        # Select the new tab using tab index
        tab_index = self.app.tab_manager.notebook.index(monitor_frame)
        self.app.tab_manager.notebook.select(tab_index)
    
    def create_monitor_view(self, parent):
        """Create the monitoring view with stats for connected equipment"""
        # Main frame
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, side=tk.TOP, padx=5, pady=5)
        
        # Add control buttons
        self.start_monitor_btn = ttk.Button(control_frame, text="Start Monitoring", 
                                           command=lambda: self.toggle_monitoring(parent))
        self.start_monitor_btn.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(control_frame, text="Refresh interval (sec):").pack(side=tk.LEFT, padx=(10, 2))
        self.refresh_var = tk.StringVar(value="5")
        refresh_entry = ttk.Entry(control_frame, textvariable=self.refresh_var, width=5)
        refresh_entry.pack(side=tk.LEFT)
        
        # Create treeview for equipment stats
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("name", "host", "cpu", "memory", "disk", "uptime")
        self.monitor_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        # Configure columns
        self.monitor_tree.heading("name", text="Name")
        self.monitor_tree.heading("host", text="Hostname")
        self.monitor_tree.heading("cpu", text="CPU Usage")
        self.monitor_tree.heading("memory", text="Memory Usage")
        self.monitor_tree.heading("disk", text="Disk Usage")
        self.monitor_tree.heading("uptime", text="Uptime")
        
        self.monitor_tree.column("name", width=100)
        self.monitor_tree.column("host", width=150)
        self.monitor_tree.column("cpu", width=80)
        self.monitor_tree.column("memory", width=100)
        self.monitor_tree.column("disk", width=100)
        self.monitor_tree.column("uptime", width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.monitor_tree.yview)
        self.monitor_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.monitor_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)
        
        self.monitor_status_var = tk.StringVar(value="Monitoring inactive")
        ttk.Label(status_frame, textvariable=self.monitor_status_var).pack(side=tk.LEFT)
    
    def toggle_monitoring(self, parent_frame):
        """Start or stop monitoring"""
        # Find tab info
        tab_info = None
        for tab_id, info in self.app.tab_manager.tabs.items():
            if info.get("frame") == parent_frame:
                tab_info = info
                break
        
        if not tab_info:
            return
        
        if tab_info.get("monitoring", False):
            # Stop monitoring
            tab_info["monitoring"] = False
            self.start_monitor_btn.config(text="Start Monitoring")
            self.monitor_status_var.set("Monitoring stopped")
        else:
            # Start monitoring
            tab_info["monitoring"] = True
            self.start_monitor_btn.config(text="Stop Monitoring")
            self.monitor_status_var.set("Monitoring active")
            
            # Start monitoring thread if not already running
            if not tab_info.get("monitor_thread") or not tab_info["monitor_thread"].is_alive():
                tab_info["monitor_thread"] = threading.Thread(target=self.monitor_equipment, args=(tab_info,))
                tab_info["monitor_thread"].daemon = True
                tab_info["monitor_thread"].start()
    
    def monitor_equipment(self, tab_info):
        """Background thread to monitor equipment"""
        while tab_info.get("monitoring", False):
            # Clear existing items
            for item in self.monitor_tree.get_children():
                self.monitor_tree.delete(item)
            
            # Get equipment list from equipment manager
            if hasattr(self.app, "equipment_manager"):
                for item_id in self.app.equipment_manager.tree.get_children():
                    item = self.app.equipment_manager.tree.item(item_id)
                    name = item["values"][0]
                    host = item["values"][1]
                    
                    # Simulate getting stats (in a real app, this would query the actual equipment)
                    import random
                    cpu = f"{random.randint(0, 100)}%"
                    memory = f"{random.randint(0, 100)}%"
                    disk = f"{random.randint(0, 100)}%"
                    uptime = f"{random.randint(1, 365)} days"
                    
                    # Add to treeview
                    self.monitor_tree.insert("", tk.END, values=(name, host, cpu, memory, disk, uptime))
            
            # Update status
            self.monitor_status_var.set(f"Last updated: {time.strftime('%H:%M:%S')}")
            
            # Wait for next refresh
            try:
                refresh_interval = int(self.refresh_var.get())
            except ValueError:
                refresh_interval = 5
            
            # Ensure reasonable interval
            if refresh_interval < 1:
                refresh_interval = 1
            
            # Sleep for the interval
            for _ in range(refresh_interval * 10):  # Check every 0.1 seconds if monitoring is still active
                if not tab_info.get("monitoring", False):
                    break
                time.sleep(0.1)
    
    def open_alarms(self):
        """Open the alarms tab"""
        # Check if tab already exists
        for tab_id, tab_info in self.app.tab_manager.tabs.items():
            if tab_info.get("type") == "alarms":
                try:
                    # Select existing tab using tab index instead of frame
                    tab_index = self.app.tab_manager.notebook.index(tab_info["frame"])
                    self.app.tab_manager.notebook.select(tab_index)
                    return
                except Exception as e:
                    # If tab selection fails, remove the invalid reference and create a new tab
                    print(f"Error selecting tab: {e}")
                    del self.app.tab_manager.tabs[tab_id]
                    break
        
        # Create a new tab frame
        alarms_frame = ttk.Frame(self.app.tab_manager.notebook)
        
        # Create a unique ID for this tab
        tab_id = str(uuid.uuid4())
        
        # Add to notebook
        self.app.tab_manager.notebook.add(alarms_frame, text="Network Alarms")
        
        # Create alarms view
        self.create_alarms_view(alarms_frame)
        
        # Store tab information
        self.app.tab_manager.tabs[tab_id] = {
            "frame": alarms_frame,
            "name": "Network Alarms",
            "type": "alarms"
        }
        
        # Select the new tab using tab index
        tab_index = self.app.tab_manager.notebook.index(alarms_frame)
        self.app.tab_manager.notebook.select(tab_index)
    
    def create_alarms_view(self, parent):
        """Create the alarms view (placeholder for future implementation)"""
        # Main frame
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Placeholder message
        placeholder = ttk.Label(main_frame, 
                               text="Alarms functionality will be implemented in a future update.",
                               font=("Helvetica", 12))
        placeholder.pack(expand=True, pady=50)