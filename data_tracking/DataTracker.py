'''
Created on Oct 21, 2021

@author: willg

This module helps track and store data from Wiimmfi.

'''
import asyncio
import json
import os
import time
import traceback
from collections import defaultdict
from copy import deepcopy
from itertools import chain
from typing import List, Dict, Tuple, Set

import aiosqlite

import Placement
import Player
import Race
import UserDataProcessing
import UtilityFunctions
import common
from data_tracking import Data_Tracker_SQL_Query_Builder as QB
import TimerDebuggers

DEBUGGING_DATA_TRACKER = False
DEBUGGING_SQL = False

db_connection:aiosqlite.Connection = None

class SQLDataBad(Exception):
    pass
class SQLTypeWrong(SQLDataBad):
    pass
class SQLFormatWrong(SQLDataBad):
    pass

# aiosqlite.Cursor is a async generator (not a regular generator) so list(cursor) does not work
class ConnectionWrapper():
    def __init__(self, connection):
        self.con: aiosqlite.Connection = connection

    async def execute(self, *args):
        cursor = await self.con.execute(*args)
        return await cursor.fetchall()

    async def executemany(self, *args):
        cursor = await self.con.executemany(*args)
        return await cursor.fetchall()

    async def executescript(self, *args):
        cursor = await self.con.executescript(*args)
        return await cursor.fetchall()

    def __getattr__(self, attr):
        return self.con.__getattribute__(attr)

class DataRetriever(object):
    #TODO: Finish method
    @staticmethod
    async def get_tracks_played_count(is_ct=False, tier=None, in_last_days=None):
        tracks_query = QB.SQL_Search_Query_Builder.get_tracks_played_query(is_ct, tier, in_last_days)
        return await db_connection.execute(tracks_query)

    @staticmethod
    async def get_best_tracks(fcs, is_ct=False, tier=None, in_last_days=None, sort_asc=False, min_count = 1):
        tracks_query = QB.SQL_Search_Query_Builder.get_best_tracks(fcs, is_ct, tier, in_last_days, min_count)
        result = await db_connection.execute(tracks_query)
        if sort_asc:
            return list(reversed(result))
        return result

    @staticmethod
    async def get_top_players(track, tier=None, in_last_days=None, min_count=1):
        #await db_connection.execute("WITH RECURSIVE cnt(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM cnt lIMIT 20000000) SELECT avg(x) FROM cnt;")
        tracks_query = QB.SQL_Search_Query_Builder.get_top_players_query(tier, in_last_days, min_count)
        return await db_connection.execute(tracks_query, [track])

    @staticmethod
    async def get_record(player_did, opponent_did, days):
        record_query = QB.SQL_Search_Query_Builder.get_record_query(player_did, opponent_did, days)
        return await db_connection.execute(record_query)

    @staticmethod
    async def get_track_list():
        return await db_connection.execute("SELECT track_name, url, fixed_track_name, is_ct, track_name_lookup "
                                           "FROM Track")

