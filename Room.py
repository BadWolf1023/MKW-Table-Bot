'''
Created on Jul 12, 2020

@author: willg
'''
import Race
import Placement
import Player
import WiimfiSiteFunctions
import UserDataProcessing

from _collections import defaultdict
import UtilityFunctions
from TagAI import getTagSmart
from typing import List
import common
import TableBotExceptions

MAXIMUM_FC_GENERATION = 15
MAXIMUM_PLAYER_NAME_GENERATION = 15
BASE_FC_FOR_GENERATION = "0000-0000-0000"
BASE_PLAYER_NAME_FOR_GENERATION = "Player "

class Room(object):
    '''
    classdocs
    '''
    def __init__(self, rLIDs, roomSoup, races=None, roomID=None, set_up_user=None, display_name="", max_races=None):
        self.name_changes = {}
        self.removed_races = []
        
        self.initialize(rLIDs, roomSoup, races, roomID, max_races=max_races)
        self.playerPenalties = defaultdict(int)
        
        #for each race, holds fc_player dced that race, and also holds 'on' or 'before'
        self.dc_on_or_before = defaultdict(dict)
        self.set_up_user = set_up_user
        self.set_up_user_display_name = display_name
        self.forcedRoomSize = {}
        self.miis = {}
        #Dict with mapping race # to list of manual placement objects - these cannot strictly be direct references, but may either be copies or direct references to the actual Placement objects
        #Race number maps to [[old_placement, new_placement], [old_placement, new_placement], [old_placement, None]...]
        #None for new_placement if matching couldn't work
        self.manual_placements = {} 
        self.FC_generation_counter = 0
        self.name_generation_counter = 1
        #Variable is only set if the player added was by name, but the name was not a valid lounge name
        #Temporarily stores the player and adds it or throws it away based on the tabler's response
        self.potential_player_addition = None
        
    
    def __get_generated_fc__(self):
        if self.FC_generation_counter >= MAXIMUM_FC_GENERATION:
            raise TableBotExceptions.NoMoreFCGeneration()
        to_add = str(self.FC_generation_counter)
        return BASE_FC_FOR_GENERATION[:-len(to_add)] + to_add
    
    def generate_new_fc(self):
        generated_FC = self.__get_generated_fc__()
        self.FC_generation_counter += 1
        return generated_FC
    
    def __get_generated_player_name__(self):
        if self.name_generation_counter > MAXIMUM_PLAYER_NAME_GENERATION: #starts at 1
            raise TableBotExceptions.NoMorePlayerNameGeneration()
        to_add = str(self.name_generation_counter)
        return BASE_PLAYER_NAME_FOR_GENERATION + to_add
    
    def generate_new_player_name(self):
        generated_player_name = self.__get_generated_player_name__()
        self.name_generation_counter += 1
        return generated_player_name
        

    
    def initialize(self, rLIDs, roomSoup, races=None, roomID=None, max_races=None):
        self.rLIDs = rLIDs
        
        if roomSoup is None:
            raise Exception
        if self.rLIDs is None or len(self.rLIDs) == 0:
            #TODO: Here? Caller should?
            roomSoup.decompose()
            raise Exception
        
        races_old = None
        if 'races' in self.__dict__:
            races_old = self.getRaces()
            
            
        self.races:List[Race.Race] = races
        self.roomID = roomID
        if self.getRaces() is None:
            self.races:List[Race.Race] = self.getRacesList(roomSoup, races_old)
        if len(self.getRaces()) > 0:
            self.roomID = self.getRaces()[0].roomID
        else:
            self.rLIDs = None
            self.races:List[Race.Race] = None
            self.roomID = None
            raise Exception
        if max_races is not None:
            self.races = self.races[:max_races]
        
        
    
    
    def is_initialized(self) -> bool:
        return self.getRaces() is not None and self.rLIDs is not None and len(self.rLIDs) > 0
        
    
    def had_positions_changed(self) -> bool:
        if self.getRaces() is not None:
            for race in self.getRaces():
                if race.placements_changed:
                    return True
        return False
    
    def has_manual_placements(self) -> bool:
        if self.getRaces() is not None:
            return any(race.has_manual_placements() for race in self.getRaces())
        
    def get_manual_placements(self) -> List[Placement.Placement]:
        result = []
        if self.getRaces() is not None:
            for race in self.getRaces():
                result.extend(race.get_manual_placements())
        return result
    
    def add_manual_placement(self, to_add, race_num:int) -> bool:
        pass
    
    def remove_manual_placement(self, to_remove, race_num:int) -> bool:
        pass
    
    
    
    def update_manual_placements_after_race_removal(self, raceIndex):
        temp_manual_placements = {}
        for race_num, race_manual_placements in self.manual_placements.items():
            if (raceIndex + 1) == race_num:
                continue
            if (raceIndex + 1) > race_num:
                temp_manual_placements[race_num] = race_manual_placements
            else:
                temp_manual_placements[race_num-1] = race_manual_placements
        self.manual_placements.clear()
        self.manual_placements.update(temp_manual_placements)

    #Outside caller should use this, it will add the removed race to the class' history
    def remove_race(self, raceIndex):
        if raceIndex >= 0 and raceIndex < len(self.getRaces()):
            raceName = self.getRaces()[raceIndex].getTrackNameWithoutAuthor()
            remove_success = self.__remove_race__(raceIndex)
            if remove_success:
                self.removed_races.append((raceIndex, raceName))
                self.update_manual_placements_after_race_removal(raceIndex)
            return remove_success, (raceIndex, raceName)
        return False, None
    
    def __remove_race__(self, raceIndex, races=None):
        if races is None:
            races=self.getRaces()
        if raceIndex >= 0 and raceIndex < len(races):
            del races[raceIndex]
            return True
        return False
    
    def get_removed_races_string(self):
        removed_str = ""
        for raceInd, raceName in self.removed_races:
            removed_str += "- " + raceName + " (originally race #" + str(raceInd+1) + ") removed by tabler\n"
        return removed_str
    
    
    def getFCPlayerList(self, start_race=1,end_race=None, ignore_manual_player_additions=False):
        fcNameDict = {}
        if end_race is None:
            end_race = len(self.getRaces())
        for race in self.getRaces()[start_race-1:end_race]:
            for placement in race.getPlacements():
                if ignore_manual_player_additions and placement.is_manual_placement():
                    continue
                FC, name = placement.get_fc_and_name()
                fcNameDict[FC] = name
        return fcNameDict
    
    def getFCPlayerListString(self, start_race=1,end_race=12, lounge_replace=True):
        FCPL = self.getFCPlayerList(start_race, end_race)
        to_build = ""
        for fc, name in FCPL.items():
            to_build += fc + ": " + UtilityFunctions.process_name(name + UserDataProcessing.lounge_add(fc, lounge_replace)) + "\n"
        return to_build
    
    def getPlayerPenalities(self):
        return self.playerPenalties
        
    def addPlayerPenalty(self, fc, amount):
        self.playerPenalties[fc] += amount
        
    
    def getFCPlayerListStartEnd(self, start_race, end_race):
        fcNameDict = {}
        for raceNumber, race in enumerate(self.getRaces(), 1):
            if raceNumber >= start_race and raceNumber <= end_race: 
                for placement in race.getPlacements():
                    FC, name = placement.get_fc_and_name()
                    fcNameDict[FC] = name
        return fcNameDict
    
    def getNameChanges(self):
        return self.name_changes
    
    def setNameForFC(self, FC, name):
        self.name_changes[FC] = name
    
    def getFCs(self, start_race=1, end_race=None, ignore_manual_player_additions=False):
        return self.getFCPlayerList(start_race=start_race, end_race=end_race, ignore_manual_player_additions=ignore_manual_player_additions).keys()
    
    def getPlayers(self, start_race=1, end_race=None, ignore_manual_player_additions=False):
        return self.getFCPlayerList(start_race=start_race, end_race=end_race, ignore_manual_player_additions=ignore_manual_player_additions).values()
    
            
    def setRaces(self, races):
        self.races:List[Race.Race] = races
        
    def getRaces(self, start_race=None, end_race=None):
        if self.races is None:
            return None
        
        if start_race is None:
            start_race = 1
        if end_race is None:
            end_race = len(self.races)
        start_race -= 1
        return self.races[start_race:end_race]
    
    def getRXXText(self):
        resultText = ""
        if len(self.rLIDs) == 1:
            rxx = self.rLIDs[0]
            resultText = f"**Room URL:** https://wiimmfi.de/stats/mkwx/list/{rxx}  |  **rxx number:** {rxx}\n"
        else:
            resultText = "**?mergeroom** was used, so there are multiple rooms:\n\n"
            for i, rxx in enumerate(self.rLIDs[::-1], 1):
                resultText += f"**- Room #{i} URL:** https://wiimmfi.de/stats/mkwx/list/{rxx}  |  **rxx number:** {rxx}\n"
        return resultText
            
    
    def getMissingOnRace(self, numGPS):
        GPPlayers = []
        missingPlayers = []
        for GPNum in range(numGPS):
            GPPlayers.append(self.getFCPlayerListStartEnd((GPNum*4)+1, (GPNum+1)*4))
        
        wentMissingThisGP = []
        for raceNum, race in enumerate(self.getRaces(end_race=numGPS*4)):
            if raceNum/4 >= len(GPPlayers): #To avoid any issues if they put less GPs than the room has
                break
            thisGPPlayers = GPPlayers[int(raceNum/4)]
            missingPlayersThisRace = []
            if raceNum % 4 == 0:
                wentMissingThisGP = []
            
            if raceNum % 4 != 0: #not the start of the GP:
                for fc, player in thisGPPlayers.items():
                    if fc not in race.getFCs() and fc not in wentMissingThisGP:
                        wentMissingThisGP.append(fc)
                        missingPlayersThisRace.append((fc, player))
            missingPlayers.append(missingPlayersThisRace)
        for missingPlayersOnRace in missingPlayers:
            missingPlayersOnRace.sort()
        return missingPlayers
    
    
    def getDCListString(self, numberOfGPs=3, replace_lounge=True):
        missingPlayersByRace = self.getMissingOnRace(numberOfGPs)
        missingPlayersAmount = sum([len(x) for x in missingPlayersByRace])
        if missingPlayersAmount == 0:
            last_race = self.getRaces()[-1]
            return False, "No one has DCed. Last race: " + str(last_race.track) + " (Race #" + str(last_race.raceNumber) + ")"
        else:
            counter = 1
            build_string = "*Disconnection List:*\n"
            for raceNum, missing_players in enumerate(missingPlayersByRace, 1):
                for fc, player in sorted(missing_players):
                    build_string += "\t" + str(counter) + ". **"
                    build_string += UtilityFunctions.process_name(player + UserDataProcessing.lounge_add(fc, replace_lounge)) + "** disconnected on or before race #" + str(raceNum) + " (" + str(self.getRaces()[raceNum-1].getTrackNameWithoutAuthor()) + ")\n"
                    counter+=1
            return True, build_string
    
    #method that returns the players in a consistent, sorted order - first by getTagSmart, then by FC (for tie breaker)
    #What is returned is a list of tuples (fc, player_name)
    def get_sorted_player_list(self, start_race=1, end_race=12):
        players = list(self.getFCPlayerListStartEnd(start_race, end_race).items())
        return sorted(players, key=lambda x: (getTagSmart(x[1]), x[0]))
       
       
    def get_sorted_player_list_string(self, start_race=1, end_race=12, lounge_replace=True):
        players = self.get_sorted_player_list(start_race, end_race)
        to_build = ""
        for list_num, (fc, player) in enumerate(players, 1):
            to_build += str(list_num) + ". " + UtilityFunctions.process_name(player + UserDataProcessing.lounge_add(fc, lounge_replace)) + "\n"
        return to_build
            
            
    def get_players_list_string(self, start_race=1, end_race=12, lounge_replace=True):
        player_list = self.get_sorted_player_list(start_race, end_race)
        build_str = ""
        for counter, (fc, player) in enumerate(player_list, 1):
            build_str += str(counter) + ". " + UtilityFunctions.process_name(player)
            if lounge_replace:
                build_str += UtilityFunctions.process_name(UserDataProcessing.lounge_add(fc, lounge_replace))
            build_str += "\n"
        return build_str
    
    #SOUP LEVEL FUNCTIONS
    
    @staticmethod
    def getPlacementInfo(line):
        allRows = line.find_all("td")
    
        FC = str(allRows[0].find("span").string)
    
        roomPosition = -1
        role = "-1"

        if (allRows[1].find("b") is not None):
            roomPosition = 1
            role = "host"
        else:
            temp = str(allRows[1].string).strip().split()
            roomPosition = temp[0].strip(".")
            role = temp[1]
        
        #TODO: Handle VR?
        vr = str(-1)
        
        delta = allRows[7].string #Not true delta, but significant delta (above .5)
        
        time = str(allRows[8].string)
        
        playerName = str(allRows[9].string)
        
        while len(allRows) > 0:
            del allRows[0]
        
        return FC, roomPosition, role, vr, delta, time, playerName
    
    def getRaceInfoFromList(self, textList):
        '''Utility Function'''
        raceTime = str(textList[0])
        UTCIndex = raceTime.index("UTC")
        raceTime = raceTime[:UTCIndex+3]
        
        matchID = str(textList[1])
        
        raceNumber = str(textList[2]).strip().strip("(").strip(")").strip("#")
        
        roomID = str(textList[4])
        
        roomType = str(textList[6])
        
        cc = str(textList[7])[3:-2] #strip white spaces, the star, and the cc
        
        track = "Unknown_Track (Bad HTML, mkwx messed up)"
        if 'rLIDs' in self.__dict__:
            track += str(self.rLIDs)
        try:
            track = str(textList[9])
        except IndexError:
            pass
        
        placements = []
        
        while len(textList) > 0:
            del textList[0]
        
        return raceTime, matchID, raceNumber, roomID, roomType, cc, track, placements
      
    def getRacesList(self, roomSoup, races_old=None):
        #Utility function
        tableLines = roomSoup.find_all("tr")
        
        foundRaceHeader = False
        races = []
        for line in tableLines:
            if foundRaceHeader:
                foundRaceHeader = False
            else:
                if (line.get('id') is not None): #Found Race Header
                    #_ used to be the racenumber, but mkwx deletes races 24 hours after being played. This leads to rooms getting races removed, and even though
                    #they have race numbers, the number doesn't match where they actually are on the page
                    #This was leading to out of bounds exceptions.
                    raceTime, matchID, _, roomID, roomType, cc, track, placements = self.getRaceInfoFromList(line.findAll(text=True))
                    raceNumber = None
                    races.insert(0, Race.Race(raceTime, matchID, raceNumber, roomID, roomType, cc, track))
                    foundRaceHeader = True
                else:
                    FC, roomPosition, role, vr, delta, time, playerName = self.getPlacementInfo(line)
                    if races[0].hasFC(FC):
                        FC = FC + "-2"
                    plyr = Player.Player(FC, playerName, role, roomPosition, vr)
                    
                    if plyr.FC in self.name_changes:
                        plyr.name = self.name_changes[plyr.FC] + " (Tabler Changed)"
                    p = Placement.Placement(plyr, -1, time, delta=delta)
                    races[0].addPlacement(p)
        
        #We have a memory leak, and it's not incredibly clear how BS4 objects work and if
        #Python's automatic garbage collection can figure out how to collect
        while len(tableLines) > 0:
            del tableLines[0]
        
        for raceNum, race in enumerate(races, 1):
            race.raceNumber = raceNum
        
        if races_old is not None:
            for race in races_old:
                if race.placements_changed:
                    races[race.raceNumber-1].placements_changed = True
                    for (index, newIndex) in race.placement_history:
                        races[race.raceNumber-1].insertPlacement(index, newIndex)
                        
        for removed_race_ind, _ in self.removed_races:
            self.__remove_race__(removed_race_ind, races)
            
        for raceNum, race in enumerate(races, 1):
            race.raceNumber = raceNum
        
        return races
    

    #Soup level functions
    
    def getNumberOfGPS(self):
        return int((len(self.getRaces())-1)/4)+1
    
    async def update_room(self, max_races=None):
        if self.is_initialized():
            soups = []
            rLIDs = []
            for rLID in self.rLIDs:
                
                _, rLID_temp, tempSoup = await WiimfiSiteFunctions.getRoomData(rLID)
                soups.append(tempSoup)
                rLIDs.append(rLID_temp)
                
            tempSoup = WiimfiSiteFunctions.combineSoups(soups)
            
            to_return = False
            if tempSoup is not None:
                self.initialize(rLIDs, tempSoup, max_races=max_races)
                tempSoup.decompose()
                del tempSoup
                to_return = True
                    
            while len(soups) > 0:
                soups[0].decompose()
                del soups[0]
            return to_return
        return False
        
    def getRacesPlayed(self):
        return [r.track for r in self.getRaces()]
    
    def get_races_abbreviated(self, last_x_races=None):
        if last_x_races is None:
            temp = []
            for ind,race in enumerate(self.getRaces(), 1):
                if race.getAbbreviatedName() is None:
                    return None
                temp.append(str(ind) + ". " + race.getAbbreviatedName())
            return " | ".join(temp)
        else:
            temp = []
            for ind,race in enumerate(self.getRaces()[-last_x_races:], 1):
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
        return UtilityFunctions.process_name(string_build)
    
    def get_loungenames_in_room(self):
        all_fcs = self.getFCs()
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
        if self.getSetupUser() is None or self.getSetupUser() == discord_id:
            return True
        discord_ids = [data[0] for data in self.getRoomFCDiscordIDs().values()]
        return str(discord_id) in discord_ids
        
    def getRoomFCDiscordIDs(self):
        FC_DID = {FC:(None, None) for FC in self.getFCs()}
        for FC in FC_DID:
            if FC in UserDataProcessing.FC_DiscordID:
                FC_DID[FC] = UserDataProcessing.FC_DiscordID[FC]
        return FC_DID
        
    
    def getSetupUser(self):
        return self.set_up_user
    
    def setSetupUser(self, setupUser, displayName:str):
        self.set_up_user = setupUser
        self.set_up_user_display_name = displayName
    

    def forceRoomSize(self, raceNum, roomSize):
        self.forcedRoomSize[raceNum] = roomSize
    
       
    #This is not the entire save state of the class, but rather, the save state for edits made by the user 
    def get_recoverable_save_state(self):
        save_state = {}
        save_state['name_changes'] = self.name_changes.copy()
        save_state['removed_races'] = self.removed_races.copy()
        save_state['playerPenalties'] = self.playerPenalties.copy()
        
        #for each race, holds fc_player dced that race, and also holds 'on' or 'before'
        save_state['dc_on_or_before'] = self.dc_on_or_before.copy()
        save_state['forcedRoomSize'] = self.forcedRoomSize.copy()
        save_state['rLIDs'] = self.rLIDs.copy()
        save_state['races'] = {}
        save_state['manual_placements'] =  self.manual_placements.copy()
        for race in self.races:
            matchID = race.matchID
            recoverable_save_state = race.get_recoverable_state()
            try:
                save_state['races'][matchID] = recoverable_save_state
            except Exception as e:
                common.log_text(f"Error in Room.get_recoverable_save_state() putting race in dictionary: {str(matchID)}", common.ERROR_LOGGING_TYPE)
                common.log_text(str(e), common.ERROR_LOGGING_TYPE)
        
        return save_state
    
    def restore_save_state(self, save_state):
        for save_attr, save_value in save_state.items():
            if save_attr != 'races':
                self.__dict__[save_attr] = save_value
        races_save_state = save_state['races']
        for race in self.races:
            if race.matchID in races_save_state:
                race.restore_save_state(races_save_state[race.matchID])
                
        
        
        
    
        