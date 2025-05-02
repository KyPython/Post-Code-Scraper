import streamlit as st
import time
import threading
import sys
from pathlib import Path

# Debug print to console
print("Starting Streamlit app...")

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from scraper.geonames_scraper import scrape_connecticut_postcodes
from supabase_utils.db_client import get_all_postcodes

# App title
st.title("Postcode Scraper Demo")
st.write("App is running!")

# Add a visual indicator
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

# Store scraping status in session state
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'last_run' not in st.session_state:
    st.session_state.last_run = None
if 'results' not in st.session_state:
    st.session_state.results = None

st.sidebar.markdown("""
## Source Code
View the complete source code on GitHub:
[GitHub Repository](https://github.com/KyPython/Post-Code-Scraper)

The repository includes all database integration code.
""")

def run_scraper():
    try:
        # Run the scraper
        scrape_connecticut_postcodes()
        st.session_state.results = "Scrape completed successfully"
    except Exception as e:
        st.session_state.results = f"Error: {str(e)}"
    finally:
        st.session_state.is_running = False
        st.session_state.last_run = time.strftime("%Y-%m-%d %H:%M:%S")

if st.button("Start Scraping", disabled=st.session_state.is_running):
    st.session_state.is_running = True
    
    # Start scraping in a background thread
    thread = threading.Thread(target=run_scraper)
    thread.daemon = True
    thread.start()
    
    st.success("Scrape started!")
    
# Display status
if st.session_state.is_running:
    st.info("Scraping in progress...")
elif st.session_state.results:
    if st.session_state.results.startswith("Error"):
        st.error(f"{st.session_state.results} (Last run: {st.session_state.last_run})")
    else:
        st.success(f"{st.session_state.results} (Last run: {st.session_state.last_run})")

# Data section
st.header("View Data")
if st.button("Load Data"):
    postcodes = get_all_postcodes()
    if postcodes and len(postcodes) > 0:
        st.dataframe(postcodes)
    else:
        st.info("No data available")