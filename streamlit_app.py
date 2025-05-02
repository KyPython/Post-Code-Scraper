import streamlit as st
import time
import threading
import sys
import os
import io
import pandas as pd
from pathlib import Path

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the scraper module
try:
    from scraper.geonames_scraper import scrape_connecticut_postcodes
    from supabase_utils.db_client import get_all_postcodes
    SCRAPER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import scraper modules: {e}")
    SCRAPER_AVAILABLE = False

# Debug: Initializing Streamlit app
print("[DEBUG] Starting execution...")

# App title
st.title("Postcode Scraper")
st.write("Real-time web scraping demonstration")

# Add a visual indicator
st.success("✅ App loaded successfully")

# About section
st.header("About This App")
st.write("This application demonstrates web scraping capabilities by extracting postal codes from the United States.")
st.write("Select a state and optionally filter by city to scrape postal codes.")

# List of US states for the dropdown
US_STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", 
    "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", 
    "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", 
    "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", 
    "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", 
    "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", 
    "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"
]

# Scraper configuration section
st.header("Configure Scraper")

# State selection
selected_state = st.selectbox(
    "Select a state to scrape:",
    options=US_STATES,
    index=US_STATES.index("Connecticut")
)

# City filter (optional)
city_filter = st.text_input("Filter by city (optional):", "")

# Store scraping status in session state
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'last_run' not in st.session_state:
    st.session_state.last_run = None
if 'results' not in st.session_state:
    st.session_state.results = None
if 'selected_state' not in st.session_state:
    st.session_state.selected_state = selected_state
if 'city_filter' not in st.session_state:
    st.session_state.city_filter = city_filter
if 'scraped_data' not in st.session_state:
    st.session_state.scraped_data = None
if 'scraping_complete' not in st.session_state:
    st.session_state.scraping_complete = False
if 'log_messages' not in st.session_state:
    st.session_state.log_messages = []

# Scraper section
st.header("Run Scraper")
st.write("Click the button below to start the scraping process. This may take a minute or two.")

# Progress indicator
if 'progress_placeholder' not in st.session_state:
    st.session_state.progress_placeholder = st.empty()

# Log container
log_container = st.empty()

# Function to add log messages
def add_log(message):
    st.session_state.log_messages.append(f"{time.strftime('%H:%M:%S')} - {message}")
    # Display logs in the UI
    log_container.code('\n'.join(st.session_state.log_messages))

# Capture stdout to display in the UI
class StreamlitCapture:
    def __init__(self):
        self.old_stdout = sys.stdout
        self.string_io = io.StringIO()
        
    def write(self, text):
        self.old_stdout.write(text)
        if text.strip():  # Only add non-empty lines
            add_log(text.strip())
            
    def flush(self):
        self.old_stdout.flush()

# Real scraper function that uses our existing scraper
def real_scrape_postcodes(state, city_filter=""):
    """Scrape postcodes for the selected state and city using our scraper module"""
    
    # Create a progress bar
    progress_bar = st.session_state.progress_placeholder.progress(0)
    
    # Currently only Connecticut is fully implemented
    if state.lower() != "connecticut":
        add_log(f"Warning: Full scraping for {state} is not yet implemented.")
        add_log(f"Defaulting to Connecticut for demonstration purposes.")
        state = "Connecticut"
    
    add_log(f"Starting scraping process for {state}...")
    
    # Capture stdout to show in the UI
    stdout_capture = StreamlitCapture()
    old_stdout = sys.stdout
    sys.stdout = stdout_capture
    
    try:
        # Run the scraper with the city filter
        scrape_connecticut_postcodes(city_filter=city_filter)
        
        # Get the results from the database
        add_log("Retrieving results from database...")
        results = get_all_postcodes()
        
        # Filter results by city if needed
        if city_filter and len(city_filter) > 0:
            filtered_results = [
                postcode for postcode in results 
                if city_filter.lower() in postcode.get('place_name', '').lower()
            ]
            add_log(f"Filtered {len(results) - len(filtered_results)} postcodes that didn't match '{city_filter}'")
            results = filtered_results
        
        # Complete the progress bar
        progress_bar.progress(100)
        
        add_log(f"Completed scraping for {state}. Found {len(results)} postcodes.")
        return results
        
    except Exception as e:
        import traceback
        add_log(f"Error during scraping: {str(e)}")
        add_log(traceback.format_exc())
        return []
    finally:
        # Restore stdout
        sys.stdout = old_stdout

