import time
import os
import sys
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# Add parent directory to sys.path to allow importing supabase_utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from supabase_utils.db_client import insert_and_get_id, insert_postcode_data, get_id_by_column

# --- State Mapping ---
# (Add more states as needed)
STATE_MAP = {
    "Connecticut": {"abbr": "CT", "slug": "connecticut"},
    "New York": {"abbr": "NY", "slug": "new-york"},
    "California": {"abbr": "CA", "slug": "california"},
    "Texas": {"abbr": "TX", "slug": "texas"},
    "Florida": {"abbr": "FL", "slug": "florida"},
    "Illinois": {"abbr": "IL", "slug": "illinois"},
    "Pennsylvania": {"abbr": "PA", "slug": "pennsylvania"},
    "Ohio": {"abbr": "OH", "slug": "ohio"},
    "Georgia": {"abbr": "GA", "slug": "georgia"},
    "North Carolina": {"abbr": "NC", "slug": "north-carolina"},
    "Michigan": {"abbr": "MI", "slug": "michigan"},
    "New Jersey": {"abbr": "NJ", "slug": "new-jersey"},
    "Virginia": {"abbr": "VA", "slug": "virginia"},
    "Washington": {"abbr": "WA", "slug": "washington"},
    "Arizona": {"abbr": "AZ", "slug": "arizona"},
    "Massachusetts": {"abbr": "MA", "slug": "massachusetts"},
    "Tennessee": {"abbr": "TN", "slug": "tennessee"},
    "Indiana": {"abbr": "IN", "slug": "indiana"},
    "Missouri": {"abbr": "MO", "slug": "missouri"},
    "Maryland": {"abbr": "MD", "slug": "maryland"},
    # Add all other states...
}


def check_for_protection(page):
    """Checks if the current page seems to be a protection/captcha page."""
    protection_indicators = [
        "captcha",
        "security check",
        "verify you're human",
        "cloudflare"
    ]
    
    page_text = page.content().lower()
    for indicator in protection_indicators:
        if indicator in page_text:
            return True
    return False

