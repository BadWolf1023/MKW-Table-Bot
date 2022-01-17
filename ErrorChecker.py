'''
Created on Jul 23, 2020

@author: willg
'''
#Module with functions for verifying room information
import UserDataProcessing
from collections import defaultdict
import common
from typing import Union, Dict, List

_SINGLE_BLANK_RACE_TIME = 11
_MULTIPLE_BLANK_RACE_TIMES = 12
_ENTIRE_ROOM_BLANK_RACE_TIMES = 13
_WRONG_PLAYER_COUNT_GP_START = 21
_WRONG_PLAYER_COUNT_RACE = 22
_SINGLE_LARGE_TIME = 31
_MULTIPLE_LARGE_TIMES = 32
_RACERS_TIED = 41
_PLAYERS_CHANGED_DURING_GP = 51
_TABLE_EDITED = 61
_ROOM_SIZE_EDITED = 62
_MULTIPLE_RACES_WITH_SAME_TIMES = 71
_LARGE_DELTA_OCURRED = 72

EC_Messages_Alternative = {_SINGLE_BLANK_RACE_TIME: "One blank race time. If no disconnections, table unreliable for this GP. If someone disconnected and DC points are being counted, this will count as a DC (and you can ignore this warning).",
               _MULTIPLE_BLANK_RACE_TIMES: "Room had a multiple blank race times (but not all times were blank). If there were no disconnections, table unreliable for this GP. If multiple people disconnected and DC points are being counted, these will count as a DCs (and you can ignore this warning).",
               _ENTIRE_ROOM_BLANK_RACE_TIMES: "Entire room had blank finish times. Could not determine actual results. Table unreliable for this GP.",
               _WRONG_PLAYER_COUNT_GP_START: "Players missing at the start of the GP (or disconnected race 1). If GP started with correct number and no DCs race 1, this is an mkwx bug.",
               _WRONG_PLAYER_COUNT_RACE: "One or more players missing.",
               _SINGLE_LARGE_TIME : "One player had a large finish time (mkwx error). Use ?quickedit to correct their position.",
               _MULTIPLE_LARGE_TIMES : "Multiple players had large finish times (mkwx error). Use ?quickedit to correct their positions.",
               _RACERS_TIED:"2 or more racers finished with the exact same time.",
               _MULTIPLE_RACES_WITH_SAME_TIMES:"",
               _LARGE_DELTA_OCURRED:""}




def get_room_errors_players(room, startrace=None, endrace=None, lounge_replace=True, show_large_time_errors=True):   
    race_errors = {}
    
    if startrace is None:
        startrace = 1
    if endrace is None:
        endrace = len(room.get_races())
    startrace -= 1
    
    
    for raceInd, race in enumerate(room.get_races()[startrace:endrace], startrace):
        errors = []
        blank_time_counter = 0
        for placement in race.placements:
            if placement.is_disconnected():
                fc, name = placement.get_fc_and_name()
                errors.append(name + UserDataProcessing.lounge_add(fc, lounge_replace) + " had a blank race time. Disconnected unless mkwx bug. Not giving DC points for this race - use ?changeroomsize if they were not on the results of this race")
                blank_time_counter += 1
            if show_large_time_errors:
                if placement.is_time_large():
                    fc, name = placement.get_fc_and_name()
                    errors.append(name + UserDataProcessing.lounge_add(fc, lounge_replace) + " had large finish time: " + placement.get_time_string() + " - use ?cp to change their position")
        
        ties = race.getTies()
        if len(ties) > 0:
            errors.append("Ties occurred (check table for errors):")
            for this_fc in sorted(ties, key=lambda fc:race.getPlacement(fc)):
                this_placement = race.getPlacement(this_fc)
                _, this_name = this_placement.get_fc_and_name()
                errors.append(this_name + UserDataProcessing.lounge_add(this_fc, lounge_replace) + "'s finish time: " + this_placement.get_time_string() + " - use ?cp to change their position")
            
        if blank_time_counter == len(race.placements):
            errors = [EC_Messages_Alternative[_ENTIRE_ROOM_BLANK_RACE_TIMES]]
            
        #Check if this race's times are the same as any of the previous races times (excluding blank times)
        prior_races = room.get_races()[startrace:raceInd]
        for prior_race in prior_races:
            if race.times_are_subset_of_and_not_all_blank(prior_race):
                errors.append("This race had the exact same race times as a previous race. Table is incorrect for this GP.")
                
        if race.has_unusual_delta_time():
            errors.append("This race had players with impossible deltas (lag). Table could be incorrect for this GP.")
            
            
        errors.extend(room.get_subin_error_string_list(race.raceNumber))
            
        if race.raceNumber in room.forcedRoomSize:
            errors.append("Room size changed to " + str(room.forcedRoomSize[race.raceNumber]) + " players for this race.")
        
        if room.placements_changed_for_racenum(race.raceNumber):
            errors.append("Placements changed by tabler for this race.")
        
        #check if list is empty
        if len(errors) > 0:
            race_errors[int(race.raceNumber)] = errors
    
    
    return race_errors

