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


"""
{"format":"6","tier":"Tier 1","teams":[{"players":[{"is_sub_out":true,"multiplier":1,"player_id":3,"races":12,"score":15},{"multiplier":1,"player_id":1041,"races":12,"score":13},{"is_sub_in":true,"multiplier":1,"player_id":281,"races":12,"score":319},{"multiplier":1,"player_id":232,"races":12,"score":17},{"multiplier":1,"player_id":820,"races":12,"score":23},{"multiplier":1,"player_id":857,"races":12,"score":27},{"multiplier":1,"player_id":115,"races":12,"score":19}]},{"players":[{"multiplier":1,"player_id":323,"races":12,"score":29},{"multiplier":1,"player_id":1995,"races":12,"score":50},{"multiplier":1,"player_id":1347,"races":12,"score":55},{"multiplier":1,"player_id":1533,"races":12,"score":23},{"is_gainloss_prevented":true,player_id":349,"races":12,"score":59},{"multiplier":1,"player_id":2231,"races":12,"score":80}]}]}
{'format':'2','tier':'Tier 1','teams':[{'players':[{'player_id':1961,'races':12,'score':45},{'player_id':1913,'races':12,'score':25}]},{'players':[{'player_id':2409,'races':12,'score':40},{'player_id':824,'races':12,'score':24}]},{'players':[{'player_id':40,'races':12,'score':57},{'player_id':1739,'races':12,'score':45}]},{'players':[{'player_id':402,'races':12,'score':56},{'player_id':2195,'races':12,'score':46}]},{'players':[{'player_id':1567,'races':12,'score':50},{'player_id':2270,'races':12,'score':36}]},{'players':[{'player_id':375,'races':12,'score':30},{'player_id':1154,'races':12,'score':0}]}]}"""

from typing import List
rt_tier_mappings = {"1":"Tier 1", "2":"Tier 2", "3":"Tier 3", "4":"Tier 4","4-5":"Tier 4", "5":"Tier 5", "6":"Tier 6", "7":"Tier 7", "8":"Top 50"}
ct_tier_mappings = {"1":"Tier 1", "2":"Tier 2", "3":"Tier 3", "4":"Tier 4", "5":"Tier 5", "6":"Tier 6"}



"""Iron: 0 - 999 MMR (Placement: 500) 
Bronze: 1000 - 2499 MMR (Placement: 1750) 
Silver: 2500 - 3999 MMR (Placement: 3250) 
Gold: 4000 - 5499 MMR (Placement: 4750) 
Platinum: 5500 - 6999 MMR (Placement: 6250) 
Emerald: 7000 - 8499 MMR 
Diamond: 8500 - 9999 MMR 
Master: 10000 - 10999 MMR 
Grandmaster: 11000+ MMR """
RT_MMR_CUTOFFS = [(999, "1"),
                  (2499, "2"),
                  (3999, "3"),
                  (5499, "4"),
                  (6999, "5"),
                  (8499, "6"),
                  (10000, "7"),
                  (999999, "8")]

