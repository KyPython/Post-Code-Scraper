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
