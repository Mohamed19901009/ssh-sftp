import tkinter as tk
from tkinter import ttk

class TreeManager:
    def __init__(self, browser):
        self.browser = browser
        self.sort_reverse = False
        self.last_sort_column = None

    def create_remote_tree(self, parent):
        style = ttk.Style()
        # Create a unique style for SFTP browser with consistent row height
        style.configure("SFTPTree.Treeview", 
            rowheight=32,  # Increased for better icon display
            font=("Segoe UI", 9)  # Consistent font
        )
        
        tree = ttk.Treeview(
            parent,
            columns=("Icon", "Name", "Size", "Owner", "Permissions", "Modified"),
            show="headings",  # Show headings
            selectmode="extended",
            style="SFTPTree.Treeview"  # Use the specific style
        )
        self._setup_tree_columns(tree)
        
        # Hide the Icon column header
        tree.heading("Icon", text=" ")  # Using a space instead of empty string for better compatibility
        
        # Configure tag colors for different file types
        for file_type, color in self.browser.file_types.type_colors.items():
            tree.tag_configure(color, foreground=color)
        
        return tree

    def _setup_tree_columns(self, tree):
        # Set Icon header to space (hidden)
        tree.heading("Icon", text=" ")
        tree.heading("Name", text="Name", command=lambda: self._sort_tree(tree, "Name", str.lower))
        tree.heading("Size", text="Size", command=lambda: self._sort_tree(tree, "Size", self._size_to_bytes))
        tree.heading("Owner", text="Owner", command=lambda: self._sort_tree(tree, "Owner", str.lower))
        tree.heading("Permissions", text="Permissions", command=lambda: self._sort_tree(tree, "Permissions", str))
        tree.heading("Modified", text="Modified Date", command=lambda: self._sort_tree(tree, "Modified", str))
        
        # Fixed width for icon column and consistent padding
        tree.column("Icon", width=32, minwidth=32, stretch=False, anchor="center")
        tree.column("Name", width=490, minwidth=240, anchor="w")
        tree.column("Size", width=50, minwidth=50, anchor="e")
        tree.column("Owner", width=50, minwidth=50, anchor="w")
        tree.column("Permissions", width=50, minwidth=50, anchor="w")
        tree.column("Modified", width=50, minwidth=50, anchor="w")

    def _size_to_bytes(self, size_str):
        if size_str == "":
            return -1  # Directories come first
        try:
            # Parse size string (e.g., "1.5 MB", "800 KB", "2 GB")
            number = float(size_str.split()[0])
            unit = size_str.split()[1].upper()
            multipliers = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
            return number * multipliers.get(unit, 0)
        except (ValueError, IndexError):
            return 0

    def _sort_tree(self, tree, column, convert):
        if self.last_sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
        self.last_sort_column = column

        items = [(convert(tree.set(item, column)), item) for item in tree.get_children('')]
        items.sort(reverse=self.sort_reverse)
        
        for index, (_, item) in enumerate(items):
            tree.move(item, '', index)

        # Update the heading to show sort direction
        for col in tree["columns"]:
            if col == "Icon":
                continue  # Skip the Icon column to keep it hidden
            if col != column:
                tree.heading(col, text=col.replace("▲", "").replace("▼", ""))
        current_text = tree.heading(column)["text"].replace("▲", "").replace("▼", "")
        tree.heading(column, text=f"{current_text} {'▼' if self.sort_reverse else '▲'}")
        
        # Ensure Icon header stays hidden
        tree.heading("Icon", text=" ")

    def _format_size(self, size):
        if size == "":
            return ""
        try:
            size = int(size)
            if size < 1024:
                return f"{size} B"
            elif size < 1024 ** 2:
                return f"{size/1024:.1f} KB"
            elif size < 1024 ** 3:
                return f"{size/(1024**2):.1f} MB"
            else:
                return f"{size/(1024**3):.1f} GB"
        except (ValueError, TypeError):
            return str(size)

    def _sort_and_insert_items(self, tree, items):
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)

        # Convert size strings to numbers for proper sorting
        def get_sort_key(item):
            name = item[1]
            size = item[2]
            # For directories (empty size)
            if size == "":
                return (0, name.lower())  # Directories first, then sort by name
            try:
                # For files, convert size to number
                return (1, int(size), name.lower())  # Files after directories, sort by size then name
            except (ValueError, TypeError):
                return (1, 0, name.lower())  # If size conversion fails, treat as size 0

        # Sort items
        sorted_items = sorted(items, key=get_sort_key)

        # Insert items with formatted size
        for item in sorted_items:
            icon, name, size, owner, permissions, mtime, color = item
            formatted_size = self._format_size(size)
            tree.insert("", tk.END, values=(icon, name, formatted_size, owner, permissions, mtime), tags=(color,))