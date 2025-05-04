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

def scrape_geonames_postcodes(state_name: str, city_filter: str = None):
    print("I'm initializing Playwright...")
    
    # Create a list to store results
    results = []
    
    try:
        with sync_playwright() as p:
            # I set browser launch options with a slower timeout and retry logic
            launch_options = {
                "headless": True,  # I changed this to True for better stability
                "timeout": 60000,   # I increased the timeout to 60 seconds
                "args": [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-extensions",
                    "--disable-setuid-sandbox"  # I added this for better stability
                ]
            }
            
            # I try to launch the browser with retry logic
            max_retries = 3
            browser = None
            for attempt in range(max_retries):
                try:
                    print(f"Attempting browser launch ({attempt + 1}/{max_retries})...")
                    browser = p.chromium.launch(**launch_options)
                    print("Browser launched successfully.")
                    break
                except Exception as e:
                    print(f"Browser launch failed: {e}")
                    if attempt < max_retries - 1:
                        print("I'll retry in 5 seconds...")
                        time.sleep(5)
                    else:
                        print("I've reached the maximum retries. I'll try Firefox instead...")
                        try:
                            browser = p.firefox.launch(**launch_options)
                            print("Firefox browser launched successfully.")
                            break
                        except Exception as firefox_error:
                            print(f"Firefox launch failed: {firefox_error}")
                            print("I'll try Webkit as a last resort...")
                            try:
                                browser = p.webkit.launch(**launch_options)
                                print("Webkit browser launched successfully.")
                                break
                            except Exception as webkit_error:
                                print(f"Webkit launch failed: {webkit_error}")
                                raise Exception("I couldn't launch any browser engines.")
            
            if not browser:
                raise Exception("I failed to launch any browser.")
                
            # I create a context with retry logic
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
            state_details = STATE_MAP.get(state_name)
            if not state_details:
                print(f"Error: State '{state_name}' not found in STATE_MAP.")
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
                
            print(f"\nPostcode table found for {state_name}. Processing data...")
            
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
            region_id = get_id_by_column("regions", "name", state_name, country_id=country_id)
            if region_id is None:
                print(f"Creating {state_name} region entry...")
                region_id = insert_and_get_id("regions", {"name": state_name, "code": state_abbr, "country_id": country_id}, "name")
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
            print(f"\nScraping completed for {state_name}" + (f" (City: {city_filter})" if city_filter else "") + ":")
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

if __name__ == "__main__":
    print("--- GeoNames Postcode Scraper ---")
    state_input = input("Enter the full name of the US state to scrape (e.g., New York): ").strip()
    city_input = input("Enter a city name to filter by (optional, press Enter to skip): ").strip()

    if not city_input:
        city_input = None # Ensure it's None if empty

    scrape_geonames_postcodes(state_name=state_input, city_filter=city_input)
