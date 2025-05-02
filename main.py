# main.py
import sys
import os
import traceback
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.geonames_scraper import scrape_connecticut_postcodes

def main():
    try:
        print("--- Scraping Connecticut Postcodes ---")
        scrape_connecticut_postcodes()
        print("--- Scraping Complete ---")
        return 0
    except Exception as e:
        print(f"Fatal error in main process: {e}")
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
