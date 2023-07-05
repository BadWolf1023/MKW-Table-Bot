'''
Created on Sep 23, 2020

@author: willg

This module does all the heavy lifting for the commands ?rtmogiupdate and ?ctmogiupdate
Interestingly, we have to recreate Lorenzi's table text parser without any knowledge, except for trying different things on his website and seeing how his parser reacts
Even if we don't recreate his parser exactly, if it's close enough and handles how people normally table, this will be sufficient,
since we'll just "give up" if their table isn't normal
'''

import MogiUpdateAPIFunctions
from MogiUpdateAPIFunctions import getLookup
import re
import json
two_deep_flatten = lambda t: [item for sublist in t for item in sublist]
three_deep_flatten = lambda t: [item for L1 in t for L2 in L1 for item in L2]
from typing import Tuple
import common
import discord


"""
{"format":"6","tier":"Tier 1","teams":[{"players":[{"is_sub_out":true,"multiplier":1,"player_id":3,"races":12,"score":15},{"multiplier":1,"player_id":1041,"races":12,"score":13},{"is_sub_in":true,"multiplier":1,"player_id":281,"races":12,"score":319},{"multiplier":1,"player_id":232,"races":12,"score":17},{"multiplier":1,"player_id":820,"races":12,"score":23},{"multiplier":1,"player_id":857,"races":12,"score":27},{"multiplier":1,"player_id":115,"races":12,"score":19}]},{"players":[{"multiplier":1,"player_id":323,"races":12,"score":29},{"multiplier":1,"player_id":1995,"races":12,"score":50},{"multiplier":1,"player_id":1347,"races":12,"score":55},{"multiplier":1,"player_id":1533,"races":12,"score":23},{"is_gainloss_prevented":true,player_id":349,"races":12,"score":59},{"multiplier":1,"player_id":2231,"races":12,"score":80}]}]}
{'format':'2','tier':'Tier 1','teams':[{'players':[{'player_id':1961,'races':12,'score':45},{'player_id':1913,'races':12,'score':25}]},{'players':[{'player_id':2409,'races':12,'score':40},{'player_id':824,'races':12,'score':24}]},{'players':[{'player_id':40,'races':12,'score':57},{'player_id':1739,'races':12,'score':45}]},{'players':[{'player_id':402,'races':12,'score':56},{'player_id':2195,'races':12,'score':46}]},{'players':[{'player_id':1567,'races':12,'score':50},{'player_id':2270,'races':12,'score':36}]},{'players':[{'player_id':375,'races':12,'score':30},{'player_id':1154,'races':12,'score':0}]}]}"""

from typing import List

SUCCESS_EC = 0
INVALID_RT_NUM_EC = 101
INVALID_CT_NUM_EC = 102
TOO_MANY_TEAMS_EC = 301
DIFFERING_NUM_PLAYERS_EC = 401
WRONG_PLAYER_COUNT = 402
PLAYER_BAD_STRING = 501 #general error if player strings are formatted wrong
SUB_BAD_STRING = 502
SUB_WRONG_RACE_COUNT = 503
SUB_WRONG_GP_COUNT = 504
BAD_TABLE = 505
PLAYER_NOT_FOUND_EC = 601
CORRUPT_DATA_EC = 701
table_text_errors = {INVALID_RT_NUM_EC:"Tier number is not an RT Tier",
                     INVALID_CT_NUM_EC:"Tier number is not a CT Tier",
                     TOO_MANY_TEAMS_EC:"The table text doesn't match a mogi format - there are too many or too few teams",
                     DIFFERING_NUM_PLAYERS_EC:"Each team must have the same amount of players",
                     WRONG_PLAYER_COUNT:"Submitted tables must have exactly 12 players. If you want to submit a table with subs, they must put the number of races they played in parentheses, like this: Jacob(5)/Sarah(7)",
                     BAD_TABLE:"Your table is wrong. Each team must have a tag. For FFAs, just put FFA at the top of the table. Don't put any other tags for 'teams' in FFAs.",
                     PLAYER_BAD_STRING:"Each player must have a name and a score - check Lorenzi's site for help_documentation if you don't know how to table",
                     SUB_BAD_STRING:"Subs must be in the following format: Jacob(5)/Sarah(7)\nNote that the number of races played is in parentheses after each player.",
                     SUB_WRONG_RACE_COUNT:"Subs races must add up to the number of races (eg if races played was 12, the subs races must add up to 12: Jacob(5)/Sarah(7))",
                     SUB_WRONG_GP_COUNT:"Subs GPs are ambiguous.\nSuppose you had the following sub: Jacob(5)/Sarah(7)\nColumn 1 must be the first 4 races Jacob played, Column 2 must be the last race Jacob played. Column 3 must be the first 4 races Sarah played, and Column 4 must be the last 3 races Sarah played.",
                     PLAYER_NOT_FOUND_EC:"One of the players was not found in your table. I can't handle new (placement) players. If you're trying to submit a table with subs, subs must look like this: Jacob(5)/Sarah(7)",
                     CORRUPT_DATA_EC:"Received corrupt data from API. (This isn't your fault. This shouldn't have happened in the first place.) You can try submitting again, but it probably won't work."}
        
