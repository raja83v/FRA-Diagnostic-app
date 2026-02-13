"""
FRA Data Validation Service.

Validates parsed FRA data against physical constraints:
  - Frequency range (20 Hz – 2 MHz per IEC 60076-18)
  - Array consistency (equal lengths, sorted, no duplicates)
  - Magnitude bounds (reasonable dB range)
  - Outlier detection with z-score
  - Minimum data point count
"""
from dataclasses import dataclass, field

import numpy as np

from app.config import settings


@dataclass
class ValidationResult:
    """Result of validating FRA data."""
    is_valid: bool = True
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.is_valid = False


# ── Configuration ──
MIN_DATA_POINTS = 10
MIN_FREQUENCY_HZ = settings.MIN_FREQUENCY_HZ  # 20 Hz
MAX_FREQUENCY_HZ = settings.MAX_FREQUENCY_HZ  # 2 MHz
MAG_LOWER_BOUND_DB = -120.0
MAG_UPPER_BOUND_DB = 40.0
OUTLIER_Z_THRESHOLD = 4.0


def validate_fra_data(
    frequency_hz: list[float],
    magnitude_db: list[float],
    phase_degrees: list[float] | None = None,
) -> ValidationResult:
    """
    Validate FRA data arrays.

    Parameters
    ----------
    frequency_hz : list[float]
        Frequency values in Hz.
    magnitude_db : list[float]
        Magnitude values in dB.
    phase_degrees : list[float] | None
        Optional phase values in degrees.

    Returns
    -------
    ValidationResult
        Contains is_valid flag, warnings, errors, and stats.
    """
    result = ValidationResult()
    freq = np.array(frequency_hz, dtype=float)
    mag = np.array(magnitude_db, dtype=float)
    phase = np.array(phase_degrees, dtype=float) if phase_degrees else None

    # ── Array length checks ──
    if len(freq) == 0 or len(mag) == 0:
        result.add_error("Frequency or magnitude array is empty")
        return result

    if len(freq) != len(mag):
        result.add_error(
            f"Array length mismatch: frequency has {len(freq)} values, "
            f"magnitude has {len(mag)} values"
        )
        return result

    if phase is not None and len(phase) != len(freq):
        result.add_warning(
            f"Phase array length ({len(phase)}) differs from frequency ({len(freq)}); "
            "phase data will be discarded"
        )

    if len(freq) < MIN_DATA_POINTS:
        result.add_error(
            f"Too few data points ({len(freq)}); minimum is {MIN_DATA_POINTS}"
        )
        return result

    # ── NaN / Inf checks ──
    nan_freq = int(np.isnan(freq).sum())
    nan_mag = int(np.isnan(mag).sum())
    inf_freq = int(np.isinf(freq).sum())
    inf_mag = int(np.isinf(mag).sum())

    if nan_freq > 0 or inf_freq > 0:
        result.add_warning(
            f"Frequency array has {nan_freq} NaN and {inf_freq} Inf values"
        )
    if nan_mag > 0 or inf_mag > 0:
        result.add_warning(
            f"Magnitude array has {nan_mag} NaN and {inf_mag} Inf values"
        )

    # Filter out NaN/Inf for remaining checks
    valid_mask = np.isfinite(freq) & np.isfinite(mag)
    freq_clean = freq[valid_mask]
    mag_clean = mag[valid_mask]

    if len(freq_clean) < MIN_DATA_POINTS:
        result.add_error(
            f"Only {len(freq_clean)} valid (finite) data points after filtering"
        )
        return result

    # ── Frequency range ──
    f_min = float(freq_clean.min())
    f_max = float(freq_clean.max())

    if f_min < MIN_FREQUENCY_HZ:
        result.add_warning(
            f"Minimum frequency ({f_min:.1f} Hz) is below expected "
            f"lower bound ({MIN_FREQUENCY_HZ} Hz)"
        )
    if f_max > MAX_FREQUENCY_HZ:
        result.add_warning(
            f"Maximum frequency ({f_max:.1f} Hz) exceeds expected "
            f"upper bound ({MAX_FREQUENCY_HZ} Hz)"
        )

    # ── Frequency ordering ──
    if not np.all(np.diff(freq_clean) > 0):
        result.add_warning("Frequency values are not strictly ascending")

    # ── Duplicate frequencies ──
    unique_count = len(np.unique(freq_clean))
    dup_count = len(freq_clean) - unique_count
    if dup_count > 0:
        result.add_warning(f"{dup_count} duplicate frequency value(s) detected")

    # ── Magnitude bounds ──
    m_min = float(mag_clean.min())
    m_max = float(mag_clean.max())

    if m_min < MAG_LOWER_BOUND_DB:
        result.add_warning(
            f"Magnitude minimum ({m_min:.1f} dB) is below expected "
            f"lower bound ({MAG_LOWER_BOUND_DB} dB)"
        )
    if m_max > MAG_UPPER_BOUND_DB:
        result.add_warning(
            f"Magnitude maximum ({m_max:.1f} dB) exceeds expected "
            f"upper bound ({MAG_UPPER_BOUND_DB} dB)"
        )

    # ── Outlier detection (z-score on magnitude) ──
    if len(mag_clean) > 3:
        mean_mag = float(np.mean(mag_clean))
        std_mag = float(np.std(mag_clean))
        if std_mag > 0:
            z_scores = np.abs((mag_clean - mean_mag) / std_mag)
            outlier_count = int((z_scores > OUTLIER_Z_THRESHOLD).sum())
            if outlier_count > 0:
                result.add_warning(
                    f"{outlier_count} potential outlier(s) in magnitude "
                    f"(z-score > {OUTLIER_Z_THRESHOLD})"
                )

    # ── Summary statistics ──
    result.stats = {
        "total_points": len(freq),
        "valid_points": int(len(freq_clean)),
        "frequency_min_hz": f_min,
        "frequency_max_hz": f_max,
        "magnitude_min_db": m_min,
        "magnitude_max_db": m_max,
        "has_phase": phase is not None and len(phase) > 0,
    }

    return result
