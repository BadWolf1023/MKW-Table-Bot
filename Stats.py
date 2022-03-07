'''
Created on Aug 4, 2020

@author: willg
'''
import fnmatch
import json
import os
import re
from datetime import datetime
import humanize
from pathlib import Path
import shutil
import common

user_delimiter = "C,'6WeWq~w,S24!z;L+EM$vL{3M,HMKjy9U2dfH8F-'mwH'2@K.qaQGpg*!StX*:D7^&P;d4@AcWS3)8f64~6CB^B4{s`>9+*brV"

backup_folder = "../backups/"
meta = {
    "command_count": {}
}

SLASH_TERMS_CONVERSIONS = {
    "flag show": 'getflag',
    "flag set": 'setflag',
    "flag remove": 'setflag',
    "update rt": 'rtupdate',
    "update ct": 'ctupdate',
    "setting prefix": 'setprefix',
    "setting theme": 'defaulttheme',
    "setting graph": 'defaultgraph',
    "setting ignore_large_times": 'defaultlargetimes',
    "blacklist user add": 'blacklistuser',
    "blacklist user remove": 'blacklistuser',
    "blacklist word add": 'blacklistword',
    "blacklist word remove": 'removeblacklistword',
    "sha add": 'addsha',
    "sha remove": 'removesha',
    "admin add": 'addadmin',
    "admin remove": 'removeadmin'
}

def initialize():
    global meta
    if os.path.isfile(common.JSON_META_FILE):
        with open(common.JSON_META_FILE) as f:
            meta = json.load(f)

def save_metadata():
    counts = meta["command_count"]
    meta["command_count"] = {k:counts[k] for k in sorted(counts.keys(),reverse=True)}

    with open(common.JSON_META_FILE,'w') as f:
        json.dump(meta, f)

def log_command(command):
    command = SLASH_TERMS_CONVERSIONS.get(command, command)
    
    for name in dir(common.main):
        if re.fullmatch("([A-Z]+_)*TERMS",name):
            command_terms = common.main.__getattribute__(name)
            if command in command_terms:
                meta["command_count"][name] = meta["command_count"].get(name, 0) + 1

def backup_files(to_back_up=common.FILES_TO_BACKUP):
    Path(backup_folder).mkdir(parents=True, exist_ok=True)
    todays_backup_path = backup_folder + str(datetime.date(datetime.now())) + "/"
    Path(todays_backup_path).mkdir(parents=True, exist_ok=True)
    
    #Create backup folders
    for local_dir in common.ALL_PATHS:
        Path(f"{todays_backup_path}{local_dir}").mkdir(parents=True, exist_ok=True)
    
    for file_name in to_back_up:
        try:
            common.check_create(file_name)
            
            temp_file_n = file_name
            if os.path.exists(todays_backup_path + temp_file_n):
                # don't backup the database more than once, otherwise server will run out of disk
                if file_name == common.ROOM_DATA_TRACKING_DATABASE_FILE:
                    continue

                for i in range(50):
                    temp_file_n = file_name + "_" + str(i) 
                    if not os.path.exists(todays_backup_path + temp_file_n):
                        break
            shutil.copy2(file_name, todays_backup_path + temp_file_n)
        except Exception as e:
            print(e)
        else:
            if file_name == common.FULL_MESSAGE_LOGGING_FILE:
                os.remove(common.FULL_MESSAGE_LOGGING_FILE)   
                common.check_create(common.FULL_MESSAGE_LOGGING_FILE)


async def prune_backups():
    for folder in os.listdir(backup_folder):
        try:
            # Fix previously zipped files
            path = backup_folder + folder
            if ".zip" in path:
                print("Unzipping", path)
                new_path = path.replace(".zip","")
                await common.run_command_async(f'unzip {path} -d {new_path}')
                await common.run_command_async(f'rm {path}')
                os.system(f'mv {new_path}/*/*/* {new_path}/')
                await common.run_command_async(f'rm -rf {new_path}/backups')
                path = new_path

            create_time = datetime.strptime(folder.replace(".zip", ""),'%Y-%m-%d').date()
            delta = datetime.date(datetime.now()) - create_time

            if delta.days > 14 and create_time.day != 1:
                if os.path.exists(path+"/tablebot_data"):
                    print("Deleting", path)
                    shutil.rmtree(path+"/tablebot_data")
                    shutil.rmtree(path + "/discord_server_settings")
            elif delta.days >= 1:
                db_path = path+"/tablebot_data/room_data_tracking.db"
                db_path_zip = db_path + ".zip"

                if not os.path.exists(db_path_zip) and os.path.exists(db_path):
                    print("Zipping", db_path)
                    await common.run_command_async(f'zip -r {db_path_zip} {db_path}')
                    await common.run_command_async(f'rm -rf {db_path}')
        except:
            pass
    