valid_formats = {1, 2, 3, 4, 6}
num_teams_mapping = {1:1, 6:2, 4:3, 3:4, 2:6, 12:12}
num_teams_mapping_reverse = {12:1, 2:6, 3:4, 4:3, 6:2}

valid_score_chars = set("+-|0123456789")
hex_code_chars = set("abcdef0123456789")
default_multiplier = 1
default_races = 12

rt_summary_channels = {}
ct_summary_channels = {}
sq_summaries = {"squadqueue": 793265898436821072}

if common.is_dev:
    rt_summary_channels.clear()
    rt_summary_channels.update({"1":common.TABLE_BOT_SERVER_BETA_THREE_CHANNEL_ID, "2":common.TABLE_BOT_SERVER_BETA_THREE_CHANNEL_ID, "3":common.TABLE_BOT_SERVER_BETA_THREE_CHANNEL_ID, "4":common.TABLE_BOT_SERVER_BETA_THREE_CHANNEL_ID, "4-5":common.TABLE_BOT_SERVER_BETA_THREE_CHANNEL_ID, "5":common.TABLE_BOT_SERVER_BETA_THREE_CHANNEL_ID, "6":common.TABLE_BOT_SERVER_BETA_THREE_CHANNEL_ID, "7":common.TABLE_BOT_SERVER_BETA_THREE_CHANNEL_ID, "squadqueue":common.TABLE_BOT_SERVER_BETA_THREE_CHANNEL_ID})
    ct_summary_channels.clear()
    ct_summary_channels.update({"1":common.TABLE_BOT_SERVER_BETA_THREE_CHANNEL_ID, "2":common.TABLE_BOT_SERVER_BETA_THREE_CHANNEL_ID, "3":common.TABLE_BOT_SERVER_BETA_THREE_CHANNEL_ID, "4":common.TABLE_BOT_SERVER_BETA_THREE_CHANNEL_ID, "4-5":common.TABLE_BOT_SERVER_BETA_THREE_CHANNEL_ID, "5":common.TABLE_BOT_SERVER_BETA_THREE_CHANNEL_ID, "6":common.TABLE_BOT_SERVER_BETA_THREE_CHANNEL_ID, "7":common.TABLE_BOT_SERVER_BETA_THREE_CHANNEL_ID, "squadqueue":common.TABLE_BOT_SERVER_BETA_THREE_CHANNEL_ID})


def update_summary_channels(all_channels: list):
    rt_summary_channels.clear()
    ct_summary_channels.clear()
    rt_summary_channels.update(sq_summaries)
    ct_summary_channels.update(sq_summaries)
    for channel in all_channels:
        if isinstance(channel, discord.channel.TextChannel):
            channel_name = channel.name.lower()
            summary_channel_regex = r"([rc]t)-(tier-)?(.+)-summary"
            if m := re.search(summary_channel_regex, channel_name):
                is_rt = m.groups()[0] == "rt"
                channel_summary_key = str(m.groups()[-1])
                if is_rt:
                    rt_summary_channels[channel_summary_key] = channel.id
                else:
                    ct_summary_channels[channel_summary_key] = channel.id

def update_mmr_ranges():
    #Need to hit Lounge API to update ranges
    pass


def get_tier_and_summary_channel_id(tier:str, is_rt=True):
    tier = tier.lower().replace(" ", "").replace("-", "")
    if tier in {"queuebot", "queue", "duoqueue", "triqueue", "trioqueue", "squad", "squadqueue", "sq"}:
        tier = "squadqueue"
    
    summary_channels = rt_summary_channels if is_rt else ct_summary_channels
    if f"Tier {tier}" in summary_channels:
        tier = f"Tier {tier}"
    if tier in summary_channels:
        return tier, summary_channels[tier]
    return None, None

