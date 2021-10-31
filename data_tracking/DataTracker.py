'''
Created on Oct 21, 2021

@author: willg

This module helps track and store data from Wiimmfi.

'''
import common
from collections import defaultdict
from datetime import datetime, timedelta
import Race as TableBotRace
import Player as TableBotPlayer
from typing import List, Dict, Tuple
import UtilityFunctions
from copy import deepcopy, copy
import pprint
import traceback
#import itertools
#from contextlib import closing

import os
from data_tracking import Data_Tracker_SQL_Query_Builder as QB

DEBUGGING_DATA_TRACKER = False

import sqlite3
database_connection:sqlite3.Connection = None

class SQLDataBad(Exception):
    pass
class SQLTypeWrong(SQLDataBad):
    pass
class FormatWrong(SQLDataBad):
    pass

#dict of channel IDs to tier numbers

RT_NAME = "rt"
CT_NAME = "ct"
RXX_LOCKER_NAME = "rxx_locker"
RT_TABLE_BOT_CHANNEL_TIER_MAPPINGS = {
    843981870751678484:8,
    836652527432499260:7,
    747290199242965062:6,
    747290182096650332:5,
    873721400056238160:5,
    747290167391551509:4,
    801620685826818078:4,
    747290151016857622:3,
    801620818965954580:3,
    805860420224942080:3,
    747290132675166330:2,
    754104414335139940:2,
    801630085823725568:2,
    747289647003992078:1,
    747544598968270868:1,
    781249043623182406:1
    }

CT_TABLE_BOT_CHANNEL_TIER_MAPPINGS = {
    875532532383363072:7,
    850520560424714240:6,
    801625226064166922:5,
    747290436275535913:4,
    879429019546812466:4,
    747290415404810250:3,
    747290383297282156:2,
    823014979279519774:2,
    747290363433320539:1,
    871442059599429632:1
    }

RT_REVERSE_TIER_MAPPINGS = defaultdict(set)
CT_REVERSE_TIER_MAPPINGS = defaultdict(set)

for k,v in RT_TABLE_BOT_CHANNEL_TIER_MAPPINGS.items():
    RT_REVERSE_TIER_MAPPINGS[v].add(k)
for k,v in CT_TABLE_BOT_CHANNEL_TIER_MAPPINGS.items():
    CT_REVERSE_TIER_MAPPINGS[v].add(k)
    
TABLE_BOT_CHANNEL_TIER_MAPPINGS = {RT_NAME:RT_TABLE_BOT_CHANNEL_TIER_MAPPINGS, CT_NAME:CT_TABLE_BOT_CHANNEL_TIER_MAPPINGS}

room_data = {RT_NAME:{},
             CT_NAME:{},
             RXX_LOCKER_NAME:{}
             }
ALREADY_ADDED_ERROR = 11
FATAL_ERROR = 12
RACE_ADD_SUCCESS = 10
DATA_DUMP_SUCCESS = 9
#Need rxx -> [channel_id:channel_data:default_dict, room_data]

from collections import namedtuple
Place = namedtuple('Place', ['fc', 'name', 'place', 'time', 'lagStart', 'playerURL', 'pid', 'ol_status', 'roomPosition', 'roomType', 'connectionFails', 'role', 'vr', 'character', 'vehicle', 'discord_name', 'lounge_name', 'mii_hex'])
Race = namedtuple('Race', ['timeAdded', 'channel_id', 'tier', 'matchTime', 'id', 'raceNumber', 'roomID', 'rxx', 'trackURL', 'roomType', 'trackName', 'trackNameFixed', 'cc', 'placements', 'region', 'is_ct'])
Event = namedtuple('Event', ['timeAdded', 'allFCs', 'races', 'room_type', 'name_changes', 'removed_races', 'placement_history', 'forcedRoomSize', 'playerPenalties', 'dc_on_or_before', 'sub_ins', 'set_up_user_discord_id', 'set_up_user_display_name', 'playersPerTeam', 'numberOfTeams', 'defaultRoomSize', 'numberOfGPs', 'eventName', 'missingRacePts', 'manualEdits', 'ignoreLargeTimes', 'teamPenalties', 'teams', 'miis'])


