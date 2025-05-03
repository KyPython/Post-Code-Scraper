from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import threading
import time
import io

app = Flask(__name__)

# Mock data for demonstration
MOCK_DATA = {
    "Connecticut": [
        {"id": 1, "code": "06001", "place_name": "Avon", "region_id": 1},
        {"id": 2, "code": "06002", "place_name": "Bloomfield", "region_id": 1}
    ],
    "New York": [
        {"id": 11, "code": "10001", "place_name": "Manhattan", "region_id": 2}
    ]
}

# Track scraping jobs
scraping_jobs = {}

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