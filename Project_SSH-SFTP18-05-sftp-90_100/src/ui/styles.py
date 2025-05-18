import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

def setup_styles():
    style = ttk.Style()
    
    # Configure treeview styles
    style.configure("Treeview", rowheight=25)
    style.configure("Treeview.Heading", font=(None, 10, "bold"))
    
    # Configure frame with border for treeviews
    style.configure("TreeviewBorder.TFrame", borderwidth=1, relief="solid")
    
    # Configure button styles
    style.configure("primary.TButton", font=(None, 10))
    style.configure("secondary.TButton", font=(None, 10))
    style.configure("info.TButton", font=(None, 10))
    style.configure("danger.TButton", font=(None, 10))
    style.configure("outline.TButton", font=(None, 9))
    
    # Configure label styles
    style.configure("secondary.TLabel", font=(None, 9))
    
    # Configure outline button variants
    style.configure("primary.Outline.TButton", font=(None, 9))
    style.configure("secondary.Outline.TButton", font=(None, 9))
    style.configure("info.Outline.TButton", font=(None, 9))
    style.configure("danger.Outline.TButton", font=(None, 9))
    
    return style