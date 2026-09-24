"""
Anomaly Detection API endpoints.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from app.ml.anomaly import AnomalyDetector, AnomalyClass

router = APIRouter()
_detector = AnomalyDetector()


class AnomalyDetectIn(BaseModel):
    facility_id: str
    blood_group: str
    component: str
    observed_demand: float
    historical_demand: List[float]


class AnomalyResultOut(BaseModel):
    facility_id: str
    blood_group: str
    component: str
    observed_demand: float
    baseline_mean: float
    baseline_std: float
    z_score: float
    anomaly_class: AnomalyClass
    confidence: float
    description: str
    is_anomaly: bool


@router.post("/detect", response_model=AnomalyResultOut)
def detect_anomaly(payload: AnomalyDetectIn):
    """
    Evaluate whether an observed demand value is anomalous
    given the historical baseline.
    """
    result = _detector.detect(
        facility_id=payload.facility_id,
        blood_group=payload.blood_group,
        component=payload.component,
        observed_demand=payload.observed_demand,
        historical_demand=payload.historical_demand,
    )
    return AnomalyResultOut(
        facility_id=result.facility_id,
        blood_group=result.blood_group,
        component=result.component,
        observed_demand=result.observed_demand,
        baseline_mean=result.baseline_mean,
        baseline_std=result.baseline_std,
        z_score=result.z_score,
        anomaly_class=result.anomaly_class,
        confidence=result.confidence,
        description=result.description,
        is_anomaly=result.anomaly_class not in (AnomalyClass.NORMAL, AnomalyClass.SEASONAL_INCREASE),
    )
