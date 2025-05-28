from fastapi import FastAPI, File, UploadFile, HTTPException
# Import the CORS middleware
from fastapi.middleware.cors import CORSMiddleware
import os

from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from typing import List
from pydantic import BaseModel
from datetime import datetime
import uuid # For generating unique IDs for metadata records
from pydantic import BaseModel, Field
from typing import List, Optional

from pathlib import Path
import aiofiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_db_client(app)
    yield
    await shutdown_db_client(app)


async def startup_db_client(app):
    app.mongodb_client = AsyncIOMotorClient("mongodb+srv://nareshmahendhar22878:xnXi6hZOMDbZFWJ9@examai-mdb.8i9lty0.mongodb.net/")
    app.mongodb = app.mongodb_client.get_database("examai_file")
    print('MongoDB connected')

async def shutdown_db_client(app):
    app.mongodb_client.close()
    print("Database disconnected.")

# Initiate fast api app
app = FastAPI(lifespan=lifespan)

# --- CORS Configuration START ---
# Define the list of origins that should be allowed to make cross-origin requests.
# You should be specific in production, but for development, localhost:3000 is key.
origins = [
    "http://localhost:3000", # Your frontend origin
    # You might want to add other origins if needed, e.g.:
    "http://127.0.0.1:3000",
    # "https://examai-frontend.vercel.app/",
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

UPLOAD_DIRECTORY = Path("uploads_docs")

# if not os.path.exists(UPLOAD_DIRECTORY):
#     os.makedirs(UPLOAD_DIRECTORY)

UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

@app.get('/')
def read_root():
    return {'message' : 'Examai Server running'}


@app.post("/upload_file")

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



# C <=== Create
# @app.post("/api/v1/create-user", response_model=User)
# async def insert_user(user: User):
#     result = await app.mongodb["users"].insert_one(user.dict())
#     inserted_user = await app.mongodb["users"].find_one({"_id": result.inserted_id})
#     return inserted_user
# Add this block if you want to run the script directly using `python your_script_name.py`
# You'll need uvicorn installed: pip install uvicorn
# if __name__ == "__main__":
#    uvicorn.run(app, host="127.0.0.1", port=8000)


class FileMetadataDB(BaseModel):
    metadata_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_filename:str
    unique_filename:str
    content_type: Optional[str] =None
    file_extension: str
    size_bytes: int
    server_file_path: str
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)

    class config:
        from_attributes = True
        populate_by_name = True


# --- Your Modified Upload Endpoint ---
@app.post("/upload_docs_with_metadata") # Changed endpoint name for clarity
async def upload_doc_with_metadata(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="Please provide files to upload.")

    saved_file_info = [] # To store dicts of {unique_filename, metadata_id}

    for file in files:
        file_ext = os.path.splitext(file.filename)[1].lower()
        is_file_type_allowed = file.content_type in ALLOWED_FILE_TYPES
        is_extension_allowed = file_ext in ALLOWED_EXTENSIONS

        if not (is_file_type_allowed or is_extension_allowed):
            await file.close()
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed for '{file.filename}'. "
                       f"Detected MIME type: '{file.content_type}', Extension: '{file_ext}'. "
                       f"Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}."
            )

        base_filename = os.path.basename(file.filename)
        name, ext = os.path.splitext(base_filename)
        unique_filename_on_server = f"{name}_{os.urandom(8).hex()}{ext}"
        file_path_on_server = UPLOAD_DIRECTORY / unique_filename_on_server # Use pathlib for paths

        file_size = 0 # Initialize file size

        try:
            # Save the file content asynchronously using aiofiles
            async with aiofiles.open(file_path_on_server, "wb") as buffer:
                while content := await file.read(1024 * 1024): # Read in 1MB chunks
                    await buffer.write(content)
            
            # Get file size after saving
            # For aiofiles, you might need to use aiofiles.os.stat
            # Or, if file.size is available and reliable from UploadFile (depends on client and FastAPI version, often it is the total size)
            # For a definitive size after writing:
            stat_result = os.stat(file_path_on_server)
            file_size = stat_result.st_size
            
            # --- MongoDB Metadata Storage ---
            metadata_to_store = FileMetadataDB(
                original_filename=file.filename,
                unique_filename=unique_filename_on_server,
                content_type=file.content_type,
                file_extension=file_ext,
                size_bytes=file_size,
                server_file_path=str(file_path_on_server.resolve()) # Store absolute path or relative as needed
            )
            
            # For Pydantic V2 use .model_dump(), for V1 use .dict()
            metadata_dict = metadata_to_store.model_dump() if hasattr(metadata_to_store, 'model_dump') else metadata_to_store.dict()

            # Ensure app.mongodb is your initialized AsyncIOMotorDatabase instance
            result = await app.mongodb["uploaded_files_metadata"].insert_one(metadata_dict) # Using a new collection name
            
            print(f"File '{file.filename}' saved as '{unique_filename_on_server}', metadata stored with ID: {result.inserted_id}")
            
            saved_file_info.append({
                "original_filename": file.filename,
                "saved_as": unique_filename_on_server,
                "metadata_id_in_db": str(result.inserted_id), # Or metadata_to_store.metadata_id if you use that
                "size": file_size
            })

        except Exception as e:
            # Basic cleanup: if file exists and an error occurred, try to remove it.
            if os.path.exists(file_path_on_server):
                 try:
                     os.remove(file_path_on_server)
                     print(f"Cleaned up partially saved file: {unique_filename_on_server}")
                 except OSError as oe:
                     print(f"Error cleaning up file {unique_filename_on_server}: {oe}")
            
            print(f"Error processing file '{file.filename}': {e}")
            # It's tricky to decide if we should continue with other files or stop.
            # For now, we stop and raise an error for the problematic file.
            # The client would then know which files succeeded based on previous uploads in a batch.
            raise HTTPException(status_code=500, detail=f"Could not process file '{file.filename}'. Error: {str(e)}")
        finally:
            await file.close()

    return {
        "message": f"{len(saved_file_info)} file(s) processed and metadata stored.",
        "files_details": saved_file_info
    }