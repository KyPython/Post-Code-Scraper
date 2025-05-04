from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import threading
import time
import io
import uuid
from email.mime.text import MIMEText
import smtplib
import os
import json
import logging
import traceback
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the actual scraper
from scraper.geonames_scraper import scrape_geonames_postcodes
# Import Supabase utilities
from supabase_utils.db_client import get_all_postcodes, supabase

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the jobs dictionary (temporary in-memory storage)
# This will be replaced with Supabase storage
jobs = {}

# Function to create jobs table in Supabase if it doesn't exist
def ensure_jobs_table_exists():
    try:
        # Check if jobs table exists by attempting to query it
        response = supabase.table("jobs").select("id").limit(1).execute()
        logger.info("Jobs table exists in Supabase")
        return True
    except Exception as e:
        if "relation" in str(e) and "does not exist" in str(e):
            logger.info("Creating jobs table in Supabase")
            try:
                # Create the jobs table
                # Note: This is a simplified approach - in production you might want to use migrations
                sql = """
                CREATE TABLE IF NOT EXISTS jobs (
                    id UUID PRIMARY KEY,
                    status VARCHAR(50) NOT NULL,
                    state VARCHAR(100) NOT NULL,
                    city VARCHAR(100),
                    results JSONB,
                    preview JSONB,
                    results_count INTEGER DEFAULT 0,
                    message TEXT,
                    db_entries INTEGER DEFAULT 0,
                    error_details TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """
                # Assuming you have an rpc function 'exec_sql' set up in Supabase
                # If not, you'll need to handle table creation differently (e.g., manually or via migrations)
                # supabase.rpc("exec_sql", {"query": sql}).execute()
                logger.warning("Automatic table creation via RPC is commented out. Ensure 'jobs' table exists.")
                # logger.info("Jobs table created successfully")
                return True # Assume success if RPC is commented out, needs manual creation
            except Exception as create_error:
                logger.error(f"Failed to create jobs table: {create_error}")
                return False
        else:
            logger.error(f"Error checking jobs table: {e}")
            return False

# Define all US states for the dropdown
STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", 
    "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", 
    "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", 
    "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", 
    "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", 
    "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", 
    "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"
]

# Run setup tasks at import time instead of using before_first_request
def setup_app():
    """Initialize application components"""
    try:
        # Ensure the jobs table exists
        ensure_jobs_table_exists()
    except Exception as e:
        logger.error(f"Error during app initialization: {e}", exc_info=True)

# Run setup at import time
setup_app()

# Function to save job to Supabase
def save_job_to_supabase(job_id, job_data):
    try:
        # Convert job data to a format suitable for Supabase
        supabase_job = {
            "id": job_id,
            "status": job_data.get("status", "unknown"),
            "state": job_data.get("state", ""),
            "city": job_data.get("city", None),
            "results": json.dumps(job_data.get("results", [])),
            "preview": json.dumps(job_data.get("preview", [])),
            "results_count": job_data.get("results_count", 0),
            "message": job_data.get("message", None),
            "db_entries": job_data.get("db_entries", 0),
            "error_details": job_data.get("error_details", None),
            "updated_at": datetime.now().isoformat()
        }
        
        # Try to create the table if it doesn't exist
        try:
            ensure_jobs_table_exists()
        except Exception as table_error:
            logger.error(f"Error ensuring jobs table exists: {table_error}")
            # Continue anyway - we'll try the operation
        
        # Check if job already exists
        try:
            response = supabase.table("jobs").select("id").eq("id", job_id).execute()
            
            if response.data:
                # Update existing job
                supabase.table("jobs").update(supabase_job).eq("id", job_id).execute()
                logger.info(f"Updated job {job_id} in Supabase")
            else:
                # Insert new job
                supabase_job["created_at"] = datetime.now().isoformat()
                supabase.table("jobs").insert(supabase_job).execute()
                logger.info(f"Inserted job {job_id} into Supabase")
            
            return True
        except Exception as e:
            logger.error(f"Failed to save job to Supabase: {e}")
            # If we get here, we'll fall back to in-memory storage only
            return False
    except Exception as e:
        logger.error(f"Failed to prepare job data for Supabase: {e}")
        return False

# Function to get job from Supabase
def get_job_from_supabase(job_id):
    try:
        response = supabase.table("jobs").select("*").eq("id", job_id).execute()
        
        if not response.data:
            return None
        
        job_data = response.data[0]
        
        # Convert JSON strings back to Python objects
        if isinstance(job_data.get("results"), str):
            job_data["results"] = json.loads(job_data.get("results", "[]"))
        
        if isinstance(job_data.get("preview"), str):
            job_data["preview"] = json.loads(job_data.get("preview", "[]"))
        
        return job_data
    except Exception as e:
        logger.error(f"Failed to get job from Supabase: {e}")
        return None

