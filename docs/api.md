# F1 PitWall AI — REST API Documentation

Complete OpenAPI REST specification for the **F1 PitWall AI** FastAPI backend service.

Base URL (Local Development): `http://127.0.0.1:8000`  
Swagger UI Interactive Docs: `http://127.0.0.1:8000/docs`  
ReDoc Documentation: `http://127.0.0.1:8000/redoc`

---

## Endpoint Summary Matrix

| Group | Method | Endpoint | Description |
|-------|--------|----------|-------------|
| **System** | `GET` | `/` | Root welcome message & API status |
| | `GET` | `/health` | Health-check endpoint for Streamlit frontend |
| | `GET` | `/status` | Operational status of backend, FastF1 cache, and database |
| **F1 Data** | `GET` | `/f1/seasons` | Available Formula 1 season years |
| | `GET` | `/f1/seasons/{year}/schedule` | Grand Prix event schedule for specified season |
| | `GET` | `/f1/session/summary` | High-level session metadata and weather overview |
| | `GET` | `/f1/session/drivers` | Driver classification standings and points |
| | `GET` | `/f1/session/laps` | Lap-by-lap timing and compound telemetry |
| | `GET` | `/f1/session/tires` | Tire compound stint records and tire life |
| | `GET` | `/f1/session/pitstops` | Pit stop history and compound transitions |
| | `GET` | `/f1/session/weather` | Weather telemetry observations |
| | `POST` | `/f1/session/preprocess` | Run data cleaning & feature engineering pipeline |
| | `GET` | `/f1/session/processed` | Retrieve preprocessed Parquet dataset path |
| **Analytics** | `GET` | `/analytics/lap-comparison` | Multi-driver lap progression timing |
| | `GET` | `/analytics/sector-analysis` | Sector time breakdown per driver |
| | `GET` | `/analytics/position-changes` | Lap-by-lap position trajectory |
| | `GET` | `/analytics/pace-distribution` | Driver lap time summary statistics & quartiles |
| | `GET` | `/analytics/degradation-summary` | Empirical compound tire degradation rates |
| | `GET` | `/analytics/team-pace-comparison` | Constructor pace spread and IQR analysis |
| | `GET` | `/analytics/long-run-analysis` | Stint pace stability for long runs (>= 5 laps) |
| | `GET` | `/analytics/consistency-analysis` | Driver pace variance and consistency rating |
| | `GET` | `/analytics/sector-delta-heatmap` | Sector time deltas heatmapping data |
| | `GET` | `/analytics/tire-degradation-curves` | Lap-by-lap tire age vs lap time curves |
| | `GET` | `/analytics/pit-stop-timeline` | Pit stop timeline records |
| **ML Models** | `GET` | `/ml/models` | Status of serialized trained ML models |
| | `POST` | `/ml/train` | Trigger model training pipeline |
| | `POST` | `/ml/predict/lap-time` | Predict expected lap time (XGBoost) |
| | `POST` | `/ml/predict/tire-degradation` | Predict tire pace degradation (GradientBoosting) |
| | `POST` | `/ml/predict/pit-window` | Predict recommended pit window (RandomForest) |
| **Strategy** | `POST` | `/strategy/recommend` | Generate AI pit stop & compound strategy recommendation |
| **Simulation** | `POST` | `/simulation/run` | Simulate single race strategy timeline |
| | `POST` | `/simulation/compare` | Compare dual strategy scenarios (Plan A vs Plan B) |
| **Auth** | `POST` | `/auth/register` | Register new user account |
| | `POST` | `/auth/login` | Authenticate user & generate JWT access token |
| | `GET` | `/auth/me` | Fetch authenticated user profile |
| **Export** | `POST` | `/export/raw` | Save raw telemetry datasets into CSV files |
| | `POST` | `/export/processed` | Save preprocessed dataset into Parquet format |
| | `GET` | `/export/report` | Download styled HTML/PDF race strategy report |

---

## Detailed Endpoint Requests & Responses

### 1. System Status (`GET /status`)
**Response (200 OK)**:
```json
{
  "backend": "connected",
  "fastf1": "ready",
  "database": "connected",
  "version": "1.0.0"
}
```

### 2. Strategy Recommendation (`POST /strategy/recommend`)
**Request Body**:
```json
{
  "driver": "VER",
  "circuit": "Bahrain International Circuit",
  "current_lap": 20,
  "total_laps": 57,
  "current_compound": "MEDIUM",
  "tire_age": 15,
  "track_temp": 38.5,
  "rainfall": false
}
```
**Response (200 OK)**:
```json
{
  "recommended_pit_window": "Lap 20 - Lap 24",
  "suggested_compound": "HARD",
  "urgency": "MEDIUM",
  "explanation": "Medium tires are experiencing degradation (~0.045s/lap). Switching to HARD compound allows running to lap 57 without additional stops."
}
```

### 3. Strategy Comparison (`POST /simulation/compare`)
**Request Body**:
```json
{
  "circuit": "Sakhir",
  "total_laps": 57,
  "track_temp": 38.0,
  "plan_a": {
    "name": "2-Stop Soft-Medium-Hard",
    "stints": [
      {"compound": "SOFT", "laps": 15},
      {"compound": "MEDIUM", "laps": 22},
      {"compound": "HARD", "laps": 20}
    ]
  },
  "plan_b": {
    "name": "1-Stop Medium-Hard",
    "stints": [
      {"compound": "MEDIUM", "laps": 25},
      {"compound": "HARD", "laps": 32}
    ]
  }
}
```
**Response (200 OK)**:
```json
{
  "circuit": "Sakhir",
  "total_laps": 57,
  "plan_a": {
    "name": "2-Stop Soft-Medium-Hard",
    "total_time_seconds": 5420.5,
    "pit_stops": 2,
    "formatted_time": "1:30:20.500"
  },
  "plan_b": {
    "name": "1-Stop Medium-Hard",
    "total_time_seconds": 5408.2,
    "pit_stops": 1,
    "formatted_time": "1:30:08.200"
  },
  "faster_plan": "Plan B",
  "delta_seconds": 12.3
}
```