def getTierFromChannelID(summaryChannelID:int) -> str:
    for tier, channelID in rt_summary_channels.items():
        if channelID == summaryChannelID:
            if tier == "squadqueue":
                return "RT Squad Queue"
            return "RT " + tier.capitalize()
    for tier, channelID in ct_summary_channels.items():
        if channelID == summaryChannelID:
            if tier == "squadqueue":
                return "CT Squad Queue"
            return "CT " + tier.capitalize()
    return "Unknown Tier"
    

def isJSONCorrupt(jsonData, mogiPlayerAmount=12):
    pass

def createJSON(players, mult=default_multiplier):
    pass

#- Global races played will always be the actual number of races played
# - Individual player races played will be the actual number of races they played as well
# - Multiplier for each person will be global races played ÷ 12
# - Updater Bot will leave all multipliers alone, even on subs/subbees. Updater Bot will not change any JSON except for the following: Updater Bot must change gain/loss prevention and full gain/loss on JSON appropriately for sub ins and sub outs.
def create_player_json(player:Tuple[str, int, int, int], races_played=12, sub_in=False, sub_out=False):
    player_json = {}
    player_json["player_id"] = player[3]
    player_json["score"] = player[1]
    
    if races_played != player[2]:
        player_json["races"] = player[2] #since the races they played is not the global race count, change their individual race count appropriately
    
    if sub_in:
        player_json["subbed_in"] = True
    if sub_out:
        player_json["subbed_out"] = True
    
    if races_played != 12: #Default multiplier is 1.0, so if 12 races are played, 1.0 is the right multiplier and we don't need to include it
        player_json["multiplier"] = round(races_played / 12, 3) #Multiplier for each person will be global races played ÷ 12
        
    return player_json

def sort_teams_json(teams_JSON):
    team_players_sort_key = lambda player: (player["score"], player["player_id"])
    teams_sort_key = lambda team: (sum(player["score"] for player in team["players"]), max(player["player_id"] for player in team["players"]))
    for team in teams_JSON:
        team["players"].sort(key=team_players_sort_key, reverse=True)
    teams_JSON.sort(key=teams_sort_key, reverse=True)

def create_teams_JSON(team_map:List[List[Tuple[str, int, int]]], races_played=12):
    teams_JSON = []
    for team in team_map:
        team_json = []
        for player_line in team:
            last_ind = len(player_line) - 1
            for ind, player in enumerate(player_line):
                sub_in = False
                sub_out = False
                if last_ind > 0:
                    if ind == 0:
                        sub_out = True
                    else:
                        sub_in = True
                        if ind < last_ind: #They subbed in and out :LUL:
                            sub_out = True
                    

                team_json.append(create_player_json(player, races_played, sub_in=sub_in, sub_out=sub_out))
        teams_JSON.append({"players":team_json})
    #import pprint
    #print("Before sort:")
    #pprint.pprint({"teams":teams_JSON})
    sort_teams_json(teams_JSON)
    #print("After sort:")
    #pprint.pprint({"teams":teams_JSON})
    return teams_JSON
           
 
def ends_with_hex_code(line:str):
    temp = line.lower().strip()
    if len(temp) < 7:
        return False
    return temp[-1] in hex_code_chars and temp[-2] in hex_code_chars and temp[-3] in hex_code_chars\
        and temp[-4] in hex_code_chars and temp[-5] in hex_code_chars and temp[-6] in hex_code_chars\
        and temp[-7] == '#'
    
def line_is_valid_player(line:str):
    if len(line) == 0:
        return False
    if ends_with_hex_code(line):
        return False
    if line[-1] not in valid_score_chars:
        return False
    for char in line[::-1]:
        if char in valid_score_chars:
            continue
        return char == " " #examine what I did closely. No, this isn't a mistake
    return False

def is_odd_ffa(table_lines:List[str]):
    for ind, line in enumerate(table_lines):
        if line.startswith("#"):
            continue
        if line_is_valid_player(line):
            for line in table_lines[ind:]:
                if line.startswith("#"):
                    continue
                if not line_is_valid_player(line):
                    return None #corrupt table
            return True #all were players, table just didn't have a header
        else:
            return False #first item was a tag
    return False
    