"""Iron: 0 - 999 MMR (Placement 500) 
Bronze: 1000 - 2249 MMR (Placement 1625) 
Silver: 2250 - 3499 MMR (Placement 2875) 
Gold: 3500 - 4499 MMR (Placement 4000) 
Platinum: 4500 - 5499 MMR (Placement 5000) 
Emerald: 5500 - 6999 MMR (Placement (6250) 
Diamond: 7000 - 8499 MMR
Master: 8500 - 9999 MMR
Grandmaster: 10000+ MMR"""
CT_MMR_CUTOFFS = [(999, "1"),
                  (2249, "2"),
                  (3499, "3"),
                  (4499, "4"),
                  (5499, "5"),
                  (999999, "6")]


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
                     WRONG_PLAYER_COUNT:"Submitted tables must have exactly 12 players. If you want to submit a table with subs, they must look like this: Jacob(1)/Sarah(2/3)",
                     BAD_TABLE:"Your table is wrong. Each team must have a tag. For FFAs, just put FFA at the top of the table. Don't put any other tags for 'teams' in FFAs.",
                     PLAYER_BAD_STRING:"Each player must have a name and a score - check Lorenzi's site for help_documentation if you don't know how to table",
                     SUB_BAD_STRING:"Subs must be in the following format: Jacob(1)/Sarah(2/3) - If you had a sub in the middle of the GP, ping reporter for manual table submission.",
                     SUB_WRONG_RACE_COUNT:"Subs races must add up to 12 (eg Jacob(1)/Sarah(2/3))",
                     SUB_WRONG_GP_COUNT:"Subs GPs must be exactly 3. (eg 25|12|23) - If you had a sub in the middle of the GP, ping reporter for manual table submission.",
                     PLAYER_NOT_FOUND_EC:"One of the players was not found in your table. I can't handle new (placement) players. If you're trying to submit a table with subs, subs must look like this: Jacob(1)/Sarah(2/3)",
                     CORRUPT_DATA_EC:"Received corrupt data from API. (This isn't your fault. This shouldn't have happened in the first place.) You can try submitting again, but it probably won't work."}
        
valid_formats = {1, 2, 3, 4, 6}
num_teams_mapping = {1:1, 6:2, 4:3, 3:4, 2:6, 12:12}
num_teams_mapping_reverse = {12:1, 2:6, 3:4, 4:3, 6:2}

valid_score_chars = set("+-|0123456789")
hex_code_chars = set("abcdef0123456789")
default_multiplier = 1
default_races = 12

rt_summary_channels = {"1":389457592952422402,
                       "2":389457132912902154,
                       "3":389251430680231947,
                       "4":723263854124990525,
                       "4-5":761789069813350430,
                       "5":389457359887532032,
                       "6":389251259384987648,
                       "7":836668063369658398,
                       "8":843941404510257152,
                       "squadqueue":793265898436821072}
ct_summary_channels = {"1":520810732280086558,
                       "2":520810716089942017,
                       "3":520810696943075328,
                       "4":521133102425309196,
                       "5":721942047023431682,
                       "6":841730154929848410,
                       "squadqueue":793265898436821072}

def get_tier_and_summary_channel_id(tier:str, is_rt=True):
    tier = tier.lower().replace(" ", "").replace("-", "")
    if is_rt:
        if tier in ["t1", "1", "tier1"]:
            return "1", rt_summary_channels["1"]
        if tier in ["t2", "2", "tier2"]:
            return "2", rt_summary_channels["2"]
        if tier in ["t3", "3", "tier3"]:
            return "3", rt_summary_channels["3"]
        if tier in ["t4", "4", "tier4"]:
            return "4", rt_summary_channels["4"]
        if tier in ["t45", "45", "tier45"]:
            return "4-5", rt_summary_channels["4-5"]
        if tier in ["t5", "5", "tier5"]:
            return "5", rt_summary_channels["5"]
        if tier in ["t6", "6", "tier6"]:
            return "6", rt_summary_channels["6"]
        if tier in ["t7", "7", "tier7"]:
            return "7", rt_summary_channels["7"]
        if tier in ["t8", "8", "tier8"]:
            return "8", rt_summary_channels["8"]
        
        if tier in ["queuebot", "queue", "duoqueue", "triqueue", "trioqueue", "squad", "squadqueue"]:
            return "squadqueue", rt_summary_channels["squadqueue"]
    else:
        if tier in ["t1", "1", "tier1"]:
            return "1", ct_summary_channels["1"]
        if tier in ["t2", "2", "tier2"]:
            return "2", ct_summary_channels["2"]
        if tier in ["t3", "3", "tier3"]:
            return "3", ct_summary_channels["3"]
        if tier in ["t4", "4", "tier4"]:
            return "4", ct_summary_channels["4"]
        if tier in ["t5", "5", "tier5"]:
            return "5", ct_summary_channels["5"]
        if tier in ["t6", "6", "tier6"]:
            return "6", ct_summary_channels["6"]
        if tier in ["queuebot", "queue", "duoqueue", "triqueue", "trioqueue", "squad", "squadqueue"]:
            return "squadqueue", ct_summary_channels["squadqueue"]
    return None, None

