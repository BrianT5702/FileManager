import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from firebase_admin import storage as admin_storage
from datetime import datetime, timedelta  # Add timedelta to the import
import os
from tkinter import ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
from firebase_config import db
from .file_viewer import FileViewer 
import threading
import queue

class ProgressDialog:
    def __init__(self, parent, title="Progress", message="Please wait..."):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        window_width = 300
        window_height = 150
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Configure grid
        self.dialog.grid_columnconfigure(0, weight=1)
        
        # Message label
        self.message_label = tk.Label(self.dialog, text=message, wraplength=250)
        self.message_label.grid(row=0, column=0, padx=20, pady=10)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.dialog,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=250
        )
        self.progress_bar.grid(row=1, column=0, padx=20, pady=10)
        
        # Status label
        self.status_label = tk.Label(self.dialog, text="Starting...")
        self.status_label.grid(row=2, column=0, padx=20, pady=10)
        
        # Message queue for thread communication
        self.queue = queue.Queue()
        self.check_queue()
        
    def check_queue(self):
        """Check for messages from the worker thread"""
        try:
            msg = self.queue.get_nowait()
            if isinstance(msg, tuple):
                msg_type, value = msg
                if msg_type == "progress":
                    self.progress_var.set(value)
                elif msg_type == "status":
                    self.status_label.config(text=value)
                elif msg_type == "message":
                    self.message_label.config(text=value)
            self.dialog.after(100, self.check_queue)
        except queue.Empty:
            self.dialog.after(100, self.check_queue)
            
    def update(self, progress=None, status=None, message=None):
        """Update progress dialog"""
        if progress is not None:
            self.queue.put(("progress", progress))
        if status is not None:
            self.queue.put(("status", status))
        if message is not None:
            self.queue.put(("message", message))
            
    def close(self):
        """Close the dialog"""
        self.dialog.grab_release()
        self.dialog.destroy()
        