def getNumTeams(table_lines:List[str]):
    start_of_team = True
    num_teams = 0
    for line in table_lines:
        if line.startswith("#"): #A comment
            continue
        
        if line_is_valid_player(line):
            if start_of_team:
                num_teams += 1
            start_of_team = False
        else:
            start_of_team = True
    return num_teams

def eachTeamHasCorrectNumPlayers(players_and_scores, warFormat):
    if len(players_and_scores) < 1:
        return False
    
    for team in players_and_scores:
        if len(team) != warFormat:
            return False
    return True

def _process_num_(num_str:str):
    if num_str == "":
        return 0
    num_str = num_str.rstrip("+-")
    if num_str == "":
        return 0
    num = ""
    
    should_negate = False
    for char in num_str[::-1]:
        if char.isnumeric():
            num = char+num
        else:
            if char == "-":
                should_negate = True
    if num == "":
        return 0
    if not num.isnumeric():
        return 0
    
    num = int(num)
    if should_negate:
        num = -num
    return num



#lazy, stack exchange for this one liner: https://stackoverflow.com/questions/19859282/check-if-a-string-contains-a-number
def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)


def remove_flag(name):
    return re.sub(r'\[.*\]',"",name).strip()

#Returns an error code in the second index if it could not determine subs in parens
def pop_parentheses(name:str):
    start_paren = name.find("(")
    end_paren = name.rfind(")")
    if start_paren == -1 or end_paren == -1 or start_paren > end_paren:
        return name, None
    new_name = name[:start_paren] + name[end_paren+1:]
    races_player_str =  name[start_paren+1:end_paren].strip()
    
    if races_player_str == '':
        return name, SUB_BAD_STRING
    
    if new_name == '':
        return name, SUB_BAD_STRING
    
    return new_name, races_player_str


    

def determine_subs_scores(subs, scores, races_played=12):
    #TODO: Check if 
    all_valid_possibilities = {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15",
                               "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29",
                               "30", "31", "32"}

    sub_scores = []

    total_races_played = 0
    for index, (sub_name, sub_races_played) in enumerate(subs):
        if sub_races_played not in all_valid_possibilities:
            return SUB_WRONG_RACE_COUNT
        subs[index] = (sub_name, int(sub_races_played))
        total_races_played += subs[index][1]
    
    if total_races_played != races_played:
        return SUB_WRONG_RACE_COUNT
    
    def determine_columns_needed(subs):
        needed = 0
        for sub_name, sub_races_played in subs:
            full_columns = sub_races_played // 4
            partial_columns = 0 if (sub_races_played % 4 == 0) else 1
            needed += full_columns + partial_columns
        return needed
    
    columns_needed = determine_columns_needed(subs)
    
    if columns_needed != len(scores):
        return SUB_WRONG_GP_COUNT
        

    cur_column = 0
    for sub_name, sub_races_played in subs:
        columns_needed_for_sub = determine_columns_needed([(sub_name, sub_races_played)])
        sub_scores.append((sub_name, sum(scores[cur_column:cur_column+columns_needed_for_sub]), sub_races_played))
        cur_column += columns_needed_for_sub
    return sub_scores
                
            
            

def getSubScores(name:str, scores, races_played=12):
            
    players = []
    start_ind = 0
    end_ind = 0
    for ind, char in enumerate(name):
        if char == ")":
            end_ind = ind+1
            players.append(name[start_ind:end_ind].strip(" /\\|-"))
            start_ind = ind+1
    else:
        players.append(name[start_ind:].strip(" /\\|-"))
    
    ind_to_remove = []
    for ind, player in enumerate(players):
        if player == "":
            ind_to_remove.append(ind)
            
    for ind in ind_to_remove[::-1]:
        del players[ind]
        

    subs = []
    
    for player in players:
        subs.append(pop_parentheses(player))
        
    #Check to see if an error code (int) is in the 2nd index
    #If it is, just return the player name as normal and their score (will throw an error to
    #the user that the player name couldn't be found)
    
    #TODO: Here is where we modify code to support mid-gp subs
    for player_name, races_player_str in subs:
        if not isinstance(player_name, str) or player_name == "" or not isinstance(races_player_str, str) or races_player_str == "":
            return [(name, sum(scores), races_played)]
    
    if len(subs) > 1:
        sub_scores = determine_subs_scores(subs, scores, races_played)
        if sub_scores is None:
            return [(name, sum(scores), races_played)]
        return sub_scores
        
    else:
        return [(name, sum(scores), races_played)]
        
    return [(name, sum(scores), races_played)]

