# Getting Started - Retention Intelligence System

## Что было создано

Вы получили полноценную структуру проекта для создания **Retention Intelligence System** для Hero's Journey. Система будет предсказывать вероятность продления HeroPass клиентами на основе внутренних и внешних факторов.

## Информация о Hero's Journey

**Hero's Journey** — это геймифицированная фитнес-студия из Казахстана, которая:
- Объединяет групповые тренировки с игровыми механиками
- Использует 8-10 станций-тренажеров в круговом формате
- Отслеживает веса, пульс, прогресс через планшеты на станциях
- Мотивирует через персонажа в приложении, который прокачивается от тренировок
- Имеет клубы в Алматы и Астане, планирует расширение в США

## Структура проекта

```
retention_intelligence_system/
├── config/                  # Конфигурации и credentials
├── sql/schemas/             # SQL DDL для создания таблиц
├── src/                     # Python код
│   ├── utils/               # Коннекторы к БД, логгер
│   ├── data_engineering/    # ETL и витрины
│   ├── features/            # Feature engineering
│   ├── models/              # ML модели
│   ├── scoring/             # Скоринг пользователей
│   └── monitoring/          # Мониторинг и DQ
├── notebooks/               # Jupyter notebooks для анализа
├── scripts/                 # CLI скрипты
└── data/                    # Локальные данные
```

## Архитектура витрин данных (PostgreSQL schema: ris)

### Core витрины
1. **ris.core_user** — профиль пользователя + внутренние факторы (1 строка на юзера)
2. **ris.core_hp_period** — периоды HeroPass + hp_end_corrected (с учётом фриза)
3. **ris.fact_user_week** — недельные метрики поведения + персональные нормы + дельты

### Таргеты и модельные витрины
4. **ris.label_hp** — таргеты продления (30/60/90 дней после hp_end_corrected)
5. **ris.interval_hp** — интервалы (недели) для дискретной survival-модели

### Служебные таблицы
6. **ris.ref_calendar** — календарь с сезонностью и праздниками
7. **ris.meta_feature_catalog** — каталог всех фич
8. **ris.dq_feature_stats** — статистики для Data Quality
9. **ris.model_importance** — feature importance из моделей
10. **ris.model_calibration** — калибровка моделей
11. **ris.model_bands** — риск-бэнды для скоринга
12. **ris.model_scores_daily** — ежедневные scores для активных юзеров

## Факторы для моделирования

### Внутренние факторы (характеристики личности)
Определяют "норму" поведения для каждого пользователя:
- Демография: возраст, пол, вес, рост, fat%
- Локация, работа (офис/фриланс), транспорт
- Опыт в фитнесе, цель
- Личность: экстраверт/интроверт (по друзьям), in_clan
- Social commitment, feed/leaderboard/achievements usage
- Онбординг: referral/individual, trial

### Внешние факторы (изменения поведения)
Показывают отклонения от нормы — **главные сигналы риска**:
- **Дельты engagement**: sessions, completion_rate, cancellation_rate
- **Дельты прогресса**: веса, inBody, assessment
- **Дельты активности**: time_in_app, steps, social_posts
- Техподдержка (тон обращений)
- Сезонность (внешняя и внутренняя)
- Изменения паттернов бронирования
- Использование HRM, weight entries
- Freeze behavior

## Следующие шаги

### Шаг 1: Настройка окружения

```bash
# Создать виртуальное окружение
python -m venv venv

# Активировать (Windows)
venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt
```

### Шаг 2: Настройка credentials

```bash
# Скопировать .env.example в .env
cp config\.env.example config\.env

# Заполнить credentials в config\.env
# - PostgreSQL (host, port, user, password)
# - MongoDB (host, port, user, password)
```

### Шаг 3: Исследование MongoDB

```bash
# Запустить скрипт для изучения структуры MongoDB
python scripts/explore_mongo.py
```

Этот скрипт поможет:
- Увидеть все коллекции в MongoDB
- Изучить схему каждой коллекции
- Сохранить схемы в `data/schemas/`

**Важно**: На основе этой информации нужно будет:
1. Определить mapping MongoDB полей → RIS витрины
2. Доработать SQL скрипты (сейчас они шаблонные)
3. Создать ETL логику для трансформации данных

