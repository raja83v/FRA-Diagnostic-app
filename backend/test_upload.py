"""
Phase 2 - End-to-end test: upload sample files through the API.
"""
import sys
import os
import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_upload():
    # 1. Get a transformer to upload to
    resp = requests.get(f"{BASE_URL}/transformers/")
    transformers = resp.json()
    if not transformers:
        print("ERROR: No transformers in database. Run seed.py first.")
        sys.exit(1)
    
    transformer_id = transformers[0]["id"]
    transformer_name = transformers[0]["name"]
    print(f"Using transformer: {transformer_name} ({transformer_id})")

    samples_dir = os.path.join(os.path.dirname(__file__), "..", "data", "samples")
    
    test_files = [
        ("sample_fra_generic.csv", "HV-LV"),
        ("sample_fra_generic.xml", "HV-TV"),
        ("sample_omicron.csv", "LV-TV"),
    ]

    results = []
    for filename, winding in test_files:
        filepath = os.path.join(samples_dir, filename)
        if not os.path.exists(filepath):
            print(f"  SKIP: {filename} not found")
            continue

        print(f"\n--- Uploading: {filename} (winding={winding}) ---")
        with open(filepath, "rb") as f:
            resp = requests.post(
                f"{BASE_URL}/measurements/upload",
                files={"file": (filename, f)},
                data={
                    "transformer_id": transformer_id,
                    "winding_config": winding,
                    "temperature_celsius": "25.0",
                    "notes": f"Test upload of {filename}",
                },
            )
        
        if resp.status_code == 201:
            data = resp.json()
            print(f"  OK: {data['data_points']} points, vendor={data['vendor_detected']}")
            print(f"      range={data['frequency_range']}")
            if data["validation_warnings"]:
                print(f"      warnings: {data['validation_warnings']}")
            results.append(("PASS", filename))
        else:
            print(f"  FAIL ({resp.status_code}): {resp.text}")
            results.append(("FAIL", filename))

    # 2. Check import history
    print("\n--- Import History ---")
    resp = requests.get(f"{BASE_URL}/imports/")
    if resp.status_code == 200:
        history = resp.json()
        print(f"  {len(history)} record(s) in import history")
        for rec in history:
            print(f"    [{rec['status']}] {rec['original_filename']} "
                  f"- {rec.get('data_points', '?')} pts "
                  f"- vendor={rec.get('detected_vendor', '?')}")
    else:
        print(f"  FAIL: {resp.status_code} - {resp.text}")

    # 3. Check import stats
    resp = requests.get(f"{BASE_URL}/imports/stats")
    if resp.status_code == 200:
        stats = resp.json()
        print(f"\n--- Import Stats ---")
        print(f"  Total: {stats['total_imports']}, Success: {stats['successful']}, "
              f"Failed: {stats['failed']}")

    # Summary
    print(f"\n{'='*50}")
    print(f"Results: {sum(1 for r in results if r[0]=='PASS')}/{len(results)} passed")
    for status, name in results:
        print(f"  [{status}] {name}")

if __name__ == "__main__":
    test_upload()
