"""
Calculate location-based metrics for users
Includes: home location, distance to club, commute patterns
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, time
from typing import Dict, Tuple, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.db_connectors import PostgresConnector, MongoConnector


# Club coordinates - ACTUAL COORDINATES FROM HERO'S JOURNEY (5 active clubs)
CLUB_COORDINATES = {
    # Almaty (3 clubs)
    'HJ Colibri': {'lat': 43.2398083, 'lon': 76.9527295},      # ул. Шокана Уалиханова, 170/1
    'HJ Promenade': {'lat': 43.2397899, 'lon': 76.9240991},    # просп. Абая, 44А
    'HJ Променад': {'lat': 43.2397899, 'lon': 76.9240991},     # Same as Promenade (Russian spelling)
    'HJ Villa': {'lat': 43.2116139, 'lon': 76.9180874},        # просп. Аль-Фараби, 140А

    # Astana (2 clubs)
    'HJ Nurly Orda': {'lat': 51.1403179, 'lon': 71.4102712},   # просп. Кабанбай Батыра, 11/5
    'Nurly Orda': {'lat': 51.1403179, 'lon': 71.4102712},      # Without HJ prefix
    'HJ Europe City': {'lat': 51.1208937, 'lon': 71.4206657},  # ул. Акмешит, 1/1
    'Europe City': {'lat': 51.1208937, 'lon': 71.4206657},     # Without HJ prefix
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on earth (in kilometers)

    Args:
        lat1, lon1: Coordinates of first point
        lat2, lon2: Coordinates of second point

    Returns:
        Distance in kilometers
    """
    from math import radians, sin, cos, sqrt, atan2

    # Earth radius in kilometers
    R = 6371.0

    # Convert to radians
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance


