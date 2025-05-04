import os
import sys # Import sys module
import traceback # Keep for error handling if needed
from typing import Dict, Any, Optional
# import pandas as pd # Removed as it seems unused

# Add parent directory to path to find config
# Do this BEFORE trying to import from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Third-party imports
try:
    from supabase import create_client, Client
    # Use the exceptions path consistently
    from postgrest.exceptions import APIError
except ImportError as e:
    print(f"Error importing Supabase modules: {e}")
    print("Make sure 'supabase-py' is installed (`pip install supabase`).")
    sys.exit(1)

# Local imports (config)
try:
    from config import SUPABASE_URL, SUPABASE_KEY
except ImportError as e:
    # Fallback to environment variables if config.py is missing
    print(f"Warning: Could not import from config.py ({e}). Attempting to use environment variables SUPABASE_URL and SUPABASE_KEY.")
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Validate Supabase credentials
if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Supabase URL and Key must be set in config.py or environment variables.")
    sys.exit(1)

def initialize_supabase_client():
    """
    Initialize Supabase client with version compatibility handling.
    Returns the initialized client or exits on failure.
    """
    # --- Debug: Print relevant environment variables ---
    print("--- Checking Environment Variables ---")
    print(f"HTTP_PROXY: {os.environ.get('HTTP_PROXY')}")
    print(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY')}")
    print(f"ALL_PROXY: {os.environ.get('ALL_PROXY')}")
    print("------------------------------------")

    # --- Debug: Test httpx directly ---
    print("--- Testing httpx connection ---")
    try:
        import httpx
        # Try connecting to the base Supabase URL or a known endpoint like auth
        # Construct the auth v1 URL which is usually accessible
        test_url = f"{SUPABASE_URL.replace('/rest/v1', '').rstrip('/')}/auth/v1"
        print(f"Attempting GET request to: {test_url}")
        with httpx.Client() as http_client:
            response = http_client.get(test_url, timeout=15.0) # Increased timeout slightly
            print(f"httpx GET request successful. Status code: {response.status_code}")
    except Exception as http_err:
        print(f"httpx direct connection failed: {http_err}")
        print("This might indicate an underlying network/proxy/SSL issue.")
    print("------------------------------")

    # --- Attempt Initialization (Simplified) ---
    try:
        print("Attempting initialization with create_client...")
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Supabase client initialized successfully using create_client.")
        return client
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")
        sys.exit(1)

# Initialize Supabase Client using the compatibility function
supabase = initialize_supabase_client()

def insert_and_get_id(table_name: str, data: Dict[str, Any], unique_column: str) -> Optional[int]:
    """
    Inserts data into a table and returns the ID of the new row.
    Handles potential API errors during insertion.
    """
    print(f"Attempting to insert into '{table_name}': {data}")
    try:
        response = supabase.table(table_name).insert(data).execute()
        if response.data:
            new_id = response.data[0].get('id')
            print(f"Successfully inserted into '{table_name}', new ID: {new_id}")
            return new_id
        else:
            print(f"Insert into '{table_name}' executed, but response has no data.")
            return get_id_by_column(table_name, unique_column, data[unique_column])
    except APIError as e:
        if e.code == '23505':  # PostgreSQL unique violation code
            print(f"Item already exists in '{table_name}'. Fetching existing ID.")
            return get_id_by_column(table_name, unique_column, data[unique_column])
        else:
            print(f"Database API Error inserting into '{table_name}': {e}")
            return None
    except Exception as e:
        print(f"An unexpected error occurred during insert into '{table_name}': {e}")
        return None

def get_id_by_column(table_name: str, column_name: str, column_value: Any, **kwargs) -> Optional[int]:
    """Gets the ID from a table based on a specific column's value."""
    print(f"Checking for ID in '{table_name}' where {column_name}='{column_value}'" + 
          (f" and {kwargs}" if kwargs else ""))
    try:
        query = supabase.table(table_name).select("id").eq(column_name, column_value)
        for key, value in kwargs.items():
            query = query.eq(key, value)
        
        response = query.limit(1).execute()
        if response.data:
            found_id = response.data[0]['id']
            print(f"Found existing ID: {found_id}")
            return found_id
        else:
            print("Item not found.")
            return None
    except APIError as e:
        print(f"Database API Error getting ID from '{table_name}': {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while getting ID from '{table_name}': {e}")
        return None

# --- Removed duplicate imports and client initialization ---
# --- Other functions like insert_and_get_id, get_id_by_column would be here ---

def insert_postcode_data(data: Dict[str, Any]) -> bool:
    """
    Inserts postcode data in the 'postcodes' table.
    If a postcode with the same 'code' already exists, it skips it.
    """
    print(f"Attempting to insert postcode: {data}")
    try:
        # Note: If the 'code' column has a UNIQUE constraint and you want to
        # UPDATE existing entries instead of skipping, use the .upsert() method:
        # supabase.table("postcodes").upsert(data, on_conflict='code').execute()

        response = supabase.table("postcodes").insert(data).execute()
        
        if hasattr(response, 'data') and response.data:
             print(f"Successfully inserted postcode: {data.get('code')}")
             return True
        elif hasattr(response, 'status_code') and 200 <= response.status_code < 300:
             print(f"Successfully inserted postcode (status code: {response.status_code}): {data.get('code')}")
             return True
        else:
             print(f"Postcode insert executed, but response indicates potential issue or no data returned.")
             print(f"Response details: {response}")
             return False

    except APIError as e:
        if e.code == '23505':  # PostgreSQL unique violation code
            print(f"Postcode '{data.get('code')}' already exists. Skipping.")
            return True  # Consider this a success since we don't need to insert it again
        elif "foreign key constraint" in str(e).lower() and "region_id" in str(e).lower():
             print(f"Error: The region_id '{data.get('region_id')}' does not exist in the 'regions' table.")
             return False
        else:
            print(f"Database API Error during postcode insert: {e}")
            print(f"Error Code: {e.code}, Message: {e.message}, Details: {e.details}, Hint: {e.hint}")
            return False
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return False

# Legacy functions maintained for backwards compatibility
def insert_country(data):
    response = supabase.table("countries").insert(data).execute()
    return response

def insert_region(data):
    response = supabase.table("regions").insert(data).execute()
    return response

def insert_postcode(data):
    response = supabase.table("postcodes").insert(data).execute()
    return response

def get_region_id(region_name, country_id):
    response = supabase.table("regions").select("id").eq("name", region_name).eq("country_id", country_id).execute()
    return response.data[0]['id'] if response.data else None

def get_country_id(country_name):
    response = supabase.table("countries").select("id").eq("name", country_name).execute()
    return response.data[0]['id'] if response.data else None

def get_all_postcodes():
    """
    Retrieves all postcodes from the database
    """
    try:
        response = supabase.table("postcodes").select("*").execute()
        if hasattr(response, 'data'):
            return response.data
        return []
    except Exception as e:
        print(f"Error retrieving postcodes: {e}")
        return []

# --- Example Usage / Test Script ---
def scrape_postcodes():
    """Ensures country and region exist, then inserts a sample postcode."""
    print("\n--- Starting Postcode Scraping Process ---")
    country_name = "USA"
    region_name = "New York"
    postcode_code = "10001"
    postcode_place = "Midtown Manhattan" # More specific example

    # 1. Ensure Country Exists and Get ID
    country_id = get_id_by_column("countries", "name", country_name)
    if country_id is None:
        print(f"Country '{country_name}' not found. Attempting to insert...")
        country_data = {"name": country_name, "code": "US"} # Example code
        country_id = insert_and_get_id("countries", country_data, "name")
        if country_id is None:
            print("Failed to get or create country ID. Aborting.")
            return # Stop if we can't get/create the country

    # 2. Ensure Region Exists and Get ID (using the verified country_id)
    region_id = get_id_by_column("regions", "name", region_name, country_id=country_id)
    if region_id is None:
        print(f"Region '{region_name}' for country_id {country_id} not found. Attempting to insert...")
        region_data = {"name": region_name, "country_id": country_id}
        region_id = insert_and_get_id("regions", region_data, "name") # Assuming name is unique per country
        if region_id is None:
            print("Failed to get or create region ID. Aborting.")
            return # Stop if we can't get/create the region

    # 3. Insert Postcode
    postcode_data = {
        "code": postcode_code,
        "place_name": postcode_place,
        "region_id": region_id
    }
    success = insert_postcode_data(postcode_data)

    if success:
        print("Postcode insertion process completed successfully (or postcode already existed).")
    else:
        print("Postcode insertion process failed.")

    print("--- Postcode Scraping Process Finished ---")

# --- Script Execution ---
if __name__ == "__main__":
    scrape_postcodes()
    
