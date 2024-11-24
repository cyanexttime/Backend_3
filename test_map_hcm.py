from matplotlib import pyplot as plt
import osmnx as ox
from pymongo import MongoClient
from shapely.geometry import mapping  # Import the mapping function

import folium
from geopy.geocoders import Nominatim
import webbrowser

# # # Connect to MongoDB
# # client = MongoClient("mongodb://localhost:27017/")  # Adjust the host and port if needed
# # db = client["osm_data_1"]  # Database name

# city = "Ho Chi Minh, Viet Nam"
# buildings = ox.geometries_from_place(query=city, tags={"building": True})

# # Plot the buildings
# fig, ax = plt.subplots(figsize=(10, 10))
# buildings.plot(ax=ax, color="blue", alpha=0.7, edgecolor="black")

# # Add title and labels
# ax.set_title("Buildings in Ho Chi Minh, Viet Nam", fontsize=16)
# ax.axis("off")  # Turn off the axis

# # Display the plot
# plt.show()

# Step 1: Get city coordinates using its name
city_name = "Ho Chi Minh, Viet Nam"
geolocator = Nominatim(user_agent="city_map")
location = geolocator.geocode(city_name)

if location:
    print(f"City: {location.address}")
    print(f"Latitude: {location.latitude}, Longitude: {location.longitude}")

    # Step 2: Create the map using folium
    map_city = folium.Map(
        location=[location.latitude, location.longitude],
        zoom_start=12,
        tiles="OpenStreetMap",
    )

    # Step 3: Save the map as an HTML file
    map_city.save("city_map.html")
    print("Map saved as 'city_map.html'. Open it in your browser to view.")
    # Automatically open the map in the default web browser
    webbrowser.open("city_map.html")
else:
    print("Could not find the city. Please check the city name.")
