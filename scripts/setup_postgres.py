"""
Setup PostgreSQL schema and tables
Run this to create the RIS schema and all necessary tables
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.db_connectors import get_postgres_connector
from src.data_engineering.postgres_loader import PostgresLoader


def main():
    """Setup PostgreSQL schema"""
    print("=" * 60)
    print("PostgreSQL Schema Setup")
    print("=" * 60)

    # Connect
    print("\n1. Connecting to PostgreSQL...")
    try:
        pg = get_postgres_connector(config_path='config/config.yaml')
        loader = PostgresLoader(pg)
        print(f"   ✓ Connected to database: {pg.database}")
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        return

    # Execute SQL scripts
    sql_dir = Path('sql/schemas')

    if not sql_dir.exists():
        print(f"\n   ✗ SQL directory not found: {sql_dir}")
        return

    sql_files = sorted(sql_dir.glob('*.sql'))

    if not sql_files:
        print(f"\n   ✗ No SQL files found in {sql_dir}")
        return

    print(f"\n2. Found {len(sql_files)} SQL scripts")

    for sql_file in sql_files:
        print(f"\n   Executing: {sql_file.name}")
        try:
            loader.execute_sql_file(str(sql_file))
            print(f"      ✓ Success")
        except Exception as e:
            print(f"      ✗ Failed: {e}")
            response = input("      Continue? (y/n): ")
            if response.lower() != 'y':
                return

    print("\n3. Verifying tables...")

    # List of expected tables
    expected_tables = [
        'core_user',
        'core_hp_period',
        'fact_user_week',
        'label_hp',
        'interval_hp',
        'ref_calendar',
        'meta_feature_catalog',
        'dq_feature_stats',
        'model_importance',
        'model_calibration',
        'model_bands',
        'model_scores_daily'
    ]

    for table in expected_tables:
        if loader.table_exists(table):
            count = loader.get_table_row_count(table)
            print(f"      ✓ {table}: {count:,} rows")
        else:
            print(f"      ✗ {table}: NOT FOUND")

    print("\n" + "=" * 60)
    print("Setup completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
