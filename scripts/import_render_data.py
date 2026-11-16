"""One-time import of the choir people into the Render PostgreSQL database.

Run with:
  python -m pip install "psycopg[binary]"
  $env:DATABASE_URL = "<Render External Database URL>"
  python scripts/import_render_data.py
"""
import json
import os
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]
children = json.loads((ROOT / "data/import/children.json").read_text(encoding="utf-8"))
servants = json.loads((ROOT / "data/import/servants.json").read_text(encoding="utf-8"))
database_url = os.environ.get("DATABASE_URL", "").strip()
if not database_url:
    raise SystemExit("DATABASE_URL is required")

with psycopg.connect(database_url) as connection:
    with connection.cursor() as cursor:
        for index, child in enumerate(children, start=1):
            note_parts = [
                f"المرحلة: {child.get('school_grade') or ''}",
                f"الأب: {child.get('father_job') or ''}",
                f"الأم: {child.get('mother_job') or ''}",
                f"الهوايات: {child.get('hobbies') or ''}",
                f"ملاحظات: {child.get('notes') or ''}",
            ]
            cursor.execute(
                """
                insert into people
                  (record_key, name, note, phone1, phone2, address, role, is_active)
                values (%s, %s, %s, %s, %s, %s, 'boy', true)
                on conflict (record_key) do update set
                  name=excluded.name, note=excluded.note, phone1=excluded.phone1,
                  phone2=excluded.phone2, address=excluded.address,
                  role='boy', is_active=true, updated_at=now()
                """,
                (index, child.get("name", "").strip(), "\n".join(note_parts),
                 child.get("father_phone") or "", child.get("mother_phone") or "",
                 child.get("address") or ""),
            )

        for index, servant in enumerate(servants, start=1):
            cursor.execute(
                """
                insert into people (record_key, name, role, is_active)
                values (%s, %s, 'servant', true)
                on conflict (record_key) do update set
                  name=excluded.name, role='servant', is_active=true, updated_at=now()
                """,
                (100000 + index, servant.get("name", "").strip()),
            )

print(f"Imported/updated {len(children)} boys and {len(servants)} servants.")
