'''
Created on Jul 12, 2020

@author: willg
'''
import random
from collections import defaultdict
from copy import copy, deepcopy
from typing import Any, DefaultDict, Dict, List, Set, SupportsIndex, Tuple, Union


import ErrorChecker
import Placement
import Player
import common
import MiiPuller
import Mii
import Race
import TableBotExceptions
import TagAIShell
import UserDataProcessing
import UtilityFunctions
import WiimmfiSiteFunctions



TWO_TEAM_TABLE_COLOR_PAIRS = [("#244f96", "#cce7e8"),
                              ("#D11425", "#E8EE28"),
                              ("#E40CA6", "#ADCFCD"),
                              ("#2EFF04", "#FF0404"),
                              ("#193FFF", "#FF0404"),
                              ("#ff8cfd", "#fdff8c"),
                              ("#96c9ff", "#ffbe96"),
                              ("#ffbbb1", "#b1ffd9"),
                              ("#ff69b4", "#b4ff69"),
                              ("#95eefa", "#58cede"),
                              ("#54ffc9", "#54e3ff"),
                              ("#a1ff3d", "#fcff3d"),
                              ("#8d8ce6", "#cfceff")]

class ROOM_LOAD_STATUS_CODES():
    DOES_NOT_EXIST = object()
    HAS_NO_RACES = object()
    NO_ROOM_LOADED = object()
    SUCCESS = object()
    FAILURE_CODES = {DOES_NOT_EXIST, HAS_NO_RACES, NO_ROOM_LOADED}
    SUCCESS_CODES = {SUCCESS}

# Function takes a default dictionary, the key being a number, and makes any keys that are greater than the threshold one less, then removes that threshold, if it exists
def generic_dictionary_shifter(old_dict, threshold: int) -> DefaultDict[int, Any]:
    new_dict = defaultdict(old_dict.default_factory)
    for k, v in old_dict.items():
        if k == threshold:
            continue
        if k > threshold:
            new_dict[k-1] = v
        else:
            new_dict[k] = v
    return new_dict

