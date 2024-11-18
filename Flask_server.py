from matplotlib import pyplot as plt
from flask import Flask, request, jsonify
import osmnx as ox
import networkx as nx
from pymongo import MongoClient
from shapely.geometry import shape
import geopandas as gpd
from shapely.geometry import LineString

app = Flask(__name__)

# Global graph variable to store the reconstructed graph
G = None


def connect_to_mongodb():
    """Connect to MongoDB and return the database instance."""
    client = MongoClient(
        "mongodb://localhost:27017/"
    )  # Change to your own mongoDB server
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


@app.route("/initialize", methods=["POST"])
def initialize_graph():
    """API to initialize the graph by loading data from MongoDB."""
    global G
    try:
        db = connect_to_mongodb()
        nodes, edges = load_data_from_mongodb(db)
        G = reconstruct_graph(nodes, edges)
        return jsonify({"message": "Graph initialized successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/shortest_path", methods=["POST"])
def shortest_path():
    """API to find the shortest path between two coordinates."""
    global G
    if G is None:
        return (
            jsonify({"error": "Graph not initialized. Please call /initialize first."}),
            400,
        )

    try:
        data = request.json
        origin_coords = tuple(data["origin_coords"])
        destination_coords = tuple(data["destination_coords"])

        # Find nearest nodes to origin and destination
        origin_node = ox.distance.nearest_nodes(
            G, X=origin_coords[1], Y=origin_coords[0]
        )
        destination_node = ox.distance.nearest_nodes(
            G, X=destination_coords[1], Y=destination_coords[0]
        )

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

        # # Calculate shortest path using Dijkstra's algorithm
        # path = nx.dijkstra_path(
        #     G, source=origin_node, target=destination_node, weight="length"
        # )

        return jsonify({"path": path}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/visualize_route", methods=["POST"])
def visualize_route():
    """API to visualize the route."""
    global G
    if G is None:
        return (
            jsonify({"error": "Graph not initialized. Please call /initialize first."}),
            400,
        )

    try:
        data = request.json
        path = data["path"]

        # Visualize the graph route
        fig, ax = ox.plot_graph_route(
            G,
            path,
            route_color="red",
            route_linewidth=3,
            route_alpha=0.7,
            show=False,  # Do not display immediately
            close=False,  # Keep the plot open for further customization
        )

        # Save the visualization to a file
        output_file = "route_visualization.png"
        fig.savefig(output_file)
        plt.close(fig)

        return jsonify({"message": f"Route visualization saved as {output_file}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/save_route_as_geojson", methods=["POST"])
def save_route_as_geojson():
    """API to save the route as a GeoJSON file."""
    global G
    if G is None:
        return (
            jsonify({"error": "Graph not initialized. Please call /initialize first."}),
            400,
        )

    try:
        data = request.json
        path = data["path"]
        output_file = data["output_file"]

        # Extract route geometry
        route_edges = [G[u][v][0]["geometry"] for u, v in zip(path[:-1], path[1:])]
        route_geometry = LineString(
            [point for geom in route_edges for point in geom.coords]
        )

        # Create GeoDataFrame and save as GeoJSON
        route_gdf = gpd.GeoDataFrame({"geometry": [route_geometry]})
        route_gdf.to_file(output_file, driver="GeoJSON")

        return jsonify({"message": f"Route saved to {output_file}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
