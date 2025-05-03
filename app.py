from flask import Flask, render_template, request, jsonify, send_file  # Ensure Flask is installed: pip install flask
import pandas as pd  # Ensure pandas is installed: pip install pandas
import threading
import time
import io

app = Flask(__name__)

# Mock data for demonstration
MOCK_DATA = {
    "Connecticut": [
MOCK_DATA = {
    "Connecticut": [
        {"id": 1, "code": "06001", "place_name": "Avon", "region_id": 1},
        {"id": 2, "code": "06002", "place_name": "Bloomfield", "region_id": 1}
    ],
    "New York": []
}
scraping_jobs = {}

# Removed duplicate import of jsonify
from email.mime.text import MIMEText
scraping_jobs = {}

from email.mime.text import MIMEText

# --- Modify your existing /scrape route ---
@app.route('/scrape', methods=['POST'])
def scrape_postcodes_route():
    state = request.form.get('state')
    city = request.form.get('city') or None # Get city, default to None if empty

    if not state:
        return jsonify({"status": "error", "message": "State is required"}), 400
    import uuid  # Add this import at the top of the file
        job_id = str(uuid.uuid4())
    # Generate a unique job ID
    job_id = str(uuid.uuid4()) # Requires 'import uuid'
    if not state:
        return jsonify({"status": "error", "message": "State is required"}), 400
    import uuid  # Add this import at the top of the file
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
        "city": city,
        "results": [],
        "preview": [],
        "results_count": 0,
        "message": None
    }

    # --- Start the scraper in a background thread ---
    # Pass the job_id so the thread can update the status
    thread = threading.Thread(target=run_scraper_thread, args=(job_id, state, city))
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started", "job_id": job_id})

# --- New function to run scraper in thread and update status ---
def run_scraper_thread(job_id, state, city):
    """Runs the scraper and updates the job dictionary."""
    try:
        jobs[job_id]["status"] = "running"
        # Modify your scraper function to return results or update the job dict directly
        # For this example, assume scrape_geonames_postcodes is modified
        # to accept the job_id and update jobs[job_id]
        # OR it returns the results list.

        # --- Placeholder for calling your actual scraper ---
        # This needs modification in geonames_scraper.py or here
        # to store results correctly.
        print(f"Starting scraper for Job ID: {job_id}, State: {state}, City: {city}")
        # Let's assume scrape_geonames_postcodes now updates the global 'jobs' dict
        # You'll need to pass 'jobs' and 'job_id' to it, or refactor.
        # A simpler way for now: have it return results
        results_list = scrape_geonames_postcodes_modified(state, city) # Assume this returns a list of dicts

        jobs[job_id]["results"] = results_list
        jobs[job_id]["results_count"] = len(results_list)
        jobs[job_id]["preview"] = results_list[:5] # Get first 5 for preview
        jobs[job_id]["status"] = "completed"
        print(f"Job {job_id} completed. Found {len(results_list)} postcodes.")

    except Exception as e:
        print(f"Job {job_id} failed: {e}")
        import traceback
        traceback.print_exc()
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = str(e)

# --- You'll need to adapt your actual scraper function ---
# Example modification (needs to be integrated into your actual scraper file)
def scrape_geonames_postcodes_modified(state_name: str, city_filter: str = None):
    # ... (Your existing scraper setup code: playwright, browser, context) ...
    scraped_data = []
        if 'postal_table' in locals() and postal_table:  # Ensure postal_table is defined before accessing it
        # ... (Your existing URL fetching, table finding logic) ...

            rows = postal_table.find_all("tr")[1:] if postal_table else []  # Ensure postal_table is defined
            # ... (Get country_id, region_id logic) ...

            rows = postal_table.find_all("tr")[1:]
            success_count = 0
            error_count = 0 # Keep track locally if needed, but main goal is return list

            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 3:
                    place_name = cols[1].text.strip()
                    postcode = cols[2].text.strip()

                    if city_filter and city_filter.lower() not in place_name.lower():
                        continue

                    if place_name and postcode:
                        data_dict = {
                            "code": postcode,
                            "place_name": place_name,
                            # "region_id": region_id # Maybe not needed for return list
                        }
                        # --- Instead of inserting here, add to list ---
                        scraped_data.append(data_dict)
                        # --- Optionally, insert to DB here as well ---
                        # if insert_postcode_data({...}): success_count += 1 else: error_count += 1
                # else: print(...)
            # print summary if needed
        # else: print("Table not found")

    except Exception as e:
        print(f"Scraper error: {e}")
        if browser:  # Ensure browser is defined before accessing it
            if 'browser' in locals():  # Ensure browser is defined before closing it
                if browser:
    finally:
        if browser:
        if browser:
            browser.close()

    return scraped_data # Return the list of dictionaries


# --- New route to check job status ---
@app.route('/job/<job_id>', methods=['GET'])
def get_job_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"status": "error", "message": "Job not found"}), 404

    # Return status and preview data if completed
    response_data = {"status": job["status"]}
    if job["status"] == "completed":
        response_data["preview"] = job["preview"]
        response_data["results_count"] = job["results_count"]
    elif job["status"] == "failed":
        response_data["message"] = job["message"]

    return jsonify(response_data)

