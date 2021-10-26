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
from copy import deepcopy


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
ALREADY_ADDED_ERROR = 11
FATAL_ERROR = 12
RACE_ADD_SUCCESS = 10
DATA_DUMP_SUCCESS = 9
for k,v in RT_TABLE_BOT_CHANNEL_TIER_MAPPINGS.items():
    RT_REVERSE_TIER_MAPPINGS[v].add(k)
for k,v in CT_TABLE_BOT_CHANNEL_TIER_MAPPINGS.items():
    CT_TABLE_BOT_CHANNEL_TIER_MAPPINGS[v].add(k)
TABLE_BOT_CHANNEL_TIER_MAPPINGS = {RT_NAME:RT_TABLE_BOT_CHANNEL_TIER_MAPPINGS, CT_NAME:CT_TABLE_BOT_CHANNEL_TIER_MAPPINGS}

room_data = {RT_NAME:{},
             CT_NAME:{},
             RXX_LOCKER_NAME:{}
             }
#Need rxx -> [channel_id:channel_data:default_dict, room_data]

from collections import namedtuple
Place = namedtuple('Place', ['fc', 'name', 'place', 'time', 'lagStart', 'playerURL', 'pid', 'ol_status', 'roomPosition', 'roomType', 'connectionFails', 'role', 'vr', 'character', 'vehicle', 'discord_name', 'lounge_name', 'mii_hex'])
Race = namedtuple('Race', ['timeAdded', 'channel_id', 'tier', 'matchTime', 'id', 'raceNumber', 'roomID', 'rxx', 'trackURL', 'roomType', 'trackName', 'trackNameFixed', 'cc', 'placements', 'region', 'is_ct'])
Event = namedtuple('Event', ['allFCs', 'races', 'name_changes', 'removed_races', 'placement_history', 'forcedRoomSize', 'playerPenalties', 'dc_on_or_before', 'set_up_user', 'sub_ins', 'playersPerTeam', 'numberOfTeams', 'defaultRoomSize', 'numberOfGPs', 'eventName', 'missingRacePts', 'manualEdits', 'ignoreLargeTimes', 'teamPenalties', 'forcedRoomSize', 'teams', 'miis'])

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
    def choose_best_event_data(channel_id_events:Dict[int, List[List, Event]], prefer_tier=False) -> Tuple[List, Event]:
        '''Takes a dictionary with channel ids mapping to event data and returns the channel data and event that is most likely to be legitimate and accurate'''
        LEIGITMATE_ROOM_UPDATE_COUNT = 3
        cur_best = None
        for channel_data, event in channel_id_events.values():
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
            channel_data, event = DataRetriever.choose_best_event_data(rxx_dict[rxx], prefer_tier=(tier is None))
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
        channel_id = channel_data_info[0]
        tier = channel_data_info[4]
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
                    trackNameFixed=Race.remove_author_and_version_from_name(race.get_track_name()),
                    cc=race.get_cc(),
                    region=race.get_region(),
                    is_ct=race.is_custom_track(),
                    placements=all_placements)
    
    @staticmethod
    def get_miis(channel_bot) -> Dict[str, str]:
        return {mii.FC : mii.mii_data_hex_str for mii in channel_bot.miis}
            
    @staticmethod
    def create_event(channel_bot) -> Event:
        return Event(allFCs=set(channel_bot.getRoom().getFCs()),
                     races=[],
                     name_changes=channel_bot.getRoom().name_changes.copy(),
                     removed_races=channel_bot.getRoom().removed_races.copy(),
                     placement_history=channel_bot.getRoom().placement_history.copy(),
                     forcedRoomSize=channel_bot.getRoom().forcedRoomSize.copy(),
                     playerPenalties=channel_bot.getRoom().playerPenalties.copy(),
                     dc_on_or_before=channel_bot.getRoom().dc_on_or_before.copy(),
                     sub_ins=deepcopy(channel_bot.getRoom().sub_ins),
                     set_up_user_discord_id=channel_bot.getRoom().set_up_user,
                     set_up_user_display_name=channel_bot.getRoom().set_up_user_display_name,
                     playersPerTeam=channel_bot.getWar().playersPerTeam,
                     numberOfTeams=channel_bot.getWar().numberOfTeams,
                     defaultRoomSize=channel_bot.getWar().get_num_players(),
                     numberOfGPs=channel_bot.getWar().numberOfGPs,
                     eventName=channel_bot.getWar().warName,
                     missingRacePts=channel_bot.getWar().missingRacePts,
                     manualEdits=channel_bot.getWar().manualEdits.copy(),
                     ignoreLargeTimes=channel_bot.getWar().ignoreLargeTimes,
                     teamPenalties=channel_bot.getWar().teamPenalties.copy(),
                     forcedRoomSize=channel_bot.getWar().forcedRoomSize.copy(),
                     teams=channel_bot.getWar().teams.copy(),
                     miis=RoomTracker.get_miis(channel_bot))
    @staticmethod
    def update_event_data(channel_bot, channel_data_info):
        channel_data_info[1].allFCs.update(channel_bot.getRoom().getFCs())
        channel_data_info[1].miis.update(RoomTracker.get_miis(channel_bot))
        channel_data_info[1] = Event(allFCs=channel_data_info[1].allFCs,
                                     races=channel_data_info[1].races,
                                     name_changes=channel_bot.getRoom().name_changes.copy(),
                                     removed_races=channel_bot.getRoom().removed_races.copy(),
                                     placement_history=channel_bot.getRoom().placement_history.copy(),
                                     forcedRoomSize=channel_bot.getRoom().forcedRoomSize.copy(),
                                     playerPenalties=channel_bot.getRoom().playerPenalties.copy(),
                                     dc_on_or_before=channel_bot.getRoom().dc_on_or_before.copy(),
                                     sub_ins=deepcopy(channel_bot.getRoom().sub_ins),
                                     set_up_user_discord_id=channel_bot.getRoom().set_up_user,
                                     set_up_user_display_name=channel_bot.getRoom().set_up_user_display_name,
                                     playersPerTeam=channel_bot.getWar().playersPerTeam,
                                     numberOfTeams=channel_bot.getWar().numberOfTeams,
                                     defaultRoomSize=channel_bot.getWar().get_num_players(),
                                     numberOfGPs=channel_bot.getWar().numberOfGPs,
                                     eventName=channel_bot.getWar().warName,
                                     missingRacePts=channel_bot.getWar().missingRacePts,
                                     manualEdits=channel_bot.getWar().manualEdits.copy(),
                                     ignoreLargeTimes=channel_bot.getWar().ignoreLargeTimes,
                                     teamPenalties=channel_bot.getWar().teamPenalties.copy(),
                                     forcedRoomSize=channel_bot.getWar().forcedRoomSize.copy(),
                                     teams=channel_bot.getWar().teams.copy(),
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
        
        event.races.append(RoomTracker.create_race(race))
        return RACE_ADD_SUCCESS
        
    
    @staticmethod
    def update_channel_meta_data(channel_bot, channel_data_info):
        channel_meta_data, event = channel_data_info
        roomRaceIDs = set(r.get_race_id() for r in channel_bot.getRoom().getRaces())
        eventRaceIDs = set(r.get_race_id() for r in event.races)
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
        if channel_bot.is_initialized():
            try:
                success_code = RoomTracker.add_races(channel_bot)
            except Exception as e:
                raise e
        print(room_data)
        
            
















            
def dump_room_data():
    common.dump_pkl(room_data, common.ROOM_DATA_TRACKER_FILE, "Could not dump pickle room data in data tracking.", display_data_on_error=True)

def load_room_data():
    room_data.clear()
    room_data.update(common.load_pkl(common.ROOM_DATA_TRACKER_FILE, "Could not load pickle for room data in data tracking, using empty data instead.", default=dict))

def initialize():
    load_room_data()

def on_exit():
    dump_room_data()
    