def get_commands_from_txt(to_find, needle_function, log_file, limit=None):
    results = []
    needle = needle_function(to_find)
    with open(log_file, "r", encoding='utf-8') as f:
        for line in f:
            if "?lookup " in line.lower():
                continue
            if needle.lower() in line.lower():
                results.append(line)
                if limit is not None and len(results) >= limit:
                    return results
    return results
                

def get_all_commands(discord_id, limit=None):
    results = []
    backups_path = Path(backup_folder)
    current_logging_path = Path(common.LOGGING_PATH)
    all_paths = list(backups_path.iterdir()) + [current_logging_path]

    needle_function = lambda x: f"User ID: {x}"
    for dated_folder in all_paths:
        if dated_folder.is_dir():
            full_log_files = [p for p in dated_folder.glob(f'**/{common.FULL_LOGGING_FILE_NAME}*') if p.is_file()]
            for log_file in full_log_files:
                new_limit = None if limit is None else limit - len(results)
                results.extend(get_commands_from_txt(discord_id, needle_function, log_file, limit=new_limit))
                if limit is not None and len(results) >= limit:
                    return results
    return results
                    
def hard_check(discord_username, limit=None):
    results = []
    backups_path = Path(backup_folder)
    current_logging_path = Path(common.LOGGING_PATH)
    all_paths = sorted(list(backups_path.iterdir()), key=lambda x:x.name) + [current_logging_path]

    needle_function = lambda x: x.lower()
    for dated_folder in all_paths:
        if dated_folder.is_dir():
            full_log_files = [p for p in dated_folder.glob(f'**/messages_logging*') if p.is_file()]
            for log_file in full_log_files:
                new_limit = None if limit is None else limit - len(results)
                results.extend(get_commands_from_txt(discord_username, needle_function, log_file, limit=new_limit))
                if limit is not None and len(results) >= limit:
                    return results
    return results   

def count_lines_of_code():
    lines_count = 0
    for file in os.listdir('.'):
        if fnmatch.fnmatch(file, '*.py'):
            with open(file, encoding='utf-8') as f:
                for _ in f:
                    lines_count += 1
    return lines_count

def get_from_stats_file(stats_file=common.STATS_FILE):
    global user_delimiter
    total_pictures = 0
    total_commands = 0
    total_code_lines = 0
    servers = set()
    users = set()
    
    with open(stats_file, "r+", encoding='utf-8') as f:
        total_pictures = int(f.readline().strip("\n"))
        total_commands = int(f.readline().strip("\n"))
        total_code_lines = int(f.readline().strip("\n"))
        for line_ in f:
            line_ = line_.strip("\n")
            if line_ == user_delimiter:
                break
            servers.add(line_)
        for line_ in f:
            line_ = line_.strip("\n")
            users.add(line_)
    return total_pictures, total_commands, total_code_lines, servers, users


def get_combined_stats_from_both(stats_file=common.STATS_FILE, commands_logging=common.MESSAGE_LOGGING_FILE):
    stats_1 = get_from_stats_file(stats_file)
    stats_2 = get_from_messages_logging_file(commands_logging)
    total_pictures = stats_1[0] + stats_2[0]
    total_commands = stats_1[1] + stats_2[1]
    total_code_lines = stats_1[2] + stats_2[2]
    stats_1[3].update(stats_2[3])
    stats_1[4].update(stats_2[4])
    return total_pictures, total_commands, total_code_lines, stats_1[3], stats_1[4]

        
