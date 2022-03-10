'''
Created on Jul 12, 2020

@author: willg
'''
import Room
import UserDataProcessing
from discord.utils import escape_markdown, escape_mentions
from collections import defaultdict
from typing import List
import TableBot
import UtilityFunctions
DEBUGGING = False


scoreMatrix = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [15, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [15, 8, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [15, 9, 4, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    [15, 9, 5, 2, 1, 0, 0, 0, 0, 0, 0, 0],
    [15, 10, 6, 3, 1, 0, 0, 0, 0, 0, 0, 0],
    [15, 10, 7, 5, 3, 1, 0, 0, 0, 0, 0, 0],
    [15, 11, 8, 6, 4, 2, 1, 0, 0, 0, 0, 0],
    [15, 11, 8, 6, 4, 3, 2, 1, 0, 0, 0, 0],
    [15, 12, 10, 8, 6, 4, 3, 2, 1, 0, 0, 0],
    [15, 12, 10, 8, 6, 5, 4, 3, 2, 1, 0, 0],
    [15, 12, 10, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    ]

alternate_Matrices = {
    771417753843925023:[
    [15, 0 ,0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [15, 9 ,0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [15, 10 ,5, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [15, 11 ,7, 3, 0, 0, 0, 0, 0, 0, 0, 0],
    [15, 11 ,8, 5, 3, 0, 0, 0, 0, 0, 0, 0],
    [15, 11 ,9, 6, 4, 3, 0, 0, 0, 0, 0, 0],
    [15, 12 ,10, 7, 5, 4, 3, 0, 0, 0, 0, 0],
    [15, 13 ,10, 8, 6, 4, 3, 2, 0, 0, 0, 0],
    [15, 13 ,10, 8, 7, 6, 4, 3, 2, 0, 0, 0],
    [15, 13 ,11, 9, 8, 6, 5, 4, 3, 2, 0, 0],
    [15, 13 ,12, 10, 8, 7, 6, 5, 3, 2, 1, 0],
    [15, 13 ,12, 10, 8, 7, 6, 5, 3, 2, 1, 0]
    ]}


def print_scores(fc_score, fc_player):
    for fc, score in sorted(fc_score.items(), key=lambda x: x[1], reverse=True):
        print(fc_player[fc] + " (" + fc + "): " + str(score))
    
    
#Calculates the scores from the start race to the end race (eg startRace = 1 and endRace = 4 would be GP1)
def calculateScoresDCs(curRoom:Room.Room, startRace=1, endRace=12, missingRacePts=3, server_id=None):
    #disconnections = curRoom.getMissingOnRace()
    fc_score = {}
    fc_player = curRoom.get_fc_to_name_dict(startRace, endRace)
    for fc in fc_player:
        fc_score[fc] = []
    #If the races completed is less than the start race, no one has score anything yet - That's in the future!
    if len(curRoom.getRaces()) < startRace:
        return fc_score
    
    
    
    #Iterating over the splice - no, this isn't an error. Check how splicing works, this won't go out of bounds.
    for raceNum, race in enumerate(curRoom.getRaces()[startRace-1:endRace], startRace):
        mkwxNumRacers = race.numRacers()
        if mkwxNumRacers != len(fc_player.keys()):
            #Someone is missing. Need to give them the specified DC points.
            raceFCs = race.getFCs()
            for fc in fc_player:
                # if raceNum in curRoom.dc_on_or_before:
                #     if fc in curRoom.dc_on_or_before[raceNum]:
                #         if curRoom.dc_on_or_before[raceNum][fc] == 'on':
                #             mkwxNumRacers += 1
                
                
                if fc not in raceFCs:
                    was_in_manual_dcs = False
                    if raceNum in curRoom.dc_on_or_before:
                        if fc in curRoom.dc_on_or_before[raceNum]:
                            was_in_manual_dcs = True
                            points_to_get = 0
                            if curRoom.dc_on_or_before[raceNum][fc] == 'on':
                                points_to_get = 0
                            else:
                                points_to_get = missingRacePts
                            fc_score[fc].append( points_to_get )
                    if not was_in_manual_dcs:    
                        fc_score[fc].append(missingRacePts)
                        
        if raceNum in curRoom.forcedRoomSize:
            mkwxNumRacers = curRoom.forcedRoomSize[raceNum]
            
        if mkwxNumRacers > 12:
            mkwxNumRacers = 12
            
        for placement in race.getPlacements():
            placement_score = 0
            if placement.place <= 12: #Only get people's score if their place is less than 12
                if server_id in alternate_Matrices:
                    placement_score = alternate_Matrices[server_id][mkwxNumRacers-1][placement.place-1]
                else:
                    placement_score = scoreMatrix[mkwxNumRacers-1][placement.place-1]
            
            fc_score[placement.player.FC].append( placement_score )
    #Fille awkward sized arrays with 0
    for fc in fc_score:
        difference = endRace-(startRace-1) - len(fc_score[fc])
        if difference > 0:
            for _ in range(difference):
                fc_score[fc].append(0)
        
    
                
    return fc_score

    
def calculateGPScoresDCS(GPNumber, curRoom, missingRacePts=3, server_id=None):
    startRace = ((GPNumber-1)*4)+1
    endRace = GPNumber * 4
    return calculateScoresDCs(curRoom, startRace, endRace, missingRacePts, server_id)

def chunk_list(to_chunk:List, n):
    """Yield successive n-sized chunks from the given list."""
    for i in range(0, len(to_chunk), n):
        yield to_chunk[i:i + n]

        
#Takes a GPs list and resizes into a new GP size
#Previous code seems to guarantee that everyone will have the same number of scores
#If this is not true, bugs can happen
def resizeGPsInto(GPs, new_size_GP):
    total_GP_dict = defaultdict(list)
    for GP_scores in GPs:
        for fc, scores in GP_scores.items():
            for score in scores:
                total_GP_dict[fc].append(score)
    
    
    new_gps = []
    if len(total_GP_dict) == 0:
        return []
    for fc, player_scores in total_GP_dict.items():
        total_GP_dict[fc] = [gp_chunk for gp_chunk in chunk_list(player_scores, new_size_GP)]
        extra_gps_needed = len(total_GP_dict[fc]) - len(new_gps)
        if extra_gps_needed > 0:
            for _ in range(extra_gps_needed):
                new_gps.append({})
    
    
    for fc, player_scores in total_GP_dict.items():
        for new_gp_ind, new_gp in enumerate(new_gps):
            if new_gp_ind <= len(player_scores):
                new_gp[fc] = player_scores[new_gp_ind]
            else:
                new_gp[fc] = []
    return new_gps

def create_table_dict():
    return {
        "title_str": "",
        "teams": {}
    }

def create_team():
    return {"table_str": "",
            "total_score": 0,
            "penalties": 0,
            "players": {},
            "hex_color": ""
    }

def create_player():
    return {"table_str": "",
            "mii_name": "",
            "lounge_name": "",
            "table_name": "",
            "tag": "",
            "total_score": 0,
            "had_penalties": False,
            "penalties": 0,
            "subbed_out": False,
            "race_scores": [],
            "gp_scores": [],
            "flag": ""
            }

def get_war_table_DCS(channel_bot:TableBot.ChannelBot, use_lounge_otherwise_mii=True, use_miis=False, lounge_replace=None, server_id=None, missingRacePts=3, discord_escape=False, step=None, up_to_race=None):
    war = channel_bot.getWar()
    room = channel_bot.getRoom()
    if step is None:
        step = channel_bot.get_race_size()
    numGPs = war.getNumberOfGPS()
    GPs = []
    use_lounge_names = lounge_replace
    for x in range(numGPs):
        GPs.append(calculateGPScoresDCS(x+1, room, missingRacePts, server_id))
        
    fcs_players = room.get_fc_to_name_dict(1, numGPs*4)
    
    FC_table_dict = {}
    table_dict = create_table_dict()
    
    
    for fc, mii_name in fcs_players.items():
        FC_table_dict[fc] = create_player()
        player_tag = war.getTeamForFC(fc)
        
        player_table_name = mii_name
        lounge_name = UserDataProcessing.lounge_get(fc)

        if use_lounge_otherwise_mii:
            if lounge_name != "":
                player_table_name = lounge_name
        else:
            if not use_miis and not use_lounge_names: # Player name for table should be their FC
                player_table_name = fc
            elif not use_miis and use_lounge_names: # Player name for table should be their mii name with a / and then their Lounge name
                if lounge_name == "":
                    player_table_name = mii_name + " / No Discord"
                else:
                    player_table_name = lounge_name
            elif use_miis and not use_lounge_names: # Player name for table should be mii name
                player_table_name = mii_name
            elif use_miis and use_lounge_names:  # Player name for table should be their lounge name with a / and then their lounge name...?
                player_table_name = mii_name
                discord = "No Discord"
                if lounge_name != "":
                    discord = lounge_name
                player_table_name = player_table_name + " / " + discord
                
        if fc in room.getNameChanges():
            player_table_name = room.getNameChanges()[fc]
        
        if room.fc_subbed_in(fc):
            player_table_name = room.get_sub_string(player_table_name, fc)
            
        if discord_escape:
            player_table_name = escape_mentions(escape_markdown(player_table_name))

        FC_table_dict[fc]["mii_name"] = mii_name
        FC_table_dict[fc]["lounge_name"] = lounge_name
        FC_table_dict[fc]["table_name"] = player_table_name
        FC_table_dict[fc]["tag"] = player_tag
        if player_tag not in table_dict["teams"]:
            table_dict["teams"][player_tag] = create_team()
        if fc not in table_dict["teams"][player_tag]["players"]:
            table_dict["teams"][player_tag]["players"][fc] = FC_table_dict[fc]
        
        player_flag = UserDataProcessing.get_flag_for_fc(fc)
        if player_flag is not None: # add flag, if the FC has a flag set
            FC_table_dict[fc]["flag"] = player_flag

        player_penalty = room.get_fc_penalty(fc)
        if player_penalty is not None:
            FC_table_dict[fc]["penalties"] = player_penalty
            FC_table_dict[fc]["had_penalties"] = True
        if room.fc_subbed_out(fc):
            FC_table_dict[fc]["subbed_out"] = True
        
        

    # Compute individual race scores for each FC
    for GPnum, GP_scores in enumerate(GPs, 1):
        for fc in FC_table_dict:
            gp_amount = [0, 0, 0, 0]
            editAmount = war.getEditAmount(fc, GPnum)
            if editAmount is not None:
                gp_amount = [editAmount, 0, 0, 0]
            else:
                if fc in GP_scores.keys():
                    gp_amount = GP_scores[fc]
                for gp_race_num in range(1, 5):
                    _, subout_old_score = room.get_sub_out_for_subbed_in_fc(fc, ((GPnum-1)*4)+gp_race_num)
                    if subout_old_score is not None:
                        gp_amount[gp_race_num-1] = subout_old_score

            GP_scores[fc] = gp_amount
    
    #after GP scores have been determined, if `up_to_race` has been set, set all races after `up_to_race` to 0 pts
    if up_to_race:
        up_to_race = min(up_to_race, len(room.races)) #`up_to_race` cannot be greater than the maximum number of races
        gp_start = int(up_to_race/4) #GP where first race needs to be reset to 0 
        first_gp_index_start = up_to_race%4 #race in first GP that needs to be reset to 0 (cutoff between races that are kept and races that are reset to 0)

        for indx, gp_scores in enumerate(GPs[gp_start:]): 
            race_start = first_gp_index_start if indx==0 else 0
            for _, player_scores in gp_scores.items():
                player_scores[race_start:] = [0] * (4-race_start)
            
            
    resizedGPs = GPs if step == 4 else resizeGPsInto(GPs, step)
    for GPnum, GP_scores in enumerate(resizedGPs, 1):
        for fc, mii_name in FC_table_dict.items():
            FC_table_dict[fc]["race_scores"].extend(GP_scores[fc])
            FC_table_dict[fc]["gp_scores"].append(GP_scores[fc])
                

    #build table string
    numRaces = up_to_race if up_to_race else min( (len(room.races), war.getNumberOfGPS()*4) )
    table_dict["title_str"] = f"#title {war.getTableWarName(numRaces)}\n"
    if war.is_ffa():
        table_dict["title_str"] += "FFA\n"

    
    # Add team penalty information
    for team_tag, team_penalty in war.getTeamPenalities().items():
        if team_penalty > 0 and team_tag in table_dict["teams"]:
            table_dict["teams"][team_tag]["penalties"] += team_penalty

    # Add team hex color information
    if war.teamColors is not None:
        for (team_color, team_dict) in zip(war.teamColors, table_dict["teams"].values()):
            team_dict["hex_color"] = team_color

    for team_dict in table_dict["teams"].values():
        for player_dict in team_dict["players"].values():
            compute_total_player_score(player_dict)
        team_dict["players"] = UtilityFunctions.sort_dict(team_dict["players"], key=lambda fc: team_dict["players"][fc]["total_score"], reverse=True)
        compute_team_score(team_dict)
    table_dict["teams"] = UtilityFunctions.sort_dict(table_dict["teams"], key=lambda tag: table_dict["teams"][tag]["total_score"], reverse=True)
    
    input_table_text(table_dict)

    return build_table_text(table_dict), table_dict

def compute_team_score(team_dict):
    for player_data in team_dict["players"].values():
        if player_data["subbed_out"]:
            continue
        team_dict["total_score"] += player_data["total_score"]
    team_dict["total_score"] -= team_dict["penalties"]

def compute_total_player_score(player_dict):
    player_dict["total_score"] = sum(player_dict["race_scores"]) - player_dict["penalties"]


def create_table_dict():
    return {
        "title_str": "",
        "teams": {}
    }

def create_team():
    return {"table_tag_str": "",
            "table_penalty_str": "",
            "total_score": 0,
            "penalties": 0,
            "players": {},
            "hex_color": ""
    }

def create_player():
    return {"table_str": "",
            "mii_name": "",
            "lounge_name": "",
            "table_name": "",
            "tag": "",
            "total_score": 0,
            "had_penalties": False,
            "penalties": 0,
            "subbed_out": False,
            "race_scores": [],
            "gp_scores": [],
            "flag": ""
            }

def build_table_text(table_dict):
    table_str = table_dict["title_str"] + "\n"
    team_texts = []
    for team_data in table_dict["teams"].values():
        cur_team_lines = [team_data["table_tag_str"]]
        cur_team_lines.extend([player_data["table_str"] for player_data in team_data["players"].values()])
        if team_data["table_penalty_str"] != "":
            cur_team_lines.append(team_data["table_penalty_str"])
        team_texts.append("\n".join(cur_team_lines))
    return table_str + "\n\n".join(team_texts)
        


def input_table_text(table_dict):
    for team_tag, team_data in table_dict["teams"].items():
        team_data["table_tag_str"] = f"{team_tag} {team_data['hex_color']}".strip()
        if team_data["penalties"] > 0:
            team_data["table_penalty_str"] = f"Penalty -{team_data['penalties']}"
        for player_data in team_data["players"].values():
            player_data["table_str"] = player_data["table_name"] + " "
            if player_data["flag"] != "":
                player_data["table_str"] += f"[{player_data['flag']}] "
            player_data["table_str"] += "|".join([str(sum(gp)) for gp in player_data["gp_scores"]])
            if player_data["had_penalties"]:
                if player_data["penalties"] <= 0:
                    player_data["table_str"] += "|"
                else:
                    player_data["table_str"] += "-"
                player_data["table_str"] += str(abs(player_data["penalties"]))





def get_race_scores_for_fc(friend_code:str, channel_bot:TableBot.ChannelBot, use_lounge_otherwise_mii=True, use_miis=False, lounge_replace=None, server_id=None, missingRacePts=3, discord_escape=False):
    _, race_score_data = get_war_table_DCS(channel_bot, use_lounge_otherwise_mii, use_miis, lounge_replace, server_id, missingRacePts, discord_escape, step=1)
    for _, team_players in race_score_data:
        for fc, player_data in team_players:
            if fc == friend_code:
                return player_data[2]
    return None

team_tag_mapping = {"λρ":"Apocalypse"}
def format_sorted_data_for_gsc(scores_by_team, team_penalties):
    gsc_tag_scores = defaultdict(lambda:[0, 0, 0, 0])
    for tag, players in scores_by_team:
        for _, (_, player_overall, score_by_race) in players:
            cur_team = gsc_tag_scores[tag]
            cur_team[3] += player_overall
            chunked_scores = [score_by_race[i:i+4] for i in range(len(score_by_race))[:12:4]]
            for gpNum, gpScores in enumerate(chunked_scores):
                cur_team[gpNum] += sum(gpScores)
    
    for tag in team_penalties:
        if tag in gsc_tag_scores:
            gsc_tag_scores[tag][3] -= team_penalties[tag]
            
    all_tags = [tag for tag in gsc_tag_scores]
    first_team_tag = all_tags[0]
    second_team_tag = all_tags[1]
    first_team_tag_altered = team_tag_mapping[first_team_tag] if first_team_tag in team_tag_mapping else first_team_tag
    second_team_tag_altered = team_tag_mapping[second_team_tag] if second_team_tag in team_tag_mapping else second_team_tag
    
    gsc_team_scores = {first_team_tag:[0, 0, 0, 0],
                       second_team_tag:[0, 0, 0, 0]}
    for gp_index, first_team_score, second_team_score in zip(range(len(gsc_tag_scores[first_team_tag])), gsc_tag_scores[first_team_tag], gsc_tag_scores[second_team_tag]):
        multiplier = 1 if gp_index != 3 else 2
        if first_team_score > second_team_score:
            gsc_team_scores[first_team_tag][gp_index] = 2
        elif first_team_score < second_team_score:
            gsc_team_scores[second_team_tag][gp_index] = 2
        else:
            gsc_team_scores[first_team_tag][gp_index] = 1
            gsc_team_scores[second_team_tag][gp_index] = 1
        
        gsc_team_scores[first_team_tag][gp_index] *= multiplier
        gsc_team_scores[second_team_tag][gp_index] *= multiplier
            
        
    first_team_gps_text = "|".join(str(s) for s in gsc_team_scores[first_team_tag]) 
    second_team_gps_text = "|".join(str(s) for s in gsc_team_scores[second_team_tag]) 
    
    
    gsc_table_text = f"""#title Grand Star Cup
{first_team_tag}
{first_team_tag_altered} {first_team_gps_text}
{second_team_tag}
{second_team_tag_altered} {second_team_gps_text}"""
    return gsc_table_text
            
            