"""
LOCK_OBTAINED = 0
NO_LOCK = 1
LOCK_IN_USE = 2
def obtain_rxx_lock(rxx):
    create_rxx_lock_if_needed()
    if rxx in room_data[RXX_LOCKER_NAME]:
        if not room_data[RXX_LOCKER_NAME][rxx][0]:
            room_data[RXX_LOCKER_NAME][rxx][0] = True
            room_data[RXX_LOCKER_NAME][rxx][1] = datetime.now()
            return LOCK_OBTAINED
        else:
            return LOCK_IN_USE
    else:
        return NO_LOCK
    
def create_rxx_lock_if_needed(rxx):
    if rxx in room_data[RXX_LOCKER_NAME]:
        return
    room_data[RXX_LOCKER_NAME][rxx] = [False, datetime.now()]

def release_rxx_lock(rxx):
    room_data[RXX_LOCKER_NAME][rxx][0] = False

def free_old_locks():
    MAX_LOCK_TIME = timedelta(seconds=15)
    for rxx_lock in room_data[RXX_LOCKER_NAME].values():
        cur_time = datetime.now()
        if rxx_lock[0] and (cur_time - MAX_LOCK_TIME) > rxx_lock[1]: #Assume we locked and didn't release somehow
            rxx_lock[0] = False
"""
def get_start_time(channel_data):
    return channel_data[1]
def get_last_updated(channel_data):
    return channel_data[2]
def get_room_update_count(channel_data):
    return channel_data[3]
def get_tier(channel_data):
    return channel_data[4]

def tier_matches(tier, channel_data):
    if tier is None:
        return True
    return tier == get_tier(channel_data)

class DataRetriever(object):
    #TODO: Finish method
    @staticmethod
    def choose_best_event_data(channel_id_events:Dict[int, List], prefer_tier=False, require_private_room=True) -> Tuple[List, Event]:
        '''Takes a dictionary with channel ids mapping to event data and returns the channel data and event that is most likely to be legitimate and accurate'''
        LEIGITMATE_ROOM_UPDATE_COUNT = 3
        cur_best = None
        #Filter by private rooms only if required
        filtered_events = filter(channel_id_events.values(), lambda event_data: (not require_private_room or all(race.roomType == TableBotRace.PRIVATE_ROOM_TYPE for race in event_data[1].races)))
        for channel_data, event in filtered_events:
            if prefer_tier and get_tier(channel_data) is None:
                continue
            if get_room_update_count(channel_data) < LEIGITMATE_ROOM_UPDATE_COUNT:
                continue
            if cur_best is None:
                cur_best = (channel_data, event)
                continue
        
        #choose best out of the ones that didn't have a tier
            
            
        return cur_best
            
    
    @staticmethod
    def get_filtered_events(rxx_dict, tier=None, in_last_days=None):
        time_cutoff = (datetime.now() - timedelta(days=in_last_days)) if in_last_days else datetime.min
        results = []
        for rxx in rxx_dict:
            best_data = DataRetriever.choose_best_event_data(rxx_dict[rxx], prefer_tier=(tier is None))
            if best_data is None:
                continue
            channel_data, event = best_data
            if tier_matches(tier, channel_data) and time_cutoff < get_start_time(channel_data):
                results.append(event)
        return results
    @staticmethod
    def get_popular_characters(is_ct=False, tier=None, in_last_days=None, starting_position=None):
        pass
    
    @staticmethod
    def get_popular_tracks(is_ct=False, tier=None, in_last_days=None):
        track_count = defaultdict(int)
        rxx_dict = room_data[CT_NAME] if is_ct else room_data[RT_NAME]
        filtered_rxxs = DataRetriever.get_filtered_rxxs(rxx_dict, tier, in_last_days)


