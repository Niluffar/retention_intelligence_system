

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, time
from typing import Dict, Tuple, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.db_connectors import PostgresConnector, MongoConnector

CLUB_COORDINATES = {
    'HJ Colibri': {'lat': 43.2398083, 'lon': 76.9527295},
    'HJ Promenade': {'lat': 43.2397899, 'lon': 76.9240991},
    'HJ Villa': {'lat': 43.2116139, 'lon': 76.9180874},
    'HJ Nurly Orda': {'lat': 51.1403179, 'lon': 71.4102712},
    'HJ Europe City': {'lat': 51.1208937, 'lon': 71.4206657}
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import radians, sin, cos, sqrt, atan2

    R = 6371.0
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance


def determine_home_location(df_locations: pd.DataFrame, user_id: str) -> Optional[Dict]:
    user_locs = df_locations[df_locations['userId'] == user_id].copy()

    if len(user_locs) == 0:
        return None

    user_locs['lat_rounded'] = user_locs['latitude'].round(4)
    user_locs['lon_rounded'] = user_locs['longitude'].round(4)

    if 'created_at' in user_locs.columns:
        user_locs['created_at'] = pd.to_datetime(user_locs['created_at'], errors='coerce')
        user_locs['created_at'] = user_locs['created_at'] + pd.Timedelta(hours=5)
        user_locs['hour'] = user_locs['created_at'].dt.hour
        user_locs['is_night'] = user_locs['hour'].apply(
            lambda h: h >= 22 or h <= 8 if pd.notna(h) else False
        )
    else:
        user_locs['is_night'] = False

    location_counts = (
        user_locs
        .groupby(['lat_rounded', 'lon_rounded'])
        .agg({
            'latitude': 'mean',
            'longitude': 'mean',
            'userId': 'count',
            'is_night': 'sum'
        })
        .rename(columns={'userId': 'count', 'is_night': 'night_count'})
        .reset_index()
    )

    location_counts['score'] = (
        location_counts['count'] +
        location_counts['night_count'] * 2
    )

    top_location = location_counts.nlargest(1, 'score').iloc[0]

    total_locations = len(user_locs)
    confidence = (top_location['count'] / total_locations) * 100

    return {
        'latitude': top_location['latitude'],
        'longitude': top_location['longitude'],
        'confidence': confidence,
        'sample_size': total_locations,
        'night_occurrences': int(top_location['night_count'])
    }


def calculate_user_metrics(
    user_id: str,
    club_name: str,
    df_locations: pd.DataFrame
) -> Dict:
    metrics = {
        'user_id': user_id,
        'home_latitude': None,
        'home_longitude': None,
        'home_location_confidence': None,
        'location_sample_size': 0,
        'distance_home_to_club_km': None,
        'avg_booking_distance_km': None,
        'min_booking_distance_km': None,
        'distance_variability': None,
        'is_home_nearby': False,
        'commute_convenience_score': None,
        'location_data_quality': 'none'
    }

    club_coords = CLUB_COORDINATES.get(club_name)
    if not club_coords:
        metrics['location_data_quality'] = 'no_club_coords'
        return metrics

    home = determine_home_location(df_locations, user_id)
    if not home:
        metrics['location_data_quality'] = 'no_user_data'
        return metrics

    metrics['home_latitude'] = home['latitude']
    metrics['home_longitude'] = home['longitude']
    metrics['home_location_confidence'] = round(home['confidence'], 2)
    metrics['location_sample_size'] = home['sample_size']

    distance_home_club = haversine_distance(
        home['latitude'],
        home['longitude'],
        club_coords['lat'],
        club_coords['lon']
    )
    metrics['distance_home_to_club_km'] = round(distance_home_club, 2)

    metrics['is_home_nearby'] = distance_home_club < 2.0

    user_locs = df_locations[df_locations['userId'] == user_id]

    if len(user_locs) >= 3:
        distances = []
        for _, row in user_locs.iterrows():
            if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                dist = haversine_distance(
                    row['latitude'],
                    row['longitude'],
                    club_coords['lat'],
                    club_coords['lon']
                )
                distances.append(dist)

        if distances:
            metrics['avg_booking_distance_km'] = round(np.mean(distances), 2)

            user_locs_copy = user_locs.copy()
            user_locs_copy['lat_rounded'] = user_locs_copy['latitude'].round(4)
            user_locs_copy['lon_rounded'] = user_locs_copy['longitude'].round(4)

            location_clusters = (
                user_locs_copy
                .groupby(['lat_rounded', 'lon_rounded'])
                .agg({
                    'latitude': 'mean',
                    'longitude': 'mean',
                    'userId': 'count'
                })
                .rename(columns={'userId': 'count'})
                .reset_index()
                .nlargest(2, 'count')
            )

            if len(location_clusters) > 0:
                cluster_distances = []
                for _, cluster in location_clusters.iterrows():
                    cluster_dist = haversine_distance(
                        cluster['latitude'],
                        cluster['longitude'],
                        club_coords['lat'],
                        club_coords['lon']
                    )
                    cluster_distances.append(cluster_dist)

                metrics['min_booking_distance_km'] = round(min(cluster_distances), 2)
            else:
                metrics['min_booking_distance_km'] = round(np.min(distances), 2)

            if len(distances) > 1:
                metrics['distance_variability'] = round(np.std(distances), 2)
            else:
                metrics['distance_variability'] = 0.0

            distance_norm = min(1.0, distance_home_club / 10)
            variability_norm = min(1.0, metrics['distance_variability'] / 5)

            convenience = 1.0 - (
                0.7 * distance_norm +
                0.3 * variability_norm
            )
            metrics['commute_convenience_score'] = round(max(0, min(1, convenience)), 4)

            if home['sample_size'] >= 20 and home['confidence'] >= 30:
                metrics['location_data_quality'] = 'good'
            elif home['sample_size'] >= 10 and home['confidence'] >= 20:
                metrics['location_data_quality'] = 'medium'
            else:
                metrics['location_data_quality'] = 'poor'
    else:
        metrics['location_data_quality'] = 'insufficient'

    return metrics


def main():
    print("\nCalculating location metrics...")

    pg = PostgresConnector()
    mongo = MongoConnector()

    collection = mongo.get_collection('userslocations')
    mongo_user_ids = collection.distinct('userId')
    mongo_user_ids_str = [str(uid) for uid in mongo_user_ids]
    print(f"Users with location data: {len(mongo_user_ids_str):,}")

    user_ids_list = "','".join(mongo_user_ids_str)

    user_query = f"""
    SELECT
        user_id,
        default_club_corr as club_name
    FROM (
        SELECT DISTINCT
            u.id as user_id,
            COALESCE(c.name, 'Unknown') as default_club_corr
        FROM raw."user" u
        LEFT JOIN raw.club c ON c.id = u.club
        WHERE u.role = 'user'
          AND u.partnershiptype IS NULL
          AND u.id IN ('{user_ids_list}')
    ) base
    WHERE default_club_corr IS NOT NULL
      AND default_club_corr != 'Unknown'
    """

    df_users = pd.read_sql(user_query, pg.engine)
    print(f"Loaded {len(df_users)} users")

    collection = mongo.get_collection('userslocations')
    locations_data = list(collection.find())
    df_locations = pd.DataFrame(locations_data)

    if 'location' in df_locations.columns:
        df_locations['latitude'] = df_locations['location'].apply(
            lambda x: x.get('latitude') if isinstance(x, dict) else None
        )
        df_locations['longitude'] = df_locations['location'].apply(
            lambda x: x.get('longitude') if isinstance(x, dict) else None
        )

    df_locations['userId'] = df_locations['userId'].astype(str)
    df_users['user_id'] = df_users['user_id'].astype(str)

    df_locations = df_locations[
        df_locations['latitude'].notna() &
        df_locations['longitude'].notna()
    ]
    print(f"Valid location records: {len(df_locations)}")

    results = []
    for idx, row in df_users.iterrows():
        if (idx + 1) % 100 == 0:
            print(f"Processed {idx + 1}/{len(df_users)} users...")

        metrics = calculate_user_metrics(
            user_id=row['user_id'],
            club_name=row['club_name'],
            df_locations=df_locations
        )
        results.append(metrics)

    df_metrics = pd.DataFrame(results)

    print(f"\nTotal users: {len(df_metrics)}")
    print(f"Users with location data: {(df_metrics['location_sample_size'] > 0).sum()}")
    print(f"Users with good quality data: {(df_metrics['location_data_quality'] == 'good').sum()}")

    output_dir = Path(__file__).parent.parent / 'data' / 'processed'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f'user_location_metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

    df_metrics.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")

    mongo.close()
    print("Complete.")


if __name__ == "__main__":
    main()
