import tkinter as tk
from tkinter import Menu

class ContextMenuManager:
    def __init__(self, browser):
        self.browser = browser

    def create_remote_context_menu(self):
        menu = Menu(self.browser.app.root, tearoff=0)
        menu.add_command(label="Open", command=self.browser.app.file_operations.open_remote_file)
        menu.add_separator()
        menu.add_command(label="Upload", command=self.browser.app.file_operations.upload_file)
        menu.add_command(label="Download", command=self.browser.app.file_operations.download_file)
        menu.add_separator()
        menu.add_command(label="Create File", command=self.browser.app.file_operations.create_remote_file)
        menu.add_command(label="Create Folder", command=self.browser.app.file_operations.create_remote_folder)
        menu.add_command(label="Delete", command=self.browser.app.file_operations.delete_remote)
        menu.add_separator()
        menu.add_command(label="Refresh", command=self.browser.refresh_browsers)
        return menu

    def show_remote_context_menu(self, event):
        try:
            self.browser.remote_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.browser.remote_context_menu.grab_release()