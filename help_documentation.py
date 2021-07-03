'''
Created on Jun 25, 2021

@author: willg
'''
from typing import List
import os
import common

main_help_file_list = ['main_help.txt']
tabling_help_file_list = ['tabling_help_1.txt', 'tabling_help_2.txt']
server_defaults_help_file_list = ['server_defaults_help.txt']
flags_help_file_list = ['flags_help.txt']
lounge_help_file_list = ['lounge_help.txt']
other_help_file_list = ['other_help_1.txt', 'other_help_2.txt']


default_help_key = 'help'
tabling_help_key = 'tabling'
HELP_KEY_FILES = {"help":main_help_file_list,
                  "tabling":tabling_help_file_list,
                  "serverdefaults":server_defaults_help_file_list,
                  "flags":flags_help_file_list,
                  "lounge":lounge_help_file_list,
                  "other":other_help_file_list
                  }

QUICKSTART_FILE = f"{common.HELP_PATH}quickstart.txt"

def get_help_files(args:List[str]):
    help_ind = None
    for ind, arg in enumerate(args):
        if 'help' in arg:
            help_ind = ind
            break
        
    if help_ind is None:
        return default_help_key
    new_args = args[help_ind+1:]
    help_key = " ".join(new_args)
    if help_key not in HELP_KEY_FILES:
        return default_help_key
    return help_key


async def send_help(message, is_lounge_server, args:List[str], prefix=common.default_prefix):
    help_key = get_help_files(args)
    
    if is_lounge_server and help_key == tabling_help_key:
        await message.channel.send("See the table bot guide and flow charts in <#835555593833414696> or <#835561764322017320>.")
        return
    #prefix_text = f"**Prefix**: {prefix}\n" if help_key == default_help_key else ""
    prefix_text = ""
    help_files = HELP_KEY_FILES[help_key]
    for index, help_text_file in enumerate(help_files, 1):
        help_file = f"{common.HELP_PATH}{help_text_file}"
        if os.path.isfile(help_file):
            with open(help_file, "r") as f:
                help_text = ""
                if index == 1:
                    help_text += prefix_text
                for line in f:
                    help_text += line
                if len(help_text) > 1:
                    help_text = help_text.replace("{SERVER_PREFIX}", prefix)
                    await message.channel.send(help_text)
                    
async def send_quickstart(discord_message_obj):
    quick_start = "No quickstart."
    with open(QUICKSTART_FILE, "r") as f:
        quick_start = ""
        for line in f:
            quick_start += line
    await discord_message_obj.channel.send(quick_start)
                    