'''
Created on Jul 12, 2020

@author: willg
'''
import UtilityFunctions
from Placement import DISCONNECTION_TIME, Placement
from collections import defaultdict
from typing import List
import common

CTGP_CTWW_REGION = 'vs_54'
BATTLE_REGION = 'bt'
RT_WW_REGION = 'vs'
PRIVATE_ROOM_REGION = 'priv'
UNKNOWN_REGION = 'unk'
VALID_REGIONS = {CTGP_CTWW_REGION, BATTLE_REGION, RT_WW_REGION, PRIVATE_ROOM_REGION, UNKNOWN_REGION}


def is_valid_region(region:str):
    return region in VALID_REGIONS or region.startswith("vs_")

# https://tinyurl.com/mkwdictionary
track_name_abbreviation_mappings = {
    #Mushroom Cup
    "Wii Luigi Circuit (Nintendo)": ("LC", "ルイサ"),
    "Wii Moo Moo Meadows (Nintendo)": ("MMM", "モモカン"),
    "Wii Mushroom Gorge (Nintendo)": ("MG", "キノキャニ"),
    "Wii Toad's Factory (Nintendo)": ("TF", "工場"),
    #Flower Cup
    "Wii Mario Circuit (Nintendo)":("MC", "マリサ"),
    "Wii Coconut Mall (Nintendo)": ("CM", "ココモ"),
    "Wii DK Summit (Nintendo)":(["DKS", "DKSC"], "スノボ"),
    "Wii Wario's Gold Mine (Nintendo)":("WGM", "鉱山"),
    #Star Cup
    "Wii Daisy Circuit (Nintendo)": ("DC", "デイサ"),
    "Wii Koopa Cape (Nintendo)": ("KC", "岬"),
    "Wii Maple Treeway (Nintendo)": ("MT", "メイプル"),
    "Wii Grumble Volcano (Nintendo)": ("GV", "火山"),
    #Special Cup
    "Wii Dry Dry Ruins (Nintendo)": ("DDR", "遺跡"),
    "Wii Moonview Highway (Nintendo)": (["MvH", "MH"], "ムンリ"),
    "Wii Bowser's Castle (Nintendo)": "BCWii",
    "Wii Rainbow Road (Nintendo)": ("RR", "虹"),
    #Shell Cup
    "GCN Peach Beach (Nintendo)": (["rPB","PB"], "ピーチビーチ"),
    "DS Yoshi Falls (Nintendo)": (["rYF", "YF"], "ヨシフォ"),
    "SNES Ghost Valley 2 (Nintendo)": (["GV2", "rGV2"], "沼"),
    "N64 Mario Raceway (Nintendo)": ("rMR", "64マリサ"),
    #Banana Cup
    "N64 Sherbet Land (Nintendo)": (["rSL", "SL"], "シャベラン"),
    "GBA Shy Guy Beach (Nintendo)": ("SGB", "兵浜"),
    "DS Delfino Square (Nintendo)": (["rDS", "DSDS"], "モンテ"),
    "GCN Waluigi Stadium (Nintendo)": (["rWS", "WS"], "ワルスタ"),
    #Leaf Cup
    "DS Desert Hills (Nintendo)": (["rDH", "DH"], "さばく"),
    "GBA Bowser Castle 3 (Nintendo)": "BC3",
    "N64 DK's Jungle Parkway (Nintendo)": (["rJP","rDKJP", "DKJP", "JP"], "ジャンパ"),
    "GCN Mario Circuit (Nintendo)": (["GCN MC", "rMC"], "GCマリサ"),
    #Lightning Cup
    "SNES Mario Circuit 3 (Nintendo)": ("MC3", "SFCマリサ"),
    "DS Peach Gardens (Nintendo)": (["rPG", "PG"], "ピチガ"),
    "GCN DK Mountain (Nintendo)": ("DKM", "山"),
    "N64 Bowser's Castle (Nintendo)": (["BC64", "rBC"], "64BC")
    }

sha_track_name_mappings = {"9f09ddb05bc5c7b04bb7aa120f6d0f21774143eb":"Waluigi's Motocross (v1.9)"}

def get_track_name_lookup(track_name):
    return track_name.replace(" ","").lower()

def remove_author_and_version_from_name(track_name):
    if track_name is None or track_name == "None":
        return "No track"
    tempName = track_name.strip()
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

def initialize():
    sha_track_name_mappings.clear()
    sha_track_name_mappings.update(common.load_pkl(common.SHA_TRACK_NAMES_FILE, "Could not load in SHA Track names. Using empty dict instead", default=dict))

