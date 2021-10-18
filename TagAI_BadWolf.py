'''
Created on Sep 23, 2020

@author: willg
'''
from typing import List, Set, Dict, Tuple
from copy import copy
from datetime import datetime, timedelta
from _collections import defaultdict


VALID_CHARS = "/\\*^+abcdefghijklmnopqrstuvwxyz\u03A9\u038F" + "abcdefghijklmnopqrstuvwxyz0123456789".upper()
UNICODE_MAPPINGS_TO_ALPHA = {"@":"A", "\u00A7":"S", "$":"S", "\u00A2":"c", "\u00A5":"Y", "\u20AC":"E", "\u00A3":"E", "\u00E0":"a", "\u00E1":"a", "\u00E2":"a", "\u00E4":"a", "\u00E5":"a", "\u00E6":"ae", "\u00E3":"a", "\u00E7":"c", "\u00E8":"e", "\u00E9":"e", "\u00EA":"e", "\u00EB":"e", "\u00EC":"i", "\u00ED":"i", "\u00EE":"i", "\u00EF":"i", "\u00F1":"n", "\u00F2":"o", "\u00F3":"o", "\u00F4":"o", "\u00F6":"o", "\u0153":"oe", "\u00F8":"o", "\u00F5":"o", "\u00DF":"B", "\u00F9":"u", "\u00FA":"u", "\u00FB":"u", "\u00FC":"u", "\u00FD":"y", "\u00FF":"y", "\u00C0":"A", "\u00C1":"A", "\u00C2":"A", "\u00C4":"A", "\u00C5":"A", "\u00C6":"AE", "\u00C3":"A", "\u00C7":"C", "\u00C8":"E", "\u00C9":"E", "\u00CA":"E", "\u00CB":"E", "\u00CC":"I", "\u00CD":"I", "\u00CE":"I", "\u00CF":"I", "\u00D1":"N", "\u00D2":"O", "\u00D3":"O", "\u00D4":"O", "\u00D6":"O", "\u0152":"OE", "\u00D8":"O", "\u00D5":"O", "\u00D9":"U", "\u00DA":"U", "\u00DB":"U", "\u00DC":"U", "\u00DD":"Y", "\u0178":"Y", "\u03B1":"a", "\u03B2":"B", "\u03B3":"y", "\u03B4":"o", "\u03B5":"e", "\u03B6":"Z", "\u03B7":"n", "\u03B8":"O", "\u03B9":"i", "\u03BA":"k", "\u03BB":"A", "\u03BC":"u", "\u03BD":"v", "\u03BE":"E", "\u03BF":"o", "\u03C0":"r", "\u03C1":"p", "\u03C3":"o", "\u03C4":"t", "\u03C5":"u", "\u03C6":"O", "\u03C7":"X", "\u03C8":"w", "\u03C9":"W", "\u0391":"A", "\u0392":"B", "\u0393":"r", "\u0394":"A", "\u0395":"E", "\u0396":"Z", "\u0397":"H", "\u0398":"O", "\u0399":"I", "\u039A":"K", "\u039B":"A", "\u039C":"M", "\u039D":"N", "\u039E":"E", "\u039F":"O", "\u03A0":"N", "\u03A1":"P", "\u03A3":"E", "\u03A4":"T", "\u03A5":"Y", "\u03A6":"O", "\u03A7":"X", "\u03A8":"w", "\u0386":"A", "\u0388":"E", "\u0389":"H", "\u038A":"I", "\u038C":"O", "\u038E":"Y", "\u0390":"i", "\u03AA":"I", "\u03AB":"Y", "\u03AC":"a", "\u03AD":"E", "\u03AE":"n", "\u03AF":"i", "\u03B0":"u", "\u03C2":"c", "\u03CA":"i", "\u03CB":"u", "\u03CC":"o", "\u03CD":"u", "\u03CE":"w", "\u2122":"TM", "\u1D49":"e", "\u00A9":"C", "\u00AE":"R", "\u00BA":"o", "\u00AA":"a", "\u266D":"b"}
#other_players_context is simple a list of other players names
REMOVE_IF_START_WITH = "/\\*^+"

