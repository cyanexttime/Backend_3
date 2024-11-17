import osmnx as ox

# Download a street network for a specific place
G = ox.graph_from_place("Ho Chi Minh, Vietnam", network_type="drive")

# Convert to GeoDataFrames
nodes, edges = ox.graph_to_gdfs(G)
