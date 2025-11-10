

import sys
from pathlib import Path
from datetime import date, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.db_connectors import PostgresConnector


# Kazakhstan public holidays (recurring annual)
KZ_HOLIDAYS = {
    # Fixed holidays
    (1, 1): "New Year",
    (1, 2): "New Year Holiday",
    (3, 8): "International Women's Day",
    (3, 21): "Nauryz",
    (3, 22): "Nauryz Holiday",
    (3, 23): "Nauryz Holiday",
    (5, 1): "Unity Day",
    (5, 7): "Defender of the Fatherland Day",
    (5, 9): "Victory Day",
    (7, 6): "Capital City Day",
    (8, 30): "Constitution Day",
    (10, 25): "Republic Day",
    (12, 16): "Independence Day",
    (12, 17): "Independence Day Holiday",
}

# School breaks (approximate dates, can be adjusted)
SCHOOL_BREAKS = [
    # Winter break: late December to early January
    ((12, 25), (1, 10)),
    # Spring break: late March
    ((3, 20), (3, 28)),
    # Summer break: June-August
    ((6, 1), (8, 31)),
    # Autumn break: early November
    ((11, 1), (11, 7)),
]


def get_season(month: int) -> str:
    """Get season label for a month"""
    if month in [12, 1, 2]:
        return 'winter'
    elif month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    else:  # 9, 10, 11
        return 'autumn'


def is_school_break(dt: date) -> bool:
    """Check if date is during school break"""
    for (start_month, start_day), (end_month, end_day) in SCHOOL_BREAKS:
        # Handle year wrap-around for winter break
        if start_month > end_month:
            # Winter break spans two years
            if (dt.month == start_month and dt.day >= start_day) or \
               (dt.month == end_month and dt.day <= end_day):
                return True
        else:
            # Normal break within same year
            start_date = date(dt.year, start_month, start_day)
            end_date = date(dt.year, end_month, end_day)
            if start_date <= dt <= end_date:
                return True
    return False


def generate_calendar_data(start_year: int, end_year: int):
    """Generate calendar data for date range"""
    start_date = date(start_year, 1, 1)
    end_date = date(end_year, 12, 31)

    calendar_data = []
    current_date = start_date

    while current_date <= end_date:
        # Day of week (1=Monday, 7=Sunday)
        dow = current_date.isoweekday()
        is_weekend = dow in [6, 7]

        # Week of year
        week_of_year = current_date.isocalendar()[1]

        # Month, quarter, year
        month = current_date.month
        quarter = (month - 1) // 3 + 1
        year = current_date.year

        # Holiday check
        is_holiday = (month, current_date.day) in KZ_HOLIDAYS

        # School break check
        is_school_break_flag = is_school_break(current_date)

        # Season
        season = get_season(month)

        calendar_data.append({
            'dt': current_date,
            'dow': dow,
            'is_weekend': is_weekend,
            'week_of_year': week_of_year,
            'month': month,
            'quarter': quarter,
            'year': year,
            'is_holiday_kz': is_holiday,
            'is_school_break': is_school_break_flag,
            'season_label': season
        })

        current_date += timedelta(days=1)

    return calendar_data


def main():
    """Populate ref_calendar table"""
    print("\n" + "=" * 70)
    print("POPULATING REF_CALENDAR TABLE")
    

    pg = PostgresConnector()

        if not pg.table_exists('ref_calendar'):
        print("\n[ERROR] Table ris.ref_calendar does not exist!")
        print("Please run create_ref_calendar_table.py first.")
        return

    # Define date range (from 2020 to 2030 for sufficient coverage)
    START_YEAR = 2020
    END_YEAR = 2030

    print(f"\n1. Generating calendar data for {START_YEAR}-{END_YEAR}...")
    calendar_data = generate_calendar_data(START_YEAR, END_YEAR)
    print(f"   Generated {len(calendar_data):,} calendar days")

        holidays = sum(1 for d in calendar_data if d['is_holiday_kz'])
    school_breaks = sum(1 for d in calendar_data if d['is_school_break'])
    weekends = sum(1 for d in calendar_data if d['is_weekend'])

    print(f"   - Holidays: {holidays:,}")
    print(f"   - School breaks: {school_breaks:,}")
    print(f"   - Weekends: {weekends:,}")

    # Insert data
    print("\n2. Inserting data into ris.ref_calendar...")

    insert_query = """
        INSERT INTO ris.ref_calendar (
            dt, dow, is_weekend, week_of_year, month, quarter, year,
            is_holiday_kz, is_school_break, season_label
        ) VALUES (
            %(dt)s, %(dow)s, %(is_weekend)s, %(week_of_year)s, %(month)s,
            %(quarter)s, %(year)s, %(is_holiday_kz)s, %(is_school_break)s,
            %(season_label)s
        )
        ON CONFLICT (dt) DO UPDATE SET
            dow = EXCLUDED.dow,
            is_weekend = EXCLUDED.is_weekend,
            week_of_year = EXCLUDED.week_of_year,
            month = EXCLUDED.month,
            quarter = EXCLUDED.quarter,
            year = EXCLUDED.year,
            is_holiday_kz = EXCLUDED.is_holiday_kz,
            is_school_break = EXCLUDED.is_school_break,
            season_label = EXCLUDED.season_label,
            updated_at = NOW();
    """

    with pg.get_connection() as conn:
        with conn.cursor() as cursor:
            # Batch insert
            cursor.executemany(insert_query, calendar_data)
            rows_inserted = cursor.rowcount

    print(f"   [SUCCESS] Inserted/updated {rows_inserted:,} rows")

        print("\n3. Verifying data...")
    with pg.get_cursor() as cursor:
        cursor.execute("""
            SELECT
                COUNT(*) as total_days,
                MIN(dt) as earliest_date,
                MAX(dt) as latest_date,
                SUM(CASE WHEN is_weekend THEN 1 ELSE 0 END) as weekends,
                SUM(CASE WHEN is_holiday_kz THEN 1 ELSE 0 END) as holidays,
                SUM(CASE WHEN is_school_break THEN 1 ELSE 0 END) as school_breaks
            FROM ris.ref_calendar;
        """)
        result = cursor.fetchone()

        print(f"   Total days: {result['total_days']:,}")
        print(f"   Date range: {result['earliest_date']} to {result['latest_date']}")
        print(f"   Weekends: {result['weekends']:,}")
        print(f"   Holidays: {result['holidays']:,}")
        print(f"   School breaks: {result['school_breaks']:,}")

        print("\n4. Sample data:")
    with pg.get_cursor() as cursor:
        cursor.execute("""
            SELECT
                dt,
                dow,
                is_weekend,
                is_holiday_kz,
                is_school_break,
                season_label
            FROM ris.ref_calendar
            WHERE is_holiday_kz = true
            ORDER BY dt
            LIMIT 10;
        """)
        results = cursor.fetchall()

        print("\n   Sample holidays:")
        for row in results:
            weekend_flag = " [Weekend]" if row['is_weekend'] else ""
            break_flag = " [School Break]" if row['is_school_break'] else ""
            print(f"   {row['dt']}: DOW={row['dow']} | {row['season_label']}{weekend_flag}{break_flag}")

    print("\n" + "=" * 70)
    print("POPULATION COMPLETE")
    


if __name__ == "__main__":
    main()
