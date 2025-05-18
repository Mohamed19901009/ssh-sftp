import tkinter as tk
from tkinter import ttk, colorchooser
import json
import os
from pathlib import Path

class TerminalSettings:
    def __init__(self, app):
        self.app = app
        
        # Font and color mode settings
        self.available_fonts = ["Courier", "Consolas", "Monaco", "DejaVu Sans Mono"]
        self.font_sizes = [10, 12, 14, 16]
        self.current_font = tk.StringVar(value="Courier")
        self.current_font_size = tk.StringVar(value="12")
        
        # Color mappings for ANSI colors
        self.ansi_colors = {
            'black': '#000000', 'red': '#FF0000', 'green': '#00FF00', 'yellow': '#FFFF00',
            'blue': '#0000FF', 'magenta': '#FF00FF', 'cyan': '#00FFFF', 'white': '#FFFFFF',
            'bright_black': '#555555', 'bright_red': '#FF5555', 'bright_green': '#55FF55',
            'bright_yellow': '#FFFF55', 'bright_blue': '#5555FF', 'bright_magenta': '#FF55FF',
            'bright_cyan': '#55FFFF', 'bright_white': '#FFFFFF',
        }
        self.ansi_bg_colors = self.ansi_colors.copy()
        
        self.available_color_modes = {
            "Black BG, Colored Text": {"bg": "#000000", "fg": "#FFFFFF", "use_ansi_colors": True},
            "White BG, Colored Text": {"bg": "#FFFFFF", "fg": "#000000", "use_ansi_colors": True},
            "White BG, Black Text": {"bg": "#FFFFFF", "fg": "#000000", "use_ansi_colors": False},
            "Black BG, White Text": {"bg": "#000000", "fg": "#FFFFFF", "use_ansi_colors": False}
        }
        self.current_color_mode = tk.StringVar(value="Black BG, Colored Text")
        
        # Custom colors
        self.custom_bg_color = tk.StringVar(value="#000000")
        self.custom_fg_color = tk.StringVar(value="#FFFFFF")
        self.enable_ansi_colors = tk.BooleanVar(value=True)

    def get_default_fg(self):
        return self.available_color_modes[self.current_color_mode.get()]["fg"]

    def get_default_bg(self):
        return self.available_color_modes[self.current_color_mode.get()]["bg"]

    def use_ansi_colors(self):
        return self.available_color_modes[self.current_color_mode.get()]["use_ansi_colors"]

    def open_settings(self):
        settings_window = tk.Toplevel(self.app.root)
        settings_window.title("Terminal Settings")
        settings_window.geometry("400x450")
        settings_window.transient(self.app.root)
        settings_window.grab_set()

        # Create notebook for settings tabs
        notebook = ttk.Notebook(settings_window)
        notebook.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Basic settings tab
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="Basic")
        
        ttk.Label(basic_frame, text="Font:").pack(pady=5)
        font_combo = ttk.Combobox(basic_frame, textvariable=self.current_font, values=self.available_fonts, state="readonly")
        font_combo.pack(pady=5, fill=tk.X)

        ttk.Label(basic_frame, text="Font Size:").pack(pady=5)
        size_combo = ttk.Combobox(basic_frame, textvariable=self.current_font_size, values=self.font_sizes, state="readonly")
        size_combo.pack(pady=5, fill=tk.X)

        ttk.Label(basic_frame, text="Color Mode:").pack(pady=5)
        mode_combo = ttk.Combobox(basic_frame, textvariable=self.current_color_mode, values=list(self.available_color_modes.keys()), state="readonly")
        mode_combo.pack(pady=5, fill=tk.X)
        
        # Advanced color settings tab
        color_frame = ttk.Frame(notebook)
        notebook.add(color_frame, text="Colors")
        
        # Custom background color
        bg_frame = ttk.Frame(color_frame)
        bg_frame.pack(fill=tk.X, pady=10)
        ttk.Label(bg_frame, text="Background Color:").pack(side=tk.LEFT, padx=5)
        bg_entry = ttk.Entry(bg_frame, textvariable=self.custom_bg_color, width=10)
        bg_entry.pack(side=tk.LEFT, padx=5)
        
        def choose_bg_color():
            color = colorchooser.askcolor(initialcolor=self.custom_bg_color.get())
            if color[1]:
                self.custom_bg_color.set(color[1])
                bg_preview.config(bg=color[1])
        
        bg_preview = tk.Frame(bg_frame, width=20, height=20, bg=self.custom_bg_color.get())
        bg_preview.pack(side=tk.LEFT, padx=5)
        ttk.Button(bg_frame, text="Choose...", command=choose_bg_color).pack(side=tk.LEFT, padx=5)
        
        # Custom foreground color
        fg_frame = ttk.Frame(color_frame)
        fg_frame.pack(fill=tk.X, pady=10)
        ttk.Label(fg_frame, text="Text Color:").pack(side=tk.LEFT, padx=5)
        fg_entry = ttk.Entry(fg_frame, textvariable=self.custom_fg_color, width=10)
        fg_entry.pack(side=tk.LEFT, padx=5)
        
        def choose_fg_color():
            color = colorchooser.askcolor(initialcolor=self.custom_fg_color.get())
            if color[1]:
                self.custom_fg_color.set(color[1])
                fg_preview.config(bg=color[1])
        
        fg_preview = tk.Frame(fg_frame, width=20, height=20, bg=self.custom_fg_color.get())
        fg_preview.pack(side=tk.LEFT, padx=5)
        ttk.Button(fg_frame, text="Choose...", command=choose_fg_color).pack(side=tk.LEFT, padx=5)
        
        # ANSI color settings
        ansi_frame = ttk.LabelFrame(color_frame, text="ANSI Colors")
        ansi_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=5)
        
        ttk.Checkbutton(ansi_frame, text="Enable ANSI Color Support", variable=self.enable_ansi_colors).pack(anchor=tk.W, pady=5)
        
        # Preview frame
        preview_frame = ttk.LabelFrame(ansi_frame, text="Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        preview_text = tk.Text(preview_frame, height=5, width=40, wrap=tk.WORD)
        preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        preview_text.insert(tk.END, "Normal text\n")
        preview_text.insert(tk.END, "This is a preview of ANSI colors:\n")
        preview_text.insert(tk.END, "Red text\n", "red")
        preview_text.insert(tk.END, "Green text\n", "green")
        preview_text.insert(tk.END, "Blue text on yellow background", "blue_on_yellow")
        
        preview_text.tag_configure("red", foreground="#FF0000")
        preview_text.tag_configure("green", foreground="#00FF00")
        preview_text.tag_configure("blue_on_yellow", foreground="#0000FF", background="#FFFF00")
        preview_text.config(state=tk.DISABLED)
        
        # Apply custom colors when checkbox is clicked
        def update_preview():
            if self.enable_ansi_colors.get():
                preview_text.config(state=tk.NORMAL)
                preview_text.tag_configure("red", foreground="#FF0000")
                preview_text.tag_configure("green", foreground="#00FF00")
                preview_text.tag_configure("blue_on_yellow", foreground="#0000FF", background="#FFFF00")
                preview_text.config(state=tk.DISABLED)
            else:
                preview_text.config(state=tk.NORMAL)
                preview_text.tag_configure("red", foreground=self.custom_fg_color.get())
                preview_text.tag_configure("green", foreground=self.custom_fg_color.get())
                preview_text.tag_configure("blue_on_yellow", foreground=self.custom_fg_color.get(), background=self.custom_bg_color.get())
                preview_text.config(state=tk.DISABLED)
        
        self.enable_ansi_colors.trace_add("write", lambda *args: update_preview())
        
        # Buttons
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(pady=10, fill=tk.X)

        ttk.Button(button_frame, text="Apply", style="primary.TButton", 
                  command=lambda: self.apply_settings(settings_window)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", style="secondary.TButton", 
                  command=settings_window.destroy).pack(side=tk.LEFT, padx=5)

    def apply_settings(self, settings_window):
        try:
            # Apply font settings
            new_font = (self.current_font.get(), int(self.current_font_size.get()))
            self.app.terminal_emulator.terminal.config(font=new_font)

            # Apply color settings
            if self.enable_ansi_colors.get():
                # Use predefined color mode
                mode = self.available_color_modes[self.current_color_mode.get()]
                bg_color = mode["bg"]
                fg_color = mode["fg"]
                use_ansi = mode["use_ansi_colors"]
            else:
                # Use custom colors
                bg_color = self.custom_bg_color.get()
                fg_color = self.custom_fg_color.get()
                use_ansi = self.enable_ansi_colors.get()
                
                # Update the current color mode with custom colors
                custom_mode = {
                    "bg": bg_color,
                    "fg": fg_color,
                    "use_ansi_colors": use_ansi
                }
                self.available_color_modes["Custom"] = custom_mode
                self.current_color_mode.set("Custom")

            # Apply to terminal
            self.app.terminal_emulator.terminal.config(
                bg=bg_color,
                fg=fg_color,
                selectbackground="#4682B4",
                selectforeground="#FFFFFF",
                inactiveselectbackground="#4682B4",
                insertbackground=fg_color
            )

            self.app.terminal_emulator.terminal.tag_configure("sel", background="#4682B4", foreground="#FFFFFF")
            self.app.terminal_emulator.terminal.tag_raise("sel")

            self.app.terminal_emulator.setup_text_tags()
            self.app.terminal_emulator.redraw_terminal()
            self.app.terminal_emulator.on_resize(None)

            settings_window.destroy()
            self.app.status_var.set("Terminal settings applied")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to apply settings: {str(e)}")
            self.app.status_var.set(f"Settings error: {str(e)}")

    def set_mode(self, mode_name):
        """Set the terminal to one of the predefined modes"""
        # Store the selected mode name for later use
        self.selected_mode = mode_name
        
        # Map mode name to color mode
        mode_mapping = {
            "default": "Black BG, Colored Text",
            "dark": "Black BG, White Text",
            "light": "White BG, Black Text",
            "retro": "White BG, Colored Text"
        }
        
        selected_color_mode = mode_mapping.get(mode_name)
        mode = self.available_color_modes[selected_color_mode]
        
        # Apply the actual mode change
        if mode_name == "default":
            self.current_color_mode.set("Black BG, Colored Text")
        elif mode_name == "dark":
            self.current_color_mode.set("Black BG, White Text")
        elif mode_name == "light":
            self.current_color_mode.set("White BG, Black Text")
        elif mode_name == "retro":
            self.current_color_mode.set("White BG, Colored Text")
        
        # Check if we have a client object with terminal_emulator
        if hasattr(self, 'client') and hasattr(self.client, 'terminal_emulator'):
            terminal_emulator = self.client.terminal_emulator
            if hasattr(terminal_emulator, 'terminal'):
                # Configure terminal with new colors
                mode = self.available_color_modes[self.current_color_mode.get()]
                
                # Update the enable_ansi_colors setting based on the mode
                self.enable_ansi_colors.set(mode["use_ansi_colors"])
                
                terminal_emulator.terminal.config(
                    bg=mode["bg"],
                    fg=mode["fg"],
                    insertbackground=mode["fg"],
                    font=(self.current_font.get(), int(self.current_font_size.get()))
                )
                
                # Update text tags for proper color rendering
                terminal_emulator.setup_text_tags()
                
                # Redraw the terminal content with new colors
                if hasattr(terminal_emulator, 'redraw_terminal'):
                    terminal_emulator.redraw_terminal()
            # Fallback to redraw_screen if redraw_terminal doesn't exist
        elif hasattr(self.app.terminal_emulator, 'redraw_screen'):
                self.app.terminal_emulator.redraw_screen()
            # Force a resize event to ensure complete refresh
        if hasattr(self.app.terminal_emulator, 'on_resize'):
                self.app.terminal_emulator.on_resize(None)
            
            # Force the terminal to update immediately
                self.app.terminal_emulator.terminal.update_idletasks()
            
            # Update status
        if hasattr(self.app, 'status_var'):
                self.app.status_var.set(f"{mode_name.capitalize()} terminal mode applied")

    def redraw_terminal(self):
        """Redraw the terminal with current settings"""
        if not hasattr(self.app, 'terminal_emulator') or not hasattr(self.app.terminal_emulator, 'terminal'):
            return
            
        terminal = self.app.terminal_emulator.terminal
        if not terminal:
            return
            
        # Instead of just reinserting content, we need to force a complete redraw
        # using the terminal emulator's redraw method which properly applies formatting
        if hasattr(self.app.terminal_emulator, 'redraw_terminal'):
            self.app.terminal_emulator.redraw_terminal()
        # Fallback to redraw_screen if redraw_terminal doesn't exist
        elif hasattr(self.app.terminal_emulator, 'redraw_screen'):
            self.app.terminal_emulator.redraw_screen()
        
        # Force the terminal to update
        terminal.update_idletasks()
        
        # Store current content
        content = terminal.get("1.0", tk.END)
        
        # Clear and reinsert with new settings
        terminal.delete("1.0", tk.END)
        terminal.insert(tk.END, content)
        
        # Apply formatting if available
        if hasattr(self.app.terminal_emulator, 'apply_text_formatting'):
            self.app.terminal_emulator.apply_text_formatting()