'''
Created on Aug 1, 2020

@author: willg
'''
import os
import common


server_prefixes = {}

default_table_theme = "1"
server_table_themes = {}

default_graph = "1"
server_graphs = {}

default_mii_setting = "1"
server_miis = {}

default_large_time_setting = "1"
server_large_times = {}

bool_map = {"1":True, "2":False}


    
def get_server_table_theme(server_id, default_table_theme=default_table_theme):
    server_id = str(server_id).strip()
    if server_id not in server_table_themes:
        return default_table_theme
    return server_table_themes[server_id]

def get_server_mii_setting(server_id, default_mii_setting=default_mii_setting):
    server_id = str(server_id).strip()
    if server_id not in server_miis:
        return bool_map[default_mii_setting]
    return bool_map[server_miis[server_id]]

def get_server_large_time_setting(server_id, default_large_time_setting=default_large_time_setting):
    server_id = str(server_id).strip()
    if server_id not in server_large_times:
        return not bool_map[default_large_time_setting]
    return not bool_map[server_large_times[server_id]]

def get_server_graph(server_id, default_graph=default_graph):
    server_id = str(server_id).strip()
    if server_id not in server_graphs:
        return default_graph
    return server_graphs[server_id]

def get_server_prefix(server_id, default_prefix=common.default_prefix):
    server_id = str(server_id).strip()
    if server_id not in server_prefixes:
        return default_prefix
    return server_prefixes[server_id]



def remove_server_setting(server_id, file_name, corresponding_dict):
    server_id = str(server_id).strip()
    temp_file_name = f"{file_name}_temp"
        
    removed = False
    common.check_create(file_name)
    with open(temp_file_name, "w", encoding="utf-8") as temp_out, open(file_name, "r", encoding="utf-8") as original:
        for line in original:
            cur_server_id = line.strip("\n").split()[0].strip()
            if cur_server_id != server_id:
                temp_out.write(line)
            else:
                removed = True
                try:
                    del corresponding_dict[server_id]
                except KeyError:
                    temp_out.write(line)
                    removed = False
                
    os.remove(file_name)
    os.rename(temp_file_name, file_name)
    return removed

def change_server_setting(server_id, new_setting, file_name, corresponding_dict):
    server_id = str(server_id).strip()
    new_setting = new_setting.strip("\n").strip()
    
    if len(new_setting) < 1:
        return False
    
    try:
        if server_id in corresponding_dict:
            remove_server_setting(server_id, file_name, corresponding_dict)
        corresponding_dict[server_id] = new_setting
        common.check_create(file_name)
        with open(file_name, "a", encoding="utf-8") as f:
            f.write(server_id + " " + new_setting + "\n")
        return True
    except:
        return False


def change_server_prefix(server_id, new_prefix):
    return change_server_setting(server_id, new_prefix, common.DEFAULT_PREFIX_FILE, server_prefixes)

def change_default_server_table_theme(server_id, new_theme):
    return change_server_setting(server_id, new_theme, common.DEFAULT_TABLE_THEME_FILE_NAME, server_table_themes)

def change_default_server_graph(server_id, new_graph):
    return change_server_setting(server_id, new_graph, common.DEFAULT_GRAPH_FILE, server_graphs)

def change_default_server_mii_setting(server_id, new_mii_setting):
    return change_server_setting(server_id, new_mii_setting, common.DEFAULT_MII_FILE, server_miis)

def change_default_large_time_setting(server_id, new_large_time_setting):
    return change_server_setting(server_id, new_large_time_setting, common.DEFAULT_LARGE_TIME_FILE, server_large_times)


def load_file(file_name, corresponding_dict):
    common.check_create(file_name)
    with open(file_name, "r", encoding="utf-8") as f:
        for line in f:
            stuffs = line.split()
            server_id = stuffs[0]
            server_setting = line[len(server_id):]
            corresponding_dict[server_id.strip()] = server_setting.strip()
            
def initialize():
    load_file(common.DEFAULT_PREFIX_FILE, server_prefixes)
    load_file(common.DEFAULT_TABLE_THEME_FILE_NAME, server_table_themes)
    load_file(common.DEFAULT_GRAPH_FILE, server_graphs)
    load_file(common.DEFAULT_MII_FILE, server_miis)
    load_file(common.DEFAULT_LARGE_TIME_FILE, server_large_times)
    
    