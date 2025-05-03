from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import threading
import time
import io
import uuid
from email.mime.text import MIMEText
import smtplib

# Import the actual scraper
from scraper.geonames_scraper import scrape_geonames_postcodes

app = Flask(__name__)

# Initialize the jobs dictionary
jobs = {}

# Define states for the dropdown
STATES = ["Connecticut", "New York", "California", "Texas", "Florida"]

@app.route('/')
def index():
    return render_template('index.html', states=STATES)

@app.route('/scrape', methods=['POST'])
def scrape_postcodes_route():
    state = request.form.get('state')
    city = request.form.get('city') or None  # Get city, default to None if empty

    if not state:
        return jsonify({"status": "error", "message": "State is required"}), 400
    
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    
    # Initialize job data
    jobs[job_id] = {
        "status": "pending",
        "state": state,
        "city": city,
        "results": [],
        "preview": [],
        "results_count": 0,
        "message": None
    }

    # Start the scraper in a background thread
    thread = threading.Thread(target=run_scraper_thread, args=(job_id, state, city))
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started", "job_id": job_id})

def run_scraper_thread(job_id, state, city):
    """Runs the scraper and updates the job dictionary."""
    try:
        jobs[job_id]["status"] = "running"
        print(f"Starting scraper for Job ID: {job_id}, State: {state}, City: {city}")
        
        # Call the actual scraper function
        results_list = scrape_geonames_postcodes(state, city_filter=city)
        
        # Format the results for our application
        formatted_results = []
        for item in results_list:
            formatted_results.append({
                "code": item.get("code", ""),
                "place_name": item.get("place_name", "")
            })
        
        # Update the job with results
        jobs[job_id]["results"] = formatted_results
        jobs[job_id]["results_count"] = len(formatted_results)
        jobs[job_id]["preview"] = formatted_results[:5]  # Get first 5 for preview
        jobs[job_id]["status"] = "completed"
        print(f"Job {job_id} completed. Found {len(formatted_results)} postcodes.")

    except Exception as e:
        print(f"Job {job_id} failed: {e}")
        import traceback
        traceback.print_exc()
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = str(e)

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

@app.route('/download/<job_id>')
def download_results(job_id):
    job = jobs.get(job_id)
    if not job or job['status'] != 'completed':
        return "Job not found or not completed", 404
    
    # Create a DataFrame from the results
    df = pd.DataFrame(job['results'])
    
    # Create a string buffer
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    
    # Create a bytes buffer for the response
    bytes_buffer = io.BytesIO()
    bytes_buffer.write(buffer.getvalue().encode('utf-8'))
    bytes_buffer.seek(0)
    
    # Generate filename
    state = job['state'].lower().replace(' ', '_')
    filename = f"postcodes_{state}.csv"
    
    return send_file(
        bytes_buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@app.route('/request-info', methods=['POST'])
def request_info():
    # Email Configuration
    sender_email = "your_app_email@example.com"
    sender_password = "your_app_password"
    receiver_email = "kyjahntsmith@gmail.com"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    # Get form data if available
    name = request.form.get('name', 'Anonymous')
    email = request.form.get('email', 'No email provided')
    message = request.form.get('message', 'No message provided')

    # Create email content
    subject = "Website Inquiry: Postcode Scraper Info Request"
    body = f"""
    Someone requested more information about the Postcode Scraper:
    
    Name: {name}
    Email: {email}
    Message: {message}
    
    This request was sent from your Postcode Scraper website.
    """

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    try:
        import smtplib
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("Info request email sent successfully.")
        return jsonify({"status": "success", "message": "Request sent"})
    except Exception as e:
        print(f"Failed to send email: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Failed to send request"}), 500

if __name__ == '__main__':
    app.run(debug=True)
