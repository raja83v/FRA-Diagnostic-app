"""
Synthetic FRA Data Generator with Physics-Based Fault Injection.

Generates healthy FRA curves using a simplified RLC model, then applies
physically realistic distortions to simulate transformer fault types:
- Axial displacement: resonance frequency shifts in mid-range (2-20 kHz)
- Radial deformation: low-frequency response changes (<2 kHz)
- Core grounding issues: low-frequency anomalies (<1 kHz)
- Winding short circuits: high-frequency changes (>100 kHz)
- Loose clamping: broadband damping increase
- Moisture ingress: general response degradation
"""

import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np


# ---------------------------------------------------------------------------
# Healthy FRA Curve Generator (based on seed.py RLC model)
# ---------------------------------------------------------------------------

# Standard resonance model for a healthy transformer
DEFAULT_RESONANCES = [
    {"f0": 800, "q": 5, "amp": -10},
    {"f0": 3500, "q": 8, "amp": -15},
    {"f0": 15000, "q": 12, "amp": -20},
    {"f0": 65000, "q": 10, "amp": -25},
    {"f0": 250000, "q": 7, "amp": -30},
    {"f0": 900000, "q": 5, "amp": -35},
]

FAULT_TYPES = [
    "healthy",
    "axial_displacement",
    "radial_deformation",
    "core_grounding",
    "winding_short_circuit",
    "loose_clamping",
    "moisture_ingress",
]


@dataclass
class FRASample:
    """A single FRA measurement sample with label."""
    frequency_hz: np.ndarray
    magnitude_db: np.ndarray
    phase_degrees: np.ndarray
    label: str
    severity: float = 0.0  # 0.0 = healthy, 0.0-1.0 = fault severity