### Шаг 4: Создание витрин в PostgreSQL

После доработки SQL скриптов:

```bash
# Создать схему и таблицы
python scripts/setup_postgres.py
```

### Шаг 5: EDA и Feature Engineering

Открыть Jupyter notebooks:

```bash
jupyter notebook
```

Начать с:
- `notebooks/01_mongo_exploration.ipynb` — изучение MongoDB данных
- `notebooks/02_eda_users.ipynb` — анализ пользователей
- `notebooks/03_eda_behavior.ipynb` — анализ поведения

## Ключевые файлы для начала

### Python коннекторы
- `src/utils/db_connectors.py` — готовые классы для работы с PostgreSQL и MongoDB
- `src/data_engineering/mongo_extractor.py` — извлечение данных из MongoDB
- `src/data_engineering/postgres_loader.py` — загрузка в PostgreSQL

### SQL шаблоны
- `sql/schemas/01_create_schema.sql` — создание схемы ris
- `sql/schemas/02_core_user_template.sql` — шаблон таблицы пользователей (требует доработки)

### Скрипты
- `scripts/explore_mongo.py` — **начните отсюда!**
- `scripts/setup_postgres.py` — создание таблиц

## Концепция моделирования

### Персональные нормы
Для каждого пользователя рассчитываем его "норму" (baseline) по каждой метрике:
- EWMA (экспоненциальное скользящее среднее)
- Квантили (25th, 50th, 75th)

Пример: для интроверта норма — 2 сессии в неделю, для экстраверта — 4 сессии.

### Дельты от нормы
Ключевые фичи — это **отклонения от персональной нормы**:
```
delta = actual_value - ewma_baseline
```

Пример:
- Обычно ходит 3 раза в неделю → на этой неделе 1 раз → delta = -2 → **риск!**
- Обычно отменяет 10% сессий → теперь 30% → delta = +20% → **риск!**

### Модели

**Baseline**: Logistic Regression
**Advanced**: XGBoost, LightGBM
**Survival Analysis**: Cox Proportional Hazards

**Таргет**: `renewed_30d` / `renewed_60d` / `renewed_90d` из `ris.label_hp`

## Полезные команды

```bash
# Исследовать MongoDB
python scripts/explore_mongo.py

# Создать PostgreSQL схему
python scripts/setup_postgres.py

# Запустить Jupyter
jupyter notebook

# Запустить тесты (когда будут готовы)
pytest tests/

# Обучить модель (когда будет готово)
python scripts/train_model.py

# Сгенерировать скоры (когда будет готово)
python scripts/generate_scores.py
```

## Дальнейшие этапы разработки

1. **Текущий этап**: Data Discovery
   - Изучение MongoDB структуры
   - Mapping полей
   - Доработка SQL DDL

2. **Этап 2**: Data Engineering
   - ETL pipeline MongoDB → PostgreSQL
   - Расчет недельных агрегатов
   - Расчет персональных норм и дельт

3. **Этап 3**: EDA & Feature Engineering
   - Exploratory analysis
   - Feature engineering
   - Feature selection

4. **Этап 4**: Modeling
   - Baseline модели
   - Advanced модели
   - Evaluation & tuning

5. **Этап 5**: Production
   - Batch scoring
   - Monitoring
   - Retraining pipeline

## Поддержка

См. также:
- [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md) — полная структура проекта
- [README.md](../README.md) — overview проекта
- `config/config.yaml` — конфигурация системы

## Вопросы для уточнения

Перед началом работы с данными уточните:

1. **MongoDB структура**:
   - Какие коллекции содержат данные пользователей?
   - Где хранятся HeroPass subscriptions?
   - Где данные о сессиях/тренировках?

2. **Доступность данных**:
   - Все ли внутренние факторы есть в MongoDB?
   - Какие факторы нужно будет вычислять?
   - Какие факторы недоступны (нужны assumptions)?

3. **Таргет**:
   - Как определить продление HeroPass?
   - Есть ли явное поле "renewed"?
   - Или нужно смотреть по последовательности purchase?

**Начните с `python scripts/explore_mongo.py` чтобы ответить на эти вопросы!**
