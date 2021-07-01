'''
Created on Aug 4, 2020

@author: willg
'''
import fnmatch
import os
from datetime import datetime
import humanize
from pathlib import Path
import shutil
import common

user_delimiter = "C,'6WeWq~w,S24!z;L+EM$vL{3M,HMKjy9U2dfH8F-'mwH'2@K.qaQGpg*!StX*:D7^&P;d4@AcWS3)8f64~6CB^B4{s`>9+*brV"

backup_folder = "../backups/"


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
                for i in range(50):
                    temp_file_n = file_name + "_" + str(i) 
                    if not os.path.exists(todays_backup_path + temp_file_n):
                        break
            shutil.copy2(file_name, todays_backup_path + temp_file_n)
        except Exception as e:
            print(e)


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
                index_start = line_.index("Sever: ") + len("Sever: ")
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
    str_build += "Number of war pictures generated: **" + str(war_picture_count) + "**\n"
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
    print(count_lines_of_code())