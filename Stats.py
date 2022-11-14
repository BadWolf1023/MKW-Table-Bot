'''
Created on Aug 4, 2020

@author: willg
'''
import fnmatch
import re
import json
import os
import re
from datetime import datetime
import humanize
from pathlib import Path
import shutil
import common

TOTAL_CODE_LINES = None

backup_folder = "../backups/"
meta = {
    "command_count": {},
    "user_ids": [],
    "last_command_time": "2000-01-01 12:00:00.000000",
    "total_commands_count": 0,
    "lorenzi_tables_picture_count": 0,
    "local_tables_picture_count": 0
}

def initialize():
    global meta
    if os.path.isfile(common.JSON_META_FILE):
        with open(common.JSON_META_FILE, 'r') as f:
            meta = json.load(f)
    else:
        print("WARNING: No meta JSON found! Resetting meta. If this is a mistake, restore a meta JSON backup.")
    
    backward_compatibility_update()
    
def backward_compatibility_update():
    if "user_ids" not in meta:
        meta["user_ids"] = []
    
    if "last_command_time" not in meta:
        meta["last_command_time"] = "2000-01-01 12:00:00.000000"

    if "total_commands_count" not in meta:
        # Note, the real MKW Table Bot should manually input the old count combined with the new count since it has old statistics
        meta["total_commands_count"] = sum(v for v in meta["command_count"].values())

    if "lorenzi_tables_picture_count" not in meta:
        meta["lorenzi_tables_picture_count"] = meta["command_count"].get("WAR_PICTURE_TERMS", 0)

    if "local_tables_picture_count" not in meta:
        meta["local_tables_picture_count"] = 0
    

def save_metadata():
    counts = meta["command_count"]
    meta["command_count"] = {k:counts[k] for k in sorted(counts.keys(),reverse=True)}
    with open(common.JSON_META_FILE,'w') as f:
        json.dump(meta, f, indent=4)

def log_command(command: str, user_id: str, slash=False):
    log_user(user_id)
    meta["total_commands_count"] += 1
    command = common.SLASH_TERMS_CONVERSIONS.get(command, command)
    if command != "stats":
        meta["last_command_time"] = str(datetime.now())
    if command == 'raw':
        meta['raw_slash_count'] = meta.get('raw_slash_count', 0) + 1
        return
    
    for name in dir(common.main):
        if re.fullmatch(r"([A-Z]+_)*TERMS",name):
            command_terms = common.main.__getattribute__(name)
            if command in command_terms:
                meta["command_count"][name] = meta["command_count"].get(name, 0) + 1
                if slash:
                    meta["slash_commands_count"] = meta.get('slash_commands_count', 0) + 1

def log_user(user_id):
    user_id = str(user_id)
    if user_id not in meta["user_ids"]:
        meta["user_ids"].append(user_id)


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

                #To the above comment, we'll lose the current day's data on Ctrl+C if we don't ^
                #if file_name == common.ROOM_DATA_TRACKING_DATABASE_FILE:
                #    continue

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
    print(f"{str(datetime.now())}: Pruning backups...")
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

            # create_time = datetime.strptime(re.sub(r"_(\d+)$", "", folder.replace(".zip", "")),'%Y-%m-%d').date()
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
        except Exception as e:
            print(f"{str(datetime.now())}: Pruning backups has exception: {e}")
            pass
    print(f"{str(datetime.now())}: Pruning backups complete data")
    
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

def count_lines_of_code(dir='.') -> int:
    global TOTAL_CODE_LINES
    if TOTAL_CODE_LINES is None:
        lines_count = 0
        for file in os.listdir(dir):
            if os.path.isdir(dir+'/'+file):
                lines_count+=count_lines_of_code(dir+'/'+file)
            if re.match(r'.*\.(py|sql)$', file):
                with open(dir+'/'+file, encoding='utf-8') as f:
                    for _ in f:
                        lines_count += 1
        TOTAL_CODE_LINES = lines_count
    return TOTAL_CODE_LINES

def add_lorenzi_picture_count():
    meta["lorenzi_tables_picture_count"] += 1

def add_local_picture_count():
    meta["local_tables_picture_count"] += 1

def get_stats_json():
    return {
        "users": len(meta["user_ids"]),
        "servers": len(common.client.guilds),
        "pictures": meta["lorenzi_tables_picture_count"] + meta["local_tables_picture_count"],
        "commands": meta["total_commands_count"]
    }

def stats(num_bots:int, client) -> str: 
    '''Returns a nicely printed string of fun Table Bot statistics
    '''  
    war_picture_count = meta["lorenzi_tables_picture_count"] + meta["local_tables_picture_count"]
    total_command_count = meta["total_commands_count"]
    total_code_lines = count_lines_of_code()
    number_servers = len(client.guilds)
    number_users = len(meta["user_ids"])

    # Compute how long ago the last command was sent:
    right_now = datetime.now()
    last_message_time_str = meta["last_command_time"]
    last_message_time = datetime.strptime(last_message_time_str, '%Y-%m-%d %H:%M:%S.%f')
    ago = humanize.naturaltime(right_now - last_message_time)

    # Format the current time into a pleasant format
    current_time = right_now.strftime('%I:%M:%S%p')

    return f"""**Meet the MKW Table Bot team:**
  - Bad Wolf: Project manager, originally created and developed MKW Table Bot
  - camelwater: Main Developer (active)
  - andrew: Developer (inactive)
  - Fear: Junior Developer

Number of servers that have MKW Table Bot: **{number_servers}**
Number of people who have used MKW Table Bot: **{number_users}**
First server ever: **The Funkynuts**

Total commands MKW Table Bot has received: **{total_command_count}**
Number of table pictures generated: **{war_picture_count}**
Lines of high quality code written to make this bot a reality: **{total_code_lines}**

Current server time: **{current_time}**
Last command before your stats command was **{ago}**
Number of tables currently being tabled: **{num_bots}**

Notable beta testers: **Chippy, callum, PhillyGator**"""
 
        
if __name__ == '__main__':
    # print(hard_check("Dash8r#2342"))
    print(count_lines_of_code())