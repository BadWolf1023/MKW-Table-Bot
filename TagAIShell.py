'''
Created on Oct 17, 2021

@author: willg

This module serves as a shell for the tag AIs. It will abstract away from other code anything having to select, test, or compare the AIs.
This module will allow easy selection of a specific AI, comparison of AIs, testing of AIs, and alpha / beta testing of AIs.
'''


import TagAI_Andrew
import TagAI_BadWolf
import time
import os
import dill
import common

USE_BETA_AI = False
RUN_ALPHA_AI = True
RUN_BETA_AI = True
LOG_AI_RESULTS = True


if USE_BETA_AI:
    getTag = lambda tag: TagAI_Andrew._get_tag_value(tag, True, True)
else:
    getTag = TagAI_BadWolf.getTagSmart

alpha_AI = TagAI_BadWolf.getTagsSmart
beta_AI = TagAI_Andrew.get_teams_smart

AI_Results_file_name = "AI_data.pkl"
AI_Results = []
EMPTY_AI_DATA = [None, None, None]
            
def load_pkl_list(list_obj, file_name):
    if os.path.exists(file_name):
        with open(file_name, "rb") as pickle_in:
            try:
                list_obj.extend(dill.load(pickle_in))
            except:
                print(f"Could not read pickle for file '{file_name}' into the given list.")
    else:
        print(f"When trying to load a pkl list, the file '{file_name}' was not found, so no additional information was loaded in")
                
def dump_to_pkl(obj, file_name):
    with open(file_name, "wb") as pickle_out:
        try:
            dill.dump(obj, pickle_out)
        except:
            print(f"Could not dump pickle. Object is: {obj}")
    
def log_AI_results(fc_players, tag_AI_results, time_taken, war_format, is_alpha_AI):
    #If the given fc_players is already in AI_Results for the specified AI, don't add - the war is being tabled in multiple servers and we already added the first one
    AI_result_index = 1 if is_alpha_AI else 2
    for result_data in AI_Results:
        stored_fc_players, alpha_AI_results, beta_AI_results = result_data
        if len(stored_fc_players) == len(fc_players) and set(stored_fc_players) == set(fc_players):
            if is_alpha_AI and alpha_AI_results != EMPTY_AI_DATA:
                #print(f"Was already in alpha results, so not adding")
                return
            elif not is_alpha_AI and beta_AI_results != EMPTY_AI_DATA:
                #print(f"Was already in beta results, so not adding")
                return
            else:
                result_data[AI_result_index] = [tag_AI_results, time_taken, war_format]
            break
                
    else: #The given fc_players were NOT in our AI results at all, so we should append it
        ai_result_data = [fc_players, EMPTY_AI_DATA, EMPTY_AI_DATA]
        ai_result_data[AI_result_index] = [tag_AI_results, time_taken, war_format]
        AI_Results.append(ai_result_data)
    
    dump_to_pkl(AI_Results, AI_Results_file_name)

def get_alpha_AI_results(players, playersPerTeam=None):
    return alpha_AI(players, playersPerTeam)

def get_beta_AI_results(players, playersPerTeam=None):
    all_player_names = [player_data[1] for player_data in players]
    players_per_team_guess, team_results = beta_AI(all_player_names)
    #Change results format into the format Table Bot expects:
    table_bot_formatted_results = {}
    for team_tag, team_player_indexes in team_results.items():
        for player_index in team_player_indexes:
            friend_code = players[player_index][0]
            player_name = players[player_index][1]
            plain_tag = team_tag
            special_tag = team_tag
            table_bot_formatted_results[(friend_code, player_name)] = (plain_tag, special_tag)
    
    return players_per_team_guess, table_bot_formatted_results
    
    
def determineTags(players, playersPerTeam=None):
    alpha_team_results = None
    alpha_has_none_tag = None
    beta_team_results = None
    beta_players_per_team_guess = None
    if RUN_ALPHA_AI or not USE_BETA_AI:
        try:
            #Run Alpha AI:
            t0_alpha = time.perf_counter()
            alpha_team_results, alpha_has_none_tag = get_alpha_AI_results(players, playersPerTeam)
            t1_alpha = time.perf_counter()
            time_taken_alpha = t1_alpha - t0_alpha
            if LOG_AI_RESULTS:
                log_AI_results(players, alpha_team_results, time_taken_alpha, playersPerTeam, is_alpha_AI=True)
        except Exception as e:
            common.log_text(f"Alpha AI threw an exception: {e}", common.ERROR_LOGGING_TYPE)

    if RUN_BETA_AI or USE_BETA_AI:
        #Run Beta AI:
        try:
            t0_beta = time.perf_counter()
            beta_players_per_team_guess, beta_team_results = get_beta_AI_results(players)
            t1_beta = time.perf_counter()
            time_taken_beta = t1_beta - t0_beta
            if LOG_AI_RESULTS:
                log_AI_results(players, beta_team_results, time_taken_beta, beta_players_per_team_guess, is_alpha_AI=False)
        except Exception as e:
            common.log_text(f"Beta AI threw an exception: {e}", common.ERROR_LOGGING_TYPE)

            
    if USE_BETA_AI:
        return beta_team_results, False
    else:
        return alpha_team_results, alpha_has_none_tag
        
    
