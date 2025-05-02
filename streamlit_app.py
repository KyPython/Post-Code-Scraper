import streamlit as st
import time
import threading
import sys
import os
from pathlib import Path

# Debug: Initializing Streamlit app
print("[DEBUG] Starting execution...")

# App title
st.title("Postcode Scraper Demo")
st.write("App is running!")

# Add a visual indicator
st.success("✅ App loaded successfully")

# About section
st.header("About This Demo")
st.write("This application demonstrates web scraping capabilities by extracting postal codes from the United States.")
st.write("Select a state and optionally filter by city to scrape postal codes.")

# Mock data for the demo
MOCK_POSTCODES = {
    "Connecticut": [
        {"id": 1, "code": "06001", "place_name": "Avon", "region_id": 1},
        {"id": 2, "code": "06002", "place_name": "Bloomfield", "region_id": 1},
        {"id": 3, "code": "06010", "place_name": "Bristol", "region_id": 1},
        {"id": 4, "code": "06013", "place_name": "Burlington", "region_id": 1},
        {"id": 5, "code": "06016", "place_name": "East Windsor", "region_id": 1},
        {"id": 6, "code": "06019", "place_name": "Canton", "region_id": 1},
        {"id": 7, "code": "06023", "place_name": "Glastonbury", "region_id": 1},
        {"id": 8, "code": "06029", "place_name": "Ellington", "region_id": 1},
        {"id": 9, "code": "06032", "place_name": "Farmington", "region_id": 1},
        {"id": 10, "code": "06033", "place_name": "Glastonbury", "region_id": 1}
    ],
    "New York": [
        {"id": 11, "code": "10001", "place_name": "Manhattan", "region_id": 2},
        {"id": 12, "code": "10002", "place_name": "Manhattan", "region_id": 2},
        {"id": 13, "code": "10003", "place_name": "Manhattan", "region_id": 2},
        {"id": 14, "code": "11201", "place_name": "Brooklyn", "region_id": 2},
        {"id": 15, "code": "11211", "place_name": "Brooklyn", "region_id": 2},
        {"id": 16, "code": "11215", "place_name": "Brooklyn", "region_id": 2},
        {"id": 17, "code": "11222", "place_name": "Brooklyn", "region_id": 2},
        {"id": 18, "code": "11101", "place_name": "Queens", "region_id": 2},
        {"id": 19, "code": "10451", "place_name": "Bronx", "region_id": 2},
        {"id": 20, "code": "10301", "place_name": "Staten Island", "region_id": 2}
    ],
    "California": [
        {"id": 21, "code": "90001", "place_name": "Los Angeles", "region_id": 3},
        {"id": 22, "code": "90210", "place_name": "Beverly Hills", "region_id": 3},
        {"id": 23, "code": "94016", "place_name": "San Francisco", "region_id": 3},
        {"id": 24, "code": "95014", "place_name": "Cupertino", "region_id": 3},
        {"id": 25, "code": "92093", "place_name": "San Diego", "region_id": 3},
        {"id": 26, "code": "94025", "place_name": "Menlo Park", "region_id": 3},
        {"id": 27, "code": "94043", "place_name": "Mountain View", "region_id": 3},
        {"id": 28, "code": "94085", "place_name": "Sunnyvale", "region_id": 3},
        {"id": 29, "code": "95054", "place_name": "Santa Clara", "region_id": 3},
        {"id": 30, "code": "94301", "place_name": "Palo Alto", "region_id": 3}
    ]
}

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

# Scraper section
st.header("Run Scraper")
st.write("Click the button below to start the scraping process. This may take a minute or two.")

# Progress indicator
if 'progress_placeholder' not in st.session_state:
    st.session_state.progress_placeholder = st.empty()

# Mock scraper function that doesn't rely on external modules
def mock_scrape_postcodes(state, city_filter=""):
    """Simulate scraping postcodes for the selected state and city"""
    print(f"Simulating scraping process for {state}...")
    
    # Create a progress bar
    progress_bar = st.session_state.progress_placeholder.progress(0)
    
    # Get mock data for the selected state or use empty list if not available
    state_data = MOCK_POSTCODES.get(state, [])
    
    # Filter by city if provided
    if city_filter and len(city_filter) > 0:
        filtered_data = [
            postcode for postcode in state_data 
            if city_filter.lower() in postcode['place_name'].lower()
        ]
    else:
        filtered_data = state_data
    
    # Simulate processing with progress updates
    total_items = len(filtered_data)
    for i, postcode in enumerate(filtered_data):
        print(f"Processing {postcode['place_name']} - {postcode['code']}")
        time.sleep(0.3)  # Simulate processing time
        
        # Update progress bar
        progress = min(100, int((i + 1) / max(1, total_items) * 100))
        progress_bar.progress(progress)
    
    # Complete the progress bar
    progress_bar.progress(100)
    time.sleep(0.5)  # Pause briefly at 100%
    
    print(f"Completed scraping simulation for {state}.")
    return filtered_data

def run_scraper():
    try:
        # Reset the completion flag
        st.session_state.scraping_complete = False
        
        # Store the state and city filter when the scraper runs
        state = st.session_state.selected_state
        city = st.session_state.city_filter
        
        # Run the mock scraper
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
    
# Display status
if st.session_state.is_running:
    st.info("Scraping in progress...")
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
    import pandas as pd
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

# Request full access section
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

st.sidebar.markdown("""
## Source Code
View the complete source code on GitHub:
[GitHub Repository](https://github.com/KyPython/Post-Code-Scraper)

The repository includes all database integration code.
""")

# Add a section to show environment information for debugging
with st.expander("Environment Information"):
    st.write(f"Python version: {sys.version}")
    st.write(f"Current directory: {os.getcwd()}")
    st.write(f"Files in current directory: {os.listdir('.')}")
    st.write(f"sys.path: {sys.path}")