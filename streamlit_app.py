import streamlit as st
import time
import threading
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from scraper.geonames_scraper import scrape_connecticut_postcodes
from supabase_utils.db_client import get_all_postcodes

# App title
st.title("Postcode Scraper Demo")

# About section
st.header("About This Demo")
st.write("This application demonstrates web scraping capabilities by extracting postal codes from Connecticut, USA.")
st.write("The data is stored in a Supabase database and can be viewed below.")

# Scraper section
st.header("Run Scraper")
st.write("Click the button below to start the scraping process. This may take a minute or two.")

# Store scraping status in session state
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'last_run' not in st.session_state:
    st.session_state.last_run = None
if 'results' not in st.session_state:
    st.session_state.results = None

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