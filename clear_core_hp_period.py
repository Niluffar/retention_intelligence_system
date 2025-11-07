"""
Clear core_hp_period table
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.db_connectors import PostgresConnector


def main():
    """Clear all data from core_hp_period table"""
    print("\n" + "=" * 70)
    print("CLEARING CORE_HP_PERIOD TABLE")
    print("=" * 70)

    pg = PostgresConnector()

    # Check current count
    with pg.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as cnt FROM ris.core_hp_period;")
        count_before = cursor.fetchone()['cnt']

    print(f"\nCurrent rows in table: {count_before:,}")

    if count_before == 0:
        print("\nTable is already empty. Nothing to clear.")
        print("=" * 70 + "\n")
        return

    # Clear table
    print("\nClearing table...")

    try:
        with pg.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE ris.core_hp_period;")
                conn.commit()
        print("   SUCCESS: Table cleared")
    except Exception as e:
        print(f"   ERROR: {str(e)}")
        return

    # Verify
    with pg.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as cnt FROM ris.core_hp_period;")
        count_after = cursor.fetchone()['cnt']

    print(f"\nRows after clearing: {count_after:,}")

    print("\n" + "=" * 70)
    print("CLEARED SUCCESSFULLY")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
