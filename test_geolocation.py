import requests
import time


def geocode_with_osm(place_name):
    """
    Geocode a place name using OpenStreetMap's Nominatim API.
    """
    # Define the Nominatim API URL
    url = "https://nominatim.openstreetmap.org/search"

    # Define parameters for the search request
    params = {
        "q": place_name,  # Place name to geocode
        "format": "json",  # Response format
        "addressdetails": 1,  # Include detailed address info
        "limit": 1,  # Limit to 1 result
        "nojson": 1,  # To avoid the raw JSON result, but optional
    }

    # Send GET request to Nominatim API
    try:
        response = requests.get(url, params=params)
        data = response.json()  # Parse the response as JSON

        # Check if we have a result
        if data:
            location = data[0]
            print(f"Place: {place_name}")
            print(f"Latitude: {location['lat']}, Longitude: {location['lon']}")
            print(
                f"Full address: {location.get('display_name', 'No address available')}"
            )
        else:
            print(f"Could not find the place: {place_name}")

        # Respect Nominatim's usage policy (pause between requests)
        time.sleep(1)  # Delay to avoid hitting rate limits
    except Exception as e:
        print(f"Error during geocoding: {e}")


# Example usage
place_name = "Eiffel Tower, Paris, France"
geocode_with_osm(place_name)