def determine_home_location(df_locations: pd.DataFrame, user_id: str) -> Optional[Dict]:
    """
    Determine user's home location based on location patterns

    Strategy:
    1. Round coordinates to ~50m precision (4 decimal places)
    2. Find most frequent location cluster
    3. Prefer night/weekend locations if available

    Args:
        df_locations: DataFrame with user location history
        user_id: User ID

    Returns:
        Dict with home location info or None
    """
    user_locs = df_locations[df_locations['userId'] == user_id].copy()

    if len(user_locs) == 0:
        return None

    # Round coordinates to cluster nearby points
    user_locs['lat_rounded'] = user_locs['latitude'].round(4)
    user_locs['lon_rounded'] = user_locs['longitude'].round(4)

    # Extract hour if created_at exists
    if 'created_at' in user_locs.columns:
        user_locs['created_at'] = pd.to_datetime(user_locs['created_at'], errors='coerce')
        user_locs['hour'] = user_locs['created_at'].dt.hour
        user_locs['is_night'] = user_locs['hour'].apply(
            lambda h: h >= 22 or h <= 8 if pd.notna(h) else False
        )
    else:
        user_locs['is_night'] = False

    # Count occurrences of each location cluster
    location_counts = (
        user_locs
        .groupby(['lat_rounded', 'lon_rounded'])
        .agg({
            'latitude': 'mean',   # Use mean of cluster for final coordinates
            'longitude': 'mean',
            'userId': 'count',    # Count of occurrences
            'is_night': 'sum'     # Count of night occurrences
        })
        .rename(columns={'userId': 'count', 'is_night': 'night_count'})
        .reset_index()
    )

    # Calculate score: prefer locations with more occurrences, bonus for night locations
    location_counts['score'] = (
        location_counts['count'] +
        location_counts['night_count'] * 2  # 2x weight for night locations
    )

    # Get top location
    top_location = location_counts.nlargest(1, 'score').iloc[0]

    # Calculate confidence (what % of all locations is this cluster)
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
    """
    Calculate all location metrics for a user

    Args:
        user_id: User ID
        club_name: User's primary club name
        df_locations: DataFrame with all location data

    Returns:
        Dict with all calculated metrics
    """
    # Default metrics
    metrics = {
        'user_id': user_id,
        'home_latitude': None,
        'home_longitude': None,
        'home_location_confidence': None,
        'location_sample_size': 0,
        'distance_home_to_club_km': None,
        'avg_booking_distance_km': None,
        'distance_variability': None,
        'is_home_nearby': False,
        'commute_convenience_score': None,
        'location_data_quality': 'none'
    }

    # Get club coordinates
    club_coords = CLUB_COORDINATES.get(club_name)
    if not club_coords:
        metrics['location_data_quality'] = 'no_club_coords'
        return metrics

    # Determine home location
    home = determine_home_location(df_locations, user_id)
    if not home:
        metrics['location_data_quality'] = 'no_user_data'
        return metrics

    metrics['home_latitude'] = home['latitude']
    metrics['home_longitude'] = home['longitude']
    metrics['home_location_confidence'] = round(home['confidence'], 2)
    metrics['location_sample_size'] = home['sample_size']

    # Calculate distance from home to club
    distance_home_club = haversine_distance(
        home['latitude'],
        home['longitude'],
        club_coords['lat'],
        club_coords['lon']
    )
    metrics['distance_home_to_club_km'] = round(distance_home_club, 2)

    # Is home nearby? (< 2 km)
    metrics['is_home_nearby'] = distance_home_club < 2.0

    # Get all user locations for booking distance analysis
    user_locs = df_locations[df_locations['userId'] == user_id]

    if len(user_locs) >= 3:  # Need at least 3 points for meaningful stats
        # Calculate distance from each booking location to club
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
            # Average booking distance
            metrics['avg_booking_distance_km'] = round(np.mean(distances), 2)

            # Variability (standard deviation)
            if len(distances) > 1:
                metrics['distance_variability'] = round(np.std(distances), 2)
            else:
                metrics['distance_variability'] = 0.0

            # Commute convenience score
            # Formula: 1.0 - normalized weighted combination of distance and variability
            distance_norm = min(1.0, distance_home_club / 10)  # normalize to 10km
            variability_norm = min(1.0, metrics['distance_variability'] / 5)  # normalize to 5km

            convenience = 1.0 - (
                0.7 * distance_norm +      # 70% weight on home-to-club distance
                0.3 * variability_norm     # 30% weight on variability
            )
            metrics['commute_convenience_score'] = round(max(0, min(1, convenience)), 4)

            # Data quality assessment
            if home['sample_size'] >= 20 and home['confidence'] >= 30:
                metrics['location_data_quality'] = 'good'
            elif home['sample_size'] >= 10 and home['confidence'] >= 20:
                metrics['location_data_quality'] = 'medium'
            else:
                metrics['location_data_quality'] = 'poor'
    else:
        # Not enough data for booking distance metrics
        metrics['location_data_quality'] = 'insufficient'

    return metrics