def getTierFromChannelID(summaryChannelID:int) -> str:
    for tier, channelID in rt_summary_channels.items():
        if channelID == summaryChannelID:
            if tier == "squadqueue":
                return "RT Squad Queue"
            return "RT Tier " + tier
    for tier, channelID in ct_summary_channels.items():
        if tier == "squadqueue":
            return "CT Squad Queue"
        if channelID == summaryChannelID:
            return "CT Tier " + tier
    return "Unknown Tier"
    

def isJSONCorrupt(jsonData, mogiPlayerAmount=12):
    pass

def createJSON(players, mult=default_multiplier):
    pass

def create_player_json(player:Tuple[str, int, int, int], sub_in=False, sub_out=False, squadqueue=False):
    player_json = {}
    player_json["player_id"] = player[3]
    player_json["races"] = player[2]
    player_json["score"] = player[1]
    if sub_in:
        player_json["subbed_in"] = True
    if sub_out:
        player_json["subbed_out"] = True
        if not sub_in: #People who sub in and sub out do not lose mmr
            player_json["multiplier"] = 12/player[2]
    
    if squadqueue:
        if "multiplier" not in player_json:
            player_json["multiplier"] = 1
        player_json["multiplier"] = player_json["multiplier"] * 1.0
        
    return player_json
    
def create_teams_JSON(team_map:List[List[Tuple[str, int, int]]], squadqueue=False):
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
                    

                team_json.append(create_player_json(player, sub_in=sub_in, sub_out=sub_out, squadqueue=squadqueue))
        teams_JSON.append({"players":team_json})
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

#Returns an error code in the second index if it could not determine subs in parans
def pop_paranthesees(name:str):
    start_paran = name.find("(")
    end_paran = name.rfind(")")
    if start_paran == -1 or end_paran == -1 or start_paran > end_paran:
        return name, None
    new_name = name[:start_paran] + name[end_paran+1:]
    gp_str =  name[start_paran+1:end_paran].strip()
    
    if gp_str == '':
        return name, SUB_BAD_STRING
    
    if new_name == '':
        return name, SUB_BAD_STRING
    
    return new_name, gp_str


    

def determine_subs_scores(subs, scores):
    all_valid_possibilities = {"1", "2", "3", "4", "8", "12", "23"}
    one_gp_terms = {}
    two_gp_terms = {}
    removal_chars = {" ", "g", "p", "/", "-", "\\", "|"}
    sub_scores = []
    races_so_far = 0
    
    formatting_1 = 0 #They do by race count
    formatting_2 = 0 #They do by GPs played
    formatting_3 = 0 #They do by which GPs played, most common formatting
    for _, gps in subs:
        gps = "".join([c for c in gps.lower() if c not in removal_chars])
        if not gps in all_valid_possibilities:
            return SUB_BAD_STRING
        formatting_1 += int(gps)
        formatting_2 += sum([4*int(char) for char in gps])
        formatting_3 += sum([4 if char in ["1", "2", "3"] else 100 for char in gps])
        
    if formatting_1 == 12:
        one_gp_terms = {"4"}
        two_gp_terms = {"8"}
    elif formatting_3 == 12:
        one_gp_terms = {"1", "2", "3"}
        two_gp_terms = {"12", "23"}
    elif formatting_2 == 12:
        one_gp_terms = {"1"}
        two_gp_terms = {"2"}
        
        

    
    for sub_name, gps in subs:
        gps = "".join([c for c in gps.lower() if c not in removal_chars])
        if gps in one_gp_terms:
            if races_so_far == 0:
                sub_scores.append((sub_name, scores[0], 4))
            elif races_so_far == 4:
                sub_scores.append((sub_name, scores[1], 4))
            elif races_so_far == 8:
                sub_scores.append((sub_name, scores[2], 4))
            else:
                return SUB_WRONG_RACE_COUNT
            races_so_far += 4
        elif gps in two_gp_terms:
            if races_so_far == 0:
                sub_scores.append((sub_name, sum(scores[0:2]), 8))
            elif races_so_far == 4:
                sub_scores.append((sub_name, sum(scores[1:3]), 8))
            else:
                return SUB_WRONG_RACE_COUNT
            races_so_far += 8
        else:
            return SUB_WRONG_RACE_COUNT
    return sub_scores
                
            
            

