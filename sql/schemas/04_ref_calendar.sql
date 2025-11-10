-- =====================================================================
-- TABLE: ris.ref_calendar
-- Description: Календарь с сезонностью и праздниками для анализа временных паттернов
-- =====================================================================

DROP TABLE IF EXISTS ris.ref_calendar CASCADE;

CREATE TABLE ris.ref_calendar (
    -- Primary key
    dt                  DATE PRIMARY KEY,

    -- Temporal attributes
    dow                 SMALLINT NOT NULL,          -- Day of week (1=Monday, 7=Sunday)
    is_weekend          BOOLEAN NOT NULL,           -- True if Saturday or Sunday
    week_of_year        SMALLINT NOT NULL,          -- Week number (1-53)
    month               SMALLINT NOT NULL,          -- Month (1-12)
    quarter             SMALLINT NOT NULL,          -- Quarter (1-4)
    year                INTEGER NOT NULL,           -- Year

    -- Special days
    is_holiday_kz       BOOLEAN DEFAULT FALSE,      -- Kazakhstan public holidays
    is_school_break     BOOLEAN DEFAULT FALSE,      -- School vacation periods
    season_label        TEXT,                       -- Season: winter, spring, summer, autumn

    -- Metadata
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_ref_calendar_year_month ON ris.ref_calendar(year, month);
CREATE INDEX idx_ref_calendar_is_holiday ON ris.ref_calendar(is_holiday_kz);
CREATE INDEX idx_ref_calendar_is_weekend ON ris.ref_calendar(is_weekend);
CREATE INDEX idx_ref_calendar_season ON ris.ref_calendar(season_label);

-- Comments
COMMENT ON TABLE ris.ref_calendar IS 'Календарь с сезонностью и праздниками для анализа retention паттернов';
COMMENT ON COLUMN ris.ref_calendar.dt IS 'Дата (первичный ключ)';
COMMENT ON COLUMN ris.ref_calendar.dow IS 'День недели (1=Понедельник, 7=Воскресенье)';
COMMENT ON COLUMN ris.ref_calendar.is_weekend IS 'Выходной день (суббота или воскресенье)';
COMMENT ON COLUMN ris.ref_calendar.week_of_year IS 'Номер недели в году (1-53)';
COMMENT ON COLUMN ris.ref_calendar.month IS 'Месяц (1-12)';
COMMENT ON COLUMN ris.ref_calendar.quarter IS 'Квартал (1-4)';
COMMENT ON COLUMN ris.ref_calendar.year IS 'Год';
COMMENT ON COLUMN ris.ref_calendar.is_holiday_kz IS 'Государственный праздник Казахстана';
COMMENT ON COLUMN ris.ref_calendar.is_school_break IS 'Школьные каникулы';
COMMENT ON COLUMN ris.ref_calendar.season_label IS 'Сезон: winter, spring, summer, autumn';
