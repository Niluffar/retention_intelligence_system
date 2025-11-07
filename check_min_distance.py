"""
Check min_booking_distance_km column in core_user table
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.db_connectors import PostgresConnector


def main():
    """Check min_booking_distance_km column"""
    print("\n" + "=" * 70)
    print("CHECKING MIN_BOOKING_DISTANCE_KM COLUMN")
    print("=" * 70)

    pg = PostgresConnector()

    # 1. Check if column exists
    print("\n1. CHECKING COLUMN EXISTS:")
    with pg.get_cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'ris'
              AND table_name = 'core_user'
              AND column_name = 'min_booking_distance_km';
        """)
        result = cursor.fetchone()

        if result:
            print(f"   [OK] Column exists: {result['column_name']} ({result['data_type']})")
        else:
            print("   [ERROR] Column NOT found!")
            return

    # 2. Check data statistics
    print("\n2. DATA STATISTICS:")
    with pg.get_cursor() as cursor:
        cursor.execute("""
            SELECT
                COUNT(*) as total_users,
                COUNT(min_booking_distance_km) as users_with_min_distance,
                ROUND(AVG(min_booking_distance_km), 2) as avg_min_distance,
                ROUND(MIN(min_booking_distance_km), 2) as min_distance,
                ROUND(MAX(min_booking_distance_km), 2) as max_distance,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY min_booking_distance_km) as median_min_distance
            FROM ris.core_user;
        """)
        result = cursor.fetchone()

        print(f"   Total users: {result['total_users']:,}")
        print(f"   Users with min_booking_distance: {result['users_with_min_distance']:,}")
        print(f"   Avg min distance: {result['avg_min_distance']} km")
        print(f"   Min distance: {result['min_distance']} km")
        print(f"   Max distance: {result['max_distance']} km")
        print(f"   Median min distance: {result['median_min_distance']} km")

    # 3. Compare min vs avg vs home distance
    print("\n3. COMPARISON: MIN vs AVG vs HOME DISTANCE:")
    with pg.get_cursor() as cursor:
        cursor.execute("""
            SELECT
                COUNT(*) as users_with_all_data,
                ROUND(AVG(min_booking_distance_km), 2) as avg_min,
                ROUND(AVG(avg_booking_distance_km), 2) as avg_avg,
                ROUND(AVG(distance_home_to_club_km), 2) as avg_home,
                COUNT(CASE WHEN min_booking_distance_km < distance_home_to_club_km THEN 1 END) as min_closer_than_home,
                ROUND(
                    COUNT(CASE WHEN min_booking_distance_km < distance_home_to_club_km THEN 1 END)::numeric /
                    COUNT(*)::numeric * 100, 1
                ) as pct_min_closer_than_home
            FROM ris.core_user
            WHERE min_booking_distance_km IS NOT NULL
              AND avg_booking_distance_km IS NOT NULL
              AND distance_home_to_club_km IS NOT NULL;
        """)
        result = cursor.fetchone()

        print(f"   Users with complete data: {result['users_with_all_data']:,}")
        print(f"   Average min distance: {result['avg_min']} km")
        print(f"   Average avg distance: {result['avg_avg']} km")
        print(f"   Average home distance: {result['avg_home']} km")
        print(f"\n   Users where min < home: {result['min_closer_than_home']:,} ({result['pct_min_closer_than_home']}%)")
        print(f"   -> This suggests they have office/work near club!")

    # 4. Sample users with interesting patterns
    print("\n4. SAMPLE USERS:")
    with pg.get_cursor() as cursor:
        cursor.execute("""
            SELECT
                user_id,
                nickname,
                default_club_corr,
                ROUND(min_booking_distance_km, 2) as min_dist,
                ROUND(avg_booking_distance_km, 2) as avg_dist,
                ROUND(distance_home_to_club_km, 2) as home_dist,
                ROUND(distance_variability, 2) as variability,
                location_data_quality
            FROM ris.core_user
            WHERE min_booking_distance_km IS NOT NULL
              AND distance_home_to_club_km IS NOT NULL
              AND min_booking_distance_km < distance_home_to_club_km
            ORDER BY (distance_home_to_club_km - min_booking_distance_km) DESC
            LIMIT 5;
        """)
        results = cursor.fetchall()

        print("\n   Top 5 users with biggest difference (home - min):")
        print("   (Suggests they book from work/office, not from home)")
        for row in results:
            diff = row['home_dist'] - row['min_dist']
            print(f"\n   {row['nickname'] or 'Anonymous'} @ {row['default_club_corr']}")
            print(f"     Min: {row['min_dist']} km | Avg: {row['avg_dist']} km | Home: {row['home_dist']} km")
            print(f"     Difference: {diff:.2f} km | Variability: {row['variability']} km")
            print(f"     Quality: {row['location_data_quality']}")

    print("\n" + "=" * 70)
    print("CHECK COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
