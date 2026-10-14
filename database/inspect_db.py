import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "bot_database.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in c.fetchall() if not row[0].startswith("sqlite_")]

print(f"Database: {db_path} ({os.path.getsize(db_path):,} bytes)")
print(f"Total tables: {len(tables)}\n")

for t in tables:
    c.execute(f"SELECT COUNT(*) FROM {t}")
    cnt = c.fetchone()[0]
    print(f"  {t:30} : {cnt} rows")

c.execute("SELECT key, value FROM settings")
print("\nSettings:")
for k, v in c.fetchall():
    print(f"  {k:30} = {v}")
