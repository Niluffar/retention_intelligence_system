"""
Create core_user table in RIS schema
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.db_connectors import PostgresConnector


def main():
    """Create core_user table"""
    print("\n" + "=" * 70)
    print("CREATING CORE_USER TABLE")
    print("=" * 70)

    pg = PostgresConnector()

    # Check if RIS schema exists
    print("\n1. Checking RIS schema...")
    with pg.get_cursor() as cursor:
        cursor.execute("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name = 'ris';
        """)
        schema_exists = cursor.fetchone()

    if not schema_exists:
        print("   ERROR: RIS schema does not exist!")
        print("   Please run: python create_schema.py first")
        return

    print("   RIS schema exists")

    # Execute DDL
    print("\n2. Creating core_user table...")
    sql_file = Path(__file__).parent / 'sql' / 'schemas' / '02_core_user.sql'

    try:
        pg.execute_script(str(sql_file))
        print("   SUCCESS: core_user table created!")
    except Exception as e:
        print(f"   ERROR: Failed to create table")
        print(f"   {str(e)}")
        return

    # Verify table creation
    print("\n3. Verifying table...")
    if pg.table_exists('core_user', 'ris'):
        print("   Table exists: ris.core_user")

        # Get column count
        with pg.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_schema = 'ris'
                  AND table_name = 'core_user';
            """)
            col_count = cursor.fetchone()['count']
            print(f"   Columns: {col_count}")

            # Get column names
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'ris'
                  AND table_name = 'core_user'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()

            print(f"\n   Column details:")
            print("   " + "-" * 66)

            # Group by category
            basic = []
            physical = []
            location_club = []
            social = []
            fitness = []
            heropass = []
            location_metrics = []
            metadata = []

            for col in columns:
                col_name = col['column_name']
                col_type = col['data_type']

                if col_name in ['user_id', 'nickname', 'firstname', 'lastname', 'gender', 'birthdate', 'age', 'age_band', 'phonenumber', 'user_created_at']:
                    basic.append((col_name, col_type))
                elif col_name in ['weight_kg', 'height_cm', 'fat_pct_latest', 'bmi_latest']:
                    physical.append((col_name, col_type))
                elif col_name in ['default_club_corr', 'city']:
                    location_club.append((col_name, col_type))
                elif col_name in ['in_clan', 'friends_cnt', 'feed_posts_total']:
                    social.append((col_name, col_type))
                elif col_name in ['active_lifestyle', 'bodytype', 'fitness_goal']:
                    fitness.append((col_name, col_type))
                elif 'hp' in col_name or 'trial' in col_name or col_name == 'ever_hp':
                    heropass.append((col_name, col_type))
                elif 'home' in col_name or 'distance' in col_name or 'location' in col_name or 'commute' in col_name or col_name == 'is_home_nearby':
                    location_metrics.append((col_name, col_type))
                else:
                    metadata.append((col_name, col_type))

            print("   BASIC PROFILE:")
            for name, dtype in basic:
                print(f"     - {name:<30} {dtype}")

            print("\n   PHYSICAL METRICS:")
            for name, dtype in physical:
                print(f"     - {name:<30} {dtype}")

            print("\n   LOCATION & CLUB:")
            for name, dtype in location_club:
                print(f"     - {name:<30} {dtype}")

            print("\n   SOCIAL:")
            for name, dtype in social:
                print(f"     - {name:<30} {dtype}")

            print("\n   FITNESS PROFILE:")
            for name, dtype in fitness:
                print(f"     - {name:<30} {dtype}")

            print("\n   HEROPASS & TRIAL:")
            for name, dtype in heropass:
                print(f"     - {name:<30} {dtype}")

            print("\n   LOCATION METRICS (from MongoDB):")
            for name, dtype in location_metrics:
                print(f"     - {name:<30} {dtype}")

            print("\n   METADATA:")
            for name, dtype in metadata:
                print(f"     - {name:<30} {dtype}")

            # Get indexes
            cursor.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'ris'
                  AND tablename = 'core_user';
            """)
            indexes = cursor.fetchall()

            print(f"\n   Indexes ({len(indexes)}):")
            for idx in indexes:
                print(f"     - {idx['indexname']}")

    else:
        print("   ERROR: Table was not created!")
        return

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("SUCCESS: core_user table created successfully!")
    print(f"Schema: ris")
    print(f"Table: core_user")
    print(f"Columns: {col_count}")
    print(f"Indexes: {len(indexes)}")

    print("\nNext steps:")
    print("1. Create ETL pipeline to populate table from:")
    print("   - PostgreSQL: raw.user, raw.club, etc.")
    print("   - MongoDB: userslocations")
    print("2. Run your SQL query to generate source data")
    print("3. Merge with location metrics CSV")
    print("4. Insert into ris.core_user")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
