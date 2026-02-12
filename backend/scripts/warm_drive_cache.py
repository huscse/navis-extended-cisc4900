import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from backend.services.drive import _drive, _list_children

ROOT_ID = "1vHWntmgJZ7Y-GAdeqGRp3mELUJis9U5e"

print("Checking root folder contents...")
children = _list_children(ROOT_ID)

if not children:
    print("❌ No files found! Service account may not have access.")
else:
    print(f"✅ Found {len(children)} items:")
    for item in children:
        print(f"  - {item['name']} (id: {item['id']}, type: {item['mimeType']})")