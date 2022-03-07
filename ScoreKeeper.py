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
    
    

def get_war_table_DCS(channel_bot:TableBot.ChannelBot, use_lounge_otherwise_mii=True, use_miis=False, lounge_replace=None, server_id=None, missingRacePts=3, discord_escape=False, step=None, up_to_race=None):
    war = channel_bot.getWar()
    room = channel_bot.getRoom()
    if step is None:
        step = channel_bot.get_race_size()
    numGPs = war.getNumberOfGPS()
    GPs = []
    use_lounge_names = lounge_replace
    fc_did = UserDataProcessing.fc_discordId
    did_lounge = UserDataProcessing.discordId_lounges
    for x in range(numGPs):
        GPs.append(calculateGPScoresDCS(x+1, room, missingRacePts, server_id))
        
    fcs_players = room.get_fc_to_name_dict(1, numGPs*4)
    room_miis = room.get_miis()
    
    FC_table_str = {}
    
    
    for fc, player in fcs_players.items():
        name = ""
        
        if player.strip() == "":
            name = "no name"
            
        if use_lounge_otherwise_mii:
            name = player
            if fc in fc_did and fc_did[fc][0] in did_lounge:
                name = did_lounge[fc_did[fc][0]]
        else:
            if not use_miis and not use_lounge_names:
                name = fc
            elif not use_miis and use_lounge_names:
                if not fc in fc_did or not fc_did[fc][0] in did_lounge:
                    name = player + " / No Discord"
                else:
                    name = did_lounge[fc_did[fc][0]]
                    
            elif use_miis and not use_lounge_names:
                name = player
            elif use_miis and use_lounge_names: 
                name = player
                discord = "No Discord"
                if fc in fc_did and fc_did[fc][0] in did_lounge:
                    discord = did_lounge[fc_did[fc][0]]
                name = name + " / " + discord
                
        if fc in room.getNameChanges():
            name = room.getNameChanges()[fc]
        
        if room.fc_subbed_in(fc):
            name = room.get_sub_string(name, fc)
        
        if discord_escape:
            name = escape_mentions(escape_markdown(name))

        FC_table_str[fc] = [name + " ", 0, [], name]
        
        #add flag, if the FC has a flag set
        if fc in UserDataProcessing.fc_discordId:
            discord_id_number = UserDataProcessing.fc_discordId[fc][0]
            if discord_id_number in UserDataProcessing.discordId_flags:
                FC_table_str[fc][0] += "[" + UserDataProcessing.discordId_flags[discord_id_number] + "] "
    
    for GPnum, GP_scores in enumerate(GPs, 1):
        for fc in FC_table_str:
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
        for fc, player in FC_table_str.items():
            section_amount = sum(GP_scores[fc])
            FC_table_str[fc][0] += f"{section_amount}|"
            FC_table_str[fc][1] += section_amount
            FC_table_str[fc][2].extend(GP_scores[fc])
                
    for fc in FC_table_str.keys():
        FC_table_str[fc][0] = FC_table_str[fc][0].strip("|")
        
    
    for fc, amount in room.getPlayerPenalities().items():
        if fc in FC_table_str:
            to_add = amount * -1
            FC_table_str[fc][1] += to_add
            if to_add >= 0:
                FC_table_str[fc][0] += "|" + str(to_add)
            else:
                FC_table_str[fc][0] += str(to_add)
            

    #build table string
    numRaces = up_to_race if up_to_race else min( (len(room.races), war.getNumberOfGPS()*4) )
    table_str = "#title " + war.getTableWarName(numRaces) + "\n"
    curTeam = None
    teamCounter = 0
    is_ffa = war.playersPerTeam == 1
    if is_ffa:
        table_str += "FFA\n"
    
    FC_table_str_items = sorted(FC_table_str.items(), key=lambda t: war.getTeamForFC(t[0]))
    scores_by_team = defaultdict(list)
    for fc, player_data in FC_table_str_items:
        scores_by_team[war.getTeamForFC(fc)].append((fc, player_data))
    
    def player_score(player_data):
        return player_data[1]
    
    def team_score(all_players, team_tag):
        total_score = 0
        for fc, player_data in all_players:
            total_score += player_score(player_data)
            
        if team_tag in war.getTeamPenalities():
            total_score -= war.getTeamPenalities()[team_tag]
        return total_score
    
            
    scores_by_team = sorted(scores_by_team.items(), key=lambda t: (team_score(t[1], t[0]), t[0]), reverse=True)
    for _, team_players in scores_by_team:
        team_players.sort(key=lambda pd:player_score(pd[1]), reverse=True)
        
    
    for team_tag, team_players in scores_by_team:
        for fc, player_data in team_players:
            player_scores_str = player_data[0]
            if not is_ffa:
                if team_tag != curTeam:
                    if curTeam in war.getTeamPenalities() and war.getTeamPenalities()[curTeam] > 0:
                        table_str += "\nPenalty -" + str(war.getTeamPenalities()[curTeam]) + "\n"
                    curTeam = war.getTeamForFC(fc)
                    teamHex = ""
                    if war.teamColors is not None:
                        if teamCounter < len(war.teamColors):
                            teamHex = " " + war.teamColors[teamCounter]
                    table_str += "\n" + curTeam + teamHex + "\n"
                    teamCounter += 1
            table_str += player_scores_str + "\n"
    if not is_ffa:
        if team_tag in war.getTeamPenalities():
            table_str += "Penalty -" + str(war.getTeamPenalities()[war.getTeamForFC(fc)]) + "\n"
    
    """for fc, player_data in FC_table_str_items:
        player_scores_str = player_data[0]
        if not is_ffa:
            if war.getTeamForFC(fc) != curTeam:
                if curTeam in war.getTeamPenalities():
                    table_str += "\nPenalty -" + str(war.getTeamPenalities()[curTeam]) + "\n"
                curTeam = war.getTeamForFC(fc)
                teamHex = ""
                if war.teamColors is not None:
                    if teamCounter < len(war.teamColors):
                        teamHex = " " + war.teamColors[teamCounter]
                table_str += "\n" + curTeam + teamHex + "\n"
                teamCounter += 1
        table_str += player_scores_str + "\n"
    if not is_ffa:
        if war.getTeamForFC(fc) in war.getTeamPenalities():
            table_str += "Penalty -" + str(war.getTeamPenalities()[war.getTeamForFC(fc)]) + "\n"""
    return table_str, scores_by_team

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
            
            
