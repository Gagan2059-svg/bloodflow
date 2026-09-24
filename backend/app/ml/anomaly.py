"""
Anomaly Detection Engine.

Detects abnormal blood demand patterns using rolling z-score statistics.
Classifies each spike as seasonal, genuine anomaly, emergency, or data quality issue.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import List


class AnomalyClass(str, Enum):
    NORMAL = "NORMAL"
    SEASONAL_INCREASE = "SEASONAL_INCREASE"
    GENUINE_ANOMALY = "GENUINE_ANOMALY"
    EMERGENCY_SPIKE = "EMERGENCY_SPIKE"
    DATA_QUALITY = "DATA_QUALITY"


@dataclass
class AnomalyResult:
    facility_id: str
    blood_group: str
    component: str
    observed_demand: float
    baseline_mean: float
    baseline_std: float
    z_score: float
    anomaly_class: AnomalyClass
    confidence: float          # 0-1
    description: str
    detected_at: datetime


class AnomalyDetector:
    """
    Rolling z-score based anomaly detector for blood demand.

    Z-score thresholds (configurable):
      |z| < 1.5  → NORMAL
      |z| 1.5-2  → SEASONAL_INCREASE (not flagged as anomaly)
      |z| 2-3    → GENUINE_ANOMALY
      |z| > 3    → EMERGENCY_SPIKE
      demand ≤ 0 → DATA_QUALITY issue
    """

    def __init__(
        self,
        seasonal_threshold: float = 1.5,
        anomaly_threshold: float = 2.0,
        emergency_threshold: float = 3.0,
        min_history_len: int = 7,
    ):
        self.seasonal_threshold = seasonal_threshold
        self.anomaly_threshold = anomaly_threshold
        self.emergency_threshold = emergency_threshold
        self.min_history_len = min_history_len

    def detect(
        self,
        facility_id: str,
        blood_group: str,
        component: str,
        observed_demand: float,
        historical_demand: List[float],
    ) -> AnomalyResult:
        """
        Evaluate whether the observed demand value is anomalous
        given the rolling historical baseline.
        """
        now = datetime.now(timezone.utc)

        # Data quality check first
        if observed_demand < 0:
            return AnomalyResult(
                facility_id=facility_id,
                blood_group=blood_group,
                component=component,
                observed_demand=observed_demand,
                baseline_mean=0.0,
                baseline_std=0.0,
                z_score=0.0,
                anomaly_class=AnomalyClass.DATA_QUALITY,
                confidence=0.99,
                description="Demand value is negative — likely a data recording error.",
                detected_at=now,
            )

        if len(historical_demand) < self.min_history_len:
            return AnomalyResult(
                facility_id=facility_id,
                blood_group=blood_group,
                component=component,
                observed_demand=observed_demand,
                baseline_mean=0.0,
                baseline_std=0.0,
                z_score=0.0,
                anomaly_class=AnomalyClass.NORMAL,
                confidence=0.0,
                description="Insufficient historical data for anomaly detection (minimum 7 observations).",
                detected_at=now,
            )

        mean = statistics.mean(historical_demand)
        std = statistics.pstdev(historical_demand)  # population std

        # Avoid division by zero on perfectly stable demand
        if std < 0.01:
            std = 0.01

        z = (observed_demand - mean) / std
        abs_z = abs(z)
        confidence = self._z_to_confidence(abs_z)

        if abs_z < self.seasonal_threshold:
            cls = AnomalyClass.NORMAL
            desc = (
                f"Demand within normal range. "
                f"{observed_demand:.1f} units observed vs. baseline mean of {mean:.1f} (z={z:.2f})."
            )
        elif abs_z < self.anomaly_threshold:
            cls = AnomalyClass.SEASONAL_INCREASE
            desc = (
                f"Demand slightly elevated — consistent with seasonal variation. "
                f"{observed_demand:.1f} units is {abs_z:.1f}σ above the {mean:.1f}-unit baseline."
            )
        elif abs_z < self.emergency_threshold:
            cls = AnomalyClass.GENUINE_ANOMALY
            desc = (
                f"{blood_group} {component} demand at {observed_demand:.1f} units is "
                f"{abs_z:.1f} standard deviations above the historical baseline of {mean:.1f}. "
                f"Recommend investigating root cause."
            )
        else:
            cls = AnomalyClass.EMERGENCY_SPIKE
            desc = (
                f"CRITICAL: {blood_group} {component} demand spike detected. "
                f"{observed_demand:.1f} units is {abs_z:.1f}σ above baseline ({mean:.1f} units). "
                f"Likely driven by a mass-casualty event or data error. Immediate review required."
            )

        return AnomalyResult(
            facility_id=facility_id,
            blood_group=blood_group,
            component=component,
            observed_demand=observed_demand,
            baseline_mean=round(mean, 2),
            baseline_std=round(std, 2),
            z_score=round(z, 3),
            anomaly_class=cls,
            confidence=round(confidence, 3),
            description=desc,
            detected_at=now,
        )

    def batch_detect(
        self,
        facility_id: str,
        demand_series: List[float],
        window: int = 14,
    ) -> List[AnomalyResult]:
        """
        Run anomaly detection across a full demand time series using a rolling window.
        Returns one AnomalyResult per observation (from index `window` onward).
        """
        results: List[AnomalyResult] = []
        for i in range(window, len(demand_series)):
            history = demand_series[max(0, i - window): i]
            obs = demand_series[i]
            result = self.detect(
                facility_id=facility_id,
                blood_group="ALL",
                component="ALL",
                observed_demand=obs,
                historical_demand=history,
            )
            results.append(result)
        return results

    @staticmethod
    def _z_to_confidence(abs_z: float) -> float:
        """Convert |z| to a rough confidence that the observation is anomalous."""
        # Uses the complementary CDF approximation of a normal distribution
        # Higher z → higher confidence it's an anomaly
        t = 1.0 / (1.0 + 0.2316419 * abs_z)
        poly = t * (0.319381530
                    + t * (-0.356563782
                           + t * (1.781477937
                                  + t * (-1.821255978
                                         + t * 1.330274429))))
        p_value = 1.0 - (1.0 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * abs_z ** 2) * poly
        return round(min(max(p_value, 0.0), 1.0), 4)
