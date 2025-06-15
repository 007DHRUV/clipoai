# 🎬 ClipoAI Assignment – Video Processing API with FastAPI, Celery, MongoDB, Cloudinary & Docker

This project is a robust, scalable video processing API built using **FastAPI**, **Celery**, **MongoDB**, **Redis**, **Cloudinary**, and **Docker**. It allows users to:

- Upload videos
- Generate thumbnails
- Extract duration using FFmpeg
- Store video metadata in MongoDB
- Upload videos & thumbnails to Cloudinary
- Check status or retrieve processed metadata

---

## 📁 Folder Structure

clipoai-assignment/
│
├── app/
│ └── main.py # FastAPI app and Celery logic
├── Dockerfile # FastAPI container config
├── celery_worker/
│ └── worker.py # Celery entrypoint
├── docker-compose.yml # Multi-container setup
├── .env # Your environment secrets (ignored by Git)
├── .gitignore
├── Makefile # Dev/Build automation commands
└── README.md # You're reading this!

yaml
Copy code

---

## 🚀 Features

- ✅ Video upload via API
- ✅ Background processing with Celery (FFmpeg, Cloudinary uploads)
- ✅ Video duration and thumbnail generation
- ✅ MongoDB storage for metadata
- ✅ Static file hosting for thumbnails
- ✅ Full Docker support for one-command startup

---

## ⚙️ Technologies Used

- **FastAPI** - Web framework
- **Celery** - Background task manager
- **Redis** - Celery broker
- **MongoDB** - Data persistence
- **Cloudinary** - Video & image CDN
- **FFmpeg** - Media probing and processing
- **Docker** - Containerized deployment

---

## 🌐 API Endpoints

| Method | Endpoint                        | Description                      |
|--------|----------------------------------|----------------------------------|
| POST   | `/upload-video/`                | Upload video                     |
| GET    | `/video-status/{video_id}`      | Check processing status          |
| GET    | `/video-metadata/{video_id}`    | Get full metadata (duration, URLs) |

---

## 📦 Setup (Local or Production)

### 1. 🔐 Create `.env` file

Although i have pushed it with my credentials intact just in case otherwise 
you can get your own with ease by a simple sign up on cloudinary

env
Copy code
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

MONGO_URI=mongodb://mongo:27017
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
2. 🐳 Run using Docker
bash
Copy code
docker-compose up --build
FastAPI will be available at: http://localhost:8000

Static thumbnails: http://localhost:8000/thumbnails/

Celery worker runs in background

🧪 Test the API
📤 Upload Video (via curl)
bash
Copy code
curl -X POST "http://localhost:8000/upload-video/"your video path"
 
🔄 Check Status
bash
Copy code
curl http://localhost:8000/video-status/{video_id}
📄 Get Metadata
bash
Copy code
curl http://localhost:8000/video-metadata/{video_id}
🛠️ Development Tools
Run Linting, Build, Format, etc.
Use the Makefile commands:
Command	Description
make help	Displays a help message listing all available commands.
make up	Builds and starts all containers (FastAPI, Celery, Redis, MongoDB) in detached mode.
make down	Stops and removes all containers.
make shell	Opens a shell session inside the FastAPI container.
make rebuild	Stops, rebuilds, and restarts all containers.
make clean	Removes files in uploads/, thumbnails/, __pycache__, and .pytest_cache.
make clean-all	Stops containers and performs a full project cleanup.
bash
Copy code

✅ To Do
 Upload to Cloudinary

 Celery async processing


🙌 Contributing
Pull requests are welcome! Feel free to fork the repo and submit PRs.

🧠 Author
Made with ❤️ by Dhruv

📜 License
This project is licensed under the MIT License. See LICENSE file for details.