class Table(List):
    '''
    classdocs
    '''
    def __init__(self, rxx: str, races: List[Race.Race], setup_discord_id, setup_display_name: str) -> List[Race.Race]:
        super().__init__()
        self.name_changes = {}
        self.removed_races = []

        # Key will be the race number, value will be a list of all the placements changed for the race
        self.placement_history = defaultdict(list)

        # Dictionary - key is race number, value is the number of players for the race that the tabler specified
        # This contains the races that have their size changed by the tabler - when a race is removed, we
        # need to change all the LATER races (the races that happened after the removed race) down by one race
        self.forcedRoomSize = defaultdict(int)

        self.playerPenalties = defaultdict(int)

        # For each race, holds dict that holds (FC, player_name) with 'on' or 'before' being the value
        self.dc_on_or_before = defaultdict(dict)
        self.set_up_user = setup_discord_id
        self.set_up_user_display_name = setup_display_name
        # dictionary of fcs that subbed in with the values being lists: fc: [subinstartrace, subinendrace, suboutfc, suboutname, suboutstartrace, suboutendrace, [suboutstartracescore, suboutstartrace+1score,...]]
        self.sub_ins = {}
        self.is_freed = False

        self.miis: Dict[str, Mii.Mii] = {}

        self.set_up([rxx], races)
        
    
    def get_set_up_user_discord_id(self):
        return self.set_up_user

    def get_set_up_display_name(self):
        return self.set_up_user_display_name

    def get_dc_statuses(self):
        return self.dc_on_or_before

    def get_subs(self):
        return self.sub_ins

    def get_miis(self) -> Dict[str, Mii.Mii]:
        return self.miis

    def get_races(self) -> List[Race.Race]:
        return self


    def remove_miis_with_missing_files(self):
        to_delete = set()
        for fc, mii in self.get_miis().items():
            if not mii.has_table_picture_file():
                common.log_error(f"{fc} does not have a mii picture - channel {self.channel_id}")
                to_delete.add(fc)

        for fc in to_delete:
            try:
                self.get_miis()[fc].clean_up()
                del self.get_miis()[fc]
            except:
                common.log_error(f"Exception in remove_miis_with_missing_files: {fc} failed to clean up - channel {self.channel_id}")

    async def populate_miis(self):
        if common.MIIS_ON_TABLE_DISABLED:
            return
        #print("\n\n\n" + str(self.get_miis()))
        if self.get_war() is not None:
            if self.populating:
                return
            self.populating = True
            #print("Start:", datetime.now())
            try:
                if self.get_table() is not None:
                    self.remove_miis_with_missing_files()
                    all_fcs_in_room = self.get_table().get_room_FCs()
                                        
                    if all_fcs_in_room != self.get_miis().keys():
                        all_missing_fcs = [fc for fc in self.get_table().get_room_FCs() if fc not in self.get_miis()]
                        result = await MiiPuller.get_miis(all_missing_fcs, self.get_event_id())
                        if not isinstance(result, (str, type(None))):
                            for fc, mii_pull_result in result.items():
                                if not isinstance(mii_pull_result, (str, type(None))):
                                    self.get_miis()[fc] = mii_pull_result
                                    mii_pull_result.output_table_mii_to_disc()
                                    mii_pull_result.__remove_main_mii_picture__()
                                
                    for mii in self.get_miis().values():
                        if mii.lounge_name == "":
                            mii.update_lounge_name()
            finally:
                #print("End:", datetime.now())
                self.populating = False

    def get_available_miis_dict(self, FCs) -> Dict[str, Mii.Mii]:
        return {fc: self.get_miis()[fc] for fc in FCs if fc in self.get_miis()}

    def set_up(self, rxxs: List[str], races: List[Race.Race], mii_dict=None):
        if not isinstance(rxxs, list) or len(rxxs) == 0 or any(not isinstance(rxx, str) for rxx in rxxs):
            raise ValueError("Caller must gaurantee that the given rxxs is a non-empty list of strings")
        if not isinstance(races, list) or len(races) == 0 or any(not isinstance(race, Race.Race) for race in races):
            raise ValueError("Caller must gaurantee that the given races is a non-empty list of Races")
        self.rxxs = rxxs
        self.set_races(races)
        self.fix_race_numbers()
        self._room_name = self[0].get_room_name()
        
    def get_rxxs(self) -> List[str]:
        return self.rxxs
    
    def had_positions_changed(self) -> bool:
        '''Returns True if any of the race's placements were changed'''
        return any(changes for changes in self.placement_history.values())
    
    def placements_changed_for_racenum(self, race_num: int) -> bool:
        '''Returns True if race for the given race number's placements were changed'''
        return race_num in self.placement_history and self.placement_history[race_num]
    
    def changePlacement(self, race_num, player_FC, new_placement):
        #We need to get their original placement on the race
        original_placement = self[race_num-1].getPlacementNumber(player_FC)
        position_change = (original_placement, new_placement)
        self.placement_history[race_num].append(position_change)        
        self[race_num-1].applyPlacementChanges([position_change])


    def had_subs(self):
        return len(self.sub_ins) != 0
    
    def fc_subbed_out(self, fc):
        return self.get_sub_in_fc_for_subout_fc(fc) is not None
    
    def get_sub_in_fc_for_subout_fc(self, suboutfc):
        for fc, sub_data in self.sub_ins.items():
            if suboutfc == sub_data[2]:
                return fc
        return None
    
    def get_sub_out_for_subbed_in_fc(self, subInFC, race_num):
        if subInFC not in self.sub_ins:
            return None, None
        suboutStartRace = self.sub_ins[subInFC][4]
        suboutEndRace = self.sub_ins[subInFC][5]
        if race_num >= suboutStartRace and race_num <= suboutEndRace:
            return subInFC, self.sub_ins[subInFC][6][race_num-suboutStartRace]
        return subInFC, None
    
    def get_sub_string(self, subin_name, subin_fc):
        if not self.fc_subbed_in(subin_fc):
            return subin_name
        
        subinStartRace = self.sub_ins[subin_fc][0]
        subinEndRace = self.sub_ins[subin_fc][1]
        #suboutFC = self.sub_ins[subin_fc][2]
        suboutName = self.sub_ins[subin_fc][3]
        suboutStartRace = self.sub_ins[subin_fc][4]
        suboutEndRace = self.sub_ins[subin_fc][5]
        return f"{suboutName}({suboutEndRace-suboutStartRace+1})/{subin_name}({subinEndRace-subinStartRace+1})"
    
    def fc_subbed_in(self, fc):
        return fc in self.sub_ins
        
    def get_subin_error_string_list(self, race_num):
        sub_str_list = []
        for sub_in_fc, sub_data in self.sub_ins.items():
            subInStartRace = sub_data[0]
            if race_num != subInStartRace:
                continue
            
            subInName = self.getMiiNameByFC(sub_in_fc) + UserDataProcessing.lounge_add(sub_in_fc)
            if sub_in_fc in self.getNameChanges():
                subInName = self.getNameChanges()[sub_in_fc]
            suboutName = sub_data[3]
            sub_str_list.append(f"Tabler subbed in {UtilityFunctions.filter_text(subInName)} for {UtilityFunctions.filter_text(suboutName)} this race")
        return sub_str_list
    
    def add_sub(self, subInFC, subInStartRace, subInEndRace, subOutFC, subOutName, subOutStartRace, subOutEndRace, subOutScores):
        #dictionary of fcs that subbed in with the values being lists: fc: [subinstartrace, subinendrace, suboutfc, suboutname, suboutstartrace, suboutendrace, [suboutstartracescore, suboutstartrace+1score,...]]
        self.sub_ins[subInFC] = [subInStartRace, subInEndRace, subOutFC, subOutName, subOutStartRace, subOutEndRace, subOutScores]
        self.setNameForFC(subOutFC, f"#subbed out: {subOutName}")
        
    
    #Outside caller should use this, it will add the removed race to the class' history
    #Okay, final step: when we remove a race, whatever room size changes and quickedits and dc_on_or_before for races after the removed race need to all shift down by one
    def remove_race(self, race_num):
        race_index = race_num - 1
        if race_index >= 0 and race_index < len(self):
            race_name = self.pop(race_num).getTrackNameWithoutAuthor()
            self.removed_races.append((race_index, race_name))
            #Update dcs, quickedits, and room size changes, and subin scores
            self.forcedRoomSize = generic_dictionary_shifter(self.forcedRoomSize, race_num)
            self.dc_on_or_before = generic_dictionary_shifter(self.dc_on_or_before, race_num)
            self.placement_history = generic_dictionary_shifter(self.placement_history, race_num)
            for sub_data in self.sub_ins.values():
                subout_start_race = sub_data[4]
                subout_end_race = sub_data[5]
                if race_num >= subout_start_race and subout_start_race <= subout_end_race: #2, 3, 4
                    sub_data[6].pop(subout_start_race - race_num)
                    sub_data[5] -= 1
                    sub_data[0] -= 1
                        
            return True, (race_index, race_name)
        return False, None
    
    def __remove_race__(self, index):
        return self.pop(index)
    
    def get_removed_races_string(self):
        removed_str = ""
        for raceInd, raceName in self.removed_races:
            removed_str += "- " + raceName + " (originally race #" + str(raceInd+1) + ") removed by tabler\n"
        return removed_str
    
    #Should only call if you know the data for an FC among the placements will be unique
    def getFCPlacements(self, startrace=1,endrace=None):
        fcPlacementDict = {}
        if endrace is None:
            endrace = len(self.get_races())
        for race in self.get_races()[startrace-1:endrace]:
            for placement in race.getPlacements():
                fcPlacementDict[placement.get_player().get_FC()] = placement
        return fcPlacementDict

    
    def getFCPlayerList(self, startrace=1,endrace=12):
        fcNameDict = {}
        if endrace is None:
            endrace = len(self.get_races())
        for race in self.get_races()[startrace-1:endrace]:
            for placement in race.getPlacements():
                FC, name = placement.get_fc_and_name()
                fcNameDict[FC] = name
        return fcNameDict
    
    def getFCPlayerListString(self, startrace=1,endrace=12, lounge_replace=True):
        FCPL = self.getFCPlayerList(startrace, endrace)
        to_build = ""
        for fc, name in FCPL.items():
            to_build += fc + ": " + UtilityFunctions.filter_text(name) + UserDataProcessing.lounge_add(fc, lounge_replace) + "\n"
        return to_build
    
    def getPlayerPenalities(self):
        return self.playerPenalties
        
    def addPlayerPenalty(self, fc, amount):
        self.playerPenalties[fc] += amount
        
    
    def getFCPlayerListStartEnd(self, startRace, endRace):
        fcNameDict = {}
        for raceNumber, race in enumerate(self.get_races(), 1):
            if raceNumber >= startRace and raceNumber <= endRace: 
                for placement in race.getPlacements():
                    FC, name = placement.get_fc_and_name()
                    fcNameDict[FC] = name
        return fcNameDict
    
    def getMiiNameByFC(self, FC):
        player_list = self.getFCPlayerList(endrace=None)
        if FC in player_list:
            return player_list[FC]
        return "no name"
    
    def get_known_region(self):
        regions = set(race.get_region() for race in self.get_races())
        if len(regions) != 1:
            return Race.UNKNOWN_REGION
        for region in regions:
            return region
        
            
            
    
    def fcIsInRoom(self, FC):
        return FC in self.get_room_FCs()       
    
    def getNameChanges(self):
        return self.name_changes
    
    def getRemovedRaces(self):
        return self.removed_races

    def getPlacementHistory(self):
        return self.placement_history
    
    def getForcedRoomSize(self):
        return self.forcedRoomSize
        
    def getPlayerPenalties(self):
        return self.playerPenalties
    
    def setNameForFC(self, FC, name):
        self.name_changes[FC] = name
    
    def get_room_FCs(self):
        return self.getFCPlayerList(endrace=None).keys()
    
    def getPlayers(self):
        return self.getFCPlayerList(endrace=None).values()
    
            
    def set_races(self, races):
        self.clear()
        self.extend(races)
    
    
    def getRXXText(self):
        resultText = ""
        if len(self.rxxs) == 1:
            rxx = self.rxxs[0]
            resultText = f"**Room URL:** https://wiimmfi.de/stats/mkwx/list/{rxx}  |  **rxx number:** {rxx}\n"
        else:
            resultText = "**?mergeroom** was used, so there are multiple rooms:\n\n"
            for i, rxx in enumerate(self.rxxs[::-1], 1):
                resultText += f"**- Room #{i} URL:** https://wiimmfi.de/stats/mkwx/list/{rxx}  |  **rxx number:** {rxx}\n"
        return resultText
    
    def getLastRXXString(self):
        if len(self.rxxs) > 0:
            last_rxx = self.rxxs[0]
            return f"**Room URL:** https://wiimmfi.de/stats/mkwx/list/{last_rxx}  |  **rxx number:** {last_rxx}"
        return ""
    
    def getMissingPlayersPerRace(self):
        numGPS = int(len(self.get_races())/4 + 1)
        GPPlayers = []
        missingPlayers = []
        for GPNum in range(numGPS):
            GPPlayers.append(self.getFCPlayerListStartEnd((GPNum*4)+1, (GPNum+1)*4))
        
        for raceNum, race in enumerate(self.get_races()):
            thisGPPlayers = GPPlayers[int(raceNum/4)]
            missingPlayersThisRace = []
            if raceNum % 4 != 0: #not the start of the GP:
                for fc, player in thisGPPlayers.items():
                    if fc not in race.get_race_FCs():
                        missingPlayersThisRace.append((fc, player))
            missingPlayers.append(missingPlayersThisRace)
        return missingPlayers
    
    def getMissingOnRace(self, numGPS):
        GPPlayers = []
        missingPlayers = []
        for GPNum in range(numGPS):
            GPPlayers.append(self.getFCPlayerListStartEnd((GPNum*4)+1, (GPNum+1)*4))
        
        wentMissingThisGP = []
        for raceNum, race in enumerate(self.get_races()[0:numGPS*4]):
            if raceNum/4 >= len(GPPlayers): #To avoid any issues if they put less GPs than the room has
                break
            thisGPPlayers = GPPlayers[int(raceNum/4)]
            missingPlayersThisRace = []
            if raceNum % 4 == 0:
                wentMissingThisGP = []
            
            if raceNum % 4 != 0: #not the start of the GP:
                for fc, player in thisGPPlayers.items():
                    if fc not in race.get_race_FCs() and fc not in wentMissingThisGP:
                        wentMissingThisGP.append(fc)
                        missingPlayersThisRace.append((fc, player))
            missingPlayers.append(missingPlayersThisRace)
        for missingPlayersOnRace in missingPlayers:
            missingPlayersOnRace.sort()
        return missingPlayers
    
    
    def getDCListString(self, num_of_GPs=3, replace_lounge=True):
        missingPlayersByRace = self.getMissingOnRace(num_of_GPs)
        missingPlayersAmount = sum([len(x) for x in missingPlayersByRace])
        if missingPlayersAmount == 0:
            last_race = self.get_races()[-1]
            return False, "No one has DCed. Last race: " + str(last_race.track) + " (Race #" + str(last_race.raceNumber) + ")"
        else:
            counter = 1
            build_string = "*Disconnection List:*\n"
            for raceNum, missing_players in enumerate(missingPlayersByRace, 1):
                for fc, player in sorted(missing_players):
                    build_string += "\t" + str(counter) + ". **"
                    build_string += UtilityFunctions.filter_text(player) + UserDataProcessing.lounge_add(fc, replace_lounge) + "** disconnected on or before race #" + str(raceNum) + " (" + str(self.get_races()[raceNum-1].getTrackNameWithoutAuthor()) + ")\n"
                    counter+=1
            return True, build_string
    
    def getPlayerAtIndex(self, index):
        player_list = self.get_sorted_player_list()
        try:
            return player_list[index]
        except IndexError:
            raise
    
    #method that returns the players in a consistent, sorted order - first by getTagSmart, then by FC (for tie breaker)
    #What is returned is a list of tuples (fc, player_name)
    def get_sorted_player_list(self, startrace=1, endrace=12):
        players = list(self.getFCPlayerListStartEnd(startrace, endrace).items())
        return sorted(players, key=lambda x: (TagAIShell.getTag(x[1]), x[0]))
       
       
    def get_sorted_player_list_string(self, startrace=1, endrace=12, lounge_replace=True):
        players = self.get_sorted_player_list(startrace, endrace)
        to_build = ""
        for list_num, (fc, player) in enumerate(players, 1):
            to_build += str(list_num) + ". " + UtilityFunctions.filter_text(player) + UserDataProcessing.lounge_add(fc, lounge_replace) + "\n"
        return to_build
            
            
    def get_players_list_string(self, startrace=1, endrace=12, lounge_replace=True):
        player_list = self.get_sorted_player_list(startrace, endrace)
        build_str = ""
        for counter, (fc, player) in enumerate(player_list, 1):
            build_str += str(counter) + ". " + UtilityFunctions.filter_text(player)
            if lounge_replace:
                build_str += UserDataProcessing.lounge_add(fc, lounge_replace)
            build_str += "\n"
        return build_str
    
    

    def update_mii_hexes(self: List[Race.Race]):
        for race in self:
            for FC, mii_hex in self.get_miis().items():
                race.update_FC_mii_hex(FC, mii_hex)

    #Soup level functions    
    async def update(self, database_call):
        all_races = []
        for rxx in self.rxxs:
            _, new_races = await WiimmfiSiteFunctions.get_races_for_rxx(rxx)
            all_races.extend(new_races)

        if len(all_races) == 0:
            return ROOM_LOAD_STATUS_CODES.HAS_NO_RACES
        self.set_races(all_races)
        self.update_mii_hexes()
        return ROOM_LOAD_STATUS_CODES.SUCCESS

    def fix_race_numbers(self):
        for race_num, race in enumerate(self.get_races(), 1):
            race.set_race_number(race_num)
    
    def apply_tabler_adjustments(self):
        #First, we number all races
        self.fix_race_numbers()
            
        #Next, apply name changes
        for FC, name_change in self.name_changes.items():
            for race in self.get_races():
                for placement in race.getPlacements():
                    if placement.get_player().get_FC() == FC:
                        placement.get_player().set_name(f"{name_change} (Tabler Changed)")
        
        #Next, we remove races
        for removed_race_ind, _ in self.removed_races:
            self.pop(removed_race_ind)
        
        #Next, we need to renumber the races
        self.fix_race_numbers()
        
        #Next, we apply quick edits
        for race_number, race in enumerate(self, 1):
            if race_number in self.placement_history:
                race.applyPlacementChanges(self.placement_history[race_number])
        
    def getRacesPlayed(self):
        return [r.track for r in self]
    
    def get_races_abbreviated(self, last_x_races=None):
        if last_x_races is None:
            temp = []
            for ind,race in enumerate(self.get_races(), 1):
                if race.getAbbreviatedName() is None:
                    return None
                temp.append(str(ind) + ". " + race.getAbbreviatedName())
            return " | ".join(temp)
        else:
            temp = []
            for ind,race in enumerate(self.get_races()[-last_x_races:], 1):
                if race.getAbbreviatedName() is None:
                    return None
                temp.append(str(ind) + ". " + race.getAbbreviatedName())
            return " | ".join(temp)
        
    
    def get_races_string(self, races=None):
        if races is None:
            races = self.getRacesPlayed()
        string_build = ""
        num = 1
        for race in races:
            string_build += "Race #" + str(num) + ": " + race + "\n"
            num += 1
        if len(string_build) < 1:
            string_build = "No races played yet."
        return UtilityFunctions.filter_text(string_build)
    
    def get_loungenames_in_room(self):
        all_fcs = self.get_room_FCs()
        lounge_names = []
        for FC in all_fcs:
            lounge_name = UserDataProcessing.lounge_get(FC)
            if lounge_name != "":
                lounge_names.append(lounge_name)
        return lounge_names
    
    def get_loungenames_can_modify_table(self):
        can_modify = self.get_loungenames_in_room()
        if self.set_up_user_display_name is not None and self.set_up_user_display_name != "":
            can_modify.append(str(self.set_up_user_display_name))
        elif self.set_up_user is not None:
            can_modify.append(str(self.set_up_user))
        return can_modify
            
    
    def canModifyTable(self, discord_id:int):
        if self.is_freed or self.getSetupUser() == discord_id:
            return True
        discord_ids = [data[0] for data in self.getRoomFCDiscordIDs().values()]
        return str(discord_id) in discord_ids
        
    def getRoomFCDiscordIDs(self):
        FC_DID = {FC:(None, None) for FC in self.get_race_FCs()}
        for FC in FC_DID:
            if FC in UserDataProcessing.fc_discordId:
                FC_DID[FC] = UserDataProcessing.fc_discordId[FC]
        return FC_DID
        
    
    def getSetupUser(self):
        return self.set_up_user
    
    def setSetupUser(self, setupUser, displayName:str):
        self.freed = False
        self.set_up_user = setupUser
        self.set_up_user_display_name = displayName
    

    def forceRoomSize(self, raceNum, roomSize):
        self.forcedRoomSize[raceNum] = roomSize
    
    def getRoomSize(self, raceNum):
        if raceNum in self.forcedRoomSize:
            return self.forcedRoomSize[raceNum]
       
    #This is not the entire save state of the class, but rather, the save state for edits made by the user 
    def get_recoverable_save_state(self):
        save_state = {}
        save_state['name_changes'] = self.name_changes.copy()
        save_state['removed_races'] = self.removed_races.copy()
        save_state['playerPenalties'] = self.playerPenalties.copy()
        
        #for each race, holds fc_player dced that race, and also holds 'on' or 'before'
        save_state['dc_on_or_before'] = self.dc_on_or_before.copy()
        save_state['forcedRoomSize'] = self.forcedRoomSize.copy()
        save_state['rxxs'] = self.rxxs.copy()
        save_state['races'] = deepcopy([race for race in self])
        save_state['placement_history'] = copy(self.placement_history)
        save_state['sub_ins'] = deepcopy(self.sub_ins)
        
        return save_state
    
    def restore_save_state(self, save_state):
        for save_attr, save_value in save_state.items():
            if save_attr != "races":
                self.__dict__[save_attr] = save_value
        self.set_races(save_state["races"])

    def insert(self, __index: SupportsIndex, __object: Any) -> None:
        if not isinstance(__object, Race.Race):
            raise TypeError(f"Can only append races, cannot append {type(__object)}")
        return super().insert(__index, __object)

    def append(self, __object: Any) -> None:
        if not isinstance(__object, Race.Race):
            raise TypeError(f"Can only append races, cannot append {type(__object)}")
        return super().append(__object) 

                




































