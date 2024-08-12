from models import CreateDB

if __name__ == "__main__":
    db = CreateDB()
    print("Tables:")
    for table in db.table:
        print(table)
