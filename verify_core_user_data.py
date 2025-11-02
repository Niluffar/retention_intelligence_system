"""
Verify data quality in core_user table
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.db_connectors import PostgresConnector


def main():
    """Verify core_user data quality"""
    print("\n" + "=" * 70)
    print("VERIFYING CORE_USER DATA QUALITY")
    print("=" * 70)

    pg = PostgresConnector()

    with pg.get_cursor() as cursor:
        # Basic counts
        print("\n1. BASIC COUNTS:")
        cursor.execute("SELECT COUNT(*) as cnt FROM ris.core_user;")
        total = cursor.fetchone()['cnt']
        print(f"   Total users: {total:,}")

        # Gender distribution
        print("\n2. GENDER DISTRIBUTION:")
        cursor.execute("""
            SELECT gender, COUNT(*) as cnt
            FROM ris.core_user
            GROUP BY gender
            ORDER BY cnt DESC;
        """)
        for row in cursor.fetchall():
            print(f"   {row['gender']}: {row['cnt']:,}")

        # Age band distribution
        print("\n3. AGE BAND DISTRIBUTION:")
        cursor.execute("""
            SELECT age_band, COUNT(*) as cnt
            FROM ris.core_user
            GROUP BY age_band
            ORDER BY
                CASE age_band
                    WHEN '<18' THEN 1
                    WHEN '18-24' THEN 2
                    WHEN '25-34' THEN 3
                    WHEN '35-44' THEN 4
                    WHEN '45-54' THEN 5
                    WHEN '55-64' THEN 6
                    WHEN '65+' THEN 7
                    ELSE 8
                END;
        """)
        for row in cursor.fetchall():
            print(f"   {row['age_band']}: {row['cnt']:,}")

        # City distribution
        print("\n4. CITY & CLUB DISTRIBUTION:")
        cursor.execute("""
            SELECT city, default_club_corr, COUNT(*) as cnt
            FROM ris.core_user
            GROUP BY city, default_club_corr
            ORDER BY city, cnt DESC;
        """)
        current_city = None
        for row in cursor.fetchall():
            if row['city'] != current_city:
                print(f"\n   {row['city']}:")
                current_city = row['city']
            print(f"     - {row['default_club_corr']}: {row['cnt']:,}")

        # HeroPass statistics
        print("\n5. HEROPASS STATISTICS:")
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN ever_hp = TRUE THEN 1 ELSE 0 END) as with_hp,
                SUM(CASE WHEN trial_before_hp = TRUE THEN 1 ELSE 0 END) as trial_before_hp
            FROM ris.core_user;
        """)
        row = cursor.fetchone()
        print(f"   Total users: {row['total']:,}")
        print(f"   With HeroPass: {row['with_hp']:,} ({row['with_hp']/row['total']*100:.1f}%)")
        print(f"   Had trial before HP: {row['trial_before_hp']:,} ({row['trial_before_hp']/row['total']*100:.1f}%)")

        # Social metrics
        print("\n6. SOCIAL METRICS:")
        cursor.execute("""
            SELECT
                SUM(CASE WHEN in_clan = TRUE THEN 1 ELSE 0 END) as in_clan_cnt,
                AVG(friends_cnt) as avg_friends,
                AVG(feed_posts_total) as avg_posts
            FROM ris.core_user;
        """)
        row = cursor.fetchone()
        print(f"   In clan: {row['in_clan_cnt']:,} ({row['in_clan_cnt']/total*100:.1f}%)")
        print(f"   Avg friends: {row['avg_friends']:.1f}")
        print(f"   Avg posts: {row['avg_posts']:.1f}")

        # Location metrics
        print("\n7. LOCATION METRICS:")
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN distance_home_to_club_km IS NOT NULL THEN 1 ELSE 0 END) as with_location,
                AVG(distance_home_to_club_km) as avg_distance,
                SUM(CASE WHEN is_home_nearby = TRUE THEN 1 ELSE 0 END) as nearby_cnt,
                AVG(commute_convenience_score) as avg_convenience
            FROM ris.core_user;
        """)
        row = cursor.fetchone()
        print(f"   Users with location data: {row['with_location']:,} ({row['with_location']/row['total']*100:.1f}%)")
        if row['avg_distance']:
            print(f"   Average distance to club: {row['avg_distance']:.2f} km")
            print(f"   Users living nearby (<2km): {row['nearby_cnt']:,} ({row['nearby_cnt']/row['with_location']*100:.1f}% of those with data)")
            print(f"   Average convenience score: {row['avg_convenience']:.4f}")

        # Data quality for location
        print("\n8. LOCATION DATA QUALITY:")
        cursor.execute("""
            SELECT
                location_data_quality,
                COUNT(*) as cnt
            FROM ris.core_user
            GROUP BY location_data_quality
            ORDER BY
                CASE location_data_quality
                    WHEN 'good' THEN 1
                    WHEN 'medium' THEN 2
                    WHEN 'poor' THEN 3
                    WHEN 'insufficient' THEN 4
                    WHEN 'no_user_data' THEN 5
                    WHEN 'none' THEN 6
                    ELSE 7
                END;
        """)
        for row in cursor.fetchall():
            print(f"   {row['location_data_quality']}: {row['cnt']:,}")

        # Physical metrics
        print("\n9. PHYSICAL METRICS (non-null counts):")
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN weight_kg IS NOT NULL THEN 1 ELSE 0 END) as with_weight,
                SUM(CASE WHEN height_cm IS NOT NULL THEN 1 ELSE 0 END) as with_height,
                SUM(CASE WHEN bmi_latest IS NOT NULL THEN 1 ELSE 0 END) as with_bmi,
                SUM(CASE WHEN fat_pct_latest IS NOT NULL THEN 1 ELSE 0 END) as with_fat_pct
            FROM ris.core_user;
        """)
        row = cursor.fetchone()
        print(f"   Weight: {row['with_weight']:,} ({row['with_weight']/row['total']*100:.1f}%)")
        print(f"   Height: {row['with_height']:,} ({row['with_height']/row['total']*100:.1f}%)")
        print(f"   BMI: {row['with_bmi']:,} ({row['with_bmi']/row['total']*100:.1f}%)")
        print(f"   Body fat %: {row['with_fat_pct']:,} ({row['with_fat_pct']/row['total']*100:.1f}%)")

        # Fitness profile
        print("\n10. FITNESS PROFILE (non-null counts):")
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN active_lifestyle IS NOT NULL THEN 1 ELSE 0 END) as with_lifestyle,
                SUM(CASE WHEN bodytype IS NOT NULL THEN 1 ELSE 0 END) as with_bodytype,
                SUM(CASE WHEN fitness_goal IS NOT NULL THEN 1 ELSE 0 END) as with_goal
            FROM ris.core_user;
        """)
        row = cursor.fetchone()
        print(f"   Active lifestyle: {row['with_lifestyle']:,} ({row['with_lifestyle']/row['total']*100:.1f}%)")
        print(f"   Body type: {row['with_bodytype']:,} ({row['with_bodytype']/row['total']*100:.1f}%)")
        print(f"   Fitness goal: {row['with_goal']:,} ({row['with_goal']/row['total']*100:.1f}%)")

    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
