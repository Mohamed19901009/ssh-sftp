import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading

def open_key_generator(parent):
    # Open key generator tool
    dialog = tk.Toplevel(parent)
    dialog.title("SSH Key Generator")
    dialog.geometry("500x450")
    dialog.transient(parent)
    dialog.grab_set()
    
    # Key settings frame
    settings_frame = ttk.LabelFrame(dialog, text="Key Settings")
    settings_frame.pack(fill=tk.X, padx=10, pady=10)
    
    # Key type
    ttk.Label(settings_frame, text="Key Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    key_type_var = tk.StringVar(value="rsa")
    key_type_combo = ttk.Combobox(settings_frame, textvariable=key_type_var, width=15)
    key_type_combo['values'] = ("rsa", "dsa", "ecdsa", "ed25519")
    key_type_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
    
    # Key size (only for RSA and DSA)
    ttk.Label(settings_frame, text="Key Size:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
    key_size_var = tk.StringVar(value="2048")
    key_size_combo = ttk.Combobox(settings_frame, textvariable=key_size_var, width=15)
    key_size_combo['values'] = ("1024", "2048", "4096")
    key_size_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
    
    # Comment/label
    ttk.Label(settings_frame, text="Comment:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
    comment_var = tk.StringVar(value=f"{os.getlogin()}@{os.environ.get('COMPUTERNAME', 'localhost')}")
    ttk.Entry(settings_frame, textvariable=comment_var, width=30).grid(row=2, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=5)
    
    # Passphrase
    ttk.Label(settings_frame, text="Passphrase:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
    passphrase_var = tk.StringVar()
    ttk.Entry(settings_frame, textvariable=passphrase_var, width=30, show="*").grid(row=3, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=5)
    
    # Confirm passphrase
    ttk.Label(settings_frame, text="Confirm:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
    confirm_var = tk.StringVar()
    ttk.Entry(settings_frame, textvariable=confirm_var, width=30, show="*").grid(row=4, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=5)
    
    # Output settings frame
    output_frame = ttk.LabelFrame(dialog, text="Output Settings")
    output_frame.pack(fill=tk.X, padx=10, pady=10)
    
    # Output directory
    ttk.Label(output_frame, text="Save to:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    output_dir_var = tk.StringVar(value=os.path.expanduser("~/.ssh"))
    output_dir_entry = ttk.Entry(output_frame, textvariable=output_dir_var, width=30)
    output_dir_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
    
    def browse_output_dir():
        directory = filedialog.askdirectory(initialdir=output_dir_var.get())
        if directory:
            output_dir_var.set(directory)
    
    ttk.Button(output_frame, text="Browse...", command=browse_output_dir).grid(row=0, column=2, padx=5, pady=5)
    
    # Key filename
    ttk.Label(output_frame, text="Filename:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
    filename_var = tk.StringVar(value="id_rsa")
    filename_entry = ttk.Entry(output_frame, textvariable=filename_var, width=30)
    filename_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
    
    # Update filename when key type changes
    def update_filename(*args):
        key_type = key_type_var.get()
        if key_type == "rsa":
            filename_var.set("id_rsa")
        elif key_type == "dsa":
            filename_var.set("id_dsa")
        elif key_type == "ecdsa":
            filename_var.set("id_ecdsa")
        elif key_type == "ed25519":
            filename_var.set("id_ed25519")
    
    key_type_var.trace("w", update_filename)
    
    # Status and progress
    status_frame = ttk.Frame(dialog)
    status_frame.pack(fill=tk.X, padx=10, pady=5)
    
    status_var = tk.StringVar(value="Ready")
    status_label = ttk.Label(status_frame, textvariable=status_var)
    status_label.pack(side=tk.LEFT)
    
    progress_var = tk.DoubleVar()
    progress = ttk.Progressbar(status_frame, variable=progress_var, maximum=100, length=200)
    progress.pack(side=tk.RIGHT)
    
    # Results frame
    results_frame = ttk.LabelFrame(dialog, text="Key Information")
    results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    results_text = tk.Text(results_frame, wrap=tk.WORD, height=8)
    results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=results_text.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    results_text.config(yscrollcommand=scrollbar.set)
    
    def generate_key():
        # Validate inputs
        key_type = key_type_var.get()
        key_size = key_size_var.get()
        passphrase = passphrase_var.get()
        confirm = confirm_var.get()
        output_dir = output_dir_var.get()
        filename = filename_var.get()
        comment = comment_var.get()
        
        # Check passphrase match
        if passphrase != confirm:
            messagebox.showerror("Error", "Passphrase and confirmation do not match")
            return
        
        # Check output directory
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("Error", f"Could not create output directory: {str(e)}")
                return
        
        # Disable generate button during generation
        generate_button.config(state=tk.DISABLED)
        
        # Update status
        status_var.set("Generating key...")
        progress_var.set(10)
        
        def key_generation_thread():
            try:
                # Build ssh-keygen command
                cmd = ["ssh-keygen"]
                cmd.append("-t")
                cmd.append(key_type)
                
                if key_type in ["rsa", "dsa"]:
                    cmd.append("-b")
                    cmd.append(key_size)
                
                # Set output file
                output_file = os.path.join(output_dir, filename)
                cmd.append("-f")
                cmd.append(output_file)
                
                # Set comment
                if comment:
                    cmd.append("-C")
                    cmd.append(comment)
                
                # Set passphrase (empty string for no passphrase)
                cmd.append("-N")
                cmd.append(passphrase)
                
                # Run command
                import subprocess
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                stdout, stderr = process.communicate()
                
                # Update progress
                progress_var.set(80)
                
                if process.returncode == 0:
                    # Success
                    status_var.set("Key generated successfully")
                    progress_var.set(100)
                    
                    # Display key info
                    results_text.delete(1.0, tk.END)
                    results_text.insert(tk.END, f"SSH key generated successfully:\n\n")
                    results_text.insert(tk.END, f"Private key: {output_file}\n")
                    results_text.insert(tk.END, f"Public key: {output_file}.pub\n\n")
                    
                    # Read and display public key
                    try:
                        with open(f"{output_file}.pub", "r") as f:
                            public_key = f.read().strip()
                            results_text.insert(tk.END, f"Public key content:\n{public_key}\n")
                    except Exception as e:
                        results_text.insert(tk.END, f"Could not read public key: {str(e)}\n")
                else:
                    # Error
                    status_var.set("Error generating key")
                    results_text.delete(1.0, tk.END)
                    results_text.insert(tk.END, f"Error generating SSH key:\n\n")
                    if stderr:
                        results_text.insert(tk.END, stderr)
                    else:
                        results_text.insert(tk.END, "Unknown error occurred")
            except Exception as e:
                status_var.set("Error generating key")
                results_text.delete(1.0, tk.END)
                results_text.insert(tk.END, f"Error: {str(e)}")
            finally:
                # Re-enable generate button
                generate_button.config(state=tk.NORMAL)
        
        # Start key generation thread
        threading.Thread(target=key_generation_thread, daemon=True).start()
    
    # Buttons
    button_frame = ttk.Frame(dialog)
    button_frame.pack(pady=10)
    
    generate_button = ttk.Button(button_frame, text="Generate Key", command=generate_key)
    generate_button.pack(side=tk.LEFT, padx=5)
    
    close_button = ttk.Button(button_frame, text="Close", command=dialog.destroy)
    close_button.pack(side=tk.LEFT, padx=5)
    
    # Center dialog
    dialog.update_idletasks()
    width = dialog.winfo_width()
    height = dialog.winfo_height()
    x = (dialog.winfo_screenwidth() // 2) - (width // 2)
    y = (dialog.winfo_screenheight() // 2) - (height // 2)
    dialog.geometry(f"{width}x{height}+{x}+{y}")