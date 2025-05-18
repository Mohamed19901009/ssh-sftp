import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
from queue import Queue

def open_port_scanner(parent):
    # Open port scanner tool
    dialog = tk.Toplevel(parent)
    dialog.title("Port Scanner")
    dialog.geometry("500x400")
    dialog.transient(parent)
    dialog.grab_set()
    
    # Input frame
    input_frame = ttk.LabelFrame(dialog, text="Scan Settings")
    input_frame.pack(fill=tk.X, padx=10, pady=10)
    
    ttk.Label(input_frame, text="Target Host:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    host_var = tk.StringVar()
    ttk.Entry(input_frame, textvariable=host_var, width=30).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
    
    ttk.Label(input_frame, text="Port Range:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
    port_frame = ttk.Frame(input_frame)
    port_frame.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
    
    start_port_var = tk.StringVar(value="1")
    ttk.Entry(port_frame, textvariable=start_port_var, width=6).pack(side=tk.LEFT)
    ttk.Label(port_frame, text=" - ").pack(side=tk.LEFT)
    end_port_var = tk.StringVar(value="1024")
    ttk.Entry(port_frame, textvariable=end_port_var, width=6).pack(side=tk.LEFT)
    
    # Results frame
    results_frame = ttk.LabelFrame(dialog, text="Results")
    results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    results_text = tk.Text(results_frame, wrap=tk.WORD, height=15)
    results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=results_text.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    results_text.config(yscrollcommand=scrollbar.set)
    
    # Progress bar
    progress_var = tk.DoubleVar()
    progress = ttk.Progressbar(dialog, variable=progress_var, maximum=100)
    progress.pack(fill=tk.X, padx=10, pady=5)
    
    # Status label
    status_var = tk.StringVar(value="Ready")
    status_label = ttk.Label(dialog, textvariable=status_var)
    status_label.pack(padx=10, pady=5)
    
    def scan_port(host, port, results_queue):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((host, port))
            if result == 0:
                service = "Unknown"
                try:
                    service = socket.getservbyport(port)
                except:
                    pass
                results_queue.put((port, service))
            sock.close()
        except:
            pass
    
    def start_scan():
        host = host_var.get().strip()
        if not host:
            messagebox.showerror("Error", "Please enter a target host")
            return
        
        try:
            start_port = int(start_port_var.get())
            end_port = int(end_port_var.get())
            if start_port < 1 or start_port > 65535 or end_port < 1 or end_port > 65535:
                raise ValueError("Port range must be between 1 and 65535")
            if start_port > end_port:
                start_port, end_port = end_port, start_port
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return
        
        # Clear results
        results_text.delete(1.0, tk.END)
        results_text.insert(tk.END, f"Scanning {host} for open ports...\n\n")
        
        # Disable scan button during scan
        scan_button.config(state=tk.DISABLED)
        cancel_button.config(state=tk.NORMAL)
        
        # Reset progress
        progress_var.set(0)
        status_var.set("Scanning...")
        
        # Create a queue for results
        results_queue = Queue()
        
        # Calculate total ports to scan
        total_ports = end_port - start_port + 1
        scanned_ports = 0
        
        # Flag to track if scan was cancelled
        cancelled = [False]
        
        def update_progress():
            if cancelled[0]:
                return
                
            # Check for results
            open_ports = []
            while not results_queue.empty():
                port, service = results_queue.get()
                open_ports.append((port, service))
            
            # Update results if we found open ports
            if open_ports:
                for port, service in sorted(open_ports):
                    results_text.insert(tk.END, f"Port {port}: Open ({service})\n")
                    results_text.see(tk.END)
            
            # Update progress
            nonlocal scanned_ports
            progress_var.set((scanned_ports / total_ports) * 100)
            status_var.set(f"Scanned {scanned_ports}/{total_ports} ports")
            
            # Schedule next update if scan is still running
            if scanned_ports < total_ports and not cancelled[0]:
                dialog.after(100, update_progress)
            else:
                # Scan complete
                scan_button.config(state=tk.NORMAL)
                cancel_button.config(state=tk.DISABLED)
                if cancelled[0]:
                    status_var.set("Scan cancelled")
                    results_text.insert(tk.END, "\nScan cancelled.\n")
                else:
                    status_var.set("Scan complete")
                    results_text.insert(tk.END, "\nScan complete.\n")
                results_text.see(tk.END)
        
        def scan_thread():
            nonlocal scanned_ports
            for port in range(start_port, end_port + 1):
                if cancelled[0]:
                    break
                scan_port(host, port, results_queue)
                scanned_ports += 1
        
        # Start scan thread
        threading.Thread(target=scan_thread, daemon=True).start()
        
        # Start progress updates
        update_progress()
    
    def cancel_scan():
        cancelled[0] = True
    
    # Buttons
    button_frame = ttk.Frame(dialog)
    button_frame.pack(pady=10)
    
    scan_button = ttk.Button(button_frame, text="Start Scan", command=start_scan)
    scan_button.pack(side=tk.LEFT, padx=5)
    
    cancel_button = ttk.Button(button_frame, text="Cancel", command=cancel_scan, state=tk.DISABLED)
    cancel_button.pack(side=tk.LEFT, padx=5)
    
    close_button = ttk.Button(button_frame, text="Close", command=dialog.destroy)
    close_button.pack(side=tk.LEFT, padx=5)
    
    # Center dialog
    dialog.update_idletasks()
    width = dialog.winfo_width()
    height = dialog.winfo_height()
    x = (dialog.winfo_screenwidth() // 2) - (width // 2)
    y = (dialog.winfo_screenheight() // 2) - (height // 2)
    dialog.geometry(f"{width}x{height}+{x}+{y}")