class ChannelBotSQLDataValidator(object):
    def wrong_type_message(self, data, expected_type, multi=False):
        if multi:
            return f"{data} of type {type(data)} is not any of the expected types: ({', '.join([(t.__name__ if t is not None else 'None') for t in expected_type])})"
        else:
            return f"{data} of type {type(data)} is not expected type: {expected_type.__name__}"
    
    def validate_type(self, data, expected_type, can_be_none):
        if can_be_none:
            if not isinstance(data, (expected_type, type(None))):
                raise SQLTypeWrong(self.wrong_type_message(data, (expected_type, None), multi=True))
        else:
            if not isinstance(data, expected_type):
                raise SQLTypeWrong(self.wrong_type_message(data, expected_type))
    
    def validate_int(self, data, can_be_none=False):
        self.validate_type(data, int, can_be_none)
        
    def validate_str(self, data, can_be_none=False):
        self.validate_type(data, str, can_be_none)
    
    def validate_float(self, data, can_be_none=False):
        self.validate_type(data, float, can_be_none)
    
    def validate_bool(self, data, can_be_none=False):
        self.validate_type(data, bool, can_be_none)
        
    def is_from_wiimmfi_validation(self, is_from_wiimmfi):
        self.validate_bool(is_from_wiimmfi)
        
    def event_id_validation(self, event_id):
        self.validate_int(event_id)
        if event_id < 1:
            raise SQLFormatWrong(f"{event_id} is not a formatted like an event id, which should be a number")
    
    def channel_id_validation(self, channel_id):
        self.validate_int(channel_id)
        if channel_id < 1:
            raise SQLFormatWrong(f"{channel_id} is not a formatted like an channel id, which should be a number")
    
    def discord_id_validation(self, discord_id):
        self.validate_int(discord_id)
        if discord_id < 1:
            raise SQLFormatWrong(f"{discord_id} is not a formatted like a discord id, which should be a number")
        
    def placement_time_validation(self, time_str):
        self.validate_str(time_str)
        if not Placement.is_valid_time_str(time_str):
            raise SQLFormatWrong(f"{time_str} is not formatted like a valid finishing time")
        
    def placement_delta_validation(self, delta):
        self.validate_float(delta, can_be_none=True)
        
    def player_ol_status_validation(self, ol_status):
        self.validate_str(ol_status, can_be_none=True)
        
    def player_position_validation(self, player_pos):
        self.validate_int(player_pos)
        if player_pos < 1 and player_pos != -1:
            raise SQLFormatWrong(f"{player_pos} is not a valid player position")
        
    def player_finish_place_validation(self, place):
        self.validate_int(place)
        if place < 1:
            raise SQLFormatWrong(f"{place} is not a valid finishing place")
    
    def fc_validation(self, fc):
        self.validate_str(fc)
        if not UtilityFunctions.is_fc(fc):
            raise SQLFormatWrong(f"{fc} is not a formatted like an FC")
    
    def race_id_validation(self, race_id):
        self.validate_str(race_id)
        if not UtilityFunctions.is_race_ID(race_id):
            raise SQLFormatWrong(f"{race_id} is not a formatted like a race ID")
        
    def mii_hex_validation(self, mii_hex):
        self.validate_str(mii_hex, can_be_none=True)
        if isinstance(mii_hex, str):
            if not UtilityFunctions.is_hex(mii_hex):
                raise SQLFormatWrong(f"{mii_hex} is not a valid mii hex")
            
    def player_id_validation(self, player_id):
        self.validate_int(player_id)
        
    def player_mkwx_url_validation(self, mkwx_url):
        self.validate_str(mkwx_url)
    
    def validate_player_data(self, players:List[Player.Player]):
        '''Validates that all the data in players is the correct type and format before going into the database'''
        for player in players:
            self.fc_validation(player.get_FC())
            self.player_id_validation(player.get_player_id())
            self.player_mkwx_url_validation(player.get_mkwx_url())
            
    def track_name_validation(self, track_name, rxx=None):
        self.validate_str(track_name)
        if track_name == "None":
            raise SQLDataBad(f"track_name cannot be an 'None', room rxx: {rxx}")
    
    def track_url_validation(self, track_url):
        self.validate_str(track_url, can_be_none=True)
        
    def track_name_no_author_validation(self, track_name_author_stripped, rxx=None):
        self.validate_str(track_name_author_stripped)
        if track_name_author_stripped == "None":
            raise SQLDataBad(f"track_name without author cannot be an 'None', room rxx: {rxx}")
        
    def track_lookup_name_validation(self, track_lookup_name, rxx=None):
        self.validate_str(track_lookup_name)
        if track_lookup_name == "None" or ' ' in track_lookup_name:
            raise SQLDataBad(f"{track_lookup_name} is not a valid track lookup name, room rxx: {rxx}")
        
    def track_is_ct_validation(self, is_ct):
        self.validate_bool(is_ct)
        
    def validate_tracks_data(self, races:List[Race.Race]):
        '''Validates that all the relevant data (regarding track information) in races is the correct type and format before going into the database'''
        for race in races:
            self.track_name_validation(race.get_track_name(), rxx=race.rxx)
            self.track_url_validation(race.get_track_url())
            no_author_name = race.getTrackNameWithoutAuthor()
            self.track_name_no_author_validation(no_author_name, rxx=race.rxx)
            self.track_is_ct_validation(race.is_custom_track())
            self.track_lookup_name_validation(Race.get_track_name_lookup(no_author_name), rxx=race.rxx)   
    
    def rxx_validation(self, rxx):
        self.validate_str(rxx)
        if not UtilityFunctions.is_rLID(rxx):
            raise SQLFormatWrong(f"{rxx} is not a formatted like an rxx")
        
    def wiimmfi_utc_time_validation(self, wiimmfi_time):
        self.validate_str(wiimmfi_time)
        if not UtilityFunctions.is_wiimmfi_utc_time(wiimmfi_time):
            raise SQLFormatWrong(f"{wiimmfi_time} is not a formatted like the expected Wiimmfi time")
        
    def race_number_validation(self, race_number):
        self.validate_int(race_number)
        if race_number < 1:
            raise SQLDataBad(f"{race_number} race number must be greater than 0")
        
    def race_room_name_validation(self, room_name):
        self.validate_str(room_name)
    
    def race_room_type_validation(self, room_type):
        self.validate_str(room_type)
    
    def race_cc_validation(self, cc):
        self.validate_str(cc)
        
    def region_validation(self, region):
        self.validate_str(region)
        if not Race.is_valid_region(region):
            raise SQLFormatWrong(f"{region} region is not a valid region (see Race.is_valid_region)")
    
    def connection_fails_validation(self, conn_fails):
        self.validate_float(conn_fails, can_be_none=True)
        
    def player_role_validation(self, player_role):
        self.validate_str(player_role)
        
    def player_vr_validation(self, vr):
        self.validate_int(vr, can_be_none=True)
        if isinstance(vr, int):
            if vr < 0:
                raise SQLFormatWrong(f"{vr} VR cannot be less than 0")
    
    def player_character_validation(self, character):
        self.validate_str(character, can_be_none=True)
        if isinstance(character, str):
            if character.strip() == "":
                raise SQLFormatWrong(f"{character} character for player cannot be an empty string")
    
    def player_vehicle_validation(self, vehicle):
        self.validate_str(vehicle, can_be_none=True)
        if isinstance(vehicle, str):
            if vehicle.strip() == "":
                raise SQLFormatWrong(f"{vehicle} vehicle for player cannot be an empty string")
            
    def name_validation(self, name):
        self.validate_str(name, can_be_none=True)
        if isinstance(name, str):
            if name.strip() == "":
                raise SQLFormatWrong(f"{name} name player cannot be an empty string")
        
    def validate_races_data(self, races:List[Race.Race]):
        '''Validates that all the data in races is the correct type and format before going into the database'''
        for race in races:
            race:Race.Race
            self.race_id_validation(race.get_race_id())
            self.rxx_validation(race.get_rxx())
            self.wiimmfi_utc_time_validation(race.get_match_start_time())
            self.race_number_validation(race.get_race_number())
            self.race_room_name_validation(race.get_room_name())
            self.race_room_type_validation(race.get_room_type())
            self.race_cc_validation(race.get_cc())
            self.region_validation(race.get_region())            
            self.is_from_wiimmfi_validation(race.is_from_wiimmfi())
            
        self.validate_tracks_data(races)
            
    def validate_placement_data(self, placements:Dict[Tuple,Placement.Placement]):
        for (race_id, fc), placement in placements.items():
            self.race_id_validation(race_id)
            self.fc_validation(fc)
            player = placement.getPlayer()
            self.fc_validation(player.get_FC())
            self.player_finish_place_validation(placement.get_place())
            self.placement_time_validation(placement.get_time_string())
            self.placement_delta_validation(placement.get_delta())
            self.player_ol_status_validation(player.get_ol_status())
            self.player_position_validation(player.get_position())
            self.region_validation(player.get_region())
            self.connection_fails_validation(player.get_connection_fails())
            self.player_role_validation(player.get_role())
            self.player_vr_validation(player.get_VR())
            self.player_character_validation(player.get_character())
            self.player_vehicle_validation(player.get_vehicle())
            self.name_validation(player.get_discord_name())
            self.name_validation(player.get_lounge_name())
            self.mii_hex_validation(player.get_mii_hex())
            self.is_from_wiimmfi_validation(placement.is_from_wiimmfi())
                
            
        
    
    def validate_event_id_race_ids(self, event_id_race_ids:Set[Tuple]):
        for event_id, race_id in event_id_race_ids:
            self.event_id_validation(event_id)
            self.race_id_validation(race_id)
            
    def validate_placement_mii_hex_update(self, race_id_fc_placements:Dict[Tuple, Placement.Placement]):
        for (race_id, fc), placement in race_id_fc_placements.items():
            self.race_id_validation(race_id)
            self.fc_validation(fc)
            self.mii_hex_validation(placement.getPlayer().get_mii_hex())
            
    def validate_event_mii_hex_update(self, event_id_fc_miis:Set[Tuple]):
        for (event_id, fc, mii_hex) in event_id_fc_miis:
            self.event_id_validation(event_id)
            self.fc_validation(fc)
            self.mii_hex_validation(mii_hex)
            
    
            
    def validate_event_data(self, channel_bot):
        self.event_id_validation(channel_bot.room.get_event_id())
        self.channel_id_validation(channel_bot.get_channel_id())
        self.discord_id_validation(channel_bot.getRoom().get_set_up_user_discord_id())
        if not isinstance(channel_bot.getRoom().get_known_region(), str):
            raise SQLTypeWrong(self.wrong_type_message(channel_bot.getRoom().get_known_region(), str))
        if not isinstance(channel_bot.getRoom().get_set_up_display_name(), str):
            raise SQLTypeWrong(self.wrong_type_message(channel_bot.getRoom().get_set_up_display_name(), str))
        self.validate_int(channel_bot.getWar().get_num_players())
            
    
    def validate_event_fc_data(self, event_id_fcs):
        for event_id, fc, _ in event_id_fcs:
            self.event_id_validation(event_id)
            self.fc_validation(fc)
            
    def validate_event_structure_data(self, event_structure_tuple):
        #Warning: this was apparently never completed
        #TODO: complete validation of event_structure data
        pass

