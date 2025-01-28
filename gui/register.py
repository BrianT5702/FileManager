import tkinter as tk
from tkinter import PhotoImage, messagebox
from firebase_config import db

def register_screen(root=None):
    """Display the registration screen."""

    def register_user():
        """Register a new user in Firebase Firestore."""
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        confirm_password = confirm_password_entry.get().strip()

        # Validate fields
        if not username or not password or not confirm_password:
            messagebox.showerror("Error", "All fields are required!")
            return

        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match!")
            return

        if len(password) < 6 or not any(char.isdigit() for char in password) or not any(char.isalpha() for char in password):
            messagebox.showerror("Error", "Password must be at least 6 characters long and include both letters and numbers!")
            return

        try:
            # Check if username already exists
            user_doc = db.collection("users").document(username).get()
            if user_doc.exists:
                messagebox.showerror("Error", "Username already exists. Please choose a different username!")
                return
            
            # Save user credentials to Firestore
            db.collection("users").document(username).set({"password": password})
            messagebox.showinfo("Success", "Account created successfully! Redirecting to login page.")
            clear_screen()
            from gui.login import login_screen
            login_screen(root)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def back_to_login():
        """Redirect to the Login page."""
        clear_screen()
        from gui.login import login_screen
        login_screen(root)

    def clear_screen():
        """Clear all widgets from the current screen."""
        for widget in root.winfo_children():
            widget.destroy()

    # Initialize the main window if not provided
    if root is None:
        root = tk.Tk()
        root.title("Register - FileHaven")
        root.geometry("600x500")
        root.configure(bg="#E3F2FD")  # Light blue background color

        # Center the window
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = int((screen_width / 2) - (600 / 2))
        y = int((screen_height / 2) - (500 / 2))
        root.geometry(f"600x500+{x}+{y}")

    # Main Frame
    frame = tk.Frame(root, bg="#E3F2FD")
    frame.pack(expand=True, fill="both")

    # Add logo
    try:
        logo_image = PhotoImage(file="assets/logo.png")  # Path to your logo file
        logo_image = logo_image.subsample(3, 3)  # Resize the logo
        tk.Label(frame, image=logo_image, bg="#E3F2FD").pack(pady=10)
    except Exception as e:
        tk.Label(frame, text="FileHaven", font=("Helvetica", 24, "bold"), bg="#E3F2FD", fg="#1E88E5").pack(pady=10)

    # Header
    tk.Label(
        frame,
        text="Register",
        font=("Helvetica", 24, "bold"),
        bg="#E3F2FD",
        fg="#1E88E5",
    ).pack(pady=10)

    # Username Entry
    tk.Label(
        frame,
        text="Username:",
        font=("Helvetica", 12),
        bg="#E3F2FD",
    ).pack(pady=5)
    username_entry = tk.Entry(frame, font=("Helvetica", 12), width=30)
    username_entry.pack(pady=5)

    # Password Entry
    tk.Label(
        frame,
        text="Password:",
        font=("Helvetica", 12),
        bg="#E3F2FD",
    ).pack(pady=5)
    password_entry = tk.Entry(frame, font=("Helvetica", 12), width=30, show="*")
    password_entry.pack(pady=5)

    # Confirm Password Entry
    tk.Label(
        frame,
        text="Confirm Password:",
        font=("Helvetica", 12),
        bg="#E3F2FD",
    ).pack(pady=5)
    confirm_password_entry = tk.Entry(frame, font=("Helvetica", 12), width=30, show="*")
    confirm_password_entry.pack(pady=5)

    # Register Button
    tk.Button(
        frame,
        text="Register",
        command=register_user,
        bg="#1E88E5",
        fg="white",
        font=("Helvetica", 14),
        width=20,
        height=2,
        relief="flat",
    ).pack(pady=20)

    # Back to Login Link
    back_label = tk.Label(
        frame,
        text="Already a member? Login here",
        font=("Helvetica", 10),
        bg="#E3F2FD",
        fg="blue",
        cursor="hand2",
    )
    back_label.pack(pady=10)
    back_label.bind("<Button-1>", lambda e: back_to_login())

    # Footer
    tk.Label(frame, text="FileHaven @2025", font=("Helvetica", 10), bg="#E3F2FD", fg="#666").pack(pady=20)

    # Keep a reference to the logo image to prevent garbage collection
    frame.image = logo_image if 'logo_image' in locals() else None

    root.mainloop()

# For testing purposes
if __name__ == "__main__":
    register_screen()
