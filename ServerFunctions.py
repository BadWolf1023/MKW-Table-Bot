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

default_large_time_setting = "0"
server_large_times = {}

bool_map = {"1":True, "2":False}
ILT_map = {"0": "Never", "1+": "Always"}

    
def get_server_table_theme(server_id, default_table_theme=default_table_theme):
    server_id = str(server_id).strip()
    if server_id not in server_table_themes:
        return default_table_theme
    return server_table_themes[server_id]

def get_server_mii_setting(server_id, display=False, default_mii_setting=default_mii_setting):
    server_id = str(server_id).strip()
    map = {'1': 'On', '2': 'Off'} if display else bool_map
    if server_id not in server_miis:
        return map[default_mii_setting]
    return map[server_miis[server_id]]

def get_server_large_time_setting(server_id, default_large_time_setting=default_large_time_setting):
    server_id = str(server_id).strip()
    if server_id not in server_large_times:
        return ILT_map[default_large_time_setting]

    return insert_formats(server_large_times[server_id])

def is_sui_from_format(server_id: int, warFormat: str):
    server_id = str(server_id).strip()
    server_setting = get_server_large_time_setting(server_id)
    try:
        warFormat = int(warFormat[0])
    except ValueError:
        warFormat = 1
    excludes = parse_ILT_setting(server_setting, local_inject=True)
    return warFormat in excludes

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

def parse_ILT_setting(setting: str, max_format=6, local_inject=False):
    args = remove_formats(setting.strip().lower()).split(',')
    args = sorted(args, key=lambda l: l.strip()[0], reverse=True)
    
    for indx, i in list(enumerate(args))[::-1]:
        i = i.strip()
        check = i.strip('+')
        if '-' not in check and (int(check)>max_format or int(check)<0): #check for illegal input
            raise ValueError

        if i=='1+': #always ignoreLargeTimes
            if local_inject: return list(range(1,max_format+1))
            return '1+'
        if i=='0': #never ignoreLargeTimes
            if local_inject: return list()
            return '0'

        if '-' in i: #range
            n_range = sorted([int(n) for n in i.split('-')])
            start, end = n_range[0], n_range[-1]
            if start>max_format or start<1 or end>max_format:
                raise ValueError
            args.pop(indx)
            args.extend(list(range(start, end+1)))
        elif i[-1] == '+': #range to end
            args.pop(indx)
            args.extend(list(range(int(i.rstrip('+')), max_format+1)))
        else: #only one format
            args[indx] = int(i)
    if local_inject:
        return args

    args = set(args)
    for i in args:
        if i>max_format or i<1:
            raise ValueError #bad input

    args = [str(i) for i in args]

    return ', '.join(sorted(args))


def remove_formats(string: str):
    return string.lower().replace('never', '0').replace('always', '1+').replace("5v5", '5').replace('2v2', '2').replace('3v3', '3').replace('4v4', '4').replace('6v6', '6').replace('ffa', '1')

def insert_formats(string: str):
    return string.replace('0', 'Never').replace('1+', 'Always').replace('5', '5v5').replace('2', '2v2').replace('3','3v3').replace('4','4v4').replace('6','6v6').replace('1', 'FFA')
    
def get_server_settings(server_name, server_id):
    setting_list = [
        (get_server_prefix, "Prefix"),
        (get_server_graph, "Default Graph"),
        (get_server_table_theme, "Default Theme"),
        (get_server_mii_setting, "Default Mii Setting"),
        (get_server_large_time_setting, "Ignore Large Times When")
    ]

    spaces = max([len(k[1]) for k in setting_list])+1
    build_str = f"asciidoc\n== [ {server_name} ] server settings =="
    for get_setting, setting_name in setting_list:
        if get_setting == get_server_mii_setting:
            setting = get_setting(server_id, display=True)
        else:
            setting = get_setting(server_id)
        build_str+=f"\n{setting_name}{' '*(spaces-len(setting_name))}:: {setting}"

    return f"```{build_str}```"

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
    
    