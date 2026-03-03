"""
FRA Feature Extraction Pipeline.

Extracts meaningful features from raw FRA curves for ML fault classification:
- Statistical features: mean, std, skewness, kurtosis, energy, range
- Frequency band features: energy/mean/std in low/mid/high bands
- Resonance features: peak counts, locations, amplitudes, Q-factors
- Phase features: statistics and correlation with magnitude
- Comparison features (optional): correlation, ASLE, relative factor vs baseline
"""

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy import signal, stats, interpolate


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Frequency band boundaries (Hz) per IEC 60076-18
LOW_BAND = (20.0, 2_000.0)       # Core and main winding
MID_BAND = (2_000.0, 100_000.0)  # Winding structure / mechanical integrity
HIGH_BAND = (100_000.0, 2_000_000.0)  # Inter-turn and lead connections

# Standard grid for resampling
DEFAULT_NUM_POINTS = 800
DEFAULT_F_MIN = 20.0
DEFAULT_F_MAX = 2_000_000.0


@dataclass
class FeatureResult:
    """Result of feature extraction on one FRA sample."""
    feature_names: list[str]
    feature_values: np.ndarray
    feature_dict: dict[str, float]


class FRAFeatureExtractor:
    """
    Extracts features from FRA magnitude/phase curves.

    Usage:
        extractor = FRAFeatureExtractor(target_points=800)
        result = extractor.extract(frequency_hz, magnitude_db, phase_degrees)
        # result.feature_values is a 1D numpy array ready for sklearn/xgboost
    """

    def __init__(
        self,
        target_points: int = DEFAULT_NUM_POINTS,
        f_min: float = DEFAULT_F_MIN,
        f_max: float = DEFAULT_F_MAX,
    ):
        self.target_points = target_points
        self.f_min = f_min
        self.f_max = f_max

        # Pre-compute the standard log-spaced frequency grid
        self.standard_grid = np.logspace(
            np.log10(f_min), np.log10(f_max), target_points
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(
        self,
        frequency_hz: np.ndarray,
        magnitude_db: np.ndarray,
        phase_degrees: Optional[np.ndarray] = None,
        baseline_freq: Optional[np.ndarray] = None,
        baseline_mag: Optional[np.ndarray] = None,
    ) -> FeatureResult:
        """
        Extract all features from an FRA measurement.

        Args:
            frequency_hz: Frequency array (Hz).
            magnitude_db: Magnitude array (dB).
            phase_degrees: Phase array (degrees), optional.
            baseline_freq: Baseline frequency array for comparison features.
            baseline_mag: Baseline magnitude array for comparison features.

        Returns:
            FeatureResult with named features and flat numpy array.
        """
        freq = np.asarray(frequency_hz, dtype=np.float64)
        mag = np.asarray(magnitude_db, dtype=np.float64)

        # Resample to standard grid if needed
        if len(freq) != self.target_points or not np.allclose(freq, self.standard_grid, rtol=0.01):
            mag = self._resample(freq, mag, self.standard_grid)
            if phase_degrees is not None:
                phase_degrees = self._resample(freq, np.asarray(phase_degrees, dtype=np.float64), self.standard_grid)
            freq = self.standard_grid.copy()

        features: dict[str, float] = {}

        # 1. Statistical features
        features.update(self._statistical_features(mag))

        # 2. Frequency band features
        features.update(self._band_features(freq, mag))

        # 3. Resonance features
        features.update(self._resonance_features(freq, mag))

        # 4. Phase features (if available)
        if phase_degrees is not None:
            phase = np.asarray(phase_degrees, dtype=np.float64)
            features.update(self._phase_features(freq, mag, phase))
        else:
            # Fill phase features with zeros
            features.update(self._phase_features_placeholder())

        # 5. Comparison features (if baseline provided)
        if baseline_freq is not None and baseline_mag is not None:
            bl_freq = np.asarray(baseline_freq, dtype=np.float64)
            bl_mag = np.asarray(baseline_mag, dtype=np.float64)
            # Resample baseline to same grid
            if len(bl_freq) != self.target_points:
                bl_mag = self._resample(bl_freq, bl_mag, self.standard_grid)
            features.update(self._comparison_features(mag, bl_mag))
        else:
            features.update(self._comparison_features_placeholder())

        # Build result
        names = list(features.keys())
        values = np.array(list(features.values()), dtype=np.float64)

        # Replace any NaN/Inf with 0
        values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)

        return FeatureResult(
            feature_names=names,
            feature_values=values,
            feature_dict=dict(zip(names, values)),
        )

    def extract_batch(
        self,
        frequencies: np.ndarray,
        magnitudes: np.ndarray,
        phases: Optional[np.ndarray] = None,
    ) -> tuple[np.ndarray, list[str]]:
        """
        Extract features for a batch of samples.

        Args:
            frequencies: (N, num_points) array of frequency values.
            magnitudes: (N, num_points) array of magnitude values.
            phases: (N, num_points) array of phase values, optional.

        Returns:
            (feature_matrix, feature_names) where feature_matrix is (N, num_features).
        """
        n_samples = len(magnitudes)
        results = []
        feature_names = None

        for i in range(n_samples):
            phase_i = phases[i] if phases is not None else None
            result = self.extract(frequencies[i], magnitudes[i], phase_i)
            results.append(result.feature_values)
            if feature_names is None:
                feature_names = result.feature_names

            if (i + 1) % 500 == 0 or i == n_samples - 1:
                print(f"    Extracted features: {i + 1}/{n_samples}")

        return np.array(results), feature_names or []

    # ------------------------------------------------------------------
    # Statistical features (8 features)
    # ------------------------------------------------------------------

    def _statistical_features(self, mag: np.ndarray) -> dict[str, float]:
        """Global statistical features of the magnitude curve."""
        return {
            "stat_mean": float(np.mean(mag)),
            "stat_std": float(np.std(mag)),
            "stat_skewness": float(stats.skew(mag)),
            "stat_kurtosis": float(stats.kurtosis(mag)),
            "stat_energy": float(np.sum(mag ** 2)),
            "stat_peak_to_peak": float(np.ptp(mag)),
            "stat_dynamic_range": float(np.max(mag) - np.min(mag)),
            "stat_rms": float(np.sqrt(np.mean(mag ** 2))),
        }

    # ------------------------------------------------------------------
    # Frequency band features (9 features)
    # ------------------------------------------------------------------

    def _band_features(self, freq: np.ndarray, mag: np.ndarray) -> dict[str, float]:
        """Features computed separately for low, mid, and high frequency bands."""
        features = {}
        bands = [
            ("low", LOW_BAND),
            ("mid", MID_BAND),
            ("high", HIGH_BAND),
        ]

        for name, (f_lo, f_hi) in bands:
            mask = (freq >= f_lo) & (freq <= f_hi)
            band_mag = mag[mask]

            if len(band_mag) == 0:
                features[f"band_{name}_energy"] = 0.0
                features[f"band_{name}_mean"] = 0.0
                features[f"band_{name}_std"] = 0.0
            else:
                features[f"band_{name}_energy"] = float(np.sum(band_mag ** 2))
                features[f"band_{name}_mean"] = float(np.mean(band_mag))
                features[f"band_{name}_std"] = float(np.std(band_mag))

        return features

    # ------------------------------------------------------------------
    # Resonance features (~20 features)
    # ------------------------------------------------------------------

    def _resonance_features(self, freq: np.ndarray, mag: np.ndarray) -> dict[str, float]:
        """Detect resonance peaks and extract their characteristics."""
        features: dict[str, float] = {}

        # Find peaks (resonances) and valleys (anti-resonances)
        peaks, peak_props = signal.find_peaks(mag, distance=5, prominence=1.0)
        valleys, valley_props = signal.find_peaks(-mag, distance=5, prominence=1.0)

        features["res_total_peaks"] = float(len(peaks))
        features["res_total_valleys"] = float(len(valleys))

        # Peaks per frequency band
        for band_name, (f_lo, f_hi) in [("low", LOW_BAND), ("mid", MID_BAND), ("high", HIGH_BAND)]:
            band_peaks = [p for p in peaks if f_lo <= freq[p] <= f_hi]
            features[f"res_{band_name}_peak_count"] = float(len(band_peaks))

        # Top-5 peak frequencies and amplitudes (padded with 0 if fewer)
        if len(peaks) > 0:
            # Sort by prominence (most significant peaks first)
            sorted_peak_indices = np.argsort(-peak_props["prominences"])
            top_n = min(5, len(peaks))

            for k in range(5):
                if k < top_n:
                    idx = peaks[sorted_peak_indices[k]]
                    features[f"res_peak_{k}_freq_hz"] = float(freq[idx])
                    features[f"res_peak_{k}_mag_db"] = float(mag[idx])
                else:
                    features[f"res_peak_{k}_freq_hz"] = 0.0
                    features[f"res_peak_{k}_mag_db"] = 0.0

            # Estimate Q-factor for top peaks
            for k in range(min(3, top_n)):
                idx = peaks[sorted_peak_indices[k]]
                q = self._estimate_q_factor(freq, mag, idx)
                features[f"res_peak_{k}_q_factor"] = float(q)
            for k in range(min(3, top_n), 3):
                features[f"res_peak_{k}_q_factor"] = 0.0
        else:
            for k in range(5):
                features[f"res_peak_{k}_freq_hz"] = 0.0
                features[f"res_peak_{k}_mag_db"] = 0.0
            for k in range(3):
                features[f"res_peak_{k}_q_factor"] = 0.0

        return features

    def _estimate_q_factor(self, freq: np.ndarray, mag: np.ndarray, peak_idx: int) -> float:
        """
        Estimate the quality factor (Q) of a resonance peak.
        Q = f0 / bandwidth_3dB
        """
        if peak_idx < 1 or peak_idx >= len(mag) - 1:
            return 0.0

        peak_mag = mag[peak_idx]
        threshold = peak_mag - 3.0  # 3 dB down from peak

        # Find left -3dB point
        left_idx = peak_idx
        for i in range(peak_idx - 1, -1, -1):
            if mag[i] <= threshold:
                left_idx = i
                break

        # Find right -3dB point
        right_idx = peak_idx
        for i in range(peak_idx + 1, len(mag)):
            if mag[i] <= threshold:
                right_idx = i
                break

        if left_idx == peak_idx or right_idx == peak_idx:
            return 0.0

        bandwidth = freq[right_idx] - freq[left_idx]
        if bandwidth <= 0:
            return 0.0

        return freq[peak_idx] / bandwidth

    # ------------------------------------------------------------------
    # Phase features (8 features)
    # ------------------------------------------------------------------

    def _phase_features(
        self, freq: np.ndarray, mag: np.ndarray, phase: np.ndarray
    ) -> dict[str, float]:
        """Features extracted from the phase response."""
        features = {
            "phase_mean": float(np.mean(phase)),
            "phase_std": float(np.std(phase)),
            "phase_skewness": float(stats.skew(phase)),
            "phase_mag_correlation": float(np.corrcoef(mag, phase)[0, 1])
            if len(mag) > 1 else 0.0,
        }

        # Phase slope in each band
        for band_name, (f_lo, f_hi) in [("low", LOW_BAND), ("mid", MID_BAND), ("high", HIGH_BAND)]:
            mask = (freq >= f_lo) & (freq <= f_hi)
            band_phase = phase[mask]
            band_freq = freq[mask]

            if len(band_phase) > 1:
                # Linear regression slope of phase vs log-frequency
                log_freq = np.log10(band_freq)
                slope, _, _, _, _ = stats.linregress(log_freq, band_phase)
                features[f"phase_{band_name}_slope"] = float(slope)
            else:
                features[f"phase_{band_name}_slope"] = 0.0

        # Wrapping count (number of 180-degree crossings)
        crossings = np.sum(np.abs(np.diff(phase)) > 90)
        features["phase_wrap_count"] = float(crossings)

        return features

    def _phase_features_placeholder(self) -> dict[str, float]:
        """Placeholder when phase data is not available."""
        return {
            "phase_mean": 0.0,
            "phase_std": 0.0,
            "phase_skewness": 0.0,
            "phase_mag_correlation": 0.0,
            "phase_low_slope": 0.0,
            "phase_mid_slope": 0.0,
            "phase_high_slope": 0.0,
            "phase_wrap_count": 0.0,
        }

    # ------------------------------------------------------------------
    # Comparison features (6 features)
    # ------------------------------------------------------------------

    def _comparison_features(
        self, mag: np.ndarray, baseline_mag: np.ndarray
    ) -> dict[str, float]:
        """Features comparing current measurement to a baseline."""
        # Correlation coefficient
        if len(mag) > 1:
            corr = float(np.corrcoef(mag, baseline_mag)[0, 1])
        else:
            corr = 0.0

        # Absolute Sum of Logarithmic Error (ASLE)
        # ASLE = sum(|20*log10(Hi/Hr)|) where Hi=current, Hr=reference
        # In dB domain: ASLE = sum(|mag - baseline_mag|)
        asle = float(np.sum(np.abs(mag - baseline_mag)))

        # Mean absolute difference
        mad = float(np.mean(np.abs(mag - baseline_mag)))

        # Max absolute difference
        max_diff = float(np.max(np.abs(mag - baseline_mag)))

        # Relative factor (normalized cross-correlation)
        norm_a = np.linalg.norm(mag)
        norm_b = np.linalg.norm(baseline_mag)
        if norm_a > 0 and norm_b > 0:
            relative_factor = float(np.dot(mag, baseline_mag) / (norm_a * norm_b))
        else:
            relative_factor = 0.0

        # Cross-correlation peak lag
        cross_corr = np.correlate(mag - np.mean(mag), baseline_mag - np.mean(baseline_mag), mode='full')
        if np.max(np.abs(cross_corr)) > 0:
            lag = float(np.argmax(cross_corr) - len(mag) + 1)
        else:
            lag = 0.0

        return {
            "comp_correlation": corr,
            "comp_asle": asle,
            "comp_mean_abs_diff": mad,
            "comp_max_abs_diff": max_diff,
            "comp_relative_factor": relative_factor,
            "comp_cross_corr_lag": lag,
        }

    def _comparison_features_placeholder(self) -> dict[str, float]:
        """Placeholder when no baseline is available."""
        return {
            "comp_correlation": 1.0,   # Perfect correlation with "self"
            "comp_asle": 0.0,
            "comp_mean_abs_diff": 0.0,
            "comp_max_abs_diff": 0.0,
            "comp_relative_factor": 1.0,
            "comp_cross_corr_lag": 0.0,
        }

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _resample(
        freq: np.ndarray, values: np.ndarray, target_freq: np.ndarray
    ) -> np.ndarray:
        """Resample values from freq grid to target_freq grid using interpolation."""
        # Use log-space interpolation for better accuracy on FRA data
        log_freq = np.log10(np.clip(freq, 1e-10, None))
        log_target = np.log10(np.clip(target_freq, 1e-10, None))

        # Cubic spline interpolation
        try:
            interp_func = interpolate.interp1d(
                log_freq, values,
                kind='cubic',
                bounds_error=False,
                fill_value='extrapolate',
            )
            return interp_func(log_target)
        except Exception:
            # Fallback to linear
            interp_func = interpolate.interp1d(
                log_freq, values,
                kind='linear',
                bounds_error=False,
                fill_value='extrapolate',
            )
            return interp_func(log_target)

    def get_feature_names(self) -> list[str]:
        """
        Get the list of all feature names (in order) without running extraction.
        Useful for training pipeline setup.
        """
        # Generate a dummy curve to get feature names
        dummy_freq = self.standard_grid
        dummy_mag = np.zeros(self.target_points)
        dummy_phase = np.zeros(self.target_points)
        result = self.extract(dummy_freq, dummy_mag, dummy_phase)
        return result.feature_names
