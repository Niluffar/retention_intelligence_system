-- =========================================
-- ris.core_user
-- Профиль пользователя и внутренние факторы
-- 1 строка = 1 пользователь
-- =========================================

-- TODO: Этот файл нужно будет доработать после изучения MongoDB схемы

DROP TABLE IF EXISTS ris.core_user CASCADE;

CREATE TABLE ris.core_user (
    -- Идентификаторы
    user_id VARCHAR(50) PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- === ВНУТРЕННИЕ ФАКТОРЫ ===
    -- TODO: Добавить/изменить поля на основе реальной структуры MongoDB

    -- Демографические данные
    age INTEGER,
    gender VARCHAR(20),
    weight_kg DECIMAL(5,2),
    height_cm DECIMAL(5,2),
    fat_percentage DECIMAL(5,2),
    bmi DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE
            WHEN height_cm > 0 THEN weight_kg / POWER(height_cm / 100, 2)
            ELSE NULL
        END
    ) STORED,

    -- Локация и работа
    location VARCHAR(100),
    club_primary VARCHAR(100),
    work_type VARCHAR(50), -- office/freelancer/other
    job_position VARCHAR(100),
    finance_segment VARCHAR(50),
    transportation_mean VARCHAR(50),

    -- Семья
    has_children BOOLEAN,

    -- Опыт в фитнесе
    fitness_experience VARCHAR(50), -- beginner/intermediate/advanced
    fitness_goal VARCHAR(100),

    -- Социальные характеристики
    personality_type VARCHAR(50), -- extrovert/introvert (by friends count)
    friends_count INTEGER DEFAULT 0,
    in_clan BOOLEAN DEFAULT FALSE,
    clan_id VARCHAR(50),

    -- Поведение в приложении (базовый профиль)
    is_feed_user BOOLEAN DEFAULT FALSE,
    is_leaderboard_user BOOLEAN DEFAULT FALSE,
    is_achievements_user BOOLEAN DEFAULT FALSE,
    social_posts_total INTEGER DEFAULT 0,

    -- Онбординг
    referral_type VARCHAR(50),
    referrer_user_id VARCHAR(50),
    had_trial BOOLEAN DEFAULT FALSE,
    trial_duration_days INTEGER,

    -- Первый HeroPass
    first_hp_start DATE,
    first_hp_type VARCHAR(50),
    first_hp_club VARCHAR(100),

    -- Текущий статус
    current_hp_id VARCHAR(50),
    current_hp_status VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,

    -- Паттерны планирования (baseline)
    planning_horizon_days DECIMAL(5,2),
    cancellation_rate_baseline DECIMAL(5,4),
    reschedule_rate_baseline DECIMAL(5,4),
    preferred_time_slot VARCHAR(50),
    preferred_days VARCHAR(100),

    -- Engagement baseline
    engagement_baseline DECIMAL(5,2),
    sessions_per_week_baseline DECIMAL(5,2),

    -- Технические
    notification_enabled BOOLEAN DEFAULT TRUE,
    app_version VARCHAR(20),
    platform VARCHAR(20),

    -- Метаданные
    data_completeness_score DECIMAL(5,4),
    last_activity_date DATE,

    CONSTRAINT chk_age CHECK (age >= 14 AND age <= 100),
    CONSTRAINT chk_weight CHECK (weight_kg > 0 AND weight_kg < 300),
    CONSTRAINT chk_height CHECK (height_cm > 0 AND height_cm < 250),
    CONSTRAINT chk_fat_pct CHECK (fat_percentage >= 0 AND fat_percentage <= 100)
);

-- Indexes
CREATE INDEX idx_core_user_active ON ris.core_user(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_core_user_club ON ris.core_user(club_primary);
CREATE INDEX idx_core_user_hp ON ris.core_user(current_hp_id);
CREATE INDEX idx_core_user_created ON ris.core_user(created_at);

-- Comments
COMMENT ON TABLE ris.core_user IS 'Профиль пользователя и внутренние факторы';
COMMENT ON COLUMN ris.core_user.personality_type IS 'Тип личности (extrovert/introvert), определяется по количеству друзей';
COMMENT ON COLUMN ris.core_user.engagement_baseline IS 'Базовый engagement - персональная норма';


-- =========================================
-- NOTES для доработки после изучения MongoDB:
-- =========================================
-- 1. Проверить какие поля есть в MongoDB для пользователей
-- 2. Добавить mapping MongoDB field names → RIS column names
-- 3. Определить логику для derived полей:
--    - personality_type (по friends_count)
--    - is_feed_user (по кол-ву постов)
--    - is_leaderboard_user (по активности просмотров)
--    - engagement_baseline (рассчитывается из истории)
-- 4. Проверить типы данных и nullable полей
-- 5. Добавить дополнительные constraints если нужно
