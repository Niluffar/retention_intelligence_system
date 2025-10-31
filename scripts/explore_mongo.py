"""
Quick script to explore MongoDB collections and schemas
Run this first to understand the data structure
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.db_connectors import get_mongo_connector
from src.data_engineering.mongo_extractor import MongoExtractor
import json


def main():
    """Explore MongoDB collections"""
    print("=" * 60)
    print("MongoDB Data Explorer")
    print("=" * 60)

    # Connect
    print("\n1. Connecting to MongoDB...")
    try:
        mongo = get_mongo_connector(config_path='config/config.yaml')
        print(f"   ✓ Connected to database: {mongo.database_name}")
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        return

    # List collections
    print("\n2. Listing collections...")
    collections = mongo.list_collections()
    print(f"   Found {len(collections)} collections:")

    for coll in collections:
        count = mongo.get_collection(coll).count_documents({})
        print(f"      - {coll}: {count:,} documents")

    # Ask user which collection to explore
    print("\n3. Schema exploration")
    collection_name = input("   Enter collection name to explore (or 'skip'): ").strip()

    if collection_name and collection_name != 'skip':
        if collection_name in collections:
            print(f"\n   Analyzing schema for '{collection_name}'...")
            extractor = MongoExtractor(mongo)
            schema = extractor.explore_schema(collection_name, sample_size=1000)

            print(f"\n   Schema for '{collection_name}':")
            print("   " + "=" * 56)

            for field, info in schema.items():
                print(f"\n   Field: {field}")
                print(f"      Type: {info['type']}")
                print(f"      Sample values: {info['sample_values'][:3]}")

            # Save to file
            output_file = f"data/schemas/{collection_name}_schema.json"
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(schema, f, indent=2, default=str)

            print(f"\n   ✓ Schema saved to: {output_file}")
        else:
            print(f"   ✗ Collection '{collection_name}' not found")

    # Close connection
    mongo.close()
    print("\n" + "=" * 60)
    print("Exploration completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
