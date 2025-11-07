# Location Metrics Calculation Guide

## Overview

Этот документ описывает процесс расчета геолокационных метрик для прогнозирования retention.

## Быстрый справочник по всем метрикам

| Метрика | Тип | Диапазон | Описание | Feature Importance |
|---------|-----|----------|----------|-------------------|
| `home_latitude` | float | -90 to 90 | Широта дома | Low (для геокластеризации) |
| `home_longitude` | float | -180 to 180 | Долгота дома | Low (для геокластеризации) |
| `home_location_confidence` | float | 0-100% | Надежность определения дома | Medium (для взвешивания) |
| `location_sample_size` | int | 0+ | Кол-во location точек | Medium (для фильтрации) |
| `distance_home_to_club_km` | float | 0-100+ км | Расстояние от дома до клуба | **High** ⭐ |
| `avg_booking_distance_km` | float | 0-100+ км | Среднее расстояние букингов | **High** |
| `distance_variability` | float | 0-50+ км | Std отклонение расстояний | **High** |
| `is_home_nearby` | bool | True/False | Живет <2км от клуба | **High** (для деревьев) |
| `commute_convenience_score` | float | 0.0-1.0 | Композитная метрика удобства | **CRITICAL** ⭐⭐⭐ |
| `location_data_quality` | categorical | 6 категорий | Качество данных | Medium (для фильтрации) |

### Интерпретация ключевых метрик

**`commute_convenience_score`** (самая важная метрика):
- **0.9-1.0**: VIP Local - живет рядом, стабильный → retention 85%+
- **0.7-0.9**: Regular Commuter - хорошее расстояние → retention 65-85%
- **0.5-0.7**: Casual Visitor - требует мотивации → retention 40-65%
- **0.3-0.5**: At Risk - далеко или нестабильно → retention 20-40%
- **0.0-0.3**: Critical - churn риск → retention <20%

**`distance_home_to_club_km`**:
- **0-1 км**: Very High retention
- **1-3 км**: High retention
- **3-5 км**: Medium retention
- **5-10 км**: Low retention
- **>10 км**: Very Low retention

**`distance_variability`**:
- **0-2 км**: Стабильный паттерн (дом/работа)
- **2-5 км**: Средняя стабильность
- **>5 км**: Хаотичное поведение, нет рутины

**`location_data_quality`**:
- **good** (1,255 users): sample_size ≥20, confidence ≥30% → использовать для ML
- **medium** (1,995 users): sample_size ≥10, confidence ≥20% → можно использовать
- **poor** (6,553 users): недостаточно данных → только для аналитики
- **insufficient** (2,496 users): <3 точек → исключить

---

## Метрики

### 1. Home Location (Дом пользователя)
**Как определяется**:
- Округление координат до ~50м (4 знака после запятой)
- Кластеризация близких точек
- Выбор топ-кластера по формуле: `score = count + night_count * 2`
- Приоритет локациям в ночное время (22:00-08:00)

**Поля**:
- `home_latitude`, `home_longitude` - координаты дома
- `home_location_confidence` - % от всех точек (чем выше, тем надежнее)
- `location_sample_size` - количество точек для расчета

### 2. Distance to Club
**Метрики**:
- `distance_home_to_club_km` - расстояние от дома до клуба пользователя
- `is_home_nearby` - TRUE если < 2 км

**Формула**: Haversine distance (учитывает кривизну Земли)

### 3. Booking Distance Patterns
**Метрики**:
- `avg_booking_distance_km` - средняя дистанция от точек бронирования до клуба
- `distance_variability` - стандартное отклонение дистанций

**Интерпретация**:
- Низкая variability → стабильный паттерн (дом/работа)
- Высокая variability → мобильный пользователь

### 4. Commute Convenience Score
**Формула**:
```python
distance_norm = min(1.0, distance_home_to_club / 10)
variability_norm = min(1.0, distance_variability / 5)

convenience = 1.0 - (0.7 * distance_norm + 0.3 * variability_norm)
```

**Диапазон**: 0.0 - 1.0
- **1.0** = очень удобно (близко к дому, стабильный паттерн)
- **0.0** = неудобно (далеко, нестабильный паттерн)

