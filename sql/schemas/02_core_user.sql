

DROP TABLE IF EXISTS ris.core_user CASCADE;

CREATE TABLE ris.core_user (
    user_id VARCHAR(50) PRIMARY KEY,
    nickname VARCHAR(100),
    firstname VARCHAR(100),
    lastname VARCHAR(100),
    gender VARCHAR(20),
    birthdate VARCHAR(50),  -- Original format from source
    age INTEGER,
    age_band VARCHAR(20),   -- '<18', '18-24', '25-34', etc.
    phonenumber VARCHAR(50),
    user_created_at DATE,
    weight_kg DECIMAL(6,2),
    height_cm DECIMAL(6,2),
    fat_pct_latest DECIMAL(5,2),
    bmi_latest DECIMAL(5,2),
    default_club_corr VARCHAR(100),  -- Corrected club name (merged/renamed)
    city VARCHAR(50),                -- Almaty or Astana
    in_clan BOOLEAN DEFAULT FALSE,
    friends_cnt INTEGER DEFAULT 0,
    feed_posts_total INTEGER DEFAULT 0,
    active_lifestyle BOOLEAN,        -- From questionnaire
    bodytype VARCHAR(50),            -- Slim, Muscular, Overweight-prone
    fitness_goal VARCHAR(100),       -- Weight loss, Muscle gain, etc.
    first_hp DATE,
    first_hp_end DATE,
    first_hp_name VARCHAR(100),
    second_hp DATE,
    second_hp_end DATE,
    second_hp_name VARCHAR(100),
    third_hp DATE,
    third_hp_end DATE,
    third_hp_name VARCHAR(100),
    fourth_hp DATE,
    fourth_hp_end DATE,
    fourth_hp_name VARCHAR(100),
    fifth_hp DATE,
    fifth_hp_end DATE,
    fifth_hp_name VARCHAR(100),
    ever_hp BOOLEAN DEFAULT FALSE,   -- Has ever had HeroPass
    trial_before_hp BOOLEAN DEFAULT FALSE,
    trial_type VARCHAR(100),         -- Marathon name
    trial_payment VARCHAR(20),       -- 'gift' or 'paid'
    home_latitude DECIMAL(10, 7),
    home_longitude DECIMAL(10, 7),
    home_location_confidence DECIMAL(5, 2),  -- Percentage
    location_sample_size INTEGER DEFAULT 0,
    distance_home_to_club_km DECIMAL(6, 2),
    avg_booking_distance_km DECIMAL(6, 2),
    min_booking_distance_km DECIMAL(6, 2),
    distance_variability DECIMAL(6, 2),
    is_home_nearby BOOLEAN DEFAULT FALSE,    -- < 2 km
    commute_convenience_score DECIMAL(5, 4), -- 0-1 score
    location_data_quality VARCHAR(20),  -- 'good', 'medium', 'poor', 'insufficient', 'none'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_core_user_club ON ris.core_user(default_club_corr);
CREATE INDEX idx_core_user_city ON ris.core_user(city);
CREATE INDEX idx_core_user_ever_hp ON ris.core_user(ever_hp);
CREATE INDEX idx_core_user_created ON ris.core_user(user_created_at);
CREATE INDEX idx_core_user_home_nearby ON ris.core_user(is_home_nearby) WHERE is_home_nearby = TRUE;
CREATE INDEX idx_core_user_distance ON ris.core_user(distance_home_to_club_km) WHERE distance_home_to_club_km IS NOT NULL;
CREATE INDEX idx_core_user_loc_quality ON ris.core_user(location_data_quality);

CREATE INDEX idx_core_user_first_hp ON ris.core_user(first_hp);
COMMENT ON TABLE ris.core_user IS 'User profile and internal factors for retention prediction';
COMMENT ON COLUMN ris.core_user.user_id IS 'MongoDB user ID (ObjectId as string)';
COMMENT ON COLUMN ris.core_user.age_band IS 'Age group: <18, 18-24, 25-34, 35-44, 45-54, 55-64, 65+';
COMMENT ON COLUMN ris.core_user.default_club_corr IS 'Primary club with corrections applied (merged clubs)';
COMMENT ON COLUMN ris.core_user.city IS 'City: Almaty or Astana';
COMMENT ON COLUMN ris.core_user.in_clan IS 'Member of any clan (admin, user, or mentor)';
COMMENT ON COLUMN ris.core_user.friends_cnt IS 'Latest friend count from friends_history';
COMMENT ON COLUMN ris.core_user.feed_posts_total IS 'Total posted posts in social feed';
COMMENT ON COLUMN ris.core_user.active_lifestyle IS 'From questionnaire: leads active lifestyle';
COMMENT ON COLUMN ris.core_user.bodytype IS 'Body type: Slim, Muscular, Overweight-prone';
COMMENT ON COLUMN ris.core_user.fitness_goal IS 'Primary fitness goal';
COMMENT ON COLUMN ris.core_user.first_hp IS 'Start date of first HeroPass';
COMMENT ON COLUMN ris.core_user.ever_hp IS 'TRUE if user has ever purchased HeroPass';
COMMENT ON COLUMN ris.core_user.trial_before_hp IS 'Had trial marathon before first HeroPass';
COMMENT ON COLUMN ris.core_user.trial_payment IS 'Trial payment type: gift or paid';
COMMENT ON COLUMN ris.core_user.home_latitude IS 'Estimated home latitude (from location patterns)';
COMMENT ON COLUMN ris.core_user.home_longitude IS 'Estimated home longitude (from location patterns)';
COMMENT ON COLUMN ris.core_user.home_location_confidence IS 'Confidence % of home detection (top cluster frequency)';
COMMENT ON COLUMN ris.core_user.location_sample_size IS 'Number of location points used for calculation';
COMMENT ON COLUMN ris.core_user.distance_home_to_club_km IS 'Distance from home to primary club (km)';
COMMENT ON COLUMN ris.core_user.avg_booking_distance_km IS 'Average distance from booking locations to club (km)';
COMMENT ON COLUMN ris.core_user.distance_variability IS 'Std deviation of booking distances (mobility indicator)';
COMMENT ON COLUMN ris.core_user.is_home_nearby IS 'TRUE if home is within 2km of club';
COMMENT ON COLUMN ris.core_user.commute_convenience_score IS 'Convenience score 0-1 (1=very convenient, 0=inconvenient)';
COMMENT ON COLUMN ris.core_user.location_data_quality IS 'Data quality: good, medium, poor, insufficient, none';


