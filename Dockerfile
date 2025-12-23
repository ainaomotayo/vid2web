# Use a more recent, stable Python base image
FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PLAYWRIGHT_BROWSERS_PATH /ms-playwright/

# Switch to root user to install system dependencies
USER root

# Install system dependencies for Playwright and OpenCV
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    # Playwright dependencies
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    libatk1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    libpangocairo-1.0-0 \
    libwebp-dev \
    libjpeg-dev \
    libtiff-dev \
    libglib2.0-0 \
    # OpenCV dependencies
    ffmpeg \
    libsm6 \
    libxext6 \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy pyproject.toml and install Python dependencies
# Using pip directly with requirements.txt is often more straightforward in Docker
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium \
    && playwright install-deps chromium

# Copy the rest of the application code
COPY . .

# Expose the port Cloud Run provides, defaulting to 8080 for documentation
EXPOSE 8080

# Command to run the Streamlit application, respecting the PORT environment variable
# The ${PORT:-8501} syntax uses the PORT variable if it's set, otherwise defaults to 8501.
CMD ["sh", "-c", "streamlit run src/video_to_website/ui/streamlit_app.py --server.port=${PORT:-8501} --server.address=0.0.0.0"]
