import base64
import io
import os
from PIL import Image
import osmnx as ox
import networkx as nx
from pymongo import MongoClient
import bson
from shapely.geometry import shape
import matplotlib.pyplot as plt
from shapely.geometry import LineString
import geopandas as gpd
from geopy.geocoders import Nominatim
from bson.binary import Binary


def connect_to_mongodb():
    """Connect to MongoDB and return the database instance."""
    client = MongoClient("mongodb://localhost:27017")
    db = client["osm_data"]  # Adjust database name if needed
    return db


def load_data_from_mongodb(db):
    """Load nodes and edges from MongoDB and return them as lists."""
    nodes = list(db.nodes.find())
    edges = list(db.edges.find())
    return nodes, edges


def retrieve_map_tile_from_mongodb(db, location_name):
    collection = db["maps"]
    """Retrieve a map tile from MongoDB based on location name."""
    # Query MongoDB collection for the map tile
    tile = collection.find_one({"location_name": location_name})

    if not tile:
        raise ValueError(f"No map tile found for {location_name}")

    # Extract the image data from the document
    image_data = tile["image_data"]

    # Convert the binary data to a PIL Image
    tile_image = Image.open(io.BytesIO(image_data))
    return tile_image


def reconstruct_graph(nodes, edges):
    """Reconstruct the graph from nodes and edges, and save to a file."""
    G = nx.MultiDiGraph()
    G.graph["crs"] = "EPSG:4326"  # WGS84

    # Add nodes
    for node in nodes:
        geometry = shape(node.pop("geometry"))
        G.add_node(node["osmid"], **node, geometry=geometry)

    # Add edges
    for edge in edges:
        geometry = shape(edge.pop("geometry"))
        G.add_edge(edge["u"], edge["v"], **edge, geometry=geometry)

    print("Graph reconstructed successfully!")

    return G

    # def load_graph_from_file(input_file):
    """Load a graph from a file and reconstruct geometries."""
    try:
        G = nx.read_graphml(input_file)

        # Convert geometry back to Shapely objects if stored as GeoJSON-like mappings
        for node, data in G.nodes(data=True):
            if "geometry" in data:
                data["geometry"] = shape(
                    data["geometry"]
                )  # Convert from GeoJSON-like dict to Shapely geometry

        for u, v, key, data in G.edges(data=True, keys=True):
            if "geometry" in data:
                data["geometry"] = shape(
                    data["geometry"]
                )  # Convert from GeoJSON-like dict to Shapely geometry

        print(f"Graph loaded successfully from {input_file}")
        return G
    except Exception as e:
        print(f"Failed to load graph: {e}")
        return None

    # def initialize_graph(nodes, edges, file_path="graph.graphml"):
    """
    Initialize the graph: load from file if it exists, otherwise reconstruct and save it.
    """
    if os.path.exists(file_path):
        print(f"Loading graph from {file_path}...")
        graph = load_graph_from_file(file_path)
    else:
        print("Graph file not found. Reconstructing graph...")
        graph = reconstruct_graph(nodes, edges, file_path)
    return graph

    # def preprocess_graph_data(G):
    """
    Preprocess graph data to ensure compatibility with GraphML.
    Convert unsupported data types (e.g., ObjectId) to strings.
    """
    for node, data in G.nodes(data=True):
        for key, value in data.items():
            if isinstance(value, dict) or isinstance(value, list):
                # Convert complex types to strings
                data[key] = str(value)
            elif isinstance(value, bson.ObjectId):  # Specific handling for ObjectId
                data[key] = str(value)

    for u, v, key, data in G.edges(data=True, keys=True):
        for key, value in data.items():
            if isinstance(value, dict) or isinstance(value, list):
                data[key] = str(value)
            elif isinstance(value, bson.ObjectId):  # Specific handling for ObjectId
                data[key] = str(value)

    # def save_graph_to_file(graph, filename="graph.graphml"):
    #     """Save the graph to a GraphML file."""
    #     nx.write_graphml(
    #         graph, filename
    #     )  # Use write_graphml() to save the graph in GraphML format
    #     print(f"Graph saved to {filename}.")

    # def load_graph_from_file(filename="graph.graphml"):
    #     """Load the graph from a GraphML file."""
    #     if os.path.exists(filename):
    #         graph = nx.read_graphml(
    #             filename
    #         )  # Use read_graphml() to load the graph from GraphML
    #         print(f"Graph loaded from {filename}.")
    #         return graph
    #     else:
    #         print(f"{filename} does not exist.")
    #         return None

    # def get_graph(db, filename="graph.graphml"):
    #     """Get the graph either from a file or by reconstructing it from MongoDB."""
    #     # Try loading the graph from the file first
    #     graph = load_graph_from_file(filename)

    #     if graph is None:
    #         # If the graph doesn't exist, reconstruct it from MongoDB
    #         print("Reconstructing the graph from MongoDB...")
    #         nodes, edges = load_data_from_mongodb(db)
    #         graph = reconstruct_graph(nodes, edges)

    #         # Save the reconstructed graph locally for future use
    #         save_graph_to_file(graph, filename)

    #     return graph


