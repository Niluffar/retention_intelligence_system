"""
Verify core_hp_period data quality
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.db_connectors import PostgresConnector


def main():
    """Verify core_hp_period table data quality"""
    print("\n" + "=" * 70)
    print("VERIFYING CORE_HP_PERIOD DATA QUALITY")
    print("=" * 70)

    pg = PostgresConnector()

    # 1. Basic counts
    print("\n1. BASIC COUNTS:")
    with pg.get_cursor() as cursor:
        cursor.execute("""
            SELECT
                COUNT(*) as total_periods,
                COUNT(DISTINCT user_id) as unique_users
            FROM ris.core_hp_period;
        """)
        result = cursor.fetchone()
        print(f"   Total HeroPass periods: {result['total_periods']:,}")
        print(f"   Unique users with HP: {result['unique_users']:,}")

    # 2. HP Type distribution
    print("\n2. HEROPASS TYPE DISTRIBUTION:")
    with pg.get_cursor() as cursor:
        cursor.execute("""
            SELECT
                hp_type,
                COUNT(*) as count
            FROM ris.core_hp_period
            GROUP BY hp_type
            ORDER BY count DESC;
        """)
        for row in cursor.fetchall():
            print(f"   {row['hp_type']}: {row['count']:,}")

    # 3. Club distribution
    print("\n3. CLUB DISTRIBUTION:")
    with pg.get_cursor() as cursor:
        cursor.execute("""
            SELECT
                hp_club_corr,
                COUNT(*) as count
            FROM ris.core_hp_period
            WHERE hp_club_corr IS NOT NULL
            GROUP BY hp_club_corr
            ORDER BY count DESC;
        """)
        for row in cursor.fetchall():
            print(f"   {row['hp_club_corr']}: {row['count']:,}")

    # 4. Renewal statistics
    print("\n4. RENEWAL STATISTICS:")
    with pg.get_cursor() as cursor:
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN renewed THEN 1 ELSE 0 END) as renewed_count,
                SUM(CASE WHEN NOT renewed THEN 1 ELSE 0 END) as not_renewed_count,
                ROUND(AVG(CASE WHEN renewed THEN 1.0 ELSE 0.0 END) * 100, 1) as renewal_rate
            FROM ris.core_hp_period;
        """)
        result = cursor.fetchone()
        print(f"   Total periods: {result['total']:,}")
        print(f"   Renewed: {result['renewed_count']:,} ({result['renewal_rate']}%)")
        print(f"   Not renewed: {result['not_renewed_count']:,}")

    # 5. Freeze statistics
    print("\n5. FREEZE STATISTICS:")
    with pg.get_cursor() as cursor:
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN freeze_days_total > 0 THEN 1 END) as with_freeze,
                ROUND(AVG(freeze_days_total), 1) as avg_freeze_days,
                MAX(freeze_days_total) as max_freeze_days,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY freeze_days_total) as median_freeze_days
            FROM ris.core_hp_period;
        """)
        result = cursor.fetchone()
        print(f"   Periods with freeze: {result['with_freeze']:,}")
        print(f"   Avg freeze days: {result['avg_freeze_days']}")
        print(f"   Median freeze days: {result['median_freeze_days']}")
        print(f"   Max freeze days: {result['max_freeze_days']}")

    # 6. Gap days statistics (for renewed)
    print("\n6. GAP DAYS STATISTICS (for renewed):")
    with pg.get_cursor() as cursor:
        cursor.execute("""
            SELECT
                COUNT(*) as renewed_count,
                ROUND(AVG(gap_days), 1) as avg_gap_days,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY gap_days) as median_gap_days,
                MIN(gap_days) as min_gap_days,
                MAX(gap_days) as max_gap_days,
                COUNT(CASE WHEN gap_days < 0 THEN 1 END) as early_renewal,
                COUNT(CASE WHEN gap_days = 0 THEN 1 END) as same_day_renewal,
                COUNT(CASE WHEN gap_days > 0 THEN 1 END) as late_renewal
            FROM ris.core_hp_period
            WHERE renewed = true;
        """)
        result = cursor.fetchone()
        if result and result['renewed_count']:
            print(f"   Total renewed: {result['renewed_count']:,}")
            print(f"   Avg gap: {result['avg_gap_days']} days")
            print(f"   Median gap: {result['median_gap_days']} days")
            print(f"   Min gap: {result['min_gap_days']} days")
            print(f"   Max gap: {result['max_gap_days']} days")
            print(f"\n   Renewal timing:")
            print(f"     Early (gap < 0): {result['early_renewal']:,}")
            print(f"     Same day (gap = 0): {result['same_day_renewal']:,}")
            print(f"     Late (gap > 0): {result['late_renewal']:,}")
        else:
            print("   No renewed periods found")

    # 7. Users with multiple HPs
    print("\n7. USERS WITH MULTIPLE HEROPASSES:")
    with pg.get_cursor() as cursor:
        cursor.execute("""
            SELECT
                hp_count,
                COUNT(*) as users
            FROM (
                SELECT
                    user_id,
                    COUNT(*) as hp_count
                FROM ris.core_hp_period
                GROUP BY user_id
            ) t
            GROUP BY hp_count
            ORDER BY hp_count;
        """)
        print("   HP count -> Number of users:")
        for row in cursor.fetchall():
            print(f"     {row['hp_count']} HP: {row['users']:,} users")

    # 8. Date range
    print("\n8. DATE RANGE:")
    with pg.get_cursor() as cursor:
        cursor.execute("""
            SELECT
                MIN(hp_start) as earliest_start,
                MAX(hp_end_corrected) as latest_end,
                MAX(hp_end_corrected) - MIN(hp_start) as total_days
            FROM ris.core_hp_period;
        """)
        result = cursor.fetchone()
        print(f"   Earliest HP start: {result['earliest_start']}")
        print(f"   Latest HP end (corrected): {result['latest_end']}")
        print(f"   Total span: {result['total_days']} days")

    # 9. Data quality checks
    print("\n9. DATA QUALITY CHECKS:")
    with pg.get_cursor() as cursor:
        # Check for nulls
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN user_id IS NULL THEN 1 END) as null_user_id,
                COUNT(CASE WHEN hp_start IS NULL THEN 1 END) as null_hp_start,
                COUNT(CASE WHEN hp_end IS NULL THEN 1 END) as null_hp_end,
                COUNT(CASE WHEN hp_end_corrected IS NULL THEN 1 END) as null_hp_end_corrected
            FROM ris.core_hp_period;
        """)
        result = cursor.fetchone()
        print(f"   Null user_id: {result['null_user_id']}")
        print(f"   Null hp_start: {result['null_hp_start']}")
        print(f"   Null hp_end: {result['null_hp_end']}")
        print(f"   Null hp_end_corrected: {result['null_hp_end_corrected']}")

        # Check for invalid dates
        cursor.execute("""
            SELECT
                COUNT(CASE WHEN hp_end < hp_start THEN 1 END) as invalid_date_range,
                COUNT(CASE WHEN hp_end_corrected < hp_end THEN 1 END) as corrected_before_end,
                COUNT(CASE WHEN hp_length_days <= 0 THEN 1 END) as invalid_length
            FROM ris.core_hp_period;
        """)
        result = cursor.fetchone()
        print(f"   Invalid date range (end < start): {result['invalid_date_range']}")
        print(f"   Corrected before end: {result['corrected_before_end']}")
        print(f"   Invalid length: {result['invalid_length']}")

    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
