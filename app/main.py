import os
import uuid
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from celery import Celery
import ffmpeg
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# I’m loading environment variables from a `.env` file for things like Cloudinary and Mongo credentials.
load_dotenv()

# Here, I configure Cloudinary using the credentials I loaded above.
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Setting up the FastAPI app and exposing the local thumbnails folder as a static route.
app = FastAPI()
app.mount("/thumbnails", StaticFiles(directory="thumbnails"), name="thumbnails")

# Here I initialize Celery with Redis as both the broker and result backend.
celery_app = Celery(
    "tasks",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)
celery_app.conf.update(task_track_started=True)

# I make sure the upload and thumbnail directories exist to avoid any file write errors.
UPLOAD_DIR = "uploads"
THUMBNAIL_DIR = "thumbnails"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

# This Pydantic model helps serialize video metadata when returned in responses.
class VideoMetadata(BaseModel):
    filename: str
    upload_time: str
    status: str
    duration: str = None
    thumbnail_url: str = None
    cloud_url: str = None
    class config:
        extra = "allow"

# This is the API endpoint to upload videos. I do basic validation and save the file locally.
@app.post("/upload-video/")
async def upload_video(file: UploadFile = File(...)):
    mongo_client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    db = mongo_client["clipo"]
    videos_collection = db["videos"]
    try:
        if not file.filename.lower().endswith(('.mp4', '.avi', '.mov')):
            raise HTTPException(status_code=400, detail="Invalid video file format")
        
        # I generate a unique ID for each uploaded video.
        video_id = str(uuid.uuid4())
        temp_path = os.path.join(UPLOAD_DIR, f"{video_id}_{file.filename}")
        
        # I save the uploaded video to disk temporarily.
        with open(temp_path, "wb") as f:
            f.write(await file.read())
        
        # I log initial metadata to MongoDB with status "pending".
        upload_time = datetime.utcnow().isoformat()
        video_metadata = {
            "_id": video_id,
            "filename": file.filename,
            "upload_time": upload_time,
            "status": "pending"
        }
        videos_collection.insert_one(video_metadata)

        # I trigger a background Celery task to process the video.
        process_video.delay(video_id, temp_path, file.filename)
        
        return {"video_id": video_id, "status": "pending"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    finally:
        mongo_client.close()

# This endpoint lets clients poll the processing status of a video by ID.
@app.get("/video-status/{video_id}")
async def get_video_status(video_id: str):
    mongo_client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    db = mongo_client["clipo"]
    try:
        video = db["videos"].find_one({"_id": video_id})
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        return {"video_id": video_id, "status": video["status"]}
    finally:
        mongo_client.close()

# This one returns the full metadata of a video, including duration, cloud URLs, etc.
@app.get("/video-metadata/{video_id}")
async def get_video_metadata(video_id: str):
    mongo_client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    db = mongo_client["clipo"]
    try:
        video = db["videos"].find_one({"_id": video_id})
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        return VideoMetadata(**video)
    finally:
        mongo_client.close()

# This is the background Celery task that does the heavy lifting: duration, thumbnail, uploads.
@celery_app.task
def process_video(video_id: str, file_path: str, filename: str):
    mongo_client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    db = mongo_client["clipo"]
    videos_collection = db["videos"]
    try:
        # First, I try to extract the duration of the video using ffmpeg.
        try:
            probe = ffmpeg.probe(file_path)
            duration = float(probe['format']['duration'])
        except ffmpeg.Error as e:
            error_message = e.stderr.decode('utf-8') if e.stderr else str(e)
            videos_collection.update_one(
                {"_id": video_id},
                {"$set": {"status": "failed", "error": f"FFmpeg probe failed: {error_message}"}}
            )
            raise Exception(f"FFmpeg probe failed: {error_message}")
        
        duration_str = f"{int(duration // 60):02d}:{int(duration % 60):02d}"

        # Then I try to generate a thumbnail at 10% into the video.
        thumbnail_time = duration * 0.1
        thumbnail_path = os.path.join(THUMBNAIL_DIR, f"{video_id}.jpg")
        try:
            stream = ffmpeg.input(file_path, ss=thumbnail_time)
            stream = ffmpeg.output(stream, thumbnail_path, vframes=1, format='image2', vcodec='mjpeg')
            ffmpeg.run(stream)
        except ffmpeg.Error as e:
            error_message = e.stderr.decode('utf-8') if e.stderr else str(e)
            videos_collection.update_one(
                {"_id": video_id},
                {"$set": {"status": "failed", "error": f"FFmpeg thumbnail failed: {error_message}"}}
            )
            raise Exception(f"Thumbnail generation failed: {error_message}")

        # I upload the video file to Cloudinary using chunked upload since it can be large.
        try:
            result_video = cloudinary.uploader.upload_large(
                file_path,
                resource_type="video",
                public_id=f"clipo/videos/{video_id}",
                chunk_size=6000000
            )
            cloud_video_url = result_video["secure_url"]
        except Exception as e:
            videos_collection.update_one(
                {"_id": video_id},
                {"$set": {"status": "failed", "error": f"Cloudinary video upload failed: {str(e)}"}}
            )
            raise

        # I also upload the thumbnail to Cloudinary.
        try:
            result_thumb = cloudinary.uploader.upload(
                thumbnail_path,
                resource_type="image",
                public_id=f"clipo/thumbnails/{video_id}"
            )
            cloud_thumbnail_url = result_thumb["secure_url"]
        except Exception as e:
            videos_collection.update_one(
                {"_id": video_id},
                {"$set": {"status": "failed", "error": f"Cloudinary thumbnail upload failed: {str(e)}"}}
            )
            raise

        # Finally, I update the MongoDB record with the video duration and cloud URLs.
        videos_collection.update_one(
            {"_id": video_id},
            {"$set": {
                "duration": duration_str,
                "thumbnail_url": cloud_thumbnail_url,
                "cloud_url": cloud_video_url,
                "status": "done"
            }}
        )
    finally:
        mongo_client.close()
        # I’ve commented out this line so I can inspect the uploaded file later if needed.
        # os.remove(file_path)
