from fastapi import FastAPI, File, UploadFile, HTTPException
# Import the CORS middleware
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import List
import uvicorn # Often used to run FastAPI apps

# Initiate fast api app
app = FastAPI()

# --- CORS Configuration START ---
# Define the list of origins that should be allowed to make cross-origin requests.
# You should be specific in production, but for development, localhost:3000 is key.
origins = [
    "http://localhost:3000", # Your frontend origin
    # You might want to add other origins if needed, e.g.:
    # "http://127.0.0.1:3000",
    # "http://localhost", # If frontend runs without port sometimes
    # "https://your-production-frontend.com" # For production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of origins that are allowed to make requests
    allow_credentials=True, # Allow cookies to be included in requests
    allow_methods=["*"],    # Allow all standard methods (GET, POST, PUT, etc.)
    allow_headers=["*"],    # Allow all headers
)
# --- CORS Configuration END ---


ALLOWED_FILE_TYPES = {
    # PDF
    "application/pdf",
    # Word
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    # Text
    "text/plain",
    # Images
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/bmp",
    "image/webp",
    # PowerPoint
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}

ALLOWED_EXTENSIONS = {
    # PDF
    ".pdf",
    # Word
    ".doc",
    ".docx",
    # Text
    ".txt",
    # Images
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
    # PowerPoint
    ".ppt",
    ".pptx",
}

UPLOAD_DIRECTORY = "uploads_docs"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)


@app.post("/upload_docs")
async def upload_doc(files: List[UploadFile]= File(...)):
    """
    Upload one or more allowed files (PDF, Word, Text, Image, PowerPoint) to the server.

    Args:
        files: A list of files uploaded via the endpoint.

    Raises:
        HTTPException: If no files are provided, a file type is not allowed,
                       or an error occurs during saving.

    Returns:
        A dictionary containing a success message and a list of saved filenames.
    """

    if not files:
        # Consider making this detail message more generic as you allow many types
        raise HTTPException(status_code=400, detail="Please provide files to upload.") # Changed "PDF files" to "files"

    saved_filenames = []

    for file in files:
        file_ext = os.path.splitext(file.filename)[1].lower()

        is_file_type_allowed = file.content_type in ALLOWED_FILE_TYPES
        is_extension_allowed = file_ext in ALLOWED_EXTENSIONS


        if not (is_file_type_allowed or is_extension_allowed):
            await file.close()
            # Raise error for disallowed file type
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed for '{file.filename}'. "
                       f"Detected MIME type: '{file.content_type}', Extension: '{file_ext}'. "
                       f"Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}. "
                       # f"Allowed MIME types: {', '.join(ALLOWED_FILE_TYPES)}." # Corrected variable name
            )


        base_filename = os.path.basename(file.filename)
        name, ext = os.path.splitext(base_filename)
        unique_filename = f"{name}_{os.urandom(8).hex()}{ext}"
        # Construct the full path to save the file
        file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)

        try:
            # Save the file content asynchronously using chunks
            with open(file_path, "wb") as buffer:
                while content := await file.read(1024 * 1024): # Read in 1MB chunks
                    buffer.write(content)
            saved_filenames.append(unique_filename) # Add the unique name to our list
            print(f"File '{file.filename}' saved successfully as '{unique_filename}'") # Server-side log
        except Exception as e:
            # Handle potential file saving errors
            print(f"Error saving file '{file.filename}': {e}")
            # Clean up already processed file handle before raising
            # Note: file.close() is already called in finally block
            raise HTTPException(status_code=500, detail=f"Could not save file '{file.filename}'. Error: {str(e)}")
        finally:
            # Ensure the file is closed even if errors occurred during saving
            await file.close()

    # Return success message and the list of saved unique filenames
    return {"message": f"{len(saved_filenames)} file(s) uploaded successfully.", "saved_filenames": saved_filenames}

# Add this block if you want to run the script directly using `python your_script_name.py`
# You'll need uvicorn installed: pip install uvicorn
# if __name__ == "__main__":
#    uvicorn.run(app, host="127.0.0.1", port=8000)