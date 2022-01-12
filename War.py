'''
Created on Jul 13, 2020

@author: willg
'''
from typing import Dict, Tuple, List, Set, DefaultDict
import ErrorChecker
from collections import defaultdict
import random
import TableBotExceptions
import UtilityFunctions
import UserDataProcessing

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


class War(object):
    '''
    classdocs
    '''
    GP_SIZE = 4

    _war_format_players_per_team = {u"ffa": 1, u"1v1": 1, u"2v2": 2,
                                    u"3v3": 3, u"4v4": 4, u"5v5": 5, u"6v6": 6}

    def __init__(self, format_: str, number_of_teams: str, message_id: int, num_of_GPs=3,
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
        self.war_id = message_id

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

        if not UtilityFunctions.isint(number_of_teams):
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
    def get_teg_for_FC(self, FC: str) -> str:
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



    def set_temporary_tag_fcs(self, tag_fcs):
        self._temporary_tags_fcs = tag_fcs

    def get_temp_team_tags(self):
        return self._temporary_tags_fcs

    def getConvertedTempTeams(self):
        fc_tags = {}
        for teamTag, team_players in self.get_temp_team_tags().items():
            for fc, _ in team_players:
                fc_tags[fc] = teamTag
        return fc_tags

    def get_tags_str(self):
        if self._temporary_tags_fcs is None:
            return "None"

        result = ""
        playerNum = 0
        for teamTag, fc_players in self._temporary_tags_fcs.items():
            result += f"**Tag: {UtilityFunctions.process_name(teamTag)}** \n"
            for fc, playerName in fc_players:
                playerNum += 1
                result += f"\t{playerNum}. {UtilityFunctions.process_name(playerName)}{UserDataProcessing.lounge_add(fc)}\n"

        return result

    def addEdit(self, FC: str, gp_number: int, gp_score: int):
        if FC not in self.get_edited_scores():
            self.get_edited_scores()[FC] = []

        index = None
        # Need to remove previous edit for this player's GP, if it exists
        for i, (cur_gp_number, _) in enumerate(self.get_edited_scores()[FC]):
            if cur_gp_number == gp_number:
                index = i
                break
        if index is not None:
            del self.get_edited_scores()[FC][index]

        self.get_edited_scores()[FC].append((gp_number, gp_score))

    def getEditsForGP(self, gpNum):
        gp_edits = []
        for FC, edits in self.get_edited_scores().items():
            for curGPNum, score in edits:
                if curGPNum == gpNum:
                    gp_edits.append((FC, score))
        return gp_edits

    def getEditAmount(self, FC, gpNum):
        if FC in self.get_edited_scores():
            for edit in self.get_edited_scores()[FC]:
                if edit[0] == gpNum:
                    return edit[1]
        return None

    def addTeamPenalty(self, team_tag, amount):
        self.get_team_penalties()[team_tag] += amount

    def get_war_errors_string_2(self, room, replaceLounge=True, up_to_race=None):
        errors = ErrorChecker.get_war_errors_players(
            self, room, replaceLounge, show_large_time_errors=self.should_show_large_time_errors())
        if errors is None:
            return "Room not loaded."

        errors_no_large_times = ErrorChecker.get_war_errors_players(
            self, room, replaceLounge, show_large_time_errors=True)
        errors_large_times = ErrorChecker.get_war_errors_players(
            self, room, replaceLounge, show_large_time_errors=False)
        num_errors_no_large_times = sum(
            [len(raceErrors) for raceErrors in errors_no_large_times.values()])
        num_errors_large_times = sum(
            [len(raceErrors) for raceErrors in errors_large_times.values()])
        build_string = "Errors that might affect the table:\n"

        removedRaceString = room.get_removed_races_string()
        build_string += removedRaceString

        if not self.should_show_large_time_errors() and num_errors_no_large_times < num_errors_large_times:
            build_string += "- Large times occurred, but are being ignored. Table could be incorrect.\n"

        if up_to_race and up_to_race > 0:  # only show errors up to specified race if it was provided
            errors = {k: v for (k, v) in errors.items() if k <= up_to_race}

        elif len(errors) == 0 and len(removedRaceString) == 0:
            return "Room had no errors. Table should be correct."

        for raceNum, error_messages in sorted(errors.items(), key=lambda x: x[0]):
            if raceNum > len(room.races):
                build_string += "   Race #" + str(raceNum) + ":\n"
            else:
                build_string += "   Race #" + \
                    str(raceNum) + " (" + \
                    room.races[raceNum-1].getTrackNameWithoutAuthor() + "):\n"

            for error_message in error_messages:
                build_string += "\t- " + error_message + "\n"
        return build_string


    def get_all_war_errors_players(self, room, lounge_replace=True):
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


    # ================ Save state functions ===================

    def get_recoverable_save_state(self):
        save_state = {}
        save_state['_user_defined_war_name'] = self.get_user_defined_war_name()
        save_state['_edited_scores'] = self.get_edited_scores().copy()
        save_state['_team_penalties'] = self.get_team_penalties().copy()
        save_state['teams'] = self.get_teams().copy()
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
