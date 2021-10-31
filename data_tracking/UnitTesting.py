'''
Created on Oct 29, 2021

@author: willg
'''
import unittest
import Race
from data_tracking import DataTracker
from data_tracking.Data_Tracker_SQL_Query_Builder import *

class PlayerSQLStatementTests(unittest.TestCase):
    def test_prepared_get_fcs(self):
        result = get_fcs_in_Player_table([1, 2, 3])
        self.assertEqual(result, """SELECT fc
FROM Player
WHERE fc in (?, ?, ?);""", f"get_fcs_in_Player_table did not produce expected result")
    
    def test_prepared_get_track_names(self):
        result = get_existing_tracks_in_Track_table(["hi", "hello"])
        self.assertEqual(result, """SELECT track_name
FROM Track
WHERE track_name in (?, ?);""", f"get_existing_tracks_in_Track_table did not produce expected result")
        
    def test_prepared_get_race_ids(self):
        result = get_existing_race_ids_in_Race_table([1, 2, 3, 4])
        self.assertEqual(result, """SELECT race_id
FROM Race
WHERE race_id in (?, ?, ?, ?);""", f"get_existing_race_ids_in_Race_table did not produce expected result")
    
    
    def test_build_data_names(self):
        result = build_data_names(['1', '2', '3', '4'])
        self.assertEqual(result, """(1, 2, 3, 4)""", f"build_data_names did not produce expected result")
    
class SQLInsertStatementTests(unittest.TestCase):
    pass

class SQLDataValidation_players(unittest.TestCase):
    """validate_player_data"""
    def test_validate_players_data_1(self):
        raise NotImplemented()
    
class SQLDataValidation_races(unittest.TestCase):
    """validate_races_data"""
    def test_validate_races_data_1(self):
        raise NotImplemented()
    
class SQLDataValidation_tracks(unittest.TestCase):
    '''Class to test data validation before inserting into database'''
    
    '''is_ct not correct type'''
    def test_validate_tracks_data_1(self):
        data_tracker = DataTracker.RoomTrackerSQL(None)
        test_races = [Race.Race(None, None, 1, None, None, None, "Final Grounds", is_ct=None, trackURL=None)]
        self.assertRaises(DataTracker.SQLTypeWrong, lambda:data_tracker.validate_tracks_data(test_races))
    
    '''is_ct is correct type'''
    def test_validate_tracks_data_2(self):
        data_tracker = DataTracker.RoomTrackerSQL(None)
        test_races = [Race.Race(None, None, 1, None, None, None, "Final Grounds", is_ct=True, trackURL=None)]
        data_tracker.validate_tracks_data(test_races)
        
    '''is_ct is correct type #2'''
    def test_validate_tracks_data_3(self):
        data_tracker = DataTracker.RoomTrackerSQL(None)
        test_races = [Race.Race(None, None, 1, None, None, None, "Final Grounds", is_ct=False, trackURL=None)]
        data_tracker.validate_tracks_data(test_races)
    
    '''track_name cannot be blank (or None)'''
    def test_validate_tracks_data_4(self):
        data_tracker = DataTracker.RoomTrackerSQL(None)
        test_races = [Race.Race(None, None, 1, None, None, None, None, is_ct=True, trackURL=None)]
        self.assertRaises(DataTracker.SQLDataBad, lambda:data_tracker.validate_tracks_data(test_races))
    
    '''track_name is correct type'''
    def test_validate_tracks_data_5(self):
        data_tracker = DataTracker.RoomTrackerSQL(None)
        test_races = [Race.Race(None, None, 1, None, None, None, "Final Grounds", is_ct=True, trackURL=None)]
        data_tracker.validate_tracks_data(test_races)
        
    '''track_url is not correct type'''
    def test_validate_tracks_data_6(self):
        data_tracker = DataTracker.RoomTrackerSQL(None)
        test_races = [Race.Race(None, None, 1, None, None, None, "Final Grounds", is_ct=True, trackURL=10)]
        self.assertRaises(DataTracker.SQLTypeWrong, lambda:data_tracker.validate_tracks_data(test_races))
        
    '''track_url is correct type'''
    def test_validate_tracks_data_7(self):
        data_tracker = DataTracker.RoomTrackerSQL(None)
        test_races = [Race.Race(None, None, 1, None, None, None, "Final Grounds", is_ct=True, trackURL="https://wiimmfi.de/test")]
        data_tracker.validate_tracks_data(test_races)
    
        
if __name__ == '__main__':
    unittest.main()
    