def find_postcode_table(html_content):
    """Finds the table containing postal codes in the HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables on the page.")
    
    for index, table in enumerate(tables):
        print(f"\nAnalyzing table {index + 1}:")
        
        # Try to find a table with a specific class
        if 'restable' in table.get('class', []):
            print("Found table with 'restable' class.")
            return table
        
        # Additional checks can be added here
            
    print("\nCould not find a suitable postcode table.")
    return None

def scrape_geonames_postcodes(state, city_filter=None):
    """
    Scrape postal codes from geonames.org for a given US state
    
    Args:
        state (str): The state to scrape postal codes for
        city_filter (str, optional): Filter results by city name
        
    Returns:
        list: List of dictionaries with postcode data
    """
    try:
        # Initialize results list
        results = []
        
        print("I'm initializing Playwright...")
        from playwright.sync_api import sync_playwright
        import subprocess
        import sys
        
        # Check if we're in a cloud environment and install browsers if needed
        if os.environ.get("CI") or os.environ.get("RENDER") or os.environ.get("DOCKER_CONTAINER"):
            try:
                print("Detected cloud environment, ensuring browsers are installed...")
                # Install browsers directly using subprocess
                subprocess.run(
                    [sys.executable, "-m", "playwright", "install", "chromium"],
                    check=True,
                    capture_output=True
                )
                print("Successfully installed Chromium browser")
            except subprocess.CalledProcessError as e:
                print(f"Failed to install browsers: {e.stderr.decode()}")
                print("Will attempt to use fallback method")
        
        # Initialize Playwright
        p = sync_playwright().start()
        
        # Set up browser launch options
        launch_options = {
            "headless": True,  # Run in headless mode
        }
        
        # Try to detect if we're running in a CI/CD environment
        if os.environ.get("CI") or os.environ.get("RENDER") or os.environ.get("DOCKER_CONTAINER"):
            # Add CI-specific options
            launch_options.update({
                "args": [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-accelerated-2d-canvas",
                    "--no-first-run",
                    "--no-zygote",
                    "--single-process",
                    "--disable-gpu"
                ]
            })
        
        # Try to launch browsers with multiple retries
        browser = None
        max_retries = 3
        
        # Try Chromium first
        for attempt in range(1, max_retries + 1):
            try:
                print(f"Attempting browser launch ({attempt}/{max_retries})...")
                browser = p.chromium.launch(**launch_options)
                break
            except Exception as e:
                print(f"Browser launch failed: {str(e)}")
                if attempt < max_retries:
                    print(f"I'll retry in 5 seconds...")
                    time.sleep(5)
                else:
                    print(f"I've reached the maximum retries. I'll try Firefox instead...")
        
        # If Chromium failed, try Firefox
        if browser is None:
            try:
                browser = p.firefox.launch(**launch_options)
            except Exception as e:
                print(f"Firefox launch failed: {str(e)}")
                print(f"I'll try Webkit as a last resort...")
                try:
                    browser = p.webkit.launch(**launch_options)
                except Exception as e:
                    print(f"Webkit launch failed: {str(e)}")
                    # If all browser engines fail, try a fallback method
                    print("All browser engines failed. Using fallback method...")
                    return fallback_scraper(state, city_filter)
        
        # Create a context with retry logic
        try:
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            print("Browser context and page created successfully.")
        except Exception as e:
            print(f"Failed to create context or page: {e}")
            if browser:
                browser.close()
            raise
        
        # Get state details from map
        state_details = STATE_MAP.get(state)
        if not state_details:
            print(f"Error: State '{state}' not found in STATE_MAP.")
            browser.close()
            return
        
        state_abbr = state_details["abbr"]
        state_slug = state_details["slug"]
        
        # Construct URLs dynamically
        urls = [
            f"https://www.geonames.org/postal-codes/US/{state_abbr}/{state_slug}.html",
            f"https://www.geonames.org/postal-codes/US/{state_abbr}/"
        ]
        
        postal_table = None
        for url in urls:
            print(f"\nI'm trying the URL: {url}")
            
            try:
                # I navigate to the URL with retry logic
                for nav_attempt in range(3):
                    try:
                        page.goto(url, timeout=60000, wait_until="domcontentloaded")
                        break
                    except Exception as nav_error:
                        print(f"Navigation attempt {nav_attempt + 1} failed: {nav_error}")
                        if nav_attempt < 2: # Use '<' for correct retry count
                            print("I'll retry navigation...")
                            time.sleep(2)
                        else:
                            raise
                
                # I wait for the page to stabilize
                page.wait_for_load_state("networkidle", timeout=30000)
                
                # I print page info for debugging
                print(f"Page title: {page.title()}")
                print(f"Current URL: {page.url}")
                
                # I check for protection/captcha
                if check_for_protection(page): # Consider removing input for automated runs
                    print("\nI detected a protection page. Please solve the captcha if present.")
                    input("Press Enter once you've solved the captcha...")
                    time.sleep(2)  # I wait after the captcha
                
                # I save the page source for debugging
                html_content = page.content()
                debug_dir = "debug_output"
                os.makedirs(debug_dir, exist_ok=True)
                with open(f"{debug_dir}/page_source_{urls.index(url)}.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                print(f"Page source saved to '{debug_dir}/page_source_{urls.index(url)}.html'")
                
                # I take a screenshot for debugging
                page.screenshot(path=f"{debug_dir}/screenshot_{urls.index(url)}.png")
                print(f"Screenshot saved to '{debug_dir}/screenshot_{urls.index(url)}.png'")
                
                # I find the postal code table
                postal_table = find_postcode_table(html_content)
                if postal_table:
                    break  # I exit the URL loop if I find the table
                    
            except Exception as e:
                print(f"Error processing URL {url}: {e}")
                continue
        
        if not postal_table:
            print("\nI couldn't find the postal code table in any of the URLs.")
            browser.close()
            return
            
        print(f"\nPostcode table found for {state}. Processing data...")
        
        # I get or create the country using improved database functions
        country_id = get_id_by_column("countries", "name", "USA")
        if country_id is None:
            print("I'm creating a USA country entry...")
            country_id = insert_and_get_id("countries", {"name": "USA", "code": "US"}, "name")
            if country_id is None:
                print("I failed to create the country entry. I'm aborting.")
                browser.close()
                return
        
        # I get or create the region
        region_id = get_id_by_column("regions", "name", state, country_id=country_id)
        if region_id is None:
            print(f"Creating {state} region entry...")
            region_id = insert_and_get_id("regions", {"name": state, "code": state_abbr, "country_id": country_id}, "name")
            if region_id is None:
                print("Failed to create region entry. Aborting.")
                browser.close()
                return
        
        # I process the rows
        rows = postal_table.find_all("tr")[1:]  # I skip the header
        success_count = 0
        error_count = 0
        
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 3:  # I ensure there are at least 3 columns
                place_name = cols[1].text.strip() # Second column is the place name (e.g., "Avon")
                postcode = cols[2].text.strip()   # Third column is the postal code (e.g., "06001")

                # Apply city filter if provided
                if city_filter and city_filter.lower() not in place_name.lower():
                    continue # Skip this row if city doesn't match

                if place_name and postcode:
                    print(f"Processing: {place_name} - {postcode}")
                    data = {
                        "code": postcode,
                        "place_name": place_name,
                        "region_id": region_id,
                    }
                    
                    # Add to results list
                    results.append({
                        "code": postcode,
                        "place_name": place_name
                    })
                    
                    if insert_postcode_data(data):
                        success_count += 1
                    else:
                        error_count += 1
            else:
                print(f"Skipping row, expected 3+ columns, found {len(cols)}.")
        
        # --- This block should be OUTSIDE the loop ---
        print(f"\nScraping completed for {state}" + (f" (City: {city_filter})" if city_filter else "") + ":")
        print(f"Successfully processed/inserted: {success_count} postcodes.")
        print(f"Errors encountered: {error_count} postcodes.")
        print(f"Total results in list: {len(results)}")
        
        browser.close()
        
        # Return the results list
        return results
        
    except Exception as e:
        print(f"An error occurred during scraping: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return []  # Return empty list on error

def fallback_scraper(state, city_filter=None):
    """
    A fallback scraper that uses requests and BeautifulSoup instead of Playwright.
    This is used when Playwright browsers are not available.
    
    Args:
        state (str): The state to scrape postcodes for
        city_filter (str, optional): Filter results to this city only
        
    Returns:
        list: List of dictionaries with postcode data
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        # Explicitly tell Playwright to use system-installed browsers (redundant here, but safe)
        print(f"Using fallback scraper for {state} {city_filter if city_filter else ''}")
        
        # Get state details from map
        state_details = STATE_MAP.get(state)
        if not state_details:
            print(f"Error: State '{state}' not found in STATE_MAP.")
            return []
        
        state_abbr = state_details["abbr"]
        state_slug = state_details["slug"]
        
        # Create the URL
        url = f"https://www.geonames.org/postal-codes/US/{state_abbr}/{state_slug}.html"
        
        # Send a request to the URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Failed to fetch data: Status code {response.status_code}")
            return []
        
        # Save the HTML for debugging
        debug_dir = "debug_output"
        os.makedirs(debug_dir, exist_ok=True)
        with open(f"{debug_dir}/fallback_page_source.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the table with postal codes
        table = soup.find('table', class_='restable')
        if not table:
            print("Could not find postal code table")
            return []
        
        # Extract data from the table
        results = []
        rows = table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 3:  # Ensure there are at least 3 columns
                place_name = cells[1].text.strip() # Second column is the place name
                postcode = cells[2].text.strip()   # Third column is the postal code
                
                # Apply city filter if provided
                if city_filter and city_filter.lower() not in place_name.lower():
                    continue
                
                results.append({
                    'place_name': place_name,
                    'code': postcode
                })
        
        print(f"Fallback scraper found {len(results)} results")
        return results
        
    except Exception as e:
        print(f"Fallback scraper error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return []

if __name__ == "__main__":
    print("--- GeoNames Postcode Scraper ---")
    state_input = input("Enter the full name of the US state to scrape (e.g., New York): ").strip()
    city_input = input("Enter a city name to filter by (optional, press Enter to skip): ").strip()

    if not city_input:
        city_input = None # Ensure it's None if empty

    scrape_geonames_postcodes(state_name=state_input, city_filter=city_input)
