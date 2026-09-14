# 🏎️ F1 PitWall AI — Formula 1 Race Strategy & Telemetry Analytics Platform

An end-to-end **AI-powered Formula 1 race strategy and telemetry analytics platform** built with FastAPI, Streamlit, PostgreSQL, and FastF1. Provides real-time session analysis, tire degradation modelling, pit-stop strategy recommendations, and what-if race simulations.

---

## 📸 Features

| Feature | Description |
|---|---|
| **📊 Dashboard** | Interactive race overview with driver classification, lap times, tire stints, weather, and fastest laps |
| **🏎️ Driver Classification** | Full session results with positions, grid slots, status, and points |
| **⏱️ Lap Time Analysis** | Lap-by-lap timing progression with multi-driver comparison |
| **🛞 Tire Strategy** | Stint timeline, compound usage, and team pace distribution |
| **🔬 Tyre Analysis** | Dedicated degradation curves, compound stats, tire life distribution, and lowess trendlines |
| **🔧 Pit Stops** | Pit stop history, compound transition Sankey diagrams, and pit window distribution |
| **⛅ Track Conditions** | Air/track temperature and wind speed evolution charts |
| **⚔️ Driver Comparison** | Head-to-head fastest lap, average pace, and compound usage comparison |
| **🤖 Strategy AI** | Rule-based pit-stop recommendation engine with compound and urgency analysis |
| **🎮 What-If Simulator** | Side-by-side strategy comparison with estimated race times and pit stop loss |
| **🔐 Authentication** | JWT-based user registration, login, and profile (DB or in-memory fallback) |
| **📈 Advanced Analytics** | Position evolution, sector heatmaps, team pace boxplots, consistency analysis, long-run stint metrics |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend API** | FastAPI (Python 3.12+) |
| **Frontend** | Streamlit |
| **Database** | PostgreSQL 16 (optional — runs without DB) |
| **F1 Data** | FastF1 (official F1 timing data) |
| **ML Models** | Scikit-Learn, XGBoost (lap time, tire degradation, pit window prediction) |
| **Visualisation** | Plotly, Matplotlib |
| **Auth** | PyJWT + bcrypt |
| **Deployment** | Docker Compose |
| **CI/CD** | GitHub Actions (CodeQL, Microsoft Defender for DevOps, Bandit, Pytest) |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- pip
- (Optional) Docker & Docker Compose
- (Optional) PostgreSQL 16

### 1. Clone & Setup

```bash
git clone https://github.com/YourUsername/F1-PitWall-AI---Formula-1-Race-Strategy---Telemetry-Analytics-Platform.git
cd F1-PitWall-AI---Formula-1-Race-Strategy---Telemetry-Analytics-Platform

# Create virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example config and fill in real values
cp .env.example .env
```

**Required:** Generate a secure `SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Edit `.env` and set at minimum:
- `SECRET_KEY` — paste the generated key
- `DATABASE_URL` — (optional) PostgreSQL connection string

### 3. Start the Backend

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

API docs available at: http://127.0.0.1:8000/docs

### 4. Start the Frontend

```bash
streamlit run frontend/app.py
```

Open http://localhost:8501 in your browser.

### 5. Load Race Data

1. Select a **Season** (2018–2025), **Grand Prix**, and **Session** (R, Q, FP1, etc.)
2. Click **🚀 LOAD SESSION**
3. Navigate through Dashboard, Drivers, Lap Times, Tire Analysis, Pit Stops, etc.

---

## 🐳 Docker Deployment

```bash
# Set required environment variables
export POSTGRES_PASSWORD=your_strong_db_password
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Build and run all services
docker compose up --build -d
```

| Service | URL |
|---|---|
| Frontend | http://localhost:8501 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

---

## 📁 Project Structure

```
├── backend/
│   ├── api/              # FastAPI routers (f1, analytics, strategy, simulation, auth, db, ml, export)
│   ├── database/         # SQLAlchemy connection, Base, session factory
│   ├── ml/               # ML model classes (LapTime, TireDegradation, PitWindow)
│   ├── models/           # ORM models (User, F1 models)
│   ├── schemas/          # Pydantic request/response models
│   ├── services/         # Business logic (f1_data, auth, ml, preprocessing, db, export)
│   ├── simulation/       # What-if race simulator engine
│   ├── strategy/         # Rule-based strategy recommendation engine
│   ├── tests/            # Pytest test suite
│   ├── utils/            # Config, logger utilities
│   └── main.py           # FastAPI application entry point
├── frontend/
│   ├── components/       # Sidebar, header, metric cards, status bar
│   ├── pages/            # All Streamlit pages (dashboard, analytics, tire, pitstops, etc.)
│   ├── utils/            # API client, formatting helpers
│   └── app.py            # Streamlit application entry point
├── data/                 # FastF1 cache & processed data
├── trained_models/       # Serialised ML model files
├── alembic/              # Database migration scripts
├── .github/workflows/    # CI/CD (CodeQL, MSDO, Bandit + Pytest)
├── docker-compose.yml    # Multi-container deployment
├── Dockerfile            # Backend container
├── Dockerfile.frontend   # Frontend container
├── requirements.txt      # Python dependencies
└── .env.example          # Environment configuration template
```

---

## 🔌 API Endpoints

### Formula One Data (`/f1`)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/f1/seasons` | List available seasons |
| GET | `/f1/seasons/{year}/schedule` | Event schedule for a season |
| GET | `/f1/session/summary` | Session metadata |
| GET | `/f1/session/drivers` | Driver classification |
| GET | `/f1/session/laps` | Lap timing data |
| GET | `/f1/session/tires` | Tire compound data |
| GET | `/f1/session/pitstops` | Pit stop transitions |
| GET | `/f1/session/weather` | Weather telemetry |
| POST | `/f1/session/preprocess` | Run feature engineering pipeline |

