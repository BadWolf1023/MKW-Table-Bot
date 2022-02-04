'''
Created on Jul 12, 2020

@author: willg
'''
import Race
import Placement
import Player
import WiimmfiSiteFunctions
import UserDataProcessing
import common

from collections import defaultdict
import UtilityFunctions
import TagAIShell
from copy import copy, deepcopy
from UtilityFunctions import isint, isfloat
from itertools import chain
from typing import List, Any, Dict

DEBUG_RACES = False
DEBUG_PLACEMENTS = False

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
    def __init__(self, rLIDs, roomSoup, setup_discord_id, setup_display_name):
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
        self.manual_dc_placements: defaultdict[int, List[Dict[str, Any]]] = defaultdict(list) #maps race to manually configured DC placements (on/before)

        self.set_up_user = setup_discord_id
        self.set_up_user_display_name = setup_display_name
        #dictionary of fcs that subbed in with the values being lists: fc: [subinstartrace, subinendrace, suboutfc, suboutname, suboutstartrace, suboutendrace, [suboutstartracescore, suboutstartrace+1score,...]]
        self.sub_ins = {}
        
        self.initialize(rLIDs, roomSoup)
        self.is_freed = False
    
    def get_set_up_user_discord_id(self):
        return self.set_up_user
    def get_set_up_display_name(self):
        return self.set_up_user_display_name
    def get_dc_statuses(self):
        return self.dc_on_or_before
    def get_subs(self):
        return self.sub_ins
    def get_manual_dc_placements(self):
        return self.manual_dc_placements
    
    def initialize(self, rLIDs, roomSoup, mii_dict=None):
        self.rLIDs = rLIDs
        
        if roomSoup is None:
            raise Exception
        if self.rLIDs is None or len(self.rLIDs) == 0:
            #TODO: Here? Caller should?
            roomSoup.decompose()
            raise Exception
            
            
        self.races: List[Race.Race] = self.getRacesList(roomSoup, mii_dict)
        
        if len(self.races) > 0:
            self.roomID = self.races[0].roomID
            
        else: #Hmmmm, if there are no races, what should we do? We currently unload the room... edge case...
            self.rLIDs = None
            self.races = None
            self.roomID = None
            raise Exception #And this is why the room unloads when that internal error occurs
        

    def is_initialized(self):
        return self.races is not None and self.rLIDs is not None and len(self.rLIDs) > 0
        
    def get_rxxs(self):
        return self.rLIDs
    
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

    
    def had_subs(self):
        return len(self.sub_ins) != 0
    
    def get_room_subs(self):
        if not self.had_subs():
            return "No subs this war."
        
        ret = "*Subs this war:*"
        
        for ind, (sub_in_fc, substitution) in enumerate(self.sub_ins.items(), 1):
            subInName = self.getMiiNameByFC(sub_in_fc) + UserDataProcessing.lounge_add(sub_in_fc)
            subOutName = substitution[3]
            race = substitution[0]
            ret+=f"\n\t{ind}. **{subInName}** subbed in for **{subOutName}** on race {race}."
        
        return ret
    
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
            sub_str_list.append(f"Tabler subbed in {UtilityFunctions.process_name(subInName)} for {UtilityFunctions.process_name(suboutName)} this race")
        return sub_str_list
    
    def add_sub(self, subInFC, subInStartRace, subInEndRace, subOutFC, subOutName, subOutStartRace, subOutEndRace, subOutScores):
        #dictionary of fcs that subbed in with the values being lists: fc: [subinstartrace, subinendrace, suboutfc, suboutname, suboutstartrace, suboutendrace, [suboutstartracescore, suboutstartrace+1score,...]]
        self.sub_ins[subInFC] = [subInStartRace, subInEndRace, subOutFC, subOutName, subOutStartRace, subOutEndRace, subOutScores]
        self.setNameForFC(subOutFC, f"#subbed out: {subOutName}")
        
    
    #Outside caller should use this, it will add the removed race to the class' history
    #Okay, final step: when we remove a race, whatever room size changes and quickedits and dc_on_or_before for races after the removed race need to all shift down by one
    def remove_race(self, race_num):
        raceIndex = race_num-1
        if raceIndex >= 0 and raceIndex < len(self.races):
            raceName = self.races[raceIndex].getTrackNameWithoutAuthor()
            remove_success = self.__remove_race__(raceIndex)
            if remove_success:
                self.removed_races.append((raceIndex, raceName))
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
    
    #Should only call if you know the data for an FC among the placements will be unique
    def getFCPlacements(self, startrace=1,endrace=None):
        fcPlacementDict = {}
        if endrace is None:
            endrace = len(self.races)
        for race in self.races[startrace-1:endrace]:
            for placement in race.getPlacements():
                fcPlacementDict[placement.getPlayer().get_FC()] = placement
        return fcPlacementDict

    
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
    
    def getMiiNameByFC(self, FC):
        player_list = self.getFCPlayerList(endrace=None)
        if FC in player_list:
            return player_list[FC]
        return "no name"
    
    def get_known_region(self):
        regions = set(race.get_region() for race in self.getRaces())
        if len(regions) != 1:
            return Race.UNKNOWN_REGION
        for region in regions:
            return region
            
    
    def fcIsInRoom(self, FC):
        return FC in self.getFCs()       
    
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
    
    def getFCs(self):
        return self.getFCPlayerList(endrace=None).keys()
    
    def getPlayers(self):
        return self.getFCPlayerList(endrace=None).values()
    
            
    def setRaces(self, races):
        self.races = races
        
    def getRaces(self, startRace=1, endRace=None):
        
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
    
    def getMissingOnRace(self, numGPS, include_blank = False):
        GPPlayers = []
        missingPlayers = [] #players who were missing or had a blank time 

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
            
            # for placement in race.placements:
            #     if placement.is_disconnected() and placement.getFC() not in wentMissingThisGP:
            #         wentMissingThisGP.append(placement.getFC())
            #         if include_blank:
            #             missingPlayersThisRace.append(placement.get_fc_and_name())

            missingPlayers.append(missingPlayersThisRace)

        for race, players in self.dc_on_or_before.items():
            for fc, status in players.items():
                if status == 'on':
                    if race-1 < len(missingPlayers):
                        missingPlayers[race-1].append((fc, self.getFCPlayerList()[fc]))

        for missingPlayersOnRace in missingPlayers:
            missingPlayersOnRace.sort()

        return missingPlayers
    
    def get_dc_list_players(self, numGPs=3):
        '''
        get a sorted list of the DCs (same order as DCListString) for use by Discord Buttons
        '''
        dc_list = list()
        missingPlayersByRace = self.getMissingOnRace(numGPs, include_blank=False)

        for raceNum, race in enumerate(missingPlayersByRace):
            for dc in race:
                dc_list.append((raceNum+1, dc[0]))

        return dc_list
        # dc_list = list(chain.from_iterable(missingPlayersByRace))
        # dc_list = [player[0] for player in dc_list]
        # return dc_list
    
    def getDCListString(self, numberOfGPs=3, replace_lounge=True):
        missingPlayersByRace = self.getMissingOnRace(numberOfGPs, include_blank=False)
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
                    status_str = "disconnected on or before"
                    confirm_str = ""
                    if raceNum in self.dc_on_or_before and fc in self.dc_on_or_before[raceNum]:
                        status_str = f"DCed **{self.dc_on_or_before[raceNum][fc]}**"
                        confirm_str = " - *Tabler confirmed*"

                    build_string += UtilityFunctions.process_name(player + UserDataProcessing.lounge_add(fc, replace_lounge)) + f"** {status_str} race #" + str(raceNum) + " (" + str(self.races[raceNum-1].getTrackNameWithoutAuthor()) + f"){confirm_str}\n"
                    counter+=1
            return True, build_string
    
    def edit_dc_status(self, player_fc, raceNum, status):
        '''
        edits a player's DC status to `status` for race `raceNum`, then adds/removes their corresponding placement to the race's `placements`
        '''
        self.dc_on_or_before[raceNum][player_fc] = status #change their dc_on_or_before status
        race = self.races[raceNum-1]
        if status in ["on", "during", "midrace", "results", "onresults"]: #STATUS=ON
            if not race.FCInPlacements(player_fc): #player wasn't on results and needs to be added as a placement
                player_obj = self.get_player_from_FC(player_fc)
                DC_placement = Placement.Placement(player_obj, -1, u'\u2014')

                add_dict = {'type': 'add', 'payload': DC_placement}
                self.manual_dc_placements[raceNum].append(add_dict)
                race.addPlacement(DC_placement)
                
        else: #STATUS=BEFORE
            if race.FCInPlacements(player_fc): #player was on results and should be removed from placements
                remove_dict = {'type': 'remove', 'payload': player_fc}
                self.manual_dc_placements[raceNum].append(remove_dict)
                race.remove_placement_by_FC(player_fc)
    
    def get_player_from_FC(self, FC):
        for race in self.races:
            for placement in race.placements:
                if placement.player.FC == FC:
                    return placement.player
        return None
    
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
        playerPageLink = str(allRows[0].find("a")[common.HREF_HTML_NAME])
        
        
        FC = str(allRows[0].find("span").string)
        ol_status = str(allRows[1][common.TOOLTIP_NAME]).split(":")[1].strip()
    
        roomPosition = -1
        
        role = "-1"
        if (allRows[1].find("b") is not None):
            roomPosition = 1
            role = "host"
        else:
            temp = str(allRows[1].string).strip().split()
            roomPosition = temp[0].strip(".")
            role = temp[1].strip()
        
        playerRegion = str(allRows[2].string)
        playerConnFails = str(allRows[3].string)
        if not isint(playerConnFails) and not isfloat(playerConnFails):
            playerConnFails = None
        else:
            playerConnFails = float(playerConnFails)
        #TODO: Handle VR?
        vr = str(allRows[4].string)
        if not isint(vr):
            vr = None
        else:
            vr = int(vr)
        
        character_vehicle = None
        if allRows[5].has_attr(common.TOOLTIP_NAME):
            character_vehicle = str(allRows[5][common.TOOLTIP_NAME])
        
        
        delta = str(allRows[7].string).strip() #Not true delta, but significant delta (above .5)
        
        time = str(allRows[8].string)
        
        playerName = str(allRows[9].string)
        while len(allRows) > 0:
            del allRows[0]
        
        return FC, playerPageLink, ol_status, roomPosition, playerRegion, playerConnFails, role, vr, character_vehicle, delta, time, playerName
    
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
        is_ct = str(textList[-1]) in {'u', 'c'}
        track = "Unknown_Track (Bad HTML, mkwx messed up)"
        try:
            if len(textList) == 12:
                track = str(textList[9])
            elif len(textList) == 10:
                track = str(textList[8]).split(":")[-1].strip()
            else:
                track = str(textList[9]).strip()
        except IndexError:
            pass
        
        placements = []
        
        while len(textList) > 0:
            del textList[0]
        
        return raceTime, matchID, raceNumber, roomID, roomType, cc, track, placements, is_ct
    
    def getRXXFromHTMLLine(self, line):
        roomLink = line.find_all('a')[1][common.HREF_HTML_NAME]
        return roomLink.split("/")[-1]
        
    def getRaceIDFromHTMLLine(self, line):
        return line.get('id')
    
    def getTrackURLFromHTMLLine(self, line):
        try:
            return line.find_all('a')[2][common.HREF_HTML_NAME]
        except IndexError:
            return "No Track Page"
        
      
    def getRacesList(self, roomSoup, mii_dict=None):
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
                    raceTime, matchID, mkwxRaceNumber, roomID, roomType, cc, track, placements, is_ct = self.getRaceInfoFromList(line.findAll(text=True))
                    room_rxx = self.getRXXFromHTMLLine(line)
                    race_id = self.getRaceIDFromHTMLLine(line)
                    trackURL = self.getTrackURLFromHTMLLine(line)
                    raceNumber = None
                    races.insert(0, Race.Race(raceTime, matchID, raceNumber, roomID, roomType, cc, track, is_ct, mkwxRaceNumber, room_rxx, race_id, trackURL))
                    foundRaceHeader = True
                    
                else:
                    FC, playerPageLink, ol_status, roomPosition, playerRegion, playerConnFails, role, vr, character_vehicle, delta, time, playerName = self.getPlacementInfo(line)
                    if races[0].hasFC(FC):
                        FC = FC + "-2"
                    mii_hex = None
                    if mii_dict is not None and FC in mii_dict:
                        mii_hex = mii_dict[FC].mii_data_hex_str
                    plyr = Player.Player(FC, playerPageLink, ol_status, roomPosition, playerRegion, playerConnFails, role, vr, character_vehicle, playerName, mii_hex=mii_hex)
                    p = Placement.Placement(plyr, -1, time, delta)
                    races[0].addPlacement(p)
        
            
        for race in races:
            if DEBUG_RACES:
                print()
                print(f"Room ID: {race.roomID}")
                print(f"Room rxx: {race.rxx}")
                print(f"Room Type: {race.roomType}")
                print(f"Race Match ID: {race.matchID}")
                print(f"Race ID: {race.raceID}")
                print(f"Race Time: {race.matchTime}")
                print(f"Race Number: {race.raceNumber}")
                print(f"Race Track: {race.track}")
                print(f"Track URL: {race.trackURL}")
                print(f"Race cc: {race.cc}")
                print(f"Is CT? {race.is_ct}")
            if DEBUG_PLACEMENTS:
                for placement in race.getPlacements():
                    print()
                    print(f"\tPlayer Name: {placement.getPlayer().name}")
                    print(f"\tPlayer FC: {placement.getPlayer().FC}")
                    print(f"\tPlayer Page: {placement.getPlayer().playerPageLink}")
                    print(f"\tPlayer ID: {placement.getPlayer().pid}")
                    print(f"\tFinish Time: {placement.get_time_string()}")
                    print(f"\tPlace: {placement.place}")
                    print(f"\tol_status: {placement.getPlayer().ol_status}")
                    print(f"\tPosition in Room: {placement.getPlayer().positionInRoom}")
                    print(f"\tPlayer Region: {placement.getPlayer().region}")
                    print(f"\tPlayer Conn Fails: {placement.getPlayer().playerConnFails}")
                    print(f"\tRole: {placement.getPlayer().role}")
                    print(f"\tVR: {placement.getPlayer().vr}")
                    print(f"\tCharacter: {placement.getPlayer().character}")
                    print(f"\tVehicle: {placement.getPlayer().vehicle}")
                    print(f"\tDiscord name: {placement.getPlayer().discord_name}")
                    print(f"\tLounge name: {placement.getPlayer().lounge_name}")
                    print(f"\tCharacter: {placement.getPlayer().character}")
                    print(f"\tVehicle: {placement.getPlayer().vehicle}")
                    print(f"\tPlayer Discord name: {placement.getPlayer().discord_name}")
                    print(f"\tPlayer lounge name: {placement.getPlayer().lounge_name}")
                    print(f"\tPlayer mii hex: {placement.getPlayer().mii_hex}")

        #We have a memory leak, and it's not incredibly clear how BS4 objects work and if
        #Python's automatic garbage collection can figure out how to collect
        while len(tableLines) > 0:
            del tableLines[0]
        

        seen_race_id_numbering = defaultdict(lambda:[{}, 0])
        for race in races:
            race:Race.Race
            rxx_numbering = seen_race_id_numbering[race.get_rxx()]
            if race.get_race_id() not in rxx_numbering:
                rxx_numbering[1] += 1
                rxx_numbering[0][race.get_race_id()] = rxx_numbering[1]
            race.set_race_number(rxx_numbering[0][race.get_race_id()])

        return races

    

    #Soup level functions
    
    def getNumberOfGPS(self):
        return int((len(self.races)-1)/4)+1
    
    async def update_room(self, database_call, is_vr_command, mii_dict=None):
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
                self.initialize(rLIDs, tempSoup, mii_dict)
                
                #Make call to database to add data
                if not is_vr_command:
                    await database_call()
                self.apply_tabler_adjustments()
                tempSoup.decompose()
                del tempSoup
                to_return = True
                    
            while len(soups) > 0:
                soups[0].decompose()
                del soups[0]
            return to_return
        return False
    
    def apply_tabler_adjustments(self):
        #First, we number all races
        for raceNum, race in enumerate(self.races, 1):
            race.raceNumber = raceNum
            
        #Next, apply name changes
        for FC, name_change in self.name_changes.items():
            for race in self.races:
                for placement in race.getPlacements():
                    if placement.getPlayer().get_FC() == FC:
                        placement.getPlayer().set_name(f"{name_change} (Tabler Changed)")
        
        #Next, we remove races
        for removed_race_ind, _ in self.removed_races:
            self.__remove_race__(removed_race_ind, self.races)
        
            
        #Next, we need to renumber the races + add/remove manual DC placements
        for raceNum, race in enumerate(self.races, 1):
            race.raceNumber = raceNum
            
            if raceNum in self.manual_dc_placements: #manual DC placements found for this race
                items = self.manual_dc_placements[raceNum]
                for p in items:
                    if p['type'] == 'add':
                        race.addPlacement(p['payload'])
                    else:
                        race.remove_placement_by_FC(p['payload'])


        #Next, we apply position changes
        for race_number, race in enumerate(self.races, 1):
            if race_number in self.placement_history:
                race.applyPlacementChanges(self.placement_history[race_number])
        
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
        if self.is_freed or self.getSetupUser() == discord_id:
            return True
        discord_ids = [data[0] for data in self.getRoomFCDiscordIDs().values()]
        return str(discord_id) in discord_ids
        
    def getRoomFCDiscordIDs(self):
        FC_DID = {FC:(None, None) for FC in self.getFCs()}
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
        save_state['dc_on_or_before'] = deepcopy(self.dc_on_or_before)
        save_state['manual_dc_placements'] = deepcopy(self.manual_dc_placements)
        save_state['forcedRoomSize'] = self.forcedRoomSize.copy()
        save_state['rLIDs'] = self.rLIDs.copy()
        save_state['races'] = deepcopy(self.races)
        save_state['placement_history'] = copy(self.placement_history)
        save_state['sub_ins'] = deepcopy(self.sub_ins)
        
        return save_state
    
    def restore_save_state(self, save_state):
        for save_attr, save_value in save_state.items():
            self.__dict__[save_attr] = save_value
                
