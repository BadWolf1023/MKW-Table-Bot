'''
Created on Oct 28, 2021

@author: willg
'''
import sqlite3
import common

def create_room_tracking_database():
    con = sqlite3.connect(common.ROOM_DATA_TRACKING_DATABASE_FILE)
    try:
        cur = con.cursor()
        sql_setup_script = common.read_sql_file(common.ROOM_DATA_TRACKING_DATABASE_CREATION_SQL)
        print(sql_setup_script)
        cur.executescript(sql_setup_script)
    except:
        con.close()
        raise
    finally:
        con.close()
    