import streamlit as st
import time
import threading
import sys
from pathlib import Path

# Debug: Initializing Streamlit app
print("[DEBUG] streamlit_app.py: Starting execution...")
print(f"[DEBUG] streamlit_app.py: Initial sys.path: {sys.path}")

# Add project root to sys.path
project_root = str(Path(__file__).resolve().parent) # Assuming streamlit_app.py is in the root
sys.path.append(project_root)
print(f"[DEBUG] streamlit_app.py: Added project root to sys.path: {project_root}")
print(f"[DEBUG] streamlit_app.py: Updated sys.path: {sys.path}")

print("[DEBUG] streamlit_app.py: Attempting to import custom modules...")
from scraper.geonames_scraper import scrape_connecticut_postcodes
from supabase_utils.db_client import get_all_postcodes

# App title
st.title("Postcode Scraper Demo")
st.write("App is running!")

# Add a visual indicator
print("[DEBUG] streamlit_app.py: Rendering success indicator.")
st.success("✅ App loaded successfully")

# About section
st.header("About This Demo")
st.write("This application demonstrates web scraping capabilities by extracting postal codes from Connecticut, USA.")
st.write("The data is stored in a Supabase database and can be viewed below.")

st.header("Request Full Access")
st.write("""
This is a demo version with mock data. To request access to the full version with real database integration:

1. Contact the developer at [your-email@example.com](mailto:your-email@example.com)
2. Provide your use case and credentials
3. We'll set up a secure access method for you
""")

with st.expander("Why is access restricted?"):
    st.write("""
    Database access is restricted to prevent:
    
    - Unauthorized data access
    - Potential misuse of the scraping functionality
    - Excessive database operations
    
    This is standard practice for applications that connect to production databases.
    """)

# Scraper section
st.header("Run Scraper")
st.write("Click the button below to start the scraping process. This may take a minute or two.")

st.header("Full Demo Video")
st.write("Watch a demonstration of the application with real database integration:")
st.video("https://youtu.be/your-demo-video-id") 
print("[DEBUG] streamlit_app.py: Rendered video section.")

# Store scraping status in session state
print("[DEBUG] streamlit_app.py: Initializing session state variables if they don't exist.")
if 'is_running' not in st.session_state:
    print("[DEBUG] streamlit_app.py: Initializing 'is_running' to False.")
    st.session_state.is_running = False
if 'last_run' not in st.session_state:
    print("[DEBUG] streamlit_app.py: Initializing 'last_run' to None.")
    st.session_state.last_run = None
if 'results' not in st.session_state:
    print("[DEBUG] streamlit_app.py: Initializing 'results' to None.")
    st.session_state.results = None

print("[DEBUG] streamlit_app.py: Rendering sidebar.")
st.sidebar.markdown("""
## Source Code
View the complete source code on GitHub:
[GitHub Repository](https://github.com/KyPython/Post-Code-Scraper)

The repository includes all database integration code.
""")

def run_scraper():
    print("[DEBUG] run_scraper: Thread started.")
    try:
        print("[DEBUG] run_scraper: Calling scrape_connecticut_postcodes()...")
        # Run the scraper
        scrape_connecticut_postcodes()
        print("[DEBUG] run_scraper: scrape_connecticut_postcodes() finished.")
        st.session_state.results = "Scrape completed successfully"
        print("[DEBUG] run_scraper: Set results to success.")
    except Exception as e:
        print(f"[ERROR] run_scraper: Exception occurred: {e}")
        import traceback
        print(traceback.format_exc())
        st.session_state.results = f"Error: {str(e)}"
        print(f"[DEBUG] run_scraper: Set results to error: {st.session_state.results}")
    finally:
        print("[DEBUG] run_scraper: Entering finally block.")
        st.session_state.is_running = False
        st.session_state.last_run = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[DEBUG] run_scraper: Set is_running to False, last_run to {st.session_state.last_run}.")
        print("[DEBUG] run_scraper: Thread finished.")

print("[DEBUG] streamlit_app.py: Rendering 'Start Scraping' button.")
if st.button("Start Scraping", disabled=st.session_state.is_running):
    print("[DEBUG] streamlit_app.py: 'Start Scraping' button clicked.")
    st.session_state.is_running = True
    print("[DEBUG] streamlit_app.py: Set is_running to True.")
    
    # Start scraping in a background thread
    print("[DEBUG] streamlit_app.py: Creating and starting background thread for run_scraper.")
    thread = threading.Thread(target=run_scraper)
    thread.daemon = True
    thread.start()
    
    st.success("Scrape started!")
    print("[DEBUG] streamlit_app.py: Displayed 'Scrape started!' message.")
    
# Display status
print("[DEBUG] streamlit_app.py: Checking scraping status for display.")
if st.session_state.is_running:
    print("[DEBUG] streamlit_app.py: Displaying 'Scraping in progress...'")
    st.info("Scraping in progress...")
elif st.session_state.results:
    print(f"[DEBUG] streamlit_app.py: Displaying results: {st.session_state.results}")
    if st.session_state.results.startswith("Error"):
        st.error(f"{st.session_state.results} (Last run: {st.session_state.last_run})")
    else:
        st.success(f"{st.session_state.results} (Last run: {st.session_state.last_run})")

# Data section
print("[DEBUG] streamlit_app.py: Rendering 'View Data' section.")
st.header("View Data")
if st.button("Load Data"):
    print("[DEBUG] streamlit_app.py: 'Load Data' button clicked.")
    print("[DEBUG] streamlit_app.py: Calling get_all_postcodes()...")
    postcodes = get_all_postcodes()
    print(f"[DEBUG] streamlit_app.py: get_all_postcodes() returned {len(postcodes) if postcodes else 0} items.")
    if postcodes and len(postcodes) > 0:
        print("[DEBUG] streamlit_app.py: Displaying postcode data in dataframe.")
        st.dataframe(postcodes)
    else:
        print("[DEBUG] streamlit_app.py: Displaying 'No data available'.")
        st.info("No data available")

print("[DEBUG] streamlit_app.py: Reached end of script execution for this run.")