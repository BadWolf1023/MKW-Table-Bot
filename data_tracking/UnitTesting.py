'''
Created on Oct 29, 2021

@author: willg
'''
import unittest
from data_tracking.Data_Tracker_SQL_Query_Builder import *

class TestPlayerSQLStatements(unittest.TestCase):
    def test_prepared_fcs(self):
        result = get_fcs_in_Player_table([1, 2, 3])
        self.assertEqual(result, """SELECT fc
FROM Player
WHERE fc in (?, ?, ?);""", f"get_fcs_in_Player_table did not produce expected result")
        
if __name__ == '__main__':
    unittest.main()
    