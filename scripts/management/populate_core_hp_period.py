

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.db_connectors import PostgresConnector


def main():
    """Populate core_hp_period table"""
    print("\n" + "=" * 70)
    print("POPULATING CORE_HP_PERIOD TABLE")
    

    pg = PostgresConnector()

        print("\n1. Loading HeroPass data from PostgreSQL...")

        base_query = r"""
    with hp_raw as (
        select
            uhp.id as hp_period_id,
            uhp."user" as user_id,
            uhp.starttime::date  as hp_start,
            uhp.endtime::date as hp_end,
            uft.starttime::date as freezing_start,
            uft.endtime::date as freezing_end,
            hp.name as hp_type,
            case
              when coalesce(c.name, c2.name) = 'HJ Villa'
                   and uhp.starttime::date < date '2025-06-01'
                then 'HJ Colibri'
              when coalesce(c.name, c2.name) = 'HJ Promenade'
                   and uhp.starttime::date < date '2025-04-01'
                then 'HJ Colibri'
              when coalesce(c.name, c2.name) = 'HJ Europe City'
                   and uhp.starttime::date < date '2025-02-01'
                then 'HJ Nurly Orda'
              else coalesce(c.name, c2.name)
            end as hp_club_corr
        from raw.userheropass uhp
        left join raw.heropass hp
               on uhp.heropass = hp.id
        left join raw."user" u
               on uhp."user" = u.id
        left join raw.club c
               on uhp.club = c.id
        left join raw.club c2
               on u.club = c2.id
        left join raw.userfreezingtime uft
               on uhp."user" = uft."user"
              and uhp.id = uft.userheropass
        where hp.name in ('Годовой Hero`s Pass', 'Полугодовой Hero`s Pass')
    ),
    hp_agg as (
        select
            hp_period_id,
            user_id,
            hp_type,
            hp_club_corr,
            hp_start,
            hp_end,
            coalesce(
              sum(
                case
                  when freezing_start is not null
                       and freezing_end   is not null
                    then (freezing_end - freezing_start + 1)
                  else 0
                end
              )::int,
              0
            ) as freeze_days_total
        from hp_raw
        group by
            hp_period_id,
            user_id,
            hp_type,
            hp_club_corr,
            hp_start,
            hp_end
    )
    select
        h.hp_period_id,
        h.user_id,
        h.hp_type,
        h.hp_club_corr,
        h.hp_start,
        h.hp_end,
        h.freeze_days_total,
        (h.hp_end + h.freeze_days_total)::date as hp_end_corrected,
        (h.hp_end - h.hp_start + 1) as hp_length_days,
        lead(h.hp_start) over (
            partition by h.user_id
            order by h.hp_start
        )::date as next_hp_purchase_dt
    from hp_agg h
    order by h.user_id, h.hp_start
    """

        try:
        df_hp = pd.read_sql(base_query, pg.engine)
        print(f"   Loaded {len(df_hp)} HeroPass periods from database")
    except Exception as e:
        print(f"   ERROR loading data: {str(e)}")
        import traceback
        traceback.print_exc()
        return

        print("\n2. Calculating additional fields...")

    # Calculate days_to_next_hp
    df_hp['days_to_next_hp'] = (
        (pd.to_datetime(df_hp['next_hp_purchase_dt']) -
         pd.to_datetime(df_hp['hp_end_corrected'])).dt.days
    )

    # Calculate renewed flag
    df_hp['renewed'] = df_hp['next_hp_purchase_dt'].notna()

    # Calculate gap_days (same as days_to_next_hp for renewed users)
    df_hp['gap_days'] = df_hp.apply(
        lambda row: row['days_to_next_hp'] if row['renewed'] else None,
        axis=1
    )

    # Add metadata
    df_hp['created_at'] = datetime.now()
    df_hp['updated_at'] = datetime.now()

    print(f"   Calculated fields for {len(df_hp)} periods")
    print(f"   Renewed HeroPasses: {df_hp['renewed'].sum():,}")
    print(f"   Not renewed: {(~df_hp['renewed']).sum():,}")

        print("\n3. Inserting data into ris.core_hp_period...")

    try:
                df_hp.to_sql(
            name='core_hp_period',
            schema='ris',
            con=pg.engine,
            if_exists='append',  # append to existing table
            index=False,
            method='multi',
            chunksize=500
        )

        print(f"   SUCCESS: Inserted {len(df_hp)} rows")

    except Exception as e:
        print(f"   ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return

        print("\n4. Verifying data...")
    with pg.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as cnt FROM ris.core_hp_period;")
        count = cursor.fetchone()['cnt']
        print(f"   Total rows in table: {count:,}")

                cursor.execute("""
            SELECT
                hp_period_id,
                user_id,
                hp_type,
                hp_club_corr,
                hp_start,
                hp_end_corrected,
                freeze_days_total,
                renewed,
                gap_days
            FROM ris.core_hp_period
            ORDER BY hp_start DESC
            LIMIT 5;
        """)
        samples = cursor.fetchall()

        print("\n   Sample rows (most recent):")
        for row in samples:
            renewed_str = 'YES' if row['renewed'] else 'NO'
            gap_str = f"{row['gap_days']}d" if row['gap_days'] is not None else 'N/A'
            print(f"     - HP#{row['hp_period_id']}: {row['user_id'][:8]}... | "
                  f"{row['hp_start']} -> {row['hp_end_corrected']} | "
                  f"{row['hp_club_corr']} | freeze={row['freeze_days_total']}d | "
                  f"renewed={renewed_str} gap={gap_str}")

        # Statistics
        cursor.execute("""
            SELECT
                COUNT(*) as total_periods,
                COUNT(DISTINCT user_id) as unique_users,
                SUM(CASE WHEN renewed THEN 1 ELSE 0 END) as renewed_count,
                AVG(freeze_days_total) as avg_freeze_days,
                AVG(CASE WHEN renewed THEN gap_days END) as avg_gap_days
            FROM ris.core_hp_period;
        """)
        stats = cursor.fetchone()

        print("\n   Statistics:")
        print(f"     Total HeroPass periods: {stats['total_periods']:,}")
        print(f"     Unique users with HP: {stats['unique_users']:,}")
        print(f"     Renewed periods: {stats['renewed_count']:,} ({stats['renewed_count']/stats['total_periods']*100:.1f}%)")
        print(f"     Avg freeze days: {stats['avg_freeze_days']:.1f}")
        print(f"     Avg gap to next HP: {stats['avg_gap_days']:.1f} days")

    print("\n" + "=" * 70)
    print("POPULATION COMPLETE")
    
    print(f"Rows inserted: {len(df_hp):,}")
    print(f"Total in table: {count:,}")
    


if __name__ == "__main__":
    main()
