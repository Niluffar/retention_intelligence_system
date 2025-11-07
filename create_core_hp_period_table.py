"""
Create ris.core_hp_period table
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.db_connectors import PostgresConnector


def main():
    """Create core_hp_period table"""
    print("\n" + "=" * 70)
    print("CREATING CORE_HP_PERIOD TABLE")
    print("=" * 70)

    pg = PostgresConnector()

    # Read SQL schema
    schema_file = Path(__file__).parent / 'sql' / 'schemas' / '03_core_hp_period.sql'

    print(f"\n1. Reading schema from: {schema_file}")

    if not schema_file.exists():
        print(f"   [ERROR] Schema file not found: {schema_file}")
        return

    with open(schema_file, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    # Execute schema
    print("\n2. Executing schema SQL...")

    try:
        with pg.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(schema_sql)
                conn.commit()
        print("   [OK] Table created successfully")
    except Exception as e:
        print(f"   [ERROR] Failed to create table: {str(e)}")
        return

    # Verify table exists
    print("\n3. Verifying table...")

    if pg.table_exists('core_hp_period'):
        print("   [OK] Table ris.core_hp_period exists")

        # Get row count
        with pg.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as cnt FROM ris.core_hp_period;")
            count = cursor.fetchone()['cnt']
            print(f"   [OK] Current rows: {count:,}")
    else:
        print("   [ERROR] Table verification failed")
        return

    print("\n" + "=" * 70)
    print("TABLE CREATION COMPLETE")
    print("=" * 70)
    print("\nNext step: Run populate_core_hp_period.py to populate the table")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
