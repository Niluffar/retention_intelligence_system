-- =====================================================================
-- TABLE: ris.core_hp_period
-- Description: Периоды HeroPass с учетом заморозок и корректировок клубов
-- =====================================================================

DROP TABLE IF EXISTS ris.core_hp_period CASCADE;

CREATE TABLE ris.core_hp_period (
    -- Primary key
    hp_period_id        VARCHAR(50) PRIMARY KEY,

    -- User reference
    user_id             VARCHAR(50),  -- Nullable to allow data load, will filter later

    -- HeroPass details
    hp_type             VARCHAR(100),           -- 'Годовой Hero`s Pass' или 'Полугодовой Hero`s Pass'
    hp_club_corr        VARCHAR(100),           -- Клуб HeroPass (с коррекцией для закрытых)

    -- Date ranges
    hp_start            DATE NOT NULL,          -- Дата начала HeroPass
    hp_end              DATE NOT NULL,          -- Исходная дата окончания HeroPass
    hp_end_corrected    DATE NOT NULL,          -- Дата окончания с учетом заморозок

    -- Duration metrics
    hp_length_days      INTEGER,                -- Длительность периода (hp_end - hp_start + 1)
    freeze_days_total   INTEGER DEFAULT 0,      -- Общее количество дней заморозки

    -- Renewal tracking
    next_hp_purchase_dt DATE,                   -- Дата покупки следующего HeroPass

    -- Calculated fields
    days_to_next_hp     INTEGER,                -- Количество дней до следующего HP (next_hp_purchase_dt - hp_end_corrected)
    renewed             BOOLEAN,                -- Был ли продлен HP (next_hp_purchase_dt IS NOT NULL)
    gap_days            INTEGER,                -- Разрыв между окончанием и следующей покупкой (если renewed=true)

    -- Metadata
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_core_hp_period_user_id ON ris.core_hp_period(user_id);
CREATE INDEX idx_core_hp_period_hp_start ON ris.core_hp_period(hp_start);
CREATE INDEX idx_core_hp_period_hp_end_corrected ON ris.core_hp_period(hp_end_corrected);
CREATE INDEX idx_core_hp_period_renewed ON ris.core_hp_period(renewed);
CREATE INDEX idx_core_hp_period_user_start ON ris.core_hp_period(user_id, hp_start);

-- Comments
COMMENT ON TABLE ris.core_hp_period IS 'Периоды HeroPass пользователей с учетом заморозок и корректировок';
COMMENT ON COLUMN ris.core_hp_period.hp_period_id IS 'ID периода HeroPass (из raw.userheropass.id)';
COMMENT ON COLUMN ris.core_hp_period.user_id IS 'ID пользователя';
COMMENT ON COLUMN ris.core_hp_period.hp_type IS 'Тип HeroPass (годовой/полугодовой)';
COMMENT ON COLUMN ris.core_hp_period.hp_club_corr IS 'Клуб HeroPass с коррекцией для исторически закрытых клубов';
COMMENT ON COLUMN ris.core_hp_period.hp_start IS 'Дата начала HeroPass';
COMMENT ON COLUMN ris.core_hp_period.hp_end IS 'Исходная дата окончания HeroPass';
COMMENT ON COLUMN ris.core_hp_period.hp_end_corrected IS 'Дата окончания с учетом заморозок';
COMMENT ON COLUMN ris.core_hp_period.hp_length_days IS 'Длительность HeroPass в днях';
COMMENT ON COLUMN ris.core_hp_period.freeze_days_total IS 'Общее количество дней заморозки';
COMMENT ON COLUMN ris.core_hp_period.next_hp_purchase_dt IS 'Дата покупки следующего HeroPass';
COMMENT ON COLUMN ris.core_hp_period.days_to_next_hp IS 'Дней до следующего HP (для тех кто продлил)';
COMMENT ON COLUMN ris.core_hp_period.renewed IS 'Был ли продлен HeroPass';
COMMENT ON COLUMN ris.core_hp_period.gap_days IS 'Разрыв между окончанием и следующей покупкой (если продлен)';
