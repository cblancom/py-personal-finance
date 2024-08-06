from database import Create_db

if __name__ == "__main__":
    db = Create_db()
    print("Tables:")
    for table in db.table:
        print(table)
