from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "bloodflow_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
)

@celery_app.task(name="tasks.generate_forecasts")
def generate_forecasts_task(facility_id: str):
    """
    Background task to generate forecasts for a facility.
    """
    from app.ml.forecasting import DemandForecaster
    import random

    # Mock pulling historical data
    historical = [random.randint(5, 20) for _ in range(30)]

    # Generate Forecasts
    naive = DemandForecaster.naive_forecast(historical, horizon=7)
    ma = DemandForecaster.moving_average(historical, window=7, horizon=7)
    ewma = DemandForecaster.exponential_smoothing(historical, alpha=0.3, horizon=7)

    return {
        "facility_id": facility_id,
        "status": "completed",
        "forecasts": {
            "naive": naive,
            "moving_average": ma,
            "exponential_smoothing": ewma
        }
    }