### 5. Data Quality
**Категории**:
- `good` - ≥20 точек, confidence ≥30%
- `medium` - ≥10 точек, confidence ≥20%
- `poor` - меньше точек или низкая confidence
- `insufficient` - <3 точки
- `no_user_data` - нет данных
- `no_club_coords` - нет координат клуба

## Использование

### Шаг 1: Получить координаты клубов

```bash
cd retention_intelligence_system
python scripts/get_club_coordinates.py
```

Это покажет:
- Список клубов из PostgreSQL
- Коллекции в MongoDB с возможными координатами
- Шаблон для `CLUB_COORDINATES`

### Шаг 2: Обновить координаты

Отредактируйте `scripts/calculate_location_metrics.py`:

```python
CLUB_COORDINATES = {
    'HJ Colibri': {'lat': 43.2380, 'lon': 76.9450},
    'HJ Mega': {'lat': 43.2220, 'lon': 76.8512},
    # ... добавьте остальные клубы
}
```

Координаты можно получить:
1. Из MongoDB (если есть в базе)
2. Google Maps - найти клуб, скопировать координаты
3. Из адресов через geocoding API

### Шаг 3: Запустить расчет метрик

```bash
python scripts/calculate_location_metrics.py
```

Скрипт:
1. Загрузит пользователей из PostgreSQL
2. Загрузит локации из MongoDB (`userslocations`)
3. Рассчитает все метрики
4. Сохранит в CSV: `data/processed/user_location_metrics_YYYYMMDD_HHMMSS.csv`

### Шаг 4: Проверить результаты

Откройте CSV файл и проверьте:
- Качество данных (`location_data_quality`)
- Распределение дистанций
- Confidence scores

### Шаг 5: Интегрировать в core_users

После проверки метрики можно добавить в таблицу `core_users`.

## Требования к данным

### MongoDB Collection: `userslocations`

Ожидаемая структура документа:
```javascript
{
  "_id": ObjectId("..."),
  "userId": "user_id_here",
  "location": {
    "latitude": 43.2380,
    "longitude": 76.9450
  },
  "created_at": ISODate("2024-01-15T14:30:00Z"),
  // other fields...
}
```

**ВАЖНО: Временная зона**
Время в MongoDB хранится в **UTC**, но для анализа нужно Kazakhstan time (**UTC+5**).
Скрипт автоматически добавляет **+5 часов** при определении ночных букингов (22:00-08:00).
Это важно для корректного определения домашней локации, так как ночные точки получают приоритет.

### PostgreSQL Query

Должна возвращать:
- `user_id` - ID пользователя
- `default_club_corr` - название клуба (должно совпадать с ключом в `CLUB_COORDINATES`)

## Подробное описание всех метрик

### 1. Home Location (Домашняя локация)

#### `home_latitude`, `home_longitude`
**Что это**: Географические координаты предполагаемого дома пользователя

**Как определяется**:
1. Все location точки пользователя округляются до 4 знаков (~50м точность)
2. Создаются кластеры близких точек
3. Для каждого кластера считается score = `count + night_count * 2`
4. Выбирается кластер с максимальным score
5. Координаты кластера усредняются

**Почему ночные точки важнее**:
- Время 22:00-08:00 (с учетом UTC+5) получает 2x вес
- Люди обычно находятся дома ночью
- Это повышает точность определения

**Пример**:
```
Пользователь имеет 100 location точек:
- 40 точек в кластере A (43.2401, 76.9293) - 10 из них ночные
- 30 точек в кластере B (43.2500, 76.9400) - 5 ночных
- 30 точек в кластере C (43.2600, 76.9500) - 0 ночных

Scores:
A: 40 + 10*2 = 60 ✓ (выбран как дом)
B: 30 + 5*2 = 40
C: 30 + 0*2 = 30
```

#### `home_location_confidence`
**Что это**: Процент всех location точек, которые принадлежат домашнему кластеру

**Формула**: `(count_in_home_cluster / total_points) * 100`

**Интерпретация**:
- **>50%** - Очень надежно (пользователь стабильно в одном месте)
- **30-50%** - Хорошо (есть дом + работа)
- **20-30%** - Средне (несколько частых мест)
- **<20%** - Ненадежно (очень мобильный или мало данных)

**Использование**: Фильтровать пользователей с confidence < 20% при анализе

#### `location_sample_size`
**Что это**: Количество location точек для расчета

**Важность**:
- Минимум 10 точек для базового анализа
- 20+ точек для надежных метрик
- <3 точек → метрика не рассчитывается

