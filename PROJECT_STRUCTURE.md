# Retention Intelligence System - Project Structure

## Обзор архитектуры

```
retention_intelligence_system/
│
├── config/                          # Конфигурации
│   ├── config.yaml                  # Основной конфиг (DB, модели, параметры)
│   └── .env.example                 # Пример переменных окружения
│
├── sql/                             # SQL скрипты
│   ├── schemas/                     # DDL - создание таблиц
│   │   ├── 01_create_schema.sql     # Создание схемы ris
│   │   ├── 02_core_user.sql         # Таблица пользователей
│   │   ├── 03_core_hp_period.sql    # Таблица периодов HeroPass
│   │   ├── 04_ref_calendar.sql      # Календарь
│   │   ├── 05_core_user_subscription.sql # Completion rate по абонементам
│   │   ├── 06_fact_user_week.sql    # Недельные метрики
│   │   ├── 07_label_hp.sql          # Таргеты для моделей
│   │   ├── 08_interval_hp.sql       # Интервалы для survival
│   │   └── 09_meta_tables.sql       # Служебные таблицы
│   │
│   ├── marts/                       # DML - заполнение витрин
│   │   ├── populate_core_user.sql
│   │   ├── populate_fact_user_week.sql
│   │   └── populate_labels.sql
│   │
│   ├── views/                       # Views для удобного доступа
│   │   └── vw_user_features.sql
│   │
│   └── procedures/                  # Stored procedures (опционально)
│       └── calculate_user_norms.sql
│
├── src/                             # Python код
│   ├── __init__.py
│   │
│   ├── utils/                       # Утилиты
│   │   ├── __init__.py
│   │   ├── db_connectors.py         # PostgreSQL и MongoDB коннекторы
│   │   ├── logger.py                # Настройка логирования
│   │   └── config_loader.py         # Загрузка конфигов
│   │
│   ├── data_engineering/            # ETL и создание витрин
│   │   ├── __init__.py
│   │   ├── mongo_extractor.py       # Извлечение из MongoDB
│   │   ├── postgres_loader.py       # Загрузка в PostgreSQL
│   │   ├── transform_users.py       # Трансформация user данных
│   │   ├── transform_sessions.py    # Трансформация сессий
│   │   └── build_features_weekly.py # Построение недельных фич
│   │
│   ├── features/                    # Feature engineering
│   │   ├── __init__.py
│   │   ├── internal_factors.py      # Внутренние факторы
│   │   ├── external_factors.py      # Внешние факторы (дельты)
│   │   ├── engagement_score.py      # Composite engagement метрики
│   │   └── feature_store.py         # Feature store (опционально)
│   │
│   ├── models/                      # ML модели
│   │   ├── __init__.py
│   │   ├── baseline.py              # Baseline модели (LogReg)
│   │   ├── xgboost_model.py         # XGBoost
│   │   ├── survival_model.py        # Survival analysis (Cox, AFT)
│   │   ├── ensemble.py              # Ансамбли
│   │   └── train.py                 # Training pipeline
│   │
│   ├── scoring/                     # Inference и скоринг
│   │   ├── __init__.py
│   │   ├── predict.py               # Batch prediction
│   │   ├── score_users.py           # Скоринг активных юзеров
│   │   └── risk_bands.py            # Присвоение риск-бэндов
│   │
│   └── monitoring/                  # Мониторинг и DQ
│       ├── __init__.py
│       ├── data_quality.py          # Data quality checks
│       ├── feature_drift.py         # Feature drift detection
│       └── model_performance.py     # Мониторинг модели
│
├── notebooks/                       # Jupyter notebooks
│   ├── 01_mongo_exploration.ipynb   # Изучение MongoDB
│   ├── 02_eda_users.ipynb           # EDA пользователей
│   ├── 03_eda_behavior.ipynb        # EDA поведения
│   ├── 04_feature_engineering.ipynb # Feature engineering
│   ├── 05_baseline_models.ipynb     # Baseline модели
│   ├── 06_advanced_models.ipynb     # Advanced модели
│   └── 07_model_evaluation.ipynb    # Оценка моделей
│
├── scripts/                         # CLI скрипты
│   ├── explore_mongo.py             # Исследование MongoDB
│   ├── setup_postgres.py            # Создание схемы PostgreSQL
│   ├── build_marts.py               # Построение витрин
│   ├── train_model.py               # Обучение модели
│   └── generate_scores.py           # Генерация скоров
│
├── tests/                           # Тесты
│   ├── unit/                        # Unit tests
│   │   ├── test_connectors.py
│   │   ├── test_features.py
│   │   └── test_models.py
│   │
│   └── integration/                 # Integration tests
│       ├── test_etl_pipeline.py
│       └── test_scoring_pipeline.py
│
├── data/                            # Локальные данные (не в git)
│   ├── raw/                         # Сырые данные из MongoDB
│   ├── processed/                   # Обработанные данные
│   ├── interim/                     # Промежуточные данные
│   └── schemas/                     # Схемы MongoDB коллекций
│
├── models/                          # Сохраненные модели (не в git)
│   ├── baseline_v1.pkl
│   ├── xgboost_v1.pkl
│   └── metadata/
│
├── logs/                            # Логи (не в git)
│
├── reports/                         # Отчеты и визуализации
│   ├── model_performance/
│   └── data_quality/
│
├── docs/                            # Документация
│   ├── data_dictionary.md           # Словарь данных
│   ├── feature_catalog.md           # Каталог фич
│   ├── model_cards/                 # Model cards
│   └── runbooks/                    # Инструкции
│
├── .gitignore
├── requirements.txt                 # Python зависимости
├── README.md                        # Описание проекта
└── PROJECT_STRUCTURE.md             # Этот файл

```

