from discord.utils import escape_markdown, escape_mentions
from common import check_create
import os
from common import BLACKLISTED_WORDS_FILE, BOT_ADMINS_FILE
blacklistedWordsFileIsOpen = False

blackListedWords = set()
botAdminsFileIsOpen = False
botAdmins = set()

    
        
def get_blw():
    return blackListedWords


def remove_blacklisted(name:str, get_blacklisted_words=get_blw):
    blacklisted_words = get_blacklisted_words()
    if name == None or len(name) == 0:
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


def readBlackListedWordsFile(filename=BLACKLISTED_WORDS_FILE):
    check_create(filename)
    temp = set()
    with open(filename, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            temp.add(line.strip("\n").strip())
    return temp

def add_blacklisted_word(word:str):
    global blacklistedWordsFileIsOpen
    global blackListedWords
    
    word = str(word).lower()
    if blacklistedWordsFileIsOpen:
        return False
    else:
        blacklistedWordsFileIsOpen = True
        #If it's not in the blacklisted words, then add it
        if word not in blackListedWords:            
            with open(BLACKLISTED_WORDS_FILE, "a", encoding="utf-8", errors="replace") as f:
                f.write(word + "\n")
                blackListedWords.add(word)
        
        blacklistedWordsFileIsOpen = False
        return True
    
def remove_blacklisted_word(word:str):
    global blacklistedWordsFileIsOpen
    global blackListedWords
    
    word = str(word).lower()
    if blacklistedWordsFileIsOpen:
        return False
    else:
        blacklistedWordsFileIsOpen = True
        #If it's in the blacklisted words, we need to remove it
        if word in blackListedWords:
            check_create(BLACKLISTED_WORDS_FILE)

            #Next, let's add all of the fc and lounge names to the file and dictionary
            temp_file_name = f"{BLACKLISTED_WORDS_FILE}_temp"
            with open(temp_file_name, "w", encoding="utf-8", errors="replace") as temp_out, open(BLACKLISTED_WORDS_FILE, "r", encoding="utf-8", errors="replace") as original:
                for line in original:
                    cur_word = line.strip("\n").strip()
                    if cur_word != word:
                        temp_out.write(line)
                blackListedWords.remove(word)

            os.remove(BLACKLISTED_WORDS_FILE)
            os.rename(temp_file_name, BLACKLISTED_WORDS_FILE)
        
        blacklistedWordsFileIsOpen = False
        return True
    
def readBotAdminsFile(filename=BOT_ADMINS_FILE):
    check_create(filename)
    temp = set()
    with open(filename, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            temp.add(line.strip("\n").strip())
    return temp

def addBotAdmin(admin_id:str):
    global botAdminsFileIsOpen
    global botAdmins
    
    admin_id = str(admin_id).lower()
    if botAdminsFileIsOpen:
        return False
    else:
        botAdminsFileIsOpen = True
        #If it's not in the blacklisted words, then add it
        if admin_id not in botAdmins:            
            with open(BOT_ADMINS_FILE, "a", encoding="utf-8", errors="replace") as f:
                f.write(admin_id + "\n")
                botAdmins.add(admin_id)
        
        botAdminsFileIsOpen = False
        return True
    
def removeBotAdmin(admin_id:str):
    global botAdminsFileIsOpen
    global botAdmins
    
    admin_id = str(admin_id).lower()
    if botAdminsFileIsOpen:
        return False
    else:
        botAdminsFileIsOpen = True
        #If it's in the blacklisted words, we need to remove it
        if admin_id in botAdmins:
            check_create(BOT_ADMINS_FILE)

            #Next, let's add all of the fc and lounge names to the file and dictionary
            temp_file_name = f"{BOT_ADMINS_FILE}_temp"
            with open(temp_file_name, "w", encoding="utf-8", errors="replace") as temp_out, open(BOT_ADMINS_FILE, "r", encoding="utf-8", errors="replace") as original:
                for line in original:
                    cur_admin = line.strip("\n").strip()
                    if cur_admin != admin_id:
                        temp_out.write(line)
                botAdmins.remove(admin_id)

            os.remove(BOT_ADMINS_FILE)
            os.rename(temp_file_name, BOT_ADMINS_FILE)
        
        botAdminsFileIsOpen = False
        return True
    
def initialize():
    global botAdmins
    global blackListedWords
    botAdmins.clear()
    botAdmins.update(readBotAdminsFile())
    blackListedWords.clear()
    blackListedWords.update(readBlackListedWordsFile())