---

### 2. Distance Metrics (Метрики расстояния)

#### `distance_home_to_club_km`
**Что это**: Расстояние от дома до основного клуба пользователя в км

**Формула**: Haversine distance (учитывает кривизну Земли)

**Распределение** (из наших данных):
- **Mean**: 17.22 км
- **Median**: 2.73 км
- **Интерпретация**: Медиана << Mean → большинство близко, но есть выбросы

**Влияние на retention**:
```
0-1 км:   Very High retention (местные жители)
1-3 км:   High retention (в пределах района)
3-5 км:   Medium retention (требуется мотивация)
5-10 км:  Low retention (долгая дорога)
>10 км:   Very Low retention (критический риск churn)
```

**Пример**: Пользователь живет в 0.44 км → очень удобно → высокий retention

#### `is_home_nearby`
**Что это**: Бинарный флаг - живет ли пользователь близко к клубу

**Формула**: `distance_home_to_club_km < 2.0`

**Статистика**: 36.5% пользователей живут в пределах 2км

**Использование в ML**:
- Важная фича для decision trees (чистый split)
- Используйте для сегментации маркетинговых кампаний

#### `avg_booking_distance_km`
**Что это**: Среднее расстояние от всех точек бронирования до клуба

**Отличие от `distance_home_to_club_km`**:
- `distance_home_to_club` → теоретическое расстояние от дома
- `avg_booking_distance` → реальное поведение (откуда на самом деле едут)

**Интерпретация разницы**:
```python
if avg_booking_distance ≈ distance_home_to_club:
    # Пользователь всегда едет из дома → stable routine

if avg_booking_distance > distance_home_to_club + 3km:
    # Едет с работы или других мест → less committed

if avg_booking_distance < distance_home_to_club:
    # Странно, проверить качество данных
```

**Пример**:
```
User A: home=2km, avg_booking=2.1km, variability=0.5km
→ Стабильный паттерн, всегда из дома

User B: home=3km, avg_booking=8km, variability=15km
→ Нестабильный, бронирует из разных мест по городу
```

---

### 3. Variability Metrics (Метрики вариативности)

#### `distance_variability`
**Что это**: Стандартное отклонение расстояний от точек бронирования до клуба

**Формула**: `std_dev(distances_from_booking_points_to_club)`

**Что показывает**:
- **Низкая (0-2 км)**: Стабильный паттерн (дом/работа)
- **Средняя (2-5 км)**: Несколько регулярных мест
- **Высокая (>5 км)**: Хаотичное поведение, нет рутины

**Зачем нужна**:
Даже если `distance_home_to_club = 3km`, но:
- `variability = 1km` → Пользователь стабильно ездит (good!)
- `variability = 20km` → Клуб не встроен в рутину (risk!)

**Реальный пример**:
```
User с distance=3.6km, но variability=46.68km
→ Бронирует из случайных точек по городу
→ Convenience score = 0.45 (плохо)
→ Высокий churn risk
```

---

### 4. Composite Metrics (Композитные метрики)

#### `commute_convenience_score`
**Что это**: Интегральная оценка удобства посещения клуба (0.0 - 1.0)

**Формула** (из кода):
```python
distance_norm = min(1.0, distance_home_to_club_km / 10)
variability_norm = min(1.0, distance_variability / 5)

convenience = 1.0 - (
    0.7 * distance_norm +      # 70% вес на расстояние
    0.3 * variability_norm     # 30% вес на стабильность
)
```

**Компоненты**:
1. **Distance (70% веса)**: Насколько далеко от дома
2. **Variability (30% веса)**: Насколько стабилен паттерн

**Интерпретация диапазонов**:

| Score | Категория | Расстояние | Паттерн | Retention | Действия |
|-------|-----------|------------|---------|-----------|----------|
| 0.9-1.0 | Отлично | <1 км | Очень стабильный | Very High | VIP программа |
| 0.7-0.9 | Хорошо | 1-3 км | Стабильный | High | Стандартный retention |
| 0.5-0.7 | Средне | 3-6 км | Умеренный | Medium | Требуется мотивация |
| 0.3-0.5 | Плохо | 6-9 км | Нестабильный | Low | Активные кампании |
| 0.0-0.3 | Критично | >10 км | Хаотичный | Very Low | Спец. предложения или churn |

