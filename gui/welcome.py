import tkinter as tk
from tkinter import PhotoImage
import os

def welcome_screen(existing_root=None):
    """
    Display the welcome screen with persistent image handling.
    
    Args:
        existing_root: Optional existing Tk root window to reuse
    """

    def open_register():
        """Navigate to the Register Screen."""
        from gui.register import register_screen
        clear_screen()
        register_screen(root)

    def open_login():
        """Navigate to the Login Screen."""
        from gui.login import login_screen
        clear_screen()
        login_screen(root)

    def clear_screen():
        """Clear all widgets from the current screen."""
        for widget in root.winfo_children():
            widget.destroy()

    # Use existing root if provided, otherwise create a new one
    if existing_root:
        root = existing_root
        clear_screen()
    else:
        root = tk.Tk()

    root.title("Welcome - FileHaven")
    root.geometry("600x400")
    root.configure(bg="#E3F2FD")

    # Center the window
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width / 2) - (600 / 2))
    y = int((screen_height / 2) - (400 / 2))
    root.geometry(f"600x400+{x}+{y}")

    # Main Frame
    frame = tk.Frame(root, bg="#E3F2FD")
    frame.pack(expand=True)

    # Get absolute path to logo
    logo_path = r"C:\Users\brian\OneDrive\Desktop\Helping Assignment\Group Assignment IT Apps 24 jan\FileManager\assets\logo.png"

    # Reload the image **every time** welcome_screen is called
    try:
        if os.path.exists(logo_path):
            logo_image = PhotoImage(file=logo_path).subsample(3, 3)  # Recreate a fresh image reference
            logo_label = tk.Label(frame, image=logo_image, bg="#E3F2FD")
            logo_label.pack(pady=10)
            # Keep a reference to prevent garbage collection
            logo_label.image = logo_image
            
    except Exception as e:
        tk.Label(frame, text="FileHaven", font=("Helvetica", 24, "bold"), 
                 bg="#E3F2FD", fg="#1E88E5").pack(pady=10)

    # Welcome Text
    tk.Label(
        frame,
        text="WELCOME",
        font=("Helvetica", 18, "bold"),
        bg="#E3F2FD",
        fg="#1E88E5",
    ).pack(pady=10)

    # Buttons
    tk.Button(
        frame,
        text="Register",
        command=open_register,
        bg="#1E88E5",
        fg="white",
        font=("Helvetica", 14),
        width=20,
        height=2,
        relief="flat",
    ).pack(pady=10)

    tk.Button(
        frame,
        text="Login",
        command=open_login,
        bg="#1E88E5",
        fg="white",
        font=("Helvetica", 14),
        width=20,
        height=2,
        relief="flat",
    ).pack(pady=10)

    # Footer
    tk.Label(
        frame,
        text="FileHaven @2025",
        font=("Helvetica", 10),
        bg="#E3F2FD",
        fg="#666",
    ).pack(pady=20)

    if not existing_root:
        root.mainloop()

    return root
