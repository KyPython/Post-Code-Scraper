# Postcode Scraper Demo

A web application that demonstrates scraping postal codes from Connecticut, USA and storing them in a Supabase database.

## Local Development

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Install Playwright browsers:
   ```
   playwright install chromium
   ```

3. Run the application:
   ```
   python app.py
   ```

4. Open http://localhost:8080 in your browser

## Deployment Options

### Deploy with Docker

1. Build the Docker image:
   ```
   docker build -t postcode-scraper .
   ```

2. Run the container:
   ```
   docker run -p 8080:8080 postcode-scraper
   ```

### Deploy to Render.com

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Use the following settings:
   - Build Command: `pip install -r requirements.txt && python -m playwright install chromium && python -m playwright install-deps chromium`
   - Start Command: `gunicorn app:app`
4. Add the following environment variables:
   - `SUPABASE_URL`: https://hhwhhfgeczrwsekzrsdw.supabase.co
   - `SUPABASE_KEY`: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhod2hoZmdlY3pyd3Nla3pyc2R3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzk5NzcyNjYsImV4cCI6MjA1NTU1MzI2Nn0.a0hu4XzA1v67h_A7sipLAP4QHc-7KmFfbeBPIaiGi50
   - `RENDER`: `true` (to indicate we're running on Render)

### Deploy to Heroku

1. Create a new Heroku app
2. Add the following buildpacks:
   - heroku/python
   - https://github.com/mxschmitt/heroku-playwright-buildpack.git
3. Deploy your code:
   ```
   git push heroku main
   ```

## Environment Variables

Make sure to set the following environment variables for your Supabase connection:
- SUPABASE_URL
- SUPABASE_KEY