def save_data():
    common.dump_pkl(sha_track_name_mappings, common.SHA_TRACK_NAMES_FILE, "Could not dump pkl for SHA Track names.", display_data_on_error=True)
    
def on_exit():
    save_data()

def set_ctgp_region(new_region:str):
    global CTGP_CTWW_REGION
    CTGP_CTWW_REGION = new_region
    
class Race:
    '''
    classdocs
    '''

    def __init__(self, matchTime, matchID, raceNumber, roomID, roomType, cc, track, is_ct, mkwxRaceNumber, rxx=None, raceID=None, trackURL=None, placements=None, is_wiimmfi_race=True):
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
        self.placements: List[Placement] = []
        self.region = UNKNOWN_REGION
        self.is_ct = is_ct
        self.is_wiimmfi_race = is_wiimmfi_race
        self.mkwxRaceNumber = mkwxRaceNumber
        if UtilityFunctions.isint(self.mkwxRaceNumber):
            self.mkwxRaceNumber = int(self.mkwxRaceNumber)
        else:
            self.mkwxRaceNumber

        self.created_when_str = None
        self.last_start_str = None
    
    def get_mkwx_race_number(self):
        return self.mkwxRaceNumber
    def get_match_start_time(self):
        return self.matchTime
    def get_match_id(self):
        return self.matchID
    def get_race_number(self):
        return self.raceNumber
    def set_race_number(self, race_number):
        self.raceNumber = race_number
    def get_room_name(self):
        return self.roomID
    def get_rxx(self):
        return self.rxx
    def get_track_url(self):
        return self.trackURL
    def get_race_id(self):
        return self.raceID
    def get_room_type(self):
        return self.roomType
    def get_track_name(self):
        return self.track
    def get_cc(self):
        return self.cc
    def get_region(self):
        return self.region
    def is_from_wiimmfi(self):
        return self.is_wiimmfi_race
    
    def get_race_size(self):
        """Return number of players in race"""
        return self.numRacers()
    
    def track_check(self):
        if len(self.track) > 0 and UtilityFunctions.is_hex(self.track):
            common.log_error(f"The following track had no SHA mapping: {self.track}")
            
    def hasFC(self, FC):
        return False if self.getPlacement(FC) is None else True
        
    def update_FC_mii_hex(self, FC, mii_hex: str):
        for placement in self.placements:
            player = placement.get_player()
            if player.get_FC() == FC:
                player.set_mii_hex(mii_hex)

    def numRacers(self):
        if (self.placements is None):
            return 0
        return len(self.placements)

    def get_players_in_race(self):
        """Return players in this race (in order by finishing position)"""
        for placement in self.placements:
            yield placement.get_player()
    
    def update_region(self):
        regionCount = defaultdict(int)
        for placement in self.getPlacements():
            regionCount[placement.getPlayer().region] += 1
        if len(regionCount) == 0:
            self.region = UNKNOWN_REGION
        mostCommonRegion = max(regionCount, key=lambda x: regionCount[x])
        self.region = mostCommonRegion
            
    def addPlacement(self, placement: Placement):
        if len(self.placements) == 0:
            self.placements.append(placement)
        else:
            i = self.__findPlacementIndex(placement)
            self.placements.insert(i, placement)
        
        for i in range(0, len(self.placements)):
            self.placements[i].place = i+1

        self.update_region()
    
    def __findPlacementIndex(self, placement: Placement): 
        left = 0
        right = len(self.placements)-1
        mid = (right+left)//2

        while right-left > 0:
            if self.placements[mid] > placement: 
                right = mid - 1
            elif self.placements[mid] < placement:
                left = mid + 1
            else:
                return len(self.placements)-1 - self.placements[::-1].index(placement)
            
            mid = (right+left)//2
        
        mid = max(0, min(len(self.placements)-1, mid))
        
        return mid+1 if placement>=self.placements[mid] else mid

    
    def remove_placement_by_FC(self, FC):
        for ind, placement in enumerate(self.placements):
            if placement.player.FC == FC:
                self.placements.pop(ind)
                for placement in self.placements[ind:]:
                    placement.place-=1
                return
         
    def setRegion(self, region):
        self.region = region
        
    
    def isCTGPWW(self):
        return self.region == CTGP_CTWW_REGION
    
    def isRTWW(self):
        return self.region == RT_WW_REGION
    
    def isBattleWW(self):
        return self.region == BATTLE_REGION
    
    def isPrivateRoom(self):
        return self.region == PRIVATE_ROOM_REGION
    
    def isUnknownRegion(self):
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

    def set_placement_changes(self, player_fcs: List[str]):
        self.placements = sorted(self.placements, key=lambda p: player_fcs.index(p.get_fc()))
        for place, placement in enumerate(self.placements, start=1):
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
        return remove_author_and_version_from_name(self.track)
    
    def hasTie(self):
        for placement_1 in self.placements:
            for placement_2 in self.placements:
                if placement_1.player.FC != placement_2.player.FC and placement_1 == placement_2:
                    return True
        return False
    
    def getTies(self):
        ties = {}
        for placement_1 in self.placements:
            for placement_2 in self.placements:
                if placement_1.player.FC != placement_2.player.FC and placement_1 == placement_2\
                and not placement_1.is_bogus_time() and not placement_2.is_bogus_time()\
                and not placement_1.is_disconnected() and not placement_1.is_disconnected():
                    if placement_1.time not in ties:
                        ties[placement_1.time] = []
                    if placement_1.player.FC not in ties[placement_1.time]:
                        ties[placement_1.time].append(placement_1.player.FC)
                    if placement_2.player.FC not in ties[placement_1.time]:
                        ties[placement_1.time].append(placement_2.player.FC)       
        return ties
    
    def get_placement_times_as_set(self) -> set:
        return set(placement.get_time() for placement in self.placements)
    
    def get_sorted_valid_times(self):
        return sorted([place.get_time() for place in self.placements if not place.is_bogus_time()])
    
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
        
    
    def FCInPlacements(self, FC):
        for placement in self.placements:
            if placement.player.FC == FC:
                return True
        return False
    
    def getAbbreviatedName(self):
        if self.track in track_name_abbreviation_mappings:
            track_mapping = track_name_abbreviation_mappings[self.track]
            if isinstance(track_mapping, tuple):
                if isinstance(track_mapping[0], list):
                    return track_mapping[0][0] + " (" + track_mapping[1] + ")"
                return track_mapping[0] + " (" + track_mapping[1] + ")"
            else:
                return track_mapping
                
        return self.getTrackNameWithoutAuthor()
    
    def getWWTypeName(self):
        if self.region is None:
            return ""
        
        if self.region == CTGP_CTWW_REGION:
            return "CTWW (CTGP)"
        if self.region == RT_WW_REGION:
            return "WW"
        if self.region == BATTLE_REGION:
            return "Battle WW"
        if self.region == PRIVATE_ROOM_REGION:
            return "Private Room"
        return "Unknown"
    
    @staticmethod
    def getWWFullName(region):
        if region is None:
            return ""
        if region == CTGP_CTWW_REGION:
            return "CTGP Custom Track Worldwide"
        if region == RT_WW_REGION:
            return "Regular Track Worldwide"
        if region == BATTLE_REGION:
            return "Battle Worldwide"
        if region == PRIVATE_ROOM_REGION:
            return "Private"
        return "Unknown"
    
    def is_custom_track(self):
        return self.is_ct
    
    def hasBlankTime(self):
        return any(placement.is_disconnected() for placement in self.getPlacements())
    
    def entireRoomBlankTimes(self):
        return all(placement.is_disconnected() for placement in self.getPlacements())
    
    def multipleBlankTimes(self):
        return not self.entireRoomBlankTimes() and sum(1 for placement in self.getPlacements() if placement.is_disconnected()) > 1
        
    def get_team_points_string(self, teams_data, server_id):
        team_placements = defaultdict(list)
        for placement in self.placements:
            tag = teams_data[placement.player.FC]
            team_placements[tag].append(placement.place)
        
        score_mat = common.alternate_Matrices[server_id] if server_id in common.alternate_Matrices else common.scoreMatrix
        score_matrix = score_mat[len(self.placements)-1]
        team_placements = dict(sorted(team_placements.items(), key=lambda team: sum(score_matrix[p-1] for p in team[1]), reverse=True))

        ret = []
        for team, placements in team_placements.items():
            r = f"**{team}** - " + ", ".join(list(map(str, placements)))
            pts_sum = sum(score_matrix[p-1] for p in placements)
            r+=f" (**{pts_sum}** {'pt' if pts_sum==1 else 'pts'})"
            ret.append(r)

        return '\n\n'+"  |  ".join(ret)

    def __str__(self):
        curStr = "Race #" + str(self.raceNumber) + " - " + UtilityFunctions.clean_for_output(self.getTrackNameWithoutAuthor()) + " - " + str(self.cc) + "cc" + \
         "\nMatch end time: " + str(self.matchTime)
        placementsSTR = ""
        for placement in self.placements:
            placementsSTR += str("\n\t" + str(placement))
        return curStr + placementsSTR
            

        