def fix_name(name:str):
    return name.replace('\u00E9', "e")


def getNameAndScore(line:str, races_played=12):
    scores = []
    curNum = ""
    for ind, char in reversed(list(enumerate(line))):
        if char == " ":
            scores.append(_process_num_(curNum))
            name = remove_flag(line[:ind+1].strip())
            name = fix_name(name)
            if name == "":
                return [(None, sum(scores), races_played)]
            scores.reverse() #We appended backwards
            return getSubScores(name, scores, races_played)
            
        
        curNum = char+curNum
        if char == "|":
            scores.append(_process_num_(curNum))
            curNum = ""
        elif char == "+" or char == "-":
            if hasNumbers(curNum):
                scores.append(_process_num_(curNum))
                curNum = ""
        elif char.isnumeric():
            continue
        else:
            return [(None, sum(scores), races_played)]

    return [(None, sum(scores), races_played)] #Empty string
        

def getPlayersAndScores(table_lines:List[str], races_played=12):
    teams = []
    start_of_team = True
    for line in table_lines:
        if line.startswith("#"): #A comment
            continue
        
        if line_is_valid_player(line):
            if start_of_team:
                teams.append([])
            start_of_team = False
            
            linePackage = getNameAndScore(line, races_played)
            #Check if it's an error code
            if isinstance(linePackage, int):
                return linePackage, None
            
            for player_data in linePackage:
                if player_data is None:
                    return PLAYER_BAD_STRING, player_data
                for item in player_data:
                    if item is None: #TODO: Come back here
                        return PLAYER_BAD_STRING, player_data 
            teams[-1].append(linePackage)
        else:
            start_of_team = True
    return SUCCESS_EC, teams
            
            
def process_table_text(tableText:str):
    lines = tableText.split("\n")
    good_lines = []
    for line in lines:
        line=line.strip(" \t\n")
        if line != "":
            good_lines.append(line)
            
    odd_ffa = is_odd_ffa(good_lines)
    if odd_ffa is None:
        return BAD_TABLE, BAD_TABLE
    if odd_ffa:
        good_lines.insert(0, "FFA")
        tableText = "FFA\n" + tableText
    return tableText, good_lines

def map_to_teams(players_and_scores, id_mapping):
    id_mapping_new = {}
    for key, val in id_mapping.items():
        id_mapping_new[getLookup(key)] = val
    players_and_scores_new = []
    
    success = True
    
    for team in players_and_scores:
        players_and_scores_new.append([])
        for player_line in team:
            players_and_scores_new[-1].append([])
            for data in player_line:
                num_races = 12
                if len(data) > 2:
                    num_races = data[2]
                lookup = getLookup(data[0])
                if lookup not in id_mapping_new:
                    success = False
                else:
                    players_and_scores_new[-1][-1].append((data[0], data[1], num_races, id_mapping_new[lookup][0]))
    return players_and_scores_new, success

#Each "player" is a list of tuples - usually this list will be one tuple,
#with the player's name and score, but if they had subs, this list will contain multiple tuples with
#their name, score, and races played
#Each team is a list of players
#And the overall structure is a list of teams
#Eg [team1, team2]
# team1 = [player_line_1, player_line_2]
# player_line_1 = [("promise", 75)]
# player_line_2 = [("jacob", 40, 8), ("sarah", 20, 4)]

def sort_teams_by_scores(teams:List[List[List[Tuple[str, int]]]]):
    new_teams = []
    for team in teams:
        temp_team = []
        for p_ind, player_list in enumerate(team):
            temp_team.append([player_list, p_ind])
        temp_team.sort(key=lambda plr: (-sum([ p[1] for p in plr[0] ]), plr[1]))
        sorted_team = []
        for item in temp_team:
            sorted_team.append(item[0])
        new_teams.append(sorted_team)
    return new_teams

#This is for Squad Queue - the tier shall be the highest tier that the lowest mmr player can access         

