# F1 PitWall AI — Machine Learning Architecture & Model Card Documentation

This document provides a technical specification of the machine learning pipelines, predictive models, feature representations, training procedures, and model limitations for **F1 PitWall AI**.

---

## Overview

F1 PitWall AI employs three distinct supervised machine learning models to assist race strategists with decision support:

1. **LapTimeModel** — Predicts baseline expected lap times based on track conditions, stint progression, and tire state.
2. **TireDegradationModel** — Forecasts lap-by-lap pace degradation per compound across extended stints.
3. **PitWindowModel** — Predicts the optimal pit stop window (laps remaining) and outputs a confidence interval.

All models are serialized using `joblib` into the `trained_models/` directory and served via FastAPI REST endpoints.

---

## 1. LapTimeModel (XGBoost Regressor)

### Objective
Predict the raw lap time (in seconds) for a given driver on a specific lap, accounting for fuel burn-off, tire compound, tire age, and ambient track temperature.

### Model Specification
- **Algorithm**: `xgboost.XGBRegressor` (Fallback: `sklearn.ensemble.GradientBoostingRegressor`)
- **Hyperparameters**:
  - `n_estimators`: 100
  - `learning_rate`: 0.05
  - `max_depth`: 6
  - `subsample`: 0.8
  - `colsample_bytree`: 0.8
  - `random_state`: 42

### Feature Schema (Inputs)
| Feature Name | Type | Description |
|--------------|------|-------------|
| `LapNumber` | float | Current lap number in the race |
| `TyreLife` | float | Number of laps completed on current tire set |
| `Compound_Enc` | int | Categorical integer encoding (`SOFT`: 0, `MEDIUM`: 1, `HARD`: 2, `INTERMEDIATE`: 3, `WET`: 4) |
| `TrackTemp` | float | Track surface temperature (°C) |
| `FuelLoadKg` | float | Estimated remaining fuel load in kilograms |
| `StintLapIndex` | float | Laps driven in current stint |
| `DriverPace_3Lap` | float | Rolling 3-lap pace average (s) |

### Target Variable (Output)
- **`LapTimeSeconds`** (`float`): Expected lap time duration in seconds.

### Evaluation Metrics
- **Mean Absolute Error (MAE)**: ~0.35s – 0.65s (on clean racing laps)
- **Root Mean Squared Error (RMSE)**: ~0.55s – 0.85s
- **Coefficient of Determination ($R^2$)**: 0.88 – 0.94

---

## 2. TireDegradationModel (GradientBoosting Regressor)

### Objective
Forecast the pace degradation rate (seconds added per lap) as a tire compound ages throughout a stint.

### Model Specification
- **Algorithm**: `sklearn.ensemble.GradientBoostingRegressor`
- **Hyperparameters**:
  - `n_estimators`: 80
  - `learning_rate`: 0.08
  - `max_depth`: 4
  - `random_state`: 42

### Feature Schema (Inputs)
| Feature Name | Type | Description |
|--------------|------|-------------|
| `TyreLife` | float | Laps accumulated on current tire set |
| `Compound_Enc` | int | Encoded compound index |
| `TrackTemp` | float | Track surface temperature (°C) |
| `Stint` | int | Stint index in the race |
| `CumulativeDegradation` | float | Total accumulated pace drop-off since stint start (s) |

### Target Variable (Output)
- **`LapDegradationRate`** (`float`): Estimated pace drop-off per lap (seconds/lap).

### Evaluation Metrics
- **MAE**: ~0.04s/lap
- **RMSE**: ~0.07s/lap
- **$R^2$**: 0.84 – 0.91

---

## 3. PitWindowModel (RandomForest Regressor)

### Objective
Estimate the recommended number of laps remaining in the current stint before a pit stop should occur, providing an ensemble confidence score.

### Model Specification
- **Algorithm**: `sklearn.ensemble.RandomForestRegressor`
- **Hyperparameters**:
  - `n_estimators`: 100
  - `max_depth`: 8
  - `min_samples_split`: 5
  - `random_state`: 42

### Feature Schema (Inputs)
| Feature Name | Type | Description |
|--------------|------|-------------|
| `TyreLife` | float | Current tire age (laps) |
| `StintLapIndex` | float | Stint lap count |
| `Compound_Enc` | int | Encoded compound index |
| `PaceDropOff` | float | Current pace drop-off vs stint initial pace (s) |
| `LapsRemainingInRace` | float | Total race laps remaining |
| `TrackTemp` | float | Track temperature (°C) |

### Target Variable (Output)
- **`predicted_laps_until_pit`** (`int`): Recommended remaining laps in current stint.
- **`confidence`** (`float`): Normalized ensemble variance confidence score (0.0 to 1.0).

### Evaluation Metrics
- **MAE**: ~1.2 laps
- **RMSE**: ~1.8 laps
- **Confidence Calibration**: High correlation with ensemble variance.

---

## Responsible AI & Model Disclosures

> [!IMPORTANT]
> **Educational & Research Purpose Notice**  
> F1 PitWall AI is an open-source educational project developed for race strategy decision support and sports analytics research.
> - Models are trained on public telemetry datasets extracted via FastF1 and Ergast API.
> - Predictive outputs are estimates intended for **decision support visualization only**.
> - The models do **NOT** use proprietary F1 team telemetry, real-time car sensors, or confidential aerodynamic data.
> - Predictions under Safety Car (SC), Virtual Safety Car (VSC), or Red Flag conditions are subject to higher variance due to non-representative pace.