class RoomTrackerSQL(object):
    def __init__(self, channel_bot):
        self.channel_bot = channel_bot
        self.data_validator = ChannelBotSQLDataValidator()
            
    
    def get_race_as_sql_tuple(self, race:Race.Race):
        '''Converts a given table bot race into a tuple that is ready to be inserted into the Race SQL table'''
        times = [x.get_time_seconds() for x in race.getPlacements() if not (x.is_bogus_time() or x.is_disconnected())]
        if len(times) == 0:
            times = [-1]
        return (race.get_race_id(),
                race.get_rxx(),
                UtilityFunctions.get_wiimmfi_utc_time(race.get_match_start_time()),
                race.get_race_number(),
                race.get_room_name(),
                race.get_track_name(),
                race.get_room_type(),
                race.get_cc(),
                race.get_region(),
                race.is_from_wiimmfi(),
                race.numRacers(),
                min(times),
                max(times),
                sum(times)/len(times)
                )
    
    def get_race_as_sql_track_tuple(self, race):
        '''Converts a given table bot race into a tuple that is ready to be inserted into the Track SQL table'''
        no_author_name = race.getTrackNameWithoutAuthor()
        return (race.get_track_name(),
                race.get_track_url(),
                no_author_name,
                race.is_custom_track(),
                Race.get_track_name_lookup(no_author_name)
                )
    
    def get_player_as_sql_player_tuple(self, player):
        '''Converts a given table bot player into a tuple that is ready to be inserted into the Player SQL table'''
        return (player.get_FC(),
                int(player.get_player_id()),
                player.get_mkwx_url())
        
    def get_placement_as_sql_place_tuple(self, race_id, placement:Placement.Placement):
        '''Converts a given table bot Placement into a tuple that is ready to be inserted into the Place SQL table'''
        player:Placement.Player.Player = placement.getPlayer()
        return (race_id,
                player.get_FC(),
                player.get_name(),
                placement.get_place(),
                placement.get_time_seconds(),
                placement.get_delta(),
                player.get_ol_status(),
                player.get_position(),
                player.get_region(),
                player.get_connection_fails(),
                player.get_role(),
                player.get_VR(),
                player.get_character(),
                player.get_vehicle(),
                player.get_discord_name(),
                player.get_lounge_name(),
                player.get_mii_hex(),
                placement.is_from_wiimmfi())
    
    
        
    async def insert_missing_placements_into_database(self):
        '''Inserts placements in self.channel_bot's races are not yet in the database's Place table.
        May raise SQLDataBad, SQLTypeWrong, SQLFormatWrong
        Returns a list of the inserted placements (as 2-tuples: race_id, fc) upon success. (An empty list is returned if no placements were inserted.)'''
        
        race_id_fc_placements = {(race.get_race_id(), placement.getPlayer().get_FC()):placement for race in self.channel_bot.getRoom().races for placement in race.getPlacements()}
        if len(race_id_fc_placements) == 0:
            return []
        
        self.data_validator.validate_placement_data(race_id_fc_placements)
        all_data = [self.get_placement_as_sql_place_tuple(race_id, p) for (race_id, _), p in race_id_fc_placements.items()]
        insert_ignore_script = QB.build_insert_missing_placement_script(all_data)
        values_args = list(chain.from_iterable(all_data))
        
        return await db_connection.execute(insert_ignore_script, values_args)
    
    async def insert_missing_players_into_database(self):
        '''Inserts players in all of the races in self.channel_bot.races that are not yet in the database's Player table.
        May raise SQLDataBad, SQLTypeWrong, SQLFormatWrong
        Returns a list of the inserted player's fcs (as 1-tuples) upon success. (An empty list is returned if no players were inserted.)'''
        unique_room_players = [placement.getPlayer() for placement in self.channel_bot.getRoom().getFCPlacements().values()]
        if len(unique_room_players) == 0:
            return []
        
        self.data_validator.validate_player_data(unique_room_players)
            
        all_data = [self.get_player_as_sql_player_tuple(p) for p in unique_room_players]
        insert_ignore_script = QB.build_insert_missing_players_script(all_data)
        values_args = list(chain.from_iterable(all_data))
        return await db_connection.execute(insert_ignore_script, values_args)
    
    async def insert_missing_races_into_database(self):
        '''Inserts races in self.channel_bot.races are not yet in the database's Race table.
        May raise SQLDataBad, SQLTypeWrong, SQLFormatWrong
        Returns a list of the inserted race's race_id's (as 1-tuples) upon success. (An empty list is returned if no races were inserted.)'''
        unique_races = {race.get_race_id():race for race in self.channel_bot.getRoom().races}.values()
        if len(unique_races) == 0:
            return []
        
        self.data_validator.validate_races_data(unique_races)
        all_data = [self.get_race_as_sql_tuple(r) for r in unique_races]
        insert_ignore_script = QB.build_insert_missing_races_script(all_data)
        values_args = list(chain.from_iterable(all_data))
        return await db_connection.execute(insert_ignore_script, values_args)
    
    async def insert_missing_tracks_into_database(self):
        '''Inserts tracks in self.channel_bot's races are not yet in the database's Track table.
        May raise SQLDataBad, SQLTypeWrong, SQLFormatWrong
        Returns the a list of the inserted track names (as 1-tuples) upon success. (An empty list is returned if no tracks were inserted.)'''
        races_unique_track_names = {race.get_track_name():race for race in self.channel_bot.getRoom().races}.values()
        if len(races_unique_track_names) == 0:
            return []
        
        self.data_validator.validate_tracks_data(races_unique_track_names)
        all_data = [self.get_race_as_sql_track_tuple(r) for r in races_unique_track_names]
        insert_ignore_script = QB.build_insert_missing_tracks_script(all_data)
        values_args = list(chain.from_iterable(all_data))
        
        return await db_connection.execute(insert_ignore_script, values_args)
    
    async def get_matching_placements_with_missing_hex(self, update_mii_args):
        '''Given a list of 3-tuples (where the tuple is (race_id, fc, _)), returns existing a list of (race_id, fcs) tuples in Place table whose mii_hex is null.
        May raise SQLDataBad, SQLTypeWrong, SQLFormatWrong'''
        missing_mii_data = [(data[0], data[1], None) for data in update_mii_args]
        if len(missing_mii_data) == 0:
            return []
        missing_mii_hexes_statement = QB.get_existing_race_fcs_in_Place_table_with_null_mii_hex(missing_mii_data)
        values_args = list(chain.from_iterable(missing_mii_data))
        return await db_connection.execute(missing_mii_hexes_statement, values_args)
    
    async def get_matching_event_fcs_with_missing_hex(self, update_mii_args):
        '''Given a list of 3-tuples (where the tuple is (event_id, fc, _)), returns existing a list of (event_id, fcs) tuples in Event_FCs table whose mii_hex is null.
        May raise SQLDataBad, SQLTypeWrong, SQLFormatWrong'''
        missing_mii_data = [(data[0], data[1], None) for data in update_mii_args]
        if len(missing_mii_data) == 0:
            return []
        missing_mii_hexes_statement = QB.get_existing_event_fcs_in_with_null_mii_hex(missing_mii_data)
        values_args = list(chain.from_iterable(missing_mii_data))
        return await db_connection.execute(missing_mii_hexes_statement, values_args)
        
    async def update_database_place_miis(self):
        '''Updates the mii_hex for placements in Place table for placements in self.channel_bot.race's placements who have a mii_hex if that mii_hex in the Place table is null.
        May raise SQLDataBad, SQLTypeWrong, SQLFormatWrong
        Returns the a list of the race_id, fc (as 2-tuples) of the placements whose mii_hex's were updated. (An empty list is returned if nothing was updated.)'''
        have_miis_for_placements = {(race.get_race_id(), placement.getPlayer().get_FC()):placement for race in self.channel_bot.getRoom().races for placement in race.getPlacements() if placement.getPlayer().get_mii_hex() is not None}
        if len(have_miis_for_placements) == 0:
            return []
        
        self.data_validator.validate_placement_mii_hex_update(have_miis_for_placements)
        
        update_mii_script = QB.update_mii_hex_script()
        update_mii_args = [(placement.getPlayer().get_mii_hex(), race_id, fc) for (race_id, fc), placement in have_miis_for_placements.items()]
        
        found_race_id_fcs_with_null_miis = await self.get_matching_placements_with_missing_hex(update_mii_args)

        await db_connection.executemany(update_mii_script, update_mii_args)
        return found_race_id_fcs_with_null_miis
    
    
    async def insert_missing_event_ids_race_ids(self):
        '''Inserts (event_id, race_id) in for each race in self.channel_bot's races that are not yet in the database's Event_Races table.
        May raise SQLDataBad, SQLTypeWrong, SQLFormatWrong
        Returns the a list of the inserted event_ids, race_ids (as 2-tuples) upon success. (An empty list is returned if nothing was inserted.)'''
        event_id_race_ids = {(self.channel_bot.room.get_event_id(), race.get_race_id()) for race in self.channel_bot.getRoom().races} #Note this is a set of tuples, not a dict
        if len(event_id_race_ids) < 1:
            return []
        self.data_validator.validate_event_id_race_ids(event_id_race_ids)
        
        insert_ignore_script = QB.build_missing_event_ids_race_ids_script(event_id_race_ids)
        values_args = list(chain.from_iterable((event_id, race_id) for event_id, race_id in event_id_race_ids))
        return await db_connection.execute(insert_ignore_script, values_args)

    def get_event_as_upsert_sql_place_tuple(self, channel_bot):
        '''Converts a given table bot a tuple that is ready to be inserted into the Event SQL table'''
        return (channel_bot.room.get_event_id(),
                channel_bot.get_channel_id(),
                0,
                channel_bot.getRoom().get_known_region(),
                channel_bot.getRoom().get_set_up_user_discord_id(),
                channel_bot.getRoom().get_set_up_display_name(),
                channel_bot.getWar().get_num_players()
                )
        
    async def insert_missing_event(self, was_real_update=False):
        self.data_validator.validate_event_data(self.channel_bot)
        event_sql_args = [*self.get_event_as_upsert_sql_place_tuple(self.channel_bot)]
        if len(event_sql_args) < 1:
            return []
        
        upsert_script = QB.build_event_upsert_script(was_real_update)

        added_updated_event_ids = await db_connection.execute(upsert_script, event_sql_args)
        if was_real_update:
            return added_updated_event_ids
        return []
    
    
    async def add_event_id(self):
        '''Inserts event_id for self.channel_bot int Event_ID table.
        May raise SQLDataBad, SQLTypeWrong, SQLFormatWrong
        Returns a list of the inserted event_id (as a 1-tuple) upon success. (An empty list is returned if nothing was inserted.)'''
        self.data_validator.event_id_validation(self.channel_bot.room.get_event_id())
        event_sql_args = [(self.channel_bot.room.get_event_id(),)]
        if len(event_sql_args) < 1:
            return []
        
        upsert_script = QB.build_missing_event_id_table_script(event_sql_args)
        return await db_connection.execute(upsert_script, event_sql_args[0])
    
    async def insert_missing_event_fcs_and_miis(self):
        '''Inserts event_id, fcs in self.channel_bot's races are not yet in the database's Event_FCS table.
        May raise SQLDataBad, SQLTypeWrong, SQLFormatWrong
        Returns a list of the inserted placements (as 2-tuples: race_id, fc) upon success. (An empty list is returned if no placements were inserted.)'''
        event_id_fcs = list({(self.channel_bot.room.get_event_id(), fc, None) for fc in self.channel_bot.getRoom().getFCs()})
        if len(event_id_fcs) == 0:
            return []
        
        self.data_validator.validate_event_fc_data(event_id_fcs)
        insert_ignore_script = QB.build_missing_event_fcs_table_script(event_id_fcs)
        values_args = list(chain.from_iterable(event_id_fcs))
        return await db_connection.execute(insert_ignore_script, values_args)
    
    async def update_missing_miis_in_event_fcs(self):
        '''Updates the mii_hex for fcs for the event in Event_FCs table if the mii is null in Event_FCs and if we have a non-null mii
        May raise SQLDataBad, SQLTypeWrong, SQLFormatWrong
        Returns the a list of the event_id, fc (as 2-tuples) of the fcs in the event whose mii_hex's were updated. (An empty list is returned if nothing was updated.)'''
        have_miis_for_event = list({(self.channel_bot.room.get_event_id(), fc, mii.mii_data_hex_str) for fc, mii in self.channel_bot.room.get_miis().items()})
        if len(have_miis_for_event) == 0:
            return []
        
        self.data_validator.validate_event_mii_hex_update(have_miis_for_event)
        
        update_mii_script = QB.update_mii_hex_script_event_fcs()
        update_mii_args = [(mii_hex, event_id, fc) for (event_id, fc, mii_hex) in have_miis_for_event]

        found_event_id_fcs_with_null_miis = await self.get_matching_event_fcs_with_missing_hex(have_miis_for_event)
        await db_connection.executemany(update_mii_script, update_mii_args)
        return found_event_id_fcs_with_null_miis
    
    def get_event_structure_tuple(self):
        return (self.channel_bot.room.get_event_id(),
                json.dumps(self.channel_bot.getRoom().getNameChanges()),
                json.dumps(self.channel_bot.getRoom().getRemovedRaces()),
                json.dumps(self.channel_bot.getRoom().getPlacementHistory()),
                json.dumps(self.channel_bot.getRoom().getForcedRoomSize()),
                json.dumps(self.channel_bot.getRoom().getPlayerPenalties()),
                json.dumps(self.channel_bot.getWar().getTeamPenalities()),
                # json.dumps(self.channel_bot.getRoom().get_manual_dc_placements()),
                json.dumps(self.channel_bot.getRoom().get_dc_statuses()),
                json.dumps(self.channel_bot.getRoom().get_subs()),
                json.dumps(self.channel_bot.getWar().get_teams()),
                json.dumps(self.channel_bot.getRoom().get_rxxs()),
                json.dumps(self.channel_bot.getWar().get_player_edits()),
                self.channel_bot.getWar().should_ignore_large_times(),
                self.channel_bot.getWar().get_missing_player_points(),
                self.channel_bot.getWar().get_manually_set_war_name(),
                self.channel_bot.getWar().get_number_of_gps(),
                self.channel_bot.getWar().get_num_players(),
                self.channel_bot.getWar().get_number_of_teams(),
                self.channel_bot.getWar().get_players_per_team())
        
    async def dump_event_structure_data(self):
        event_structure_tuple = self.get_event_structure_tuple()
        if len(event_structure_tuple) == 0:
            return []
        
        self.data_validator.validate_event_structure_data(event_structure_tuple)
        upsert_script = QB.build_event_structure_script()
        #values_args = list(chain.from_iterable(upsert_script))
        return await db_connection.execute(upsert_script, event_structure_tuple)
    