class RoomTrackerSQL(object):
    def __init__(self, channel_bot):
        self.channel_bot = channel_bot
    
    def wrong_type_message(self, data, expected_type, multi=False):
        if multi:
            return f"{data} of type {type(data)} is not any of the expected types: ({', '.join([(t.__name__ if t is not None else 'None') for t in expected_type])})"
        else:
            return f"{data} of type {type(data)} is not expected type: {expected_type.__name__}"
    
    def validate_player_data(self, players:List[TableBotPlayer.Player]):
        '''Validates that all the data is players is the correct type and format before going into the database'''
        for player in players:
            if not isinstance(player.get_FC(), str):
                raise SQLTypeWrong(self.wrong_type_message(player.get_FC(), str))
            if not UtilityFunctions.is_fc(player.get_FC()):
                raise SQLDataBad(f"{player.get_FC()} is not a formatted like an FC")
            if not isinstance(player.get_player_id(), int):
                raise SQLTypeWrong(self.wrong_type_message(player.get_player_id(), int))
            if not isinstance(player.get_mkwx_url(), str):
                raise SQLTypeWrong(self.wrong_type_message(player.get_mkwx_url(), str))
    
    def insert_players_into_database(self, players:List[TableBotPlayer.Player]):
        self.validate_player_data(players)
        insert_player_statement = QB.get_insert_into_player_table_script()      
        all_data = [(p.get_FC(), int(p.get_player_id()), p.get_mkwx_url()) for p in players]
        with database_connection:
            result = database_connection.executemany(insert_player_statement, all_data)
            
    def insert_missing_players_into_database(self):
        room_fc_placements = self.channel_bot.getRoom().getFCPlacements()
        find_fcs_statement = QB.get_fcs_in_Player_table(room_fc_placements.keys())
        found_fcs = set(result[0] for result in database_connection.execute(find_fcs_statement, [k for k in room_fc_placements]))
        print(found_fcs)
        missing_fcs = set(room_fc_placements).difference(found_fcs)
        print(missing_fcs)
        if len(missing_fcs) > 0:
            self.insert_players_into_database([room_fc_placements[fc].getPlayer() for fc in missing_fcs])
    
    def validate_races_data(self, races:List[TableBotRace.Race]):
        raise NotImplementedError()
    
    def get_race_as_sql_tuple(self, race):
        raise NotImplementedError()
    
    def get_race_as_sql_track_tuple(self, race):
        no_author_name = race.getTrackNameWithoutAuthor()
        return (race.get_track_name(),
                race.get_track_url(),
                no_author_name,
                Race.is_custom_track(),
                TableBotRace.get_track_name_lookup(no_author_name)
                )
    
    def insert_races_into_database(self, races:List[TableBotRace.Race]):
        self.validate_races_data(races)
        insert_race_statement = QB.get_insert_into_race_table_script()
        all_data = [self.get_race_as_sql_tuple(r) for r in races]
        with database_connection:
            result = database_connection.executemany(insert_race_statement, all_data)
    
    def insert_missing_races_into_database(self):
        race_id_races = {race.get_race_id():race for race in self.channel_bot.getRoom().races}
        find_race_ids_statement = QB.get_existing_race_ids_in_Race_table(race_id_races)
        found_race_ids = set(result[0] for result in database_connection.execute(find_race_ids_statement, [k for k in race_id_races]))
        print(found_race_ids)
        missing_race_ids = set(race_id_races).difference(found_race_ids)
        print(missing_race_ids)
        if len(missing_race_ids) > 0:
            self.insert_races_into_database([race_id_races[race_id] for race_id in missing_race_ids])


    def validate_tracks_data(self, races:List[TableBotRace.Race]):
        for race in races:
            race:TableBotRace.Race
            if not isinstance(race.get_track_name(), str):
                raise SQLTypeWrong(self.wrong_type_message(race.get_track_name(), str))
            if race.get_track_name() == "None":
                raise SQLDataBad(f"track_name cannot be an 'None', room rxx: {race.rxx}")
            if not isinstance(race.get_track_url(), (str, type(None))):
                raise SQLTypeWrong(self.wrong_type_message(race.get_track_url(), (str, None), multi=True))
            
            no_author_name = race.getTrackNameWithoutAuthor()
            if not isinstance(no_author_name, str):
                raise SQLTypeWrong(self.wrong_type_message(race.get_track_url(), str))
            
            if not isinstance(race.is_custom_track(), bool):
                raise SQLTypeWrong(self.wrong_type_message(race.is_custom_track(), bool))
            
            if not isinstance(TableBotRace.get_track_name_lookup(no_author_name), str):
                raise SQLTypeWrong(self.wrong_type_message(TableBotRace.get_track_name_lookup(no_author_name), str))
            
    
    def insert_tracks_into_database(self, races:List[TableBotRace.Race]):
        self.validate_tracks_data(races)
        insert_track_statement = QB.get_insert_into_track_table_script()
        all_data = [self.get_race_as_sql_track_tuple(r) for r in races]
        with database_connection:
            result = database_connection.executemany(insert_track_statement, all_data)
    
    def insert_missing_tracks_into_database(self):
        track_names = {race.get_track_name():race for race in self.channel_bot.getRoom().races}
        find_track_names_statement = QB.get_existing_tracks_in_Track_table(track_names)
        found_track_names = set(result[0] for result in database_connection.execute(find_track_names_statement, [tn for tn in track_names]))
        print(found_track_names)
        missing_track_names = set(track_names).difference(found_track_names)
        print(missing_track_names)
        if len(missing_track_names) > 0:
            self.insert_tracks_into_database([track_names[tn] for tn in missing_track_names])
        

