from codecs import ignore_errors
from dataclasses import dataclass
import shutil
import sqlite3, os
from sqlite3 import Error

def create_connection(db_file):
    conn = None
    try:        
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
        
    except Error as e:
        print(e)
    
    return conn

def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def close_connection(db_file):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.close()

def main():
    database = get_db_path()
    print("database",database)
    sql_create_vehicles_table = """
                                    CREATE TABLE IF NOT EXISTS vehicle (
                                        license varchar PRIMARy KEY,
                                        device_id varchar
                                    );                                
                                """
    
    sql_create_trips_table = """
                                CREATE TABLE IF NOT EXISTS trips (
                                    id varchar PRIMARy KEY,
                                    device_id varchar,
                                    start_time DATETIME,
                                    stop_time  DATETIME,
                                    distance integer
                                );                                
                            """
    sql_create_driving_exceptions_table =  """
                                                CREATE TABLE IF NOT EXISTS driving_exception (
                                                    id varchar PRIMARy KEY,
                                                    device_id varchar,
                                                    active_from DATETIME,
                                                    active_to  DATETIME,
                                                    rule_id VARCHAR
                                                );                                
                                            """
    conn = create_connection(database)     
    if conn is not None:
        print("Connection Established")
        create_table(conn, sql_create_vehicles_table)
        create_table(conn, sql_create_trips_table)
        create_table(conn, sql_create_driving_exceptions_table)
    else:
        print("Error establishing database connection!!!")


def get_db_path():
    sqlpath = os.path.join("db", "moove_challenge.db")    
    return sqlpath


if __name__ == '__main__':    
    if os.path.isdir("db"):
        shutil.rmtree("db", ignore_errors=False, onerror=None)
    os.mkdir("db")
    main()
    close_connection(get_db_path())
    