def get_available_states():
    """Returns the list of states for the dropdown."""
    return STATES # Return the hardcoded list for now

@app.route('/')
def index():
    # Get database stats to display on the homepage
    db_stats = get_database_stats()
    return render_template('index.html', states=get_available_states(), db_stats=db_stats)

def get_database_stats():
    """Get statistics about the Supabase database for display"""
    try:
        # Get total count of postcodes
        postcodes = get_all_postcodes()
        total_postcodes = len(postcodes)
        
        # Get recent entries (last 5)
        recent_postcodes = postcodes[-5:] if total_postcodes > 0 else []
        
        # Format recent entries for display
        recent_entries = []
        for postcode in recent_postcodes:
            recent_entries.append({
                "Post-Code": postcode.get("code", ""),
                "City/Town": postcode.get("place_name", "")
            })
        
        # Get count by region if available
        region_counts = {}
        try:
            response = supabase.table("regions").select("id,name").execute()
            regions = {r['id']: r['name'] for r in response.data}
            
            for region_id, region_name in regions.items():
                count_response = supabase.table("postcodes").select("id").eq("region_id", region_id).execute()
                region_counts[region_name] = len(count_response.data)
        except Exception as e:
            print(f"Error getting region counts: {e}")
        
        return {
            "total_postcodes": total_postcodes,
            "recent_entries": recent_entries,
            "region_counts": region_counts
        }
    except Exception as e:
        print(f"Error getting database stats: {e}")
        return {
            "total_postcodes": 0,
            "recent_entries": [],
            "region_counts": {},
            "error": str(e)
        }

@app.route('/scrape', methods=['POST'])
def scrape_postcodes_route():
    state = request.form.get('state')
    city = request.form.get('city') or None  # Get city, default to None if empty

    if not state:
        return jsonify({"status": "error", "message": "State is required"}), 400
    
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    
    # Initialize job data
    job_data = {
        "status": "pending",
        "state": state,
        "city": city,
        "results": [],
        "preview": [],
        "results_count": 0,
        "message": None,
        "db_entries": 0  # Track how many entries were added to the database
    }
    
    # Store in memory temporarily
    jobs[job_id] = job_data
    
    # Save to Supabase
    save_job_to_supabase(job_id, job_data)

    # Start the scraper in a background thread
    thread = threading.Thread(target=run_scraper_thread, args=(job_id, state, city))
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started", "job_id": job_id})

def run_scraper_thread(job_id, state, city):
    """Runs the scraper and updates the job dictionary."""
    try:
        # Update job status to running
        jobs[job_id]["status"] = "running"
        save_job_to_supabase(job_id, jobs[job_id])
        
        logger.info(f"Starting scraper for Job ID: {job_id}, State: {state}, City: {city}")
        
        # Call the actual scraper function
        results_list = scrape_geonames_postcodes(state, city_filter=city)
        
        # Check if results_list is None or empty and provide detailed logging
        if results_list is None:
            logger.warning(f"Scraper returned None for state: {state}, city: {city}")
            results_list = []
        elif len(results_list) == 0:
            logger.warning(f"Scraper returned empty list for state: {state}, city: {city}")
        else:
            logger.info(f"Scraper returned {len(results_list)} results for state: {state}, city: {city}")
        
        # Format the results for our application with renamed fields
        formatted_results = []
        for item in results_list:
            formatted_result = {
                "Post-Code": item.get("code", ""),
                "City/Town": item.get("place_name", "")
            }
            formatted_results.append(formatted_result)
        
        # Update the job with results
        jobs[job_id]["results"] = formatted_results
        jobs[job_id]["results_count"] = len(formatted_results)
        jobs[job_id]["preview"] = formatted_results[:5] if formatted_results else []
        
        if len(formatted_results) > 0:
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["message"] = f"Found {len(formatted_results)} postcodes for {state}" + (f" ({city})" if city else "")
        else:
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["message"] = f"No postcodes found for {state}" + (f" ({city})" if city else "")
        
        # Get the count of database entries after scraping
        try:
            postcodes = get_all_postcodes()
            jobs[job_id]["db_entries"] = len(postcodes)
        except Exception as e:
            logger.error(f"Error getting database count: {e}")
            jobs[job_id]["db_entries"] = 0
        
        # Save updated job to Supabase
        save_job_to_supabase(job_id, jobs[job_id])
        
        logger.info(f"Job {job_id} completed. Found {len(formatted_results)} postcodes.")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = str(e)
        jobs[job_id]["error_details"] = traceback.format_exc()
        
        # Save failed job to Supabase
        save_job_to_supabase(job_id, jobs[job_id])

