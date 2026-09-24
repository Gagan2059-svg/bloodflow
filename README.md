# BloodFlow

**Intelligence for resilient blood supply networks.**

BloodFlow is a production-grade healthcare logistics intelligence platform designed to forecast demand, detect shortages early, reduce wastage, and optimize emergency blood allocations across a network of hospitals and blood banks.

## Capabilities

- **Demand Forecasting**: Predicts future blood demand at a facility level using baseline models (Moving Average, Exponential Smoothing) and provides a pipeline for advanced machine learning models.
- **Shortage & Wastage Prediction**: Continuously models inventory burn-rates against expirations to warn operators of impending shortages and potential blood wastage.
- **Network Optimization**: Uses Google OR-Tools to recommend optimal blood transfer routes between facilities to balance inventory constraints while minimizing transportation time.
- **Digital Twin Simulation**: Run "what-if" scenarios (e.g. facility outages, demand spikes) to see the systemic impact on regional blood supply.
- **Enterprise Operations Dashboard**: A React Flow powered mapping visualization and command center tailored for logistics coordinators.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed diagrams and system design principles.

### Stack
- **Frontend**: Next.js 15, React, Tailwind CSS, shadcn/ui, Recharts, React Flow.
- **Backend**: FastAPI, Pydantic, SQLAlchemy 2.0.
- **Data**: PostgreSQL, Redis.
- **ML/Optimization**: scikit-learn, Google OR-Tools.
- **Workers**: Celery.

## Quick Start

### 1. Requirements
- Docker & Docker Compose
- Node.js (v18+)
- Python (3.12+)

### 2. Infrastructure
Start the database and caching layers:
```bash
make up
```

### 3. Demo Mode
BloodFlow comes with a synthetic data generator that seeds the database with realistic facilities, population-weighted blood group distributions, and network graphs.

```bash
make demo
```

### 4. Running the Application
Start the backend API (http://localhost:8000):
```bash
make api
```

Start the frontend Command Center (http://localhost:3000):
```bash
make web
```

## Security & Privacy
> **Notice**: BloodFlow is a logistics and operational decision-support platform and is not a substitute for clinical judgment. The initial project uses exclusively synthetic and de-identified data.
