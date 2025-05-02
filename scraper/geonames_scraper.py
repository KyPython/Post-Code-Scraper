import time
import os
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from supabase_utils.db_client import insert_and_get_id, insert_postcode_data, get_id_by_column

def check_for_protection(page):
    """I check if I'm on a protection/captcha page."""
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
    """I find the table containing postal codes in the HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')
    print(f"I found {len(tables)} tables on the page.")
    
    for index, table in enumerate(tables):
        print(f"\nI'm analyzing table {index + 1}:")
        
        # I try to find a table with a specific class
        if 'restable' in table.get('class', []):
            print("I found a table with the 'restable' class.")
            return table
        
        # Additional checks can be added here
            
    print("\nI couldn't find a suitable postcode table.")
    return None

def scrape_connecticut_postcodes():
    print("I'm initializing Playwright...")
    
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
                    print(f"I'm attempting to launch the browser ({attempt + 1}/{max_retries})...")
                    browser = p.chromium.launch(**launch_options)
                    print("I successfully launched the browser.")
                    break
                except Exception as e:
                    print(f"My browser launch failed: {e}")
                    if attempt < max_retries - 1:
                        print("I'll retry in 5 seconds...")
                        time.sleep(5)
                    else:
                        print("I've reached the maximum retries. I'll try Firefox instead...")
                        try:
                            browser = p.firefox.launch(**launch_options)
                            print("I successfully launched the Firefox browser.")
                            break
                        except Exception as firefox_error:
                            print(f"My Firefox launch failed: {firefox_error}")
                            print("I'll try Webkit as a last resort...")
                            try:
                                browser = p.webkit.launch(**launch_options)
                                print("I successfully launched the Webkit browser.")
                                break
                            except Exception as webkit_error:
                                print(f"My Webkit launch failed: {webkit_error}")
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
                print("I successfully created the browser context and page.")
            except Exception as e:
                print(f"I failed to create the context or page: {e}")
                if browser:
                    browser.close()
                raise
            
            # I try both URLs
            urls = [
                "https://www.geonames.org/postal-codes/US/CT/connecticut.html",
                "https://www.geonames.org/postal-codes/US/CT/"
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
                            print(f"My navigation attempt {nav_attempt + 1} failed: {nav_error}")
                            if nav_attempt < 2:
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
                    if check_for_protection(page):
                        print("\nI detected a protection page. Please solve the captcha if present.")
                        input("Press Enter once you've solved the captcha...")
                        time.sleep(2)  # I wait after the captcha
                    
                    # I save the page source for debugging
                    html_content = page.content()
                    debug_dir = "debug_output"
                    os.makedirs(debug_dir, exist_ok=True)
                    with open(f"{debug_dir}/page_source_{urls.index(url)}.html", "w", encoding="utf-8") as f:
                        f.write(html_content)
                    print(f"I saved the page source to '{debug_dir}/page_source_{urls.index(url)}.html'")
                    
                    # I take a screenshot for debugging
                    page.screenshot(path=f"{debug_dir}/screenshot_{urls.index(url)}.png")
                    print(f"I saved the screenshot to '{debug_dir}/screenshot_{urls.index(url)}.png'")
                    
                    # I find the postal code table
                    postal_table = find_postcode_table(html_content)
                    if postal_table:
                        break  # I exit the URL loop if I find the table
                        
                except Exception as e:
                    print(f"I encountered an error processing the URL {url}: {e}")
                    continue
            
            if not postal_table:
                print("\nI couldn't find the postal code table in any of the URLs.")
                browser.close()
                return
                
            print("\nI found the postcode table. I'm processing the data...")
            
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
            region_id = get_id_by_column("regions", "name", "Connecticut")
            if region_id is None:
                print("I'm creating a Connecticut region entry...")
                region_id = insert_and_get_id("regions", {"name": "Connecticut", "code": "CT", "country_id": country_id}, "name")
                if region_id is None:
                    print("I failed to create the region entry. I'm aborting.")
                    browser.close()
                    return
            
            # I process the rows
            rows = postal_table.find_all("tr")[1:]  # I skip the header
            success_count = 0
            error_count = 0
            
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 3:  # I ensure there are at least 3 columns
                    # The actual table structure has index in col[0], place in col[1], code in col[2]
                    # index = cols[0].text.strip()      # First column is the index number (optional to store)
                    place_name = cols[1].text.strip() # Second column is the place name (e.g., "Avon")
                    postcode = cols[2].text.strip()   # Third column is the postal code (e.g., "06001")
                    
                    if place_name and postcode:
                        print(f"I'm processing: {place_name} - {postcode}")
                        data = {
                            "code": postcode,         # I put the postal code in the "code" field
                            "place_name": place_name, # I put the place name in the "place_name" field
                            "region_id": region_id,
                        }
                        if insert_postcode_data(data):
                            success_count += 1
                        else:
                            error_count += 1
                else:
                    print(f"I'm skipping a row. I expected 3+ columns, but I found {len(cols)}.")
            
            # --- This block should be OUTSIDE the loop ---
            print(f"\nI've completed the scraping:")
            print(f"I successfully processed: {success_count} postcodes.")
            print(f"I encountered errors with: {error_count} postcodes.")
            
            browser.close()
    except Exception as e:
        print(f"I encountered an error: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    scrape_connecticut_postcodes()
