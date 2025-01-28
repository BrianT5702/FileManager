import tkinter as tk
from tkinter import PhotoImage, messagebox
from firebase_config import db

def login_screen(root):
    """Display the login screen."""

    def login_user():
        """Authenticate the user and switch to the main dashboard using the same window."""
        username = username_entry.get().strip()
        password = password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "All fields are required!")
            return

        try:
            # Retrieve user data from Firestore
            user_doc = db.collection("users").document(username).get()
            if not user_doc.exists:
                messagebox.showerror("Error", "User does not exist. Please register first!")
                return

            # Check if the password matches
            stored_password = user_doc.to_dict().get("password")
            if stored_password != password:
                messagebox.showerror("Error", "Invalid password. Please try again!")
                return

            # Login successful
            messagebox.showinfo("Success", "Login successful! Redirecting to dashboard.")

            # Switch to main dashboard using the same window
            from gui.main_dashboard import main_dashboard
            main_dashboard(root, username)

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def forgot_password():
        """Redirect to the password reset page."""
        clear_screen()
        from gui.reset_password import reset_password_screen
        reset_password_screen(root)

    def go_to_register():
        """Redirect to the Register page."""
        clear_screen()
        from gui.register import register_screen
        register_screen(root)

    def clear_screen():
        """Clear all widgets from the current screen."""
        for widget in root.winfo_children():
            widget.destroy()

    # Initialize the main window if not provided
    if root is None:
        root = tk.Tk()
        root.title("Login - FileHaven")
        root.geometry("600x500")
        root.configure(bg="#E3F2FD")

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
        text="Login",
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

    # Login Button
    tk.Button(
        frame,
        text="Login",
        command=login_user,
        bg="#1E88E5",
        fg="white",
        font=("Helvetica", 14),
        width=20,
        height=2,
        relief="flat",
    ).pack(pady=20)

    # Forgot Password Link
    forgot_label = tk.Label(
        frame,
        text="Forgot Password?",
        font=("Helvetica", 10),
        bg="#E3F2FD",
        fg="blue",
        cursor="hand2",
    )
    forgot_label.pack()
    forgot_label.bind("<Button-1>", lambda e: forgot_password())

    # Register Link
    register_label = tk.Label(
        frame,
        text="Not a member? Register here!",
        font=("Helvetica", 10),
        bg="#E3F2FD",
        fg="blue",
        cursor="hand2",
    )
    register_label.pack(pady=5)
    register_label.bind("<Button-1>", lambda e: go_to_register())

    # Footer
    tk.Label(frame, text="FileHaven @2025", font=("Helvetica", 10), bg="#E3F2FD", fg="#666").pack(pady=20)

    # Keep a reference to the logo image to prevent garbage collection
    frame.image = logo_image if 'logo_image' in locals() else None

    root.mainloop()

# For testing purposes
if __name__ == "__main__":
    login_screen()
