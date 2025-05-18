import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess
import threading
from pathlib import Path

def open_certificate_manager(parent):
    # Open certificate manager tool
    dialog = tk.Toplevel(parent)
    dialog.title("SSL/TLS Certificate Manager")
    dialog.geometry("600x500")
    dialog.transient(parent)
    dialog.grab_set()
    
    # Create notebook for different certificate operations
    notebook = ttk.Notebook(dialog)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Create tabs for different operations
    create_tab = ttk.Frame(notebook)
    import_tab = ttk.Frame(notebook)
    view_tab = ttk.Frame(notebook)
    
    notebook.add(create_tab, text="Create Certificate")
    notebook.add(import_tab, text="Import Certificate")
    notebook.add(view_tab, text="View Certificates")
    
    # ===== Create Certificate Tab =====
    create_frame = ttk.LabelFrame(create_tab, text="Create Self-Signed Certificate")
    create_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Certificate details
    ttk.Label(create_frame, text="Common Name (CN):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    cn_var = tk.StringVar()
    ttk.Entry(create_frame, textvariable=cn_var, width=30).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
    
    ttk.Label(create_frame, text="Organization (O):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
    org_var = tk.StringVar()
    ttk.Entry(create_frame, textvariable=org_var, width=30).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
    
    ttk.Label(create_frame, text="Country (C):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
    country_var = tk.StringVar(value="US")
    ttk.Entry(create_frame, textvariable=country_var, width=30).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
    
    ttk.Label(create_frame, text="State/Province (ST):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
    state_var = tk.StringVar()
    ttk.Entry(create_frame, textvariable=state_var, width=30).grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
    
    ttk.Label(create_frame, text="Locality (L):").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
    locality_var = tk.StringVar()
    ttk.Entry(create_frame, textvariable=locality_var, width=30).grid(row=4, column=1, sticky=tk.EW, padx=5, pady=5)
    
    ttk.Label(create_frame, text="Validity (days):").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
    validity_var = tk.StringVar(value="365")
    ttk.Entry(create_frame, textvariable=validity_var, width=30).grid(row=5, column=1, sticky=tk.EW, padx=5, pady=5)
    
    ttk.Label(create_frame, text="Key Size:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
    key_size_var = tk.StringVar(value="2048")
    key_size_combo = ttk.Combobox(create_frame, textvariable=key_size_var, width=10)
    key_size_combo['values'] = ("1024", "2048", "4096")
    key_size_combo.grid(row=6, column=1, sticky=tk.W, padx=5, pady=5)
    
    ttk.Label(create_frame, text="Output Directory:").grid(row=7, column=0, sticky=tk.W, padx=5, pady=5)
    output_dir_var = tk.StringVar(value=os.path.expanduser("~/.ssh/certs"))
    output_dir_frame = ttk.Frame(create_frame)
    output_dir_frame.grid(row=7, column=1, sticky=tk.EW, padx=5, pady=5)
    
    ttk.Entry(output_dir_frame, textvariable=output_dir_var, width=30).pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def browse_output_dir():
        directory = filedialog.askdirectory(initialdir=output_dir_var.get())
        if directory:
            output_dir_var.set(directory)
    
    ttk.Button(output_dir_frame, text="Browse...", command=browse_output_dir).pack(side=tk.RIGHT, padx=5)
    
    ttk.Label(create_frame, text="Certificate Name:").grid(row=8, column=0, sticky=tk.W, padx=5, pady=5)
    cert_name_var = tk.StringVar(value="mycert")
    ttk.Entry(create_frame, textvariable=cert_name_var, width=30).grid(row=8, column=1, sticky=tk.EW, padx=5, pady=5)
    
    # Status and progress
    status_frame = ttk.Frame(create_tab)
    status_frame.pack(fill=tk.X, padx=10, pady=5)
    
    status_var = tk.StringVar(value="Ready")
    status_label = ttk.Label(status_frame, textvariable=status_var)
    status_label.pack(side=tk.LEFT)
    
    progress_var = tk.DoubleVar()
    progress = ttk.Progressbar(status_frame, variable=progress_var, maximum=100, length=200)
    progress.pack(side=tk.RIGHT)
    
    # Create certificate button
    def create_certificate():
        # Validate inputs
        cn = cn_var.get().strip()
        if not cn:
            messagebox.showerror("Error", "Common Name (CN) is required")
            return
        
        try:
            validity = int(validity_var.get())
            if validity <= 0:
                raise ValueError("Validity must be a positive number")
        except ValueError:
            messagebox.showerror("Error", "Validity must be a valid number of days")
            return
        
        output_dir = output_dir_var.get()
        cert_name = cert_name_var.get().strip()
        if not cert_name:
            messagebox.showerror("Error", "Certificate name is required")
            return
        
        # Create output directory if it doesn't exist
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Could not create output directory: {str(e)}")
            return
        
        # Disable create button during generation
        create_button.config(state=tk.DISABLED)
        
        # Update status
        status_var.set("Generating certificate...")
        progress_var.set(10)
        
        def certificate_generation_thread():
            try:
                # Build OpenSSL command for generating a self-signed certificate
                key_file = os.path.join(output_dir, f"{cert_name}.key")
                csr_file = os.path.join(output_dir, f"{cert_name}.csr")
                crt_file = os.path.join(output_dir, f"{cert_name}.crt")
                
                # Generate private key
                key_cmd = [
                    "openssl", "genrsa",
                    "-out", key_file,
                    key_size_var.get()
                ]
                
                # Run key generation command
                process = subprocess.Popen(
                    key_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    raise Exception(f"Error generating private key: {stderr}")
                
                progress_var.set(30)
                status_var.set("Creating certificate signing request...")
                
                # Build subject string
                subject = f"/CN={cn}"
                if org_var.get():
                    subject += f"/O={org_var.get()}"
                if country_var.get():
                    subject += f"/C={country_var.get()}"
                if state_var.get():
                    subject += f"/ST={state_var.get()}"
                if locality_var.get():
                    subject += f"/L={locality_var.get()}"
                
                # Generate CSR
                csr_cmd = [
                    "openssl", "req",
                    "-new",
                    "-key", key_file,
                    "-out", csr_file,
                    "-subj", subject
                ]
                
                # Run CSR generation command
                process = subprocess.Popen(
                    csr_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    raise Exception(f"Error generating CSR: {stderr}")
                
                progress_var.set(60)
                status_var.set("Creating self-signed certificate...")
                
                # Generate self-signed certificate
                crt_cmd = [
                    "openssl", "x509",
                    "-req",
                    "-days", str(validity),
                    "-in", csr_file,
                    "-signkey", key_file,
                    "-out", crt_file
                ]
                
                # Run certificate generation command
                process = subprocess.Popen(
                    crt_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    raise Exception(f"Error generating certificate: {stderr}")
                
                # Success
                progress_var.set(100)
                status_var.set("Certificate generated successfully")
                
                # Show success message
                messagebox.showinfo(
                    "Success", 
                    f"Certificate generated successfully:\n\n"
                    f"Private Key: {key_file}\n"
                    f"Certificate: {crt_file}"
                )
                
                # Refresh certificate list in view tab
                refresh_certificates()
                
            except Exception as e:
                messagebox.showerror("Error", str(e))
                status_var.set("Error generating certificate")
            finally:
                # Re-enable create button
                create_button.config(state=tk.NORMAL)
        
        # Start certificate generation in a separate thread
        threading.Thread(target=certificate_generation_thread, daemon=True).start()
    
    button_frame = ttk.Frame(create_tab)
    button_frame.pack(pady=10)
    
    create_button = ttk.Button(button_frame, text="Create Certificate", command=create_certificate)
    create_button.pack(side=tk.LEFT, padx=5)
    
    # ===== Import Certificate Tab =====
    import_frame = ttk.LabelFrame(import_tab, text="Import Certificate")
    import_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    ttk.Label(import_frame, text="Certificate File:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    cert_file_var = tk.StringVar()
    cert_file_frame = ttk.Frame(import_frame)
    cert_file_frame.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
    
    ttk.Entry(cert_file_frame, textvariable=cert_file_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def browse_cert_file():
        filename = filedialog.askopenfilename(
            title="Select Certificate File",
            filetypes=[
                ("Certificate Files", "*.crt;*.pem;*.cer"),
                ("All Files", "*.*")
            ]
        )
        if filename:
            cert_file_var.set(filename)
    
    ttk.Button(cert_file_frame, text="Browse...", command=browse_cert_file).pack(side=tk.RIGHT, padx=5)
    
    ttk.Label(import_frame, text="Private Key File:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
    key_file_var = tk.StringVar()
    key_file_frame = ttk.Frame(import_frame)
    key_file_frame.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
    
    ttk.Entry(key_file_frame, textvariable=key_file_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def browse_key_file():
        filename = filedialog.askopenfilename(
            title="Select Private Key File",
            filetypes=[
                ("Key Files", "*.key;*.pem"),
                ("All Files", "*.*")
            ]
        )
        if filename:
            key_file_var.set(filename)
    
    ttk.Button(key_file_frame, text="Browse...", command=browse_key_file).pack(side=tk.RIGHT, padx=5)
    
    ttk.Label(import_frame, text="Destination Name:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
    dest_name_var = tk.StringVar()
    ttk.Entry(import_frame, textvariable=dest_name_var, width=30).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
    
    ttk.Label(import_frame, text="Destination Directory:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
    dest_dir_var = tk.StringVar(value=os.path.expanduser("~/.ssh/certs"))
    dest_dir_frame = ttk.Frame(import_frame)
    dest_dir_frame.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
    
    ttk.Entry(dest_dir_frame, textvariable=dest_dir_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def browse_dest_dir():
        directory = filedialog.askdirectory(initialdir=dest_dir_var.get())
        if directory:
            dest_dir_var.set(directory)
    
    ttk.Button(dest_dir_frame, text="Browse...", command=browse_dest_dir).pack(side=tk.RIGHT, padx=5)
    
    # Import button
    def import_certificate():
        cert_file = cert_file_var.get().strip()
        key_file = key_file_var.get().strip()
        dest_name = dest_name_var.get().strip()
        dest_dir = dest_dir_var.get().strip()
        
        if not cert_file:
            messagebox.showerror("Error", "Certificate file is required")
            return
        
        if not os.path.exists(cert_file):
            messagebox.showerror("Error", "Certificate file does not exist")
            return
        
        if key_file and not os.path.exists(key_file):
            messagebox.showerror("Error", "Private key file does not exist")
            return
        
        if not dest_name:
            # Use the base filename without extension
            dest_name = os.path.splitext(os.path.basename(cert_file))[0]
        
        # Create destination directory if it doesn't exist
        try:
            os.makedirs(dest_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Could not create destination directory: {str(e)}")
            return
        
        try:
            # Copy certificate file
            import shutil
            dest_cert = os.path.join(dest_dir, f"{dest_name}.crt")
            shutil.copy2(cert_file, dest_cert)
            
            # Copy key file if provided
            if key_file:
                dest_key = os.path.join(dest_dir, f"{dest_name}.key")
                shutil.copy2(key_file, dest_key)
            
            messagebox.showinfo(
                "Success", 
                f"Certificate imported successfully:\n\n"
                f"Certificate: {dest_cert}\n"
                + (f"Private Key: {dest_key}" if key_file else "")
            )
            
            # Refresh certificate list in view tab
            refresh_certificates()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error importing certificate: {str(e)}")
    
    import_button_frame = ttk.Frame(import_tab)
    import_button_frame.pack(pady=10)
    
    ttk.Button(import_button_frame, text="Import Certificate", command=import_certificate).pack(side=tk.LEFT, padx=5)
    
    # ===== View Certificates Tab =====
    view_frame = ttk.Frame(view_tab)
    view_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Certificate list
    ttk.Label(view_frame, text="Certificates:").pack(anchor=tk.W, padx=5, pady=5)
    
    cert_list_frame = ttk.Frame(view_frame)
    cert_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    cert_tree = ttk.Treeview(cert_list_frame, columns=("name", "type", "expiry"), show="headings")
    cert_tree.heading("name", text="Name")
    cert_tree.heading("type", text="Type")
    cert_tree.heading("expiry", text="Expiry Date")
    cert_tree.column("name", width=150)
    cert_tree.column("type", width=100)
    cert_tree.column("expiry", width=150)
    cert_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    cert_scrollbar = ttk.Scrollbar(cert_list_frame, orient=tk.VERTICAL, command=cert_tree.yview)
    cert_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    cert_tree.configure(yscrollcommand=cert_scrollbar.set)
    
    # Certificate details
    details_frame = ttk.LabelFrame(view_frame, text="Certificate Details")
    details_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    details_text = tk.Text(details_frame, wrap=tk.WORD, height=10)
    details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    details_scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=details_text.yview)
    details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    details_text.config(yscrollcommand=details_scrollbar.set)
    
    # Function to refresh certificate list
    def refresh_certificates():
        # Clear existing items
        for item in cert_tree.get_children():
            cert_tree.delete(item)
        
        # Get certificates from default directory
        cert_dir = os.path.expanduser("~/.ssh/certs")
        if not os.path.exists(cert_dir):
            return
        
        for filename in os.listdir(cert_dir):
            if filename.endswith(('.crt', '.pem', '.cer')):
                cert_path = os.path.join(cert_dir, filename)
                cert_name = os.path.splitext(filename)[0]
                
                # Get certificate info using OpenSSL
                try:
                    cmd = ["openssl", "x509", "-in", cert_path, "-noout", "-text"]
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    stdout, stderr = process.communicate()
                    
                    if process.returncode != 0:
                        continue
                    
                    # Extract certificate type and expiry date
                    cert_type = "X.509"
                    expiry_date = "Unknown"
                    
                    # Try to extract expiry date
                    cmd = ["openssl", "x509", "-in", cert_path, "-noout", "-enddate"]
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    stdout, stderr = process.communicate()
                    
                    if process.returncode == 0 and stdout:
                        # Format: notAfter=May 17 10:23:13 2021 GMT
                        expiry_parts = stdout.strip().split('=', 1)
                        if len(expiry_parts) > 1:
                            expiry_date = expiry_parts[1]
                    
                    # Add to tree
                    cert_tree.insert("", tk.END, values=(cert_name, cert_type, expiry_date), tags=(cert_path,))
                    
                except Exception:
                    # Skip this certificate if there's an error
                    continue
    
    # Show certificate details when selected
    def show_certificate_details(event):
        selected_items = cert_tree.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        cert_path = cert_tree.item(item, "tags")[0]
        
        # Clear details
        details_text.delete(1.0, tk.END)
        
        # Get certificate details using OpenSSL
        try:
            cmd = ["openssl", "x509", "-in", cert_path, "-noout", "-text"]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                details_text.insert(tk.END, stdout)
            else:
                details_text.insert(tk.END, f"Error getting certificate details: {stderr}")
        except Exception as e:
            details_text.insert(tk.END, f"Error: {str(e)}")
    
    cert_tree.bind("<<TreeviewSelect>>", show_certificate_details)
    
    # Buttons for view tab
    view_button_frame = ttk.Frame(view_tab)
    view_button_frame.pack(pady=10)
    
    ttk.Button(view_button_frame, text="Refresh", command=refresh_certificates).pack(side=tk.LEFT, padx=5)
    
    def export_certificate():
        selected_items = cert_tree.selection()
        if not selected_items:
            messagebox.showinfo("Export", "Please select a certificate to export")
            return
        
        item = selected_items[0]
        cert_path = cert_tree.item(item, "tags")[0]
        cert_name = cert_tree.item(item, "values")[0]
        
        # Ask for export location
        export_path = filedialog.asksaveasfilename(
            title="Export Certificate",
            initialfile=f"{cert_name}.crt",
            defaultextension=".crt",
            filetypes=[
                ("Certificate Files", "*.crt"),
                ("PEM Files", "*.pem"),
                ("All Files", "*.*")
            ]
        )
        
        if export_path:
            try:
                import shutil
                shutil.copy2(cert_path, export_path)
                messagebox.showinfo("Export", f"Certificate exported to {export_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Error exporting certificate: {str(e)}")
    
    ttk.Button(view_button_frame, text="Export", command=export_certificate).pack(side=tk.LEFT, padx=5)
    
    def delete_certificate():
        selected_items = cert_tree.selection()
        if not selected_items:
            messagebox.showinfo("Delete", "Please select a certificate to delete")
            return
        
        item = selected_items[0]
        cert_path = cert_tree.item(item, "tags")[0]
        cert_name = cert_tree.item(item, "values")[0]
        
        # Confirm deletion
        if not messagebox.askyesno("Delete", f"Are you sure you want to delete certificate '{cert_name}'?"):
            return
        
        try:
            # Delete certificate file
            os.remove(cert_path)
            
            # Try to delete corresponding key file if it exists
            key_path = os.path.splitext(cert_path)[0] + ".key"
            if os.path.exists(key_path):
                os.remove(key_path)
            
            # Refresh certificate list
            refresh_certificates()
            
            messagebox.showinfo("Delete", f"Certificate '{cert_name}' deleted")
        except Exception as e:
            messagebox.showerror("Error", f"Error deleting certificate: {str(e)}")
    
    ttk.Button(view_button_frame, text="Delete", command=delete_certificate).pack(side=tk.LEFT, padx=5)
    
    # Initial refresh of certificates
    refresh_certificates()
    
    # Close button for dialog
    close_button = ttk.Button(dialog, text="Close", command=dialog.destroy)
    close_button.pack(pady=10)
    
    # Center dialog
    dialog.update_idletasks()
    width = dialog.winfo_width()
    height = dialog.winfo_height()
    x = (dialog.winfo_screenwidth() // 2) - (width // 2)
    y = (dialog.winfo_screenheight() // 2) - (height // 2)
    dialog.geometry(f"{width}x{height}+{x}+{y}")