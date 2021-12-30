'''Do not run this file unless you know what you are doing.

Make sure that the migrations are in the correct order in the list.
'''


import sqlite3

db_connection:sqlite3.Connection = None
database_name = "./tablebot_data/room_data_tracking.db"
migration_files = [""]



dec_29_2021_migration_database_name = "./tablebot_data/room_data_tracking.db"
dec_29_2021_migration_files = ["./data_tracking/migrations/12_29_2021/new_table_migrations.sql",
                            "./data_tracking/migrations/database_cascade_delete_prep.sql",
                            "./data_tracking/migrations/12_29_2021/remove_corrupted_events.sql",
                            "./data_tracking/migrations/database_restrict_delete_prep.sql",
                            "./data_tracking/migrations/12_29_2021/time_migration.sql",
                            "./data_tracking/migrations/12_29_2021/race_migration.sql",
                            "./data_tracking/migrations/12_29_2021/event_migration.sql"]




def read_sql_file(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        return f.read()

def start_database():
    global db_connection
    db_connection = sqlite3.connect(database_name, isolation_level=None)

def close_database():
    db_connection.close()

def main():
    print("Opening database...")
    start_database()
    print("Database opened.")
    try:
        for file_name in migration_files:
            maintenance_script = read_sql_file(file_name)
            print(f"- Running: {file_name}")
            db_connection.executescript(maintenance_script)
            print(f"- Completed: {file_name}")
    except Exception as e:
        print(e)
    finally:
        print("Closing database...")
        close_database()
        print("Database closed.")

if __name__ == "__main__":
    main()
    print("Exiting...")
