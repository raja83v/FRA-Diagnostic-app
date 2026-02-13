"""
FRA Data Normalization Service.

Transforms raw parsed FRA data into a unified, clean schema:
  - Sorts by frequency (ascending)
  - Removes NaN/Inf values
  - Removes duplicate frequency points
  - Optionally resamples to a standard logarithmic frequency grid
  - Maps winding config to standard enum values
"""
from dataclasses import dataclass, field

import numpy as np

from app.models.measurement import WindingConfig
from app.parsers.base import RawFRAData


@dataclass
class NormalizedFRAData:
    """FRA data after normalization — ready for database storage."""
    frequency_hz: list[float]
    magnitude_db: list[float]
    phase_degrees: list[float] | None = None
    vendor: str | None = None
    winding_config: str = WindingConfig.HV_LV.value
    measurement_date: str | None = None
    temperature_celsius: float | None = None
    serial_number: str | None = None
    transformer_name: str | None = None
    notes: str | None = None
    extra_metadata: dict = field(default_factory=dict)
    normalization_notes: list[str] = field(default_factory=list)


# Winding config alias mapping
_WINDING_ALIASES: dict[str, str] = {
    "hv-lv": WindingConfig.HV_LV.value,
    "hv_lv": WindingConfig.HV_LV.value,
    "h-l": WindingConfig.HV_LV.value,
    "high-low": WindingConfig.HV_LV.value,
    "hv-tv": WindingConfig.HV_TV.value,
    "hv_tv": WindingConfig.HV_TV.value,
    "h-t": WindingConfig.HV_TV.value,
    "lv-tv": WindingConfig.LV_TV.value,
    "lv_tv": WindingConfig.LV_TV.value,
    "l-t": WindingConfig.LV_TV.value,
    "hv-gnd": WindingConfig.HV_GND.value,
    "hv_gnd": WindingConfig.HV_GND.value,
    "hv-ground": WindingConfig.HV_GND.value,
    "lv-gnd": WindingConfig.LV_GND.value,
    "lv_gnd": WindingConfig.LV_GND.value,
    "lv-ground": WindingConfig.LV_GND.value,
    "tv-gnd": WindingConfig.TV_GND.value,
    "tv_gnd": WindingConfig.TV_GND.value,
    "hv-open": WindingConfig.HV_OPEN.value,
    "hv_open": WindingConfig.HV_OPEN.value,
    "lv-open": WindingConfig.LV_OPEN.value,
    "lv_open": WindingConfig.LV_OPEN.value,
}


def _normalize_winding_config(raw: str | None) -> str:
    """Map raw winding config string to standard WindingConfig value."""
    if not raw:
        return WindingConfig.HV_LV.value

    cleaned = raw.strip().lower()

    # Direct match to enum value
    for wc in WindingConfig:
        if cleaned == wc.value.lower():
            return wc.value

    # Alias lookup
    if cleaned in _WINDING_ALIASES:
        return _WINDING_ALIASES[cleaned]

    return WindingConfig.OTHER.value


def normalize_fra_data(
    raw: RawFRAData,
    resample: bool = False,
    target_points: int = 800,
) -> NormalizedFRAData:
    """
    Normalize raw FRA data.

    Parameters
    ----------
    raw : RawFRAData
        Parsed raw data from any parser.
    resample : bool
        If True, resample to a uniform log-spaced frequency grid.
    target_points : int
        Number of points if resampling.

    Returns
    -------
    NormalizedFRAData
        Cleaned and standardized data.
    """
    notes: list[str] = []

    freq = np.array(raw.frequency_hz, dtype=float)
    mag = np.array(raw.magnitude_db, dtype=float)
    has_phase = raw.phase_degrees is not None and len(raw.phase_degrees) > 0
    phase = np.array(raw.phase_degrees, dtype=float) if has_phase else None

    original_count = len(freq)

    # ── 1. Remove NaN / Inf ──
    valid_mask = np.isfinite(freq) & np.isfinite(mag)
    if phase is not None:
        valid_mask &= np.isfinite(phase)

    freq = freq[valid_mask]
    mag = mag[valid_mask]
    if phase is not None:
        phase = phase[valid_mask]

    removed = original_count - len(freq)
    if removed > 0:
        notes.append(f"Removed {removed} NaN/Inf value(s)")

    # ── 2. Sort by frequency (ascending) ──
    sort_idx = np.argsort(freq)
    if not np.array_equal(sort_idx, np.arange(len(freq))):
        notes.append("Re-sorted data by ascending frequency")
    freq = freq[sort_idx]
    mag = mag[sort_idx]
    if phase is not None:
        phase = phase[sort_idx]

    # ── 3. Remove duplicate frequency points (keep first) ──
    _, unique_idx = np.unique(freq, return_index=True)
    dup_count = len(freq) - len(unique_idx)
    if dup_count > 0:
        freq = freq[unique_idx]
        mag = mag[unique_idx]
        if phase is not None:
            phase = phase[unique_idx]
        notes.append(f"Removed {dup_count} duplicate frequency point(s)")

    # ── 4. Optional resampling to uniform log-spaced grid ──
    if resample and len(freq) > 2:
        f_min = max(freq[0], 1.0)  # avoid log(0)
        f_max = freq[-1]
        new_freq = np.logspace(np.log10(f_min), np.log10(f_max), target_points)
        new_mag = np.interp(new_freq, freq, mag)
        new_phase = np.interp(new_freq, freq, phase) if phase is not None else None

        notes.append(
            f"Resampled from {len(freq)} to {target_points} log-spaced points"
        )
        freq = new_freq
        mag = new_mag
        phase = new_phase

    # ── Build result ──
    return NormalizedFRAData(
        frequency_hz=freq.tolist(),
        magnitude_db=mag.tolist(),
        phase_degrees=phase.tolist() if phase is not None else None,
        vendor=raw.vendor,
        winding_config=_normalize_winding_config(raw.winding_config),
        measurement_date=raw.measurement_date,
        temperature_celsius=raw.temperature_celsius,
        serial_number=raw.serial_number,
        transformer_name=raw.transformer_name,
        notes=raw.notes,
        extra_metadata=raw.extra_metadata,
        normalization_notes=notes,
    )