#Returns 2 values. The first is the ranking value used by sorting methods, the 2nd is the tag itself
#This is useful so that we can return lambda as a tag, but make it have the same ranking value as A
#In computer language, the value of lambda makes it come after the letter Z, so we can use this cheap mapping method to make special characters have a
#different value for sorting methods, but still maintain its original value
#Because we return a 2-tuple, sorting methods will run lexicographically - if there's a tie between lambda and A (because both have the value of A),
#the tie breaker goes to actual tag, and so lambda would be a distinctly different "ranking" than A if there were actually 2 teams (lambda and A)



def _get_tag_value(tag):
    while len(tag) > 0:
        if tag[0] in REMOVE_IF_START_WITH:
            tag = tag[1:]
        else:
            break
    temp = ""
    for c in tag:
        if c in UNICODE_MAPPINGS_TO_ALPHA:
            temp += UNICODE_MAPPINGS_TO_ALPHA[c]
        elif c in VALID_CHARS:
            temp += c
    return temp.upper()

def stripBadChars(tag):
    while len(tag) > 0:
        if tag[0] in REMOVE_IF_START_WITH:
            tag = tag[1:]
        else:
            break
    temp = ""
    for c in tag:
        if c in UNICODE_MAPPINGS_TO_ALPHA or c in VALID_CHARS:
            temp += c
    return temp


"""def __score_tag_likelihood(this_player_tags:List[str], players_tags: List[List[str]]) -> Dict[str, int]:
    this_player_tag_scores = {}
    counter = 0
    found = 0
    for this_player_tag in this_player_tags:
        for player_tags in players_tags:
            for player_tag in player_tags:
                counter += 1
                if _get_tag_value(this_player_tag) == _get_tag_value(player_tag):
                    found += 1
        this_player_tag_scores[this_player_tag] = found
"""   
        
#def __get_most_likely_tag(player_tag_scores:Dict[str, int]):
#   return max(player_tag_scores.keys(), key=lambda tag: (player_tag_scores[tag], len(tag)))

def __get_bracket_tag(name):
    MAXIMUM_BRACKET_TAG_LEN = 4
    #Handle stuff in brackets
    if "[" in name and "]" in name:
        startbracket_index = name.index("[")
        endbracket_index = name.index("]")
        if endbracket_index - startbracket_index - 1 >= 1: #Something is in the brackets
            if endbracket_index - startbracket_index - 1 <= MAXIMUM_BRACKET_TAG_LEN:
                brackets_tag = name[startbracket_index+1:endbracket_index]
                return (_get_tag_value(brackets_tag), stripBadChars(brackets_tag))
    return None

def __get_player_tags(name:str):
    #If player has something in brackets, we're assuming 100% it is their tag
    bracket_tag = __get_bracket_tag(name)

    if bracket_tag is not None:
        return [(bracket_tag[0], stripBadChars(bracket_tag[1]))]

    name = stripBadChars(name)
    all_possible = []
    #If their name is blank, they will be given the Player tag
    if len(name) == 0:
        return [("Player", "Player")]
    if name.lower() in ['player', 'no name']:
        return [("Player", "Player"), ("P", "P")]
    
    elif len(name) == 1:
        all_possible.append( (_get_tag_value(name), name) )
        return all_possible
    
    for i, _ in enumerate(name):
        front_tag = name[i:]
        all_possible.append( (_get_tag_value(front_tag), front_tag) ) #what a tag at the end of the name would be
        end_tag = name[:i+1]
        all_possible.append( (_get_tag_value(end_tag), end_tag) ) #what a tag at the front of the name would be
    
    #Note: when the loop ends, there will be a duplicate tag - that is their full name
    all_possible.pop()
    return all_possible
    
    
        
#Takes a List of tuples (FC and player) and returns a Dictionary of those players' sorting value and actual tag value

def __count_tags(all_possible:Dict[Tuple[str, str], List[Tuple[str, str]]]) -> Dict[Tuple[str, str], List[Tuple[str, str, int]]]:
    this_player_tag_scores = {}
    for fc_player_1, tags_1 in all_possible.items():
        this_player_tag_scores[fc_player_1] = []
        for player_1_tag in tags_1:
            found = 0
            for fc_player_2, tags_2 in all_possible.items():
                if fc_player_1[0] != fc_player_2[0]: #Don't get tags for ourself...
                    for player_2_tag in tags_2:
                        if player_1_tag[0] == player_2_tag[0]: #if they have the same tag VALUE, not actual tag
                            found += 1
                            break
            this_player_tag_scores[fc_player_1].append( (player_1_tag[0], player_1_tag[1], found) )
    return this_player_tag_scores