class RoomTracker(object):
        
    @staticmethod
    async def add_everything_to_database(channel_bot):
        sql_helper = RoomTrackerSQL(channel_bot)
        added_players = await sql_helper.insert_missing_players_into_database()
        added_tracks = await sql_helper.insert_missing_tracks_into_database()
        added_races = await sql_helper.insert_missing_races_into_database()
        added_placements = await sql_helper.insert_missing_placements_into_database()
        added_miis = await sql_helper.update_database_place_miis()
        added_event_id = await sql_helper.add_event_id()
        added_event_ids_race_ids = await sql_helper.insert_missing_event_ids_race_ids()
        added_event_ids = await sql_helper.insert_missing_event(was_real_update=(len(added_event_ids_race_ids) > 0))
        added_event_fcs = await sql_helper.insert_missing_event_fcs_and_miis()
        added_event_fcs_miis = await sql_helper.update_missing_miis_in_event_fcs()
        event_structure_data_dump_event_id = await sql_helper.dump_event_structure_data()

        if DEBUGGING_SQL:
            print(f"Added players: {added_players}")
            print(f"Added tracks: {added_tracks}")
            print(f"Added races: {added_races}")
            print(f"Added placements: {added_placements}")
            print(f"Added miis for placements in races: {added_miis}")
            print(f"Added event id: {added_event_id}")
            print(f"Added event_id, race_id's: {added_event_ids_race_ids}")
            print(f"Added event ids: {added_event_ids}")
            print(f"Added event_id, fc's: {added_event_fcs}")
            print(f"Added miis for event fcs: {added_event_fcs_miis}")
            print(f"Event ids updated for event structure: {event_structure_data_dump_event_id}")
    
    @staticmethod
    @TimerDebuggers.timer_coroutine
    async def add_data(channel_bot):
        if channel_bot.is_table_loaded():
            #Make a deep copy to avoid asyncio switching current task to a tabler command and modifying our data in the middle of us validating it or adding it
            deepcopied_channel_bot = deepcopy(channel_bot)
            if deepcopied_channel_bot.is_table_loaded(): #This check might seem unnecessary, but we'll leave it in case we convert things to asyncio that aren't currently asynchronous (making it necessary)
                try:
                    await RoomTracker.add_everything_to_database(deepcopied_channel_bot)
                except:
                    common.log_traceback(traceback)