def initialize():
    TagAI_Andrew.initialize()
    load_pkl_list(AI_Results, AI_Results_file_name)
    
def rerun_AIs_for_all():
    #WARNING: Calling this will replace whatever old results you may have had in "AI_Results" with brand new results
    fc_players_data = [all_data for all_data in AI_Results]
    AI_Results.clear()
    for fc_player, alpha_AI_data, beta_AI_data in fc_players_data:
        if alpha_AI_data[2] is None:
            print("Warning, no known players per team was found, so using Beta's guess for Alpha's determination")
            determineTags(fc_player, beta_AI_data[2])
        else:
            determineTags(fc_player, alpha_AI_data[2])

def format_into_comparable(teams):
    if teams is None:
        return None
    comparable_results = {}
    for fc_player_data, tag_data in teams.items():
        tag_value, actual_tag = ("No Tag", "No Tag") if tag_data is None else tag_data
        cur_tag = TagAI_Andrew._get_tag_value(tag_value)
        if cur_tag not in comparable_results:
            comparable_results[cur_tag] = set()
        comparable_results[cur_tag].add(fc_player_data)
    return comparable_results

def match_names_with_tags():
    pass

def view_AI_results():
    SHOULD_PRINT_VERBOSE = False
    beta_AI_inaccurate_format_amount = 0
    total_results_differed = 0
    total_alpha_ai_results = 0
    total_beta_ai_results = 0
    total_alpha_ai_time_taken = 0.0
    total_beta_ai_time_taken = 0.0
    for stored_fc_players, alpha_AI_results, beta_AI_results in AI_Results:
        alpha_teams, alpha_time_taken, alpha_players_per_team = alpha_AI_results
        if alpha_time_taken is not None:
            total_alpha_ai_time_taken += alpha_time_taken
            total_alpha_ai_results += 1
        beta_teams, beta_time_taken, beta_players_per_team = beta_AI_results
        if beta_time_taken is not None:
            total_beta_ai_time_taken += beta_time_taken
            total_beta_ai_results += 1
        comparable_alpha_teams = format_into_comparable(alpha_teams)
        comparable_beta_teams = format_into_comparable(beta_teams)
        if alpha_players_per_team is not None and alpha_players_per_team != beta_players_per_team:
            beta_AI_inaccurate_format_amount += 1
        results_differed = comparable_alpha_teams != comparable_beta_teams and alpha_teams is not None and beta_teams is not None
        alpha_string = f"Alpha AI: if alpha AI is running, it could not determine a solution, so it gave tabler an alphabetical list. Otherwise, Alpha AI simply hasn't run for these teams yet." if alpha_teams is None else f"Alpha AI: Time taken: {round(alpha_time_taken, 5)}s | Players per team: {alpha_players_per_team}"
        beta_string = f"Beta  AI: did not run for these teams yet." if beta_teams is None else    f"Beta  AI: Time taken: {round(beta_time_taken, 5)}s | Players per team: {beta_players_per_team} (Beta AI's guess)"
        print(f"AI Results Differed: {'Yes' if results_differed else 'No'}\n\t{alpha_string}\n\t{beta_string}")
        if results_differed or alpha_teams is None:
            total_results_differed += 1
        
        
        if SHOULD_PRINT_VERBOSE:
            print("\tAlpha AI's teams (in comparable format):")
            print(f"\t\t{comparable_alpha_teams}")
            print("\tBeta  AI's teams (in comparable format):")
            print(f"\t\t{comparable_beta_teams}")
            print("\tDetailed player data:")
            print(f"\t\t{stored_fc_players}")
    
    print(f"\nSUMMARY:\nBeta AI inaccurate players per team: {beta_AI_inaccurate_format_amount} times out of {len(AI_Results)}")
    print(f"Alpha AI gave alphabetical list {sum(1 for x in AI_Results if x[1][0] is None)} times out of {len(AI_Results)}")
    print(f"AIs had same tags {len(AI_Results) - total_results_differed} times out of {len(AI_Results)}")
    print(f"Alpha AIs average time for solving (not including alphabetical lists): {round((total_alpha_ai_time_taken/total_alpha_ai_results),10)}s")
    print(f"Beta  AIs average time for solving: {round((total_beta_ai_time_taken/total_beta_ai_results),10)}s")
            
if __name__ == '__main__':
    initialize()
    #rerun_AIs_for_all()
    view_AI_results()