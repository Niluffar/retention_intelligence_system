import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from utils.db_connectors import PostgresConnector


def main():
    print("Loading user data from PostgreSQL...")

    pg = PostgresConnector()

    base_query = r"""
    with base as (
      select
          u.id                 as user_id,
          u.nickname,
          u.firstname,
          u.lastname,
          u.sex                as gender,
          u.birthday           as birthdate,
          u.phonenumber,
          u.weight             as weight_user,
          u.height             as height_user_cm,
          u.club               as user_club_id,
          u.created_at::date   as user_created_at,
          case
            when u.birthday ~ '^\d{2}-\d{2}-\d{4}$' then to_date(u.birthday, 'DD-MM-YYYY')
            else null
          end as birth_dt
      from raw."user" u
      where
          u.role = 'user'
          and u.partnershiptype is null
    ),
    calc as (
      select
          *,
          case
            when birth_dt is not null
              then extract(year from age(current_date, birth_dt))::int
            else null
          end as age_years
      from base
    ),
    user_profile_club as (
      select
          b.user_id,
          coalesce(mc.name, rc.name) as club_name
      from calc b
      left join main.clubs mc on mc.club = b.user_club_id
      left join raw.club   rc on rc.id  = b.user_club_id
    ),
    hp_latest as (
      select user_id, club_hp_name, hp_created_at
      from (
        select
            uhp."user"       as user_id,
            chp.name         as club_hp_name,
            uhp.created_at   as hp_created_at,
            row_number() over (
              partition by uhp."user"
              order by uhp.created_at desc nulls last
            ) as rn
        from raw.userheropass uhp
        join raw.heropass h on h.id = uhp.heropass
        left join raw.club chp on chp.id = uhp.club
        where h."name" in ('Годовой Hero`s Pass', 'Полугодовой Hero`s Pass')
      ) s
      where rn = 1
    ),
    inbody_latest as (
      select user_id, weight_kg_latest, height_cm_latest, fat_pct_latest, bmi_latest
      from (
        select
            uit."user"       as user_id,
            uit.wt           as weight_kg_latest,
            uit.ht           as height_cm_latest,
            uit.pbf          as fat_pct_latest,
            uit.bmi          as bmi_latest,
            row_number() over (
              partition by uit."user"
              order by uit.testdate desc nulls last
            ) as rn
        from raw.userinbodytest uit
      ) s
      where rn = 1
    ),
    friends_latest as (
      select user_id, friends_cnt
      from (
        select
            fh."user"        as user_id,
            fh.friends_count as friends_cnt,
            row_number() over (
              partition by fh."user"
              order by fh."date" desc nulls last
            ) as rn
        from main.friends_history fh
      ) s
      where rn = 1
    ),
    posts_cnt as (
      select
          p."user" as user_id,
          count(*)::int as feed_posts_total
      from raw.post p
      where p.status = 'posted'
      group by p."user"
    ),
    lifestyle_flag as (
      select user_id,
             case
               when ans ilike '%да%' then true
               when ans ilike '%нет%' then false
               else null
             end as active_lifestyle
      from (
        select
          umr."user" as user_id,
          (uq.answers)::text as ans,
          row_number() over (
            partition by umr."user"
            order by coalesce(umr.updated_at, umr.created_at) desc nulls last
          ) as rn
        from raw.usermarathonrecommendation_questionandanswer uq
        join raw.usermarathonrecommendation umr
          on uq.usermarathonrecommendation_id = umr.id
        where lower(uq.question) ~ 'вы.*вед[её]те.*актив.*образ.*жизни'
      ) s
      where rn = 1
    ),
    bodytype_flag as (
      select user_id,
             case
               when ans ~* 'Худощавое'          then 'Slim'
               when ans ~* 'Мускулистое'        then 'Muscular'
               when ans ~* 'Склонен к полноте'  then 'Overweight-prone'
               else null
             end as bodytype
      from (
        select
          umr."user" as user_id,
          (uq.answers)::text as ans,
          row_number() over (
            partition by umr."user"
            order by coalesce(umr.updated_at, umr.created_at) desc nulls last
          ) as rn
        from raw.usermarathonrecommendation_questionandanswer uq
        join raw.usermarathonrecommendation umr
          on uq.usermarathonrecommendation_id = umr.id
        where lower(uq.question) ~ 'выбер.*тип.*телосложен'
      ) s
      where rn = 1
    ),
    fitness_goal_flag as (
      select user_id,
             case
               when ans ~* 'Похудеть'                                  then 'Weight loss'
               when ans ~* 'Нарастить мышечную массу'                   then 'Muscle gain'
               when ans ~* 'Сбалансированная проработка всех групп'     then 'Balanced full-body'
               when ans ~* 'Развить выносливость и силовые показатели'  then 'Endurance & strength'
               when ans ~* 'Накачать ноги и ягодицы'                    then 'Legs & glutes'
               else null
             end as fitness_goal
      from (
        select
          umr."user" as user_id,
          (uq.answers)::text as ans,
          row_number() over (
            partition by umr."user"
            order by coalesce(umr.updated_at, umr.created_at) desc nulls last
          ) as rn
        from raw.usermarathonrecommendation_questionandanswer uq
        join raw.usermarathonrecommendation umr
          on uq.usermarathonrecommendation_id = umr.id
        where lower(uq.question) like '%первостепенная цель%'
      ) s
      where rn = 1
    ),
    hp_first_five as (
      select
        user_id,
        max(case when rn = 1 then start_date end) as first_hp,
        max(case when rn = 1 then end_date   end) as first_hp_end,
        max(case when rn = 1 then hp_name    end) as first_hp_name,
        max(case when rn = 2 then start_date end) as second_hp,
        max(case when rn = 2 then end_date   end) as second_hp_end,
        max(case when rn = 2 then hp_name    end) as second_hp_name,
        max(case when rn = 3 then start_date end) as third_hp,
        max(case when rn = 3 then end_date   end) as third_hp_end,
        max(case when rn = 3 then hp_name    end) as third_hp_name,
        max(case when rn = 4 then start_date end) as fourth_hp,
        max(case when rn = 4 then end_date   end) as fourth_hp_end,
        max(case when rn = 4 then hp_name    end) as fourth_hp_name,
        max(case when rn = 5 then start_date end) as fifth_hp,
        max(case when rn = 5 then end_date   end) as fifth_hp_end,
        max(case when rn = 5 then hp_name    end) as fifth_hp_name
      from (
        select
          uhp."user"             as user_id,
          uhp.starttime::date    as start_date,
          uhp.endtime::date      as end_date,
          hp.name                as hp_name,
          row_number() over (
            partition by uhp."user"
            order by uhp.starttime asc nulls last
          ) as rn
        from raw.userheropass uhp
        join raw.heropass hp
          on uhp.heropass = hp.id
        where hp.name in ('Годовой Hero`s Pass', 'Полугодовой Hero`s Pass')
      ) s
      group by user_id
    ),
    earliest_trial as (
      select
        user_id, marathonevent_id, trial_start, marathon_name
      from (
        select
          ume."user"          as user_id,
          me.id               as marathonevent_id,
          me.starttime::date  as trial_start,
          coalesce(m.name,'') as marathon_name,
          row_number() over (
            partition by ume."user"
            order by me.starttime asc nulls last
          ) as rn
        from raw.usermarathonevent ume
        join raw.marathonevent me on me.id = ume.marathonevent
        left join raw.marathon m  on m.id  = me.marathon
      ) s
      where rn = 1
    ),
    trial_payment as (
      select
        et.user_id,
        et.trial_start,
        et.marathon_name,
        case
          when et.marathon_name = 'Hero''s Week'
               and exists (
                 select 1
                 from raw.userpayment up
                 where up."user" = et.user_id
                   and up.marathonevent = et.marathonevent_id
                   and up.name like 'Подарочный Hero''s Week%'
               )
            then 'gift'
          when et.marathon_name in ('Первый шаг','Basecamp')
               and exists (
                 select 1
                 from raw.userpayment up
                 where up."user" = et.user_id
                   and up.marathonevent = et.marathonevent_id
                   and (up.paidamount = 0 or up.paidamount is null)
                   and up.type in ('adminAdd','added')
               )
            then 'gift'
          else 'paid'
        end as trial_payment
      from earliest_trial et
    ),
    test_exclude as (
      select distinct t."user" as user_id
      from raw.test_users_list t
      where t.free_pass_type = 'hp'
    )
    select
        c.user_id,
        c.nickname,
        c.firstname,
        c.lastname,
        c.gender,
        c.birthdate,
        c.age_years as age,
        c.phonenumber,
        c.user_created_at,
        coalesce(ib.weight_kg_latest, c.weight_user)     as weight_kg,
        coalesce(ib.height_cm_latest, c.height_user_cm)  as height_cm,
        case
          when c.age_years is null           then 'unknown'
          when c.age_years < 18              then '<18'
          when c.age_years between 18 and 24 then '18-24'
          when c.age_years between 25 and 34 then '25-34'
          when c.age_years between 35 and 44 then '35-44'
          when c.age_years between 45 and 54 then '45-54'
          when c.age_years between 55 and 64 then '55-64'
          else '65+'
        end as age_band,
        ib.fat_pct_latest,
        ib.bmi_latest,
        case
          when coalesce(hp.club_hp_name, upc.club_name) = 'HJ Villa'
               and coalesce(hp.hp_created_at, c.user_created_at, current_date)::date < date '2025-06-01'
            then 'HJ Colibri'
          when coalesce(hp.club_hp_name, upc.club_name) = 'HJ Promenade'
               and coalesce(hp.hp_created_at, c.user_created_at, current_date)::date < date '2025-04-01'
            then 'HJ Colibri'
          when coalesce(hp.club_hp_name, upc.club_name) = 'HJ Europe City'
               and coalesce(hp.hp_created_at, c.user_created_at, current_date)::date < date '2025-02-01'
            then 'HJ Nurly Orda'
          else coalesce(hp.club_hp_name, upc.club_name)
        end as default_club_corr,
        case
          when (
            case
              when coalesce(hp.club_hp_name, upc.club_name) = 'HJ Villa'
                   and coalesce(hp.hp_created_at, c.user_created_at, current_date)::date < date '2025-06-01'
                then 'HJ Colibri'
              when coalesce(hp.club_hp_name, upc.club_name) = 'HJ Promenade'
                   and coalesce(hp.hp_created_at, c.user_created_at, current_date)::date < date '2025-04-01'
                then 'HJ Colibri'
              when coalesce(hp.club_hp_name, upc.club_name) = 'HJ Europe City'
                   and coalesce(hp.hp_created_at, c.user_created_at, current_date)::date < date '2025-02-01'
                then 'HJ Nurly Orda'
              else coalesce(hp.club_hp_name, upc.club_name)
            end
          ) in ('HJ Nurly Orda', 'HJ Europe City')
            then 'Астана'
          else 'Алматы'
        end as city,
        exists (
          select 1
          from raw.clans cl
          where c.user_id = cl.admin
             or (cl.users   is not null and c.user_id = any (cl.users))
             or (cl.mentors is not null and c.user_id = any (cl.mentors))
        ) as in_clan,
        coalesce(fl.friends_cnt, 0) as friends_cnt,
        coalesce(pc.feed_posts_total, 0) as feed_posts_total,
        lf.active_lifestyle,
        bt.bodytype,
        fg.fitness_goal,
        hp5.first_hp,
        hp5.first_hp_end,
        hp5.first_hp_name,
        hp5.second_hp,
        hp5.second_hp_end,
        hp5.second_hp_name,
        hp5.third_hp,
        hp5.third_hp_end,
        hp5.third_hp_name,
        hp5.fourth_hp,
        hp5.fourth_hp_end,
        hp5.fourth_hp_name,
        hp5.fifth_hp,
        hp5.fifth_hp_end,
        hp5.fifth_hp_name,
        (hp5.first_hp is not null) as ever_hp,
        case
          when hp5.first_hp is not null and et.trial_start < hp5.first_hp then true
          else false
        end as trial_before_hp,
        case
          when hp5.first_hp is not null and et.trial_start < hp5.first_hp then et.marathon_name
          else null
        end as trial_type,
        case
          when hp5.first_hp is not null and et.trial_start < hp5.first_hp then tp.trial_payment
          else null
        end as trial_payment
    from calc c
    left join inbody_latest      ib  on ib.user_id = c.user_id
    left join hp_latest          hp  on hp.user_id = c.user_id
    left join user_profile_club  upc on upc.user_id = c.user_id
    left join friends_latest     fl  on fl.user_id = c.user_id
    left join posts_cnt          pc  on pc.user_id = c.user_id
    left join lifestyle_flag     lf  on lf.user_id = c.user_id
    left join bodytype_flag      bt  on bt.user_id = c.user_id
    left join fitness_goal_flag  fg  on fg.user_id = c.user_id
    left join hp_first_five      hp5 on hp5.user_id = c.user_id
    left join earliest_trial     et  on et.user_id = c.user_id
    left join trial_payment      tp  on tp.user_id = c.user_id
    where not exists (
      select 1 from test_exclude te where te.user_id = c.user_id
    )
    """

    try:
        with pg.get_cursor() as cursor:
            cursor.execute(base_query)
            rows = cursor.fetchall()

        df_base = pd.DataFrame(rows)
        print(f"Loaded {len(df_base)} users")

    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return

    print("Loading location metrics...")
    processed_dir = Path(__file__).parent.parent.parent / 'data' / 'processed'

    location_files = list(processed_dir.glob('user_location_metrics_*.csv'))

    if not location_files:
        print(f"Warning: No location metrics found")
        df_location = pd.DataFrame()
    else:
        loc_file = sorted(location_files)[-1]
        print(f"Using: {loc_file.name}")
        df_location = pd.read_csv(loc_file)

    print("Merging datasets...")
    if len(df_location) > 0:
        df_merged = df_base.merge(df_location, on='user_id', how='left')
        print(f"Merged {len(df_merged)} rows")
    else:
        df_merged = df_base
        df_merged['home_latitude'] = None
        df_merged['home_longitude'] = None
        df_merged['home_location_confidence'] = None
        df_merged['location_sample_size'] = 0
        df_merged['distance_home_to_club_km'] = None
        df_merged['avg_booking_distance_km'] = None
        df_merged['min_booking_distance_km'] = None
        df_merged['distance_variability'] = None
        df_merged['is_home_nearby'] = False
        df_merged['commute_convenience_score'] = None
        df_merged['location_data_quality'] = 'none'

    print("Inserting into ris.core_user...")

    df_merged['created_at'] = datetime.now()
    df_merged['updated_at'] = datetime.now()

    try:
        df_merged.to_sql(
            name='core_user',
            schema='ris',
            con=pg.engine,
            if_exists='append',
            index=False,
            method='multi',
            chunksize=500
        )
        print(f"Inserted {len(df_merged)} rows")

    except Exception as e:
        print(f"Error: {str(e)}")
        return

    with pg.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as cnt FROM ris.core_user;")
        count = cursor.fetchone()['cnt']
        print(f"Total in table: {count:,}")


if __name__ == "__main__":
    main()
