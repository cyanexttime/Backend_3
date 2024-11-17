import osmnx as ox
from pymongo import MongoClient
from shapely.geometry import mapping  # Import the mapping function

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Adjust the host and port if needed
db = client["osm_data"]  # Database name

# Download a street network
print("Downloading data...")
G = ox.graph_from_place("Ho Chi Minh, Vietnam", network_type="drive")

# Convert to GeoDataFrames
print("Converting data to GeoDataFrames...")
nodes, edges = ox.graph_to_gdfs(G)

# Reset index and convert geometries to GeoJSON format
print("Preparing nodes data...")
nodes["geometry"] = nodes["geometry"].apply(
    mapping
)  # Convert Shapely geometries to GeoJSON
nodes_data = nodes.reset_index().to_dict(orient="records")

print("Preparing edges data...")
edges["geometry"] = edges["geometry"].apply(
    mapping
)  # Convert Shapely geometries to GeoJSON
edges_data = edges.reset_index().to_dict(orient="records")

# Save nodes and edges to MongoDB
print("Saving nodes to MongoDB...")
db.nodes.insert_many(nodes_data)

print("Saving edges to MongoDB...")
db.edges.insert_many(edges_data)

print("Data saved successfully!")
