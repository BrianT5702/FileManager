import firebase_admin
from firebase_admin import credentials, firestore, storage

# Path to your Firebase Admin SDK JSON file
CREDENTIALS_PATH = "data/firebase_credentials.json"

# Initialize Firebase
cred = credentials.Certificate(CREDENTIALS_PATH)
firebase_admin.initialize_app(cred, {"storageBucket": "filemanagement-68e13.firebasestorage.app"})  # Replace with your Firebase project ID

# Firestore client for database operations
db = firestore.client()

# Firebase Storage client for file operations
bucket = storage.bucket()
