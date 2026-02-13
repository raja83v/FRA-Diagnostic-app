"""Quick test to verify the API is serving data correctly."""
from urllib.request import urlopen
import json

r = urlopen("http://localhost:8000/api/v1/transformers/")
data = json.loads(r.read())
print(f"Transformers: {len(data)}")
for t in data:
    print(f"  - {t['name']} ({t['criticality']}, {t['measurement_count']} measurements)")

print("\nAPI test passed!")
