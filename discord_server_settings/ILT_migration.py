import fileinput
LARGE_TIME_FILE = 'discord_server_settings/server_large_time_defaults.txt'

def migrate_settings():
    for line in fileinput.input(LARGE_TIME_FILE, inplace=True):
        split = line.find(' ')
        guild_id = line[:split].strip()
        cur_setting = line[split+1:].strip()
        new_setting = '0' if cur_setting == '1' else '1+'
        print(f'{guild_id} {new_setting}') #write to file line in-place
    fileinput.close()

if __name__ == "__main__":
    migrate_settings()