def load_room_data():
    if not os.path.exists(common.ROOM_DATA_TRACKING_DATABASE_FILE):
        print("Warning: No database for room tracking found, so creating a new one. If you should have had a database, stop the program immediately using Ctrl+Z, locate the room tracking database or restore a backup.")
        from data_tracking import sql_database_setup
        try:
            sql_database_setup.create_room_tracking_database()
        except:
            os.remove(common.ROOM_DATA_TRACKING_DATABASE_FILE)
            print("Warning: Failed to create database")
            raise

async def start_database():
    global db_connection
    db_connection = ConnectionWrapper(await aiosqlite.connect(common.ROOM_DATA_TRACKING_DATABASE_FILE,isolation_level=None))

async def populate_tier_table():
    populate_tier_table_script = common.read_sql_file(common.ROOM_DATA_POPULATE_TIER_TABLE_SQL)
    await db_connection.executescript(populate_tier_table_script)

async def populate_score_matrix_table():
    rows = []

    for room_size in range(0,12):
        for place in range(0,12):
            rows.append((room_size+1, place+1, common.SCORE_MATRIX[room_size][place]))

    await db_connection.executescript("DELETE FROM Score_Matrix;")
    await db_connection.executemany("INSERT INTO Score_Matrix VALUES (?, ?, ?)", rows)

