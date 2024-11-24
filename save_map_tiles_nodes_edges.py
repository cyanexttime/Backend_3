import webbrowser
import osmnx as ox
from pymongo import MongoClient
from shapely.geometry import mapping
import folium

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Adjust the host and port if needed
db = client["osm_data_1"]  # Database name

# Define the place
place_name = "Ho Chi Minh, Vietnam"

# Download a street network
print(f"Downloading data for {place_name}...")
G = ox.graph_from_place(place_name, network_type="drive")

# Convert to GeoDataFrames
print("Converting data to GeoDataFrames...")
nodes, edges = ox.graph_to_gdfs(G)

# Reset index and convert geometries to GeoJSON format
print("Preparing nodes data...")
nodes["geometry"] = nodes["geometry"].apply(mapping)
nodes_data = nodes.reset_index().to_dict(orient="records")

print("Preparing edges data...")
edges["geometry"] = edges["geometry"].apply(mapping)
edges_data = edges.reset_index().to_dict(orient="records")

# Save nodes and edges to MongoDB
print("Saving nodes to MongoDB...")
db.nodes.insert_many(nodes_data)

print("Saving edges to MongoDB...")
db.edges.insert_many(edges_data)

print("Data saved successfully!")

# Get the geographical center of the place
place_center = ox.geocode(place_name)

# Create a folium map
map_place = folium.Map(location=place_center, zoom_start=13, tiles="OpenStreetMap")

# Add nodes to the map
for node in nodes_data:
    folium.CircleMarker(
        location=[node["y"], node["x"]],  # Latitude and longitude
        radius=2,
        color="blue",
        fill=True,
        fill_color="blue",
        fill_opacity=0.6,
    ).add_to(map_place)

# Add edges to the map
for edge in edges_data:
    if "geometry" in edge:
        coords = edge["geometry"]["coordinates"]
        folium.PolyLine(
            locations=[(lat, lon) for lon, lat in coords],
            color="red",
            weight=1,
            opacity=0.7,
        ).add_to(map_place)

# Save the map as an HTML file
output_file = (
    f"{place_name.replace(', ', '_').replace(' ', '_').lower()}_nodes_edges.html"
)
map_place.save(output_file)
print(f"Map saved as '{output_file}'. Open it in your browser to view.")
webbrowser.open(output_file)