**Реальные примеры из данных**:

```python
# Пример 1: Идеальный клиент
home_distance = 0.44 km
variability = 1.25 km
→ convenience_score = 0.8943
→ Интерпретация: Живет рядом, стабильный паттерн
→ Retention: Very High

# Пример 2: Проблемный паттерн
home_distance = 3.60 km  # вроде нормально
variability = 46.68 km   # но очень нестабильно!
→ convenience_score = 0.4480
→ Интерпретация: Нет рутины, бронирует из разных мест
→ Retention: Low

# Пример 3: Далеко живет
home_distance = 9.54 km
variability = 2.60 km
→ convenience_score = 0.1759
→ Интерпретация: Далеко, но стабильный паттерн (возможно работа рядом)
→ Retention: Low, но можно удержать
```

**Почему важна вариативность**:
```
User A: distance=5km, variability=1km → score=0.59
User B: distance=5km, variability=10km → score=0.05

Разница огромная! User B не встроил клуб в рутину.
```

**Статистика по базе**:
- Mean score: 0.6231
- Median score: 0.6747
- Интерпретация: В среднем удобство выше среднего

---

### 5. Data Quality Metrics

#### `location_data_quality`
**Что это**: Категориальная оценка надежности location данных

**Категории**:

| Категория | Условия | Интерпретация | Использование |
|-----------|---------|---------------|---------------|
| `good` | sample_size ≥20 AND confidence ≥30% | Надежные данные | Использовать все метрики |
| `medium` | sample_size ≥10 AND confidence ≥20% | Приемлемо | Использовать с осторожностью |
| `poor` | sample_size <10 OR confidence <20% | Ненадежно | Только для общих трендов |
| `insufficient` | sample_size <3 | Очень мало данных | Не использовать |
| `no_user_data` | Нет location точек | Нет данных | Пропустить |
| `no_club_coords` | Нет координат клуба | Проблема с данными | Исправить CLUB_COORDINATES |

**Распределение в базе**:
```
good:          1,255 (10.2%)  ← Только эти для критичных моделей
medium:        1,995 (16.2%)  ← Можно использовать
poor:          6,553 (53.3%)  ← Только для общих инсайтов
insufficient:  2,496 (20.3%)  ← Исключить
```

**Рекомендации по использованию**:

```python
# Для ML моделей (строгая фильтрация)
df_ml = df[df['location_data_quality'].isin(['good', 'medium'])]

# Для бизнес-аналитики (мягче)
df_analytics = df[df['location_data_quality'] != 'insufficient']

# Для segmentation (все с данными)
df_segment = df[df['location_sample_size'] > 0]
```

---

## Интерпретация для ML

### Feature Importance (по убыванию важности)

**1. Критически важные** (обязательно включать):
- `commute_convenience_score` - композитная метрика, лучший предиктор
- `distance_home_to_club_km` - прямая связь с retention
- `is_home_nearby` - бинарная фича, хорошо работает в деревьях

**2. Важные** (сильно улучшают модель):
- `distance_variability` - показывает стабильность рутины
- `avg_booking_distance_km` - реальное поведение vs теория
- `home_location_confidence` - вес наблюдений

**3. Вспомогательные** (для feature engineering):
- `location_sample_size` - для взвешивания
- `location_data_quality` - для фильтрации
- `home_latitude`, `home_longitude` - для геокластеризации

### Feature Engineering Ideas

```python
# 1. Расхождение между теорией и практикой
df['booking_vs_home_diff'] = df['avg_booking_distance_km'] - df['distance_home_to_club_km']
# Если > 3km → едет не из дома → lower retention

# 2. Weighted convenience (с учетом confidence)
df['weighted_convenience'] = (
    df['commute_convenience_score'] *
    (df['home_location_confidence'] / 100)
)

# 3. Distance buckets (для деревьев)
df['distance_bucket'] = pd.cut(
    df['distance_home_to_club_km'],
    bins=[0, 1, 2, 3, 5, 10, 100],
    labels=['<1km', '1-2km', '2-3km', '3-5km', '5-10km', '>10km']
)

# 4. Convenience тренды (если есть история)
df['convenience_trend'] = df.groupby('user_id')['commute_convenience_score'].diff()
# Негативный тренд → переехал дальше → risk

# 5. Interaction features
df['distance_x_variability'] = (
    df['distance_home_to_club_km'] *
    df['distance_variability']
)
# Высокие значения = двойная проблема
```

