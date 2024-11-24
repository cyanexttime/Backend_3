from pymongo import MongoClient
from PIL import Image
import io


def connect_to_mongodb():
    """Connect to MongoDB and return the database instance."""
    client = MongoClient("mongodb://localhost:27017")
    db = client["osm_data"]  # Adjust database name if needed
    return db


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


def display_map_image(image):
    """Display a PIL Image."""
    image.show()


def main():
    # Connect to MongoDB
    db = connect_to_mongodb()

    # Retrieve and display the map image
    location_name = "Ho Chi Minh City, Vietnam"
    tile_image = retrieve_map_tile_from_mongodb(db, location_name)
    display_map_image(tile_image)


if __name__ == "__main__":
    main()
