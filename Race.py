'''
Created on Jul 12, 2020

@author: willg
'''
import UtilityFunctions
import UserDataProcessing
from Placement import DISCONNECTION_TIME, Placement
from collections import defaultdict
from typing import List
import common

CTGP_CTWW_ROOM_TYPE = 'vs_54'
BATTLE_ROOM_TYPE = 'bt'
RT_WW_ROOM_TYPE = 'vs'
PRIVATE_ROOM_TYPE = 'priv'
UNKNOWN_ROOM_TYPE = 'unk'




track_name_abbreviation_mappings = {
    #Mushroom Cup
    "Wii Luigi Circuit (Nintendo)": ("LC", "ルイサ"),
    "Wii Moo Moo Meadows (Nintendo)": ("MMM", "モモカン"),
    "Wii Mushroom Gorge (Nintendo)": ("MG", "キノキャニ"),
    "Wii Toad's Factory (Nintendo)": ("TF", "工場"),
    #Flower Cup
    "Wii Mario Circuit (Nintendo)":("MC", "マリサ"),
    "Wii Coconut Mall (Nintendo)": ("CM", "ココモ"),
    "Wii DK Summit (Nintendo)":("DKS", "スノボ"),
    "Wii Wario's Gold Mine (Nintendo)":("WGM", "鉱山"),
    #Star Cup
    "Wii Daisy Circuit (Nintendo)": ("DC", "デイサ"),
    "Wii Koopa Cape (Nintendo)": ("KC", "岬"),
    "Wii Maple Treeway (Nintendo)": ("MT", "メイプル"),
    "Wii Grumble Volcano (Nintendo)": ("GV", "火山"),
    #Special Cup
    "Wii Dry Dry Ruins (Nintendo)": ("DDR", "遺跡"),
    "Wii Moonview Highway (Nintendo)": ("MvH", "ムンリ"),
    "Wii Bowser's Castle (Nintendo)": "BCWii",
    "Wii Rainbow Road (Nintendo)": ("RR", "虹"),
    #Shell Cup
    "GCN Peach Beach (Nintendo)": ("rPB", "ピーチビーチ"),
    "DS Yoshi Falls (Nintendo)": ("rYF", "ヨシフォ"),
    "SNES Ghost Valley 2 (Nintendo)": ("GV2", "沼"),
    "N64 Mario Raceway (Nintendo)": ("rMR", "64マリサ"),
    #Banana Cup
    "N64 Sherbet Land (Nintendo)": ("rSL", "シャベラン"),
    "GBA Shy Guy Beach (Nintendo)": ("SGB", "兵浜"),
    "DS Delfino Square (Nintendo)": ("rDS", "モンテ"),
    "GCN Waluigi Stadium (Nintendo)": ("rWS", "ワルスタ"),
    #Leaf Cup
    "DS Desert Hills (Nintendo)": ("rDH", "さばく"),
    "GBA Bowser Castle 3 (Nintendo)": "BC3",
    "N64 DK's Jungle Parkway (Nintendo)": ("rJP", "ジャンパ"),
    "GCN Mario Circuit (Nintendo)": ("GCN MC", "GCマリサ"),
    #Lightning Cup
    "SNES Mario Circuit 3 (Nintendo)": ("MC3", "SFCマリサ"),
    "DS Peach Gardens (Nintendo)": ("rPG", "ピチガ"),
    "GCN DK Mountain (Nintendo)": ("DKM", "山"),
    "N64 Bowser's Castle (Nintendo)": ("BC64", "64BC")
    }

hex_chars = "abcdef0123456789"
sha_track_name_mappings = {"9f09ddb05bc5c7b04bb7aa120f6d0f21774143eb":"Waluigi's Motocross (v1.9)"}

def initialize():
    sha_track_name_mappings.clear()
    sha_track_name_mappings.update(common.load_pkl(common.SHA_TRACK_NAMES_FILE, "Could not load in SHA Track names. Using empty dict instead", default=dict))
    
def on_exit():
    common.dump_pkl(sha_track_name_mappings, common.SHA_TRACK_NAMES_FILE, "Could not dump pkl for SHA Track names.", display_data_on_error=True)

def set_ctgp_region(new_region:str):
    global CTGP_CTWW_ROOM_TYPE
    CTGP_CTWW_ROOM_TYPE = new_region
    
