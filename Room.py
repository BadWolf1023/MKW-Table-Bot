'''
Created on Jul 12, 2020

@author: willg
'''
import Race
import Placement
import Player
import WiimmfiSiteFunctions
import UserDataProcessing

from _collections import defaultdict
import UtilityFunctions
from TagAI import getTagSmart
from copy import copy, deepcopy

#Function takes a default dictionary, the key being a number, and makes any keys that are greater than the threshold one less, then removes that threshold, if it exists
def generic_dictionary_shifter(old_dict, threshold):
    new_dict = defaultdict(old_dict.default_factory)
    for k, v in old_dict.items():
        if k == threshold:
            continue
        if k > threshold:
            new_dict[k-1] = v
        else:
            new_dict[k] = v
    return new_dict

class Room(object):
    '''
    classdocs
    '''
    def __init__(self, rLIDs, roomSoup):
        self.name_changes = {}
        self.removed_races = []
        
        #Key will be the race number, value will be a list of all the placements changed for the race
        self.placement_history = defaultdict(list)
        
        #Dictionary - key is race number, value is the number of players for the race that the tabler specified
        self.forcedRoomSize = defaultdict(int) #This contains the races that have their size changed by the tabler - when a race is removed, we
        #need to change all the LATER races (the races that happened after the removed race) down by one race

        self.playerPenalties = defaultdict(int)
        
        #for each race, holds fc_player dced that race, and also holds 'on' or 'before'
        self.dc_on_or_before = defaultdict(dict)
        self.set_up_user = None
        self.set_up_user_display_name = ""
        
        self.miis = {}
        
        self.initialize(rLIDs, roomSoup)
        

    
    def initialize(self, rLIDs, roomSoup):
        self.rLIDs = rLIDs
        
        if roomSoup is None:
            raise Exception
        if self.rLIDs is None or len(self.rLIDs) == 0:
            #TODO: Here? Caller should?
            roomSoup.decompose()
            raise Exception
            
            

        self.races = self.getRacesList(roomSoup)
        
        if len(self.races) > 0:
            self.roomID = self.races[0].roomID
        else: #Hmmmm, if there are no races, what should we do? We currently unload the room... edge case...
            self.rLIDs = None
            self.races = None
            self.roomID = None
            raise Exception #And this is why the room unloads when that internal error occurs
        
        
    
    
    def is_initialized(self):
        return self.races is not None and self.rLIDs is not None and len(self.rLIDs) > 0
        
    
    def had_positions_changed(self):
        for changes in self.placement_history.values():
            if len(changes) > 0:
                return True
        return False
    
    def placements_changed_for_racenum(self, race_num):
        return race_num in self.placement_history and len(self.placement_history[race_num]) > 0
    
    def changePlacement(self, race_num, player_FC, new_placement):
        #We need to get their original placement on the race
        original_placement = self.races[race_num-1].getPlacementNumber(player_FC)
        position_change = (original_placement, new_placement)
        self.placement_history[race_num].append(position_change)        
        self.races[race_num-1].applyPlacementChanges([position_change])

    

    
    #Outside caller should use this, it will add the removed race to the class' history
    #Okay, final step: when we remove a race, whatever room size changes and quickedits and dc_on_or_before for races after the removed race need to all shift down by one
    def remove_race(self, race_num):
        raceIndex = race_num-1
        if raceIndex >= 0 and raceIndex < len(self.races):
            raceName = self.races[raceIndex].getTrackNameWithoutAuthor()
            remove_success = self.__remove_race__(raceIndex)
            if remove_success:
                self.removed_races.append((raceIndex, raceName))
                #Update dcs, quickedits, and room size changes
                self.forcedRoomSize = generic_dictionary_shifter(self.forcedRoomSize, race_num)
                self.dc_on_or_before = generic_dictionary_shifter(self.dc_on_or_before, race_num)
                self.placement_history = generic_dictionary_shifter(self.placement_history, race_num)
            return remove_success, (raceIndex, raceName)
        return False, None
    
    def __remove_race__(self, raceIndex, races=None):
        if races is None:
            races=self.races
        if raceIndex >= 0 and raceIndex < len(races):
            del races[raceIndex]
            return True
        return False
    
    def get_removed_races_string(self):
        removed_str = ""
        for raceInd, raceName in self.removed_races:
            removed_str += "- " + raceName + " (originally race #" + str(raceInd+1) + ") removed by tabler\n"
        return removed_str
    
    
    def getFCPlayerList(self, startrace=1,endrace=12):
        fcNameDict = {}
        if endrace is None:
            endrace = len(self.races)
        for race in self.races[startrace-1:endrace]:
            for placement in race.getPlacements():
                FC, name = placement.get_fc_and_name()
                fcNameDict[FC] = name
        return fcNameDict
    
    def getFCPlayerListString(self, startrace=1,endrace=12, lounge_replace=True):
        FCPL = self.getFCPlayerList(startrace, endrace)
        to_build = ""
        for fc, name in FCPL.items():
            to_build += fc + ": " + UtilityFunctions.process_name(name + UserDataProcessing.lounge_add(fc, lounge_replace)) + "\n"
        return to_build
    
    def getPlayerPenalities(self):
        return self.playerPenalties
        
    def addPlayerPenalty(self, fc, amount):
        self.playerPenalties[fc] += amount
        
    
    def getFCPlayerListStartEnd(self, startRace, endRace):
        fcNameDict = {}
        for raceNumber, race in enumerate(self.races, 1):
            if raceNumber >= startRace and raceNumber <= endRace: 
                for placement in race.getPlacements():
                    FC, name = placement.get_fc_and_name()
                    fcNameDict[FC] = name
        return fcNameDict
    
    def getNameChanges(self):
        return self.name_changes
    
    def setNameForFC(self, FC, name):
        self.name_changes[FC] = name
    
    def getFCs(self):
        return self.getFCPlayerList(endrace=None).keys()
    
    def getPlayers(self):
        return self.getFCPlayerList(endrace=None).values()
    
            
    def setRaces(self, races):
        self.races = races
        
    def getRaces(self):
        return self.races
    
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
    
    def getLastRXXString(self):
        if len(self.rLIDs) > 0:
            last_rxx = self.rLIDs[0]
            return f"**Room URL:** https://wiimmfi.de/stats/mkwx/list/{last_rxx}  |  **rxx number:** {last_rxx}"
        return ""
    
    def getMissingPlayersPerRace(self):
        numGPS = int(len(self.races)/4 + 1)
        GPPlayers = []
        missingPlayers = []
        for GPNum in range(numGPS):
            GPPlayers.append(self.getFCPlayerListStartEnd((GPNum*4)+1, (GPNum+1)*4))
        
        for raceNum, race in enumerate(self.races):
            thisGPPlayers = GPPlayers[int(raceNum/4)]
            missingPlayersThisRace = []
            if raceNum % 4 != 0: #not the start of the GP:
                for fc, player in thisGPPlayers.items():
                    if fc not in race.getFCs():
                        missingPlayersThisRace.append((fc, player))
            missingPlayers.append(missingPlayersThisRace)
        return missingPlayers
    
    def getMissingOnRace(self, numGPS):
        GPPlayers = []
        missingPlayers = []
        for GPNum in range(numGPS):
            GPPlayers.append(self.getFCPlayerListStartEnd((GPNum*4)+1, (GPNum+1)*4))
        
        wentMissingThisGP = []
        for raceNum, race in enumerate(self.races[0:numGPS*4]):
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
            last_race = self.races[-1]
            return False, "No one has DCed. Last race: " + str(last_race.track) + " (Race #" + str(last_race.raceNumber) + ")"
        else:
            counter = 1
            build_string = "*Disconnection List:*\n"
            for raceNum, missing_players in enumerate(missingPlayersByRace, 1):
                for fc, player in sorted(missing_players):
                    build_string += "\t" + str(counter) + ". **"
                    build_string += UtilityFunctions.process_name(player + UserDataProcessing.lounge_add(fc, replace_lounge)) + "** disconnected on or before race #" + str(raceNum) + " (" + str(self.races[raceNum-1].getTrackNameWithoutAuthor()) + ")\n"
                    counter+=1
            return True, build_string
    
    #method that returns the players in a consistent, sorted order - first by getTagSmart, then by FC (for tie breaker)
    #What is returned is a list of tuples (fc, player_name)
    def get_sorted_player_list(self, startrace=1, endrace=12):
        players = list(self.getFCPlayerListStartEnd(startrace, endrace).items())
        return sorted(players, key=lambda x: (getTagSmart(x[1]), x[0]))
       
       
    def get_sorted_player_list_string(self, startrace=1, endrace=12, lounge_replace=True):
        players = self.get_sorted_player_list(startrace, endrace)
        to_build = ""
        for list_num, (fc, player) in enumerate(players, 1):
            to_build += str(list_num) + ". " + UtilityFunctions.process_name(player + UserDataProcessing.lounge_add(fc, lounge_replace)) + "\n"
        return to_build
            
            
    def get_players_list_string(self, startrace=1, endrace=12, lounge_replace=True):
        player_list = self.get_sorted_player_list(startrace, endrace)
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
      
    def getRacesList(self, roomSoup):
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
                    p = Placement.Placement(plyr, -1, time, delta)
                    races[0].addPlacement(p)
        
        #We have a memory leak, and it's not incredibly clear how BS4 objects work and if
        #Python's automatic garbage collection can figure out how to collect
        while len(tableLines) > 0:
            del tableLines[0]
        
        #First, we number all races
        for raceNum, race in enumerate(races, 1):
            race.raceNumber = raceNum
        
        #Next, we remove races
        for removed_race_ind, _ in self.removed_races:
            self.__remove_race__(removed_race_ind, races)
            
        #Next, we need to renumber the races
        for raceNum, race in enumerate(races, 1):
            race.raceNumber = raceNum
        
        #Next, we apply quick edits
        for race_number, race in enumerate(races, 1):
            if race_number in self.placement_history:
                race.applyPlacementChanges(self.placement_history[race_number])
        
        return races
    

    #Soup level functions
    
    def getNumberOfGPS(self):
        return int((len(self.races)-1)/4)+1
    
    async def update_room(self):
        if self.is_initialized():
            soups = []
            rLIDs = []
            for rLID in self.rLIDs:
                
                _, rLID_temp, tempSoup = await WiimmfiSiteFunctions.getRoomData(rLID)
                soups.append(tempSoup)
                rLIDs.append(rLID_temp)
                
            tempSoup = WiimmfiSiteFunctions.combineSoups(soups)
            
            to_return = False
            if tempSoup is not None:
                self.initialize(rLIDs, tempSoup)
                tempSoup.decompose()
                del tempSoup
                to_return = True
                    
            while len(soups) > 0:
                soups[0].decompose()
                del soups[0]
            return to_return
        return False
        
    def getRacesPlayed(self):
        return [r.track for r in self.races]
    
    def get_races_abbreviated(self, last_x_races=None):
        if last_x_races is None:
            temp = []
            for ind,race in enumerate(self.races, 1):
                if race.getAbbreviatedName() is None:
                    return None
                temp.append(str(ind) + ". " + race.getAbbreviatedName())
            return " | ".join(temp)
        else:
            temp = []
            for ind,race in enumerate(self.races[-last_x_races:], 1):
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
        save_state['rLIDs'] = self.rLIDs.copy()
        save_state['races'] = deepcopy(self.races)
        save_state['placement_history'] = copy(self.placement_history)
        
        return save_state
    
    def restore_save_state(self, save_state):
        for save_attr, save_value in save_state.items():
            self.__dict__[save_attr] = save_value
                