def get_from_messages_logging_file(commands_logging=common.MESSAGE_LOGGING_FILE):
    users = set()
    servers = set()
    war_picture_count = 0
    total_commands = 0
    common.check_create(commands_logging)
    with open(commands_logging, "r+", encoding='utf-8') as f:
        for line_ in f:
            total_commands += 1
            try:
                if "?wp" in line_[line_.index(" - Command: ") + len(" - Command: "):]:
                    war_picture_count += 1
                index_start = line_.index(" - User: ") + len(" - User: ")
                end_index = line_.index(" - Command: ", index_start)
                users.add(line_[index_start:end_index])
                index_start = line_.index("Server: ") + len("Server: ")
                end_index = line_.index(" - Channel: ", index_start)
                servers.add(line_[index_start:end_index].strip())
            except Exception:
                pass
    return war_picture_count, total_commands, 0, servers, users
    

def dump_to_stats_file(stats_file=common.STATS_FILE, commands_logging=common.MESSAGE_LOGGING_FILE):
    global user_delimiter
    war_picture_count, total_commands, total_code_lines, servers, users = get_combined_stats_from_both(stats_file, commands_logging)
    temp_stats = f"{stats_file}_temp"
    with open(temp_stats, "w+", encoding="utf-8", errors="replace") as temp_out:
        temp_out.write(str(war_picture_count) + "\n")
        temp_out.write(str(total_commands) + "\n")
        temp_out.write(str(total_code_lines) + "\n")
        for server in servers:
            temp_out.write(server + "\n")
        temp_out.write(user_delimiter + "\n")
        for user in users:
            temp_out.write(str(user) + "\n")
            
    os.remove(stats_file)
    os.rename(temp_stats, stats_file)
    os.remove(commands_logging)   
    common.check_create(commands_logging) 
    


def stats(num_bots:int, client=None, stats_file=common.STATS_FILE, commands_logging=common.MESSAGE_LOGGING_FILE):
    str_build = ""
    
    war_picture_count, total_commands, total_code_lines, servers, users = get_combined_stats_from_both(stats_file, commands_logging)
    str_build += "Number of servers that have MKW Table Bot: **" + str(len(client.guilds if client is not None else servers)) + "**\n"
    str_build += "First server ever: **The Funkynuts" + "**\n"
    str_build += "\n"
    str_build += "Number of people who have used MKW Table Bot: **" + str(len(users)) + "**\n"
    str_build += "First user ever: **Chippy#8126" + "**\n"                
    str_build += "\n"
    str_build += "Number of table pictures generated: **" + str(war_picture_count) + "**\n"
    str_build += "Total commands MKW Table Bot has recieved: **" + str(total_commands) + "**\n"
    str_build += "\n"
    #4133
    #str_build += "Lines of high quality code written to make this bot a reality: **" + str(count_lines_of_code()) + "**\n"
    str_build += "Lines of high quality code written to make this bot a reality: **" + str(total_code_lines) + "**\n"
    str_build += "\n"
    right_now = datetime.now()
    current_time = right_now.strftime('%I:%M:%S%p')
    str_build += "Current server (and BadWolf's) time: **" + current_time + "**\n"
    
    ago = None
    with open(commands_logging, "rb+") as f:
        line_num = 0
        try:
            f.seek(-2, os.SEEK_END)
            while True:
                if f.read(1) == b'\n':
                    line_num += 1
                    if line_num == 2:
                        break
                f.seek(-2, os.SEEK_CUR)
            last_line = f.readline().decode()
            last_message_time = last_line.split("S")[0][:-2]
            last_message_obj = datetime.strptime(last_message_time, '%Y-%m-%d %H:%M:%S.%f')
            ago = right_now - last_message_obj
        except:
            pass
    
    if ago is not None:
        str_build += "Last command before your stats command was **" + humanize.naturaltime(ago) + "**\n"
    else:
        str_build += "Last command before your stats command was **" + "N/A" + "**\n"
    str_build += "Number of wars being tabled with the bot right now: **" + str(num_bots) + "**\n"
    
    str_build += "\n\nNotable beta testers: **\n\t- Chippy#8126\n\t- callum#6560\n\t- PhillyGator#0850**"

    str_build += "\n\nSpecial thanks to: **\n\t- callum#6560's dad for solving the last piece to the tag recognition AI**"
    
    return str_build
 
        
if __name__ == '__main__':
    print(hard_check("Dash8r#2342"))
    print(count_lines_of_code())