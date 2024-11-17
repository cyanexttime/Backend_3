import osmnx as ox
import networkx as nx
from pymongo import MongoClient
from shapely.geometry import shape
import matplotlib.pyplot as plt
from shapely.geometry import LineString
import geopandas as gpd


def connect_to_mongodb():
    """Connect to MongoDB and return the database instance."""
    client = MongoClient("mongodb://localhost:27017/")
    db = client["osm_data"]  # Adjust database name if needed
    return db


def load_data_from_mongodb(db):
    """Load nodes and edges from MongoDB and return them as lists."""
    nodes = list(db.nodes.find())
    edges = list(db.edges.find())
    return nodes, edges


def reconstruct_graph(nodes, edges):
    """Reconstruct the graph from nodes and edges."""
    G = nx.MultiDiGraph()

    # Set the CRS
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


def find_shortest_path(G, origin_coords, destination_coords):
    """Find the shortest path between two coordinates using Dijkstra's algorithm."""
    # Find nearest nodes to origin and destination
    origin_node = ox.distance.nearest_nodes(G, X=origin_coords[1], Y=origin_coords[0])
    destination_node = ox.distance.nearest_nodes(
        G, X=destination_coords[1], Y=destination_coords[0]
    )

    print(f"Origin Node: {origin_node}, Destination Node: {destination_node}")

    # Calculate shortest path using Dijkstra's algorithm
    path = nx.dijkstra_path(
        G, source=origin_node, target=destination_node, weight="length"
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
        show=False,  # Do not display immediately
        close=False,  # Keep the plot open for further customization
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
    origin_coords = (10.86090, 106.79403)  # Replace with your starting location
    destination_coords = (10.87041, 106.75372)  # Replace with your destination

    # Step 5: Find shortest path
    path = find_shortest_path(G, origin_coords, destination_coords)

    # Step 6: Visualize or save the route
    visualize_route(G, path)
    # save_route_as_geojson(G, path, "route.geojson")


if __name__ == "__main__":
    main()