class Race:
    '''
    classdocs
    '''



    def __init__(self, matchTime, matchID, raceNumber, roomID, roomType, cc, track, is_ct, rxx=None, raceID=None, trackURL=None, placements=None):
        self.matchTime = matchTime
        self.matchID = matchID
        self.raceNumber = raceNumber
        self.roomID = roomID
        self.rxx = rxx
        self.trackURL = trackURL
        self.raceID = raceID
        self.roomType = roomType
        self.track = str(track)
        if self.track in sha_track_name_mappings:
            self.track = sha_track_name_mappings[self.track]
        self.track_check()
        self.cc = cc
        self.placements = []
        self.region = None
        self.is_ct = is_ct
        
    
    def track_check(self):
        if all(c in hex_chars for c in self.track):
            common.log_error(f"The following track had no SHA mapping: {self.track}")
            
    
    def hasFC(self, FC):
        return False if self.getPlacement(FC) is None else True
        
        
    def numRacers(self):
        if (self.placements is None):
            return 0
        return len(self.placements)
    
    def updateRoomType(self):
        roomTypeCount = defaultdict(int)
        for placement in self.getPlacements():
            roomTypeCount[placement.getPlayer().room_type] += 1
        mostCommonRoomType = max(roomTypeCount, key=lambda x: roomTypeCount[x])
        self.roomType = mostCommonRoomType
            
    def addPlacement(self, placement):
        #I'm seriously lazy, but it doesn't matter if we sort 12 times rather than inserting in the correct place - this is a small list
        self.placements.append(placement)
        self.placements.sort(key=lambda x: x.time)
        i = 0
        while i < len(self.placements):
            self.placements[i].place = i+1
            i += 1
        self.updateRoomType()
         
    def setRegion(self, region):
        self.region = region
        
    def setRegionFromPlacements(self):
        if len(self.placements) > 0:
            first_placement = self.placements[0]
            self.region = first_placement.player.room_type
    
    def isCTGPWW(self):
        return self.region == CTGP_CTWW_ROOM_TYPE
    
    def isRTWW(self):
        return self.region == RT_WW_ROOM_TYPE
    
    def isBattleWW(self):
        return self.region == BATTLE_ROOM_TYPE
    
    def isPrivateRoom(self):
        return self.region == PRIVATE_ROOM_TYPE
    
    def isUnknownRoomType(self):
        return not self.isCTGPWW() and not self.isRTWW() and not self.isBattleWW() and not self.isPrivateRoom()
    
    def getRoomRating(self):
        roomRating = 0
        all_ratings =[placement.player.get_player_skill_rating() for placement in self.placements]
        if len(all_ratings) > 0:
            roomRating = sum(all_ratings) // len(all_ratings)
        return roomRating
    
    def applyPlacementChanges(self, placement_changes):
        for (old_position_number, new_position_number) in placement_changes:
            self.insertPlacement(old_position_number, new_position_number)
    
    def insertPlacement(self, old_position_number, new_position_number):
        self.placements.insert(new_position_number-1, self.placements.pop(old_position_number-1))
        for place, placement in enumerate(self.placements, 1):
            placement.place = place

    
    def getPlacements(self) -> List[Placement]:
        return self.placements
    
    def getPlacement(self, fc) -> Placement:
        for p in self.placements:
            if p.player.FC == fc:
                return p
            
    def getPlacementNumber(self, fc):
        for placement_num, p in enumerate(self.placements, 1):
            if p.player.FC == fc:
                return placement_num
    
    def getNumberOfPlayers(self):
        return len(self.placements)
    
    def getFCs(self):
        return [pl.player.FC for pl in self.placements]
    
    
    def getTrackNameWithoutAuthor(self):
        if self.track is None or self.track == "None":
            return "No track"
        tempName = self.track.strip()
        if "(" in tempName:
            author_index = tempName.rfind("(")
            if author_index > 2:
                tempName = tempName[:author_index-1].strip()
        
        for i in reversed(range(2, len(tempName))):
            
            if tempName[i].isnumeric() and tempName[i-1] == 'v':
                tempName = tempName[:i-1].strip()
                
                break
        
        if "beta" in tempName.lower():
            betaIndex = tempName.lower().rfind("beta")
            if betaIndex > 0:
                temp = tempName[:betaIndex].strip()
                if len(temp) > 0:
                    tempName = temp
        
        tempOld = tempName.replace(".ctgp", "").strip()
        if len(tempOld) > 0:
            return tempOld
        
        return tempName
    
    def hasTie(self):
        for placement_1 in self.placements:
            for placement_2 in self.placements:
                if placement_1.player.FC != placement_2.player.FC and placement_1 == placement_2:
                    return True
        return False
    
    def getTies(self):
        ties = []
        for placement_1 in self.placements:
            for placement_2 in self.placements:
                if placement_1.player.FC != placement_2.player.FC and placement_1 == placement_2\
                and not placement_1.is_bogus_time() and not placement_2.is_bogus_time()\
                and not placement_1.is_disconnected() and not placement_1.is_disconnected():
                    if placement_1.player.FC not in ties:
                        ties.append(placement_1.player.FC)
                    if placement_2.player.FC not in ties:
                        ties.append(placement_2.player.FC)       
        return ties
    
    def get_placement_times_as_set(self) -> set:
        return set(placement.get_time() for placement in self.placements)
    
    #Specialized function
    def times_are_subset_of(self, other_race) -> bool:
        race_times_set = self.get_placement_times_as_set()
        other_race_times_set = other_race.get_placement_times_as_set()
        return other_race_times_set.issubset(race_times_set)
    
    def times_are_subset_of_and_not_all_blank(self, other_race) -> bool:
        race_times_set = self.get_placement_times_as_set()
        race_times_set.discard(DISCONNECTION_TIME) #Discard disconnection 
        other_race_times_set = other_race.get_placement_times_as_set()
        other_race_times_set.discard(DISCONNECTION_TIME)
        #If there were no times left after removing blank times, then the entire room had blank times, which is a different error
        if len(race_times_set) == 0 or len(other_race_times_set) == 0:
            return False
        
        return other_race_times_set.issubset(race_times_set)
    
    def has_unusual_delta_time(self):
        return any(True for placement in self.placements if placement.is_delta_unlikely())
        
    
    def getPlayerObjects(self):
        players = []
        for placement in self.placements:
            players.append(placement.player)
        return players
    
    def getPlayersByPlaceInRoom(self):
        players = self.getPlayerObjects()
        try:
            players.sort(key=lambda p: int(p.positionInRoom))
        except ValueError:
            print("This actually happened - position in room wasn't a number.")
            players.sort(key=lambda p: p.positionInRoom)
        return players
    
    def getPlayersByPlaceInRoomString(self):
        sortedPlayers = self.getPlayersByPlaceInRoom()
        to_build = ""
        for player in sortedPlayers:
            lounge_name = UtilityFunctions.process_name(UserDataProcessing.lounge_get(player.FC))
            if lounge_name is None or len(lounge_name) == 0:
                lounge_name = "No Lounge"
            to_build += "**" + str(player.positionInRoom) + ". " + lounge_name + "** - " + UtilityFunctions.process_name(player.name) + "\n"
        return to_build
    
    def FCInPlacements(self, FC):
        for placement in self.placements:
            if placement.player.FC == FC:
                return True
        return False
    
    def getAbbreviatedName(self):
        if self.track in track_name_abbreviation_mappings:
            track_mapping = track_name_abbreviation_mappings[self.track]
            if isinstance(track_mapping, tuple):
                return track_mapping[0] + " (" + track_mapping[1] + ")"
            else:
                return track_mapping
                
        return self.getTrackNameWithoutAuthor()
    
    def getWWTypeName(self):
        if self.region is None:
            return ""
        
        if self.region == CTGP_CTWW_ROOM_TYPE:
            return "CTWW (CTGP)"
        if self.region == RT_WW_ROOM_TYPE:
            return "WW"
        if self.region == BATTLE_ROOM_TYPE:
            return "Battle WW"
        if self.region == PRIVATE_ROOM_TYPE:
            return "Private Room"
        return "Unknown"
    
    @staticmethod
    def getWWFullName(region):
        if region is None:
            return ""
        if region == CTGP_CTWW_ROOM_TYPE:
            return "CTGP Custom Track Worldwide"
        if region == RT_WW_ROOM_TYPE:
            return "Regular Track Worldwide"
        if region == BATTLE_ROOM_TYPE:
            return "Battle Worldwide"
        if region == PRIVATE_ROOM_TYPE:
            return "Private"
        return "Unknown"
        
        
    def __str__(self):
        curStr = "Race #" + str(self.raceNumber) + " - " + UtilityFunctions.process_name(self.getTrackNameWithoutAuthor()) + " - " + str(self.cc) + "cc" + \
         "\nMatch end time: " + str(self.matchTime)
        placementsSTR = ""
        for placement in self.placements:
            placementsSTR += str("\n\t" + str(placement))
        return curStr + placementsSTR
            

        