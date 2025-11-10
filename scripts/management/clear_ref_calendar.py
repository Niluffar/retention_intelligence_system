

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.db_connectors import PostgresConnector


def main():
    """Clear ref_calendar table"""
    print("\n" + "=" * 70)
    print("CLEARING REF_CALENDAR TABLE")
    

    pg = PostgresConnector()

        if not pg.table_exists('ref_calendar'):
        print("\n[ERROR] Table ris.ref_calendar does not exist!")
        return

        with pg.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM ris.ref_calendar;")
        result = cursor.fetchone()
        row_count = result['count']

    print(f"\nCurrent rows in table: {row_count:,}")

    if row_count == 0:
        print("Table is already empty.")
        return

    # Confirm deletion
    response = input(f"\nAre you sure you want to delete {row_count:,} rows? (yes/no): ")
    if response.lower() != 'yes':
        print("Aborted.")
        return

    # Truncate table
    print("\nTruncating table...")
    with pg.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE ris.ref_calendar;")

        with pg.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM ris.ref_calendar;")
        result = cursor.fetchone()
        new_count = result['count']

    print(f"[SUCCESS] Table cleared. New row count: {new_count}")

    print("\n" + "=" * 70)
    print("CLEAR COMPLETE")
    


if __name__ == "__main__":
    main()
