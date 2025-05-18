import tkinter as tk
from tkinter import font
import pyte
from pyte.screens import Char
import time
from queue import Empty

class TerminalEmulator:
    def __init__(self, app):
        self.app = app
        self.terminal = None
        self.context_menu = None
        
        # Terminal emulation with history
        self.screen = pyte.HistoryScreen(80, 24, history=10000)
        self.stream = pyte.Stream(self.screen)
        
        # Resize debounce
        self.resize_timeout = None
        self.last_resize_time = 0
        self.resize_delay = 0.2

    def create_terminal_frame(self, parent):
        # SSH Terminal frame
        terminal_frame = tk.LabelFrame(parent, text="SSH Terminal")
        terminal_frame.pack(fill=tk.BOTH, expand=True)

        # Terminal text widget with default settings
        self.terminal = tk.Text(
            terminal_frame,
            wrap=tk.NONE,
            bg="black",
            fg="white",
            font=("Courier New", 10),
            selectbackground="#4682B4",
            selectforeground="#FFFFFF",
            inactiveselectbackground="#4682B4",
            insertbackground="white",
            insertwidth=2,
            highlightthickness=1,
            highlightbackground="#CCCCCC",
            relief=tk.SUNKEN
        )
        self.terminal.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Vertical scrollbar for terminal
        yscroll = tk.Scrollbar(terminal_frame, orient=tk.VERTICAL, command=self.terminal.yview)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.terminal.config(yscrollcommand=yscroll.set)
        
        # Bind events
        self.terminal.bind("<<Copy>>", self.copy_text)
        self.terminal.bind("<<Paste>>", self.paste_text)
        self.terminal.bind("<Button-3>", self.show_context_menu)
        self.terminal.bind("<Key>", self.handle_key)
        self.terminal.bind("<Control-c>", self.send_ctrl_c)
        self.terminal.bind("<MouseWheel>", self.on_mouse_wheel)
        self.terminal.bind("<Button-4>", lambda event: self.on_mouse_wheel(event, -1))
        self.terminal.bind("<Button-5>", lambda event: self.on_mouse_wheel(event, 1))
        
        # Context menu for copy/paste
        self.context_menu = tk.Menu(self.app.root, tearoff=0)
        self.context_menu.add_command(label="Copy", command=self.copy_text)
        self.context_menu.add_command(label="Paste", command=self.paste_text)
        
        # Setup basic text tags
        self.setup_text_tags()

    def setup_text_tags(self):
        # Define basic ANSI colors
        ansi_colors = {
            "black": "#000000",
            "red": "#CD0000",
            "green": "#00CD00",
            "yellow": "#CDCD00",
            "blue": "#0000CD",
            "magenta": "#CD00CD",
            "cyan": "#00CDCD",
            "white": "#E5E5E5",
            "default": "white"
        }
        
        ansi_bg_colors = {
            "black": "#000000",
            "red": "#CD0000",
            "green": "#00CD00",
            "yellow": "#CDCD00",
            "blue": "#0000CD",
            "magenta": "#CD00CD",
            "cyan": "#00CDCD",
            "white": "#E5E5E5",
            "default": "black"
        }

        # Create tags for all color combinations
        for fg in list(ansi_colors.keys()):
            for bg in list(ansi_bg_colors.keys()):
                for bold in [False, True]:
                    for underscore in [False, True]:
                        tag_name = f"fg_{fg}_bg_{bg}_bold_{bold}_underscore_{underscore}"
                        config = {
                            'foreground': ansi_colors[fg],
                            'background': ansi_bg_colors[bg]
                        }
                        if bold:
                            config['font'] = ("Courier New", 10, "bold")
                        else:
                            config['font'] = ("Courier New", 10)
                        if underscore:
                            config['underline'] = True
                        self.terminal.tag_configure(tag_name, **config)

        self.terminal.tag_configure("sel", background="#4682B4", foreground="#FFFFFF")
        self.terminal.tag_raise("sel")

    def redraw_terminal(self):
        self.terminal.delete(1.0, tk.END)

        # Draw history
        for row in self.screen.history.top:
            text = ""
            current_fg = None
            current_bg = None
            current_bold = None
            current_underscore = None
            for x in range(self.screen.columns):
                char = row.get(x, Char(data=" "))
                data = char.data
                fg = char.fg or "default"
                bg = char.bg or "default"
                bold = char.bold
                underscore = char.underscore
                if (fg != current_fg or bg != current_bg or
                    bold != current_bold or underscore != current_underscore):
                    if text:
                        tag_name = (f"fg_{current_fg}_bg_{current_bg}_"
                                   f"bold_{current_bold}_underscore_{current_underscore}")
                        self.terminal.insert(tk.END, text, tag_name)
                        text = ""
                    current_fg = fg
                    current_bg = bg
                    current_bold = bold
                    current_underscore = underscore
                text += data
            if text:
                tag_name = (f"fg_{current_fg}_bg_{current_bg}_"
                           f"bold_{current_bold}_underscore_{current_underscore}")
                self.terminal.insert(tk.END, text, tag_name)
            self.terminal.insert(tk.END, "\n")

        # Draw current buffer
        for y in range(self.screen.lines):
            row = self.screen.buffer.get(y, {})
            text = ""
            current_fg = None
            current_bg = None
            current_bold = None
            current_underscore = None
            for x in range(self.screen.columns):
                char = row.get(x, Char(data=" "))
                data = char.data
                fg = char.fg or "default"
                bg = char.bg or "default"
                bold = char.bold
                underscore = char.underscore
                if (fg != current_fg or bg != current_bg or
                    bold != current_bold or underscore != current_underscore):
                    if text:
                        tag_name = (f"fg_{current_fg}_bg_{current_bg}_"
                                   f"bold_{current_bold}_underscore_{current_underscore}")
                        self.terminal.insert(tk.END, text, tag_name)
                        text = ""
                    current_fg = fg
                    current_bg = bg
                    current_bold = bold
                    current_underscore = underscore
                text += data
            if text:
                tag_name = (f"fg_{current_fg}_bg_{current_bg}_"
                           f"bold_{current_bold}_underscore_{current_underscore}")
                self.terminal.insert(tk.END, text, tag_name)
            self.terminal.insert(tk.END, "\n")

        # Set cursor position
        cursor_line = len(self.screen.history.top) + self.screen.cursor.y + 1
        cursor_col = self.screen.cursor.x
        cursor_index = f"{cursor_line}.{cursor_col}"
        self.terminal.mark_set("insert", cursor_index)
        self.terminal.see("insert")
        self.terminal.tag_raise("sel")

    def update_terminal(self):
        try:
            data_received = False
            while True:
                data = self.app.queue.get_nowait()
                self.stream.feed(data)
                data_received = True
        except Empty:
            pass
            
        if data_received:
            self.redraw_terminal()

    def handle_key(self, event):
        if not self.app.connected:
            return "break"

        key = event.keysym
        char = event.char
        # Don't echo characters locally, just send them to the server
        if key == "Return":
            self.app.ssh_client.channel.send("\n")
        elif key == "BackSpace":
            self.app.ssh_client.channel.send("\b")
        elif key == "Tab":
            self.app.ssh_client.channel.send("\t")
        elif key == "Up":
            self.app.ssh_client.channel.send("\x1b[A")
        elif key == "Down":
            self.app.ssh_client.channel.send("\x1b[B")
        elif key == "Right":
            self.app.ssh_client.channel.send("\x1b[C")
        elif key == "Left":
            self.app.ssh_client.channel.send("\x1b[D")
        elif char and (char.isprintable() or char == " "):
            self.app.ssh_client.channel.send(char)

        return "break"

    def send_ctrl_c(self, event):
        if self.app.connected:
            self.app.ssh_client.channel.send("\x03")
            return "break"

    def on_resize(self, event):
        if not self.app.connected or not self.app.ssh_client.channel:
            return

        current_time = time.time()
        if current_time - self.last_resize_time < self.resize_delay:
            if self.resize_timeout:
                self.app.root.after_cancel(self.resize_timeout)
            self.resize_timeout = self.app.root.after(int(self.resize_delay * 1000), self.handle_resize)
            return
        self.handle_resize()

    def handle_resize(self):
        try:
            # Use fixed font size
            font_size = 10
            char_width = font.Font(family="Courier New", size=font_size).measure("M")
            char_height = font.Font(family="Courier New", size=font_size).metrics("linespace")

            width = max(80, self.terminal.winfo_width() // char_width)
            height = max(24, self.terminal.winfo_height() // char_height)

            self.app.ssh_client.channel.resize_pty(width=width, height=height)
            self.screen.resize(height, width)
            self.redraw_terminal()

            self.last_resize_time = time.time()
            self.resize_timeout = None
        except Exception:
            pass

    def on_mouse_wheel(self, event, delta=None):
        if delta is None:
            delta = -int(event.delta / 120)
        self.terminal.yview_scroll(delta, "units")
        return "break"

    def copy_text(self, event=None):
        try:
            selected = self.terminal.selection_get()
            self.app.root.clipboard_clear()
            self.app.root.clipboard_append(selected)
            self.app.status_var.set("Text copied to clipboard")
        except tk.TclError:
            self.app.status_var.set("No text selected to copy")

    def paste_text(self, event=None):
        if self.app.connected:
            try:
                text = self.app.root.clipboard_get()
                self.app.ssh_client.channel.send(text)
                self.app.status_var.set("Text pasted to terminal")
            except tk.TclError:
                self.app.status_var.set("No text in clipboard")

    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)