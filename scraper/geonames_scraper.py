
import time
import os
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from supabase_utils.db_client import insert_and_get_id, insert_postcode_data, get_id_by_column

def check_for_protection(page):
    """Check if we're on a protection/captcha page"""
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
    """Find the table containing postal codes in the HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables on the page")
    
    for index, table in enumerate(tables):
        print(f"\nAnalyzing table {index + 1}:")
        
        # Try to find table with specific class
        if 'restable' in table.get('class', []):
            print("Found table with 'restable' class")
            return table
        
        # Additional checks can be added here
            
    print("\nNo suitable postcode table found.")
    return None

def scrape_connecticut_postcodes():
    print("Initializing Playwright...")
    
    try:
        with sync_playwright() as p:
            # Set browser launch options with slower timeout and retry logic
            launch_options = {
                "headless": True,  # Changed to True for better stability
                "timeout": 60000,   # Increase timeout to 60 seconds
                "args": [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-extensions",
                    "--disable-setuid-sandbox"  # Added for better stability
                ]
            }
            
            # Try to launch browser with retry logic
            max_retries = 3
            browser = None
            for attempt in range(max_retries):
                try:
                    print(f"Browser launch attempt {attempt + 1}/{max_retries}...")
                    browser = p.chromium.launch(**launch_options)
                    print("Browser launched successfully.")
                    break
                except Exception as e:
                    print(f"Browser launch failed: {e}")
                    if attempt < max_retries - 1:
                        print("Retrying in 5 seconds...")
                        time.sleep(5)
                    else:
                        print("Maximum retries reached. Trying Firefox instead...")
                        try:
                            browser = p.firefox.launch(**launch_options)
                            print("Firefox browser launched successfully.")
                            break
                        except Exception as firefox_error:
                            print(f"Firefox launch failed: {firefox_error}")
                            print("Trying Webkit as last resort...")
                            try:
                                browser = p.webkit.launch(**launch_options)
                                print("Webkit browser launched successfully.")
                                break
                            except Exception as webkit_error:
                                print(f"Webkit launch failed: {webkit_error}")
                                raise Exception("All browser engines failed to launch")
            
            if not browser:
                raise Exception("Failed to launch any browser")
                
            # Create context with retry logic
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
            
            # Try both URLs
            urls = [
                "https://www.geonames.org/postal-codes/US/CT/connecticut.html",
                "https://www.geonames.org/postal-codes/US/CT/"
            ]
            
            postal_table = None
            for url in urls:
                print(f"\nTrying URL: {url}")
                
                try:
                    # Navigate to the URL with retry logic
                    for nav_attempt in range(3):
                        try:
                            page.goto(url, timeout=60000, wait_until="domcontentloaded")
                            break
                        except Exception as nav_error:
                            print(f"Navigation attempt {nav_attempt + 1} failed: {nav_error}")
                            if nav_attempt < 2:
                                print("Retrying navigation...")
                                time.sleep(2)
                            else:
                                raise
                    
                    # Wait for page to stabilize
                    page.wait_for_load_state("networkidle", timeout=30000)
                    
                    # Print page info for debugging
                    print(f"Page title: {page.title()}")
                    print(f"Current URL: {page.url}")
                    
                    # Check for protection/captcha
                    if check_for_protection(page):
                        print("\nProtection page detected. Please solve the captcha if present.")
                        input("Press Enter once you've solved the captcha...")
                        time.sleep(2)  # Wait after captcha
                    
                    # Save page source for debugging
                    html_content = page.content()
                    debug_dir = "debug_output"
                    os.makedirs(debug_dir, exist_ok=True)
                    with open(f"{debug_dir}/page_source_{urls.index(url)}.html", "w", encoding="utf-8") as f:
                        f.write(html_content)
                    print(f"Page source saved to '{debug_dir}/page_source_{urls.index(url)}.html'")
                    
                    # Take screenshot for debugging
                    page.screenshot(path=f"{debug_dir}/screenshot_{urls.index(url)}.png")
                    print(f"Screenshot saved to '{debug_dir}/screenshot_{urls.index(url)}.png'")
                    
                    # Find postal code table
                    postal_table = find_postcode_table(html_content)
                    if postal_table:
                        break  # Exit URL loop if table is found
                        
                except Exception as e:
                    print(f"Error processing URL {url}: {e}")
                    continue
            
            if not postal_table:
                print("\nCould not find postal code table in any of the URLs")
                browser.close()
                return
                
            print("\nPostcode table found. Processing data...")
            
            # Get or create country using improved database functions
            country_id = get_id_by_column("countries", "name", "USA")
            if country_id is None:
                print("Creating USA country entry...")
                country_id = insert_and_get_id("countries", {"name": "USA", "code": "US"}, "name")
                if country_id is None:
                    print("Failed to create country entry. Aborting.")
                    browser.close()
                    return
            
            # Get or create region
            region_id = get_id_by_column("regions", "name", "Connecticut")
            if region_id is None:
                print("Creating Connecticut region entry...")
                region_id = insert_and_get_id("regions", {"name": "Connecticut", "code": "CT", "country_id": country_id}, "name")
                if region_id is None:
                    print("Failed to create region entry. Aborting.")
                    browser.close()
                    return
            
            # Process rows
            rows = postal_table.find_all("tr")[1:]  # Skip header
            success_count = 0
            error_count = 0
            
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 3:  # Ensure we have at least 3 columns
                    # The actual table structure has index in col[0], place in col[1], code in col[2]
                    # index = cols[0].text.strip()      # First column is the index number (optional to store)
                    place_name = cols[1].text.strip() # Second column is place name (e.g., "Avon")
                    postcode = cols[2].text.strip()   # Third column is postal code (e.g., "06001")
                    
                    if place_name and postcode:
                        print(f"Processing: {place_name} - {postcode}")
                        data = {
                            "code": postcode,         # Put the postal code in the "code" field
                            "place_name": place_name, # Put the place name in the "place_name" field
                            "region_id": region_id,
                        }
                        if insert_postcode_data(data):
                            success_count += 1
                        else:
                            error_count += 1
                else:
                    print(f"Skipping row, expected 3+ columns, found {len(cols)}")
            
            # --- This block should be OUTSIDE the loop ---
            print(f"\nScraping completed:")
            print(f"Successfully processed: {success_count} postcodes")
            print(f"Errors encountered: {error_count} postcodes")
            
            browser.close()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    scrape_connecticut_postcodes()