def __clean(all_possible_counts: Dict[Tuple[str, str], List[Tuple[str, str, int]]]):
    for tags_counts in all_possible_counts.values():
        to_remove = set()
        for index, (tag_val, _, tag_count) in enumerate(tags_counts):
            
            if tag_count == 0:
                to_remove.add(index)
            #I forgot what the issue with this was, but I believe it was eliminating short tags that were correct too early, in favor of bogus long tags (ie "A^Brandon" and "C^Anon" would incorrectly be "on" since the short tags were eliminated too early)
            """else:
                for (tag_val_2, _, tag_count_2) in tags_counts:
                    if tag_val != tag_val_2: #if it's not the same tag (meaning, the exact same object as tag_val)
                        if tag_count == tag_count_2 and len(tag_val_2) > len(tag_val) and tag_val in tag_val_2: #greedy, we will remove if it is a substring of another tag with the same count
                            to_remove.add(index)
            """
        #remove from list, from greatest index to least (so that we don't change list order and remove something we shouldn't)
        for i in sorted(to_remove, reverse=True):
            tags_counts.pop(i)
    

            
def __clean_by_num_players(all_possible_counts: Dict[Tuple[str, str], List[Tuple[str, str, int]]], playersPerTeam:int):       
    for tags_counts in all_possible_counts.values():
        to_remove = set()
        for index, (tag_val, _, tag_count) in enumerate(tags_counts):
            
            if tag_count < (playersPerTeam - 1): #the number of *other* players who have this tag
                to_remove.add(index)
        
        #remove from list, from greatest index to least (so that we don't change list order and remove something we shouldn't)
        
        for i in sorted(to_remove, reverse=True):
            tags_counts.pop(i)

def count_tags_at_front(solution):
    count = 0
    for tag_data, players in solution.items():
        tag = tag_data[0]
        for (_, name) in players:
            name = _get_tag_value(stripBadChars(name)).lower()
            if name.startswith(tag.lower()):
                count += 1
    return count
def __choose_best_solution(solutions: List[Dict[Tuple[str, str, int], Set[Tuple[str,str]]]]) -> Dict[Tuple[str, str, int], Set[Tuple[str,str]]]:
    
    proccessing_solution_start_time = datetime.now()
    did_cut_off = False
    def should_cut_off(max_time=timedelta(seconds=5)):
        return (datetime.now() - proccessing_solution_start_time) > max_time
    

    if len(solutions) == 0: #There were no solutions
        return None
    

    #TODO: Undo this
    #if len(solutions) == 1: #There was only one solution, so return it
    #    return solutions[0]
    else:
        number_of_teams = len(solutions[0])
        #TODO: Do something smart
        eliminate = set()
        for sol_1_index, solution_1 in enumerate(solutions):
            
            for sol_2_index, solution_2 in enumerate(solutions):
                if sol_2_index != sol_1_index:
                    did_cut_off = should_cut_off()
                    if did_cut_off:
                        return None
                    
                    for (tag_1_val, _, _), player_set_1 in solution_1.items():
                        for (tag_2_val, _, _), player_set_2 in solution_2.items():
                            if tag_1_val != tag_2_val:
                                #Example: If tag_2 is DSD, and tag 1 is D, and tag 1's players are all in tag 2's players, we want to eliminate this solution because
                                #a better one will be in the solution possibilities
                                if len(tag_2_val) > len(tag_1_val) and \
                                (tag_2_val.startswith(tag_1_val) or tag_2_val.endswith(tag_1_val)) and\
                                player_set_1.issubset(player_set_2):
                                    eliminate.add(sol_1_index)
                                    
        for i in sorted(eliminate, reverse=True):
            del solutions[i]
            
        

        if len(solutions) >= 1:
            #return the solution with the most tags at the front
            index_with_most = 0
            index_with_most_count = -1
            for ind, sol in enumerate(solutions):
                did_cut_off = should_cut_off()
                if did_cut_off:
                    return None
                tag_at_front_count = count_tags_at_front(sol) #count
                if tag_at_front_count > index_with_most_count:
                    index_with_most = ind
                    index_with_most_count = tag_at_front_count
            return solutions[index_with_most]
        else:
            return None
        
            
                