def get_war_errors_players(war, room, lounge_replace=True, show_large_time_errors=True) -> Union[None, Dict[int, List[str]]]:
    '''Returns the errors that occurred on each race.
       In the dictionary that is returned, the race number is the key, mapped to a List of strings. Each string is a single error that occurred on that race.
       Returns None if the room is not initialized.'''
    
    race_errors = {}
    numberOfPlayers = war.get_user_defined_num_players()
    missingPlayersByRace = room.getMissingOnRace(war.get_user_defined_num_of_gps())
        
    startrace = 0
    endrace = war.get_user_defined_num_of_gps()*4
    dc_on_or_before = room.dc_on_or_before
    for race in room.get_races()[startrace:endrace]:
        if race.getNumberOfPlayers() != numberOfPlayers:
            race_errors[int(race.raceNumber)] = []
            try:
                if ((int(race.raceNumber)-1) % 4) == 0:
                    race_errors[int(race.raceNumber)].append(str(len(race.placements)) + " players at start of GP. Should have " + str(war.get_user_defined_num_players()) + " players. Use ?earlydc if necessary.")
                elif missingPlayersByRace[int(race.raceNumber)-1] != []:
                    for missingFC, missingName in missingPlayersByRace[int(race.raceNumber)-1]:
                        stuffs = [4, 3, 2, 1]
                        numberOfDCPtsGivenMissing = war.get_race_points_when_missing() * stuffs[(int(race.raceNumber)-1)%4]
                        numberOfDCPtsGivenOn = war.get_race_points_when_missing() * stuffs[(int(race.raceNumber)-1)%4] - war.get_race_points_when_missing()
                        
                        if race.raceNumber in dc_on_or_before\
                            and missingFC in dc_on_or_before[race.raceNumber]:
                            num_extra_players = 0
                            for _, on_before in dc_on_or_before[race.raceNumber].items():
                                if on_before == 'on':
                                    num_extra_players += 1
                                    
                            if dc_on_or_before[race.raceNumber][missingFC] == 'on':
                                race_errors[int(race.raceNumber)].append(missingName + UserDataProcessing.lounge_add(missingFC, lounge_replace) + " DCed and was on results. Giving " + str(numberOfDCPtsGivenOn) + " total DC points (3 per missing race). (" + str(len(race.placements) + num_extra_players) + " players in room this race)")
                            else:
                                race_errors[int(race.raceNumber)].append(missingName + UserDataProcessing.lounge_add(missingFC, lounge_replace) + " DCed before this race. Giving " + str(numberOfDCPtsGivenMissing) + " total DC points (3 per missing race). (" + str(len(race.placements) + num_extra_players) + " players in room this race)")
    
                        else:
                            race_errors[int(race.raceNumber)].append(missingName + UserDataProcessing.lounge_add(missingFC, lounge_replace) + " is missing. Giving " + str(war.get_race_points_when_missing()) + " DC points per missing race. (" + str(len(race.placements)) + " players in room) - Use ?dcs to fix this.")
                
                if not race_errors[int(race.raceNumber)]:
                    del race_errors[int(race.raceNumber)]
            except IndexError:
                common.log_text(str(missingPlayersByRace), common.ERROR_LOGGING_TYPE)
                common.log_text(str(race), common.ERROR_LOGGING_TYPE)
                raise
                
            
    by_gp = defaultdict(list)
    for race in room.get_races()[startrace:endrace]:
        race_num = race.raceNumber
        gp_num = int((race_num-1)/4)
        by_gp[gp_num].append(race)
        
    for gp_num, gp in by_gp.items():
        if len(gp) >= 2:
            for gp_race_num in range(1, len(gp)):
                if not set(gp[gp_race_num].get_race_FCs()).issubset(set(gp[gp_race_num-1].get_race_FCs())):
                    race_num = int(gp[gp_race_num].raceNumber)
                    if race_num not in race_errors:
                        race_errors[race_num] = []
                    race_errors[race_num].append("Players in room changed mid-GP. THIS IS AN MKWX BUG. Table is incorrect for this GP.")      
                    
    for i in range(war.get_user_defined_num_of_gps()):
        if len(war.get_gp_score_edits(i+1)) > 0:
            GPRaceStart = (i*4) + 1
            if GPRaceStart not in race_errors:
                race_errors[GPRaceStart] = []
            race_errors[GPRaceStart].insert(0, "Table has been manually modified for this GP.")
            
    temp_dict = get_room_errors_players(room, startrace+1, endrace, lounge_replace=lounge_replace, show_large_time_errors=show_large_time_errors)
    
    for raceNum, ECs in temp_dict.items():
        if raceNum in race_errors:
            race_errors[raceNum].extend(ECs)
        else:
            race_errors[raceNum] = ECs
    return race_errors
    
            
        