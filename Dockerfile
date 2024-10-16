# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required by OpenCV, psycopg2, and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container at /app
COPY . .

# Expose the port that Gunicorn will run on (default is 8000)
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Download the checkpoint files
# RUN mkdir -p /app/api/checkpoints && \
#     curl -L -o /app/api/checkpoints/best_1600_box_100.pt https://github.com/Orbin-Ahmed/Keystone--Backend/releases/download/test/best_1600_box_100.pt && \
#     curl -L -o /app/api/checkpoints/best_wall_7k_100.pt https://github.com/Orbin-Ahmed/Keystone--Backend/releases/download/test/best_wall_7k_100.pt

# Collect static files, apply migrations, and start Gunicorn
CMD ["sh", "-c", "python manage.py collectstatic --noinput && \
                   python manage.py migrate --noinput && \
                   python download_checkpoints.py && \
                   gunicorn core.wsgi:application --bind 0.0.0.0:8000"]