## Ключевые компоненты

### 1. Data Engineering (`src/data_engineering/`)
- Извлечение данных из MongoDB
- Трансформация и очистка
- Загрузка в PostgreSQL витрины
- Расчет недельных агрегатов и дельт

### 2. Feature Engineering (`src/features/`)
- **Internal factors**: демография, личность, базовые паттерны
- **External factors**: поведенческие дельты, engagement changes
- Расчет персональных норм (EWMA, квантили)
- Composite метрики

### 3. Models (`src/models/`)
- **Baseline**: Logistic Regression
- **Tree-based**: XGBoost, LightGBM, CatBoost
- **Survival**: Cox Proportional Hazards, AFT
- **Ensemble**: Stacking, blending

### 4. Scoring (`src/scoring/`)
- Batch prediction для всех активных пользователей
- Real-time scoring (будущее)
- Risk band assignment
- Explainability (SHAP, feature importance)

### 5. Monitoring (`src/monitoring/`)
- Data quality checks
- Feature drift detection
- Model performance tracking
- Alerting

## Workflow

### Phase 1: Data Discovery (текущая фаза)
1. ✅ Создание структуры проекта
2. 🔄 Изучение MongoDB коллекций (`scripts/explore_mongo.py`)
3. 🔄 Mapping MongoDB → PostgreSQL витрины
4. 🔄 Создание SQL схем (`sql/schemas/`)

### Phase 2: Data Engineering
1. Создание витрин в PostgreSQL
2. ETL pipeline: MongoDB → PostgreSQL
3. Расчет недельных агрегатов
4. Расчет персональных норм и дельт

### Phase 3: EDA & Feature Engineering
1. Exploratory Data Analysis (notebooks)
2. Feature engineering
3. Feature selection
4. Data quality validation

### Phase 4: Modeling
1. Train/test split
2. Baseline models
3. Advanced models
4. Model evaluation & selection

### Phase 5: Production
1. Batch scoring pipeline
2. Monitoring & alerting
3. Model retraining
4. API (опционально)

## Следующие шаги

1. **Сейчас**: Исследовать MongoDB с помощью `scripts/explore_mongo.py`
2. Определить mapping MongoDB полей → RIS витрины
3. Доработать SQL скрипты для витрин
4. Запустить ETL pipeline
5. EDA и feature engineering

## Полезные команды

```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Explore MongoDB
python scripts/explore_mongo.py

# Setup PostgreSQL schema
python scripts/setup_postgres.py

# Build data marts
python scripts/build_marts.py

# Train model
python scripts/train_model.py

# Generate scores
python scripts/generate_scores.py

# Run tests
pytest tests/
```
