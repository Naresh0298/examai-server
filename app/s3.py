from fastapi import FastAPI,File, UploadFile, HTTPException
import boto3
from dotenv import load_dotenv
import os
from botocore.exceptions import NoCredentialsError
import uuid
from datetime import datetime

load_dotenv()

app = FastAPI()
AWS_ACCESS_KEY_ID="AKIA43HML5NC346FBAHN"
AWS_SECRET_ACCESS_KEY="SjP9I2qyzhZjDP9KcJbmyt8kys7ReM1qGk5f2c6R"
AWS_REGION_NAME="eu-north-1" # e.g., us-east-1
S3_BUCKET_NAME="myexamaibucket"

# Create S3 client
try:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION_NAME
    )
    print("✅ Connected to AWS S3 successfully!")
except NoCredentialsError:
    print("❌ AWS credentials not found!")
    raise Exception("Please set your AWS credentials in .env file")

@app.get("/")
async def root():
    return {"message": "S3 API is ready!", "bucket": S3_BUCKET_NAME}

@app.get("/health")
async def health_check():
    """Check if we can connect to S3"""
    try:
        # Try to access our bucket
        s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
        return {"status": "healthy", "s3_connection": "OK"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
    
@app.post("/upload")
async def upload_file(file: UploadFile=File(...)):
    """Upload a single file s3"""

    file_content = await file.read()
    print(f"received file:{file.filename}, Size:{len(file_content)} bytes")

    # Step 2: Generate unique filename to avoid conflicts
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    print(f"🏷️ Generated unique name: {unique_filename}")

# Step 3: Upload to S3
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,           # Which bucket to upload to
            Key=unique_filename,             # What to name the file in S3
            Body=file_content,               # The actual file data
            ContentType=file.content_type    # MIME type (image/jpeg, text/pdf, etc.)
        )
        print(f"✅ File uploaded successfully to S3")
        
        # Step 4: Generate public URL for the file
        file_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION_NAME}.amazonaws.com/{unique_filename}"
        
        # Step 5: Return success response
        return {
            "success": True,
            "message": "File uploaded successfully",
            "filename": unique_filename,
            "original_filename": file.filename,
            "url": file_url,
            "size": len(file_content),
            "uploaded_at": datetime.utcnow().isoformat()
        }
            
    except Exception as e:
        print(f"❌ Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
