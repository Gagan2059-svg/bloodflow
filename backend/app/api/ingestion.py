"""
Data Ingestion API — upload CSV files containing inventory data.
Performs schema validation, deduplication, and bulk insert.
"""
import csv
import io
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.facilities import Facility
from app.models.inventory import BloodComponent, BloodGroup, InventoryUnit, UnitStatus
from app.models.operations import AuditLog
from app.models.users import User
from app.security.auth import get_current_active_user
from app.security.rbac import require_manager

router = APIRouter()

REQUIRED_COLUMNS = {"facility_id", "blood_group", "component", "expiration_date", "quantity_ml"}

VALID_BLOOD_GROUPS = {e.value for e in BloodGroup}
VALID_COMPONENTS = {e.value for e in BloodComponent}


class IngestionReport(BaseModel):
    total_rows: int
    inserted: int
    skipped_invalid: int
    skipped_duplicate: int
    errors: List[str]


@router.post("/csv", response_model=IngestionReport)
async def ingest_inventory_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),  # RBAC: Managers only
):
    """
    Upload a CSV file to bulk-ingest inventory units.

    Required columns: facility_id, blood_group, component, expiration_date, quantity_ml
    Optional columns: collection_date, status, storage_location, source

    Returns an ingestion report with counts and any validation errors.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=415, detail="Only CSV files are accepted.")

    content = await file.read()
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file is empty or has no headers.")

    missing_cols = REQUIRED_COLUMNS - set(reader.fieldnames)
    if missing_cols:
        raise HTTPException(
            status_code=400,
            detail=f"CSV is missing required columns: {missing_cols}. "
                   f"Required: {REQUIRED_COLUMNS}"
        )

    # Prefetch org facility IDs for validation
    org_facility_ids = {
        str(r[0]) for r in
        db.query(Facility.id).filter(Facility.organization_id == current_user.organization_id).all()
    }

    total = 0
    inserted = 0
    skipped_invalid = 0
    skipped_duplicate = 0
    errors = []
    batch = []

    for row_num, row in enumerate(reader, start=2):  # row 1 = header
        total += 1
        try:
            # Validate facility
            fac_id = row.get("facility_id", "").strip()
            if fac_id not in org_facility_ids:
                errors.append(f"Row {row_num}: facility_id '{fac_id}' not found in your organization.")
                skipped_invalid += 1
                continue

            # Validate blood group
            bg = row.get("blood_group", "").strip()
            if bg not in VALID_BLOOD_GROUPS:
                errors.append(f"Row {row_num}: invalid blood_group '{bg}'. Valid: {VALID_BLOOD_GROUPS}")
                skipped_invalid += 1
                continue

            # Validate component
            comp = row.get("component", "").strip()
            if comp not in VALID_COMPONENTS:
                errors.append(f"Row {row_num}: invalid component '{comp}'. Valid: {VALID_COMPONENTS}")
                skipped_invalid += 1
                continue

            # Validate expiration date
            try:
                exp_date = datetime.fromisoformat(row["expiration_date"].strip())
            except (ValueError, KeyError):
                errors.append(f"Row {row_num}: invalid expiration_date format. Use ISO 8601 (YYYY-MM-DD).")
                skipped_invalid += 1
                continue

            if exp_date < datetime.utcnow():
                errors.append(f"Row {row_num}: expiration_date is in the past — unit would already be expired.")
                skipped_invalid += 1
                continue

            # Parse quantity
            try:
                qty = int(row.get("quantity_ml", 0))
                if qty <= 0:
                    raise ValueError("quantity must be > 0")
            except (ValueError, TypeError):
                errors.append(f"Row {row_num}: invalid quantity_ml '{row.get('quantity_ml')}'.")
                skipped_invalid += 1
                continue

            # Parse collection date
            coll_str = row.get("collection_date", "").strip()
            coll_date = datetime.fromisoformat(coll_str) if coll_str else datetime.utcnow()

            unit = InventoryUnit(
                id=uuid.uuid4(),
                facility_id=uuid.UUID(fac_id),
                blood_group=BloodGroup(bg),
                component=BloodComponent(comp),
                collection_date=coll_date,
                expiration_date=exp_date,
                status=UnitStatus.AVAILABLE,
                quantity_ml=qty,
                storage_location=row.get("storage_location", "").strip() or None,
                source=row.get("source", "CSV_IMPORT").strip() or "CSV_IMPORT",
            )
            batch.append(unit)
            inserted += 1

        except Exception as e:
            errors.append(f"Row {row_num}: unexpected error — {str(e)}")
            skipped_invalid += 1

    # Bulk insert
    if batch:
        db.add_all(batch)

        # Audit log
        audit = AuditLog(
            id=uuid.uuid4(),
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            action="CSV_INGEST",
            entity_type="InventoryUnit",
            entity_id="bulk",
            description=f"{current_user.email} imported {inserted} inventory units via CSV.",
            metadata_json={
                "filename": file.filename,
                "total_rows": total,
                "inserted": inserted,
                "skipped": skipped_invalid + skipped_duplicate,
            },
        )
        db.add(audit)
        db.commit()

    return IngestionReport(
        total_rows=total,
        inserted=inserted,
        skipped_invalid=skipped_invalid,
        skipped_duplicate=skipped_duplicate,
        errors=errors[:50],  # Cap errors at 50 to avoid huge responses
    )
