from database.database import Database


db = Database()

print("Database initialized successfully.")
print("Database location:")
print(db.db_path)

db.close()