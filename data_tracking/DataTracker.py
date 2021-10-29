'''
Created on Oct 21, 2021

@author: willg

This module helps track and store data from Wiimmfi.

'''
import common
from collections import defaultdict
from datetime import datetime, timedelta
import Race as TableBotRace
from typing import List, Dict, Tuple
import UtilityFunctions
from copy import deepcopy, copy
import pprint
import traceback
import os
DEBUGGING_DATA_TRACKER = False

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
    if not os.path.exists(common.DATA_TRACKING_DATABASE_FILE):
        print("Warning: No database for data tracking found, to creating a new one. If you should have had a database, stop the program immediately using Ctrl+Z, locate the data tracking database or restore a backup.")
        from data_tracking import sql_database_setup
        sql_database_setup.create_room_tracking_database()

def initialize():
    load_room_data()
    for update_number in data_change_versions:
        modify_existing_data(update_number)

def save_data():
    dump_room_data()
    
def on_exit():
    save_data()


if __name__ == '__init__':
    initialize()
    pretty_print_room_data()
    