async def textInputUpdate(tableText:str, tier:str, races_played=12, warFormat=None, is_rt=True):
    newTableText, table_lines = process_table_text(tableText)
    if newTableText == BAD_TABLE:
        return BAD_TABLE, None, None
    
    numTeams = None
    if not warFormat:
        numTeams = getNumTeams(table_lines)
        if numTeams not in num_teams_mapping:
            return TOO_MANY_TEAMS_EC, None, None
        warFormat = num_teams_mapping[numTeams]
    else:
        numTeams = num_teams_mapping_reverse[warFormat]
    
    EC, players_and_scores = getPlayersAndScores(table_lines, races_played)
    if EC != SUCCESS_EC:
        return EC, None, players_and_scores
    
    
    if warFormat == 1:
        temp = []
        if len(players_and_scores) > 0:
            for data in players_and_scores[0]:
                temp.append([data])
            players_and_scores = temp
            
    if warFormat == 12:
        warFormat = 1
            
    players_and_scores = sort_teams_by_scores(players_and_scores)
    
    
    if not eachTeamHasCorrectNumPlayers(players_and_scores, warFormat):
        return DIFFERING_NUM_PLAYERS_EC, None, None
    
    if len(two_deep_flatten(players_and_scores)) != 12:
        return WRONG_PLAYER_COUNT, None, None
    
    
    json_data = {}
    json_data["format"] = str(warFormat)
    json_data["races"] = races_played
    
    
    id_mapping, missing = await MogiUpdateAPIFunctions.getPlayerIDs(three_deep_flatten(players_and_scores), is_rt)
    
    if id_mapping is None:
        return CORRUPT_DATA_EC, None, id_mapping
    elif len(missing) > 0:
        return PLAYER_NOT_FOUND_EC, None, missing
    
    if tier == "squadqueue":
        tier = "Squad Queue"
    else:
        tier = "Tier " + tier
        
    json_data["tier"] = tier
    
    team_map, success = map_to_teams(players_and_scores, id_mapping)
    
    if not success:
        return None, None, None
    
    json_data["teams"] = create_teams_JSON(team_map, races_played)
    json_dump = json.dumps(json_data, separators=(',', ':'))
    
    return SUCCESS_EC, newTableText, json_dump

if __name__ == '__main__':
    test_table_text_1 = """
promise 29|29|42
Garrett [us_tx] 24|39|37
Glaceon 18|19|26
Raeika [us_ca] 24|7|36
PhillyGator [lb] 32|33|23
me3 [jp] 10|28|32
Pharis 23|31|26
Saionji 19|20|11
Axis 49|20|29
Wheel4life [at] 25|38|19
Spock [ca] 17|13|8
Eimii [jp] 22|15|13"""
    test_table_text_2 = """#title 12 races
A
promise 29|29|42
Garrett [us_tx] 24|39|37

G
Glaceon 18|19|26
Raeika [us_ca] 24|7|36

Me3
PhillyGator [lb] 32|33|23
me3 [jp] 10|28|32

P
Pharis 23|31|26
Saionji 19|20|11

W
Axis 49|20|29
Wheel4life [at] 25|38|19
e
Spock [ca] 17|13|8
Eimii [jp] 22|15|13"""
    test_table_text_3 = """#title 12 races
A
Garrett [us_tx] 24|39|37
promise(4)/Bad Wolf(8) 29|29|0

G
Glaceon 18|19|26
Raeika [us_ca] 24|7|36

Me3
PhillyGator [lb] 32|33|23
me3 [jp] 10|28|32

P
Pharis 23|31|26
Saionji 19|20|11

W
Axis 49|20|29
Wheel4life [at] 25|38|19
e
Spock [ca] 17|13|8
Eimii [jp] 22|15|13"""
    test_table_text_4 = """
promise 29|29|42
Garrett [us_tx] 24|39|37
Glaceon 18|19|26
Raeika [us_ca] 24|7|36
PhillyGator [lb] 32|33|23
me3 [jp] 10|28|32
Pharis(1)/BadWolf(2) 23|31|26
Saionji(4)Kasperinos(4)KasperUS(4) 19|20|11
Axis 49|20|29
Wheel4life [at] 25|38|19
Spock [ca] 17|13|8
Eimii [jp] 22|15|13"""
    test_table_text_5 = """?ctupdate sq 12

Timmi
Tim [de] 37|28|23
Revenant [us_sc] 25|29|34

sos
dhavz [in] 29|23|25
Wob [us] 24|17|35

JsFJ
Empex [cl_lr] 28|29|47
Helpy [de] 16|9|22

S
oatmeal [lc] 22|35|15
margio [lb] 18|17|25

E
Spock [in] 19|44|21
BadWolf [us_tx] 31|9|5

G
quiescent [us] 13|24|12
noshow [us] 18|18|18"""
    print(common.run_async_function_no_loop(textInputUpdate(test_table_text_5, "squadqueue")))

    
        
