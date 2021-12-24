from discord.utils import escape_markdown, escape_mentions
import os
import common
from typing import List
import discord
from pathlib import Path
import re
from datetime import datetime, timezone

    
        
def get_blw():
    return common.blackListedWords


def remove_blacklisted(name:str, get_blacklisted_words=get_blw):
    blacklisted_words = get_blacklisted_words()
    if name is None or len(name) == 0:
        return "", False
    
    for blacklisted_word in blacklisted_words:
        if blacklisted_word.lower() in name.lower():
            name = name.lower().replace(blacklisted_word.lower(), "*"*len(blacklisted_word))
            return name, True
        elif len(blacklisted_word) > 3 and blacklisted_word[::-1] in name:
            name = name.lower().replace(blacklisted_word[::-1].lower(), "*"*len(blacklisted_word))
            return name, True
    return name, False
            

def process_name(name:str, get_blacklisted_words=get_blw):
    had_blacklisted = True
    while had_blacklisted:
        name, had_blacklisted = remove_blacklisted(name, get_blacklisted_words)
    return escape_mentions(escape_markdown(name))


def readBlackListedWordsFile(filename=common.BLACKLISTED_WORDS_FILE):
    common.check_create(filename)
    temp = set()
    with open(filename, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            temp.add(line.strip("\n").strip())
    return temp

def add_blacklisted_word(word:str):    
    word = str(word).lower()
    if common.blacklistedWordsFileIsOpen:
        return False
    else:
        common.blacklistedWordsFileIsOpen = True
        #If it's not in the blacklisted words, then add it
        if word not in common.blackListedWords:            
            with open(common.BLACKLISTED_WORDS_FILE, "a", encoding="utf-8", errors="replace") as f:
                f.write(word + "\n")
                common.blackListedWords.add(word)
        
        common.blacklistedWordsFileIsOpen = False
        return True
    
def remove_blacklisted_word(word:str):
    
    word = str(word).lower()
    if common.blacklistedWordsFileIsOpen:
        return False
    else:
        common.blacklistedWordsFileIsOpen = True
        #If it's in the blacklisted words, we need to remove it
        if word in common.blackListedWords:
            common.check_create(common.BLACKLISTED_WORDS_FILE)

            #Next, let's add all of the fc and lounge names to the file and dictionary
            temp_file_name = f"{common.BLACKLISTED_WORDS_FILE}_temp"
            with open(temp_file_name, "w", encoding="utf-8", errors="replace") as temp_out, open(common.BLACKLISTED_WORDS_FILE, "r", encoding="utf-8", errors="replace") as original:
                for line in original:
                    cur_word = line.strip("\n").strip()
                    if cur_word != word:
                        temp_out.write(line)
                common.blackListedWords.remove(word)

            os.remove(common.BLACKLISTED_WORDS_FILE)
            os.rename(temp_file_name, common.BLACKLISTED_WORDS_FILE)
        
        common.blacklistedWordsFileIsOpen = False
        return True
    
def readBotAdminsFile(filename=common.BOT_ADMINS_FILE):
    common.check_create(filename)
    temp = set()
    with open(filename, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            temp.add(line.strip("\n").strip())
    return temp

def addBotAdmin(admin_id:str):
    
    admin_id = str(admin_id).lower()
    if common.botAdminsFileIsOpen:
        return False
    else:
        common.botAdminsFileIsOpen = True
        #If it's not in the blacklisted words, then add it
        if admin_id not in common.botAdmins:            
            with open(common.BOT_ADMINS_FILE, "a", encoding="utf-8", errors="replace") as f:
                f.write(admin_id + "\n")
                common.botAdmins.add(admin_id)
        
        common.botAdminsFileIsOpen = False
        return True
    
def removeBotAdmin(admin_id:str):
    
    admin_id = str(admin_id).lower()
    if common.botAdminsFileIsOpen:
        return False
    else:
        common.botAdminsFileIsOpen = True
        #If it's in the blacklisted words, we need to remove it
        if admin_id in common.botAdmins:
            common.check_create(common.BOT_ADMINS_FILE)

            #Next, let's add all of the fc and lounge names to the file and dictionary
            temp_file_name = f"{common.BOT_ADMINS_FILE}_temp"
            with open(temp_file_name, "w", encoding="utf-8", errors="replace") as temp_out, open(common.BOT_ADMINS_FILE, "r", encoding="utf-8", errors="replace") as original:
                for line in original:
                    cur_admin = line.strip("\n").strip()
                    if cur_admin != admin_id:
                        temp_out.write(line)
                common.botAdmins.remove(admin_id)

            os.remove(common.BOT_ADMINS_FILE)
            os.rename(temp_file_name, common.BOT_ADMINS_FILE)
        
        common.botAdminsFileIsOpen = False
        return True
    
def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False
    
def isint(value):
    try:
        int(value)
        return True
    except:
        return False

#Takes a list of strings and concatenates them until a new concatenation would push it over the limit given
#Separator is what will separate each concatenation
def chunk_join(str_items:List[str], limit=2047, separator="\n"):
    if len(str_items) == 0:
        return [""]
    
    to_return = []
    to_return.append(str_items[0])
    for item in str_items[1:]:
        new_length = len(to_return[-1]) + len(separator) + len(item)
        if new_length > limit:
            to_return.append(item)
        else:
            to_return[-1] = to_return[-1] + separator + item
    return to_return
        
    
async def safe_send_file(message:discord.Message, content):
    file_name = str(message.id) + ".txt"
    Path('./attachments').mkdir(parents=True, exist_ok=True)
    file_path = "./attachments/" + file_name
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    txt_file = discord.File(file_path, filename=file_name)
    try:
        await message.channel.send(file=txt_file)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

hex_chars = "ABCDEFabcdef0123456789" 
def is_hex(text):
    return all(c in hex_chars for c in text)

def is_wiimmfi_utc_time(race_time:str):
    race_time = race_time.strip()
    if race_time.endswith("UTC"):
        race_time = race_time[:-3]
    race_time = race_time.strip()
    try:
        datetime.strptime(race_time, '%Y-%m-%d %H:%M')
    except ValueError:
        return False
    return re.match("^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$", race_time) is not None


def get_wiimmfi_utc_time(race_time:str):
    """Caller is responsible for calling is_wiimmfi_utc_time first"""
    race_time = race_time.strip()
    if race_time.endswith("UTC"):
        race_time = race_time[:-3]
    race_time = race_time.strip()
    return datetime.strptime(race_time, '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc)

def is_race_ID(raceID):
    return re.match("^r[0-9]{7}$", raceID) is not None

def is_rLID(roomID):
    return re.match("^r[0-9]{7}$", roomID) is not None

def is_fc(fc):
    return re.match("^[0-9]{4}[-][0-9]{4}[-][0-9]{4}$", fc.strip()) is not None
    
def initialize():
    common.botAdmins.clear()
    common.botAdmins.update(readBotAdminsFile())
    common.blackListedWords.clear()
    common.blackListedWords.update(readBlackListedWordsFile())