def __clean_by_overlap(all_possible_counts: Dict[Tuple[str, str], List[Tuple[str, str, int]]], playersPerTeam:int):       
    #if there exists a combination of players and tags such that no player is on both teams, this combination is most likely correct
    #At this point, hopefully, all players will have at least one possible tag - if they don't, we'll handle that in the calling function after this runs
    #The important thing at this point is to eliminate any tags that create an impossible scenario, such as player 1 being on both tag Ap and tag Pw
    
    #Tag values are now the key, and the value is the fc_player 
    tag_players = {}
    for fc_player, tags_counts in all_possible_counts.items():
        for tag_tuple in tags_counts:
            for tp in tag_players:
                if tp[0] == tag_tuple[0]:
                    tag_players[tp].add(fc_player)
                    break
            else:
                tag_players[tag_tuple] = set([fc_player])
    
    players_on_more_than_one_team = set()
    for tag, players in tag_players.items():
        for tag_2, players_2 in tag_players.items():
            if tag[0] != tag_2[0]:
                for p_1 in players:
                    if p_1 in players_2:
                        players_on_more_than_one_team.add(p_1)
   
    #Each player can only appear once, and each tag must have the same or more players per team as numPlayersPerTeam
    def is_possible_solution(tags_possibilities:List[Tuple[Tuple[str, str, int], Set[Tuple[str,str]]]], allPlayers:List[Tuple[str, str]], playersPerTeam:int):
        #check if the solution set has the same players as the original player set
        #if it doesn't, it clearly can't be a valid solution
        solution_players = set()
        for tags_players in tags_possibilities.values():
            solution_players.update(tags_players)
        if allPlayers != solution_players:
            return False
        possible_solution = True
        for player in allPlayers:
            instanceCount = 0
            for (tag, players) in tags_possibilities.items():
                if len(players) != playersPerTeam:
                        return False
                if player in players:
                    instanceCount += 1
                    if instanceCount >= 2:
                        return False
        return possible_solution
                    
            #we have the correct number of teams, now we need to check if each team has the right number of players
    
    def copy_solution(tags_possibilities:Dict[Tuple[str, str, int], Set[Tuple[str,str]]]) -> Dict[Tuple[str, str, int], Set[Tuple[str,str]]]:
        solution_copy = {}
        for tag, players in tags_possibilities.items():
            players_copy = set()
            for fc, player in players:
                players_copy.add( (copy(fc), copy(player)))
            solution_copy[( copy(tag[0]), copy(tag[1]), copy(tag[2]) )] = players_copy
        return solution_copy
    
    max_time_solving = timedelta(seconds=5)
    tag_recur_start = datetime.now()
    def beyond_time():
        return (datetime.now() - tag_recur_start) > max_time_solving
        
    def all_possible_solutions_recurrsion(duplicates:List[Tuple[str, str]], tags_possibilities:List[Tuple[str, Set[Tuple[str,str]]]], allPlayers:List[Tuple[str, str]], possible_solutions:List[Tuple[str, Set[Tuple[str,str]]]], playersPerTeam:int):
        if beyond_time():
            return
        
        if is_possible_solution(tags_possibilities, allPlayers, playersPerTeam):
            possible_solutions.append(copy_solution(tags_possibilities))
                
        if len(duplicates) == 0:
            return
        
        this_duplicate = duplicates.pop()
        
        duplicate_tags = []
        for tag, players in tags_possibilities.items():
            if this_duplicate in players:
                duplicate_tags.append(tag)
        
        for i in duplicate_tags:
            remove_these = []
            for j in duplicate_tags:
                if i != j:
                    remove_these.append(j)
            
            for x in remove_these:
                tags_possibilities[x].remove(this_duplicate)
                
            #Remove empty tags before checking for solution (so the function works)
            #alpha beta pruning as well
            #don't even go down the path if there's a tag with less players per team than the format has
            not_enough_players = {}
            for tag, players in tags_possibilities.items():
                if players is None or len(players) < playersPerTeam:
                    not_enough_players[tag] = players
            for tag in not_enough_players:
                del(tags_possibilities[tag])
            
            all_possible_solutions_recurrsion(duplicates, tags_possibilities, allPlayers, possible_solutions, playersPerTeam)
            if beyond_time():
                return
            
            #Coming back up from the recursion, need to add those empty tags back in case we're putting players in them
            tags_possibilities.update(not_enough_players)
            
            for x in remove_these: #coming back up from the recursion, need to put them back in
                tags_possibilities[x].add(this_duplicate)
        duplicates.append(this_duplicate)
        return
    
    dups = list(players_on_more_than_one_team)
    all_players = set(all_possible_counts.keys())
    all_possible_solutions = []
    all_possible_solutions_recurrsion(dups, tag_players, all_players, all_possible_solutions, playersPerTeam)
    if beyond_time():
        return None
    if all_possible_solutions is None or len(all_possible_solutions) == 0:
        return None
    
    #for number, solution in enumerate(all_possible_solutions, 1):
    #    print("Possible solution #" + str(number))
    #    print(solution)
    #print(all_possible_solutions)
    best_solution = __choose_best_solution(all_possible_solutions)
    if best_solution is None:
        return None
    players_tags = {}
    for tag, fc_players in best_solution.items():
        for fc_player in fc_players:
            original_data = None
            for possible_tag in all_possible_counts[fc_player]:
                if possible_tag[0] == tag[0]:
                    original_data = possible_tag
            if fc_player in players_tags:
                players_tags[fc_player].append(original_data)
            else:
                players_tags[fc_player] = [original_data]
    return players_tags
    


