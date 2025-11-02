# Location Metrics Calculation Guide

## Overview

Этот документ описывает процесс расчета геолокационных метрик для прогнозирования retention.

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

### PostgreSQL Query

Должна возвращать:
- `user_id` - ID пользователя
- `default_club_corr` - название клуба (должно совпадать с ключом в `CLUB_COORDINATES`)

## Интерпретация для ML

### Feature Importance

**Высокая важность**:
- `distance_home_to_club_km` - прямая связь с retention
- `is_home_nearby` - бинарная фича для деревьев

**Средняя важность**:
- `commute_convenience_score` - композитная метрика
- `avg_booking_distance_km` - реальное поведение

**Вспомогательные**:
- `distance_variability` - для сегментации
- `home_location_confidence` - для фильтрации данных

### Фильтрация данных

Рекомендуется использовать только пользователей с:
```python
location_data_quality in ['good', 'medium']
# или
location_sample_size >= 10 AND home_location_confidence >= 20
```

### Сегментация

```python
if distance_home_to_club_km < 1:
    segment = "Local Hero"           # Высокий retention
elif distance_home_to_club_km < 3:
    segment = "Neighborhood Regular" # Средний retention
elif distance_home_to_club_km < 5:
    segment = "Commuter"            # Requires motivation
else:
    segment = "Long Distance"       # Churn risk
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
