# Use Python 3.11 for stability
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the entire project (respecting .dockerignore)
COPY . .

# Set environment variables for memory optimization
ENV PYTHONPATH=/app
ENV PORT=8000
ENV MALLOC_ARENA_MAX=2
ENV WEB_CONCURRENCY=1
ENV TRANSFORMERS_CACHE=/app/model_cache

# Expose port
EXPOSE 8000

# Start the application pointing to the main file in the backend folder
CMD ["python", "backend/main.py"]
