import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import platform
import re

def open_network_diagnostics(parent):
    # Open network diagnostics tool
    dialog = tk.Toplevel(parent)
    dialog.title("Network Diagnostics")
    dialog.geometry("600x500")
    dialog.transient(parent)
    dialog.grab_set()
    
    # Input frame
    input_frame = ttk.LabelFrame(dialog, text="Diagnostic Settings")
    input_frame.pack(fill=tk.X, padx=10, pady=10)
    
    ttk.Label(input_frame, text="Target Host:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    host_var = tk.StringVar(value="8.8.8.8")  # Default to Google DNS
    ttk.Entry(input_frame, textvariable=host_var, width=30).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
    
    # Tools frame
    tools_frame = ttk.LabelFrame(dialog, text="Diagnostic Tools")
    tools_frame.pack(fill=tk.X, padx=10, pady=10)
    
    # Checkboxes for different tools
    ping_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(tools_frame, text="Ping", variable=ping_var).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    
    traceroute_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(tools_frame, text="Traceroute", variable=traceroute_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
    
    dns_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(tools_frame, text="DNS Lookup", variable=dns_var).grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
    
    # Results frame
    results_frame = ttk.LabelFrame(dialog, text="Results")
    results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    results_text = tk.Text(results_frame, wrap=tk.WORD)
    results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=results_text.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    results_text.config(yscrollcommand=scrollbar.set)
    
    # Progress indicator
    progress_var = tk.StringVar(value="Ready")
    progress_label = ttk.Label(dialog, textvariable=progress_var)
    progress_label.pack(padx=10, pady=5)
    
    def run_command(command, output_prefix=""):
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True
            )
            
            # Read output line by line
            for line in process.stdout:
                results_text.insert(tk.END, f"{output_prefix}{line}")
                results_text.see(tk.END)
                results_text.update_idletasks()
            
            # Get any error output
            stderr = process.stderr.read()
            if stderr:
                results_text.insert(tk.END, f"{output_prefix}Error: {stderr}\n")
                results_text.see(tk.END)
            
            process.wait()
            return process.returncode
        except Exception as e:
            results_text.insert(tk.END, f"{output_prefix}Error executing command: {str(e)}\n")
            results_text.see(tk.END)
            return -1
    
    def run_diagnostics():
        host = host_var.get().strip()
        if not host:
            messagebox.showerror("Error", "Please enter a target host")
            return
        
        # Clear results
        results_text.delete(1.0, tk.END)
        
        # Disable run button during diagnostics
        run_button.config(state=tk.DISABLED)
        
        # Set progress indicator
        progress_var.set("Running diagnostics...")
        
        def diagnostic_thread():
            # Determine OS for command differences
            is_windows = platform.system() == "Windows"
            
            if ping_var.get():
                results_text.insert(tk.END, "=== PING TEST ===\n")
                ping_cmd = f"ping -n 4 {host}" if is_windows else f"ping -c 4 {host}"
                run_command(ping_cmd)
                results_text.insert(tk.END, "\n")
            
            if traceroute_var.get():
                results_text.insert(tk.END, "=== TRACEROUTE ===\n")
                tracert_cmd = f"tracert {host}" if is_windows else f"traceroute {host}"
                run_command(tracert_cmd)
                results_text.insert(tk.END, "\n")
            
            if dns_var.get():
                results_text.insert(tk.END, "=== DNS LOOKUP ===\n")
                
                # Try to determine if host is IP or hostname
                is_ip = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", host) is not None
                
                if is_ip:
                    # Reverse DNS lookup
                    nslookup_cmd = f"nslookup {host}"
                    run_command(nslookup_cmd)
                else:
                    # Forward DNS lookup
                    nslookup_cmd = f"nslookup {host}"
                    run_command(nslookup_cmd)
                    
                    # Additional DNS info
                    if is_windows:
                        run_command(f"nslookup -type=MX {host}", "Mail servers (MX records):\n")
                    else:
                        run_command(f"dig {host} MX", "Mail servers (MX records):\n")
                
                results_text.insert(tk.END, "\n")
            
            # Re-enable run button
            run_button.config(state=tk.NORMAL)
            progress_var.set("Diagnostics complete")
        
        # Start diagnostic thread
        threading.Thread(target=diagnostic_thread, daemon=True).start()
    
    # Buttons
    button_frame = ttk.Frame(dialog)
    button_frame.pack(pady=10)
    
    run_button = ttk.Button(button_frame, text="Run Diagnostics", command=run_diagnostics)
    run_button.pack(side=tk.LEFT, padx=5)
    
    close_button = ttk.Button(button_frame, text="Close", command=dialog.destroy)
    close_button.pack(side=tk.LEFT, padx=5)
    
    # Center dialog
    dialog.update_idletasks()
    width = dialog.winfo_width()
    height = dialog.winfo_height()
    x = (dialog.winfo_screenwidth() // 2) - (width // 2)
    y = (dialog.winfo_screenheight() // 2) - (height // 2)
    dialog.geometry(f"{width}x{height}+{x}+{y}")