FROM python:3.9-slim

# Install OS-level dependencies (ffmpeg, etc.)
RUN apt-get update && apt-get install -y ffmpeg gcc

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Create folders
RUN mkdir -p uploads thumbnails

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Start FastAPI server (used only for API container)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
