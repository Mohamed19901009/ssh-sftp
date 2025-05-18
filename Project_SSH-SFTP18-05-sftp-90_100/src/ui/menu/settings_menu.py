import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import json
import os
from pathlib import Path

class SettingsMenu:
    def __init__(self, menubar, app):
        self.app = app
        
        # Create Settings menu
        self.menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=self.menu)
        
        # Add terminal settings as the main menu item
        self.menu.add_command(label="Terminal Settings", command=self.terminal_settings)
        
        # Add connection preferences
        self.menu.add_command(label="Connection Preferences", command=self.connection_preferences)
        self.menu.add_command(label="UI Customization", command=self.ui_customization)
        self.menu.add_separator()
        self.menu.add_command(label="Import Settings...", command=self.import_settings)
        self.menu.add_command(label="Export Settings...", command=self.export_settings)
        self.menu.add_separator()
        self.menu.add_command(label="Reset to Defaults", command=self.reset_defaults)
        
        # Default settings
        self.default_settings = {
            "terminal": {
                "font_family": "Consolas",
                "font_size": 10,
                "foreground_color": "#FFFFFF",
                "background_color": "#000000",
                "cursor_color": "#FFFFFF",
                "cursor_blink": True,
                "scrollback_lines": 1000,
                "bell_sound": True,
                "mode": "default"  # Add default mode
            },
            "connection": {
                "timeout": 30,
                "keepalive": 60,
                "default_port": 22,
                "compression": True,
                "verify_host_keys": True,
                "auto_reconnect": True,
                "reconnect_attempts": 3
            },
            "ui": {
                "theme": "default",
                "tab_position": "top",
                "show_toolbar": True,
                "show_statusbar": True,
                "confirm_close": True,
                "save_window_size": True,
                "save_layout": True
            }
        }
        
        # Load settings
        self.settings_file = Path.home() / ".ssh-sftp-client" / "settings.json"
        self.settings = self.load_settings()
    
    def load_settings(self):
        """Load settings from file or use defaults"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                merged_settings = self.default_settings.copy()
                
                # Update terminal settings
                if "terminal" in settings:
                    merged_settings["terminal"].update(settings["terminal"])
                
                # Update connection settings
                if "connection" in settings:
                    merged_settings["connection"].update(settings["connection"])
                
                # Update UI settings
                if "ui" in settings:
                    merged_settings["ui"].update(settings["ui"])
                
                return merged_settings
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load settings: {str(e)}")
                return self.default_settings.copy()
        else:
            return self.default_settings.copy()
    
    def save_settings(self):
        """Save settings to file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
            return False
    
    def apply_settings(self):
        """Apply settings to the application"""
        # Apply terminal settings
        if hasattr(self.app, 'terminal_emulator'):
            term_settings = self.settings["terminal"]
            self.app.terminal_emulator.configure(
                font=(term_settings["font_family"], term_settings["font_size"]),
                fg=term_settings["foreground_color"],
                bg=term_settings["background_color"],
                insertbackground=term_settings["cursor_color"]
            )
        
        # Apply UI settings
        ui_settings = self.settings["ui"]
        
        # Apply theme
        if ui_settings["theme"] != "default":
            style = ttk.Style()
            style.theme_use(ui_settings["theme"])
        
        # Apply tab position
        if hasattr(self.app, 'tab_manager'):
            self.app.tab_manager.notebook.configure(tabposition=ui_settings["tab_position"])
        
        # Apply toolbar and statusbar visibility
        if hasattr(self.app, 'toolbar') and hasattr(self.app.toolbar, 'frame'):
            if ui_settings["show_toolbar"]:
                self.app.toolbar.frame.pack(fill=tk.X, before=self.app.main_frame)
            else:
                self.app.toolbar.frame.pack_forget()
        
        if hasattr(self.app, 'statusbar') and hasattr(self.app.statusbar, 'frame'):
            if ui_settings["show_statusbar"]:
                self.app.statusbar.frame.pack(fill=tk.X, side=tk.BOTTOM)
            else:
                self.app.statusbar.frame.pack_forget()
    
    def terminal_settings(self):
        """Open terminal settings dialog with integrated terminal modes"""
        settings_window = tk.Toplevel(self.app.root)
        settings_window.title("Terminal Settings")
        settings_window.geometry("600x550")
        settings_window.resizable(False, False)
        settings_window.transient(self.app.root)
        settings_window.grab_set()
        
        # Create a notebook for different settings categories
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Appearance tab
        appearance_frame = ttk.Frame(notebook)
        notebook.add(appearance_frame, text="Appearance")
        
        # Terminal modes section
        modes_frame = ttk.LabelFrame(appearance_frame, text="Terminal Modes")
        modes_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Mode selection
        mode_var = tk.StringVar(value=self.settings["terminal"].get("mode", "default"))
        
        ttk.Radiobutton(modes_frame, text="Default (Black BG, Colored Text)", 
                       variable=mode_var, value="default").pack(anchor=tk.W, padx=10, pady=5)
        ttk.Radiobutton(modes_frame, text="Dark (Black BG, White Text)", 
                       variable=mode_var, value="dark").pack(anchor=tk.W, padx=10, pady=5)
        ttk.Radiobutton(modes_frame, text="Light (White BG, Black Text)", 
                       variable=mode_var, value="light").pack(anchor=tk.W, padx=10, pady=5)
        ttk.Radiobutton(modes_frame, text="Retro (White BG, Colored Text)", 
                       variable=mode_var, value="retro").pack(anchor=tk.W, padx=10, pady=5)
        
        # Apply mode button
        ttk.Button(modes_frame, text="Apply Mode", 
                  command=lambda: self.apply_terminal_mode(mode_var.get())).pack(anchor=tk.E, padx=10, pady=5)
        
        # Create a frame for the preview
        preview_frame = ttk.LabelFrame(appearance_frame, text="Preview")
        preview_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Define font variables
        font_family_var = tk.StringVar(value=self.settings["terminal"].get("font_family", "Courier New"))
        font_size_var = tk.StringVar(value=str(self.settings["terminal"].get("font_size", 10)))
        
        # Create a preview terminal
        preview_terminal = tk.Text(preview_frame, height=5, width=40, 
                                  bg="black", fg="white", 
                                  insertbackground="white",
                                  font=(font_family_var.get(), int(font_size_var.get())))
        preview_terminal.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        preview_terminal.insert(tk.END, "$ ls -la\ndrwxr-xr-x  2 user group  4096 Jan 1 12:34 .\n" +
                               "drwxr-xr-x 10 user group  4096 Jan 1 12:34 ..\n" +
                               "-rw-r--r--  1 user group  1234 Jan 1 12:34 file.txt\n")
        preview_terminal.config(state=tk.DISABLED)
        
        # Font settings
        font_frame = ttk.LabelFrame(appearance_frame, text="Font")
        font_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Font family
        ttk.Label(font_frame, text="Font Family:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        font_family_combo = ttk.Combobox(font_frame, textvariable=font_family_var)
        font_family_combo['values'] = ('Courier New', 'Consolas', 'Lucida Console', 'Monospace')
        font_family_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Font size
        ttk.Label(font_frame, text="Font Size:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        font_size_combo = ttk.Combobox(font_frame, textvariable=font_size_var, width=5)
        font_size_combo['values'] = ('8', '9', '10', '11', '12', '14', '16', '18', '20')
        font_size_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Color settings
        color_frame = ttk.LabelFrame(appearance_frame, text="Colors")
        color_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Text color
        ttk.Label(color_frame, text="Text Color:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        text_color_var = tk.StringVar(value=self.settings["terminal"].get("foreground_color", "#FFFFFF"))
        text_color_button = ttk.Button(color_frame, text="Choose...", 
                                     command=lambda: self.choose_color(text_color_var, preview_terminal, "fg"))
        text_color_button.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Background color
        ttk.Label(color_frame, text="Background Color:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        bg_color_var = tk.StringVar(value=self.settings["terminal"].get("background_color", "#000000"))
        bg_color_button = ttk.Button(color_frame, text="Choose...", 
                                   command=lambda: self.choose_color(bg_color_var, preview_terminal, "bg"))
        bg_color_button.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Cursor color
        ttk.Label(color_frame, text="Cursor Color:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        cursor_color_var = tk.StringVar(value=self.settings["terminal"].get("cursor_color", "#FFFFFF"))
        cursor_color_button = ttk.Button(color_frame, text="Choose...", 
                                       command=lambda: self.choose_color(cursor_color_var, preview_terminal, "insertbackground"))
        cursor_color_button.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Behavior tab
        behavior_frame = ttk.Frame(notebook)
        notebook.add(behavior_frame, text="Behavior")
        
        # Cursor settings
        cursor_frame = ttk.LabelFrame(behavior_frame, text="Cursor")
        cursor_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Cursor blink
        cursor_blink_var = tk.BooleanVar(value=self.settings["terminal"].get("cursor_blink", True))
        ttk.Checkbutton(cursor_frame, text="Blinking cursor", variable=cursor_blink_var).pack(anchor=tk.W, padx=5, pady=5)
        
        # Scrollback settings
        scrollback_frame = ttk.LabelFrame(behavior_frame, text="Scrollback")
        scrollback_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Scrollback lines
        scrollback_lines_frame = ttk.Frame(scrollback_frame)
        scrollback_lines_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(scrollback_lines_frame, text="Scrollback lines:").pack(side=tk.LEFT)
        scrollback_lines_var = tk.StringVar(value=str(self.settings["terminal"].get("scrollback_lines", 1000)))
        ttk.Spinbox(scrollback_lines_frame, from_=100, to=10000, textvariable=scrollback_lines_var, width=7).pack(side=tk.LEFT, padx=5)
        
        # Bell settings
        bell_frame = ttk.LabelFrame(behavior_frame, text="Bell")
        bell_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Bell sound
        bell_sound_var = tk.BooleanVar(value=self.settings["terminal"].get("bell_sound", True))
        ttk.Checkbutton(bell_frame, text="Enable bell sound", variable=bell_sound_var).pack(anchor=tk.W, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="OK", command=lambda: self.save_terminal_settings(
            font_family_var.get(), font_size_var.get(), 
            text_color_var.get(), bg_color_var.get(), cursor_color_var.get(),
            cursor_blink_var.get(), scrollback_lines_var.get(), bell_sound_var.get(),
            mode_var.get(), settings_window
        )).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(button_frame, text="Cancel", command=settings_window.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Apply", command=lambda: self.save_terminal_settings(
            font_family_var.get(), font_size_var.get(), 
            text_color_var.get(), bg_color_var.get(), cursor_color_var.get(),
            cursor_blink_var.get(), scrollback_lines_var.get(), bell_sound_var.get(),
            mode_var.get()
        )).pack(side=tk.RIGHT, padx=5)
    
    def choose_color(self, color_var, preview_widget, property_name):
        """Open color chooser dialog and update preview"""
        color = colorchooser.askcolor(color_var.get())[1]
        if color:
            color_var.set(color)
            preview_widget.config(**{property_name: color})
    
    def save_terminal_settings(self, font_family, font_size, text_color, bg_color, cursor_color, 
                              cursor_blink, scrollback_lines, bell_sound, mode, window=None):
        """Save terminal settings"""
        # Update settings
        self.settings["terminal"]["font_family"] = font_family
        self.settings["terminal"]["font_size"] = int(font_size)
        self.settings["terminal"]["foreground_color"] = text_color
        self.settings["terminal"]["background_color"] = bg_color
        self.settings["terminal"]["cursor_color"] = cursor_color
        self.settings["terminal"]["cursor_blink"] = cursor_blink
        self.settings["terminal"]["scrollback_lines"] = int(scrollback_lines)
        self.settings["terminal"]["bell_sound"] = bell_sound
        self.settings["terminal"]["mode"] = mode
        
        # Save to file
        self.save_settings()
        
        # Apply settings
        self.apply_settings()
        
        # Apply terminal mode if needed
        self.apply_terminal_mode(mode)
        
        self.app.status_var.set("Terminal settings saved")
        
        # Close the window if provided
        if window:
            window.destroy()
    
    def apply_terminal_mode(self, mode_name):
        """Apply one of the predefined terminal modes to all terminal tabs"""
        try:
            # Define color schemes for different modes with correct definitions
            modes = {
                "default": {
                    "foreground_color": "#00FF00",  # Green text
                    "background_color": "#000000",  # Black background
                    "cursor_color": "#00FF00"       # Green cursor
                },
                "dark": {
                    "foreground_color": "#FFFFFF",  # White text
                    "background_color": "#000000",  # Black background
                    "cursor_color": "#FFFFFF"       # White cursor
                },
                "light": {
                    "foreground_color": "#000000",  # Black text
                    "background_color": "#FFFFFF",  # White background
                    "cursor_color": "#000000"       # Black cursor
                },
                "retro": {
                    "foreground_color": "#FFCC00",  # Amber/Orange text
                    "background_color": "#FFFFFF",  # White background
                    "cursor_color": "#FFCC00"       # Amber/Orange cursor
                }
            }
            
            # Get the color scheme for the selected mode
            mode_colors = modes.get(mode_name, modes["default"])
            
            # Update the settings with the mode colors
            self.settings["terminal"]["foreground_color"] = mode_colors["foreground_color"]
            self.settings["terminal"]["background_color"] = mode_colors["background_color"]
            self.settings["terminal"]["cursor_color"] = mode_colors["cursor_color"]
            self.settings["terminal"]["mode"] = mode_name
            
            # Save the settings
            self.save_settings()
            
            # Update the preview if we're in the terminal settings dialog
            for widget in self.app.root.winfo_children():
                if isinstance(widget, tk.Toplevel) and widget.winfo_exists():
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Notebook):
                            for tab in child.winfo_children():
                                for frame in tab.winfo_children():
                                    if isinstance(frame, ttk.LabelFrame) and frame.winfo_children():
                                        for w in frame.winfo_children():
                                            if isinstance(w, tk.Text):
                                                # This is likely our preview terminal
                                                w.config(
                                                    fg=mode_colors["foreground_color"],
                                                    bg=mode_colors["background_color"],
                                                    insertbackground=mode_colors["cursor_color"]
                                                )
                                                    
                                                # Apply to ALL tabs, not just the current one
                                                tabs_updated = 0
                                                    
                                                # Get all tabs from the tab manager
                                                for tab_id, tab_info in self.app.tab_manager.tabs.items():
                                                    client = tab_info.get("client")
                                                    if client:
                                                        # Check if client has a terminal_emulator attribute
                                                        if hasattr(client, "terminal_emulator") and client.terminal_emulator:
                                                            # Update the terminal widget configuration
                                                            if hasattr(client.terminal_emulator, "terminal") and client.terminal_emulator.terminal:
                                                                # Update the terminal widget base colors
                                                                client.terminal_emulator.terminal.config(
                                                                    bg=mode_colors["background_color"],
                                                                    fg=mode_colors["foreground_color"],
                                                                    insertbackground=mode_colors["cursor_color"]
                                                                )
                                                                    
                                                                # Update the ANSI color definitions for "default" colors
                                                                # This is crucial for the terminal to display properly
                                                                for tag in client.terminal_emulator.terminal.tag_names():
                                                                    if "_bg_" in tag:
                                                                        tag_parts = tag.split("_bg_")
                                                                        bg_color = tag_parts[1].split("_")[0]
                                                                        if bg_color == "default":
                                                                            # Update all tags with default background
                                                                            client.terminal_emulator.terminal.tag_configure(
                                                                                tag, background=mode_colors["background_color"]
                                                                            )
                                                                    
                                                                    if tag.startswith("fg_default"):
                                                                        # Update all tags with default foreground
                                                                        client.terminal_emulator.terminal.tag_configure(
                                                                            tag, foreground=mode_colors["foreground_color"]
                                                                        )
                                                                    
                                                                # Force a complete redraw of the terminal
                                                                if hasattr(client.terminal_emulator, "redraw_terminal"):
                                                                    # Clear the terminal first
                                                                    client.terminal_emulator.terminal.delete(1.0, tk.END)
                                                                    # Then redraw it
                                                                    client.terminal_emulator.redraw_terminal()
                                                                    
                                                                tabs_updated += 1
                                                        
                                                        if tabs_updated > 0:
                                                            self.app.status_var.set(f"{mode_name.capitalize()} terminal mode applied to {tabs_updated} tab(s)")
                                                        else:
                                                            self.app.status_var.set(f"{mode_name.capitalize()} terminal mode saved, but no active terminals found")
                                                                
        except Exception as e:
            self.app.status_var.set(f"Error applying terminal mode: {str(e)}")

    def connection_preferences(self):
        """Open connection preferences dialog"""
        prefs_window = tk.Toplevel(self.app.root)
        prefs_window.title("Connection Preferences")
        prefs_window.geometry("500x400")
        prefs_window.resizable(False, False)
        prefs_window.transient(self.app.root)
        prefs_window.grab_set()
        
        # Create a notebook for different preference categories
        notebook = ttk.Notebook(prefs_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # SSH tab
        ssh_frame = ttk.Frame(notebook)
        notebook.add(ssh_frame, text="SSH")
        
        # SSH keepalive settings
        keepalive_frame = ttk.LabelFrame(ssh_frame, text="Keepalive")
        keepalive_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Enable keepalive
        keepalive_var = tk.BooleanVar(value=self.settings["connection"].get("keepalive_enabled", True))
        ttk.Checkbutton(keepalive_frame, text="Enable keepalive", variable=keepalive_var).pack(anchor=tk.W, padx=5, pady=5)
        
        # Keepalive interval
        interval_frame = ttk.Frame(keepalive_frame)
        interval_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(interval_frame, text="Interval (seconds):").pack(side=tk.LEFT)
        interval_var = tk.StringVar(value=str(self.settings["connection"].get("keepalive", 60)))
        ttk.Spinbox(interval_frame, from_=10, to=300, textvariable=interval_var, width=5).pack(side=tk.LEFT, padx=5)
        
        # SSH timeout settings
        timeout_frame = ttk.LabelFrame(ssh_frame, text="Connection Timeout")
        timeout_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Connection timeout
        conn_timeout_frame = ttk.Frame(timeout_frame)
        conn_timeout_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(conn_timeout_frame, text="Connection timeout (seconds):").pack(side=tk.LEFT)
        conn_timeout_var = tk.StringVar(value=str(self.settings["connection"].get("timeout", 30)))
        ttk.Spinbox(conn_timeout_frame, from_=5, to=120, textvariable=conn_timeout_var, width=5).pack(side=tk.LEFT, padx=5)
        
        # SFTP tab
        sftp_frame = ttk.Frame(notebook)
        notebook.add(sftp_frame, text="SFTP")
        
        # SFTP transfer settings
        transfer_frame = ttk.LabelFrame(sftp_frame, text="File Transfer")
        transfer_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Buffer size
        buffer_frame = ttk.Frame(transfer_frame)
        buffer_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(buffer_frame, text="Buffer size (KB):").pack(side=tk.LEFT)
        buffer_var = tk.StringVar(value=str(self.settings["connection"].get("buffer_size", 32)))
        ttk.Spinbox(buffer_frame, from_=8, to=1024, textvariable=buffer_var, width=5).pack(side=tk.LEFT, padx=5)
        
        # Confirm overwrite
        overwrite_var = tk.BooleanVar(value=self.settings["connection"].get("confirm_overwrite", True))
        ttk.Checkbutton(transfer_frame, text="Confirm before overwriting files", variable=overwrite_var).pack(anchor=tk.W, padx=5, pady=5)
        
        # Preserve file attributes
        preserve_var = tk.BooleanVar(value=self.settings["connection"].get("preserve_attributes", True))
        ttk.Checkbutton(transfer_frame, text="Preserve file attributes (permissions, times)", variable=preserve_var).pack(anchor=tk.W, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(prefs_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="OK", command=lambda: self.save_connection_preferences(
            keepalive_var.get(), interval_var.get(), conn_timeout_var.get(),
            buffer_var.get(), overwrite_var.get(), preserve_var.get(), prefs_window
        )).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(button_frame, text="Cancel", command=prefs_window.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Apply", command=lambda: self.save_connection_preferences(
            keepalive_var.get(), interval_var.get(), conn_timeout_var.get(),
            buffer_var.get(), overwrite_var.get(), preserve_var.get()
        )).pack(side=tk.RIGHT, padx=5)

    def save_connection_preferences(self, keepalive_enabled, interval, conn_timeout, buffer_size, confirm_overwrite, preserve_attrs, window=None):
        """Save connection preferences"""
        # Update settings
        self.settings["connection"]["keepalive_enabled"] = keepalive_enabled
        self.settings["connection"]["keepalive"] = int(interval)
        self.settings["connection"]["timeout"] = int(conn_timeout)
        self.settings["connection"]["buffer_size"] = int(buffer_size)
        self.settings["connection"]["confirm_overwrite"] = confirm_overwrite
        self.settings["connection"]["preserve_attributes"] = preserve_attrs
        
        # Save to file
        self.save_settings()
        
        self.app.status_var.set("Connection preferences saved")
        
        # Close the window if provided
        if window:
            window.destroy()
            
    # Add missing methods that are referenced in the menu
    def ui_customization(self):
        """Open UI customization dialog"""
        settings_window = tk.Toplevel(self.app.root)
        settings_window.title("UI Customization")
        settings_window.geometry("500x600")
        settings_window.transient(self.app.root)
        settings_window.grab_set()
        
        # Create notebook for settings tabs
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Theme tab
        theme_frame = ttk.Frame(notebook)
        notebook.add(theme_frame, text="Theme")
        
        # Theme selection
        theme_label_frame = ttk.LabelFrame(theme_frame, text="Application Theme")
        theme_label_frame.pack(fill=tk.X, padx=10, pady=10)
        
        theme_var = tk.StringVar(value=self.settings["ui"].get("theme", "cosmo"))  # Change default to cosmo
        themes = ["cosmo", "clam", "alt", "classic"]  # Add cosmo to the list
        
        for theme in themes:
            ttk.Radiobutton(theme_label_frame, text=theme.capitalize(), 
                           variable=theme_var, value=theme).pack(anchor=tk.W, padx=10, pady=5)
        
        # Layout tab
        layout_frame = ttk.Frame(notebook)
        notebook.add(layout_frame, text="Layout")
        
        # Tab position
        tab_frame = ttk.LabelFrame(layout_frame, text="Tab Position")
        tab_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tab_pos_var = tk.StringVar(value=self.settings["ui"].get("tab_position", "top"))
        positions = ["top", "bottom", "left", "right"]
        
        for pos in positions:
            ttk.Radiobutton(tab_frame, text=pos.capitalize(), 
                           variable=tab_pos_var, value=pos).pack(anchor=tk.W, padx=10, pady=5)
        
        # Visibility options
        visibility_frame = ttk.LabelFrame(layout_frame, text="Show/Hide Elements")
        visibility_frame.pack(fill=tk.X, padx=10, pady=10)
        
        toolbar_var = tk.BooleanVar(value=self.settings["ui"].get("show_toolbar", True))
        statusbar_var = tk.BooleanVar(value=self.settings["ui"].get("show_statusbar", True))
        
        ttk.Checkbutton(visibility_frame, text="Show Toolbar", 
                        variable=toolbar_var).pack(anchor=tk.W, padx=10, pady=5)
        ttk.Checkbutton(visibility_frame, text="Show Statusbar", 
                        variable=statusbar_var).pack(anchor=tk.W, padx=10, pady=5)
        
        # Behavior tab
        behavior_frame = ttk.Frame(notebook)
        notebook.add(behavior_frame, text="Behavior")
        
        # Window behavior
        window_frame = ttk.LabelFrame(behavior_frame, text="Window Behavior")
        window_frame.pack(fill=tk.X, padx=10, pady=10)
        
        save_size_var = tk.BooleanVar(value=self.settings["ui"].get("save_window_size", True))
        save_layout_var = tk.BooleanVar(value=self.settings["ui"].get("save_layout", True))
        confirm_close_var = tk.BooleanVar(value=self.settings["ui"].get("confirm_close", True))
        
        ttk.Checkbutton(window_frame, text="Remember Window Size", 
                        variable=save_size_var).pack(anchor=tk.W, padx=10, pady=5)
        ttk.Checkbutton(window_frame, text="Remember Layout", 
                        variable=save_layout_var).pack(anchor=tk.W, padx=10, pady=5)
        ttk.Checkbutton(window_frame, text="Confirm Before Closing", 
                        variable=confirm_close_var).pack(anchor=tk.W, padx=10, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def apply_settings():
            # Update settings
            self.settings["ui"].update({
                "theme": theme_var.get(),
                "tab_position": tab_pos_var.get(),
                "show_toolbar": toolbar_var.get(),
                "show_statusbar": statusbar_var.get(),
                "save_window_size": save_size_var.get(),
                "save_layout": save_layout_var.get(),
                "confirm_close": confirm_close_var.get()
            })
            
            # Apply settings
            style = ttk.Style()
            style.theme_use(theme_var.get())
            
            # Use the new tab position method
            if hasattr(self.app, 'tab_manager'):
                self.app.tab_manager.set_tab_position(tab_pos_var.get())
            
            # Update toolbar visibility
            if hasattr(self.app, 'toolbar'):
                if toolbar_var.get():
                    self.app.toolbar.frame.pack(fill=tk.X, before=self.app.main_frame)
                else:
                    self.app.toolbar.frame.pack_forget()
            
            # Update statusbar visibility
            if hasattr(self.app, 'statusbar'):
                if statusbar_var.get():
                    self.app.statusbar.frame.pack(fill=tk.X, side=tk.BOTTOM)
                else:
                    self.app.statusbar.frame.pack_forget()
            
            # Save settings to file
            self.save_settings()
            settings_window.destroy()
            messagebox.showinfo("Success", "UI settings have been updated")
        
        ttk.Button(button_frame, text="Apply", command=apply_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=settings_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def import_settings(self):
        """Import settings from a file"""
        messagebox.showinfo("Import Settings", "Settings import will be implemented in a future version.")
        
    def export_settings(self):
        """Export settings to a file"""
        messagebox.showinfo("Export Settings", "Settings export will be implemented in a future version.")
        
    def reset_defaults(self):
        """Reset settings to defaults"""
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to defaults?"):
            self.settings = self.default_settings.copy()
            self.save_settings()
            self.apply_settings()
            self.app.status_var.set("Settings reset to defaults")