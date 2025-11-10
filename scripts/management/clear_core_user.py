

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.db_connectors import PostgresConnector


def main():
    """Clear core_user table"""
    print("\n" + "=" * 70)
    print("CLEARING CORE_USER TABLE")
    

    pg = PostgresConnector()

        with pg.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as cnt FROM ris.core_user;")
        current_count = cursor.fetchone()['cnt']
        print(f"\nCurrent rows in table: {current_count:,}")

    if current_count == 0:
        print("Table is already empty.")
        return

    # Clear table
    print("\nClearing table...")
    with pg.get_cursor() as cursor:
        cursor.execute("TRUNCATE TABLE ris.core_user;")
        print("   SUCCESS: Table cleared")

        with pg.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as cnt FROM ris.core_user;")
        new_count = cursor.fetchone()['cnt']
        print(f"\nRows after clearing: {new_count:,}")

    print("\n" + "=" * 70)
    print("CLEARED SUCCESSFULLY")
    


if __name__ == "__main__":
    main()
