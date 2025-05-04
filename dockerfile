# /Users/ky/Desktop/GitHub/VS Code/cloud-postcode-scraper/Post-Code-Scraper/Dockerfile

# Use the official Playwright Python image (choose a specific version if needed)
# Check https://mcr.microsoft.com/en-us/product/playwright/python/about for available tags
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Set the working directory inside the container
WORKDIR /app

# Copy requirements file first to leverage Docker build cache
COPY requirements.txt .

# Install Python dependencies from requirements.txt
# Install Playwright browsers system-wide within the container image
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps

# Copy the rest of your application code into the container's working directory
COPY . .

# Command to run the application using Gunicorn
# Render automatically sets the PORT environment variable.
# Gunicorn will listen on 0.0.0.0 and the port specified by $PORT.
# Adjust workers/threads/timeout based on your Render plan and needs.
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:${PORT}", "--workers", "1", "--threads", "2", "--timeout", "120"]