@dataclass
class SyntheticDataset:
    """Container for a full synthetic dataset."""
    samples: list[FRASample] = field(default_factory=list)

    @property
    def labels(self) -> list[str]:
        return [s.label for s in self.samples]

    def save(self, path: str | Path) -> None:
        """Save dataset as .npz file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        frequencies = np.array([s.frequency_hz for s in self.samples])
        magnitudes = np.array([s.magnitude_db for s in self.samples])
        phases = np.array([s.phase_degrees for s in self.samples])
        labels = np.array([s.label for s in self.samples])
        severities = np.array([s.severity for s in self.samples])

        np.savez_compressed(
            path,
            frequencies=frequencies,
            magnitudes=magnitudes,
            phases=phases,
            labels=labels,
            severities=severities,
        )
        print(f"Saved dataset: {len(self.samples)} samples → {path}")

    @classmethod
    def load(cls, path: str | Path) -> "SyntheticDataset":
        """Load dataset from .npz file."""
        data = np.load(path, allow_pickle=True)
        dataset = cls()
        for i in range(len(data["labels"])):
            dataset.samples.append(
                FRASample(
                    frequency_hz=data["frequencies"][i],
                    magnitude_db=data["magnitudes"][i],
                    phase_degrees=data["phases"][i],
                    label=str(data["labels"][i]),
                    severity=float(data["severities"][i]),
                )
            )
        return dataset


class SyntheticFRAGenerator:
    """
    Generates synthetic FRA training data with physics-based fault injection.

    Usage:
        gen = SyntheticFRAGenerator(num_points=800, seed=42)
        dataset = gen.generate(
            n_healthy=2000,
            n_per_fault=200,
        )
        dataset.save("ml/data_generation/training_data.npz")
    """

    def __init__(
        self,
        num_points: int = 800,
        f_min: float = 20.0,
        f_max: float = 2_000_000.0,
        seed: Optional[int] = 42,
    ):
        self.num_points = num_points
        self.f_min = f_min
        self.f_max = f_max
        self.rng = np.random.RandomState(seed)

        # Log-spaced frequency grid
        self.frequencies = np.logspace(
            np.log10(f_min), np.log10(f_max), num_points
        )

    # ------------------------------------------------------------------
    # Healthy curve generation
    # ------------------------------------------------------------------

    def _random_resonances(self) -> list[dict]:
        """Generate slightly randomized resonance parameters around defaults."""
        resonances = []
        for r in DEFAULT_RESONANCES:
            resonances.append({
                "f0": r["f0"] * (1 + self.rng.uniform(-0.15, 0.15)),
                "q": r["q"] * (1 + self.rng.uniform(-0.2, 0.2)),
                "amp": r["amp"] * (1 + self.rng.uniform(-0.2, 0.2)),
            })
        return resonances

    def generate_healthy_curve(
        self, noise_level: float = 0.3
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate a single healthy FRA curve with natural variation.

        Returns: (frequency_hz, magnitude_db, phase_degrees)
        """
        resonances = self._random_resonances()
        magnitudes = np.zeros(self.num_points)
        phases = np.zeros(self.num_points)

        for i, f in enumerate(self.frequencies):
            # Base magnitude: gentle rolloff
            mag = -5 - 10 * np.log10(1 + (f / 1e6) ** 2)

            phase = 0.0
            for r in resonances:
                f0, q, amp = r["f0"], r["q"], r["amp"]
                x = (f / f0 - f0 / f) * q
                denom = np.sqrt(1 + x * x)
                mag += amp / denom
                phase += np.degrees(np.arctan2(-x, 1))

            magnitudes[i] = mag + self.rng.normal(0, noise_level)
            phases[i] = (phase + self.rng.normal(0, noise_level * 2)) % 360 - 180

        return self.frequencies.copy(), magnitudes, phases

    # ------------------------------------------------------------------
    # Fault injection functions
    # ------------------------------------------------------------------

    def inject_axial_displacement(
        self,
        magnitude: np.ndarray,
        phase: np.ndarray,
        severity: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Simulate axial displacement.

        FRA signature: Shift in resonance frequencies in mid-frequency range
        (2-20 kHz), changes in peak amplitudes, altered spacing between resonances.
        """
        mag = magnitude.copy()
        ph = phase.copy()

        # Frequency band: 2 kHz - 100 kHz (indices)
        mid_mask = (self.frequencies >= 2_000) & (self.frequencies <= 100_000)
        mid_indices = np.where(mid_mask)[0]

        if len(mid_indices) == 0:
            return mag, ph

        # Shift resonance locations by applying frequency-dependent magnitude distortion
        shift_amount = severity * 8  # dB shift at max severity
        # Create a sinusoidal distortion pattern (simulates resonance shifting)
        t = np.linspace(0, 3 * np.pi, len(mid_indices))
        distortion = shift_amount * np.sin(t) * self.rng.uniform(0.7, 1.3)

        mag[mid_indices] += distortion

        # Alter peak amplitudes in mid-band
        amplitude_change = severity * 5
        peak_distortion = amplitude_change * np.sin(t * 1.5)
        mag[mid_indices] += peak_distortion * self.rng.uniform(0.5, 1.0)

        # Phase distortion in affected band
        phase_shift = severity * 25  # degrees
        ph[mid_indices] += phase_shift * np.sin(t * 2) * self.rng.uniform(0.6, 1.2)

        # Slight spillover into adjacent bands
        spillover = severity * 2
        low_adj = np.where((self.frequencies >= 1_000) & (self.frequencies < 2_000))[0]
        high_adj = np.where((self.frequencies > 100_000) & (self.frequencies <= 200_000))[0]
        if len(low_adj) > 0:
            mag[low_adj] += self.rng.normal(0, spillover, len(low_adj))
        if len(high_adj) > 0:
            mag[high_adj] += self.rng.normal(0, spillover, len(high_adj))

        return mag, ph

    def inject_radial_deformation(
        self,
        magnitude: np.ndarray,
        phase: np.ndarray,
        severity: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Simulate radial deformation.

        FRA signature: Changes in low-frequency response (below 2 kHz),
        capacitance variations affecting overall curve shape, damping changes.
        """
        mag = magnitude.copy()
        ph = phase.copy()

        # Low-frequency band: below 2 kHz
        low_mask = self.frequencies <= 2_000
        low_indices = np.where(low_mask)[0]

        if len(low_indices) == 0:
            return mag, ph

        # Capacitance-like change: shifts the low-frequency baseline
        cap_shift = severity * 6  # dB
        t = np.linspace(0, np.pi, len(low_indices))
        mag[low_indices] += cap_shift * np.sin(t) * self.rng.uniform(0.8, 1.2)

        # Damping change affects the overall shape
        damping_factor = 1 + severity * 0.3
        # Broader effect: slightly dampen mid-range too
        mid_mask = (self.frequencies > 2_000) & (self.frequencies <= 20_000)
        mid_indices = np.where(mid_mask)[0]
        if len(mid_indices) > 0:
            damping = severity * 3 * np.exp(-np.linspace(0, 3, len(mid_indices)))
            mag[mid_indices] -= damping

        # Phase shifts in low-frequency region
        ph[low_indices] += severity * 15 * np.sin(t * 2) * self.rng.uniform(0.7, 1.1)

        return mag, ph

    def inject_core_grounding(
        self,
        magnitude: np.ndarray,
        phase: np.ndarray,
        severity: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Simulate core grounding issues.

        FRA signature: Low-frequency anomalies (below 1 kHz), altered inductance
        patterns, additional resonance points in low-frequency region.
        """
        mag = magnitude.copy()
        ph = phase.copy()

        # Very low frequency band: below 1 kHz
        vlow_mask = self.frequencies <= 1_000
        vlow_indices = np.where(vlow_mask)[0]

        if len(vlow_indices) == 0:
            return mag, ph

        # Add spurious resonance peak(s) simulating inductance anomaly
        n_spurious = self.rng.randint(1, 3)
        for _ in range(n_spurious):
            peak_pos = self.rng.randint(len(vlow_indices) // 4, len(vlow_indices) - 1)
            peak_width = max(3, int(len(vlow_indices) * 0.15))
            peak_amp = severity * 10 * self.rng.uniform(0.6, 1.4)

            for j in range(max(0, peak_pos - peak_width), min(len(vlow_indices), peak_pos + peak_width)):
                dist = abs(j - peak_pos) / peak_width
                mag[vlow_indices[j]] += peak_amp * np.exp(-3 * dist ** 2)

        # Altered inductance pattern: overall level shift
        inductance_shift = severity * 4 * self.rng.uniform(0.8, 1.2)
        mag[vlow_indices] += inductance_shift

        # Phase anomalies
        ph[vlow_indices] += severity * 20 * self.rng.uniform(-1, 1, len(vlow_indices))

        # Slight effect up to 2 kHz
        ext_mask = (self.frequencies > 1_000) & (self.frequencies <= 2_000)
        ext_indices = np.where(ext_mask)[0]
        if len(ext_indices) > 0:
            decay = severity * 2 * np.exp(-np.linspace(0, 4, len(ext_indices)))
            mag[ext_indices] += decay

        return mag, ph

    def inject_winding_short_circuit(
        self,
        magnitude: np.ndarray,
        phase: np.ndarray,
        severity: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Simulate winding short circuits.

        FRA signature: High-frequency response changes (above 100 kHz),
        emergence of new resonance peaks, amplitude variations.
        """
        mag = magnitude.copy()
        ph = phase.copy()

        # High-frequency band: above 100 kHz
        high_mask = self.frequencies >= 100_000
        high_indices = np.where(high_mask)[0]

        if len(high_indices) == 0:
            return mag, ph

        # Amplitude variations in high-frequency band
        variation_amp = severity * 10
        t = np.linspace(0, 4 * np.pi, len(high_indices))
        mag[high_indices] += variation_amp * np.sin(t) * self.rng.uniform(0.6, 1.3)

        # Add new resonance peaks (simulating inter-turn shorts)
        n_peaks = self.rng.randint(1, 4)
        for _ in range(n_peaks):
            peak_pos = self.rng.randint(0, len(high_indices) - 1)
            peak_width = max(2, int(len(high_indices) * 0.08))
            peak_amp = severity * 12 * self.rng.uniform(0.5, 1.5)

            for j in range(max(0, peak_pos - peak_width), min(len(high_indices), peak_pos + peak_width)):
                dist = abs(j - peak_pos) / peak_width
                mag[high_indices[j]] += peak_amp * np.exp(-2 * dist ** 2)

        # Phase distortion
        ph[high_indices] += severity * 30 * np.sin(t * 1.5) * self.rng.uniform(0.5, 1.0)

        return mag, ph

    def inject_loose_clamping(
        self,
        magnitude: np.ndarray,
        phase: np.ndarray,
        severity: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Simulate loose clamping.

        FRA signature: Broadband changes across frequency spectrum,
        increased damping, progressive degradation.
        """
        mag = magnitude.copy()
        ph = phase.copy()

        # Broadband damping: affects entire spectrum
        damping = severity * 4  # dB overall damping
        freq_normalized = np.log10(self.frequencies / self.f_min) / np.log10(self.f_max / self.f_min)

        # Non-uniform damping (more in mid-range where mechanical effects show)
        damping_profile = damping * (0.5 + 0.5 * np.sin(np.pi * freq_normalized))
        mag -= damping_profile * self.rng.uniform(0.7, 1.3)

        # Add broadband noise (degradation)
        noise_level = severity * 2
        mag += self.rng.normal(0, noise_level, self.num_points)

        # Reduce Q-factor effect (peaks become less sharp)
        # Implemented as smoothing / low-pass filtering
        if severity > 0.3:
            kernel_size = max(3, int(severity * 10))
            kernel = np.ones(kernel_size) / kernel_size
            mag_smooth = np.convolve(mag, kernel, mode='same')
            blend = severity * 0.4
            mag = (1 - blend) * mag + blend * mag_smooth

        # Phase noise increase
        ph += self.rng.normal(0, severity * 8, self.num_points)

        return mag, ph

    def inject_moisture_ingress(
        self,
        magnitude: np.ndarray,
        phase: np.ndarray,
        severity: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Simulate moisture ingress.

        FRA signature: General response degradation, reduced insulation quality
        affecting capacitive coupling, long-term trend changes.
        """
        mag = magnitude.copy()
        ph = phase.copy()

        # Overall response degradation (magnitude shift)
        overall_shift = severity * 3 * self.rng.uniform(0.8, 1.2)
        mag -= overall_shift

        # Capacitive coupling degradation:
        # Higher frequencies are affected more (capacitive paths)
        freq_weight = np.log10(self.frequencies / self.f_min) / np.log10(self.f_max / self.f_min)
        cap_degradation = severity * 5 * freq_weight * self.rng.uniform(0.7, 1.3)
        mag -= cap_degradation

        # Insulation quality: smoothing of sharp resonance features
        if severity > 0.2:
            kernel_size = max(3, int(severity * 8))
            kernel = np.ones(kernel_size) / kernel_size
            mag_smooth = np.convolve(mag, kernel, mode='same')
            blend = severity * 0.3
            mag = (1 - blend) * mag + blend * mag_smooth

        # Phase degradation: general drift
        phase_drift = severity * 12
        ph += phase_drift * freq_weight * self.rng.uniform(-1, 1)

        # Random noise increase (degraded insulation)
        noise = severity * 1.5
        mag += self.rng.normal(0, noise, self.num_points)
        ph += self.rng.normal(0, noise * 3, self.num_points)

        return mag, ph

    # ------------------------------------------------------------------
    # Dataset generation
    # ------------------------------------------------------------------

    FAULT_INJECTORS = {
        "axial_displacement": "inject_axial_displacement",
        "radial_deformation": "inject_radial_deformation",
        "core_grounding": "inject_core_grounding",
        "winding_short_circuit": "inject_winding_short_circuit",
        "loose_clamping": "inject_loose_clamping",
        "moisture_ingress": "inject_moisture_ingress",
    }

    def generate(
        self,
        n_healthy: int = 2000,
        n_per_fault: int = 200,
        noise_range: tuple[float, float] = (0.2, 0.6),
        severity_range: tuple[float, float] = (0.3, 1.0),
    ) -> SyntheticDataset:
        """
        Generate a complete synthetic training dataset.

        Args:
            n_healthy: Number of healthy samples to generate.
            n_per_fault: Number of samples per fault type.
            noise_range: Range of noise levels for curve generation.
            severity_range: Range of fault severity levels.

        Returns:
            SyntheticDataset with all samples.
        """
        dataset = SyntheticDataset()

        # Generate healthy samples
        print(f"Generating {n_healthy} healthy samples...")
        for i in range(n_healthy):
            noise = self.rng.uniform(*noise_range)
            freq, mag, phase = self.generate_healthy_curve(noise_level=noise)
            dataset.samples.append(
                FRASample(
                    frequency_hz=freq,
                    magnitude_db=mag,
                    phase_degrees=phase,
                    label="healthy",
                    severity=0.0,
                )
            )

        # Generate fault samples
        for fault_type, injector_name in self.FAULT_INJECTORS.items():
            print(f"Generating {n_per_fault} {fault_type} samples...")
            injector = getattr(self, injector_name)

            for i in range(n_per_fault):
                noise = self.rng.uniform(*noise_range)
                freq, mag, phase = self.generate_healthy_curve(noise_level=noise)

                severity = self.rng.uniform(*severity_range)
                mag, phase = injector(mag, phase, severity)

                dataset.samples.append(
                    FRASample(
                        frequency_hz=freq,
                        magnitude_db=mag,
                        phase_degrees=phase,
                        label=fault_type,
                        severity=severity,
                    )
                )

        # Shuffle
        self.rng.shuffle(dataset.samples)

        # Print summary
        from collections import Counter
        counts = Counter(dataset.labels)
        print(f"\nDataset summary ({len(dataset.samples)} total samples):")
        for label in FAULT_TYPES:
            if label in counts:
                print(f"  {label}: {counts[label]}")

        return dataset


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic FRA training data")
    parser.add_argument("--n-healthy", type=int, default=2000, help="Number of healthy samples")
    parser.add_argument("--n-per-fault", type=int, default=200, help="Samples per fault type")
    parser.add_argument("--output", type=str, default="ml/data_generation/training_data.npz", help="Output file path")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    gen = SyntheticFRAGenerator(seed=args.seed)
    dataset = gen.generate(n_healthy=args.n_healthy, n_per_fault=args.n_per_fault)
    dataset.save(args.output)