### Analytics (`/analytics`)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/analytics/lap-comparison` | Compare lap times between drivers |
| GET | `/analytics/sector-analysis` | Sector time breakdown |
| GET | `/analytics/position-changes` | Position evolution data |
| GET | `/analytics/pace-distribution` | Pace statistics per driver |
| GET | `/analytics/degradation-summary` | Tire degradation rates per compound |
| GET | `/analytics/team-pace-comparison` | Team/constructor pace comparison |
| GET | `/analytics/long-run-analysis` | Stint degradation analysis |
| GET | `/analytics/consistency-analysis` | Driver lap time consistency |
| GET | `/analytics/tire-degradation-curves` | Degradation curve data |
| GET | `/analytics/pit-stop-timeline` | Pit stop timeline records |

### Strategy (`/strategy`)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/strategy/recommend` | Get pit-stop strategy recommendation |
| GET | `/strategy/compounds` | Compound performance reference data |

### Simulation (`/simulation`)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/simulation/compare` | Compare two race strategies |

### Machine Learning (`/ml`)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/ml/models` | ML models status & metrics |
| POST | `/ml/train` | Train all ML models |
| POST | `/ml/predict/lap-time` | Predict lap time (XGBoost) |
| POST | `/ml/predict/tire-degradation` | Predict tire degradation |
| POST | `/ml/predict/pit-window` | Predict optimal pit window |

### Auth (`/auth`)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login and get JWT token |
| GET | `/auth/me` | Get current user profile |

### System & Health (`/`)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API welcome and version info |
| GET | `/health` | Health-check endpoint |
| GET | `/status` | Component status (backend, FastF1, database) |

### Database & Storage (`/db`)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/db/status` | Database connectivity and table counts |
| POST | `/db/sync/session` | Persist FastF1 session data to database |

### Export (`/export`)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/export/csv` | Export session laps or telemetry as CSV |
| GET | `/export/json` | Export session laps or telemetry as JSON |

---

## 🧪 Testing

```bash
# Run unit tests
pytest backend/tests/ -v

# Security scan
bandit -r backend/ -ll -x backend/tests/
```

---

## 🔒 Security

- **JWT Authentication** with bcrypt password hashing
- **SECRET_KEY** loaded from environment (never hardcoded)
- **CORS** origins configurable via `CORS_ORIGINS` env var
- **Database credentials** injected via environment variables (no defaults in Docker)
- **CI/CD Security**: CodeQL analysis, Microsoft Defender for DevOps, Bandit SAST scanning
- **Parameterized queries** via SQLAlchemy ORM (no raw SQL injection risk)

---

## 📊 Machine Learning Models

| Model | Algorithm | Target | Features |
|---|---|---|---|
| Lap Time Predictor | XGBoost | Predicted lap time (s) | Tire life, compound, lap number, fuel correction, stint |
| Tire Degradation | GradientBoosting | Pace loss per lap (s) | Compound, tire life, stint, lap number |
| Pit Window | RandomForest | Optimal laps until pit | Compound, tire life, current lap, remaining laps, recent pace, pace dropoff |

Train all models via the API:
```bash
curl -X POST http://127.0.0.1:8000/ml/train
```

---

## 📜 License

This project is for educational and research purposes. F1 timing data is provided by the FastF1 library under its own license terms.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

*Built with ❤️ for Formula 1 data analytics*
