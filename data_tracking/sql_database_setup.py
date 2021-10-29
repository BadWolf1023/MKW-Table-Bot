'''
Created on Oct 28, 2021

@author: willg
'''
import sqlite3
import common
con = sqlite3.connect(common.DATA_TRACKING_DATABASE_FILE)
cur = con.cursor()
cur.executescript(common.read_file(common.DATA_TRACKING_DATABASE_CREATION_SQL))