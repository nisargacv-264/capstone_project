import sqlite3
from database.database import Database


# Make sure database and tables exist
db = Database()
db.close()


connection = sqlite3.connect("database/telemetry.db")
cursor = connection.cursor()


print("\n--- TABLES ---")

cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
""")

tables = cursor.fetchall()

for table in tables:
    print(table[0])


print("\n--- TELEMETRY TABLE ---")

cursor.execute("SELECT * FROM telemetry")

rows = cursor.fetchall()

if rows:
    for row in rows:
        print(row)
else:
    print("No telemetry data yet.")


print("\n--- ANOMALY EVENTS TABLE ---")

cursor.execute("SELECT * FROM anomaly_events")

events = cursor.fetchall()

if events:
    for event in events:
        print(event)
else:
    print("No anomaly events yet.")


connection.close()