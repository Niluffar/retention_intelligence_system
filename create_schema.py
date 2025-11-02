"""
Simple script to create RIS schema in PostgreSQL
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.db_connectors import PostgresConnector


def main():
    """Create RIS schema"""
    print("\nCreating RIS schema in PostgreSQL\n")
    print("=" * 60)

    pg = PostgresConnector()

    # Create schema
    sql_file = Path(__file__).parent / 'sql' / 'schemas' / '01_create_schema.sql'

    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql = f.read()

        with pg.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)

        print("SUCCESS: RIS schema created!")

        # Verify
        with pg.get_cursor() as cursor:
            cursor.execute("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = 'ris';
            """)
            result = cursor.fetchone()

            if result:
                print("VERIFIED: Schema 'ris' exists in database")
            else:
                print("WARNING: Schema not found after creation")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

    print("=" * 60)


if __name__ == "__main__":
    main()