class War(object):
    '''
    War objects contain user defined meta information. The information in Wars is used to morph how Rooms look, though overtime, morphing how Rooms look has spread to other classes too.
    '''
    GP_SIZE = 4

    _war_format_players_per_team = {u"ffa": 1, u"1v1": 1, u"2v2": 2,
                                    u"3v3": 3, u"4v4": 4, u"5v5": 5, u"6v6": 6}

    def __init__(self, format_: str, number_of_teams: str, num_of_GPs=3,
                 race_points_when_missing=3, show_large_time_errors=True, display_miis=True):
        self._set_team_colors(None)
        self.set_teams(None)
        self._war_format_setup(format_, number_of_teams)
        self.set_number_of_gps(num_of_GPs)
        self.set_user_set_war_name(None)
        self.set_race_points_when_missing(race_points_when_missing)
        self._set_edited_scores(dict())
        self.set_show_large_time_errors(show_large_time_errors)
        self.set_display_miis(display_miis)
        self._set_team_penalties(defaultdict(int))
        self.set_temporary_tag_fcs(None)


    # Getters
    def get_team_colors(self) -> Tuple[str, str]:
        return self._team_colors

    def get_teams(self) -> Dict[str, str]:
        '''returns a dictionary of FCs, each FC is mapped to its tag'''
        return self._teams

    def get_user_defined_num_of_gps(self) -> int:
        return self._number_of_GPs

    def get_user_defined_num_of_races(self) -> int:
        return self.get_user_defined_num_of_gps() * War.GP_SIZE

    def get_user_defined_war_name(self) -> str:
        return self._user_defined_war_name

    def get_race_points_when_missing(self) -> int:
        return self._race_points_when_missing

    def get_edited_scores(self) -> Dict[str, Tuple[int, int]]:
        '''Returns a dictionary of FCs mapped to a List of Tuples.
        Each Tuple contains the GP number in the first index,
        and the edited score for that GP in the second index'''
        return self._edited_scores

    def should_show_large_time_errors(self) -> bool:
        return self._show_large_time_errors

    def display_miis(self) -> bool:
        return self._display_miis

    def get_team_penalties(self) -> DefaultDict[str, int]:
        '''Returns a default dict: team tag mapped to the penalty for the team'''
        return self._team_penalties

    def get_user_defined_war_format(self) -> str:
        return self._user_defined_war_format

    def get_user_defined_num_of_teams(self) -> int:
        return self._user_defined_number_of_teams
    
    def get_user_defined_players_per_team(self) -> int:
        return self._user_defined_players_per_team

    def get_user_defined_num_players(self) -> int:
        return self.get_user_defined_num_of_teams()*self.get_user_defined_players_per_team()

    def is_FFA(self) -> bool:
        return self.get_user_defined_players_per_team() == 1


    # Setters
    def _set_team_colors(self, team_colors: Tuple[str, str]):
        self._team_colors = team_colors

    def set_teams(self, teams: Dict[str, str]):
        '''teams is a dictionary of FCs, each FC having a tag'''
        self._teams = teams

    def set_number_of_gps(self, number_of_GPs: int):
        self._number_of_GPs = number_of_GPs

    def set_user_set_war_name(self, war_name: str):
        self._user_defined_war_name = war_name

    def set_race_points_when_missing(self, race_points_when_missing: int):
        self._race_points_when_missing = race_points_when_missing

    def _set_edited_scores(self, edited_scores: Dict[str, Tuple[int, int]]):
        '''See get_edited_scores for more information'''
        self._edited_scores = edited_scores

    def set_show_large_time_errors(self, show_large_time_errors: bool):
        self._show_large_time_errors = show_large_time_errors

    def set_display_miis(self, display_miis: bool):
        self._display_miis = display_miis

    def _set_team_penalties(self, team_penalties: DefaultDict[str, int]):
        self._team_penalties = team_penalties

    def _set_user_defined_war_format(self, war_format: str):
        self._user_defined_war_format = war_format

    def _set_user_defined_number_of_teams(self, number_of_teams: int):
        self._user_defined_number_of_teams = number_of_teams

    def _set_user_defined_players_per_teams(self, players_per_team: int):
        self._user_defined_players_per_team = players_per_team

    def _war_format_setup(self, format_: str, number_of_teams: str):
        if format_ not in self._war_format_players_per_team:
            raise TableBotExceptions.InvalidWarFormatException()
        players_per_team = self._war_format_players_per_team[format_]

        if not UtilityFunctions.is_int(number_of_teams):
            raise TableBotExceptions.InvalidNumberOfPlayersException()
        number_of_teams = int(number_of_teams)

        if players_per_team * number_of_teams > 12:
            raise TableBotExceptions.InvalidNumberOfPlayersException()

        self._set_user_defined_war_format(format_)
        self._set_user_defined_number_of_teams(number_of_teams)
        self._set_user_defined_players_per_teams(players_per_team)
        if self.get_user_defined_num_of_teams() == 2:
            self._set_team_colors(random.choice(TWO_TEAM_TABLE_COLOR_PAIRS))


    # ========= Functions for looking up tags and FCs ==========
    def get_tag_for_FC(self, FC: str) -> str:
        '''Takes the tag for a given FC. If there is no tag for the FC, "NO TEAM" is returned'''
        if self.get_teams() is None:
            raise TableBotExceptions.WarSetupStillRunning()
        if FC in self.get_teams():
            return self.get_teams()[FC]
        return "NO TEAM"

    def set_tag_for_FC(self, FC: str, tag: str):
        '''Sets the given FC's tag to the specified tag.'''
        if self.get_teams() is None:
            raise TableBotExceptions.WarSetupStillRunning()
        self.get_teams()[FC] = tag

    def get_all_tags(self) -> Set[str]:
        '''Returns a set of all the tags - the tags returned are a combination of the accepted AI results and users defining tags for players'''
        if self.get_teams() is None:
            raise TableBotExceptions.WarSetupStillRunning()
        return set(self.get_teams().values())

    def get_FCs_for_tag(self, tag: str) -> List[str]:
        '''Returns a list of FCs whose tag is the specified tag'''
        if self.get_teams() is None:
            raise TableBotExceptions.WarSetupStillRunning()
        return [fc for fc, team_tag in self.get_teams().items() if team_tag == tag]


    # ===================== Functions for the setup related to starting a war/table =================
    def set_temporary_tag_fcs(self, tag_fcs: Dict[str, List[str]]):
        self._temporary_tags_fcs = tag_fcs

    def get_temporary_tag_fcs(self) -> Dict[str, List[str]]:
        '''Returns the temporary tag fcs are stored between the several commands used for starting the war.
        Currently, the temporary tag fcs are generated by the tag AI and are set when a user starts a new war (using ?sw command)
        Team tags are mapped to a list of FCs (that have that tag)'''
        return self._temporary_tags_fcs

    def get_temporary_tag_fcs_str(self) -> str:
        '''Returns a formatted string of the tags and the players for each tag based on what is in the temporary tag fcs.
           See get_temporary_tag_fcs function for more information on what the temporary tag fcs are.
           This is currently used to display the tag and player list after ?sw is run'''
        if self.get_temporary_tag_fcs() is None:
            return "None"

        result = ""
        cur_player_num = 0
        for team_tag, fc_players in self.get_temporary_tag_fcs().items():
            result += f"**Tag: {UtilityFunctions.filter_text(team_tag)}** \n"
            for fc, player_name in fc_players:
                cur_player_num += 1
                result += f"\t{cur_player_num}. {UtilityFunctions.filter_text(player_name)}{UserDataProcessing.lounge_add(fc)}\n"

        return result

    def converted_temporary_tag_fcs(self) -> Dict[str, str]:
        '''Converts the temporary tag fcs (stored between the several commands used for starting the war),
           to a dictionary with each FC mapped to its corresponding tag.
           Currently, the temporary tag fcs are generated by the tag AI'''
        fc_tags = {}
        for team_tag, team_players in self.get_temporary_tag_fcs().items():
            for fc, _ in team_players:
                fc_tags[fc] = team_tag
        return fc_tags

    # ================ Functions related to GP edits for players ===============
    def edit_player_gp_score(self, FC: str, gp_number: int, gp_score: int) -> None:
        '''Sets the score of the given FC for the given gp number'''
        if FC not in self.get_edited_scores():
            self.get_edited_scores()[FC] = {}

        self._remove_player_gp_edit(FC, gp_number)

        self.get_edited_scores()[FC][gp_number] = gp_score

    def _remove_player_gp_edit(self, FC: str, gp_number: int):
        '''If the given FC has an edit for the given GP, deletes that edit'''
        if FC in self.get_edited_scores() and gp_number in self.get_edited_scores()[FC]:
            del self.get_edited_scores()[FC][gp_number]

    def get_gp_score_edits(self, gp_num: int) -> Dict[str, int]:
        '''Returns a dictionary of FCs with their edited score for a given gp'''
        gp_edits = {}
        for FC, edits in self.get_edited_scores().items():
            if gp_num in edits:
                gp_edits[FC] = edits[gp_num]
        return gp_edits

    def get_player_gp_score_edit(self, FC: str, gp_num: int) -> Union[None, int]:
        '''If the given FC has an edited score for the given GP, returns that edited score.
           Otherwise (if the given FC does not have a score edit for that GP), returns None'''
        if FC in self.get_edited_scores() and gp_num in self.get_edited_scores()[FC]:
            return self.get_edited_scores()[FC][gp_num]

    # =================== Functions related to team penalties ==========================
    def add_penalty_for_tag(self, team_tag: str, penalty_amount: int) -> None:
        '''For a given tag, adds the specified penalty amount to the team's penalties'''
        self.get_team_penalties()[team_tag] += penalty_amount

    
    # =================== Functions related to possible errors in the room ==============
    def get_war_errors_text(self, room, replace_lounge=True, up_to_race=None) -> str:
        '''Returns formatted text for all of the errors that occurred in a room and war.
           Specify replace_lounge for lounge names to be added to the errors
           Specify up_to_race to ignore errors on races beyond up_to_race'''
        errors = ErrorChecker.get_war_errors_players(self, room, replace_lounge, show_large_time_errors=self.should_show_large_time_errors())
        if errors is None:
            return "Room not loaded."

        errors_no_large_times = ErrorChecker.get_war_errors_players(self, room, replace_lounge, show_large_time_errors=True)
        errors_large_times = ErrorChecker.get_war_errors_players(self, room, replace_lounge, show_large_time_errors=False)
        num_errors_no_large_times = sum([len(race_errors) for race_errors in errors_no_large_times.values()])
        num_errors_large_times = sum([len(race_errors) for race_errors in errors_large_times.values()])
        
        build_string = "Errors that might affect the table:\n"
        removed_race_string = room.get_removed_races_string()
        build_string += removed_race_string

        if not self.should_show_large_time_errors() and num_errors_no_large_times < num_errors_large_times:
            build_string += "- Large times occurred, but are being ignored. Table could be incorrect.\n"

        if up_to_race and up_to_race > 0:  # only show errors up to specified race if it was provided
            errors = {race_num: errors for (race_num, errors) in errors.items() if race_num <= up_to_race}

        elif len(errors) == 0 and len(removed_race_string) == 0:
            return "Room had no errors. Table should be correct."

        for race_num, error_messages in sorted(errors.items(), key=lambda x: x[0]):
            if race_num > len(room.get_races()):
                build_string += f"   Race #{race_num}:\n"
            else:
                track_name = room.get_races()[race_num-1].getTrackNameWithoutAuthor()
                build_string += f"   Race #{race_num} ({track_name}):\n"

            for error_message in error_messages:
                build_string += f"\t- {error_message}\n"
        return build_string


    def get_war_errors(self, room, lounge_replace=True):
        '''See ErrorChecker.get_war_errors_players'''
        return ErrorChecker.get_war_errors_players(self, room, lounge_replace, show_large_time_errors=False)


    def get_war_name_for_display(self, num_races: int) -> str:
        '''If the user has set a name for the table manually, that is returned.
           Otherwise, returns a string with the teams and the number of races played
           Currently, this is what is displayed as the Discord embed's title'''
        if self.get_teams() is None:
            raise TableBotExceptions.WarSetupStillRunning()
        if self.get_user_defined_war_name() is not None:
            return self.get_user_defined_war_name()
        
        all_teams = {"FFA"} if self.is_FFA() else set(self.get_teams().values())
        return " vs ".join(all_teams) + f": {self._user_defined_war_format} ({num_races} races)"

    def get_war_name_for_table(self, num_races: int) -> str:
        '''If the user has set a name for the table manually, that is returned.
           Otherwise, returns a string with the number of races played.
           Currently, this is sent to Lorenzi's website and is displayed at the top of the table picture'''
        if self.get_user_defined_war_name() is None:
            return f"{num_races} races"
        else:
            return self.get_user_defined_war_name()


    def clean_up(self):
        for mii in self.get_miis().values():
            mii.clean_up()
            
    def destroy(self):
        self.populating = True
        self.clean_up()
        self.populating = False

    # ================ Save state functions ===================
    def get_recoverable_save_state(self) -> Dict[str, Any]:
        save_state = {}
        save_state['_user_defined_war_name'] = self.get_user_defined_war_name()
        save_state['_edited_scores'] = self.get_edited_scores().copy()
        save_state['_team_penalties'] = self.get_team_penalties().copy()
        save_state['_teams'] = self.get_teams().copy()
        return save_state

    def restore_save_state(self, save_state):
        for save_attr, save_value in save_state.items():
            self.__dict__[save_attr] = save_value


    # ============== Debugging Functions ====================
    def _print_teams(self) -> None:
        if self.get_teams() is None:
            raise TableBotExceptions.WarSetupStillRunning()
        for tag in self.get_all_tags(self, self.get_teams()):
            print(tag + self.get_FCs_for_tag(tag))

    def __str__(self):
        return f"""-- WAR --
Number of teams: {self.get_user_defined_num_of_teams()}
Format: {self.get_user_defined_war_format()}
Number of players: {self.get_user_defined_num_players()}
"""
