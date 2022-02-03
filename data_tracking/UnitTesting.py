'''
Created on Oct 29, 2021

@author: willg
'''
import unittest
import Race
from data_tracking import DataTracker
from data_tracking.Data_Tracker_SQL_Query_Builder import *
import UtilityFunctions


class SQLInsertStatementTests(unittest.TestCase):
    def test_validate_players_data_1(self):
        pass

class SQLDataValidation_players(unittest.TestCase):
    """validate_player_data"""
    def test_validate_players_data_1(self):
        pass
    
class SQLDataValidation_races(unittest.TestCase):
    """validate_races_data"""
    def test_validate_races_data_1(self):
        pass



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
    
    def test_prepared_get_race_id_fcs(self):
        result = get_existing_race_fcs_in_Place_table({('r0000000', '0000-0000-0000'),
                                                      ('r0000000', '0000-0000-0001'),
                                                      ('r0000001', '0000-0000-0000'),
                                                      ('r0000001', '0000-0000-0001')})
        expected_result = """SELECT race_id, fc
FROM Place
WHERE (race_id = ? AND fc = ?)
OR (race_id = ? AND fc = ?)
OR (race_id = ? AND fc = ?)
OR (race_id = ? AND fc = ?);"""
        self.assertEqual(result, expected_result)

    def test_build_data_names(self):
        result = build_data_names(['1', '2', '3', '4'])
        self.assertEqual(result, """(1, 2, 3, 4)""", f"build_data_names did not produce expected result")
        
    def test_build_multiple_coniditional_operators(self):
        test_data = [ ("race_id", "fc"), ("=", "="), [(-1, -2), (2, 3)] ]
        result = build_multiple_coniditional_operators(*test_data)
        self.assertEqual(result, "(race_id = ? AND fc = ?)\nOR (race_id = ? AND fc = ?)")
    
    
    def test_build_multiple_coniditional_operators_2(self):
        test_data = [ ("race_id", "fc"), ("=", "="), [(-1, -2)] ]
        result = build_multiple_coniditional_operators(*test_data)
        self.assertEqual(result, "(race_id = ? AND fc = ?)")
   
class WiimmfiTimeValidation(unittest.TestCase):
    "is_wiimmfi_utc_time and get_wiimmfi_utc_time"
    def test_is_wiimmfi_utc_time_1(self):
        result = UtilityFunctions.is_wiimmfi_utc_time("2021-08-30 09:37UTC")
        self.assertTrue(result)
    
    def test_is_wiimmfi_utc_time_2(self):
        result = UtilityFunctions.is_wiimmfi_utc_time("2021-08-30 09:37")
        self.assertTrue(result)
    
    def test_is_wiimmfi_utc_time_3(self):
        result = UtilityFunctions.is_wiimmfi_utc_time("2021-08-30 09:3")
        self.assertFalse(result)
        
    def test_is_wiimmfi_utc_time_4(self):
        """February doesn't have 30 days"""
        result = UtilityFunctions.is_wiimmfi_utc_time("2029-30-02 22:30 UTC")
        self.assertFalse(result) #Because 
    
    def test_is_wiimmfi_utc_time_5(self):
        result = UtilityFunctions.is_wiimmfi_utc_time("2029-30-02 22:30 UT")
        self.assertFalse(result)
        
    def test_is_wiimmfi_utc_time_6(self):
        """Valid date, but wrong format"""
        result = UtilityFunctions.is_wiimmfi_utc_time("2021-08-3 09:37")
        self.assertFalse(result)
    
    def test_is_wiimmfi_utc_time_7(self):
        """Valid date, but wrong format"""
        result = UtilityFunctions.is_wiimmfi_utc_time("2021-8-30 09:37")
        self.assertFalse(result)
    
    def test_is_wiimmfi_utc_time_8(self):
        """Valid date, but wrong format"""
        result = UtilityFunctions.is_wiimmfi_utc_time("08-31-2021 09:37")
        self.assertFalse(result)
    
    def test_is_wiimmfi_utc_time_9(self):
        """Valid date, but wrong format"""
        result = UtilityFunctions.is_wiimmfi_utc_time("21-08-30 09:37")
        self.assertFalse(result)
        
    def test_is_wiimmfi_utc_time_10(self):
        """Valid date, but wrong format"""
        result = UtilityFunctions.is_wiimmfi_utc_time("2021-08-30 9:30")
        self.assertFalse(result)
    
    def test_is_wiimmfi_utc_time_11(self):
        """With space at end"""
        result = UtilityFunctions.is_wiimmfi_utc_time("2021-08-30 09:30 UTC ")
        self.assertTrue(result)
        
    def test_is_wiimmfi_utc_time_12(self):
        """Impossible time"""
        result = UtilityFunctions.is_wiimmfi_utc_time("2021-08-30 09:60 UTC ")
        self.assertFalse(result)
        
    def test_is_wiimmfi_utc_time_13(self):
        """Impossible time"""
        result = UtilityFunctions.is_wiimmfi_utc_time("2021-08-30 24:00 UTC ")
        self.assertFalse(result)
        
    
