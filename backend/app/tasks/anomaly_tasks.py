"""
Celery task: Anomaly detection using Isolation Forest.
Scans daily demand records for statistical outliers and creates Alerts when found.
"""
import uuid
from datetime import datetime, timedelta

from app.core.celery_app import celery_app


@celery_app.task(bind=True, name="tasks.run_anomaly_detection")
def run_anomaly_detection(self, org_id: str):
    """
    Async Celery task:
    1. Aggregates daily demand per (facility, blood_group, component) for last 60 days
    2. Fits an Isolation Forest on the time-series features
    3. Scores today's demand — if anomalous, creates an Alert in the DB
    4. Deduplicates: won't create a duplicate alert for the same (facility, bg, comp) on same day
    """
    try:
        import numpy as np
        from sklearn.ensemble import IsolationForest
        from sqlalchemy import func
        from app.core.database import SessionLocal
        from app.models.operations import DemandRecord, Alert, AlertSeverity, AlertStatus
        from app.models.facilities import Facility

        db = SessionLocal()
        org_uuid = uuid.UUID(org_id)

        try:
            cutoff = datetime.utcnow() - timedelta(days=60)
            today = datetime.utcnow().date()

            # Get all facilities in org
            facility_ids = [r[0] for r in db.query(Facility.id).filter(Facility.organization_id == org_uuid).all()]

            anomaly_count = 0

            for facility_id in facility_ids:
                # Get daily aggregates per blood_group + component
                combos = (
                    db.query(DemandRecord.blood_group, DemandRecord.component)
                    .filter(
                        DemandRecord.facility_id == facility_id,
                        DemandRecord.recorded_at >= cutoff,
                    )
                    .distinct()
                    .all()
                )

                for bg, comp in combos:
                    rows = (
                        db.query(
                            func.date(DemandRecord.recorded_at).label("day"),
                            func.sum(DemandRecord.requested_quantity).label("total"),
                        )
                        .filter(
                            DemandRecord.facility_id == facility_id,
                            DemandRecord.blood_group == bg,
                            DemandRecord.component == comp,
                            DemandRecord.recorded_at >= cutoff,
                        )
                        .group_by(func.date(DemandRecord.recorded_at))
                        .order_by(func.date(DemandRecord.recorded_at))
                        .all()
                    )

                    if len(rows) < 14:
                        continue  # Not enough data to detect anomalies

                    daily_values = [float(r.total) for r in rows]

                    # Feature matrix: [day_value, rolling_mean_7d, rolling_std_7d]
                    X = []
                    for i in range(7, len(daily_values)):
                        window = daily_values[i - 7:i]
                        X.append([daily_values[i], np.mean(window), np.std(window) or 0.1])

                    if not X:
                        continue

                    clf = IsolationForest(contamination=0.1, random_state=42)
                    clf.fit(X[:-1])  # Train on all but last day
                    score = clf.predict([X[-1]])[0]  # -1 means anomaly

                    if score == -1:
                        # Check if an alert already exists for today
                        existing = db.query(Alert).filter(
                            Alert.facility_id == facility_id,
                            Alert.blood_group == bg,
                            Alert.component == comp,
                            Alert.alert_type == "DEMAND_ANOMALY",
                            Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED]),
                        ).first()

                        if not existing:
                            latest_val = daily_values[-1]
                            mean_7d = np.mean(daily_values[-8:-1])
                            deviation_pct = abs((latest_val - mean_7d) / (mean_7d + 1e-9)) * 100

                            alert = Alert(
                                id=uuid.uuid4(),
                                organization_id=org_uuid,
                                facility_id=facility_id,
                                alert_type="DEMAND_ANOMALY",
                                severity=AlertSeverity.HIGH if deviation_pct > 50 else AlertSeverity.WARNING,
                                title=f"Demand Anomaly: {bg} {comp}",
                                description=(
                                    f"Unusual demand detected for {bg} {comp}. "
                                    f"Latest value: {latest_val:.0f} units, "
                                    f"7-day mean: {mean_7d:.1f} units "
                                    f"({deviation_pct:.1f}% deviation). "
                                    f"Detected via Isolation Forest anomaly detection."
                                ),
                                status=AlertStatus.OPEN,
                                blood_group=bg,
                                component=comp,
                                metadata_json={
                                    "latest_value": latest_val,
                                    "mean_7d": round(mean_7d, 2),
                                    "deviation_pct": round(deviation_pct, 2),
                                    "detected_at": str(today),
                                    "method": "IsolationForest",
                                },
                            )
                            db.add(alert)
                            anomaly_count += 1

            db.commit()
            return {
                "status": "success",
                "org_id": org_id,
                "anomalies_detected": anomaly_count,
                "facilities_scanned": len(facility_ids),
            }
        finally:
            db.close()

    except Exception as exc:
        raise self.retry(exc=exc, countdown=120, max_retries=3)
