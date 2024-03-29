'''
Created on Jul 12, 2020

@author: willg
'''
import asyncio
from Player import Player
import Race
import Placement
import WiimmfiSiteFunctions
import UserDataProcessing
import common
import MiiPuller

from collections import defaultdict
import UtilityFunctions
import TagAIShell
from copy import copy, deepcopy
from UtilityFunctions import isint, isfloat
import Mii
from typing import TYPE_CHECKING, List, Any, Dict, Union, Tuple
import TimerDebuggers

DEBUG_RACES = False
DEBUG_PLACEMENTS = False

if TYPE_CHECKING:
    from TableBot import ChannelBot


watched_suggestions = {}

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
    def __init__(self, table: 'ChannelBot', rxx: str, races: List[Race.Race], event_id, setup_discord_id, setup_display_name: str):
        self.table = table

        self.name_changes: Dict[str, Dict[str, Union[str, bool]]] = {}

        #holds removed races and race order changes
        self.race_changes: List[Dict[str, Union[List[int], Tuple[int, str]]]] = []

        #Key will be the race number, value will be a list of all the placements changed for the race (including manual DC placements)
        self.placement_history: defaultdict[int, List[Dict[str, Any]]] = defaultdict(list)
        
        #Dictionary - key is race number, value is the number of players for the race that the tabler specified
        self.forcedRoomSize: defaultdict[int, int] = defaultdict(int) #This contains the races that have their size changed by the tabler - when a race is removed, we
        #need to change all the LATER races (the races that happened after the removed race) down by one race

        self.playerPenalties = defaultdict(int)
        
        #for each race, holds fc_player dced that race, and also holds 'on' or 'before'
        self.dc_on_or_before: defaultdict[int, Dict[str, str]] = defaultdict(dict)
        # self.manual_dc_placements: defaultdict[int, List[Dict[str, Any]]] = defaultdict(list) #maps race to manually configured DC placements (on/before)

        self.set_up_user = setup_discord_id
        self.set_up_user_display_name = setup_display_name
        self.sub_ins: Dict[str, Dict[str, Any]] = {} #dict of FCs that subbed in: dict(sub_in_start_race, sub_in_end_race, sub_out_fc, sub_out_mii_name, sub_out_name, sub_out_start_race, sub_out_end_race, sub_out_scores)
        self.is_freed = False
        
        self.miis: Dict[str, Mii.Mii] = {}
        self.populating = False
        self.event_id = event_id
        self.rLIDs: List[str] = []
        self.races: List[Race.Race] = []

        self.suggestion_errors = None
        self.channel_id = None
        
        self.add_races(rxx, races)
    
    @property
    def removed_races(self):
        return [change['payload'] for change in self.race_changes if change['type']=='remove']

    def add_races(self, rxx: str, races: List[Race.Race]):
        if not isinstance(rxx, str):
            raise ValueError("Caller must gaurantee that the given rxx is a string")
        if not isinstance(races, list) or len(races) == 0 or any(not isinstance(race, Race.Race) for race in races):
            raise ValueError("Caller must gaurantee that the given races is a non-empty list of Races")
        self.rLIDs.append(rxx)
        self.races.extend(races)
        self.fix_race_numbers()
    
    def add_rxx(self, rxx: str):
        if not isinstance(rxx, str):
            raise ValueError("Caller must gaurantee that the given rxx is a string")
        self.rLIDs.append(rxx)
    
    def get_set_up_user_discord_id(self):
        return self.set_up_user
    def get_set_up_display_name(self):
        return self.set_up_user_display_name
    def get_dc_statuses(self):
        return self.dc_on_or_before
    def get_subs(self):
        return self.sub_ins
    def get_event_id(self):
        return self.event_id
    
    def watch_suggestions(self, view, errors, channel_id):
        """Watch suggestions view so that it updates automatically on race removals and state changes."""
        watched_suggestions[channel_id] = view #store active channel suggestion view
        self.suggestion_errors = errors
        self.channel_id = channel_id
    
    def stop_watching_suggestions(self):
        if self.channel_id:
            watched_suggestions.pop(self.channel_id, None)
            self.suggestion_errors = None
        
    def update_suggestions(self):
        if self.suggestion_errors: #a suggestion view is active and must be updated after race removal/race order change
            view = watched_suggestions.get(self.channel_id, None)
            self.apply_tabler_adjustments(suggestion_call=True)
            updated_suggestions = view.bot.war.get_war_errors_string_2(self, view.bot.get_all_resolved_errors(), suggestion_call=True)
                
            if view:
                self.suggestion_errors = updated_suggestions
                asyncio.create_task(view.refresh_suggestions())

    def set_races(self, races: List[Race.Race]):
        #In case any outsiders have a reference to our race list, we want to update their reference
        self.races.clear()
        self.races.extend(races)
    
    def update_edits(self, order: List[int]):
        #TODO: add check for GP order changes: then can edit war.manualEdits
        
        race_replace = {k: i + 1 for i, k in enumerate(order)}
        for struct in [self.placement_history, self.forcedRoomSize, self.dc_on_or_before]:
            new_struct = dict()
            for race_num, data in struct.items():
                new_struct[race_replace[race_num]] = data
            struct.clear()
            for k, v in new_struct.items():
                struct[k] = v
        
        for _, sub_data in self.sub_ins.items():
            for key in ['in_start_race', 'out_end_race']: 
                sub_data[key] = race_replace[sub_data[key]]

    def change_race_order(self, order: List[int], local_call=False):
        new_order = list(range(1, len(self.races)+1))
        altered_races = [self.races[race_num-1] for race_num in order]
        
        is_consecutive = len(order) > 1 and sorted(order) == list(range(min(order), max(order)+1))
        
        if is_consecutive:
            self.races[min(order)-1:max(order)] = altered_races
            new_order[min(order)-1:max(order)] = order
        else:
            for race_num in sorted(order, reverse=True):
                self.races.pop(race_num-1)
                new_order.pop(race_num-1)

            new_order = order + new_order
            self.set_races(altered_races + self.races)

        self.fix_race_numbers()

        if not local_call:
            self.race_changes.append({
                'type': 'order',
                'payload': order
            })
            self.update_edits(new_order)
            self.update_suggestions()
    
        return ", ".join(list(map(str, new_order)))

    def fix_race_numbers(self):
        for race_num, race in enumerate(self.races, 1):
            race.set_race_number(race_num)
        
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
        if race_num in self.placement_history:
            race_placement_changes = self.placement_history[race_num]
            # manual DC placements do not count as placement changes and should not trigger the warning
            race_placement_changes = [i for i in race_placement_changes if 'change' in i['type']] 

        return race_num in self.placement_history and len(race_placement_changes) > 0
    
    def changePlacement(self, race_num, player_FC, new_placement):
        #We need to get their original placement on the race
        original_placement = self.races[race_num-1].getPlacementNumber(player_FC)
        position_change_payload = (original_placement, new_placement)
        position_change = {'type': 'change', 'payload': position_change_payload}
        self.placement_history[race_num].append(position_change)        
        self.races[race_num-1].applyPlacementChanges([position_change_payload])
    
    def change_race_placements(self, race_num: int, player_fcs: List[str]):
        race_change = {'type': 'race_change', 'payload': player_fcs}
        self.placement_history[race_num].append(race_change)
        self.races[race_num-1].set_placement_changes(player_fcs)
    
    def had_subs(self):
        return len(self.sub_ins) != 0
    
    def get_room_subs(self):
        if not self.had_subs():
            return "No subs for this table."
        
        ret = "*Subs for this table:*"
        
        for ind, (sub_in_fc, sub_data) in enumerate(self.sub_ins.items(), 1):
            subInName = UserDataProcessing.proccessed_lounge_add(self.getMiiNameByFC(sub_in_fc), sub_in_fc)
            out_player = self.get_player_from_FC(sub_data['out_fc'])
            sub_out_fc = out_player.FC
            subOutName = UserDataProcessing.proccessed_lounge_add(out_player.get_full_display_name(), sub_out_fc)
            race = sub_data['in_start_race']
            ret+=f"\n\t{ind}. **{subInName}** subbed in for **{subOutName}** on race {race}."
        
        return ret
    
    def fc_subbed_out(self, fc):
        return self.get_sub_in_fc_for_subout_fc(fc) is not None
    
    def get_sub_in_fc_for_subout_fc(self, suboutfc):
        for fc, sub_data in self.sub_ins.items():
            if suboutfc == sub_data['out_fc']:
                return fc
        return None
    
    def get_sub_out_for_subbed_in_fc(self, subInFC, race_num):
        if subInFC not in self.sub_ins:
            return None, None
        suboutStartRace = self.sub_ins[subInFC]['out_start_race']
        suboutEndRace = self.sub_ins[subInFC]['out_end_race']
        if race_num >= suboutStartRace and race_num <= suboutEndRace:
            return subInFC, self.sub_ins[subInFC]['out_scores'][race_num-suboutStartRace]
        return subInFC, None
    
    def get_sub_string(self, subin_name, subin_fc):
        if not self.fc_subbed_in(subin_fc):
            return subin_name
        
        subinStartRace = self.sub_ins[subin_fc]['in_start_race']
        subinEndRace = self.sub_ins[subin_fc]['in_end_race']
        subOutPlayer: Player = self.get_player_from_FC(self.sub_ins[subin_fc]['out_fc'])
        suboutStartRace = self.sub_ins[subin_fc]['out_start_race']
        suboutEndRace = self.sub_ins[subin_fc]['out_end_race']

        sub_out_name = subOutPlayer.get_sub_out_name()
        
        return f"{sub_out_name}({suboutEndRace-suboutStartRace+1})/{subin_name}({subinEndRace-subinStartRace+1})"
    
    def fc_subbed_in(self, fc):
        return fc in self.sub_ins
        
    def get_subin_error_string_list(self, race_num):
        sub_str_list = []
        for sub_in_fc, sub_data in self.sub_ins.items():
            subInStartRace = sub_data['in_start_race']
            if race_num != subInStartRace:
                continue
            sub_in_player = self.get_player_by_fc(sub_in_fc)
            subInName = UtilityFunctions.clean_for_output(UserDataProcessing.proccessed_lounge_add(sub_in_player.get_full_display_name(), sub_in_fc))
            # if sub_in_fc in self.name_changes:
            #     subInName = UtilityFunctions.clean_for_output(self.name_changes[sub_in_fc]['name'])
            out_player = self.get_player_from_FC(sub_data['out_fc'])
            suboutName = UserDataProcessing.proccessed_lounge_add(out_player.get_full_display_name(), sub_data['out_fc'])
            suboutName = UtilityFunctions.clean_for_output(suboutName)

            sub_str_list.append(f"Tabler subbed in {subInName} for {suboutName} this race")
        return sub_str_list
    
    def add_sub(self, subInFC, subInStartRace, subInEndRace, subOutFC, subOutStartRace, subOutEndRace, subOutScores):
        #dictionary of fcs that subbed in with the values being lists: fc: [subinstartrace, subinendrace, suboutfc, suboutname, suboutstartrace, suboutendrace, [suboutstartracescore, suboutstartrace+1score,...]]
        # self.sub_ins[subInFC] = [subInStartRace, subInEndRace, subOutFC, subOutName, subOutStartRace, subOutEndRace, subOutScores]
        self.sub_ins[subInFC] = {
            'in_start_race': subInStartRace,
            'in_end_race': subInEndRace,
            'out_fc': subOutFC,
            'out_start_race': subOutStartRace,
            'out_end_race': subOutEndRace,
            'out_scores': subOutScores
        }
        # subOutPlayer = self.get_player_from_FC(subOutFC)
        self.setNameForFC(subOutFC, None, is_sub=True)
        
    
    #Outside caller should use this, it will add the removed race to the class' history
    #Okay, final step: when we remove a race, whatever room size changes and quickedits and dc_on_or_before for races after the removed race need to all shift down by one
    def remove_race(self, race_num):
        raceIndex = race_num-1
        if raceIndex >= 0 and raceIndex < len(self.races):
            raceName = self.races[raceIndex].getTrackNameWithoutAuthor()
            remove_success = self.__remove_race__(raceIndex)
            if remove_success:
                self.race_changes.append({
                    'type': 'remove',
                    'payload': (raceIndex, raceName)
                })
                #Update dcs, manual placements, quickedits, and room size changes, and subin scores
                self.forcedRoomSize = generic_dictionary_shifter(self.forcedRoomSize, race_num)
                self.dc_on_or_before = generic_dictionary_shifter(self.dc_on_or_before, race_num)
                self.placement_history = generic_dictionary_shifter(self.placement_history, race_num)
                for sub_data in self.sub_ins.values():
                    subout_start_race = sub_data['out_start_race']
                    subout_end_race = sub_data['out_end_race']
                    if subout_start_race <= race_num <= subout_end_race and subout_start_race <= subout_end_race: #2, 3, 4
                        sub_data['out_scores'].pop(race_num - subout_start_race)
                        sub_data['out_end_race'] -= 1
                        sub_data['in_start_race'] -= 1

                self.update_suggestions()
                        
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
    
    def race_order_changed(self):
        for key in self.race_changes:
            if key == 'order':
                return True

        return False
    
    #Should only call if you know the data for an FC among the placements will be unique
    def getFCPlacements(self, startrace=1,endrace=None):
        fcPlacementDict = {}
        if endrace is None:
            endrace = len(self.races)
        for race in self.races[startrace-1:endrace]:
            for placement in race.getPlacements():
                fcPlacementDict[placement.getPlayer().get_FC()] = placement
        return fcPlacementDict

    
    def getPlayerPenalities(self):
        return self.playerPenalties
    
    def get_fc_penalty(self, fc):
        if self.fc_has_penalty(fc):
            return self.playerPenalties[fc]
        return None

    def fc_has_penalty(self, fc):
        return fc in self.playerPenalties
        
    def addPlayerPenalty(self, fc, amount):
        self.playerPenalties[fc] += amount
    
    
    def getMiiNameByFC(self, FC):
        player_list = self.get_fc_to_name_dict()
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
    
    def setNameForFC(self, FC, name, is_sub=False):
        try:
            changing_sub_out = 'sub' in self.name_changes[FC]['type'] or (FC in self.name_changes and is_sub)
            if FC in self.name_changes and is_sub:
                name = self.name_changes[FC]['name']
        except KeyError:
            changing_sub_out = False

        _type = 'change'
        if changing_sub_out:
            _type = 'change_sub'
        elif is_sub:
            _type = 'sub'

        self.name_changes[FC] = {'name': name, 'type': _type}
        for race in self.races:
            for placement in race.getPlacements():
                if placement.getPlayer().get_FC() == FC:
                    placement.getPlayer().set_name(name, _type)
    
    def getFCs(self):
        return self.get_fc_to_name_dict().keys()
    
    def get_player_by_fc(self, fc):
        return self.get_player_from_FC(fc)

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
            for i, rxx in enumerate(self.rLIDs, 1):
                resultText += f"**- Room #{i} URL:** https://wiimmfi.de/stats/mkwx/list/{rxx}  |  **rxx number:** {rxx}\n"
        return resultText
    
    def getLastRXXString(self):
        if len(self.rLIDs) > 0:
            last_rxx = self.rLIDs[-1]
            return f"**Room URL:** https://wiimmfi.de/stats/mkwx/list/{last_rxx}  |  **rxx number:** {last_rxx}"
        return ""

    def has_merged(self):
        return len(self.rLIDs) > 1

    def get_table_id_text(self):
        #return f"**Table ID:** {self.get_event_id()} | Table Bot API Link: {common.TABLE_BOT_API_LINK}?table_id={self.get_event_id()}"
        return f"**Table ID:** {self.get_event_id()}"
    
    def getMissingPlayersPerRace(self):
        numGPS = int(len(self.races)/4 + 1)
        GPPlayers = []
        missingPlayers = []
        for GPNum in range(numGPS):
            GPPlayers.append(self.get_fc_to_name_dict((GPNum*4)+1, (GPNum+1)*4))
        
        for raceNum, race in enumerate(self.races):
            thisGPPlayers = GPPlayers[int(raceNum/4)]
            missingPlayersThisRace = []
            if raceNum % 4 != 0: #not the start of the GP:
                for fc, player in thisGPPlayers.items():
                    if fc not in race.getFCs():
                        missingPlayersThisRace.append((fc, player))
            missingPlayers.append(missingPlayersThisRace)
        return missingPlayers
    
    def getMissingOnRace(self, numGPS, include_blank=False):
        GPPlayers = []
        missingPlayers = [] #players who were missing or had a blank time 

        for GPNum in range(numGPS):
            GPPlayers.append(self.get_fc_to_name_dict((GPNum*4)+1, (GPNum+1)*4))
        
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
            
            for placement in race.placements:
                if placement.is_manual_DC() and placement.get_fc() not in wentMissingThisGP:
                    wentMissingThisGP.append(placement.get_fc())
                    missingPlayersThisRace.append(placement.get_fc_and_name())
                # if placement.is_disconnected() and placement.get_fc() not in wentMissingThisGP:
                #     wentMissingThisGP.append(placement.get_fc())
                #     if include_blank:
                #         missingPlayersThisRace.append(placement.get_fc_and_name())

            missingPlayers.append(missingPlayersThisRace)

        # for race, players in self.dc_on_or_before.items():
        #     for fc, status in players.items():
        #         if status == 'on':
        #             if race-1 < len(missingPlayers):
        #                 missingPlayers[race-1].append((fc, self.get_fc_to_name_dict()[fc]))

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
                    build_string += "\t" + str(counter) + "\. **"
                    status_str = "disconnected on or before"
                    confirm_str = ""
                    if raceNum in self.dc_on_or_before and fc in self.dc_on_or_before[raceNum]:
                        status_str = f"DCed **{self.dc_on_or_before[raceNum][fc]}**"
                        confirm_str = " - *Tabler confirmed*"

                    build_string += f"{UserDataProcessing.proccessed_lounge_add(player, fc, replace_lounge)} ** {status_str} race #{raceNum} ({self.races[raceNum-1].getTrackNameWithoutAuthor()}){confirm_str}\n"
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
                DC_placement = Placement.Placement(player_obj, 'DC')

                add_dict = {'type': 'add', 'payload': player_fc}
                self.placement_history[raceNum].append(add_dict)
                race.addPlacement(DC_placement)
                
        else: #STATUS=BEFORE
            if race.FCInPlacements(player_fc): #player was on results and should be removed from placements
                remove_dict = {'type': 'remove', 'payload': player_fc}
                self.placement_history[raceNum].append(remove_dict)
                race.remove_placement_by_FC(player_fc)
    
    def get_player_from_FC(self, FC) -> Player:
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

    def get_fc_to_name_dict(self, start_race=None, end_race=None):
        if start_race is None:
            start_race = 1
        if end_race is None:
            end_race = len(self.races)

        fcNameDict = {}
        for raceNumber, race in enumerate(self.races, 1):
            if raceNumber >= start_race and raceNumber <= end_race: 
                for placement in race.getPlacements():
                    FC, name = placement.get_fc_and_name()
                    fcNameDict[FC] = name
        return fcNameDict

    
    #method that returns the players in a consistent, sorted order - first by getTagSmart, then by FC (for tie breaker)
    #What is returned is a list of tuples (fc, player_name)
    def get_sorted_player_list(self, startrace=None, endrace=None):
        players = list(self.get_fc_to_name_dict(startrace, endrace).items())
        return sorted(players, key=lambda x: (TagAIShell.getTag(x[1]), x[0]))
        # return sorted(players, key=lambda p: (self.table.war.teams.get(x[0], TagAIShell.getTag(x[1])), x[0]))
       
    def get_sorted_player_list_string(self, startrace=None, endrace=None, lounge_replace=True, include_fc=False):
        players = self.get_sorted_player_list(startrace, endrace)
        to_build = ""
        for counter, (fc, player) in enumerate(players, 1):
            fc_str = f" - {fc}" if include_fc else ""
            to_build += f"{counter}. {UserDataProcessing.proccessed_lounge_add(player, fc, lounge_replace)}{fc_str}\n"
        return to_build

    
    def getNumberOfGPS(self):
        return int((len(self.races)-1)/4)+1

    def get_miis(self) -> Dict[str, Mii.Mii]:
        return self.miis

    def get_available_miis_dict(self, FCs) -> Dict[str, Mii.Mii]:
        miis = {fc: self.get_miis()[fc] for fc in FCs if fc in self.get_miis()}
        # Name changes don't update Mii objects, 
        # so name changes have to be updated here
        for fc, mii in miis.items():
            try:
                mii.change_display_name(self.name_changes[fc]['name'])
            except KeyError:
                # save states do not track Mii objects, so need case for undo here  
                if mii.name_changed():
                    mii.name_change = False
        return miis

    def remove_miis_with_missing_files(self):
        to_delete = set()
        for fc, mii in self.get_miis().items():
            if not mii.has_table_picture_file():
                common.log_error(f"{fc} does not have a mii picture - table id {self.event_id}")
                to_delete.add(fc)

        for fc in to_delete:
            try:
                self.get_miis()[fc].clean_up()
                del self.get_miis()[fc]
            except:
                common.log_error(f"Exception in remove_miis_with_missing_files: {fc} failed to clean up - table id {self.event_id}")

    def update_mii_hexes(self):
        for race in self.races:
            for FC, mii_hex in self.get_miis().items():
                race.update_FC_mii_hex(FC, mii_hex)

    def populating_miis(self) -> bool:
        return self.populating

    def set_populating_miis(self, populating: bool) -> bool:
        self.populating = populating

    def get_room_FCs(self):
        return self.get_fc_to_name_dict().keys()

    @property
    def players(self):
        return self.getPlayers()

    def getPlayers(self, start=None, end=None) -> List[Player]:
        if start is None:
            start = 1
        if end is None:
            end = self.table.war.numberOfGPs()*4
            
        players = {}
        for race in self.races[start-1:end-1]:
            for placement in race.getPlacements():
                players[placement.get_fc()] = placement.get_player()
        return players.values()

    async def populate_miis(self):
        if common.MIIS_ON_TABLE_DISABLED:
            return
        #print("\n\n\n" + str(self.get_miis()))
        if self.populating_miis():
            return
        self.set_populating_miis(True)
        #print("Start:", datetime.now())
        try:
            self.remove_miis_with_missing_files()
            all_missing_fcs = [fc for fc in self.get_room_FCs() if fc not in self.get_miis()]
            if len(all_missing_fcs) > 0:
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
            self.set_populating_miis(False)
        self.update_mii_hexes()

    @TimerDebuggers.timer_coroutine
    async def update(self) -> WiimmfiSiteFunctions.RoomLoadStatus:
        '''RETURNS HAS_NO_RACES, FAILED_REQUEST, SUCCESS'''
        all_races = []
        status_codes = []
        for rxx in self.rLIDs:
            status_code, _, new_races = await WiimmfiSiteFunctions.get_races_for_rxx(rxx)
            if status_code.status is status_code.FAILED_REQUEST:
                return status_code
            all_races.extend(new_races)
            status_codes.append(status_code)

        if len(all_races) == 0:
            return WiimmfiSiteFunctions.RoomLoadStatus(WiimmfiSiteFunctions.RoomLoadStatus.HAS_NO_RACES)
        self.set_races(all_races)
        return WiimmfiSiteFunctions.RoomLoadStatus(WiimmfiSiteFunctions.RoomLoadStatus.SUCCESS)


    def apply_tabler_adjustments(self, suggestion_call=False):
        #First, we number all races
        self.fix_race_numbers()
            
        #Next, apply name changes
        for FC, name_change_payload in self.name_changes.items():
            for race in self.races:
                for placement in race.getPlacements():
                    if placement.getPlayer().get_FC() == FC:
                        placement.getPlayer().set_name(name_change_payload['name'], name_change_payload['type'])
        
        #Next, we remove races and change race order
        if not suggestion_call: # race orders and removed races are already applied if suggestion_call==True, so don't apply them again
            for change in self.race_changes:
                payload = change['payload']
                if change['type']=='remove':
                    self.races.pop(payload[0])
                else:
                    self.change_race_order(payload, local_call=True)
        
        #Next, we need to renumber the races
        self.fix_race_numbers()

        #Next, we apply position changes/modifications (including manual DC placements)
        for race_number, race in enumerate(self.races, 1):
            if race_number in self.placement_history:
                items = self.placement_history[race_number]
                for p in items:
                    payload = p['payload']
                    if p['type'] == 'add':
                        player_obj = self.get_player_from_FC(payload)
                        DC_placement = Placement.Placement(player_obj, 'DC')
                        race.addPlacement(DC_placement)
                    elif p['type'] == 'remove':
                        race.remove_placement_by_FC(payload)
                    elif p['type'] == 'change':
                        race.applyPlacementChanges([payload])
                    else:
                        race.set_placement_changes(payload)
        
    def getRacesPlayed(self):
        return [r.track for r in self.races]
    
    @staticmethod
    def get_race_names_abbreviated(races: List[Race.Race], last_x_races=None):
        last_races = races if last_x_races is None else races[-last_x_races:]
        temp = []
        for ind,race in enumerate(last_races, 1):
            temp.append(f"{ind}. {race.getAbbreviatedName()}")
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
        return UtilityFunctions.clean_for_output(string_build)
    
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
        self.is_freed = False
        self.set_up_user = setupUser
        self.set_up_user_display_name = displayName
    

    def forceRoomSize(self, raceNum, roomSize):
        self.forcedRoomSize[raceNum] = roomSize
    
    def getRoomSize(self, raceNum):
        if raceNum in self.forcedRoomSize:
            return self.forcedRoomSize[raceNum]
    
    def clean_up(self):
        for mii in self.get_miis().values():
            mii.clean_up()
            
    def destroy(self):
        self.stop_watching_suggestions()
        self.set_populating_miis(True)
        self.clean_up()
        self.set_populating_miis(False)

    #This is not the entire save state of the class, but rather, the save state for edits made by the user 
    def get_recoverable_save_state(self):
        save_state = {}
        save_state['name_changes'] = self.name_changes.copy()
        # save_state['removed_races'] = self.removed_races.copy()
        save_state['race_changes'] = deepcopy(self.race_changes)
        save_state['playerPenalties'] = self.playerPenalties.copy()
        save_state['dc_on_or_before'] = deepcopy(self.dc_on_or_before) #for each race, holds fc_player dced that race, and also holds 'on' or 'before'
        save_state['forcedRoomSize'] = self.forcedRoomSize.copy()
        save_state['rLIDs'] = self.rLIDs.copy()
        save_state['races'] = deepcopy(self.races)
        save_state['placement_history'] = deepcopy(self.placement_history)
        save_state['sub_ins'] = deepcopy(self.sub_ins)
        save_state['suggestion_errors'] = deepcopy(self.suggestion_errors)
        
        return save_state
    
    def restore_save_state(self, save_state):
        for save_attr, save_value in save_state.items():
            self.__dict__[save_attr] = save_value
        
        if self.suggestion_errors:
            view = watched_suggestions.get(self.channel_id, None)
            if view:
                asyncio.create_task(view.refresh_suggestions())
                