class SQLDataValidation_tracks(unittest.TestCase):
    '''Class to test data validation before inserting into database'''
    
    '''is_ct not correct type'''
    def test_validate_tracks_data_1(self):
        data_validator = DataTracker.ChannelBotSQLDataValidator()
        test_races = [Race.Race(None, None, 1, None, None, None, "Final Grounds", is_ct=None, track_url=None)]
        self.assertRaises(DataTracker.SQLTypeWrong, lambda:data_validator.validate_tracks_data(test_races))
    
    '''is_ct is correct type'''
    def test_validate_tracks_data_2(self):
        data_validator = DataTracker.ChannelBotSQLDataValidator()
        test_races = [Race.Race(None, None, 1, None, None, None, "Final Grounds", is_ct=True, track_url=None)]
        data_validator.validate_tracks_data(test_races)
        
    '''is_ct is correct type #2'''
    def test_validate_tracks_data_3(self):
        data_validator = DataTracker.ChannelBotSQLDataValidator()
        test_races = [Race.Race(None, None, 1, None, None, None, "Final Grounds", is_ct=False, track_url=None)]
        data_validator.validate_tracks_data(test_races)
    
    '''track_name cannot be blank (or None)'''
    def test_validate_tracks_data_4(self):
        data_validator = DataTracker.ChannelBotSQLDataValidator()
        test_races = [Race.Race(None, None, 1, None, None, None, None, is_ct=True, track_url=None)]
        self.assertRaises(DataTracker.SQLDataBad, lambda:data_validator.validate_tracks_data(test_races))
    
    '''track_name is correct type'''
    def test_validate_tracks_data_5(self):
        data_validator = DataTracker.ChannelBotSQLDataValidator()
        test_races = [Race.Race(None, None, 1, None, None, None, "Final Grounds", is_ct=True, track_url=None)]
        data_validator.validate_tracks_data(test_races)
        
    '''track_url is not correct type'''
    def test_validate_tracks_data_6(self):
        data_validator = DataTracker.ChannelBotSQLDataValidator()
        test_races = [Race.Race(None, None, 1, None, None, None, "Final Grounds", is_ct=True, track_url=10)]
        self.assertRaises(DataTracker.SQLTypeWrong, lambda:data_validator.validate_tracks_data(test_races))
        
    '''track_url is correct type'''
    def test_validate_tracks_data_7(self):
        data_validator = DataTracker.ChannelBotSQLDataValidator()
        test_races = [Race.Race(None, None, 1, None, None, None, "Final Grounds", is_ct=True, track_url="https://wiimmfi.de/test")]
        data_validator.validate_tracks_data(test_races)
    
    
if __name__ == '__main__':
    unittest.main()
    