def find_shortest_path(G, origin_coords, destination_coords):
    """Find the shortest path between two coordinates using Dijkstra's algorithm."""
    # Find nearest nodes to origin and destination
    origin_node = ox.distance.nearest_nodes(G, X=origin_coords[1], Y=origin_coords[0])
    destination_node = ox.distance.nearest_nodes(
        G, X=destination_coords[1], Y=destination_coords[0]
    )

    print(f"Origin Node: {origin_node}, Destination Node: {destination_node}")

    # Define the heuristic: straight-line (Euclidean) distance from current node to destination
    def heuristic(u, v):
        (lat_u, lon_u) = G.nodes[u]["y"], G.nodes[u]["x"]
        (lat_v, lon_v) = G.nodes[v]["y"], G.nodes[v]["x"]
        return ox.distance.great_circle_vec(
            lat_u, lon_u, lat_v, lon_v
        )  # straight-line distance in meters

    # Calculate shortest path using A* algorithm
    path = nx.astar_path(
        G,
        source=origin_node,
        target=destination_node,
        weight="length",
        heuristic=heuristic,
    )
    return path


def visualize_route(G, path):
    """Visualize the route on the graph, focusing on the route area."""
    fig, ax = ox.plot_graph_route(
        G,
        path,
        route_color="red",
        route_linewidth=3,
        route_alpha=0.7,
        show=False,
        close=False,
    )

    # Get the bounding box around the route
    nodes = [G.nodes[node] for node in path]
    lats = [data["y"] for data in nodes]
    lons = [data["x"] for data in nodes]

    # Set limits to focus on the route
    margin = 0.01  # Add a margin to the bounding box
    ax.set_xlim(min(lons) - margin, max(lons) + margin)
    ax.set_ylim(min(lats) - margin, max(lats) + margin)

    plt.show()


def visualize_route_with_map(G, path, db, location_name):
    """Visualize the route on top of the map tile."""
    # Step 1: Retrieve the map tile from MongoDB
    tile_image = retrieve_map_tile_from_mongodb(db, location_name)

    # Step 2: Plot the map tile as the background
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.imshow(tile_image, extent=(0, 1, 0, 1))  # Adjust extent based on the map size

    # Step 3: Extract the route coordinates from the graph path
    route_coords = [(G.nodes[node]["x"], G.nodes[node]["y"]) for node in path]
    lons, lats = zip(*route_coords)

    # Step 4: Overlay the route on the map tile
    ax.plot(lons, lats, color="red", linewidth=2, alpha=0.8)

    # Step 5: Set titles and labels
    plt.title(f"Route Visualization for {location_name}")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()


# Example usage
# visualize_route(G, path)


# def show_graph(G):
#     """Visualize the graph."""
#     # Extract positions from node attributes (longitude and latitude)
#     pos = {node: (data["x"], data["y"]) for node, data in G.nodes(data=True)}

#     # Draw the graph
#     plt.figure(figsize=(10, 8))
#     nx.draw(
#         G, pos, node_size=10, node_color="blue", edge_color="gray", with_labels=False
#     )
#     plt.title("Reconstructed Graph")
#     plt.xlabel("Longitude")
#     plt.ylabel("Latitude")
#     plt.show()


# def save_route_as_geojson(G, path, output_file):
#     """Save the route as a GeoJSON file."""
#     # Extract route geometry
#     route_edges = [G[u][v][0]["geometry"] for u, v in zip(path[:-1], path[1:])]
#     route_geometry = LineString(
#         [point for geom in route_edges for point in geom.coords]
#     )

#     # Create GeoDataFrame and save as GeoJSON
#     route_gdf = gpd.GeoDataFrame({"geometry": [route_geometry]})
#     route_gdf.to_file(output_file, driver="GeoJSON")
#     print(f"Route saved to {output_file}")


def main():
    # Step 1: Connect to MongoDB
    db = connect_to_mongodb()
    # Step 2: Load data from MongoDB
    nodes, edges = load_data_from_mongodb(db)

    # Step 3: Reconstruct the graph
    G = reconstruct_graph(nodes, edges)

    # Step 4: Define origin and destination coordinates
    origin_coords = (10.882311, 106.782409)  # Replace with your starting location
    destination_coords = (10.759388, 106.667391)
    # Step 5: Find shortest path
    path = find_shortest_path(G, origin_coords, destination_coords)
    # Step 6: Visualize or save the route
    visualize_route(G, path)
    # visualize_route_with_map(G, path, db, "Ho Chi Minh City, Vietnam")
    # save_route_as_geojson(G, path, "route.geojson")


if __name__ == "__main__":
    main()