class RoomTracker(object):
    
    @staticmethod
    def new_channel_data(channel_id):
        lounge_tier = None
        if channel_id in RT_TABLE_BOT_CHANNEL_TIER_MAPPINGS:
            lounge_tier = RT_TABLE_BOT_CHANNEL_TIER_MAPPINGS[channel_id]
        if channel_id in CT_TABLE_BOT_CHANNEL_TIER_MAPPINGS:
            lounge_tier = CT_TABLE_BOT_CHANNEL_TIER_MAPPINGS[channel_id]
        #channelid, first command time, last command time, total room updates sent, tier
        return [channel_id, datetime.now(), datetime.now(), 0, lounge_tier]
    
    @staticmethod
    def check_create_channel_data(rxx, rxx_dict, channel_bot):
        if rxx not in rxx_dict:
            rxx_dict[rxx] = {}
        if channel_bot.channel_id not in rxx_dict[rxx]:
            rxx_dict[rxx][channel_bot.channel_id] = [RoomTracker.new_channel_data(channel_bot.channel_id), RoomTracker.create_event(channel_bot)]
            return False
        return True
    
    @staticmethod
    def create_placement(placement:TableBotRace.Placement) -> Place:
        player = placement.getPlayer()
        return Place(fc=player.get_FC(),
                     name=player.get_name(),
                     place=placement.get_place(),
                     time=placement.get_time(),
                     lagStart=placement.get_delta(),
                     playerURL=player.get_mkwx_url(),
                     pid=player.get_player_id(),
                     ol_status=player.get_ol_status(),
                     roomPosition=player.get_position(),
                     roomType=player.get_room_type(),
                     connectionFails=player.get_connection_fails(),
                     role=player.get_role(),
                     vr=player.get_VR(),
                     character=player.get_character(),
                     vehicle=player.get_vehicle(),
                     discord_name=player.get_discord_name(),
                     lounge_name=player.get_lounge_name(),
                     mii_hex=player.get_mii_hex())
    
    @staticmethod
    def create_race(channel_data_info, race:TableBotRace.Race) -> Race:
        channel_id = channel_data_info[0][0]
        tier = get_tier(channel_data_info[0])
        all_placements = [RoomTracker.create_placement(p) for p in race.getPlacements()]
        return Race(timeAdded=datetime.now(),
                    channel_id=channel_id,
                    tier=tier,
                    matchTime=race.get_match_start_time(),
                    id=race.get_race_id(),
                    raceNumber=race.get_race_number(),
                    roomID=race.get_room_id(),
                    rxx=race.get_rxx(),
                    trackURL=race.get_track_url(),
                    roomType=race.get_room_type(),
                    trackName=race.get_track_name(),
                    trackNameFixed=TableBotRace.remove_author_and_version_from_name(race.get_track_name()),
                    cc=race.get_cc(),
                    region=race.get_region(),
                    is_ct=race.is_custom_track(),
                    placements=all_placements)
    
    @staticmethod
    def get_miis(channel_bot) -> Dict[str, str]:
        #[print(mii) for mii in channel_bot.get_miis()]
        return {FC : mii.mii_data_hex_str for (FC,mii) in channel_bot.get_miis().items()}
            
    @staticmethod
    def create_event(channel_bot) -> Event:
        return Event(timeAdded=datetime.now(),
                     allFCs=set(channel_bot.getRoom().getFCs()),
                     races=[],
                     room_type=channel_bot.getRoom().get_room_type(),
                     name_changes=copy(channel_bot.getRoom().name_changes),
                     removed_races=copy(channel_bot.getRoom().removed_races),
                     placement_history=copy(channel_bot.getRoom().placement_history),
                     forcedRoomSize=copy(channel_bot.getRoom().forcedRoomSize),
                     playerPenalties=copy(channel_bot.getRoom().playerPenalties),
                     dc_on_or_before=copy(channel_bot.getRoom().dc_on_or_before),
                     sub_ins=deepcopy(channel_bot.getRoom().sub_ins),
                     set_up_user_discord_id=channel_bot.getRoom().set_up_user,
                     set_up_user_display_name=channel_bot.getRoom().set_up_user_display_name,
                     playersPerTeam=channel_bot.getWar().playersPerTeam,
                     numberOfTeams=channel_bot.getWar().numberOfTeams,
                     defaultRoomSize=channel_bot.getWar().get_num_players(),
                     numberOfGPs=channel_bot.getWar().numberOfGPs,
                     eventName=channel_bot.getWar().warName,
                     missingRacePts=channel_bot.getWar().missingRacePts,
                     manualEdits=copy(channel_bot.getWar().manualEdits),
                     ignoreLargeTimes=channel_bot.getWar().ignoreLargeTimes,
                     teamPenalties=copy(channel_bot.getWar().teamPenalties),
                     teams=copy(channel_bot.getWar().teams),
                     miis=RoomTracker.get_miis(channel_bot))
    @staticmethod
    def update_event_data(channel_bot, channel_data_info):
        channel_data_info[1].allFCs.update(channel_bot.getRoom().getFCs())
        channel_data_info[1].miis.update(RoomTracker.get_miis(channel_bot))
        channel_data_info[1] = Event(timeAdded=channel_data_info[1].timeAdded,
                                     allFCs=channel_data_info[1].allFCs,
                                     races=channel_data_info[1].races,
                                     room_type=channel_bot.getRoom().get_room_type(),
                                     name_changes=copy(channel_bot.getRoom().name_changes),
                                     removed_races=copy(channel_bot.getRoom().removed_races),
                                     placement_history=copy(channel_bot.getRoom().placement_history),
                                     forcedRoomSize=copy(channel_bot.getRoom().forcedRoomSize),
                                     playerPenalties=copy(channel_bot.getRoom().playerPenalties),
                                     dc_on_or_before=copy(channel_bot.getRoom().dc_on_or_before),
                                     sub_ins=deepcopy(channel_bot.getRoom().sub_ins),
                                     set_up_user_discord_id=channel_bot.getRoom().set_up_user,
                                     set_up_user_display_name=channel_bot.getRoom().set_up_user_display_name,
                                     playersPerTeam=channel_bot.getWar().playersPerTeam,
                                     numberOfTeams=channel_bot.getWar().numberOfTeams,
                                     defaultRoomSize=channel_bot.getWar().get_num_players(),
                                     numberOfGPs=channel_bot.getWar().numberOfGPs,
                                     eventName=channel_bot.getWar().warName,
                                     missingRacePts=channel_bot.getWar().missingRacePts,
                                     manualEdits=copy(channel_bot.getWar().manualEdits),
                                     ignoreLargeTimes=channel_bot.getWar().ignoreLargeTimes,
                                     teamPenalties=copy(channel_bot.getWar().teamPenalties),
                                     teams=copy(channel_bot.getWar().teams),
                                     miis=channel_data_info[1].miis)
    
    @staticmethod
    def add_race(channel_data_info, race:TableBotRace.Race):
        _, event = channel_data_info
        for r in event.races:
            if r.rxx != race.get_rxx():
                common.log_error(f"rxx's didn't match in add_race:\n{race}\n{r}")
                return FATAL_ERROR
            if r.id == race.raceID:
                return ALREADY_ADDED_ERROR
        #lock_status = obtain_rxx_lock(race.get_rxx())
        #if lock_status != LOCK_OBTAINED: #in use
        #    return
        
        event.races.append(RoomTracker.create_race(channel_data_info, race))
        return RACE_ADD_SUCCESS
        
    
    @staticmethod
    def update_channel_meta_data(channel_bot, channel_data_info):
        channel_meta_data, event = channel_data_info
        roomRaceIDs = set(r.get_race_id() for r in channel_bot.getRoom().getRaces())
        eventRaceIDs = set(r.id for r in event.races)
        if not (len(roomRaceIDs.difference(eventRaceIDs)) == 0 or roomRaceIDs.issubset(eventRaceIDs)): #The room added a race
            channel_meta_data[2] = datetime.now()
            channel_meta_data[3] += 1
        
    @staticmethod
    def add_races(channel_bot):
        races:List[TableBotRace.Race] = channel_bot.getRoom().getRaces()
        sql_helper = RoomTrackerSQL(channel_bot)
        sql_helper.insert_missing_players_into_database()
        sql_helper.insert_missing_tracks_into_database()
        added_race_ids = sql_helper.insert_missing_races_into_database()
        #sql_helper.
        update_channel_data = True
        update_event_data = True
        for race in races:
            if race.get_rxx() is None or not UtilityFunctions.is_rLID(race.get_rxx()):
                common.log_error(f"No rxx for this race: {race}")
                continue
            rxx_dict = room_data[CT_NAME] if race.is_custom_track() else room_data[RT_NAME]
            update_event_data = RoomTracker.check_create_channel_data(race.get_rxx(), rxx_dict, channel_bot)
            if update_channel_data:
                update_channel_data = False
                RoomTracker.update_channel_meta_data(channel_bot, rxx_dict[race.get_rxx()][channel_bot.channel_id])
            if update_event_data:
                update_event_data = False
                RoomTracker.update_event_data(channel_bot, rxx_dict[race.get_rxx()][channel_bot.channel_id])
            
            success_code = RoomTracker.add_race(rxx_dict[race.get_rxx()][channel_bot.channel_id], race)
            if success_code == FATAL_ERROR:
                return FATAL_ERROR
        return DATA_DUMP_SUCCESS
    #Greedily add all races
    @staticmethod
    def add_data(channel_bot):
        #free_old_locks()
        
        if channel_bot.getRoom().is_initialized():
            try:
                success_code = RoomTracker.add_races(channel_bot)
                if DEBUGGING_DATA_TRACKER:
                    dump_room_data()
                    pretty_print_room_data()
            except:
                raise
                common.log_traceback(traceback)
        
        
            