def __choose_and_cleanup(counts: Dict[Tuple[str, str], List[Tuple[str, str, int]]]) -> Dict[Tuple[str, str], Tuple[str, str]]:
    fc_player_tags = {}
    
    
    has_None_Tags = False
    for fc_player, tags_counts in counts.items():
        if len(tags_counts) == 0:
            fc_player_tags[fc_player] = None
            has_None_Tags = True
        else:
            temp = sorted(tags_counts)
            if temp[0][0] == "NO NAME" and temp[0][1] == "no name":
                fc_player_tags[fc_player] = ("PLAYER", "Player")
            else:
                fc_player_tags[fc_player] = (temp[0][0], temp[0][1])
        
    return fc_player_tags, has_None_Tags

def __correctTags(counts: Dict[Tuple[str, str], List[Tuple[str, str, int]]], has_None_Tags, playersPerTeam:int) -> Dict[Tuple[str, str], Tuple[str, str]]:
    #Now we want to correct anyone with the wrong tag
    if not has_None_Tags and playersPerTeam >= 3: #Only do this for 3v3s, majority tag correction
        value_tags_counts = defaultdict(list)
        for tag in counts.values():
            tag_val, actual_tag = tag[0], tag[1]
            value_tags_counts[tag_val].append(actual_tag)
        
        #Collapse the dictionary with the most common actual tag for each value tag
        replacement_tags = {}
        for tag_val, list_of_actual_tags in value_tags_counts.items():
            replacement_tags[tag_val] = max(set(list_of_actual_tags), key = list_of_actual_tags.count)
        
        for fc_player, tag in counts.items():
            counts[fc_player] = (tag[0], replacement_tags[tag[0]])
         

    return counts

def getTagsSmart(fc_players:List[Tuple[str, str]], playersPerTeam:int) -> Dict[Tuple[str, str], Tuple[str, str]]:
    #import time
    #startTime = time.perf_counter_ns() 
    if playersPerTeam < 2:
        none_team_dict = {}
        for fc_player in fc_players:
            none_team_dict[fc_player] = None
        return none_team_dict, True
            
    
    all_possible = {}
    for fc, player in fc_players:
        all_possible[(fc, player)] = __get_player_tags(player)
    tag_counts = __count_tags(all_possible)
    
    __clean(tag_counts)
    __clean_by_num_players(tag_counts, playersPerTeam)
    temp = __clean_by_overlap(tag_counts, playersPerTeam)
    

    if temp is None or len(temp) == 0:
        return None, True
    
    if len(tag_counts) == len(temp):
        tag_counts = temp


    tag_counts, hasNoneTags = __choose_and_cleanup(tag_counts)
    tag_counts = __correctTags(tag_counts, hasNoneTags, playersPerTeam)
    #print("Time this took:", time.perf_counter_ns() - startTime)
    return tag_counts, hasNoneTags
    

def getTagSmart(name:str):
    bracket_tag = __get_bracket_tag(name)
    
    
    if bracket_tag is not None:
        return bracket_tag
    
    name = stripBadChars(name)
    
    if name == "no name" or name == "Player":
        return ("P", "P")

    if len(name) == 0:
        return ("","")
    else:
        #Return the Alpha value (for sorting) in the first tuple index, and the actual tag as the 2nd index
        return (_get_tag_value(name[0]), name[0])
