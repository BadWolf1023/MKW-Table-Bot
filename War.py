'''
Created on Jul 13, 2020
@author: willg
'''

import itertools
import ErrorChecker
from collections import defaultdict
import random
from Room import Room
import TableBotExceptions
import UtilityFunctions
import UserDataProcessing
import base64
import copy

tableColorPairs = [("#244f96", "#cce7e8"),
                   ("#D11425","#E8EE28"),
                   ("#E40CA6","#ADCFCD"),
                   ("#2EFF04","#FF0404"),
                   ("#193FFF","#FF0404"),
                   ("#ff8cfd","#fdff8c"),
                   ("#96c9ff","#ffbe96"),
                   ("#ffbbb1","#b1ffd9"),
                   ("#ff69b4","#b4ff69"),
                   ("#95eefa","#58cede"),
                   ("#54ffc9","#54e3ff"),
                   ("#a1ff3d","#fcff3d"),
                   ("#8d8ce6","#cfceff")]



class War(object):
    '''
    classdocs
    '''

    __formatMapping = {u"ffa":1,u"1v1":1, u"2v2":2, u"3v3":3, u"4v4":4, u"5v5":5, u"6v6":6}

    def __init__(self,format,numberOfTeams,message_id,numberOfGPs=3,missingRacePts=3,dc_race_pts=0,ignoreLargeTimes=False,displayMiis=True):
        self.teamColors = None
        self.setWarFormat(format,numberOfTeams)
        self.numberOfGPs = numberOfGPs
        self.warName = None
        self.missingRacePts = missingRacePts
        self.dc_race_pts = dc_race_pts
        self.manualEdits = {}
        self.ignoreLargeTimes = ignoreLargeTimes
        self.displayMiis = displayMiis
        self.teamPenalties = defaultdict(int)
        self.forcedRoomSize = {}
        self.teams = None
        self.temporary_tag_data = None
        self.current_discord_picture_path = None
    
    def set_discord_picture_url(self, url: str):
        self.current_discord_picture_path = url

    def get_discord_picture_url(self):
        return self.current_discord_picture_path

    def get_teams(self):  
        return self.teams
    def get_player_edits(self):
        return self.manualEdits
    def should_ignore_large_times(self):
        return self.ignoreLargeTimes
    def get_missing_player_points(self):
        return self.missingRacePts
    
        
    def setWarFormat(self, formatting, numberOfTeams):
        if formatting not in self.__formatMapping:
            raise TableBotExceptions.InvalidWarFormatException()
        
        try: 
            int(numberOfTeams)
        except ValueError:
            raise TableBotExceptions.InvalidNumPlayersInputException()
        
        if self.__formatMapping[formatting.lower().strip()] * int(numberOfTeams) > 12:
            raise TableBotExceptions.InvalidNumberOfPlayersException()
        
        self.formatting = formatting.lower()
        self.numberOfTeams = int(numberOfTeams)
        self.playersPerTeam = self.__formatMapping[self.formatting]
        if self.numberOfTeams == 2:
            self.teamColors = random.choice(tableColorPairs)
    def get_players_per_team(self):
        return self.playersPerTeam
    def get_number_of_gps(self):
        return self.numberOfGPs
    def get_number_of_teams(self):
        return self.numberOfTeams
    def isFFA(self):
        return self.playersPerTeam == 1
        
    def setTeams(self, teams):
        #teams is a dictionary of FCs, each FC having a tag
        self.teams = teams
        
    def getTeamForFC(self, FC):
        if self.teams is None:
            raise TableBotExceptions.WarSetupStillRunning()
        if self.is_ffa() or FC not in self.teams:
            return "No Tag"
        if FC in self.teams:
            return self.teams[FC]

    def setTeamForFC(self, FC, team):
        if self.teams is None:
            raise TableBotExceptions.WarSetupStillRunning()
        self.teams[FC] = team
    
    def getTags(self):
        if self.teams is None:
            raise TableBotExceptions.WarSetupStillRunning()
        return set(self.teams.values())
    
    def getFCsForTag(self, tagToGet):
        if self.teams is None:
            raise TableBotExceptions.WarSetupStillRunning()
        return [fc for fc, tag in self.teams.items() if tag == tagToGet]

    def change_tag_name(self, tag: str, new_tag: str):
        if tag == new_tag:
            return
        for fc in self.getFCsForTag(tag):
            self.setTeamForFC(fc, new_tag)
    
    def set_temp_team_tags(self, tags_player_fcs):
        self.temporary_tag_data = tags_player_fcs
        
    def get_temp_team_tags(self):
        return self.temporary_tag_data
    
    def getConvertedTempTeams(self):
        fc_tags = {}
        for teamTag, team_players in self.get_temp_team_tags().items():
            for fc, _ in team_players:
                fc_tags[fc] = teamTag
        return fc_tags
    
    def get_tags_str(self):
        if self.temporary_tag_data is None:
            return "None"
        
        result = ""
        playerNum = 0
        for teamTag, fc_players in self.temporary_tag_data.items():
            result += f"**Tag: {UtilityFunctions.clean_for_output(teamTag)}**\n"
            for fc, playerName in fc_players:
                playerNum += 1
                result += f"\t{playerNum}\. {UserDataProcessing.proccessed_lounge_add(playerName, fc)}\n"
            
        return result
    
    def get_tag_list_str(self):
        result = ""
        for tag in sorted(self.getTags()):
            result += f"**Tag: {UtilityFunctions.clean_for_output(tag)}**\n"
        
        return result
        
    def print_teams(self):
        if self.teams is None:
            raise TableBotExceptions.WarSetupStillRunning()
        for tag in self.getTags():
            print(tag + self.getFCsForTag(tag))
            
    def addEdit(self, FC, gpNum, gpScore):
        if FC not in self.manualEdits:
            self.manualEdits[FC] = {}
            
        self.manualEdits[FC][gpNum] = gpScore
    
    def getEditsForGP(self, gpNum):
        gp_edits = []
        for FC, edits in self.manualEdits.items():
            if gpNum in edits:
                gp_edits.append((FC, edits[gpNum]))
        return gp_edits
    
    def getEditAmount(self, FC, gpNum):
        if FC not in self.manualEdits or gpNum not in self.manualEdits[FC]:
            return None
        
        return self.manualEdits[FC][gpNum]
                    
    def getTeamPenalities(self):
        return self.teamPenalties
        
    def addTeamPenalty(self, team_tag, amount):
        self.teamPenalties[team_tag] += amount
    
    def set_number_of_gps(self, new_gp_count):
        self.numberOfGPs = new_gp_count

    def __str__(self):
        war_string = "-- WAR --"
        war_string += "\nNumber of teams: " + str(self.numberOfTeams)
        war_string += "\nFormat: " + str(self.formatting)
        war_string += "\nNumber of players: " + str(self.numberOfTeams*self.playersPerTeam)
        return war_string
    
    def is_ffa(self):
        return self.formatting == "1v1" or self.formatting == "ffa"
    
    
    def get_num_players(self):
        return self.numberOfTeams*self.playersPerTeam

    def clear_resolved_errors(self, room: Room, errors, resolved):
        def error_priority(err_type):
            return ['tie', 'missing_player', 'blank_player', 'gp_missing_1', 'large_time', 'gp_missing'].index(err_type)

        errors = [[k,v] for k, v in errors.items() if len(v)>0]

        for race_indx in range(len(errors)-1, -1, -1):
            race_errors = errors[race_indx][1]
            for err_indx in range(len(race_errors)-1, -1, -1):
                err = race_errors[err_indx]
                err['race'] = errors[race_indx][0]
                players = err['player_fcs'] if 'player_fcs' in err else err['player_fc']
                err_makeup = err['type'] + '-' + str(players) + '-' + str(room.getRaces()[err['race']-1].get_match_id())
                err_bytes = err_makeup.encode('ascii')
                err['id'] = base64.b64encode(err_bytes)
                if err['id'] in resolved:
                    race_errors.pop(err_indx)
            if len(race_errors) == 0: 
                errors.pop(race_indx)
            else:
                errors[race_indx][1] = sorted(race_errors, key=lambda l: error_priority(l['type']), reverse=True)

        errors = sorted(errors, key=lambda l: l[0])
        # errors = {k: v for (k, v) in errors}
        errors = list(itertools.chain.from_iterable([race[1] for race in errors]))
        return errors


    def get_war_errors_string_2(self, room: Room, resolved_errors, replaceLounge=True, up_to_race=None, suggestion_call=False):
        error_types = defaultdict(list)

        errors = ErrorChecker.get_war_errors_players(self, room, error_types, replaceLounge, ignoreLargeTimes=self.ignoreLargeTimes)
        if errors is None:
            return "Room not loaded.", "", None

        error_types = self.clear_resolved_errors(room, error_types, resolved_errors)

        if suggestion_call: 
            return error_types
        
        errors_no_large_times = ErrorChecker.get_war_errors_players(self, room, defaultdict(list), replaceLounge, ignoreLargeTimes=True)
        errors_large_times = ErrorChecker.get_war_errors_players(self, room, defaultdict(list), replaceLounge, ignoreLargeTimes=False)
        num_errors_no_large_times = sum( [ len(raceErrors) for raceErrors in errors_no_large_times.values()])
        num_errors_large_times = sum( [ len(raceErrors) for raceErrors in errors_large_times.values()])

        init_string = "Errors that might affect the table:\n"
        info_string = ""
        build_string = ""
        
        removedRaceString = room.get_removed_races_string()
        info_string += removedRaceString
        
        if self.ignoreLargeTimes and num_errors_no_large_times < num_errors_large_times:
            info_string += "- Large times occurred, but are being ignored. Table could be incorrect.\n"
        
        if room.race_order_changed():
            info_string += "- Race order changed by tabler"
        
        if up_to_race and up_to_race>0: # only show errors up to specified race if it was provided
            errors = {k: v for (k, v) in errors.items() if k<=up_to_race}

        elif len(errors) == 0 and len(info_string) == 0:
            return "Room had no errors. Table should be correct.", "", None
        
        init_string += info_string

        for raceNum, error_messages in sorted(errors.items(), key=lambda x:x[0]):
            if raceNum > len(room.races):
                build_string += "   Race #" + str(raceNum) + ":\n"
            else:
                build_string += "   Race #" + str(raceNum) + " (" + room.races[raceNum-1].getTrackNameWithoutAuthor() + "):\n"
            
            for error_message in error_messages:
                build_string += "\t- " + error_message + "\n"
        return init_string, build_string, error_types
    
    def get_all_war_errors_players(self, room, lounge_replace=True):
        return ErrorChecker.get_war_errors_players(self, room, defaultdict(list), lounge_replace, ignoreLargeTimes=False)

    def setWarName(self, warName):
        self.warName = warName
    
    def get_manually_set_war_name(self):
        return self.warName  
    
    def getWarName(self, numRaces:int):
        if self.teams is None:
            raise TableBotExceptions.WarSetupStillRunning()
        if self.warName is not None:
            return self.warName
        war_string = ""
        if self.is_ffa():
            war_string += "FFA"
            war_string += " (" + str(numRaces) + " races)"
            return war_string
        # for teamTag in set(self.teams.values()):
        #     war_string += teamTag + " vs "
        # if len(war_string) > 0:
        #     war_string = war_string[:-4]
        war_string += ' vs '.join(set(self.teams.values()))
        
        war_string = self.formatting + ": " + war_string
        war_string += " (" + str(numRaces) + " races)"
        return war_string
    
    def getTableWarName(self, numRaces:int):
        if self.warName is None:
            return str(numRaces) + " races"
        else:
            return self.getWarName(numRaces)
    
    def getNumberOfGPS(self):
        return self.numberOfGPs
    
    def getNumberOfRaces(self):
        return self.numberOfGPs*4
    
    def get_recoverable_save_state(self):
        save_state = {}
        save_state['warName'] = self.warName
        save_state['manualEdits'] = copy.deepcopy(self.manualEdits)
        save_state['teamPenalties'] = self.teamPenalties.copy()
        
        save_state['forcedRoomSize'] = self.forcedRoomSize.copy()
        save_state['teams'] = self.teams.copy()
        return save_state
    
    def restore_save_state(self, save_state):
        for save_attr, save_value in save_state.items():
            self.__dict__[save_attr] = save_value

    def is_5v5(self):
        return self.numberOfTeams == 2 and self.playersPerTeam == 5
    
        
            
