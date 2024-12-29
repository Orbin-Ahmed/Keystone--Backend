# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# Add memory limiting environment variables
ENV MALLOC_ARENA_MAX=2
ENV PYTHONMALLOC=malloc
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata
ENV LC_ALL=C

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required by OpenCV, psycopg2, and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libpq-dev \
    build-essential \
    python3-dev \
    curl \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*


RUN mkdir -p /usr/share/tesseract-ocr/4.00/tessdata && \
    curl -L -o /usr/share/tesseract-ocr/4.00/tessdata/eng.traineddata \
    https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies with pip optimization flags
RUN pip install --no-cache-dir -r requirements.txt \
    && pip cache purge

# Create directory for checkpoints
RUN mkdir -p /app/api/checkpoints

# Download checkpoint files more efficiently
RUN cd /app/api/checkpoints && \
    curl -L -o best_1600_box_100.pt https://github.com/Orbin-Ahmed/Keystone--Backend/releases/download/test/best_1600_box_100.pt && \
# curl -L -o best_27k_50.pt https://github.com/Orbin-Ahmed/Keystone--Backend/releases/download/test/best_27k_50.pt
# Copy the rest of your application code
COPY . .

# Expose the port that Gunicorn will run on
EXPOSE 8000

# Start command with optimized Gunicorn settings
CMD ["sh", "-c", "\
    python manage.py collectstatic --noinput && \
    python manage.py migrate --noinput && \
    gunicorn core.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 2 \
    --worker-class=gthread \
    --worker-tmp-dir=/dev/shm \
    --max-requests 1000 \
    --max-requests-jitter 50"]