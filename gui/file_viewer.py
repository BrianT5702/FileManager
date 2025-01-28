import tkinter as tk
from tkinter import messagebox
import webbrowser
import tempfile
import os
import requests
from PIL import Image, ImageTk
import mimetypes

class FileViewer:
    def __init__(self, root, file_url, file_name):
        self.window = tk.Toplevel(root)
        self.window.title(f"Viewing: {file_name}")
        self.window.geometry("800x600")
        
        # Center the window
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = int((screen_width / 2) - (800 / 2))
        y = int((screen_height / 2) - (600 / 2))
        self.window.geometry(f"800x600+{x}+{y}")
        
        self.file_url = file_url
        self.file_name = file_name
        self.temp_dir = tempfile.gettempdir()
        
        # Initialize viewer
        self.init_viewer()
        
    def init_viewer(self):
        try:
            # Get file extension
            _, ext = os.path.splitext(self.file_name)
            ext = ext.lower()
            
            # Download the file
            response = requests.get(self.file_url)
            if response.status_code != 200:
                raise Exception("Failed to download file")
            
            # Save to temp file
            temp_path = os.path.join(self.temp_dir, self.file_name)
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            # Handle different file types
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                self.show_image(temp_path)
            elif ext in ['.txt', '.py', '.java', '.html', '.css', '.js', '.json', '.xml', '.csv']:
                self.show_text(temp_path)
            elif ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
                # For these types, open in default system application
                webbrowser.open(self.file_url)
                self.window.destroy()
            else:
                # For unknown types, offer download
                self.offer_download(temp_path)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")
            self.window.destroy()
            
    def show_image(self, file_path):
        try:
            # Create a frame for the image
            frame = tk.Frame(self.window)
            frame.pack(expand=True, fill='both')
            
            # Load and display the image
            image = Image.open(file_path)
            
            # Calculate scaling to fit window while maintaining aspect ratio
            display_width = 780  # Leaving some padding
            display_height = 580
            
            # Calculate scaling factor
            width_ratio = display_width / image.width
            height_ratio = display_height / image.height
            scale = min(width_ratio, height_ratio)
            
            # Resize image
            new_width = int(image.width * scale)
            new_height = int(image.height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(image)
            
            # Create canvas for image
            canvas = tk.Canvas(frame, width=display_width, height=display_height)
            canvas.pack(expand=True)
            
            # Center image on canvas
            x = (display_width - new_width) // 2
            y = (display_height - new_height) // 2
            
            # Display image
            canvas.create_image(x, y, anchor='nw', image=photo)
            canvas.image = photo  # Keep a reference
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display image: {str(e)}")
            self.window.destroy()
            
    def show_text(self, file_path):
        try:
            # Create text widget
            text_widget = tk.Text(self.window, wrap=tk.WORD, padx=10, pady=10)
            text_widget.pack(expand=True, fill='both')
            
            # Add scrollbar
            scrollbar = tk.Scrollbar(text_widget)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            text_widget.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=text_widget.yview)
            
            # Read and display the content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                text_widget.insert(tk.END, content)
                
            # Make it read-only
            text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display text: {str(e)}")
            self.window.destroy()
            
    def offer_download(self, file_path):
        # Create centered message
        message = tk.Label(
            self.window,
            text="This file type cannot be previewed.\nWould you like to download it?",
            font=("Helvetica", 12),
            pady=20
        )
        message.pack()
        
        # Create button frame
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=20)
        
        # Add buttons
        tk.Button(
            button_frame,
            text="Download",
            command=lambda: self.download_file(file_path),
            bg="#1E88E5",
            fg="white",
            font=("Helvetica", 10),
            padx=20,
            pady=10
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            button_frame,
            text="Cancel",
            command=self.window.destroy,
            bg="#666666",
            fg="white",
            font=("Helvetica", 10),
            padx=20,
            pady=10
        ).pack(side=tk.LEFT, padx=10)
        
    def download_file(self, source_path):
        try:
            # Ask user for save location
            file_types = [('All Files', '*.*')]
            save_path = filedialog.asksaveasfilename(
                defaultextension="*.*",
                filetypes=file_types,
                initialfile=self.file_name
            )
            
            if save_path:
                # Copy file to selected location
                with open(source_path, 'rb') as src, open(save_path, 'wb') as dst:
                    dst.write(src.read())
                messagebox.showinfo("Success", "File downloaded successfully!")
                self.window.destroy()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to download file: {str(e)}")