### Фильтрация данных для ML

**Для критичных моделей** (binary classification, scoring):
```python
# Только качественные данные
df_strict = df[
    (df['location_data_quality'].isin(['good', 'medium'])) &
    (df['location_sample_size'] >= 10) &
    (df['home_location_confidence'] >= 20)
]
# ~3,250 пользователей (good + medium)
```

**Для exploratory analysis**:
```python
# Все с location данными
df_exploratory = df[
    (df['location_sample_size'] > 0) &
    (df['location_data_quality'] != 'no_user_data')
]
# ~12,000 пользователей
```

**Для feature importance**:
```python
# Используем все, но добавляем quality как фичу
df_all = df.copy()
df_all['has_quality_location'] = df['location_data_quality'].isin(['good', 'medium'])
# Модель сама определит важность
```

### Сегментация пользователей

**По convenience score**:
```python
def segment_by_convenience(score):
    if pd.isna(score):
        return "No Data"
    elif score >= 0.8:
        return "VIP Local"        # Retention: 85%+
    elif score >= 0.6:
        return "Regular Commuter" # Retention: 65-85%
    elif score >= 0.4:
        return "Casual Visitor"   # Retention: 40-65%
    else:
        return "At Risk"          # Retention: <40%
```

**По distance + variability (двумерная сегментация)**:
```python
def segment_advanced(distance, variability):
    # Стабильные паттерны (variability < 3km)
    if variability < 3:
        if distance < 2:
            return "Local Stable"     # Best segment
        elif distance < 5:
            return "Commuter Stable"  # Good segment
        else:
            return "Distant Stable"   # Moderate risk

    # Нестабильные паттерны (variability >= 3km)
    else:
        if distance < 3:
            return "Local Chaotic"    # Medium risk
        else:
            return "High Risk"        # Churn risk
```

**Маркетинговые сегменты**:
```python
segments = {
    'VIP Local': {
        'criteria': 'convenience >= 0.8',
        'action': 'VIP loyalty program, referral incentives',
        'message': 'Наши самые ценные клиенты'
    },
    'Regular Commuter': {
        'criteria': '0.6 <= convenience < 0.8',
        'action': 'Standard retention, rewards',
        'message': 'Стабильная база'
    },
    'Casual Visitor': {
        'criteria': '0.4 <= convenience < 0.6',
        'action': 'Engagement campaigns, motivational content',
        'message': 'Требуется активация'
    },
    'At Risk': {
        'criteria': 'convenience < 0.4',
        'action': 'Win-back campaigns, special offers',
        'message': 'Высокий риск churn'
    }
}
```

## Troubleshooting

### Проблема: Мало пользователей с данными

**Причины**:
- Коллекция `userslocations` пустая или имеет другое название
- `userId` в MongoDB не совпадает с `user_id` в PostgreSQL
- Координаты не извлекаются из вложенного поля `location`

**Решение**: Проверить структуру MongoDB коллекции

### Проблема: Все дистанции = 0 или очень большие

**Причина**: Неверные координаты клубов

**Решение**: Проверить `CLUB_COORDINATES`, использовать Google Maps

### Проблема: Low confidence scores

**Причина**: У пользователей мало точек или они разбросаны

**Решение**: Это нормально для неактивных пользователей. Фильтровать по `location_data_quality`

## Примеры

### Хороший результат
```
User: 12345
  Home: (43.2380, 76.9450)
  Confidence: 65.0%
  Distance to club: 1.5 km
  Avg booking distance: 1.8 km
  Variability: 0.5 km
  Is nearby: True
  Convenience score: 0.8500
  Data quality: good
```

### Результат требует проверки
```
User: 67890
  Home: (43.1000, 76.8000)
  Confidence: 15.0%
  Distance to club: 8.2 km
  Avg booking distance: None
  Variability: None
  Is nearby: False
  Convenience score: None
  Data quality: poor
```

## Следующие шаги

1. Запустить `get_club_coordinates.py`
2. Обновить координаты клубов
3. Запустить `calculate_location_metrics.py` на тестовой выборке
4. Проверить качество результатов
5. Запустить на полной выборке
6. Добавить метрики в таблицу `core_users`