def getSubScores(name:str, scores):
            
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
        subs.append(pop_paranthesees(player))
    
    
    
    #Check to see if an error code (int) is in the 2nd index
    #If it is, just return the player name as normal and their score (will throw an error to
    #the user that the player name couldn't be found)
    for player_name, gps_str in subs:
        if not isinstance(player_name, str) or player_name == "" or\
        not isinstance(gps_str, str) or gps_str == "":
            return [(name, sum(scores))]
    
    if len(subs) > 1:
        if len(scores) != 3:
            return SUB_WRONG_GP_COUNT
        else:
            sub_scores = determine_subs_scores(subs, scores)
            if sub_scores is None:
                return [(name, sum(scores))]
            return sub_scores
        
    else:
        return [(name, sum(scores))]
        
    return [(name, sum(scores))]

def fix_name(name:str):
    return name.replace('\u00E9', "e")


def getNameAndScore(line:str):
    scores = []
    curNum = ""
    for ind, char in reversed(list(enumerate(line))):
        if char == " ":
            scores.append(_process_num_(curNum))
            name = remove_flag(line[:ind+1].strip())
            name = fix_name(name)
            if name == "":
                return [(None, sum(scores))]
            scores.reverse() #We appended backwards
            return getSubScores(name, scores)
            
        
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
            return [(None, sum(scores))]

    return [(None, sum(scores))] #Empty string
        

def getPlayersAndScores(table_lines:List[str]):
    teams = []
    start_of_team = True
    for line in table_lines:
        if line.startswith("#"): #A comment
            continue
        
        if line_is_valid_player(line):
            if start_of_team:
                teams.append([])
            start_of_team = False
            
            linePackage = getNameAndScore(line)
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
def determine_tier(id_mapping, is_rt=True):
    lowest_mmr = id_mapping[min(id_mapping, key=lambda k: id_mapping[k][2])][2]
    cutoffs = RT_MMR_CUTOFFS if is_rt else CT_MMR_CUTOFFS
    for cutoff, tier in cutoffs:
        if lowest_mmr <= cutoff:
            return tier
    return None
    
            

async def textInputUpdate(tableText:str, tier:str, warFormat=None, is_rt=True):
    squadqueue = False
    if tier == "squadqueue":
        squadqueue = True
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
    
    EC, players_and_scores = getPlayersAndScores(table_lines)
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
    
    

    id_mapping, missing = await MogiUpdateAPIFunctions.getPlayerIDs(three_deep_flatten(players_and_scores), is_rt)
    
    if id_mapping is None:
        return CORRUPT_DATA_EC, None, id_mapping
    elif len(missing) > 0:
        return PLAYER_NOT_FOUND_EC, None, missing
    
    if tier == "squadqueue":
        tier = determine_tier(id_mapping)
        
    if is_rt:
        if tier not in rt_tier_mappings:
            return None, None, None
        json_data["tier"] = rt_tier_mappings[tier]
    else:
        if tier not in ct_tier_mappings:
            return None, None, None
        json_data["tier"] = ct_tier_mappings[tier]
    
    team_map, success = map_to_teams(players_and_scores, id_mapping)
    
    if not success:
        return None, None, None
    
    json_data["teams"] = create_teams_JSON(team_map, squadqueue)
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
    #loop = asyncio.get_event_loop()
    #loop.run_until_complete(textInputUpdate(test_table_text_3, "1"))
    #loop.close()
    
        