def main():
    """Main function to calculate location metrics"""
    print("\n" + "=" * 70)
    print("CALCULATING LOCATION METRICS FOR USERS")
    print("=" * 70)

    # Connect to databases
    print("\n1. Connecting to databases...")
    pg = PostgresConnector()
    mongo = MongoConnector()

    # Get location data from MongoDB FIRST to know which users have data
    print("\n2. Loading location data from MongoDB...")
    collection = mongo.get_collection('userslocations')

    # Get unique user IDs with locations
    print("   Getting unique users with location data...")
    mongo_user_ids = collection.distinct('userId')
    mongo_user_ids_str = [str(uid) for uid in mongo_user_ids]
    print(f"   Users with location data in MongoDB: {len(mongo_user_ids_str):,}")

    # Get user data from PostgreSQL - ONLY users with location data
    print("\n3. Loading user data from PostgreSQL (only users with locations)...")

    # Convert list to SQL-compatible format
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
    print(f"   Loaded {len(df_users)} users with clubs and locations")

    # Load all locations
    print("\n4. Loading all location records from MongoDB...")
    collection = mongo.get_collection('userslocations')

    # Load locations
    locations_data = list(collection.find())
    print(f"   Loaded {len(locations_data)} location records")

    # Convert to DataFrame
    df_locations = pd.DataFrame(locations_data)

    # Extract coordinates from nested location dict
    if 'location' in df_locations.columns:
        df_locations['latitude'] = df_locations['location'].apply(
            lambda x: x.get('latitude') if isinstance(x, dict) else None
        )
        df_locations['longitude'] = df_locations['location'].apply(
            lambda x: x.get('longitude') if isinstance(x, dict) else None
        )

    # Convert userId to string for matching
    df_locations['userId'] = df_locations['userId'].astype(str)
    df_users['user_id'] = df_users['user_id'].astype(str)

    # Remove records without coordinates
    df_locations = df_locations[
        df_locations['latitude'].notna() &
        df_locations['longitude'].notna()
    ]
    print(f"   Valid location records: {len(df_locations)}")

    # Calculate metrics for each user
    print("\n5. Calculating metrics for each user...")
    results = []

    for idx, row in df_users.iterrows():
        if (idx + 1) % 100 == 0:
            print(f"   Processed {idx + 1}/{len(df_users)} users...")

        metrics = calculate_user_metrics(
            user_id=row['user_id'],
            club_name=row['club_name'],
            df_locations=df_locations
        )
        results.append(metrics)

    df_metrics = pd.DataFrame(results)

    # Summary statistics
    print("\n6. Summary Statistics:")
    print("=" * 70)
    print(f"Total users: {len(df_metrics)}")
    print(f"Users with location data: {(df_metrics['location_sample_size'] > 0).sum()}")
    print(f"Users with good quality data: {(df_metrics['location_data_quality'] == 'good').sum()}")
    print(f"\nData quality breakdown:")
    print(df_metrics['location_data_quality'].value_counts())

    print(f"\nDistance statistics (users with data):")
    valid_distances = df_metrics[df_metrics['distance_home_to_club_km'].notna()]
    if len(valid_distances) > 0:
        print(f"  Mean distance: {valid_distances['distance_home_to_club_km'].mean():.2f} km")
        print(f"  Median distance: {valid_distances['distance_home_to_club_km'].median():.2f} km")
        print(f"  Users within 2km: {valid_distances['is_home_nearby'].sum()} ({valid_distances['is_home_nearby'].mean()*100:.1f}%)")

    print(f"\nCommute convenience score (users with data):")
    valid_scores = df_metrics[df_metrics['commute_convenience_score'].notna()]
    if len(valid_scores) > 0:
        print(f"  Mean score: {valid_scores['commute_convenience_score'].mean():.4f}")
        print(f"  Median score: {valid_scores['commute_convenience_score'].median():.4f}")

    # Save to CSV
    output_dir = Path(__file__).parent.parent / 'data' / 'processed'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f'user_location_metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

    df_metrics.to_csv(output_file, index=False)
    print(f"\n7. Results saved to: {output_file}")

    # Sample output
    print("\n8. Sample results (first 5 users with data):")
    print("=" * 70)
    sample = df_metrics[df_metrics['distance_home_to_club_km'].notna()].head()
    if len(sample) > 0:
        for _, row in sample.iterrows():
            print(f"\nUser: {row['user_id']}")
            print(f"  Home: ({row['home_latitude']:.4f}, {row['home_longitude']:.4f})")
            print(f"  Confidence: {row['home_location_confidence']:.1f}%")
            print(f"  Distance to club: {row['distance_home_to_club_km']:.2f} km")
            print(f"  Avg booking distance: {row['avg_booking_distance_km']:.2f} km")
            print(f"  Variability: {row['distance_variability']:.2f} km")
            print(f"  Is nearby: {row['is_home_nearby']}")
            print(f"  Convenience score: {row['commute_convenience_score']:.4f}")
            print(f"  Data quality: {row['location_data_quality']}")

    # Close connections
    mongo.close()

    print("\n" + "=" * 70)
    print("CALCULATION COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Review the output file and verify metrics")
    print("2. Update CLUB_COORDINATES with actual club coordinates if needed")
    print("3. Run on full dataset (remove LIMIT in SQL query)")
    print("4. Integrate metrics into core_users table")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