async def populate_player_fcs_table():
    rows = []

    fc_map = UserDataProcessing.fc_discordId
    existing_count = (await db_connection.execute("SELECT count(*) FROM Player_FCs;"))[0][0]

    if len(fc_map) == 0 or len(fc_map) == existing_count:
        print("Not changing FC table")
        return

    start = time.time()
    print(f'Populating FC table in database...')

    for fc in fc_map:
        discord_id = fc_map[fc][0]
        rows.append((fc, discord_id))

    await db_connection.execute("DELETE FROM Player_FCs;")
    await db_connection.executemany("insert into Player_FCs values (?, ?)", rows)
    print(f'FC table population finished in {time.time()-start} seconds')

async def add_player_fcs(fc_map):
    rows = []
    for fc in fc_map:
        discord_id = fc_map[fc][0]
        rows.append((fc, discord_id))

    await db_connection.executemany("INSERT OR REPLACE INTO Player_FCs VALUES(?, ?)", rows)

async def ensure_foreign_keys_on():
    await db_connection.executescript("""PRAGMA foreign_keys = ON;""")
    
async def database_maintenance():
    maintenance_script = common.read_sql_file(common.ROOM_DATA_TRACKING_DATABASE_MAINTENANCE_SQL)
    await db_connection.executescript(maintenance_script)

