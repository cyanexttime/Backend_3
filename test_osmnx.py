import os
import osmnx as ox
import networkx as nx

# Download a street network for Ho Chi Minh, Vietnam
G = ox.graph_from_place("Ho Chi Minh, Vietnam", network_type="drive")

# Save the graph as a .osm file (XML format)
xml_file = "ho_chi_minh.xml"
ox.save_graph_xml(G, xml_file)

# Now, convert the .osm file to .osm.pbf format using osmium tool
os.system(f"osmium convert {xml_file} -o ho_chi_minh.osm.pbf")
