"""
FRA Measurement API endpoints.
Handles measurement CRUD and file upload with auto-detection parsing.
"""
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.measurement import FRAMeasurement
from app.models.transformer import Transformer
from app.models.import_history import ImportHistory, ImportStatus
from app.parsers import registry
from app.services.validation import validate_fra_data
from app.services.normalization import normalize_fra_data
from app.schemas.measurement import (
    MeasurementCreate,
    MeasurementResponse,
    MeasurementSummary,
    UploadResponse,
)

router = APIRouter(prefix="/api/v1/measurements", tags=["Measurements"])


@router.get("/", response_model=list[MeasurementSummary])
def list_measurements(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    transformer_id: str | None = None,
    vendor: str | None = None,
    db: Session = Depends(get_db),
):
    """List measurements with optional filtering."""
    query = db.query(FRAMeasurement)

    if transformer_id:
        query = query.filter(FRAMeasurement.transformer_id == transformer_id)
    if vendor:
        query = query.filter(FRAMeasurement.vendor == vendor)

    measurements = (
        query.order_by(FRAMeasurement.measurement_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    results = []
    for m in measurements:
        summary = MeasurementSummary.model_validate(m)
        summary.data_points = len(m.frequency_hz) if m.frequency_hz else 0
        results.append(summary)
    return results


@router.get("/{measurement_id}", response_model=MeasurementResponse)
def get_measurement(measurement_id: str, db: Session = Depends(get_db)):
    """Retrieve a specific measurement with full data."""
    measurement = (
        db.query(FRAMeasurement).filter(FRAMeasurement.id == measurement_id).first()
    )
    if not measurement:
        raise HTTPException(status_code=404, detail="Measurement not found")
    return MeasurementResponse.model_validate(measurement)


@router.post("/", response_model=MeasurementResponse, status_code=201)
def create_measurement(data: MeasurementCreate, db: Session = Depends(get_db)):
    """Create a measurement record directly (non-file-upload path)."""
    # Verify transformer exists
    transformer = (
        db.query(Transformer).filter(Transformer.id == data.transformer_id).first()
    )
    if not transformer:
        raise HTTPException(status_code=404, detail="Transformer not found")

    # Validate array lengths match
    if len(data.frequency_hz) != len(data.magnitude_db):
        raise HTTPException(
            status_code=422,
            detail="frequency_hz and magnitude_db arrays must have the same length",
        )
    if data.phase_degrees and len(data.phase_degrees) != len(data.frequency_hz):
        raise HTTPException(
            status_code=422,
            detail="phase_degrees array must have the same length as frequency_hz",
        )

    measurement = FRAMeasurement(**data.model_dump())
    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    return MeasurementResponse.model_validate(measurement)


@router.delete("/{measurement_id}", status_code=204)
def delete_measurement(measurement_id: str, db: Session = Depends(get_db)):
    """Delete a specific measurement."""
    measurement = (
        db.query(FRAMeasurement).filter(FRAMeasurement.id == measurement_id).first()
    )
    if not measurement:
        raise HTTPException(status_code=404, detail="Measurement not found")

    db.delete(measurement)
    db.commit()


# Convenience endpoint: get measurements for a specific transformer
@router.get(
    "/transformer/{transformer_id}",
    response_model=list[MeasurementSummary],
)
def get_transformer_measurements(
    transformer_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List all measurements for a specific transformer."""
    transformer = (
        db.query(Transformer).filter(Transformer.id == transformer_id).first()
    )
    if not transformer:
        raise HTTPException(status_code=404, detail="Transformer not found")

    measurements = (
        db.query(FRAMeasurement)
        .filter(FRAMeasurement.transformer_id == transformer_id)
        .order_by(FRAMeasurement.measurement_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    results = []
    for m in measurements:
        summary = MeasurementSummary.model_validate(m)
        summary.data_points = len(m.frequency_hz) if m.frequency_hz else 0
        results.append(summary)
    return results


# ── File Upload Endpoint ──

@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_fra_file(
    file: UploadFile = File(..., description="FRA data file (CSV, XML, vendor-specific)"),
    transformer_id: str = Form(..., description="Target transformer ID"),
    winding_config: str = Form("HV-LV", description="Winding configuration override"),
    measurement_date: str | None = Form(None, description="Measurement date (ISO 8601)"),
    temperature_celsius: float | None = Form(None, description="Temperature at measurement"),
    notes: str | None = Form(None, description="Optional notes"),
    db: Session = Depends(get_db),
):
    """
    Upload and parse an FRA measurement file.

    Steps:
      1. Validate transformer exists
      2. Check file size
      3. Auto-detect vendor/format via parser registry
      4. Parse the file
      5. Validate the parsed data
      6. Normalize the data
      7. Store the measurement
      8. Log import history
    """
    # 1. Verify transformer
    transformer = (
        db.query(Transformer).filter(Transformer.id == transformer_id).first()
    )
    if not transformer:
        raise HTTPException(status_code=404, detail="Transformer not found")

    # 2. Read file content
    content = await file.read()
    file_size = len(content)

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({file_size / 1024 / 1024:.1f} MB). "
                   f"Maximum is {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    filename = file.filename or "unknown"

    # Create import history record
    import_record = ImportHistory(
        original_filename=filename,
        file_size_bytes=file_size,
        transformer_id=transformer_id,
        status=ImportStatus.PARSING,
    )
    db.add(import_record)
    db.flush()

    try:
        # 3. Auto-detect parser
        header_bytes = content[:4096]
        parser = registry.detect_parser(filename, header_bytes)

        if parser is None:
            import_record.status = ImportStatus.FAILED
            import_record.error_message = "No parser could handle this file format"
            import_record.completed_at = datetime.now(timezone.utc)
            db.commit()
            raise HTTPException(
                status_code=422,
                detail="Unsupported file format. Could not auto-detect a parser. "
                       "Supported: CSV, XML, Omicron, Megger FRAX, Doble.",
            )

        import_record.parser_used = parser.name
        import_record.detected_vendor = parser.name

        # 4. Parse
        fileobj = io.BytesIO(content)
        parse_result = parser.parse(filename, fileobj)

        import_record.detected_format = parse_result.detected_format

        if not parse_result.is_ok or parse_result.data is None:
            import_record.status = ImportStatus.FAILED
            import_record.errors_json = parse_result.errors
            import_record.error_message = "; ".join(parse_result.errors)
            import_record.completed_at = datetime.now(timezone.utc)
            db.commit()
            raise HTTPException(
                status_code=422,
                detail=f"Parsing failed: {'; '.join(parse_result.errors)}",
            )

        all_warnings = list(parse_result.warnings)

        # 5. Validate
        import_record.status = ImportStatus.VALIDATING
        db.flush()

        validation = validate_fra_data(
            parse_result.data.frequency_hz,
            parse_result.data.magnitude_db,
            parse_result.data.phase_degrees,
        )

        if not validation.is_valid:
            import_record.status = ImportStatus.FAILED
            import_record.errors_json = validation.errors
            import_record.warnings_json = validation.warnings
            import_record.error_message = "; ".join(validation.errors)
            import_record.completed_at = datetime.now(timezone.utc)
            db.commit()
            raise HTTPException(
                status_code=422,
                detail=f"Validation failed: {'; '.join(validation.errors)}",
            )

        all_warnings.extend(validation.warnings)

        # 6. Normalize
        import_record.status = ImportStatus.NORMALIZING
        db.flush()

        normalized = normalize_fra_data(parse_result.data)
        all_warnings.extend(normalized.normalization_notes)

        # Apply form overrides
        final_winding = winding_config or normalized.winding_config
        final_date = (
            datetime.fromisoformat(measurement_date)
            if measurement_date
            else (
                datetime.fromisoformat(normalized.measurement_date)
                if normalized.measurement_date
                else datetime.now(timezone.utc)
            )
        )
        final_temp = temperature_celsius or normalized.temperature_celsius

        # 7. Store measurement
        measurement = FRAMeasurement(
            transformer_id=transformer_id,
            measurement_date=final_date,
            winding_config=final_winding,
            frequency_hz=normalized.frequency_hz,
            magnitude_db=normalized.magnitude_db,
            phase_degrees=normalized.phase_degrees,
            vendor=normalized.vendor,
            original_format=parse_result.detected_format,
            original_filename=filename,
            metadata_json=normalized.extra_metadata or None,
            temperature_celsius=final_temp,
            notes=notes or normalized.notes,
        )
        db.add(measurement)
        db.flush()

        # 8. Update import history
        f_min = normalized.frequency_hz[0]
        f_max = normalized.frequency_hz[-1]
        import_record.status = ImportStatus.SUCCESS
        import_record.measurement_id = measurement.id
        import_record.data_points = len(normalized.frequency_hz)
        import_record.frequency_range = f"{f_min:.1f} Hz - {f_max:.1f} Hz"
        import_record.warnings_json = all_warnings if all_warnings else None
        import_record.completed_at = datetime.now(timezone.utc)

        db.commit()

        return UploadResponse(
            measurement_id=measurement.id,
            transformer_id=transformer_id,
            filename=filename,
            vendor_detected=normalized.vendor,
            data_points=len(normalized.frequency_hz),
            frequency_range=f"{f_min:.1f} Hz - {f_max:.1f} Hz",
            validation_warnings=all_warnings,
            message="File uploaded and parsed successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        import_record.status = ImportStatus.FAILED
        import_record.error_message = str(e)
        import_record.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Upload processing error: {e}")