async def vacuum():
    await db_connection.executescript("VACUUM;")

async def fix_shas(shas:Dict):
    for sha, track_name in shas.items():
        no_author_name = Race.remove_author_and_version_from_name(track_name)
        lookup = Race.get_track_name_lookup(no_author_name)
        script =     f"""
            INSERT OR IGNORE INTO Track VALUES("{track_name}", "No Track Page", "{no_author_name}", 1, "{lookup}");
            UPDATE Race SET track_name = "{track_name}" WHERE Race.track_name = "{sha}";
            DELETE FROM Track WHERE track.track_name = "{sha}";
        """
        await db_connection.executescript(script)

async def initialize():
    from datetime import datetime
    print(f"{datetime.now()}: Database initialization started")
    load_room_data()
    await start_database()
    await ensure_foreign_keys_on()
    await populate_tier_table()
    await populate_score_matrix_table()
    await populate_player_fcs_table()

    # Race.initialize needs to be called first
    await fix_shas(Race.sha_track_name_mappings)
    if common.is_prod or common.is_beta:
        await vacuum()
    print(f"{datetime.now()}: Database initialization finished")

def save_data():
    pass

# Unused
def on_exit():
    save_data()
    db_connection.close()

if __name__ == '__main__':
    os.chdir("..")
    initialize()
    