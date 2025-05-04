#!/usr/bin/env python3
"""
Simple test script for the GeoNames scraper.
Run this from the Post-Code-Scraper directory.
"""

import sys
import os
from scraper.geonames_scraper import scrape_geonames_postcodes

def test_scraper(state_name, city_filter=None):
    print(f"Testing scraper with state: {state_name}" + (f", city: {city_filter}" if city_filter else ""))
    print("-" * 50)
    
    # Call the scraper function
    results = scrape_geonames_postcodes(state_name=state_name, city_filter=city_filter)
    
    # Print results
    if results is None:
        print("\nScraper returned None")
    elif len(results) == 0:
        print("\nScraper returned an empty list")
    else:
        print(f"\nScraper returned {len(results)} results")
        print("\nFirst 5 results:")
        for i, result in enumerate(results[:5]):
            print(f"{i+1}. {result.get('place_name', 'N/A')} - {result.get('code', 'N/A')}")
    
    print("-" * 50)
    return results

if __name__ == "__main__":
    # Check if we're in the right directory
    if not os.path.exists("scraper/geonames_scraper.py"):
        print("Error: This script must be run from the Post-Code-Scraper directory")
        print(f"Current directory: {os.getcwd()}")
        print("Expected to find: scraper/geonames_scraper.py")
        sys.exit(1)
    
    # Get state and city from command line arguments or prompt
    if len(sys.argv) > 1:
        state_name = sys.argv[1]
        city_filter = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        print("Testing GeoNames Postcode Scraper")
        state_name = input("Enter state name (e.g., Connecticut): ").strip()
        city_input = input("Enter city name (optional, press Enter to skip): ").strip()
        city_filter = city_input if city_input else None
    
    # Run the test
    test_scraper(state_name, city_filter)