# Fallback to mock data if the scraper is not available
def mock_scrape_postcodes(state, city_filter=""):
    """Simulate scraping postcodes for the selected state and city"""
    add_log(f"Using mock data for {state}...")
    
    # Create a progress bar
    progress_bar = st.session_state.progress_placeholder.progress(0)
    
    # Mock data for demonstration
    MOCK_POSTCODES = {
        "Connecticut": [
            {"id": 1, "code": "06001", "place_name": "Avon", "region_id": 1},
            {"id": 2, "code": "06002", "place_name": "Bloomfield", "region_id": 1},
            {"id": 3, "code": "06010", "place_name": "Bristol", "region_id": 1},
            # ... more mock data
        ],
        "New York": [
            {"id": 11, "code": "10001", "place_name": "Manhattan", "region_id": 2},
            {"id": 12, "code": "10002", "place_name": "Manhattan", "region_id": 2},
            # ... more mock data
        ],
        # ... more states
    }
    
    # Get mock data for the selected state or use empty list if not available
    state_data = MOCK_POSTCODES.get(state, [])
    
    # Filter by city if provided
    if city_filter and len(city_filter) > 0:
        filtered_data = [
            postcode for postcode in state_data 
            if city_filter.lower() in postcode['place_name'].lower()
        ]
        add_log(f"Filtered to {len(filtered_data)} postcodes matching '{city_filter}'")
    else:
        filtered_data = state_data
    
    # Simulate processing with progress updates
    total_items = len(filtered_data)
    for i, postcode in enumerate(filtered_data):
        add_log(f"Processing {postcode['place_name']} - {postcode['code']}")
        time.sleep(0.3)  # Simulate processing time
        
        # Update progress bar
        progress = min(100, int((i + 1) / max(1, total_items) * 100))
        progress_bar.progress(progress)
    
    # Complete the progress bar
    progress_bar.progress(100)
    time.sleep(0.5)  # Pause briefly at 100%
    
    add_log(f"Completed mock scraping for {state}.")
    return filtered_data

def run_scraper():
    try:
        # Reset the completion flag and logs
        st.session_state.scraping_complete = False
        st.session_state.log_messages = []
        
        # Store the state and city filter when the scraper runs
        state = st.session_state.selected_state
        city = st.session_state.city_filter
        
        # Run the appropriate scraper
        if SCRAPER_AVAILABLE and state.lower() == "connecticut":
            add_log("Using real scraper...")
            results = real_scrape_postcodes(state, city)
        else:
            add_log("Using mock scraper (real scraper not available)...")
            results = mock_scrape_postcodes(state, city)
        
        # Store the results
        st.session_state.scraped_data = results
        st.session_state.results = f"Successfully scraped {len(results)} postcodes from {state}"
        
        if city and len(city) > 0:
            st.session_state.results += f" (filtered by city: {city})"
            
        # Set the completion flag
        st.session_state.scraping_complete = True
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        st.session_state.results = f"Error: {str(e)}"
        st.session_state.scraped_data = None
    finally:
        st.session_state.is_running = False
        st.session_state.last_run = time.strftime("%Y-%m-%d %H:%M:%S")

# Update session state when selections change
if selected_state != st.session_state.selected_state:
    st.session_state.selected_state = selected_state
    
if city_filter != st.session_state.city_filter:
    st.session_state.city_filter = city_filter

