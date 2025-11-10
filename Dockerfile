FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev \
        libffi-dev \
        libpq-dev \
        gcc \
        && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Download NLTK data (stopwords required by illumenti_search.py)
RUN python -c "import nltk; nltk.download('stopwords', download_dir='/usr/local/nltk_data')"

# Copy project files
COPY . .

# Set environment variable for Flask
ENV FLASK_APP=web/main.py

# Expose port
EXPOSE 5001

# Run the application
CMD ["gunicorn", "--workers=3", "--bind=0.0.0.0:5001", "web.main:app"]