# --- New route to handle information requests ---
@app.route('/request-info', methods=['POST'])
def request_info():
    # --- Email Configuration (Use environment variables or config file in production!) ---
    sender_email = "your_app_email@example.com" # An email address you control
    sender_password = "your_app_password"      # App password if using Gmail, etc.
    receiver_email = "kyjahntsmith@gmail.com"
    smtp_server = "smtp.gmail.com" # Or your provider's SMTP server
    smtp_port = 587 # Or 465 for SSL

    subject = "Website Inquiry: Postcode Scraper Info Request"
    body = "Someone requested more information about the Postcode Scraper from your website."

    message = MIMEText(body)
    message['Subject'] = subject
    message['From'] = sender_email
    message['To'] = receiver_email

    try:
        import smtplib
        with smtplib.SMTP(smtp_server, smtp_port) as server:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls() # Secure the connection
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("Info request email sent successfully.")
        return jsonify({"status": "success", "message": "Request sent"})
    except Exception as e:
        print(f"Failed to send email: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Failed to send request"}), 500

# --- Optional: Route to download full results ---
# This requires storing the full results somewhere accessible
# @app.route('/download/<job_id>')
# def download_results(job_id):
#     job = jobs.get(job_id)
#     if not job or job['status'] != 'completed':
#         return "Job not found or not completed", 404
#     # Logic to create and return a CSV file from job['results']
#     # ... (using StringIO and Flask's send_file) ...
#     pass

}

@app.route('/')
def index():
    return render_template('index.html', states=list(MOCK_DATA.keys()))

@app.route('/scrape', methods=['POST'])
def scrape():
    state = request.form.get('state', 'Connecticut')
    city = request.form.get('city', '')
    
    # Generate a job ID
    job_id = f"{int(time.time())}"
    
    # Start scraping in background
    thread = threading.Thread(
        target=run_scraper, 
        args=(job_id, state, city)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'status': 'started',
        'job_id': job_id,
        'message': f'Started scraping postcodes for {state}'
    })

def run_scraper(job_id, state, city):
    try:
        # Simulate scraping
        time.sleep(2)
        
        # Get mock data
        results = MOCK_DATA.get(state, [])
        
        # Filter by city if provided
        if city:
            results = [r for r in results if city.lower() in r['place_name'].lower()]
        
        # Store results
        scraping_jobs[job_id] = {
            'state': state,
            'city': city,
            'status': 'completed',
            'results': results
        }
    except Exception as e:
        scraping_jobs[job_id] = {
            'state': state,
            'city': city,
            'status': 'error',
            'error': str(e)
        }

@app.route('/job/<job_id>')
def job_status(job_id):
    if job_id not in scraping_jobs:
        return jsonify({'status': 'not_found'})
    
    return jsonify(scraping_jobs[job_id])

@app.route('/download/<job_id>')
def download_csv(job_id):
    if job_id not in scraping_jobs or scraping_jobs[job_id]['status'] != 'completed':
        return "Job not found or not completed", 404
    
    # Create CSV
    results = scraping_jobs[job_id]['results']
    df = pd.DataFrame(results)
    
    # Create in-memory file
    output = io.StringIO()
    df.to_csv(output, index=False)
    
    # Create response
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    
    state = scraping_jobs[job_id]['state'].lower().replace(' ', '_')
    return send_file(
        mem, 
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'postcodes_{state}.csv'
    )

if __name__ == '__main__':
    app.run(debug=True)