def pretty_print_room_data():
    temp_data = deepcopy(room_data)
    rt_rxx_dict = temp_data[RT_NAME]
    ct_rxx_dict = temp_data[CT_NAME]
    for rxx_dict in [rt_rxx_dict, ct_rxx_dict]:
        for channel_ids in rxx_dict.values():
            for rxx_channel_data in channel_ids.values():
                _, event = rxx_channel_data
                if event.races is not None:
                    for race_index, race in enumerate(event.races):
                        for place_index, place in enumerate(race.placements):
                            race.placements[place_index] = place._asdict()
                        event.races[race_index] = race._asdict()
                with open("room_race_data.txt", "w", encoding="utf-8") as g:
                    pprint.pprint([r for r in reversed(event.races)], stream=g, depth=15, width=200, sort_dicts=False)
                rxx_channel_data[1] = event._asdict()
    with open("room_data.txt", "w", encoding="utf-8") as f:
        pprint.pprint(temp_data, stream=f, depth=15, width=200)


data_change_versions = {1:"added the time an event was added to Event.timeAdded"}
def modify_existing_data(version=1):
    rt_rxx_dict = room_data[RT_NAME]
    ct_rxx_dict = room_data[CT_NAME]
    if version == 1:
        for rxx_dict in [rt_rxx_dict, ct_rxx_dict]:
            for channel_ids in rxx_dict.values():
                for rxx_channel_data in channel_ids.values():
                    if not 'timeAdded' in rxx_channel_data[1]._fields:
                        time_added = get_start_time(rxx_channel_data[0])
                        rxx_channel_data[1] = Event(timeAdded=time_added, **rxx_channel_data[1])
                    
                        
                        
                        
            
def dump_room_data():
    common.dump_pkl(room_data, common.ROOM_DATA_TRACKER_FILE, "Could not dump pickle room data in data tracking.", display_data_on_error=True)

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


def start_database():
    global database_connection
    database_connection = sqlite3.connect(common.ROOM_DATA_TRACKING_DATABASE_FILE)

def populate_tier_table():
    cur = database_connection.cursor()
    populate_tier_table_script = common.read_sql_file(common.ROOM_DATA_POPULATE_TIER_TABLE_SQL)
    cur.executescript(populate_tier_table_script)
    
def initialize():
    load_room_data()
    start_database()
    populate_tier_table()
    for update_number in data_change_versions:
        modify_existing_data(update_number)

def save_data():
    dump_room_data()
    
def on_exit():
    save_data()


if __name__ == '__init__':
    initialize()
    pretty_print_room_data()
    