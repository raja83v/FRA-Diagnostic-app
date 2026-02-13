"""
Seed script: Populate the database with sample transformers and measurements.
Run: python -m app.seed
"""
import uuid
import math
import random
from datetime import datetime, timezone, timedelta

from app.database import SessionLocal, Base, engine
from app.models.transformer import Transformer, TransformerCriticality
from app.models.measurement import FRAMeasurement, WindingConfig


def generate_fra_curve(
    num_points: int = 800,
    noise_level: float = 0.5,
    seed: int | None = None,
) -> tuple[list[float], list[float], list[float]]:
    """
    Generate a synthetic healthy FRA curve using a simplified RLC model.

    Returns (frequency_hz, magnitude_db, phase_degrees) arrays.
    """
    if seed is not None:
        random.seed(seed)

    # Frequency sweep: 20 Hz to 2 MHz (logarithmic)
    f_min, f_max = 20.0, 2_000_000.0
    frequencies = [
        f_min * (f_max / f_min) ** (i / (num_points - 1))
        for i in range(num_points)
    ]

    # Simulate multiple resonance points (typical transformer FRA)
    resonances = [
        {"f0": 800, "q": 5, "amp": -10},
        {"f0": 3500, "q": 8, "amp": -15},
        {"f0": 15000, "q": 12, "amp": -20},
        {"f0": 65000, "q": 10, "amp": -25},
        {"f0": 250000, "q": 7, "amp": -30},
        {"f0": 900000, "q": 5, "amp": -35},
    ]

    magnitudes = []
    phases = []

    for f in frequencies:
        # Base magnitude: gentle rolloff
        mag = -5 - 10 * math.log10(1 + (f / 1e6) ** 2)

        # Add resonance contributions
        phase = 0.0
        for r in resonances:
            f0, q, amp = r["f0"], r["q"], r["amp"]
            x = (f / f0 - f0 / f) * q
            denom = math.sqrt(1 + x * x)
            mag += amp / denom
            phase += math.degrees(math.atan2(-x, 1))

        # Add noise
        mag += random.gauss(0, noise_level)
        phase += random.gauss(0, noise_level * 2)

        magnitudes.append(round(mag, 4))
        phases.append(round(phase % 360 - 180, 4))  # Wrap to [-180, 180]

    freq_rounded = [round(f, 2) for f in frequencies]
    return freq_rounded, magnitudes, phases


SAMPLE_TRANSFORMERS = [
    {
        "name": "GT-01 (Substation Alpha)",
        "location": "Northern Grid, State Electricity Board",
        "substation": "Alpha 400kV Substation",
        "voltage_rating_kv": 400.0,
        "power_rating_mva": 315.0,
        "manufacturer": "BHEL",
        "year_of_manufacture": 2005,
        "serial_number": "BHEL-GT-2005-0142",
        "criticality": TransformerCriticality.CRITICAL,
    },
    {
        "name": "GT-02 (Substation Alpha)",
        "location": "Northern Grid, State Electricity Board",
        "substation": "Alpha 400kV Substation",
        "voltage_rating_kv": 400.0,
        "power_rating_mva": 315.0,
        "manufacturer": "BHEL",
        "year_of_manufacture": 2005,
        "serial_number": "BHEL-GT-2005-0143",
        "criticality": TransformerCriticality.CRITICAL,
    },
    {
        "name": "ICT-01 (Substation Beta)",
        "location": "Western Grid, Transmission Utility",
        "substation": "Beta 220kV Substation",
        "voltage_rating_kv": 220.0,
        "power_rating_mva": 160.0,
        "manufacturer": "Siemens",
        "year_of_manufacture": 2010,
        "serial_number": "SIE-ICT-2010-0087",
        "criticality": TransformerCriticality.IMPORTANT,
    },
    {
        "name": "PT-03 (Substation Gamma)",
        "location": "Southern Grid, Distribution Company",
        "substation": "Gamma 132kV Substation",
        "voltage_rating_kv": 132.0,
        "power_rating_mva": 50.0,
        "manufacturer": "ABB",
        "year_of_manufacture": 2015,
        "serial_number": "ABB-PT-2015-0321",
        "criticality": TransformerCriticality.STANDARD,
    },
    {
        "name": "GT-05 (Substation Delta)",
        "location": "Eastern Grid, Power Generation Corp",
        "substation": "Delta 765kV Substation",
        "voltage_rating_kv": 765.0,
        "power_rating_mva": 500.0,
        "manufacturer": "Crompton Greaves",
        "year_of_manufacture": 2018,
        "serial_number": "CG-GT-2018-0056",
        "criticality": TransformerCriticality.CRITICAL,
    },
]


def seed_database():
    """Populate database with sample transformers and FRA measurements."""
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if already seeded
        existing = db.query(Transformer).count()
        if existing > 0:
            print(f"Database already has {existing} transformers. Skipping seed.")
            return

        print("Seeding database with sample data...")

        winding_configs = [
            WindingConfig.HV_LV,
            WindingConfig.HV_TV,
            WindingConfig.LV_TV,
        ]
        vendors = ["Omicron", "Megger", "Doble"]

        for i, t_data in enumerate(SAMPLE_TRANSFORMERS):
            transformer = Transformer(id=str(uuid.uuid4()), **t_data)
            db.add(transformer)
            db.flush()  # Get the ID

            print(f"  Created transformer: {transformer.name}")

            # Create 2-3 measurements per transformer
            num_measurements = random.randint(2, 3)
            baseline_id = None

            for j in range(num_measurements):
                freq, mag, phase = generate_fra_curve(
                    num_points=800,
                    noise_level=0.3 + j * 0.1,
                    seed=i * 100 + j,
                )

                measurement = FRAMeasurement(
                    id=str(uuid.uuid4()),
                    transformer_id=transformer.id,
                    measurement_date=datetime.now(timezone.utc)
                    - timedelta(days=365 * (num_measurements - j)),
                    winding_config=winding_configs[j % len(winding_configs)],
                    frequency_hz=freq,
                    magnitude_db=mag,
                    phase_degrees=phase,
                    vendor=vendors[i % len(vendors)],
                    original_format="csv",
                    original_filename=f"fra_measurement_{transformer.serial_number}_{j+1}.csv",
                    temperature_celsius=round(random.uniform(20, 35), 1),
                )
                db.add(measurement)

                if j == 0:
                    baseline_id = measurement.id

                print(f"    Measurement {j+1}: {measurement.winding_config.value}, "
                      f"{len(freq)} points, vendor={measurement.vendor}")

            # Set baseline
            if baseline_id:
                transformer.baseline_measurement_id = baseline_id

        db.commit()
        total_t = db.query(Transformer).count()
        total_m = db.query(FRAMeasurement).count()
        print(f"\nSeed complete: {total_t} transformers, {total_m} measurements.")

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
