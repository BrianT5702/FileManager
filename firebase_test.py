from firebase_config import db, bucket

def test_firestore():
    """Test Firestore connectivity."""
    try:
        doc_ref = db.collection("test").document("example")
        doc_ref.set({"message": "Hello, Firebase!"})
        print("Firestore Test: Data written successfully!")
    except Exception as e:
        print(f"Firestore Test: Failed with error: {e}")

def test_storage():
    """Test Firebase Storage connectivity."""
    try:
        blob = bucket.blob("test/example.txt")
        blob.upload_from_string("This is a test file for Firebase Storage.")
        print("Storage Test: File uploaded successfully!")
    except Exception as e:
        print(f"Storage Test: Failed with error: {e}")

if __name__ == "__main__":
    test_firestore()
    test_storage()
