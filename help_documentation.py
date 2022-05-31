'''
Created on Jun 25, 2021

@author: willg
'''
from typing import List
import os

import discord
import common
import UtilityFunctions

main_help_file_list = ['main_help.txt']
tabling_help_file_list = ['tabling_help_1.txt', 'tabling_help_2.txt']
server_defaults_help_file_list = ['server_defaults_help.txt']
flags_help_file_list = ['flags_help.txt']
lounge_reporter_help_file_list = ['lounge_staff_help_1.txt','lounge_staff_help_2.txt','lounge_staff_help_3.txt']
lounge_submitting_tables_help_file_list = ['lounge_table_submission_help.txt']
other_help_file_list = ['other_help_1.txt', 'other_help_2.txt']


default_help_key = 'help'
tabling_help_key = 'tabling'
all_players_help_file_list = ['all_players_help.txt']
change_tag_help_file_list = ['change_tag_help.txt']
dc_help_file_list = ['dc_help.txt']
fcs_help_file_list = ['fcs_help.txt']
graph_help_file_list = ['graph_help.txt']
race_results_help_file_list = ['race_results_help.txt']
race_size_help_file_list = ['race_size_help.txt']
races_help_file_list = ['races_help.txt']
remove_race_help_file_list = ['remove_race_help.txt']
reset_undo_help_file_list = ['reset_undo_help.txt']
start_war_help_file_list = ['start_war_help.txt']
style_help_file_list = ['style_help.txt']



TABLING_HELP_FILES = {"1":start_war_help_file_list,
                      "2":reset_undo_help_file_list,
                      "3":dc_help_file_list,
                      "4":remove_race_help_file_list,
                      "5":change_tag_help_file_list,
                      "6":style_help_file_list,
                      "7":graph_help_file_list,
                      "8":race_size_help_file_list,
                      "9":races_help_file_list,
                      "10":all_players_help_file_list,
                      "11":fcs_help_file_list,
                      "12":race_results_help_file_list}

HELP_KEY_FILES = {default_help_key:main_help_file_list,
                  tabling_help_key:tabling_help_file_list,
                  "serverdefaults":server_defaults_help_file_list,
                  "server defaults":server_defaults_help_file_list,
                  "flags":flags_help_file_list,
                  "submittable":lounge_submitting_tables_help_file_list,
                  "submitable":lounge_submitting_tables_help_file_list,
                  "submit table":lounge_submitting_tables_help_file_list,
                  "reporter":lounge_reporter_help_file_list,
                  "reporters":lounge_reporter_help_file_list,
                  "updater":lounge_reporter_help_file_list,
                  "updaters":lounge_reporter_help_file_list,
                  "other":other_help_file_list
                  }

HELP_CATEGORIES = [
    "tabling", 
    "server defaults",
    "flags",
    "submit table",
    "reporter",
    "updater",
    "other"
]

for tabling_help_list in TABLING_HELP_FILES.values():
    for index, file_name in enumerate(tabling_help_list):
        if not tabling_help_list[index].startswith(common.TABLING_HELP_PATH):
            tabling_help_list[index] = f"{common.TABLING_HELP_PATH}{file_name}"

for help_list in HELP_KEY_FILES.values():
    for index, file_name in enumerate(help_list):
        if not help_list[index].startswith(common.HELP_PATH):
            help_list[index] = f"{common.HELP_PATH}{file_name}"
    
QUICKSTART_FILE = f"{common.HELP_PATH}quickstart.txt"

def get_help_files(args:List[str]):
    help_ind = None
    for ind, arg in enumerate(args):
        if 'help' in arg:
            help_ind = ind
            break
        
    if help_ind is None:
        return default_help_key, HELP_KEY_FILES[default_help_key]
    new_args = args[help_ind+1:]
    help_key = " ".join(new_args)
    if help_key in HELP_KEY_FILES:
        return help_key, HELP_KEY_FILES[help_key]
    if help_key in TABLING_HELP_FILES:
        return help_key, TABLING_HELP_FILES[help_key]
    return default_help_key, HELP_KEY_FILES[default_help_key]


async def send_help(message: discord.Message, args:List[str], prefix=common.default_prefix, is_lounge_server=False):
    embed = discord.Embed(description="- [Help Documentation](https://www.github.com/BadWolf1023/MKW-Table-Bot/wiki)\n"
                                            f"- [Discord Server](https://discord.gg/{common.TABLEBOT_SERVER_INVITE_CODE})\n"
                                            f"- [Invite the bot]({common.INVITE_LINK})")
    embed.set_author(name="MKW Table Bot Help", icon_url="https://64.media.tumblr.com/b0df9696b2c8388dba41ad9724db69a4/tumblr_mh1nebDwp31rsjd4ho1_500.jpg")

    await message.channel.send(embed=embed)
    # help_key, help_files = get_help_files(args)
    
    # """if is_lounge_server and help_key == tabling_help_key:
    #     await message.channel.send("See the table bot guide and flow charts in <#835555593833414696> or <#835561764322017320>.")
    #     return
    # """
    # for help_text_file in help_files:
    #     if os.path.isfile(help_text_file):
    #         with open(help_text_file, "r", encoding="utf-8") as f:
    #             help_text = f.read()
    #             if len(help_text) > 1:
    #                 help_text = help_text.replace("{SERVER_PREFIX}", prefix)
    #                 help_text_chunks = list(UtilityFunctions.string_chunks(help_text, 2000))

    #                 for chunk in help_text_chunks:
    #                     await message.channel.send(chunk)
    #             else:
    #                 break
                    
async def send_quickstart(discord_message_obj):
    quick_start = "No quickstart."
    with open(QUICKSTART_FILE, "r", encoding="utf-8") as f:
        quick_start = f.read()
    await discord_message_obj.channel.send(quick_start)
                    