# Start scraping button
if st.button("Start Scraping", disabled=st.session_state.is_running):
    st.session_state.is_running = True
    st.session_state.scraping_complete = False
    st.session_state.progress_placeholder = st.empty()
    
    # Start scraping in a background thread
    thread = threading.Thread(target=run_scraper)
    thread.daemon = True
    thread.start()
    
    st.success(f"Started scraping postcodes for {selected_state}...")
    
# Display status and logs
if st.session_state.is_running:
    st.info("Scraping in progress... See the log below for details.")
    # Show the log container if it's not already visible
    if not st.session_state.log_messages:
        log_container.code("Initializing scraper...")
elif st.session_state.results:
    if st.session_state.results.startswith("Error"):
        st.error(f"{st.session_state.results} (Last run: {st.session_state.last_run})")
    else:
        st.success(f"{st.session_state.results} (Last run: {st.session_state.last_run})")

# Show completion notification and preview
if st.session_state.scraping_complete and st.session_state.scraped_data:
    # Clear the progress bar
    st.session_state.progress_placeholder.empty()
    
    # Show completion notification
    st.balloons()  # Visual celebration
    
    # Preview section
    st.header("🎉 Scraping Complete!")
    st.subheader("Preview of First 5 Postcodes")
    
    # Show the first 5 postcodes as a preview
    preview_data = st.session_state.scraped_data[:5]
    st.table(preview_data)
    
    # Show how many more are available
    remaining = max(0, len(st.session_state.scraped_data) - 5)
    if remaining > 0:
        st.info(f"Plus {remaining} more postcodes. View the full dataset below.")

# Full data section
st.header("View Full Dataset")

# Show the scraped data if available
if st.session_state.scraped_data is not None and len(st.session_state.scraped_data) > 0:
    # Add a download button
    df = pd.DataFrame(st.session_state.scraped_data)
    csv = df.to_csv(index=False)
    
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"postcodes_{st.session_state.selected_state.lower().replace(' ', '_')}.csv",
        mime="text/csv"
    )
    
    # Show the full dataset
    st.dataframe(st.session_state.scraped_data)
elif st.session_state.last_run is not None:
    st.info("No data found for the selected criteria.")
else:
    st.info("Run the scraper to see results here.")

# How it works section
st.header("How It Works")
st.write("""
This application demonstrates real web scraping in action:

1. **Data Source**: The app connects to geonames.org to fetch postal code data
2. **Scraping Process**: For the selected state, the app:
   - Navigates to the state's postal code page
   - Extracts postal codes using HTML parsing
   - Organizes the data into a structured format
3. **Real-time Logging**: Watch the scraping process happen in real-time
4. **Results**: View and download the scraped data

The entire process is transparent, showing you exactly how web scraping works.
""")

# Ethical considerations
with st.expander("Ethical Web Scraping Considerations"):
    st.write("""
    When scraping websites, always consider these ethical guidelines:
    
    - **Respect robots.txt**: Check if scraping is allowed
    - **Rate limiting**: Don't overwhelm servers with too many requests
    - **Data usage**: Only use the data for legitimate purposes
    - **Terms of Service**: Ensure you're not violating the website's terms
    - **Personal data**: Be careful with personally identifiable information
    
    This demo implements rate limiting and only collects public postal code data.
    """)

st.sidebar.markdown("""
## About This Project
This web scraping demonstration shows how to:

- Extract data from websites
- Process HTML content
- Structure data for analysis
- Store data in a database
- Provide real-time feedback

The code is available on GitHub:
[GitHub Repository](https://github.com/KyPython/Post-Code-Scraper)
""")

# Add a section to show environment information for debugging
with st.expander("Environment Information"):
    st.write(f"Python version: {sys.version}")
    st.write(f"Current directory: {os.getcwd()}")
    st.write(f"Files in current directory: {os.listdir('.')}")
    st.write(f"sys.path: {sys.path}")
    st.write(f"Scraper available: {SCRAPER_AVAILABLE}")