@app.route('/job/<job_id>', methods=['GET'])
def get_job_status(job_id):
    # Try to get job from memory first
    job = jobs.get(job_id)
    
    # If not in memory, try to get from Supabase
    if not job:
        job = get_job_from_supabase(job_id)
        
        # If found in Supabase, cache in memory
        if job:
            jobs[job_id] = job
    
    if not job:
        return jsonify({"status": "error", "message": "Job not found"}), 404

    # Return status and preview data if completed
    response_data = {"status": job["status"]}
    
    if job["status"] == "completed":
        response_data["preview"] = job["preview"] or []
        response_data["results_count"] = job["results_count"]
        response_data["db_entries"] = job.get("db_entries", 0)
        response_data["message"] = job.get("message", "")
        
        # Get fresh database stats
        try:
            db_stats = get_database_stats()
            response_data["db_stats"] = db_stats
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            response_data["db_stats_error"] = str(e)
            
    elif job["status"] == "failed":
        response_data["message"] = job["message"]
        # Include more detailed error info if available
        if "error_details" in job:
            response_data["error_details"] = job["error_details"]

    return jsonify(response_data)

@app.route('/database-stats')
def database_stats_route():
    """API endpoint to get current database statistics"""
    return jsonify(get_database_stats())

@app.route('/download/<job_id>')
def download_results(job_id):
    # Try to get job from memory first
    job = jobs.get(job_id)
    
    # If not in memory, try to get from Supabase
    if not job:
        job = get_job_from_supabase(job_id)
    
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
    # Email Configuration - Get from environment variables with fallbacks
    sender_email = os.environ.get("EMAIL_SENDER", "")
    sender_password = os.environ.get("EMAIL_PASSWORD", "")
    receiver_email = os.environ.get("EMAIL_RECEIVER", "kyjahntsmith@gmail.com")
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))

    # Check if credentials are set
    if not sender_email or not sender_password:
        logger.error("Email credentials not configured")
        return jsonify({"status": "error", "message": "Email credentials not configured"}), 500

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
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        logger.info("Info request email sent successfully")
        return jsonify({"status": "success", "message": "Request sent"})
    except Exception as e:
        logger.error(f"Failed to send email: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Failed to send request"}), 500

@app.route('/debug-scraper', methods=['GET'])
def debug_scraper():
    """Debug endpoint to test the scraper directly - protected in production"""
    # Check if we're in development mode
    is_development = os.environ.get('FLASK_ENV') == 'development' or app.debug
    
    # Check for debug API key if in production
    api_key = request.args.get('api_key')
    debug_api_key = os.environ.get('DEBUG_API_KEY')
    
    if not is_development and (not api_key or api_key != debug_api_key):
        return jsonify({
            "status": "error",
            "message": "This endpoint is only available in development mode or with a valid API key"
        }), 403
    
    state = request.args.get('state', 'Connecticut')
    city = request.args.get('city', None)
    
    try:
        # Call the scraper directly
        results = scrape_geonames_postcodes(state, city_filter=city)
        
        # Return limited information in production
        if is_development:
            # Return detailed information in development
            return jsonify({
                "status": "success",
                "state": state,
                "city": city,
                "results_count": len(results) if results else 0,
                "results": results[:10] if results else [],  # Return first 10 results
                "is_none": results is None,
                "type": str(type(results)),
                "scraper_info": {
                    "module": scrape_geonames_postcodes.__module__,
                    "function": scrape_geonames_postcodes.__name__
                }
            })
        else:
            # Return limited information in production
            return jsonify({
                "status": "success",
                "state": state,
                "city": city,
                "results_count": len(results) if results else 0,
                "sample_results": [r.get("code", "") for r in results[:5]] if results else []
            })
    except Exception as e:
        if is_development:
            import traceback
            return jsonify({
                "status": "error",
                "state": state,
                "city": city,
                "error": str(e),
                "traceback": traceback.format_exc()
            }), 500
        else:
            logger.error(f"Debug scraper error: {e}", exc_info=True)
            return jsonify({
                "status": "error",
                "message": "An error occurred during scraping"
            }), 500

if __name__ == '__main__':
    app.run(debug=True)