class MainDashboard:
    def __init__(self, container, username):
        self.container = container
        self.username = username
        self.drag_data = {"widget": None, "type": None, "name": None, "x": 0, "y": 0}
        self.current_path = []
        self.root = container
        self.click_data = {
            "time": 0,
            "position": None,
            "widget": None,
            "timer": None
        }
        self.selected_item = None  # Track selected item by name and type
        self.initialize_ui()
        self.update_clock()

    def initialize_ui(self):
        # Main container configuration
        self.container.configure(bg="#E3F2FD")
        
        # Configure grid weights for full space utilization
        self.container.grid_rowconfigure(2, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Header Section
        header = tk.Frame(self.container, bg="#1E88E5", height=60)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        
        # Welcome Label
        welcome_label = tk.Label(
            header,
            text=f"Welcome, {self.username}!",
            font=("Helvetica", 16),
            bg="#1E88E5",
            fg="white",
        )
        welcome_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        # Time Label
        self.time_label = tk.Label(
            header,
            font=("Helvetica", 12),
            bg="#1E88E5",
            fg="white"
        )
        self.time_label.grid(row=0, column=1, padx=20, pady=10, sticky="e")

        # Navigation Bar
        nav_frame = tk.Frame(self.container, bg="#BBDEFB")
        nav_frame.grid(row=1, column=0, sticky="ew", pady=5)
        nav_frame.grid_columnconfigure(2, weight=1)
        
        # Back button
        self.back_button = tk.Button(
            nav_frame,
            text="← Back",
            command=self.go_back,
            bg="#1E88E5",
            fg="white",
            state="disabled"
        )
        self.back_button.grid(row=0, column=0, padx=5)
        
        # Path display
        self.path_label = tk.Label(
            nav_frame,
            text="Home",
            font=("Helvetica", 10),
            bg="#BBDEFB"
        )
        self.path_label.grid(row=0, column=1, padx=10, sticky="w")
        
        # Action buttons
        actions_frame = tk.Frame(nav_frame, bg="#BBDEFB")
        actions_frame.grid(row=0, column=2, sticky="e")

        buttons = [
            ("New Folder", self.create_folder, "#4CAF50"),
            ("Upload Files", self.upload_files, "#2196F3"),
            ("Sync to Storage", self.sync_to_storage, "#673AB7"),
            ("Logout", self.logout, "#D32F2F")
        ]
        
        for i, (text, command, color) in enumerate(buttons):
            tk.Button(
                actions_frame,
                text=text,
                command=command,
                bg=color,
                fg="white",
                font=("Helvetica", 10),
                relief="flat"
            ).grid(row=0, column=i, padx=5)

        # Content Area
        self.content_frame = tk.Frame(self.container)
        self.content_frame.grid(row=2, column=0, sticky="nsew")
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self.content_frame, bg="#E3F2FD")
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#E3F2FD")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Create window in canvas
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Configure grid
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Bind canvas resizing
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        
        # Set up drag and drop for the scrollable frame instead of canvas
        self.scrollable_frame.drop_target_register(DND_FILES)
        self.scrollable_frame.dnd_bind('<<Drop>>', self.handle_drop)

        self.load_items()

    def handle_drop(self, event):
            """Handle file drop events"""
            files = event.data
            for file in files:
                self.upload_specific_file(file)
                
    def file_exists(self, filename):
        """Check if file exists in current location"""
        try:
            if self.current_path:
                current_folder = self.current_path[-1]
                file_ref = db.collection("folders").document(self.username).collection("user_folders").document(current_folder).collection("files").document(filename)
            else:
                file_ref = db.collection("files").document(self.username).collection("user_files").document(filename)
            
            return file_ref.get().exists
        except Exception:
            return False

    def upload_files(self):
        """Upload multiple files using file dialog"""
        file_paths = filedialog.askopenfilenames(
            title="Select files to upload",
            filetypes=[
                ("All Files", "*.*"),
                ("Text Files", "*.txt"),
                ("PDF Files", "*.pdf"),
                ("Image Files", "*.png *.jpg *.jpeg *.gif")
            ]
        )
        
        if not file_paths:
            return
            
        for file_path in file_paths:
            try:
                file_name = os.path.basename(file_path)
                new_name = self.check_duplicate_filename(file_name)
                
                if new_name != file_name:
                    if not messagebox.askyesno("File Exists", 
                        f"File '{file_name}' already exists. Save as '{new_name}'?"):
                        continue
                    file_name = new_name

                self.upload_specific_file(file_path, file_name)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to upload {file_name}: {e}")
                
    def upload_specific_file(self, file_path, file_name=None):
        """Upload a specific file with progress dialog"""
        try:
            if file_name is None:
                file_name = os.path.basename(file_path)
                
            # Create and show progress dialog
            progress = ProgressDialog(
                self.root,
                "Uploading File",
                f"Uploading {file_name}..."
            )
            
            def upload_task():
                try:
                    file_stats = os.stat(file_path)
                    bucket = admin_storage.bucket()
                    storage_path = f"users/{self.username}/files/{file_name}"
                    blob = bucket.blob(storage_path)
                    
                    # Custom upload with progress
                    progress.update(status="Reading file...")
                    with open(file_path, 'rb') as file_obj:
                        file_size = os.path.getsize(file_path)
                        chunk_size = 256 * 1024  # 256KB chunks
                        uploaded_bytes = 0
                        
                        while True:
                            chunk = file_obj.read(chunk_size)
                            if not chunk:
                                break
                                
                            # Upload chunk
                            blob.upload_from_string(
                                chunk,
                                if_generation_match=None,
                                content_type='application/octet-stream'
                            )
                            
                            uploaded_bytes += len(chunk)
                            progress_percent = (uploaded_bytes / file_size) * 100
                            
                            progress.update(
                                progress=progress_percent,
                                status=f"Uploaded {uploaded_bytes}/{file_size} bytes"
                            )
                    
                    progress.update(progress=100, status="Generating download URL...")
                    
                    # Generate signed URL
                    download_url = blob.generate_signed_url(
                        version="v4",
                        expiration=timedelta(days=7),
                        method="GET"
                    )
                    
                    # Update database
                    file_data = {
                        "name": file_name,
                        "original_path": file_path,
                        "storage_path": storage_path,
                        "download_url": download_url,
                        "size": file_stats.st_size,
                        "modified_time": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                        "uploaded_at": datetime.now().isoformat(),
                        "type": "file",
                        "synced": True
                    }
                    
                    if self.current_path:
                        current_folder = self.current_path[-1]
                        file_ref = db.collection("folders").document(self.username).collection("user_folders").document(current_folder).collection("files")
                    else:
                        file_ref = db.collection("files").document(self.username).collection("user_files")
                    
                    file_ref.document(file_name).set(file_data)
                    
                    # Close progress dialog and reload items
                    self.root.after(0, lambda: [
                        progress.close(),
                        messagebox.showinfo("Success", f"File '{file_name}' uploaded successfully!"),
                        self.load_items()
                    ])
                    
                except Exception as e:
                    self.root.after(0, lambda: [
                        progress.close(),
                        messagebox.showerror("Error", f"Failed to upload file: {str(e)}")
                    ])
            
            # Start upload in separate thread
            threading.Thread(target=upload_task, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start upload: {str(e)}")
                
    def check_duplicate_filename(self, filename):
        """Check if filename exists and return a unique name if it does"""
        base, ext = os.path.splitext(filename)
        counter = 1
        new_filename = filename
        
        while self.file_exists(new_filename):
            new_filename = f"{base}_{counter}{ext}"
            counter += 1
            
        return new_filename
    
    def file_exists(self, filename):
        """Check if file exists in current location"""
        try:
            if self.current_path:
                current_folder = self.current_path[-1]
                file_ref = db.collection("folders").document(self.username).collection("user_folders").document(current_folder).collection("files").document(filename)
            else:
                file_ref = db.collection("files").document(self.username).collection("user_files").document(filename)
            
            return file_ref.get().exists
        except Exception:
            return False
            
    def on_canvas_configure(self, event):
        """Handle canvas resize"""
        width = event.width
        self.canvas.itemconfig(self.canvas_frame, width=width)
        
    def update_clock(self):
        """Update the clock display only if widget still exists."""
        if hasattr(self, "time_label") and self.time_label.winfo_exists():
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.time_label.config(text=current_time)
            self.root.after(1000, self.update_clock)  # Update every second

    def create_draggable_item(self, name, item_type, row, col):
        """Create a draggable file or folder with improved selection and drag-drop feedback."""
        color = "#4CAF50" if item_type == "folder" else "#2196F3"
        icon = "📁" if item_type == "folder" else "📄"

        # Create main frame with full background
        frame = tk.Frame(self.scrollable_frame, bg="white", width=180, height=180)
        frame.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
        frame.grid_propagate(False)

        # Create a single content frame that fills the entire area
        content_frame = tk.Frame(frame, bg="white")
        content_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)

        # Center the icon and label vertically in the content frame
        label_icon = tk.Label(content_frame, text=icon, font=("Helvetica", 48), bg="white", fg=color)
        label_icon.pack(expand=True, pady=(20, 5))

        display_name = name if len(name) <= 20 else name[:17] + "..."
        label_name = tk.Label(content_frame, text=display_name, font=("Helvetica", 12), bg="white")
        label_name.pack(expand=True, pady=(0, 20))

        if len(name) > 20:
            self.create_tooltip(label_name, name)

        # Create context menu
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="Rename", command=lambda: self.rename_item(name, item_type))
        context_menu.add_command(label="Delete", command=lambda: self.delete_item(name, item_type))
        
        if item_type == "folder":
            context_menu.add_command(label="Open", command=lambda: self.open_folder(name))

        # Bind events to both frame and content_frame
        for widget in (frame, content_frame, label_icon, label_name):
            widget.bind("<ButtonPress-1>", 
                       lambda e, f=frame, n=name, t=item_type: self.handle_click(e, f, n, t))
            widget.bind("<B1-Motion>", lambda e, f=frame: self.handle_motion(e, f))
            widget.bind("<ButtonRelease-1>", 
                       lambda e, f=frame, n=name, t=item_type: self.handle_release(e, f, n, t))
            widget.bind("<Double-Button-1>", 
                       lambda e, f=frame, n=name, t=item_type: self.handle_double_click(e, f, n, t))
            widget.bind("<Button-3>", lambda e: self.show_context_menu(e, context_menu))
            
            if item_type == "folder":
                widget.bind("<Enter>", lambda e, f=frame: self.highlight_drop_target(e, f))
                widget.bind("<Leave>", lambda e, f=frame: self.unhighlight_drop_target(e, f))

        # If this item was previously selected, reselect it
        if (self.selected_item and 
            self.selected_item["name"] == name and 
            self.selected_item["type"] == item_type):
            self.select_item(None, frame, name, item_type)

        return frame

    def handle_click(self, event, widget, name, item_type):
        """Handle single click events with delay to differentiate from drag."""
        # Cancel any existing click timer
        if self.click_data["timer"]:
            self.root.after_cancel(self.click_data["timer"])
            self.click_data["timer"] = None

        # Store click data
        self.click_data.update({
            "time": event.time,
            "position": (event.x_root, event.y_root),
            "widget": widget,
            "name": name,
            "type": item_type
        })

        # Select the item with the updated signature
        self.select_item(event, widget, name, item_type)

        # Set timer for potential drag start
        self.click_data["timer"] = self.root.after(100, lambda: self.check_drag_start(event, widget, name, item_type))
        
    def handle_motion(self, event, widget):
        """Handle mouse motion events."""
        if self.drag_data["widget"]:
            # Already dragging
            self.do_drag(event, widget)
        elif self.click_data["position"]:
            # Check if movement is significant enough to start drag
            start_x, start_y = self.click_data["position"]
            if abs(event.x_root - start_x) > 5 or abs(event.y_root - start_y) > 5:
                # Cancel click timer if it exists
                if self.click_data["timer"]:
                    self.root.after_cancel(self.click_data["timer"])
                    self.click_data["timer"] = None
                # Start drag
                self.start_drag(event, self.click_data["widget"], 
                              self.click_data["name"], self.click_data["type"])

    def handle_release(self, event, widget, name, item_type):
        """Handle mouse release events."""
        # Cancel any pending click timer
        if self.click_data["timer"]:
            self.root.after_cancel(self.click_data["timer"])
            self.click_data["timer"] = None

        # If we were dragging, handle the drop
        if self.drag_data["widget"]:
            self.stop_drag(event, widget, name, item_type)
        
        # Reset click data
        self.click_data.update({
            "time": 0,
            "position": None,
            "widget": None,
            "name": None,
            "type": None
        })

    def handle_double_click(self, event, widget, name, item_type):
        """Handle double click events."""
        # Cancel any pending click timer
        if self.click_data["timer"]:
            self.root.after_cancel(self.click_data["timer"])
            self.click_data["timer"] = None

        # Handle double click based on item type
        if item_type == "folder":
            self.open_folder(name)
        else:
            self.view_file(name)

    def check_drag_start(self, event, widget, name, item_type):
        """Check if we should start a drag operation."""
        self.click_data["timer"] = None
        # If mouse hasn't moved significantly, this was just a click
        # No need to do anything as selection was already handled

    def select_item(self, event, widget, name, item_type):
        """Highlight the selected item and reset previous selection."""
        try:
            # Check if previous widget still exists and is valid
            if hasattr(self, 'selected_widget') and self.selected_widget:
                try:
                    # Verify widget still exists
                    self.selected_widget.winfo_exists()
                    # Only configure if widget still exists
                    self.selected_widget.configure(bg="white")
                    for child in self.selected_widget.winfo_children():
                        child.configure(bg="white")
                except tk.TclError:
                    # Widget no longer exists, just ignore and continue
                    pass

            # Highlight the current widget
            widget.configure(bg="#BBDEFB")  # Light blue for selection
            for child in widget.winfo_children():
                child.configure(bg="#BBDEFB")
            
            self.selected_widget = widget
            self.selected_item = {"name": name, "type": item_type}
        except Exception as e:
            print(f"Error in select_item: {str(e)}")
            # Reset selection state in case of error
            self.selected_widget = None
            self.selected_item = None
    
    def highlight_drop_target(self, event, widget):
        """Highlight a folder when the mouse enters its area during dragging."""
        if self.drag_data["widget"]:
            widget.configure(bg="#FFFACD")  # Light yellow for drop target
            for child in widget.winfo_children():
                child.configure(bg="#FFFACD")

    def unhighlight_drop_target(self, event, widget):
        """Remove highlight when the mouse leaves a folder."""
        if widget != getattr(self, 'selected_widget', None):
            widget.configure(bg="white")
            for child in widget.winfo_children():
                child.configure(bg="white")
    
    def view_file(self, file_name):
        """Open file viewer for the selected file."""
        try:
            # Get file data from Firestore
            if self.current_path:
                current_folder = self.current_path[-1]
                file_ref = db.collection("folders").document(self.username).collection("user_folders").document(current_folder).collection("files").document(file_name)
            else:
                file_ref = db.collection("files").document(self.username).collection("user_files").document(file_name)
            
            file_data = file_ref.get().to_dict()
            
            if not file_data or 'download_url' not in file_data:
                messagebox.showerror("Error", "File data or download URL not found!")
                return
                
            # Create file viewer
            FileViewer(self.root, file_data['download_url'], file_name)
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")
        
    def create_tooltip(self, widget, text):
        """Create tooltip for showing full name on hover"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            
            label = tk.Label(tooltip, text=text, background="#FFE", relief="solid", borderwidth=1)
            label.pack()
            
            def hide_tooltip():
                tooltip.destroy()
            
            widget.tooltip = tooltip
            widget.bind("<Leave>", lambda e: hide_tooltip())
            tooltip.bind("<Leave>", lambda e: hide_tooltip())

        widget.bind("<Enter>", show_tooltip)

    def start_drag(self, event, widget, name, item_type):
        """Start dragging with improved visibility."""
        if hasattr(self, 'drag_clone') and self.drag_clone:
            return

        self.drag_data.update({
            "widget": widget,
            "type": item_type,
            "name": name,
            "x": event.x,
            "y": event.y
        })
        
        # Create a visual drag feedback
        self.drag_clone = tk.Frame(self.scrollable_frame, bg="#E3F2FD", width=180, height=180)
        self.drag_clone.place(x=widget.winfo_x(), y=widget.winfo_y())
        
        # Copy the content to the clone
        clone_content = tk.Frame(self.drag_clone, bg="#E3F2FD")
        clone_content.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)
        
        icon = "📁" if item_type == "folder" else "📄"
        color = "#4CAF50" if item_type == "folder" else "#2196F3"
        
        tk.Label(clone_content, text=icon, font=("Helvetica", 48), bg="#E3F2FD", fg=color).pack(expand=True, pady=(20, 5))
        tk.Label(clone_content, text=name[:17] + "..." if len(name) > 20 else name, 
                font=("Helvetica", 12), bg="#E3F2FD").pack(expand=True, pady=(0, 20))

        # Make original semi-transparent
        widget.configure(bg="#E3F2FD")
        for child in widget.winfo_children():
            child.configure(bg="#E3F2FD")

    def do_drag(self, event, widget):
        """Handle dragging motion with improved visibility."""
        if hasattr(self, 'drag_clone') and self.drag_clone:
            # Update clone position
            x = event.x_root - self.drag_data["x"] - self.scrollable_frame.winfo_rootx()
            y = event.y_root - self.drag_data["y"] - self.scrollable_frame.winfo_rooty()
            self.drag_clone.place(x=x, y=y)

    def stop_drag(self, event, widget, name, item_type):
        """Handle dropping of files with cleanup."""
        if hasattr(self, 'drag_clone') and self.drag_clone:
            self.drag_clone.destroy()
            self.drag_clone = None
        
        widget.configure(bg="white")  # Reset original widget background

        # Handle drop logic
        target_folder = None
        for child in self.scrollable_frame.winfo_children():
            if child != widget and self.is_dropped_on_widget(event, child):
                try:
                    content_frame = child.winfo_children()[0]
                    labels = [w for w in content_frame.winfo_children() if isinstance(w, tk.Label)]
                    if len(labels) >= 2:
                        icon_label = labels[0]
                        if icon_label.cget("text") == "📁":
                            name_label = labels[1]
                            target_folder = name_label.cget("text")
                            break
                except Exception:
                    continue

        if target_folder and self.drag_data["type"] == "file":
            self.move_file(name, target_folder)

        self.drag_data = {"widget": None, "type": None, "name": None, "x": 0, "y": 0}

    def is_dropped_on_widget(self, event, target_widget):
        """Check if the dragged widget is dropped on a target widget."""
        target_x1 = target_widget.winfo_rootx()
        target_y1 = target_widget.winfo_rooty()
        target_x2 = target_x1 + target_widget.winfo_width()
        target_y2 = target_y1 + target_widget.winfo_height()

        # Check if the mouse pointer overlaps with the target widget
        return target_x1 <= event.x_root <= target_x2 and target_y1 <= event.y_root <= target_y2
    
    def load_items(self):
        """Load files and folders into the scrollable frame."""
        # Store currently selected item before clearing
        currently_selected = self.selected_item

        # Clear existing items
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        try:
            if self.current_path:
                current_folder = self.current_path[-1]
                folders_ref = db.collection("folders").document(self.username).collection("user_folders").document(current_folder).collection("subfolders")
                files_ref = db.collection("folders").document(self.username).collection("user_folders").document(current_folder).collection("files")
            else:
                folders_ref = db.collection("folders").document(self.username).collection("user_folders")
                files_ref = db.collection("files").document(self.username).collection("user_files")

            row, col = 0, 0
            max_cols = 4  # Number of items per row

            # Load folders
            for folder in folders_ref.stream():
                folder_name = folder.id
                self.create_draggable_item(folder_name, "folder", row, col)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

            # Load files
            for file in files_ref.stream():
                file_name = file.id
                self.create_draggable_item(file_name, "file", row, col)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

            # Configure grid columns to be equal width
            for i in range(max_cols):
                self.scrollable_frame.grid_columnconfigure(i, weight=1)

            # If the previously selected item no longer exists, clear selection
            if currently_selected:
                exists = False
                for widget in self.scrollable_frame.winfo_children():
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Label) and child.cget("text") == currently_selected["name"]:
                            exists = True
                            break
                if not exists:
                    self.selected_item = None
                    self.selected_widget = None

        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch items: {e}")

    def show_context_menu(self, event, menu):
        """Show context menu on right-click."""
        menu.post(event.x_root, event.y_root)

    def rename_item(self, name, item_type):
        """Rename a file or folder"""
        new_name = simpledialog.askstring("Rename", f"Enter new name for {name}:")
        if not new_name:
            return

        try:
            if item_type == "folder":
                collection_ref = db.collection("folders").document(self.username).collection("user_folders")
                # Rename folder
                old_doc = collection_ref.document(name).get()
                collection_ref.document(new_name).set(old_doc.to_dict() or {})
                collection_ref.document(name).delete()
            else:
                # Get file reference
                if self.current_path:
                    current_folder = self.current_path[-1]
                    file_ref = db.collection("folders").document(self.username).collection("user_folders").document(current_folder).collection("files")
                else:
                    file_ref = db.collection("files").document(self.username).collection("user_files")
                
                # Get old file data
                old_doc = file_ref.document(name).get()
                file_data = old_doc.to_dict()
                
                if file_data and 'storage_path' in file_data:
                    # Update storage path
                    old_storage_path = file_data['storage_path']
                    new_storage_path = f"users/{self.username}/files/{new_name}"
                    
                    # Get bucket and create blob references
                    bucket = admin_storage.bucket()
                    old_blob = bucket.blob(old_storage_path)
                    new_blob = bucket.blob(new_storage_path)
                    
                    # Copy the blob to the new location
                    bucket.copy_blob(old_blob, bucket, new_storage_path)
                    
                    # Generate new signed URL
                    new_url = new_blob.generate_signed_url(
                        version="v4",
                        expiration=timedelta(days=7),
                        method="GET"
                    )
                    
                    # Update file data
                    file_data['storage_path'] = new_storage_path
                    file_data['download_url'] = new_url
                    
                    # Delete old blob
                    old_blob.delete()
                
                # Update database
                file_data['name'] = new_name
                file_ref.document(new_name).set(file_data)
                file_ref.document(name).delete()

            messagebox.showinfo("Success", f"{item_type.capitalize()} renamed successfully!")
            self.load_items()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename {item_type}: {e}")

    def delete_item(self, name, item_type):
        """Delete item with progress dialog"""
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {name}?"):
            return
            
        try:
            progress = ProgressDialog(
                self.root,
                "Deleting Item",
                f"Deleting {item_type} {name}..."
            )
            
            def delete_task():
                try:
                    if item_type == "folder":
                        progress.update(progress=50, status="Deleting folder...")
                        collection_ref = db.collection("folders").document(self.username).collection("user_folders")
                        collection_ref.document(name).delete()
                    else:
                        # Delete file
                        progress.update(progress=25, status="Getting file data...")
                        
                        if self.current_path:
                            current_folder = self.current_path[-1]
                            file_ref = db.collection("folders").document(self.username).collection("user_folders").document(current_folder).collection("files").document(name)
                        else:
                            file_ref = db.collection("files").document(self.username).collection("user_files").document(name)
                        
                        file_data = file_ref.get().to_dict()
                        
                        if file_data and 'storage_path' in file_data:
                            progress.update(progress=50, status="Deleting from storage...")
                            try:
                                bucket = admin_storage.bucket()
                                blob = bucket.blob(file_data['storage_path'])
                                blob.delete()
                            except Exception:
                                pass
                        
                        progress.update(progress=75, status="Deleting file record...")
                        file_ref.delete()
                    
                    progress.update(progress=100, status="Delete complete!")
                    
                    # Close progress and update UI
                    self.root.after(0, lambda: [
                        progress.close(),
                        messagebox.showinfo("Success", f"{item_type.capitalize()} deleted successfully!"),
                        self.load_items()
                    ])
                    
                except Exception as e:
                    self.root.after(0, lambda: [
                        progress.close(),
                        messagebox.showerror("Error", f"Failed to delete {item_type}: {str(e)}"),
                        self.load_items()
                    ])
            
            # Start delete in separate thread
            threading.Thread(target=delete_task, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start delete: {str(e)}")

    def open_folder(self, folder_name):
        """Open a folder and update the current path."""
        self.current_path.append(folder_name)
        self.update_path_display()
        self.back_button.config(state="normal")
        self.load_items()

    def go_back(self):
        """Navigate to the previous folder."""
        if self.current_path:
            self.current_path.pop()
            self.update_path_display()
            if not self.current_path:
                self.back_button.config(state="disabled")
            self.load_items()

    def update_path_display(self):
        """Update the path display in the navigation bar."""
        path_text = "Home" if not self.current_path else " > ".join(["Home"] + self.current_path)
        self.path_label.config(text=path_text)

    def move_file(self, file_name, target_folder):
        """Move a file with progress dialog"""
        try:
            progress = ProgressDialog(
                self.root,
                "Moving File",
                f"Moving {file_name} to {target_folder}..."
            )
            
            def move_task():
                try:
                    # Update progress
                    progress.update(progress=25, status="Getting source file...")
                    
                    # Get source reference
                    if self.current_path:
                        current_folder = self.current_path[-1]
                        source_ref = db.collection("folders").document(self.username).collection("user_folders").document(current_folder).collection("files").document(file_name)
                    else:
                        source_ref = db.collection("files").document(self.username).collection("user_files").document(file_name)
                    
                    progress.update(progress=50, status="Checking target location...")
                    
                    # Get source data
                    source_doc = source_ref.get()
                    if not source_doc.exists:
                        raise Exception(f"File '{file_name}' does not exist!")

                    file_data = source_doc.to_dict()
                    
                    # Update metadata
                    file_data.update({
                        "moved_at": datetime.now().isoformat(),
                        "parent_folder": target_folder,
                        "path": self.current_path + [target_folder] if self.current_path else [target_folder]
                    })
                    
                    progress.update(progress=75, status="Moving file...")
                    
                    # Get target reference and check existence
                    target_ref = db.collection("folders").document(self.username).collection("user_folders").document(target_folder).collection("files").document(file_name)
                    
                    if target_ref.get().exists:
                        raise Exception("A file with the same name already exists in the target folder!")
                    
                    # Perform move
                    target_ref.set(file_data)
                    source_ref.delete()
                    
                    progress.update(progress=100, status="Move complete!")
                    
                    # Close progress and update UI
                    self.root.after(0, lambda: [
                        progress.close(),
                        messagebox.showinfo("Success", f"Moved '{file_name}' to folder '{target_folder}'!"),
                        self.load_items()
                    ])
                    
                except Exception as e:
                    self.root.after(0, lambda: [
                        progress.close(),
                        messagebox.showerror("Error", f"Failed to move file: {str(e)}"),
                        self.load_items()
                    ])
            
            # Start move in separate thread
            threading.Thread(target=move_task, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start move: {str(e)}")

    def create_folder(self):
        """Create a new folder."""
        folder_name = simpledialog.askstring("Folder Name", "Enter folder name:")
        if not folder_name:
            return
        try:
            # Prevent duplicate folder names
            if self.current_path:
                current_folder = self.current_path[-1]
                folder_ref = db.collection("folders").document(self.username).collection("user_folders").document(current_folder).collection("subfolders")
            else:
                folder_ref = db.collection("folders").document(self.username).collection("user_folders")
            
            # Check if folder already exists
            if folder_ref.document(folder_name).get().exists:
                messagebox.showerror("Error", f"Folder '{folder_name}' already exists!")
                return

            # Save the folder in Firebase
            folder_ref.document(folder_name).set({"created_at": datetime.now().isoformat()})
            messagebox.showinfo("Success", f"Folder '{folder_name}' created successfully!")
            self.load_items()  # Reload the dashboard to show the new folder
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create folder: {e}")
            
    def sync_to_storage(self):
        """Sync files to Firebase Storage"""
        try:
            # Get bucket
            bucket = admin_storage.bucket()
            
            # Get all files in current location
            if self.current_path:
                current_folder = self.current_path[-1]
                files_ref = db.collection("folders").document(self.username).collection("user_folders").document(current_folder).collection("files")
            else:
                files_ref = db.collection("files").document(self.username).collection("user_files")
            
            files = files_ref.get()
            
            for file in files:
                file_data = file.to_dict()
                if not file_data.get('synced'):
                    original_path = file_data.get('original_path')
                    if original_path and os.path.exists(original_path):
                        try:
                            storage_path = f"users/{self.username}/files/{file_data['name']}"
                            blob = bucket.blob(storage_path)
                            
                            # Upload the file
                            with open(original_path, 'rb') as file_obj:
                                blob.upload_from_file(file_obj)
                            
                            # Get download URL
                            download_url = blob.generate_signed_url(
                                version="v4",
                                expiration=datetime.timedelta(days=7),
                                method="GET"
                            )
                            
                            # Update file data with storage info
                            file_data['synced'] = True
                            file_data['storage_path'] = storage_path
                            file_data['download_url'] = download_url
                            files_ref.document(file.id).set(file_data)
                            
                        except Exception as e:
                            print(f"Failed to upload {file_data['name']}: {e}")
                            continue
            
            messagebox.showinfo("Success", "Files synced to Firebase Storage successfully!")
            self.load_items()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to sync to storage: {str(e)}")

    def logout(self):
        """Log out and return to welcome screen with fresh image loading."""
        from gui.welcome import welcome_screen

        # Stop update_clock from running after logout
        try:
            self.root.after_cancel(self.update_clock)
        except Exception:
            pass

        # Destroy all widgets in the current root
        for widget in self.root.winfo_children():
            widget.destroy()

        # Force garbage collection to ensure Tkinter reloads the image properly
        import gc
        gc.collect()

        # Reload welcome screen
        welcome_screen(self.root)
        
def main_dashboard(root, username):
    """
    Initialize the main dashboard using the existing window.
    
    Args:
        root: The existing Tkinter root window
        username: The logged in user's username
    """
    # Convert existing root to TkinterDnD if it isn't already
    if not isinstance(root, TkinterDnD.Tk):
        # Destroy old root
        root.destroy()
        
        # Create new TkinterDnD root
        root = TkinterDnD.Tk()
        
        # Set window title
        root.title("FileHaven - Dashboard")
        
        # Get screen dimensions
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # Calculate window size (80% of screen size)
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        
        # Calculate position
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Set window geometry
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Make window resizable
        root.resizable(True, True)
        
        # Set minimum size
        root.minsize(800, 600)
        
        # Lift window to top but don't maximize
        root.lift()
        root.focus_force()
    
    app = MainDashboard(root, username)
    root.mainloop()

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    main_dashboard(root, "admin123")